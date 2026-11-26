"""Prepare RC4 binary and configs without modifying RC1 or RC2."""
import hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/"android-demo"/"rc4"
BUILD=ROOT/"engine"/"android"/"build"
BASE="https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/android-demo/rc4"
def main():
    if DEST.exists():raise ValueError("RC4 already published; use a new version")
    jar=(BUILD/"harbor.jar").read_bytes()
    digest=hashlib.sha256(jar).hexdigest()
    if digest!=(BUILD/"sha256.txt").read_text().split()[0]:raise ValueError("Checksum mismatch")
    DEST.mkdir(parents=True)
    (DEST/"harbor.jar").write_bytes(jar)
    (DEST/"media-probe.json").write_bytes((BUILD/"media-probe.json").read_bytes())
    (DEST/"sha256.txt").write_text(digest+"  harbor.jar\n")
    for name,prefix in (("config.json",""),("config-cn.json","https://gh-proxy.com/")):
        config={"spider":prefix+BASE+"/harbor.jar","sites":[{"key":"harbor_rc4","name":"Harbor RC4","type":3,"api":"csp_Harbor","searchable":1,"quickSearch":1,"filterable":0,"ext":"harbor-rc4-demo"}]}
        (DEST/name).write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (DEST/"provenance.json").write_text(json.dumps({"commit":os.environ["GITHUB_SHA"],"run":os.environ["GITHUB_RUN_ID"],"sha256":digest,"status":"device acceptance only","diagnostic_revision":"abefe13500b01b8a7474ad9d58271c49c9b070cb"},indent=2)+"\n")
if __name__=="__main__":main()
