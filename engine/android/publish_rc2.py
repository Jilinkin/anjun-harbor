"""Prepare immutable RC2 static demo using locally built original media and JAR."""
import hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/"android-demo"/"rc2"
BUILD=ROOT/"engine"/"android"/"build"
BASE="https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/android-demo/rc2"
PROXY="https://gh-proxy.com/"
def write_once(name,data):
    path=DEST/name
    if path.exists():
        if path.read_bytes()!=data: raise ValueError("RC2 already published with different bytes")
    else:
        with path.open("xb") as f:f.write(data)
def encode(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode()
def main():
    DEST.mkdir(parents=True,exist_ok=True)
    jar=(BUILD/"harbor.jar").read_bytes()
    digest=hashlib.sha256(jar).hexdigest()
    if digest!=(BUILD/"sha256.txt").read_text().split()[0]:raise ValueError("JAR checksum mismatch")
    for name in ("diagnostic.mp4","bunny.png","steel.png"):
        data=(BUILD/name).read_bytes()
        if not 0<len(data)<2*1024*1024:raise ValueError("Media size")
        write_once(name,data)
    write_once("harbor.jar",jar)
    write_once("sha256.txt",(digest+"  harbor.jar\n").encode())
    for name,prefix in (("config.json",""),("config-cn.json",PROXY)):
        config={"spider":prefix+BASE+"/harbor.jar","sites":[{"key":"harbor_rc2","name":"Harbor RC2","type":3,"api":"csp_Harbor","searchable":1,"quickSearch":1,"filterable":0}]}
        write_once(name,encode(config))
    write_once("provenance.json",encode({"commit":os.environ["GITHUB_SHA"],"run":os.environ["GITHUB_RUN_ID"],"sha256":digest,"status":"device acceptance only","diagnostic":"original generated color bars and test tone; not a film"}))
if __name__=="__main__":main()
