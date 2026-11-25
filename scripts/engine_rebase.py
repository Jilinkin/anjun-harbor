"""Review-only migration of local display preferences across authorized snapshots."""
import argparse
import copy
import json
from pathlib import Path
from engine_preferences import template,apply,load_json
from engine_dedupe import apply as dedupe
from engine_registry import load_mixed

def rebase(old,new,prefs):
    # Verify that the old preferences were valid for the actual old catalog.
    apply(old,prefs)
    candidate=template(new)
    candidate["warehouse_name"]=prefs["warehouse_name"]
    conflicts=[];retained={"warehouse_name":1,"provider_priority":0,"category_names":0,"records":0}
    a=old.records;b=new.records
    common=set(a)&set(b)
    unchanged={k for k in common if a[k]==b[k]}
    for provider in prefs["provider_priority"]:
        if provider not in new.providers:
            reason="provider_removed"
        elif not any(a[k].provider==provider for k in unchanged):
            reason="no_unchanged_provider_record"
        else:
            candidate["provider_priority"].append(provider)
            retained["provider_priority"]+=1
            continue
        conflicts.append({"kind":"provider_priority","key":provider,"reason":reason})
    for category,value in prefs["category_names"].items():
        before={k for k,t in a.items() if t.category==category}
        after={k for k,t in b.items() if t.category==category}
        if before==after and before<=unchanged:
            candidate["category_names"][category]=value
            retained["category_names"]+=1
        else:
            conflicts.append({"kind":"category_names","key":category,"reason":"category_membership_or_records_changed","old_value":value})
    for rid,edit in prefs["records"].items():
        if rid in unchanged:
            candidate["records"][rid]=copy.deepcopy(edit)
            retained["records"]+=1
        else:
            conflicts.append({"kind":"records","key":rid,"reason":"record_changed" if rid in b else "record_removed","old_value":copy.deepcopy(edit)})
    # Validate resulting proposal, but never write it as an active preference file.
    result,_,_=apply(new,candidate)
    return {"version":1,"review_required":True,"old_fingerprint":prefs["catalog_fingerprint"],
            "new_fingerprint":candidate["catalog_fingerprint"],
            "added":sorted(set(b)-set(a)),"removed":sorted(set(a)-set(b)),
            "changed":sorted(common-unchanged),"unchanged_count":len(unchanged),
            "retained":retained,"conflicts":conflicts,"candidate_visible":len(result.records),
            "candidate_preferences":candidate}

def local_catalog(manifest,selection):
    catalog,status=load_mixed(manifest)
    if any(s["status"]!="ok" for s in status): raise ValueError("Incomplete catalog; repair providers before migration")
    if selection: catalog,_=dedupe(catalog,load_json(selection))
    return catalog

def main():
    p=argparse.ArgumentParser()
    p.add_argument("old_manifest",type=Path)
    p.add_argument("new_manifest",type=Path)
    p.add_argument("--preferences",required=True,type=Path)
    p.add_argument("--old-dedupe-selection",type=Path)
    p.add_argument("--new-dedupe-selection",type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    old=local_catalog(a.old_manifest,a.old_dedupe_selection)
    new=local_catalog(a.new_manifest,a.new_dedupe_selection)
    report=rebase(old,new,load_json(a.preferences))
    with a.output.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")

if __name__=="__main__":main()
