"""Private, read-only LAN CMS for a folder of media you may use."""
import argparse
import hashlib
import ipaddress
import json
import os
import re
import secrets
import stat
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

FORMATS={".mp4":"video/mp4",".m4v":"video/mp4",".mkv":"video/x-matroska",
         ".webm":"video/webm",".mov":"video/quicktime"}
MAX_FILES=20000
PAGE=30

def ident(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]

def scan(root):
    root=Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Select a dedicated media directory")
    groups={}
    files={}
    for folder,dirs,names in os.walk(root,followlinks=False):
        folder=Path(folder)
        dirs[:]=sorted(d for d in dirs if not d.startswith(".") and not (folder/d).is_symlink())
        for name in sorted(names):
            path=folder/name
            if name.startswith(".") or path.suffix.lower() not in FORMATS or path.is_symlink():
                continue
            info=path.stat()
            if not stat.S_ISREG(info.st_mode) or not info.st_size:
                continue
            relative=path.relative_to(root)
            category=relative.parts[0] if len(relative.parts)>1 else "未分类"
            gid=ident(category)
            mid=ident(relative.as_posix())
            groups.setdefault(gid,{"name":category,"ids":[]})["ids"].append(mid)
            if mid in files:
                raise ValueError("Duplicate media ID")
            files[mid]={"path":path,"name":path.stem,"gid":gid,"dev":info.st_dev,"inode":info.st_ino}
            if len(files)>MAX_FILES:
                raise ValueError("Media library exceeds 20,000 files")
    return groups,files

def cms(gid,query,groups,files,base):
    group=groups[gid]
    ids=group["ids"]
    requested=query.get("ids",[""])[0]
    if requested:
        wanted=set(requested.split(","))
        ids=[i for i in ids if i in wanted]
    if query.get("t",[""])[0] not in ("","1"):
        ids=[]
    keyword=query.get("wd",[""])[0].strip().casefold()
    if keyword:
        ids=[i for i in ids if keyword in files[i]["name"].casefold()]
    try:
        page=max(1,int(query.get("pg",["1"])[0]))
    except ValueError:
        page=1
    total=len(ids)
    rows=[]
    for mid in ids[(page-1)*PAGE:page*PAGE]:
        f=files[mid]
        rows.append({"vod_id":mid,"type_id":"1","type_name":group["name"],"vod_name":f["name"],
                     "vod_remarks":"家庭局域网","vod_play_from":"local",
                     "vod_play_url":"正片$"+base+"/media/"+mid+f["path"].suffix.lower()})
    return {"code":1,"msg":"ok","page":page,"pagecount":(total+PAGE-1)//PAGE,
            "limit":PAGE,"total":total,"class":[{"type_id":"1","type_name":group["name"]}],"list":rows}

def route(path,base,groups,files):
    u=urlsplit(path)
    if u.path=="/index.json":
        return {"urls":[{"name":"Harbor · "+g["name"],"url":base+"/warehouse/"+gid+".json"} for gid,g in groups.items()]}
    for gid,g in groups.items():
        if u.path=="/warehouse/"+gid+".json":
            return {"sites":[{"key":"local_"+gid,"name":g["name"],"type":1,"api":base+"/api/"+gid,"searchable":1,"quickSearch":1}]}
        if u.path=="/api/"+gid:
            return cms(gid,parse_qs(u.query,max_num_fields=32),groups,files,base)
    return None

def byte_range(header,size):
    if not header:
        return 0,size-1,False
    match=re.fullmatch(r"bytes=(\d*)-(\d*)",header)
    if not match or size<=0:
        raise ValueError("Unsupported range")
    a,b=match.groups()
    if not a:
        count=int(b or "0")
        if count<=0:
            raise ValueError("Invalid suffix")
        return max(0,size-count),size-1,True
    start=int(a)
    end=min(int(b),size-1) if b else size-1
    if start>=size or end<start:
        raise ValueError("Unsatisfiable range")
    return start,end,True

