"""Local, review-only deduplication of authorized normalized catalogs."""
import argparse
import hashlib
import json
import unicodedata
from dataclasses import asdict
from pathlib import Path
from harbor_engine import Catalog
from engine_network import LoadedAdapter
from engine_registry import load_mixed
from audit_dependencies import read_limited

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

def normalized(value):
    return " ".join(unicodedata.normalize("NFKC",value).casefold().split())

def fingerprint(catalog):
    return digest([asdict(catalog.records[k]) for k in sorted(catalog.records)])

def preview(catalog):
    exact={}; metadata={}
    for item in catalog.records.values():
        # Exact match includes all episode names and ordered URLs, title metadata,
        # description and authorization; never infer rights from URL equality.
        sig=digest([item.name,item.category,item.year,item.description,item.license_note,
                    [(e.name,e.url) for e in item.episodes]])
        exact.setdefault(sig,[]).append(item.id)
        if item.year.strip():
            key=digest([normalized(item.name),item.year.strip()])
            metadata.setdefault(key,[]).append(item.id)
    def groups(mapping):
        return [{"group":k,"members":sorted(ids)} for k,ids in sorted(mapping.items()) if len(ids)>1]
    return {"version":1,"catalog_fingerprint":fingerprint(catalog),"total":len(catalog.records),
            "exact_record_candidates":groups(exact),"same_title_year_candidates":groups(metadata),
            "records":[{"id":t.id,"provider":t.provider,"name":t.name,"year":t.year,
                        "category":t.category,"episodes":len(t.episodes)} for t in catalog.records.values()],
            "note":"Candidates only. No automatic removal or playback/rights verification."}

def apply(catalog,selection):
    report=preview(catalog)
    if not isinstance(selection,dict) or set(selection)!={"version","catalog_fingerprint","decisions"} or type(selection["version"]) is not int or selection["version"]!=1:
        raise ValueError("Invalid selection version")
    if selection["catalog_fingerprint"]!=report["catalog_fingerprint"]:
        raise ValueError("Stale selection; review the current preview")
    choices=selection["decisions"]
    if not isinstance(choices,list): raise ValueError("Invalid decisions")
    groups={g["group"]:set(g["members"]) for g in report["exact_record_candidates"]}
    used=set();drop=set();history=[]
    for choice in choices:
        if not isinstance(choice,dict) or set(choice)!={"group","keep","remove","approved"} or choice["approved"] is not True:
            raise ValueError("Explicit review required")
        group=choice["group"]
        if not isinstance(group,str) or group not in groups or group in used:
            raise ValueError("Unknown or repeated exact group")
        used.add(group)
        keep=choice["keep"];remove=choice["remove"]
        if not isinstance(keep,str) or not isinstance(remove,list) or not remove or any(not isinstance(x,str) for x in remove):
            raise ValueError("Invalid selection members")
        if keep not in groups[group] or len(set(remove))!=len(remove) or keep in remove or not set(remove)<=groups[group]:
            raise ValueError("Selection outside exact group")
        drop.update(remove)
        history.append({"group":group,"keep":keep,"hidden":sorted(remove)})
    rows={p:[] for p in sorted(catalog.providers)}
    for t in catalog.records.values():
        if t.id not in drop: rows[t.provider].append(t)
    result=Catalog([LoadedAdapter(p,items) for p,items in rows.items()])
    return result,{"version":1,"before":len(catalog.records),"after":len(result.records),
                   "hidden":len(drop),"decisions":history,"catalog_fingerprint":report["catalog_fingerprint"]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest",type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--selection",type=Path)
    a=parser.parse_args()
    catalog,status=load_mixed(a.manifest)
    if any(s["status"]!="ok" for s in status):
        parser.error("Incomplete catalog; repair failed providers before reviewing")
    result=preview(catalog)
    if a.selection:
        _,result=apply(catalog,json.loads(read_limited(a.selection).decode("utf-8-sig")))
    with a.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")

if __name__=="__main__":main()
