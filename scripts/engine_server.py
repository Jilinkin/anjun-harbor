"""Single-warehouse local demonstration. No upstream network requests."""
import argparse
import ipaddress
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import parse_qs,urlsplit
from pathlib import Path
from harbor_engine import Catalog,CmsSnapshotAdapter

ROOT=Path(__file__).resolve().parent.parent

def demo():
    # Existing CC BY 3.0 movie metadata; no third-party code imported.
    adapters=[]
    for slug in ("animation","scifi"):
        data=json.loads((ROOT/"smoke"/(slug+"-data.json")).read_text(encoding="utf-8"))
        adapters.append(CmsSnapshotAdapter(slug,data,"CC BY 3.0; see original project credits in description."))
    return Catalog(adapters)

def route(path,base,catalog):
    u=urlsplit(path)
    if u.path=="/config.json":
        return {"sites":[{"key":"harbor_engine","name":"Harbor Engine","type":1,"api":base+"/api","searchable":1,"quickSearch":1}]}
    if u.path=="/api":
        return catalog.cms(parse_qs(u.query,max_num_fields=32))
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--host",default="127.0.0.1")
    p.add_argument("--port",type=int,default=8898)
    p.add_argument("--allow-lan",action="store_true")
    a=p.parse_args()
    try:
        addr=ipaddress.IPv4Address(a.host)
        private=any(addr in ipaddress.IPv4Network(n) for n in ("10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"))
        if not (addr.is_loopback or (private and a.allow_lan)) or not 1024<=a.port<=65535:
            raise ValueError()
    except ValueError:
        p.error("Specify loopback or explicitly allow a private LAN address")
    catalog=demo()
    base=f"http://{addr}:{a.port}"
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                obj=route(self.path,base,catalog)
            except ValueError:
                self.send_error(400)
                return
            if obj is None:
                self.send_error(404)
                return
            body=json.dumps(obj,ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    print("Single warehouse:",base+"/config.json",flush=True)
    with ThreadingHTTPServer((str(addr),a.port),Handler) as s:
        s.serve_forever()

if __name__=="__main__":main()
