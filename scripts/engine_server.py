"""Single-warehouse gateway; network mode requires explicit opt-in."""
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
    mode=p.add_mutually_exclusive_group()
    mode.add_argument("--providers",type=Path)
    mode.add_argument("--rules",type=Path)
    mode.add_argument("--html-rules",type=Path)
    mode.add_argument("--mixed",type=Path)
    p.add_argument("--allow-network",action="store_true")
    p.add_argument("--dedupe-selection",type=Path)
    a=p.parse_args()
    if a.dedupe_selection and (not a.mixed or a.allow_network):
        p.error("Deduplication requires a local mixed snapshot manifest without network mode")
    try:
        addr=ipaddress.IPv4Address(a.host)
        private=any(addr in ipaddress.IPv4Network(n) for n in ("10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"))
        if not (addr.is_loopback or (private and a.allow_lan)) or not 1024<=a.port<=65535:
            raise ValueError()
    except ValueError:
        p.error("Specify loopback or explicitly allow a private LAN address")
    if a.providers:
        if not a.allow_network:
            p.error("--providers requires explicit --allow-network")
        from engine_network import load_network
        from audit_dependencies import read_limited
        catalog,status=load_network(json.loads(read_limited(a.providers).decode("utf-8-sig")))
        print(json.dumps(status,ensure_ascii=False),flush=True)
        if not catalog.records:
            p.error("No valid records from reviewed providers")
    elif a.rules:
        from engine_rules import load_rules
        catalog,status=load_rules(a.rules)
        print(json.dumps(status,ensure_ascii=False),flush=True)
        if not catalog.records:
            p.error("No valid records from reviewed snapshots")
    elif a.html_rules:
        from engine_html import load_html
        catalog,status=load_html(a.html_rules)
        print(json.dumps(status,ensure_ascii=False),flush=True)
        if not catalog.records:
            p.error("No valid records from reviewed HTML snapshots")
    elif a.mixed:
        from engine_registry import load_mixed
        catalog,status=load_mixed(a.mixed,a.allow_network)
        print(json.dumps(status,ensure_ascii=False),flush=True)
        if not catalog.records:
            p.error("No valid records from reviewed mixed providers")
        if a.dedupe_selection:
            if any(s["status"]!="ok" for s in status):
                p.error("Incomplete catalog; repair failed providers")
            from engine_dedupe import apply
            from audit_dependencies import read_limited
            catalog,history=apply(catalog,json.loads(read_limited(a.dedupe_selection).decode("utf-8-sig")))
            print(json.dumps(history,ensure_ascii=False),flush=True)
    else:
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