def open_media(root,record):
    path=record["path"]
    if path.resolve()!=path or not path.is_relative_to(root):
        raise ValueError("Path changed")
    fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_NONBLOCK",0))
    stream=os.fdopen(fd,"rb")
    info=os.fstat(stream.fileno())
    if not stat.S_ISREG(info.st_mode) or (info.st_dev,info.st_ino)!=(record["dev"],record["inode"]):
        stream.close()
        raise ValueError("File changed; restart to rescan")
    return stream,info.st_size

def handler(root,groups,files,base,token):
    prefix="/"+token
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass # Never write token, search or file paths to logs.
        def do_HEAD(self):
            self.respond(False)
        def do_GET(self):
            self.respond(True)
        def respond(self,send_body):
            u=urlsplit(self.path)
            if not u.path.startswith(prefix+"/"):
                self.send_error(404)
                return
            sub=u.path[len(prefix):]
            if sub.startswith("/media/"):
                m=re.fullmatch(r"/media/([a-f0-9]{24})(\.[a-z0-9]+)",sub)
                if not m or m[1] not in files or files[m[1]]["path"].suffix.lower()!=m[2]:
                    self.send_error(404)
                    return
                try:
                    stream,size=open_media(root,files[m[1]])
                except (ValueError,OSError):
                    self.send_error(404)
                    return
                with stream:
                    try:
                        start,end,partial=byte_range(self.headers.get("Range"),size)
                    except ValueError:
                        self.send_response(416)
                        self.send_header("Content-Range",f"bytes */{size}")
                        self.send_header("Content-Length","0")
                        self.end_headers()
                        return
                    self.send_response(206 if partial else 200)
                    self.send_header("Content-Type",FORMATS[m[2]])
                    self.send_header("Accept-Ranges","bytes")
                    self.send_header("Content-Length",str(end-start+1))
                    self.send_header("Cache-Control","private, no-store")
                    if partial:
                        self.send_header("Content-Range",f"bytes {start}-{end}/{size}")
                    self.end_headers()
                    if send_body:
                        stream.seek(start)
                        remaining=end-start+1
                        try:
                            while remaining:
                                block=stream.read(min(65536,remaining))
                                if not block:
                                    break
                                self.wfile.write(block)
                                remaining-=len(block)
                        except (BrokenPipeError,ConnectionResetError):
                            pass
                return
            try:
                body=route(sub+("?" + u.query if u.query else ""),base,groups,files)
            except ValueError:
                self.send_error(400)
                return
            if body is None:
                self.send_error(404)
                return
            payload=json.dumps(body,ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Cache-Control","private, no-store")
            self.send_header("Content-Length",str(len(payload)))
            self.end_headers()
            if send_body:
                self.wfile.write(payload)
    return Handler

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--media-root",required=True,type=Path)
    p.add_argument("--host",default="127.0.0.1")
    p.add_argument("--port",type=int,default=8900)
    p.add_argument("--allow-lan",action="store_true")
    args=p.parse_args()
    try:
        addr=ipaddress.IPv4Address(args.host)
        lan=any(addr in ipaddress.IPv4Network(n) for n in ("192.168.0.0/16","10.0.0.0/8","172.16.0.0/12"))
        if not (addr.is_loopback or (lan and args.allow_lan)) or not 1024<=args.port<=65535:
            raise ValueError()
    except ValueError:
        p.error("Use loopback or a specific private LAN IPv4 with --allow-lan")
    root=args.media_root.resolve(strict=True)
    groups,files=scan(root)
    token=secrets.token_urlsafe(24)
    base=f"http://{addr}:{args.port}/{token}"
    print(f"{len(files)} files, {len(groups)} warehouses",flush=True)
    print("Private subscription (changes on restart): "+base+"/index.json",flush=True)
    with ThreadingHTTPServer((str(addr),args.port),handler(root,groups,files,base,token)) as service:
        service.serve_forever()

if __name__=="__main__":
    main()
