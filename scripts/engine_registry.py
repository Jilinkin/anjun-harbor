"""Trusted built-in registry for mixed authorized snapshot/network adapters."""
import json
import http.client
from pathlib import Path
from urllib.parse import urlsplit
from harbor_engine import Catalog,CmsSnapshotAdapter,SLUG
from engine_network import CmsNetworkAdapter,LoadedAdapter,MAX_PROVIDERS,MAX_ROWS,fetch_metadata
from engine_rules import JsonRuleAdapter
from engine_html import HtmlRuleAdapter
from audit_dependencies import read_limited

KINDS=("cms-snapshot","cms-network","json-snapshot","html-snapshot")

def load_mixed(manifest_path,allow_network=False,fetcher=fetch_metadata):
    root=Path(manifest_path).resolve().parent
    def read(name):
        if not isinstance(name,str) or not name: raise ValueError("Invalid path")
        path=(root/name).resolve()
        if not path.is_relative_to(root): raise ValueError("Path outside manifest directory")
        return read_limited(path).decode("utf-8-sig")
    manifest=json.loads(read_limited(Path(manifest_path)).decode("utf-8-sig"))
    if not isinstance(manifest,dict) or set(manifest)!={"version","providers"} or type(manifest["version"]) is not int or manifest["version"]!=1:
        raise ValueError("Invalid manifest version")
    entries=manifest["providers"]
    if not isinstance(entries,list) or not 1<=len(entries)<=MAX_PROVIDERS: raise ValueError("Invalid provider count")
    prepared=[];seen=set()
    # Validate manifest and network permissions before requesting any network data.
    for row in entries:
        if not isinstance(row,dict): raise ValueError("Invalid provider entry")
        kind=row.get("kind")
        provider=row.get("provider")
        if kind not in KINDS or not isinstance(provider,str) or not SLUG.fullmatch(provider) or provider in seen:
            raise ValueError("Unknown adapter kind or duplicate provider")
        seen.add(provider)
        if row.get("approved") is not True or not isinstance(row.get("authorization"),str) or not row["authorization"].strip():
            raise ValueError("Explicit permission review required")
        common={"kind","provider","approved","authorization"}
        if kind=="cms-network":
            if not allow_network: raise ValueError("Network opt-in required")
            if set(row)-common-{"api","media_hosts","pages"}: raise ValueError("Unknown network option")
            adapter=CmsNetworkAdapter(row,fetcher)
            prepared.append((row,adapter))
        else:
            expected=common|({"snapshot","media_hosts"} if kind=="cms-snapshot" else {"snapshot","rule"})
            if set(row)!=expected: raise ValueError("Invalid snapshot options")
            prepared.append((row,None))
    loaded=[];statuses=[]
    for row,adapter in prepared:
        kind=row["kind"]; provider=row["provider"]
        try:
            if kind=="cms-snapshot":
                hosts=row["media_hosts"]
                if not isinstance(hosts,list) or not 1<=len(hosts)<=20 or any(not isinstance(h,str) or not h or h.lower()!=h or any(c in h for c in "/:@?# ") for h in hosts):
                    raise ValueError("Explicit media host allowlist required")
                data=json.loads(read(row["snapshot"]))
                if not isinstance(data,dict) or not isinstance(data.get("list"),list) or len(data["list"])>MAX_ROWS:
                    raise ValueError("Invalid CMS snapshot")
                adapter=CmsSnapshotAdapter(provider,data,row["authorization"])
            elif kind in ("json-snapshot","html-snapshot"):
                rule=json.loads(read(row["rule"]))
                if not isinstance(rule,dict) or rule.get("provider")!=provider or rule.get("approved") is not True or rule.get("authorization")!=row["authorization"]:
                    raise ValueError("Rule review identity mismatch")
                source=read(row["snapshot"])
                adapter=JsonRuleAdapter(rule,json.loads(source)) if kind=="json-snapshot" else HtmlRuleAdapter(rule,source)
            rows=list(adapter.titles())
            if kind=="cms-snapshot" and any(urlsplit(e.url).hostname not in hosts for t in rows for e in t.episodes):
                raise ValueError("Unreviewed media host")
            checked=LoadedAdapter(provider,rows)
            Catalog([checked])
        except (OSError,ValueError,KeyError,TypeError,AttributeError,SyntaxError,http.client.HTTPException):
            statuses.append({"provider":provider,"kind":kind,"status":"failed","items":0})
            continue
        loaded.append(checked)
        statuses.append({"provider":provider,"kind":kind,"status":"ok","items":len(rows)})
    return Catalog(loaded),statuses
