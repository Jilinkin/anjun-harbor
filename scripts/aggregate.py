"""Offline aggregation of authorized local snapshots. No downloads or code execution."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from audit_dependencies import read_limited
from build import build

MAX_DEPTH=8
MAX_NODES=500
MAX_SITES=20000

def digest(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def parse_config(text):
    # Strip JSON comments only outside quoted strings, then trailing commas.
    out=[]; i=0; quoted=False
    while i<len(text):
        c=text[i]
        if quoted:
            out.append(c)
            if c=="\\":
                i+=1
                if i>=len(text): raise ValueError("Unterminated escape")
                out.append(text[i])
            elif c=='"': quoted=False
        elif c=='"':
            quoted=True; out.append(c)
        elif text.startswith("//",i):
            j=text.find("\n",i+2)
            i=len(text) if j<0 else j
            out.append("\n"); continue
        elif text.startswith("/*",i):
            j=text.find("*/",i+2)
            if j<0: raise ValueError("Unterminated comment")
            i=j+2; out.append(" "); continue
        else: out.append(c)
        i+=1
    text="".join(out); out=[]; quoted=False; i=0
    while i<len(text):
        c=text[i]
        if quoted:
            out.append(c)
            if c=="\\":
                i+=1
                if i>=len(text): raise ValueError("Unterminated escape")
                out.append(text[i])
            elif c=='"': quoted=False
        elif c=='"': quoted=True; out.append(c)
        elif c=="," and re.match(r"\s*[}\]]",text[i+1:]): pass
        else: out.append(c)
        i+=1
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result: raise ValueError("Duplicate JSON field")
            result[k]=v
        return result
    return json.loads("".join(out).lstrip("\ufeff"),object_pairs_hook=unique)

def public_url(url,https_only=False):
    try:
        u=urlsplit(url)
        return u.scheme in (("https",) if https_only else ("http","https")) and bool(u.hostname) and not u.username and not u.password and not u.fragment and not any(c.isspace() for c in url)
    except (ValueError,TypeError): return False

def snapshots(manifest,root):
    root=Path(root).resolve()
    mapped={}
    for row in manifest["snapshots"]:
        url=row["url"]
        if not public_url(url) or url in mapped: raise ValueError("Invalid or duplicate snapshot URL")
        path=(root/row["file"]).resolve()
        if not path.is_relative_to(root): raise ValueError("Snapshot path outside directory")
        mapped[url]=path
    return mapped

def inventory(roots,mapped):
    seen=set(); warehouses=[]; issues=[]; sites_total=0
    def walk(url,stack,depth):
        nonlocal sites_total
        if url in stack:
            issues.append({"url":url,"reason":"cycle"}); return
        if depth>MAX_DEPTH:
            issues.append({"url":url,"reason":"depth_limit"}); return
        if url in seen: return
        if len(seen)>=MAX_NODES: raise ValueError("Too many configurations")
        seen.add(url)
        if url not in mapped:
            issues.append({"url":url,"reason":"snapshot_missing"}); return
        try: obj=parse_config(read_limited(mapped[url]).decode("utf-8-sig"))
        except (OSError,ValueError,UnicodeError):
            issues.append({"url":url,"reason":"parse_failed"}); return
        if not isinstance(obj,dict):
            issues.append({"url":url,"reason":"unsupported_shape"}); return
        if isinstance(obj.get("urls"),list) and not isinstance(obj.get("sites"),list):
            for child in obj["urls"]:
                if not isinstance(child,dict) or not isinstance(child.get("url"),str):
                    issues.append({"url":url,"reason":"invalid_child"}); continue
                target=urljoin(url,child["url"])
                if not public_url(target):
                    issues.append({"url":url,"reason":"unsupported_child_url"}); continue
                walk(target,stack|{url},depth+1)
        elif isinstance(obj.get("sites"),list) and not isinstance(obj.get("urls"),list):
            sites_total+=len(obj["sites"])
            if sites_total>MAX_SITES: raise ValueError("Too many sites")
            warehouses.append((url,obj))
        else: issues.append({"url":url,"reason":"unsupported_or_ambiguous_shape"})
    for url in roots:
        if not public_url(url): raise ValueError("Invalid root URL")
        walk(url,set(),0)
    return warehouses,issues

def analyze(warehouses,issues):
    fingerprints={}; apis={}; keys={}; rows=[]
    for url,obj in warehouses:
        fingerprints.setdefault(digest(obj),[]).append(url)
        for i,s in enumerate(obj["sites"]):
            if not isinstance(s,dict): continue
            row={"id":digest([url,i,s]),"warehouse":url,"position":i,"key":str(s.get("key","")),
                 "name":str(s.get("name","")),"type":s.get("type")}
            rows.append(row)
            if row["key"]: keys.setdefault(row["key"],[]).append(row["id"])
            api=s.get("api")
            if type(s.get("type")) is int and s["type"] in (0,1) and isinstance(api,str) and public_url(api):
                apis.setdefault((s["type"],api),[]).append(row["id"])
    return {"warehouses":len(warehouses),"sites":len(rows),"unresolved":issues,"entries":rows,
            "identical_config_content_candidates":[v for v in fingerprints.values() if len(v)>1],
            "same_independent_api_candidates":[v for v in apis.values() if len(v)>1],
            "same_key_candidates":[v for v in keys.values() if len(v)>1],
            "note":"All groups are review candidates; identical content at different base URLs can resolve relative dependencies differently."}

def make_catalog(warehouses,selection):
    # Each selection explicitly authorizes the independent API and confirms no extra context is required.
    lookup={digest([url,i,s]):s for url,obj in warehouses for i,s in enumerate(obj["sites"]) if isinstance(s,dict)}
    groups={}; used=set()
    for choice in selection["entries"]:
        sid=choice["id"]
        if sid not in lookup: raise ValueError("Selection is stale or missing")
        if choice.get("approved") is not True or choice.get("independent_confirmed") is not True:
            raise ValueError("Explicit review is required")
        auth=choice.get("authorization")
        if not isinstance(auth,str) or not auth.strip(): raise ValueError("Authorization evidence required")
        s=lookup[sid]; api=s.get("api")
        if type(s.get("type")) is not int or s["type"] not in (0,1) or not isinstance(api,str) or not public_url(api,True) or urlsplit(api).query:
            raise ValueError("Unsupported independent API")
        # Existing builder emits only the simple CMS fields. Never silently strip special site options.
        if any(k not in {"key","name","type","api","searchable","quickSearch"} for k in s):
            raise ValueError("Site has additional settings; preserve separately for review")
        if s.get("searchable",1)!=1 or s.get("quickSearch",1)!=1:
            raise ValueError("Site search settings differ from builder")
        signature=(s["type"],api)
        if signature in used: continue
        used.add(signature)
        gid=choice["group"]
        group=groups.setdefault(gid,{"id":gid,"name":choice.get("group_name",gid),"sites":[]})
        group["sites"].append({"key":"s-"+sid[:24],"name":choice.get("name",s.get("name","")),"type":s["type"],
                               "api":api,"approved":True,"authorization":auth,"probe":False})
    catalog={"version":1,"groups":list(groups.values())}
    build(catalog)
    return catalog

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--selection",type=Path)
    args=p.parse_args()
    manifest=json.loads(read_limited(args.manifest).decode("utf-8-sig"))
    mapped=snapshots(manifest,args.manifest.resolve().parent)
    warehouses,issues=inventory(manifest["roots"],mapped)
    if args.selection:
        selection=json.loads(read_limited(args.selection).decode("utf-8-sig"))
        result=make_catalog(warehouses,selection)
    else: result=analyze(warehouses,issues)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2); f.write("\n")
    print("Output written:",args.output)

if __name__=="__main__": main()
