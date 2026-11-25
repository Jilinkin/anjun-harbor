"""Harbor Engine 2.0: normalized VOD model and offline adapter contract."""
from dataclasses import dataclass
from typing import Protocol, Iterable
from urllib.parse import urlsplit
import re
import hashlib

SLUG=re.compile(r"^[a-z][a-z0-9_-]{0,39}$")
MAX_ITEMS=20000

def text(value,limit=500):
    if not isinstance(value,str) or len(value)>limit or any(ord(c)<32 for c in value):
        raise ValueError("Invalid text field")
    return value

def media_url(value):
    value=text(value,4096)
    u=urlsplit(value)
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.fragment or any(c in value for c in "$#") or any(c.isspace() for c in value):
        raise ValueError("Expected explicit HTTPS media URL")
    return value

@dataclass(frozen=True)
class Episode:
    name: str
    url: str
    def __post_init__(self):
        if not text(self.name) or any(c in self.name for c in "$#"):
            raise ValueError("Invalid episode label")
        media_url(self.url)

@dataclass(frozen=True)
class Title:
    provider: str
    native_id: str
    name: str
    category: str
    year: str
    description: str
    episodes: tuple
    license_note: str
    def __post_init__(self):
        if not SLUG.fullmatch(self.provider) or not text(self.native_id) or not text(self.name) or not text(self.category):
            raise ValueError("Invalid title identity")
        text(self.year,20)
        text(self.description,16000)
        if not text(self.license_note,4000).strip():
            raise ValueError("Record actual authorization")
        if not isinstance(self.episodes,tuple) or not self.episodes or len(self.episodes)>1000 or not all(isinstance(x,Episode) for x in self.episodes):
            raise ValueError("Invalid episode list")
    @property
    def id(self):
        return self.provider+"-"+hashlib.sha256(self.native_id.encode()).hexdigest()[:24]

class Adapter(Protocol):
    """Trusted, locally installed implementation; never load code from a config URL."""
    provider: str
    def titles(self) -> Iterable[Title]: ...

class Catalog:
    def __init__(self,adapters):
        self.records={}
        self.providers=set()
        for adapter in adapters:
            if not SLUG.fullmatch(adapter.provider) or adapter.provider in self.providers:
                raise ValueError("Duplicate or invalid provider")
            self.providers.add(adapter.provider)
            for item in adapter.titles():
                if not isinstance(item,Title) or item.provider!=adapter.provider or item.id in self.records:
                    raise ValueError("Duplicate or invalid title")
                self.records[item.id]=item
                if len(self.records)>MAX_ITEMS:
                    raise ValueError("Catalog limit exceeded")
        self.categories={hashlib.sha256(x.category.encode()).hexdigest()[:16]:x.category for x in self.records.values()}
    def query(self,keyword="",category="",ids=(),page=1,limit=20):
        if type(page) is not int or type(limit) is not int or page<1 or page>100000 or not 1<=limit<=100:
            raise ValueError("Invalid pagination")
        keyword=text(keyword).casefold().strip()
        wanted=set(ids)
        rows=[x for x in self.records.values() if (not wanted or x.id in wanted) and
              (not category or self.categories.get(category)==x.category) and
              (not keyword or keyword in x.name.casefold())]
        total=len(rows)
        return rows[(page-1)*limit:page*limit],total
    def cms(self,params):
        page=int(params.get("pg",["1"])[0])
        ids=params.get("ids",[""])[0].split(",")
        rows,total=self.query(params.get("wd",[""])[0],params.get("t",[""])[0],tuple(x for x in ids if x),page)
        detail=params.get("ac",[""])[0] in ("detail","videolist")
        data=[]
        for x in rows:
            cat=hashlib.sha256(x.category.encode()).hexdigest()[:16]
            item={"vod_id":x.id,"vod_name":x.name,"type_id":cat,"type_name":x.category,
                  "vod_year":x.year,"vod_remarks":"授权资源"}
            if detail:
                item.update(vod_content=x.description+"\n"+x.license_note,
                            vod_play_from="harbor",vod_play_url="#".join(e.name+"$"+e.url for e in x.episodes))
            data.append(item)
        return {"code":1,"msg":"ok","page":page,"pagecount":(total+19)//20,"limit":20,
                "total":total,"class":[{"type_id":k,"type_name":v} for k,v in self.categories.items()],"list":data}

class CmsSnapshotAdapter:
    """Imports explicitly approved, local CMS-shaped metadata, not executable crawlers."""
    def __init__(self,provider,data,authorization):
        self.provider=provider
        self.data=data
        self.authorization=authorization
        if not isinstance(data,dict) or not isinstance(data.get("list"),list) or not isinstance(authorization,str) or not authorization.strip():
            raise ValueError("Invalid snapshot or missing permission")
    def titles(self):
        for row in self.data["list"]:
            # Only a single explicit direct-play line is supported in this first adapter.
            raw=row["vod_play_url"]
            if not isinstance(raw,str) or "$$$" in raw:
                raise ValueError("Multiple play lines require another adapter")
            episodes=[]
            for part in raw.split("#"):
                name,sep,url=part.partition("$")
                if not sep: raise ValueError("Invalid episode")
                episodes.append(Episode(name,url))
            yield Title(self.provider,str(row["vod_id"]),row["vod_name"],row["type_name"],
                        str(row.get("vod_year","")),row.get("vod_content","").replace("\n"," "),
                        tuple(episodes),self.authorization)
