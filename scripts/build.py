"""Build independent, VOD-only configurations from a reviewed catalog."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/"
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

def label(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Missing name")
    return value.strip()

def build(data):
    if data.get("version") != 1 or not isinstance(data.get("groups"), list):
        raise ValueError("Expected catalog version 1 and groups")
    outputs, urls, seen_groups = {}, [], set()
    for group in data["groups"]:
        gid = group["id"]
        if not isinstance(gid, str) or not ID.fullmatch(gid) or gid in seen_groups:
            raise ValueError("Invalid or duplicate group ID")
        seen_groups.add(gid)
        name = label(group["name"])
        sites, seen_keys, seen_apis = [], set(), set()
        for item in group["sites"]:
            if item.get("approved") is not True:
                continue
            if not label(item.get("authorization")):
                raise ValueError("Authorization evidence required")
            key, api = item["key"], item["api"]
            if not isinstance(key, str) or not ID.fullmatch(key):
                raise ValueError("Invalid site ID")
            if type(item["type"]) is not int or item["type"] not in (0, 1):
                raise ValueError("Only independent type 0/1 APIs are supported")
            parsed = urlsplit(api)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                    or parsed.query or parsed.fragment or any(c.isspace() for c in api)):
                raise ValueError("API must be a public HTTPS URL without credentials/query/fragment")
            if key in seen_keys:
                raise ValueError("Duplicate site ID")
            if api in seen_apis:
                continue
            seen_keys.add(key)
            seen_apis.add(api)
            sites.append({"key": key, "name": label(item["name"]), "type": item["type"],
                          "api": api, "searchable": 1, "quickSearch": 1})
        if sites:
            path = f"warehouses/{gid}.json"
            outputs[path] = {"sites": sites}
            urls.append({"name": name, "url": BASE + path})
    return outputs, {"urls": urls}

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    data = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    outputs, index = build(data)
    print(f"{len(outputs)} nonempty independent warehouses")
    if not args.publish:
        return
    for path, config in outputs.items():
        write(ROOT / path, config)
    if index["urls"]:
        write(ROOT / "index.json", index)
    else:
        # Restore the explicitly preserved legacy entry rather than publish an empty list.
        write(ROOT / "index.json", json.loads((ROOT / "legacy.json").read_text(encoding="utf-8")))
    for path in (ROOT / "warehouses").glob("*.json"):
        if str(path.relative_to(ROOT)) not in outputs:
            path.unlink()

if __name__ == "__main__":
    main()
