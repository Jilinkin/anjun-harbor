"""Stage immutable independent VOD releases and explicitly select production."""
import hashlib
import json
import re
from pathlib import Path

from build import ROOT, BASE, build, write

ID = re.compile(r"^[a-f0-9]{64}$")
WAREHOUSE = re.compile(r"^warehouses/[a-z0-9][a-z0-9_-]{0,63}\.json$")

def digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def materialize(payload):
    files, logical = payload["files"], payload["index"]
    if not isinstance(files, dict) or not files or not isinstance(logical.get("urls"), list):
        raise ValueError("Release must contain independent warehouses")
    if not all(WAREHOUSE.fullmatch(k) for k in files):
        raise ValueError("Invalid warehouse path")
    expected = {BASE + path for path in files}
    actual = [row["url"] for row in logical["urls"]]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Index and warehouse paths disagree")
    for config in files.values():
        if set(config) != {"sites"} or not isinstance(config["sites"], list) or not config["sites"]:
            raise ValueError("Invalid independent configuration")
        for site in config["sites"]:
            if set(site) != {"key","name","type","api","searchable","quickSearch"} or type(site["type"]) is not int or site["type"] not in (0,1):
                raise ValueError("Unexpected fields or unsupported site type")
    rid = digest(payload)
    index = {"urls":[{"name":row["name"],"url":BASE+"releases/"+rid+"/"+row["url"][len(BASE):]} for row in logical["urls"]]}
    return rid, index

def stage(root, catalog):
    files, logical = build(catalog)
    if not files:
        return None, {"urls":[]}
    payload = {"version":1,"files":files,"index":logical}
    rid, index = materialize(payload)
    folder = root/"releases"/rid
    manifest = {"id":rid,"payload":payload}
    expected = {"manifest.json":manifest,"index.json":index,**files}
    if folder.exists():
        for path,value in expected.items():
            if read(folder/path) != value:
                raise ValueError("Existing release was modified: "+rid)
    else:
        for path,value in expected.items():
            write(folder/path,value)
    return rid,index

def verify(root,rid):
    if not isinstance(rid,str) or not ID.fullmatch(rid):
        raise ValueError("Invalid release ID")
    folder = root/"releases"/rid
    manifest = read(folder/"manifest.json")
    payload = manifest["payload"]
    calculated,index = materialize(payload)
    if calculated != rid or manifest["id"] != rid or read(folder/"index.json") != index:
        raise ValueError("Release fingerprint or index mismatch")
    for path,value in payload["files"].items():
        if read(folder/path) != value:
            raise ValueError("Warehouse integrity mismatch")
    return index

def summary(before,after):
    a={row["url"]:row["name"] for row in before["urls"]}
    b={row["url"]:row["name"] for row in after["urls"]}
    return {"active_warehouses":len(a),"candidate_warehouses":len(b),
            "added_urls":len(b.keys()-a.keys()),"removed_urls":len(a.keys()-b.keys())}

def publish(root):
    catalog=read(root/"catalog.json")
    control=read(root/"release-control.json")
    if set(control)!={"version","active"} or control["version"]!=1:
        raise ValueError("Invalid release control")
    active=control["active"]
    # Check the explicit production selection before modifying any pointers.
    production=read(root/"legacy.json") if active=="legacy" else verify(root,active)
    candidate,test_index=stage(root,catalog)
    status={"version":1,"active":active,"candidate":candidate,
            "candidate_ready":candidate is not None,
            "comparison":summary(production,test_index)}
    write(root/"test.json",test_index)
    write(root/"index.json",production)
    write(root/"release-status.json",status)
    return status

if __name__=="__main__":
    print(json.dumps(publish(ROOT),ensure_ascii=False))
