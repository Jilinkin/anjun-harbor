"""Offline HTML mapping for explicitly authorized metadata snapshots.
Restricted CSS and XPath subsets; no network requests or JavaScript execution.
"""
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from harbor_engine import Catalog,Title,Episode,SLUG
from engine_network import LoadedAdapter,MAX_PROVIDERS,MAX_ROWS
from audit_dependencies import read_limited

MAX_NODES=20000
MAX_DEPTH=80
VOID={"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
SKIP={"script","style","iframe","object","template","noscript"}
TOKEN=re.compile(r"(?P<tag>[a-zA-Z][\w-]*|\*)?(?P<suffix>(?:[.#][a-zA-Z_][\w-]*)*)")
ATTR=re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,59}$")
XPATH=re.compile(r"^\.(?:/{1,2}(?:[a-zA-Z][\w-]*|\*)(?:\[@[a-zA-Z][\w-]*(?:='[a-zA-Z0-9_ .:-]{1,80}')?\])?)+$")

class Tree(HTMLParser):
    def __init__(self,source):
        super().__init__(convert_charrefs=True)
        self.root=ET.Element("root")
        self.stack=[self.root]
        self.skipped=[]
        self.count=0
        self.feed(source)
        self.close()
    def handle_starttag(self,tag,attrs):
        if self.skipped:
            if tag in SKIP: self.skipped.append(tag)
            return
        if tag in SKIP:
            self.skipped.append(tag)
            return
        self.count+=1
        if self.count>MAX_NODES or len(self.stack)>MAX_DEPTH:
            raise ValueError("HTML tree limit")
        node=ET.SubElement(self.stack[-1],tag,{k:v or "" for k,v in attrs})
        if tag not in VOID: self.stack.append(node)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_endtag(self,tag):
        if self.skipped:
            if tag==self.skipped[-1]: self.skipped.pop()
            return
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:
                del self.stack[i:]
                return
    def handle_data(self,data):
        if self.skipped: return
        node=self.stack[-1]
        if len(node):
            child=node[-1]
            child.tail=(child.tail or "")+data
        else: node.text=(node.text or "")+data

def css_match(node,token):
    m=TOKEN.fullmatch(token)
    if not m or not token: raise ValueError("Unsupported CSS token")
    tag=m.group("tag")
    if tag and tag!="*" and node.tag!=tag.lower(): return False
    for prefix,value in re.findall(r"([.#])([a-zA-Z_][\w-]*)",m.group("suffix")):
        if prefix=="#" and node.get("id")!=value: return False
        if prefix=="." and value not in node.get("class","").split(): return False
    return True

def selector(rule):
    if not isinstance(rule,dict) or set(rule)!={"kind","path"}: raise ValueError("Invalid selector")
    path=rule["path"]
    if not isinstance(path,str) or not path or len(path)>300: raise ValueError("Invalid selector path")
    if rule["kind"]=="css":
        parts=path.split()
        if len(parts)>5 or any(not TOKEN.fullmatch(p) or not p for p in parts):
            raise ValueError("Unsupported CSS selector")
    elif rule["kind"]=="xpath":
        if not XPATH.fullmatch(path) or path.count("/")>10: raise ValueError("Unsupported XPath")
    else: raise ValueError("Unknown selector kind")
    return rule

def nodes(root,rule):
    selector(rule)
    if rule["kind"]=="xpath":
        return root.findall(rule["path"])
    current=[root]
    for token in rule["path"].split():
        found={}
        for parent in current:
            for node in parent.iter():
                if node is not parent and css_match(node,token): found[id(node)]=node
                if len(found)>MAX_NODES: raise ValueError("Selector result limit")
        current=list(found.values())
    return current

def field_spec(spec):
    if not isinstance(spec,dict) or set(spec)!={"selector","attribute"}:
        raise ValueError("Invalid field specification")
    if spec["selector"] is not None: selector(spec["selector"])
    attr=spec["attribute"]
    if attr!="text" and (not isinstance(attr,str) or not ATTR.fullmatch(attr) or attr.lower().startswith("on")):
        raise ValueError("Unsupported attribute")

