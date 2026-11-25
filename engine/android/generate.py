"""Compile the bundled, reviewed open-film catalog into Java source.
No network requests, external source imports, or executable rules.
"""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent
def generate(data):
    if not isinstance(data,list) or not 1<=len(data)<=100:
        raise ValueError("Invalid catalog")
    ids=set();lines=[]
    for row in data:
        if not isinstance(row,dict) or set(row)!={"id","title","category","year","url","credit"}:
            raise ValueError("Invalid row")
        vals=[row[k] for k in ("id","title","category","year","url","credit")]
        if any(not isinstance(v,str) or not v or len(v)>2000 or any(ord(c)<32 for c in v) for v in vals):
            raise ValueError("Invalid field")
        if not re.fullmatch(r"[a-z0-9_-]{1,60}",row["id"]) or row["id"] in ids:
            raise ValueError("Invalid or duplicate identity")
        ids.add(row["id"])
        if row["category"] not in ("animation","scifi") or "CC BY 3.0" not in row["credit"]:
            raise ValueError("Unreviewed fixture")
        u=urlsplit(row["url"])
        if u.scheme!="https" or u.hostname!="storage.googleapis.com" or u.username or u.password or u.port not in (None,443) or u.query or u.fragment or not u.path.startswith("/gtv-videos-bucket/sample/"):
            raise ValueError("Unsupported fixture URL")
        lines.append("        {"+",".join(json.dumps(v,ensure_ascii=False) for v in vals)+"}")
    return "package com.github.catvod.spider;\nfinal class HarborData {\n    static final String[][] FILMS={\n"+",\n".join(lines)+"\n    };\n}\n"

if __name__=="__main__":
    target=ROOT/"build"/"generated"/"HarborData.java"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(generate(json.loads((ROOT/"catalog.json").read_text(encoding="utf-8"))),encoding="utf-8")
