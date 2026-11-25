"""Validate a manually maintained multi-repository list and check reachability."""
import concurrent.futures
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 8 * 1024 * 1024

def load_sources():
    raw = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("urls"), list):
        raise ValueError("sources.json must contain a urls array")
    seen, entries = set(), []
    for row in raw["urls"]:
        name, url = row["name"].strip(), row["url"].strip()
        parsed = urlsplit(url)
        if not name or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Each source needs a name and an HTTPS URL without credentials")
        if url not in seen:
            seen.add(url)
            entries.append({"name": name, "url": url})
    if not entries:
        raise ValueError("Refusing to publish an empty index")
    return entries

def check(row):
    result = {"name": row["name"], "url": row["url"]}
    try:
        req = Request(row["url"], headers={"User-Agent": "AnjunHarbor/0.1"})
        with urlopen(req, timeout=15) as response:
            result["http_status"] = response.status
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            result["status"] = "too_large"
            return result
        try:
            obj = json.loads(data.decode("utf-8-sig"))
        except (UnicodeError, ValueError):
            result["status"] = "nonstandard_json_or_invalid"
            return result
        if isinstance(obj, dict) and isinstance(obj.get("sites"), list):
            result["status"] = "vod_config"
        elif isinstance(obj, dict) and isinstance(obj.get("urls"), list):
            result["status"] = "nested_multi_repository_review"
        else:
            result["status"] = "unrecognized_config"
    except Exception as exc:
        result["status"] = "unreachable"
        result["error_type"] = type(exc).__name__
    return result

def write_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)

def main():
    entries = load_sources()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        report = list(pool.map(check, entries))
    # Never delete an entry because of a temporary network or parsing failure.
    write_json(ROOT / "index.json", {"urls": entries})
    write_json(ROOT / "status.json", {"checks": report})
    for item in report:
        print(item["name"], item["status"])

if __name__ == "__main__":
    main()
