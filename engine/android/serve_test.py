"""Serve a verified Harbor demo JAR and a single-site test config on a trusted LAN."""
import argparse
import hashlib
import hmac
import io
import ipaddress
import json
import re
import secrets
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_JAR=2*1024*1024

def verified_jar(path,expected):
    if not isinstance(expected,str) or not re.fullmatch("[0-9a-fA-F]{64}",expected):
        raise ValueError("Supply the trusted CI SHA-256")
    with Path(path).open("rb") as f:
        data=f.read(MAX_JAR+1)
    if not data or len(data)>MAX_JAR:
        raise ValueError("Invalid artifact size")
    digest=hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(digest,expected.lower()):
        raise ValueError("SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        files=z.infolist()
        if len(files)>5 or any(i.filename not in {"META-INF/","META-INF/MANIFEST.MF","classes.dex"} for i in files):
            raise ValueError("Unexpected JAR contents")
        if len({i.filename for i in files})!=len(files):
            raise ValueError("Duplicate archive entry")
        dex=z.getinfo("classes.dex")
        if not 8<=dex.file_size<=MAX_JAR:
            raise ValueError("Invalid DEX size")
        with z.open(dex) as f:
            if f.read(4)!=b"dex\n": raise ValueError("Invalid DEX header")
    return data,digest

def validate_address(host,port,allow_lan=False):
    ip=ipaddress.IPv4Address(host)
    private=any(ip in ipaddress.IPv4Network(n) for n in ("10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"))
    if not (ip.is_loopback or (private and allow_lan)) or not 1024<=port<=65535:
        raise ValueError("Use loopback or explicit trusted private LAN IP")
    return str(ip)

def make_handler(base,token,data,digest):
    prefix="/"+token
    jar_path=prefix+"/harbor-"+digest[:16]+".jar"
    cfg={"spider":base+jar_path,"sites":[{"key":"harbor_demo","name":"Harbor Android Test","type":3,"api":"csp_Harbor","searchable":1,"quickSearch":1,"filterable":0}]}
    routes={prefix+"/config.json":("application/json; charset=utf-8",json.dumps(cfg,ensure_ascii=False).encode("utf-8")),
            jar_path:("application/java-archive",data),
            prefix+"/sha256.txt":("text/plain; charset=utf-8",(digest+"  harbor.jar\n").encode("ascii"))}
    class Handler(BaseHTTPRequestHandler):
        def serve(self,body):
            result=routes.get(self.path)
            if result is None:
                self.send_error(404)
                return
            kind,payload=result
            self.send_response(200)
            self.send_header("Content-Type",kind)
            self.send_header("Content-Length",str(len(payload)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.end_headers()
            if body: self.wfile.write(payload)
        def do_GET(self): self.serve(True)
        def do_HEAD(self): self.serve(False)
        def log_message(self,fmt,*args):
            # Do not log the unguessable test URL.
            pass
    return Handler,prefix+"/config.json"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--jar",type=Path,required=True)
    parser.add_argument("--sha256",required=True,help="Trusted CI checksum, 64 hex characters")
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=8897)
    parser.add_argument("--allow-lan",action="store_true")
    args=parser.parse_args()
    try:
        host=validate_address(args.host,args.port,args.allow_lan)
        data,digest=verified_jar(args.jar,args.sha256)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    base=f"http://{host}:{args.port}"
    handler,route=make_handler(base,secrets.token_urlsafe(24),data,digest)
    with ThreadingHTTPServer((host,args.port),handler) as server:
        print("Test subscription:",base+route,flush=True)
        print("Trusted LAN only; stop with Ctrl+C after acceptance.",flush=True)
        server.serve_forever()

if __name__=="__main__": main()
