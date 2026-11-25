"""Generate optional TVBox MD5 hints from verified release bytes, not proxy responses."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def encode(obj):
    return (json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

def generate(jar,expected_sha,version,ref):
    if not re.fullmatch(r"rc[1-9][0-9]*",version) or not re.fullmatch(r"[0-9a-f]{40}",ref):
        raise ValueError("Invalid release or Git revision")
    if not re.fullmatch(r"[0-9a-f]{64}",expected_sha) or hashlib.sha256(jar).hexdigest()!=expected_sha:
        raise ValueError("Trusted SHA-256 mismatch")
    md5=hashlib.md5(jar).hexdigest()
    base=f"https://raw.githubusercontent.com/Jilinkin/anjun-harbor/{ref}/android-demo/{version}/harbor.jar"
    out={"md5.txt":(md5+"  harbor.jar\n").encode(),
         "integrity.json":encode({"sha256":expected_sha,"md5":md5,"jar_revision":ref,
              "md5_role":"TVBox compatibility hint; verification depends on client",
              "security":"Not a signature; proxy can modify configuration and JAR"})}
    for name,prefix in (("config-md5.json",""),("config-cn-md5.json","https://gh-proxy.com/")):
        out[name]=encode({"spider":prefix+base+";md5;"+md5,"sites":[{
            "key":"harbor_"+version,"name":"Harbor "+version.upper(),"type":3,
            "api":"csp_Harbor","searchable":1,"quickSearch":1,"filterable":0}]})
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--version",required=True)
    parser.add_argument("--ref",required=True)
    parser.add_argument("--expected-sha256",required=True)
    a=parser.parse_args()
    if not re.fullmatch(r"rc[1-9][0-9]*",a.version):parser.error("Invalid version")
    dest=ROOT/"android-demo"/a.version
    data=(dest/"harbor.jar").read_bytes()
    outputs=generate(data,a.expected_sha256,a.version,a.ref)
    for name,content in outputs.items():
        path=dest/name
        if path.exists() and path.read_bytes()!=content:raise ValueError("Refuse to change existing "+name)
    for name,content in outputs.items():
        path=dest/name
        if not path.exists():
            with path.open("xb") as f:f.write(content)
if __name__=="__main__":main()
