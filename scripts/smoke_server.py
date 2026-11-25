"""Local, read-only CMS compatibility test for the two open movie fixtures."""
import argparse
import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from build import ROOT

SLUGS = ("animation", "scifi")

def fixture(slug):
    if slug not in SLUGS:
        raise ValueError("Unknown fixture")
    return json.loads((ROOT / "smoke" / (slug + "-data.json")).read_text(encoding="utf-8"))

def cms(slug, query):
    data = fixture(slug)
    rows = data["list"]
    ids = set(query.get("ids", [""])[0].split(","))
    if ids != {""}:
        rows = [v for v in rows if str(v["vod_id"]) in ids]
    category = query.get("t", [""])[0]
    if category:
        rows = [v for v in rows if str(v["type_id"]) == category]
    keyword = query.get("wd", [""])[0].strip().casefold()
    if keyword:
        rows = [v for v in rows if keyword in v["vod_name"].casefold()]
    try:
        page = max(1, int(query.get("pg", ["1"])[0]))
    except ValueError:
        page = 1
    data["total"] = len(rows)
    data["pagecount"] = 1 if rows else 0
    data["page"] = page
    data["list"] = rows if page == 1 else []
    return data

def route(path, base):
    u = urlsplit(path)
    if u.path == "/index.json":
        return {"urls":[{"name":"Harbor · "+fixture(s)["class"][0]["type_name"],"url":base+"/warehouse/"+s+".json"} for s in SLUGS]}
    for slug in SLUGS:
        if u.path == "/warehouse/"+slug+".json":
            return {"sites":[{"key":"harbor_"+slug,"name":fixture(slug)["class"][0]["type_name"],"type":1,
                              "api":base+"/api/"+slug,"searchable":1,"quickSearch":1}]}
        if u.path == "/api/"+slug:
            return cms(slug,parse_qs(u.query, max_num_fields=32))
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--host",default="127.0.0.1",help="Local IPv4 address, or explicitly selected LAN interface")
    p.add_argument("--port",type=int,default=8899)
    args=p.parse_args()
    try:
        addr=ipaddress.IPv4Address(args.host)
        if not (addr.is_loopback or addr in ipaddress.IPv4Network("192.168.0.0/16") or addr in ipaddress.IPv4Network("10.0.0.0/8") or addr in ipaddress.IPv4Network("172.16.0.0/12")):
            raise ValueError()
        if not 1024<=args.port<=65535:
            raise ValueError()
    except ValueError:
        p.error("Use loopback or a specific RFC1918 LAN IPv4 address and port 1024-65535")
    base=f"http://{addr}:{args.port}"
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                body=route(self.path,base)
            except ValueError:
                self.send_error(400)
                return
            if body is None:
                self.send_error(404)
                return
            data=json.dumps(body,ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            self.send_header("Cache-Control","no-store")
            self.end_headers()
            self.wfile.write(data)
    print("Local test subscription:",base+"/index.json",flush=True)
    with ThreadingHTTPServer((str(addr),args.port),Handler) as server:
        server.serve_forever()

if __name__=="__main__":
    main()
