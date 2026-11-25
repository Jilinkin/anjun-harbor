"""Declarative, offline JSON field mapping for reviewed data snapshots."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from harbor_engine import Catalog,Title,Episode,SLUG
from engine_network import LoadedAdapter,MAX_PROVIDERS,MAX_ROWS
from audit_dependencies import read_limited

def path_tokens(value):
    if not isinstance(value,list) or len(value)>16 or any(
        not ((isinstance(x,str) and 0<len(x)<=100) or (type(x) is int and 0<=x<=10000))
        for x in value):
        raise ValueError("Invalid field path")
    return value

def select(obj,path):
    for key in path_tokens(path):
        if isinstance(key,str) and isinstance(obj,dict) and key in obj:
            obj=obj[key]
        elif type(key) is int and isinstance(obj,list) and key<len(obj):
            obj=obj[key]
        else:
            raise ValueError("Missing mapped field")
    return obj

def scalar(obj,path):
    v=select(obj,path)
    if isinstance(v,str): return v
    if type(v) is int: return str(v)
    raise ValueError("Expected string or integer")

class JsonRuleAdapter:
    def __init__(self,rule,data):
        if not isinstance(rule,dict) or rule.get("version")!=1 or rule.get("approved") is not True:
            raise ValueError("Reviewed version 1 rule required")
        allowed={"version","provider","approved","authorization","items","fields","episodes","media_hosts"}
        if set(rule)-allowed: raise ValueError("Unknown rule property")
        self.provider=rule["provider"]
        if not isinstance(self.provider,str) or not SLUG.fullmatch(self.provider): raise ValueError("Invalid provider")
        self.authorization=rule["authorization"]
        if not isinstance(self.authorization,str) or not self.authorization.strip(): raise ValueError("Permission required")
        self.fields=rule["fields"]
        if not isinstance(self.fields,dict) or not {"id","name","category"}<=set(self.fields) or set(self.fields)-{"id","name","category","year","description"}:
            raise ValueError("Invalid mapped fields")
        for p in self.fields.values(): path_tokens(p)
        self.ep=rule["episodes"]
        if not isinstance(self.ep,dict) or set(self.ep)!={"items","name","url"}: raise ValueError("Invalid episode mapping")
        for p in self.ep.values(): path_tokens(p)
        hosts=rule["media_hosts"]
        if not isinstance(hosts,list) or not 1<=len(hosts)<=20 or any(not isinstance(h,str) or not h or h!=h.lower() or any(c in h for c in "/:@?# ") for h in hosts):
            raise ValueError("Explicit media host allowlist required")
        self.hosts=set(hosts)
        self.items=select(data,rule["items"])
        if not isinstance(self.items,list) or len(self.items)>MAX_ROWS: raise ValueError("Invalid item list")
    def titles(self):
        for obj in self.items:
            fields={k:scalar(obj,p) for k,p in self.fields.items()}
            rows=select(obj,self.ep["items"])
            if not isinstance(rows,list) or not 1<=len(rows)<=1000: raise ValueError("Invalid episodes")
            eps=[]
            for row in rows:
                ep=Episode(scalar(row,self.ep["name"]),scalar(row,self.ep["url"]))
                if urlsplit(ep.url).hostname not in self.hosts: raise ValueError("Unreviewed media host")
                eps.append(ep)
            yield Title(self.provider,fields["id"],fields["name"],fields["category"],
                        fields.get("year",""),fields.get("description","").replace("\n"," "),tuple(eps),self.authorization)

def load_rules(manifest_path):
    root=Path(manifest_path).resolve().parent
    manifest=json.loads(read_limited(Path(manifest_path)).decode("utf-8-sig"))
    entries=manifest.get("providers")
    if not isinstance(entries,list) or not 1<=len(entries)<=MAX_PROVIDERS: raise ValueError("Invalid provider list")
    def load_file(name):
        if not isinstance(name,str): raise ValueError("Invalid file path")
        path=(root/name).resolve()
        if not path.is_relative_to(root): raise ValueError("Path outside manifest directory")
        return json.loads(read_limited(path).decode("utf-8-sig"))
    loaded=[];status=[];seen=set()
    for row in entries:
        if not isinstance(row,dict) or set(row)!={"rule","snapshot"}: raise ValueError("Invalid manifest row")
        rule=load_file(row["rule"])
        provider=rule.get("provider")
        if not isinstance(provider,str) or not SLUG.fullmatch(provider) or provider in seen: raise ValueError("Duplicate or invalid provider")
        seen.add(provider)
        try:
            adapter=JsonRuleAdapter(rule,load_file(row["snapshot"]))
            titles=list(adapter.titles())
            checked=LoadedAdapter(provider,titles)
            Catalog([checked])
        except (OSError,ValueError,KeyError,TypeError,AttributeError):
            status.append({"provider":provider,"status":"failed","items":0})
            continue
        loaded.append(checked)
        status.append({"provider":provider,"status":"ok","items":len(titles)})
    return Catalog(loaded),status
