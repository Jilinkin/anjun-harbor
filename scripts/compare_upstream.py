"""Compare authorized local upstream snapshots without altering the catalog."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_dependencies import read_limited

MAX_SITES = 5000

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()

def snapshot(config):
    if not isinstance(config, dict) or not isinstance(config.get("sites"), list):
        raise ValueError("Expected strict JSON object with sites array")
    if len(config["sites"]) > MAX_SITES:
        raise ValueError("Too many sites")
    result = {}
    for s in config["sites"]:
        if not isinstance(s, dict) or not isinstance(s.get("key"), str) or not s["key"].strip():
            raise ValueError("Every site requires a nonempty stable key")
        k = s["key"]
        if k in result:
            raise ValueError("Duplicate site key; resolve before comparing")
        result[k] = s
    return result

def fields_changed(old, new):
    return sorted(k for k in old.keys() | new.keys() if k not in old or k not in new or canonical(old[k]) != canonical(new[k]))

def compare(old, new):
    a, b = snapshot(old), snapshot(new)
    added = [{"key": k, "type": b[k].get("type"), "fingerprint": fingerprint(b[k])} for k in b if k not in a]
    removed = [{"key": k, "type": a[k].get("type"), "fingerprint": fingerprint(a[k])} for k in a if k not in b]
    changed, unchanged = [], 0
    for k in b:
        if k not in a:
            continue
        fields = fields_changed(a[k], b[k])
        if fields:
            changed.append({"key": k, "fields": fields, "before": fingerprint(a[k]), "after": fingerprint(b[k]),
                            "dependency_review": bool(set(fields) & {"api", "ext", "jar", "spider", "script", "rule", "rules", "type"})})
        else:
            unchanged += 1
    top_fields = fields_changed({k:v for k,v in old.items() if k != "sites"},
                                {k:v for k,v in new.items() if k != "sites"})
    return {"version":1, "scope":"Local snapshot comparison; no automatic catalog mutation",
            "before":fingerprint(old), "after":fingerprint(new),
            "summary":{"added":len(added), "removed":len(removed), "changed":len(changed), "unchanged":unchanged},
            "reordered":[k for k in a if k in b] != [k for k in b if k in a],
            "top_level_fields":top_fields,
            "global_dependency_review":bool(set(top_fields)&{"spider","jar","script","rules","parses"}),
            "added":added, "removed":removed, "changed":changed}

def load(path):
    return json.loads(read_limited(path).decode("utf-8-sig"))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = compare(load(args.before), load(args.after))
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(report["summary"]))

if __name__ == "__main__":
    main()
