"""Publish only the pinned original two-film demo, never the legacy subscriptions."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/"engine"/"android"/"build"
DEST=ROOT/"android-demo"/"rc1"
BASE="https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/android-demo/rc1"

def write_once(name,data):
    path=DEST/name
    if path.exists():
        if path.read_bytes()!=data:
            raise ValueError("RC1 is immutable; use a new version path")
    else:
        with path.open("xb") as f: f.write(data)

def encode(obj):
    return (json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

def main():
    jar=(BUILD/"harbor.jar").read_bytes()
    digest=hashlib.sha256(jar).hexdigest()
    checksum=(BUILD/"sha256.txt").read_text().split()[0]
    if checksum!=digest: raise ValueError("Checksum mismatch")
    config={"spider":BASE+"/harbor.jar","sites":[{"key":"harbor_demo","name":"Harbor RC1","type":3,"api":"csp_Harbor","searchable":1,"quickSearch":1,"filterable":0}]}
    provenance={"source_commit":"4878a659264c1ecb10e81f0d9213231838a1f01a","build_run":45579229576,"sha256":digest,"status":"device acceptance only","titles":["Big Buck Bunny","Tears of Steel"]}
    DEST.mkdir(parents=True,exist_ok=True)
    write_once("harbor.jar",jar)
    write_once("sha256.txt",(digest+"  harbor.jar\n").encode())
    write_once("config.json",encode(config))
    write_once("provenance.json",encode(provenance))

if __name__=="__main__": main()
