"""Local content-addressed catalog releases; explicit promotion and rollback."""
import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict
from pathlib import Path
from contextlib import contextmanager
from harbor_engine import Catalog,Title,Episode,SLUG,MAX_ITEMS
from engine_network import LoadedAdapter
from engine_registry import load_mixed
from engine_dedupe import apply as dedupe
from engine_preferences import apply as preferences,label,load_json

MAX_BYTES=16*1024*1024
ID=re.compile(r"^[0-9a-f]{64}$")

def encode(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def read(path):
    with Path(path).open("rb") as f: data=f.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES: raise ValueError("Release size limit")
    return data

def checksum(data):
    return hashlib.sha256(data).hexdigest()

def atomic(path,data,exclusive=False):
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".harbor-")
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        if exclusive:
            try: os.link(tmp,path)
            except FileExistsError:
                if read(path)!=data: raise ValueError("Existing release differs")
        else: os.replace(tmp,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def snapshot(catalog,name):
    if not catalog.records: raise ValueError("Empty release")
    return {"version":1,"warehouse_name":label(name),"providers":sorted(catalog.providers),
            "records":[asdict(t) for t in catalog.records.values()]}

def decode(data):
    obj=json.loads(data)
    if not isinstance(obj,dict) or set(obj)!={"version","warehouse_name","providers","records"} or type(obj["version"]) is not int or obj["version"]!=1:
        raise ValueError("Invalid release")
    name=label(obj["warehouse_name"])
    providers=obj["providers"];records=obj["records"]
    if not isinstance(providers,list) or any(not isinstance(p,str) or not SLUG.fullmatch(p) for p in providers) or len(set(providers))!=len(providers):
        raise ValueError("Invalid release providers")
    if not isinstance(records,list) or not 1<=len(records)<=MAX_ITEMS:
        raise ValueError("Invalid release records")
    rows={p:[] for p in providers};ordered=[]
    for row in records:
        if not isinstance(row,dict): raise ValueError("Invalid record")
        row=dict(row)
        episodes=row.pop("episodes")
        if not isinstance(episodes,list) or not 1<=len(episodes)<=1000: raise ValueError("Invalid episodes")
        title=Title(**row,episodes=tuple(Episode(**ep) for ep in episodes))
        if title.provider not in rows: raise ValueError("Unknown provider")
        rows[title.provider].append(title);ordered.append(title)
    cat=Catalog([LoadedAdapter(p,items) for p,items in rows.items()])
    cat.records={t.id:t for t in ordered}
    cat.categories={hashlib.sha256(t.category.encode()).hexdigest()[:16]:t.category for t in ordered}
    return cat,name

class Store:
    def __init__(self,root):
        self.root=Path(root)
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.snapshots=self.root/"snapshots"
        self.snapshots.mkdir(mode=0o700,exist_ok=True)
        self.pointer=self.root/"state.json"
    @contextmanager
    def lock(self):
        fd=os.open(self.root/".lock",os.O_CREAT|os.O_RDWR,0o600)
        with os.fdopen(fd,"r+") as f:
            fcntl.flock(f,fcntl.LOCK_EX)
            yield
    def state(self):
        if not self.pointer.exists():
            return {"version":1,"active":None,"candidate":None,"previous":None}
        state=json.loads(read(self.pointer))
        if not isinstance(state,dict) or set(state)!={"version","active","candidate","previous"} or state["version"]!=1:
            raise ValueError("Invalid release state")
        if any(x is not None and (not isinstance(x,str) or not ID.fullmatch(x)) for x in (state["active"],state["candidate"],state["previous"])):
            raise ValueError("Invalid release pointer")
        return state
    def get(self,rid):
        if not isinstance(rid,str) or not ID.fullmatch(rid): raise ValueError("Invalid release ID")
        data=read(self.snapshots/(rid+".json"))
        if checksum(data)!=rid: raise ValueError("Corrupt release")
        return decode(data)
    def write_state(self,state):
        atomic(self.pointer,encode(state))
    def stage(self,cat,name):
        data=encode(snapshot(cat,name))
        if len(data)>MAX_BYTES: raise ValueError("Release size limit")
        decode(data)
        rid=checksum(data)
        with self.lock():
            state=self.state()
            atomic(self.snapshots/(rid+".json"),data,True)
            state["candidate"]=rid
            self.write_state(state)
        return rid
    def promote(self,rid,expected_active):
        with self.lock():
            state=self.state()
            if state["active"]!=expected_active or state["candidate"]!=rid:
                raise ValueError("Release changed; review current state")
            self.get(rid)
            if rid!=state["active"]:
                state["previous"]=state["active"]
                state["active"]=rid
            self.write_state(state)
        return state
    def rollback(self,expected_active):
        with self.lock():
            state=self.state()
            if state["active"]!=expected_active or state["previous"] is None:
                raise ValueError("No matching rollback")
            self.get(state["previous"])
            state["active"],state["previous"]=state["previous"],state["active"]
            self.write_state(state)
        return state
    def channel(self,name):
        if name not in ("active","candidate"): raise ValueError("Unknown channel")
        rid=self.state()[name]
        if rid is None: raise ValueError("Channel not staged")
        return self.get(rid)

def compare(old,new):
    a,an=old;b,bn=new
    aa=a.records;bb=b.records
    common=set(aa)&set(bb)
    changed=sorted(k for k in common if aa[k]!=bb[k])
    return {"warehouse_name_changed":an!=bn,"added":sorted(set(bb)-set(aa)),
            "removed":sorted(set(aa)-set(bb)),"changed":changed,
            "order_changed":[k for k in aa if k in common]!=[k for k in bb if k in common]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--store",required=True,type=Path)
    sub=p.add_subparsers(dest="cmd",required=True)
    st=sub.add_parser("stage");st.add_argument("manifest",type=Path)
    st.add_argument("--dedupe-selection",type=Path);st.add_argument("--preferences",type=Path)
    sub.add_parser("status");sub.add_parser("diff")
    pr=sub.add_parser("promote");pr.add_argument("candidate");pr.add_argument("--expected-active",required=True)
    rb=sub.add_parser("rollback");rb.add_argument("--expected-active",required=True)
    a=p.parse_args();store=Store(a.store)
    if a.cmd=="stage":
        catalog,status=load_mixed(a.manifest)
        if any(s["status"]!="ok" for s in status): p.error("Incomplete catalog")
        name="Harbor"
        if a.dedupe_selection: catalog,_=dedupe(catalog,load_json(a.dedupe_selection))
        if a.preferences: catalog,name,_=preferences(catalog,load_json(a.preferences))
        result={"candidate":store.stage(catalog,name)}
    elif a.cmd=="status": result=store.state()
    elif a.cmd=="diff":
        state=store.state()
        result=compare(store.get(state["active"]),store.get(state["candidate"])) if state["active"] and state["candidate"] else {"note":"Both channels required for diff"}
    elif a.cmd=="promote": result=store.promote(a.candidate,None if a.expected_active=="none" else a.expected_active)
    else: result=store.rollback(a.expected_active)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
