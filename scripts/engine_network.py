"""Bounded, opt-in metadata adapter for reviewed public HTTPS CMS services."""
import http.client
import json
import time
from urllib.parse import urlsplit,urlencode
from harbor_engine import SLUG,Catalog,CmsSnapshotAdapter
from probe import public_ip,PinnedHTTPS

MAX_BYTES=512*1024
MAX_PROVIDERS=8
MAX_PAGES=3
MAX_ROWS=300

def endpoint(value):
    if not isinstance(value,str) or len(value)>2048 or any(c.isspace() or ord(c)<32 for c in value):
        raise ValueError("Invalid endpoint")
    u=urlsplit(value)
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.query or u.fragment or u.port not in (None,443):
        raise ValueError("Expected public HTTPS endpoint without credentials or query")
    return u

def fetch_metadata(url,page):
    u=endpoint(url)
    if type(page) is not int or not 1<=page<=MAX_PAGES:
        raise ValueError("Page limit")
    ip=public_ip(u.hostname,443)
    conn=PinnedHTTPS(u.hostname,443,ip)
    started=time.monotonic()
    try:
        conn.request("GET",(u.path or "/")+"?"+urlencode({"ac":"detail","pg":page}),
                     headers={"Accept":"application/json","Accept-Encoding":"identity","User-Agent":"HarborEngine/2.1"})
        response=conn.getresponse()
        if response.status!=200 or response.getheader("Content-Encoding","identity").lower()!="identity":
            raise ValueError("Unsupported HTTP response")
        chunks=[];size=0
        while True:
            if time.monotonic()-started>15:
                raise TimeoutError("Metadata read deadline")
            chunk=response.read1(min(32768,MAX_BYTES+1-size))
            if not chunk: break
            size+=len(chunk)
            if size>MAX_BYTES: raise ValueError("Response limit")
            chunks.append(chunk)
        return json.loads(b"".join(chunks).decode("utf-8-sig"))
    finally:
        conn.close()

class CmsNetworkAdapter:
    def __init__(self,config,fetcher=fetch_metadata):
        self.provider=config["provider"]
        if not isinstance(self.provider,str) or not SLUG.fullmatch(self.provider):
            raise ValueError("Invalid provider")
        if config.get("approved") is not True or not isinstance(config.get("authorization"),str) or not config["authorization"].strip():
            raise ValueError("Explicit permission review required")
        self.authorization=config["authorization"]
        self.url=config["api"]
        endpoint(self.url)
        self.pages=config.get("pages",1)
        if type(self.pages) is not int or not 1<=self.pages<=MAX_PAGES:
            raise ValueError("Invalid page count")
        hosts=config.get("media_hosts")
        if not isinstance(hosts,list) or not hosts or len(hosts)>20 or any(not isinstance(h,str) or not h or h!=h.lower() or any(c in h for c in "/:@?# ") for h in hosts):
            raise ValueError("Explicit media host allowlist required")
        self.hosts=set(hosts)
        self.fetcher=fetcher
    def titles(self):
        total=0
        for page in range(1,self.pages+1):
            data=self.fetcher(self.url,page)
            if not isinstance(data,dict) or not isinstance(data.get("list"),list):
                raise ValueError("Unrecognized CMS response")
            rows=data["list"]
            total+=len(rows)
            if total>MAX_ROWS:
                raise ValueError("Provider row limit")
            for item in CmsSnapshotAdapter(self.provider,data,self.authorization).titles():
                if any(urlsplit(e.url).hostname not in self.hosts for e in item.episodes):
                    raise ValueError("Unreviewed media host")
                yield item
            if not rows: break
            count=data.get("pagecount")
            if type(count) is int and page>=count: break

class LoadedAdapter:
    def __init__(self,provider,rows):
        self.provider=provider
        self.rows=tuple(rows)
    def titles(self): return iter(self.rows)

def load_network(config,fetcher=fetch_metadata):
    if not isinstance(config,dict) or not isinstance(config.get("providers"),list) or not 1<=len(config["providers"])<=MAX_PROVIDERS:
        raise ValueError("Invalid provider list")
    # Validate every entry before any request. No implicit network opt-in.
    adapters=[CmsNetworkAdapter(row,fetcher) for row in config["providers"]]
    if len({a.provider for a in adapters})!=len(adapters):
        raise ValueError("Duplicate provider")
    loaded=[]; statuses=[]
    for adapter in adapters:
        try:
            rows=list(adapter.titles())
            # Validate duplicate IDs and all records before adding this provider.
            Catalog([LoadedAdapter(adapter.provider,rows)])
        except (OSError,ValueError,KeyError,TypeError,AttributeError,http.client.HTTPException):
            statuses.append({"provider":adapter.provider,"status":"failed","items":0})
            continue
        loaded.append(LoadedAdapter(adapter.provider,rows))
        statuses.append({"provider":adapter.provider,"status":"ok","items":len(rows)})
    return Catalog(loaded),statuses
