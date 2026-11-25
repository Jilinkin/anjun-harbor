"""Opt-in HTTPS metadata checks. Never fetch or play a media stream."""
import concurrent.futures
import http.client
import ipaddress
import json
import socket
import ssl
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlsplit

from build import ROOT, build, write

LIMIT = 512 * 1024
MAX_PROBES = 24
TIMEOUT = 5

def public_ip(host, port):
    addresses = [a[4][0] for a in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)]
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise ValueError("Non-public address")
    return addresses[0]

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, port, ip):
        super().__init__(host, port, timeout=TIMEOUT, context=ssl.create_default_context())
        self.ip = ip

    def connect(self):
        sock = socket.create_connection((self.ip, self.port), timeout=TIMEOUT)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise

def inspect_body(data, kind):
    if kind == 1:
        obj = json.loads(data.decode("utf-8-sig"))
        if not isinstance(obj, dict) or not isinstance(obj.get("list"), list):
            return None
        return len(obj["list"])
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        return None
    root = ET.fromstring(data)
    items = root.find("list")
    if items is None and root.tag == "list":
        items = root
    return None if items is None else len(items.findall("video"))

def probe(site):
    started = time.monotonic()
    result = {"status": "unreachable", "score": 0}
    conn = None
    try:
        u = urlsplit(site["api"])
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment or u.port not in (None, 443):
            result["status"] = "unsupported_url"
            return result
        ip = public_ip(u.hostname, 443)
        conn = PinnedHTTPS(u.hostname, 443, ip)
        conn.request("GET", (u.path or "/") + "?ac=list", headers={"User-Agent":"AnjunHarbor/0.3","Accept-Encoding":"identity"})
        response = conn.getresponse()
        result["http_status"] = response.status
        if not 200 <= response.status < 300:
            result["status"] = "http_error"
            return result
        result["score"] = 20
        chunks, size = [], 0
        while True:
            if time.monotonic() - started > 15:
                raise TimeoutError("Probe deadline")
            chunk = response.read1(min(32768, LIMIT + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > LIMIT:
                result["status"] = "response_too_large"
                return result
        try:
            count = inspect_body(b"".join(chunks), site["type"])
        except (ValueError, UnicodeError, ET.ParseError):
            count = None
        if count is None:
            result["status"] = "unrecognized_metadata"
            return result
        result["status"] = "metadata_ok" if count else "metadata_empty"
        result["items_on_page"] = count
        result["score"] += 40 + (20 if count else 0)
        seconds = time.monotonic() - started
        result["score"] += 20 if seconds <= 2 else 10 if seconds <= 5 else 0
    except (OSError, ValueError, http.client.HTTPException):
        result["status"] = "unreachable"
        result["score"] = 0
    finally:
        if conn:
            conn.close()
        result["elapsed_ms"] = round((time.monotonic() - started) * 1000)
    return result

def report(catalog, checker=probe):
    outputs, _ = build(catalog)
    published = {(path.split("/")[-1][:-5], s["key"]) for path, config in outputs.items() for s in config["sites"]}
    entries, targets = [], {}
    for group in catalog["groups"]:
        for site in group["sites"]:
            key = (group["id"], site["key"])
            row = {"group": key[0], "key": key[1], "api": site["api"],
                   "status": "not_published" if key not in published else "not_requested", "score": None}
            entries.append(row)
            if key in published and site.get("probe") is True:
                signature = (site["api"], site["type"])
                targets.setdefault(signature, (site, []))[1].append(row)
    selected = list(targets.values())[:MAX_PROBES]
    for _, rows in list(targets.values())[MAX_PROBES:]:
        for row in rows:
            row["status"] = "deferred_limit"
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for (_, rows), result in zip(selected, executor.map(checker, (site for site, _ in selected))):
            for row in rows:
                row.update(result)
    return {"version": 1, "checked_at": datetime.now(timezone.utc).isoformat() if selected else None,
            "scope": "Metadata only; not playback or authorization", "checks": entries}

if __name__ == "__main__":
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    result = report(catalog)
    write(ROOT / "health.json", result)
    print(f"{len(result['checks'])} catalog entries recorded")