def field(root,spec):
    field_spec(spec)
    result=[root] if spec["selector"] is None else nodes(root,spec["selector"])
    if len(result)!=1: raise ValueError("Field must match exactly one node")
    n=result[0]
    if spec["attribute"]=="text": return " ".join("".join(n.itertext()).split())
    value=n.get(spec["attribute"])
    if value is None: raise ValueError("Missing attribute")
    return value.strip()

class HtmlRuleAdapter:
    def __init__(self,rule,source):
        allowed={"version","provider","approved","authorization","items","fields","episodes","media_hosts"}
        if not isinstance(rule,dict) or set(rule)!=allowed or rule["version"]!=1 or rule["approved"] is not True:
            raise ValueError("Reviewed rule required")
        self.provider=rule["provider"]
        self.authorization=rule["authorization"]
        if not isinstance(self.provider,str) or not SLUG.fullmatch(self.provider) or not isinstance(self.authorization,str) or not self.authorization.strip():
            raise ValueError("Invalid provider or missing permission")
        self.fields=rule["fields"]
        if not isinstance(self.fields,dict) or not {"id","name","category"}<=set(self.fields) or set(self.fields)-{"id","name","category","year","description"}:
            raise ValueError("Invalid fields")
        for spec in self.fields.values(): field_spec(spec)
        self.ep=rule["episodes"]
        if not isinstance(self.ep,dict) or set(self.ep)!={"items","name","url"}: raise ValueError("Invalid episode mapping")
        selector(self.ep["items"])
        field_spec(self.ep["name"]);field_spec(self.ep["url"])
        hosts=rule["media_hosts"]
        if not isinstance(hosts,list) or not 1<=len(hosts)<=20 or any(not isinstance(h,str) or not h or h.lower()!=h or any(c in h for c in "/:@?# ") for h in hosts):
            raise ValueError("Media host allowlist required")
        self.hosts=set(hosts)
        selector(rule["items"])
        if not isinstance(source,str) or len(source)>512*1024: raise ValueError("HTML size limit")
        self.items=nodes(Tree(source).root,rule["items"])
        if len(self.items)>MAX_ROWS: raise ValueError("Item limit")
    def titles(self):
        for obj in self.items:
            fields={k:field(obj,v) for k,v in self.fields.items()}
            rows=nodes(obj,self.ep["items"])
            if not 1<=len(rows)<=1000: raise ValueError("Invalid episodes")
            eps=[]
            for row in rows:
                ep=Episode(field(row,self.ep["name"]),field(row,self.ep["url"]))
                if urlsplit(ep.url).hostname not in self.hosts: raise ValueError("Unreviewed media host")
                eps.append(ep)
            yield Title(self.provider,fields["id"],fields["name"],fields["category"],fields.get("year",""),
                        fields.get("description",""),tuple(eps),self.authorization)

def load_html(manifest_path):
    root=Path(manifest_path).resolve().parent
    manifest=json.loads(read_limited(Path(manifest_path)).decode("utf-8-sig"))
    entries=manifest.get("providers")
    if not isinstance(entries,list) or not 1<=len(entries)<=MAX_PROVIDERS: raise ValueError("Invalid provider list")
    def local_file(name):
        if not isinstance(name,str): raise ValueError("Invalid path")
        p=(root/name).resolve()
        if not p.is_relative_to(root): raise ValueError("Path outside manifest directory")
        return read_limited(p).decode("utf-8-sig")
    loaded=[];status=[];seen=set()
    for row in entries:
        if not isinstance(row,dict) or set(row)!={"rule","snapshot"}: raise ValueError("Invalid manifest entry")
        rule=json.loads(local_file(row["rule"]))
        provider=rule.get("provider")
        if not isinstance(provider,str) or not SLUG.fullmatch(provider) or provider in seen: raise ValueError("Invalid provider")
        seen.add(provider)
        try:
            adapter=HtmlRuleAdapter(rule,local_file(row["snapshot"]))
            titles=list(adapter.titles())
            checked=LoadedAdapter(provider,titles)
            Catalog([checked])
        except (OSError,ValueError,KeyError,TypeError,AttributeError,SyntaxError):
            status.append({"provider":provider,"status":"failed","items":0});continue
        loaded.append(checked)
        status.append({"provider":provider,"status":"ok","items":len(titles)})
    return Catalog(loaded),status
