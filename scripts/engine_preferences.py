"""Reversible local display preferences for an authorized normalized catalog."""
import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from harbor_engine import Catalog,text
from engine_network import LoadedAdapter
from engine_dedupe import fingerprint,apply as dedupe
from engine_registry import load_mixed
from audit_dependencies import read_limited

def label(value):
    if not text(value,100).strip():
        raise ValueError("Empty display label")
    return value.strip()

def load_json(path):
    return json.loads(read_limited(Path(path)).decode("utf-8-sig"))

def template(catalog):
    return {"version":1,"catalog_fingerprint":fingerprint(catalog),
            "warehouse_name":"Harbor","provider_priority":[],"category_names":{},
            "records":{}}

def apply(catalog,prefs):
    if not isinstance(prefs,dict) or set(prefs)!=set(template(catalog)) or type(prefs["version"]) is not int or prefs["version"]!=1:
        raise ValueError("Invalid preferences schema")
    if prefs["catalog_fingerprint"]!=fingerprint(catalog):
        raise ValueError("Stale preferences: regenerate and review")
    name=label(prefs["warehouse_name"])
    priority=prefs["provider_priority"]
    if not isinstance(priority,list) or any(not isinstance(x,str) or x not in catalog.providers for x in priority) or len(priority)!=len(set(priority)):
        raise ValueError("Invalid provider priority")
    rank={p:i for i,p in enumerate(priority)}
    categories=prefs["category_names"]
    if not isinstance(categories,dict) or not set(categories)<=set(catalog.categories.values()):
        raise ValueError("Unknown category")
    categories={k:label(v) for k,v in categories.items()}
    edits=prefs["records"]
    if not isinstance(edits,dict) or not set(edits)<=set(catalog.records):
        raise ValueError("Unknown record")
    for edit in edits.values():
        if not isinstance(edit,dict) or set(edit)-{"name","category","hidden","priority"}:
            raise ValueError("Unsupported display option")
        for k in ("name","category"):
            if k in edit: label(edit[k])
        if "hidden" in edit and type(edit["hidden"]) is not bool:
            raise ValueError("Invalid hidden flag")
        if "priority" in edit and (type(edit["priority"]) is not int or not -1000<=edit["priority"]<=1000):
            raise ValueError("Invalid record priority")
    ordered=[];hidden=[];aliases={}
    for i,record in enumerate(catalog.records.values()):
        edit=edits.get(record.id,{})
        if edit.get("hidden",False):
            hidden.append(record.id)
            continue
        item=replace(record,name=label(edit.get("name",record.name)) if "name" in edit else record.name,
                     category=label(edit["category"]) if "category" in edit else categories.get(record.category,record.category))
        aliases[item.id]=record.name
        ordered.append(((-edit.get("priority",0),rank.get(record.provider,len(rank)),i),item))
    ordered.sort(key=lambda row:row[0])
    rows={p:[] for p in sorted(catalog.providers)}
    for _,item in ordered: rows[item.provider].append(item)
    result=Catalog([LoadedAdapter(p,items) for p,items in rows.items()])
    # Catalog groups by provider during construction; restore global display order.
    result.records={item.id:item for _,item in ordered}
    result.categories={hashlib.sha256(t.category.encode()).hexdigest()[:16]:t.category for t in result.records.values()}
    return result,name,{"before":len(catalog.records),"after":len(result.records),"hidden":hidden,
                        "warehouse_name":name,"records":[{"id":t.id,"provider":t.provider,"name":t.name,
                        "original_name":aliases[t.id],"category":t.category} for t in result.records.values()]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--preferences",type=Path)
    p.add_argument("--dedupe-selection",type=Path)
    a=p.parse_args()
    catalog,status=load_mixed(a.manifest)
    if any(s["status"]!="ok" for s in status):
        p.error("Incomplete catalog")
    if a.dedupe_selection: catalog,_=dedupe(catalog,load_json(a.dedupe_selection))
    if a.preferences:
        _,_,result=apply(catalog,load_json(a.preferences))
    else: result=template(catalog)
    with a.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")

if __name__=="__main__": main()
