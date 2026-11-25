"""Personalize a locally saved, authorized single-warehouse config.
No network access, code execution, or automatic publishing.
"""
import argparse
import copy
import json
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from aggregate import parse_config,public_url
from audit_dependencies import read_limited

REF_FIELDS={"api","ext","jar","spider","script","rule","rules","url","playUrl","wallpaper","logo"}

def relocate(value,base,field=None):
    if isinstance(value,dict):
        return {k:relocate(v,base,k) for k,v in value.items()}
    if isinstance(value,list):
        return [relocate(v,base,field) for v in value]
    if isinstance(value,str) and value.startswith(("./","../","/")):
        if field not in REF_FIELDS:
            raise ValueError("Unrecognized relative reference field: "+str(field))
        if value.startswith("//"):
            raise ValueError("Protocol-relative reference requires review")
        raw,sep,suffix=value.partition(";md5;")
        target=urljoin(base,raw)
        if not public_url(target,True):
            raise ValueError("Unsafe relative reference")
        return target+sep+suffix
    return value

def personalize(config,base,prefs):
    if not public_url(base,True) or urlsplit(base).query:
        raise ValueError("Use original effective HTTPS config URL, without query")
    if not isinstance(config,dict) or not isinstance(config.get("sites"),list) or "urls" in config:
        raise ValueError("Expected single warehouse")
    sites=config["sites"]
    if not all(isinstance(s,dict) and isinstance(s.get("key"),str) and s["key"] for s in sites):
        raise ValueError("Every site needs a stable key")
    by_key={s["key"]:s for s in sites}
    if len(by_key)!=len(sites):
        raise ValueError("Duplicate site key")
    approved=prefs.get("approved_keys",[])
    if not isinstance(approved,list) or not approved or len(set(approved))!=len(approved):
        raise ValueError("Explicit reviewed site keys are required")
    if any(k not in by_key for k in approved):
        raise ValueError("Reviewed keys no longer present")
    if not isinstance(prefs.get("authorization"),str) or not prefs["authorization"].strip():
        raise ValueError("Document actual permission before exporting")
    if prefs.get("dependencies_reviewed") is not True:
        raise ValueError("Review all retained dependencies before exporting")
    hide=set(prefs.get("hide",[]))
    priority=prefs.get("priority",[])
    names=prefs.get("rename",{})
    search=prefs.get("search_keys")
    chosen=[k for k in approved if k not in hide]
    if not chosen: raise ValueError("Refusing empty warehouse")
    if len(set(priority))!=len(priority) or any(k not in chosen for k in priority):
        raise ValueError("Invalid priority keys")
    order=priority+[k for k in chosen if k not in priority]
    if search is not None and any(k not in chosen for k in search):
        raise ValueError("Unknown search key")
    result=copy.deepcopy(config)
    result.pop("lives",None)
    result["sites"]=[]
    for k in order:
        s=copy.deepcopy(by_key[k])
        if k in names:
            if not isinstance(names[k],str) or not names[k].strip():
                raise ValueError("Empty replacement name")
            s["name"]=names[k].strip()
        if search is not None:
            if k not in search:
                s["searchable"]=0
                s["quickSearch"]=0
            # Never force-enable unsupported search features.
        result["sites"].append(s)
    return relocate(result,base)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("snapshot",type=Path)
    p.add_argument("--base-url",required=True)
    p.add_argument("--preferences",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    config=parse_config(read_limited(a.snapshot).decode("utf-8-sig"))
    prefs=json.loads(read_limited(a.preferences).decode("utf-8-sig"))
    output=personalize(config,a.base_url,prefs)
    with a.output.open("x",encoding="utf-8") as f:
        json.dump(output,f,ensure_ascii=False,indent=2)
        f.write("\n")
    print("Local output:",len(output["sites"]),"reviewed sites")

if __name__=="__main__": main()
