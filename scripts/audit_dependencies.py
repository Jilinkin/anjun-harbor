"""Static inventory of explicitly supplied, authorized TVBox configurations.
No downloading, archive extraction, script execution, or publishing.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urljoin, unquote

MAX_BYTES = 8 * 1024 * 1024
MAX_DEPS = 2000
FIELDS = {"spider", "jar", "api", "ext", "script", "rule", "rules"}
SUFFIXES = {".jar", ".js", ".mjs", ".json", ".py", ".txt", ".wasm", ".zip"}
EXECUTABLE = {".jar", ".js", ".mjs", ".py", ".wasm", ".zip"}

def read_limited(path):
    with path.open("rb") as f:
        data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("File exceeds 8 MiB audit limit")
    return data

def classify(value, field):
    value = value.strip()
    if not value or len(value) > 4096 or value.startswith(("csp_", "clan://", "file://", "data:")):
        return None
    raw, _, digest = value.partition(";md5;")
    try:
        u = urlsplit(raw)
    except ValueError:
        return None
    suffix = Path(u.path).suffix.lower()
    explicit_path = raw.startswith(("./", "../", "/"))
    if field == "api" and suffix not in EXECUTABLE and not explicit_path:
        return None
    if suffix not in SUFFIXES and not (field in {"spider", "jar", "script"} and (u.scheme in {"http", "https"} or explicit_path)):
        return None
    return raw, digest or None, suffix

def redact_url(value):
    u = urlsplit(value)
    # Do not echo credentials or query values in reports.
    return u._replace(netloc=u.hostname or "", query="", fragment="").geturl()

def entry(raw, digest, suffix, location, root, base):
    result = {"location": location, "kind": suffix.lstrip(".") or "unknown",
              "executable_or_archive": suffix in EXECUTABLE, "status": "review_required",
              "reference": "[redacted]" if "?" in raw or "#" in raw else raw}
    try:
        u = urlsplit(raw)
        if u.scheme or u.netloc:
            result["reference"] = redact_url(raw)
            result["status"] = "remote_unverified" if u.scheme == "https" and u.hostname and not u.username and not u.password and not u.query and not u.fragment else "unsupported_remote"
            return result
        if u.query or u.fragment:
            result["status"] = "unsupported_reference"
            return result
        decoded = unquote(u.path)
        if "\\" in decoded or "\x00" in decoded or decoded.startswith("/") or ":" in decoded:
            result["status"] = "unsafe_path"
            return result
        target = (root / decoded).resolve()
        if not target.is_relative_to(root):
            result["status"] = "outside_root"
            return result
        if base:
            result["resolved_url"] = redact_url(urljoin(base, raw))
        if not target.is_file():
            result["status"] = "local_missing"
            return result
        data = read_limited(target)
        result["size"] = len(data)
        result["sha256"] = hashlib.sha256(data).hexdigest()
        if digest:
            if not re.fullmatch(r"[0-9a-fA-F]{32}", digest):
                result["status"] = "invalid_md5"
                return result
            result["declared_md5_matches"] = hashlib.md5(data, usedforsecurity=False).hexdigest() == digest.lower()
            if not result["declared_md5_matches"]:
                result["status"] = "hash_mismatch"
                return result
        result["status"] = "local_hashed"
    except (ValueError, OSError, RuntimeError):
        result["status"] = "unreadable_or_invalid"
    return result

def audit(config, root, base=None):
    if not isinstance(config, dict) or not isinstance(config.get("sites"), list):
        raise ValueError("Expected strict JSON object with sites list")
    if base:
        u = urlsplit(base)
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError("Base must be a public HTTPS configuration URL without credentials")
    root = Path(root).resolve()
    refs, skipped = [], 0
    def walk(node, loc, field=None, depth=0):
        nonlocal skipped
        if depth > 32:
            raise ValueError("Configuration nesting exceeds limit")
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{loc}.{k}", k, depth + 1)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{loc}[{i}]", field, depth + 1)
        elif isinstance(node, str) and field in FIELDS:
            candidate = classify(node, field)
            if candidate:
                if len(refs) >= MAX_DEPS:
                    raise ValueError("Too many dependency references")
                refs.append(entry(*candidate, loc, root, base))
            elif field in {"spider", "jar", "script", "ext"} and node.strip():
                skipped += 1
    for k in ("spider", "jar", "sites"):
        if k in config:
            walk(config[k], k, k)
    by_name = {}
    for i, ref in enumerate(refs):
        name = Path(urlsplit(ref["reference"]).path).name
        if name and name != "[redacted]":
            by_name.setdefault(name, []).append(i)
    conflicts = []
    for name, indices in by_name.items():
        distinct = {refs[i].get("sha256") or refs[i].get("resolved_url") or refs[i]["reference"] for i in indices}
        if len(distinct) > 1:
            conflicts.append({"basename": name, "references": indices})
    return {"version": 1, "scope": "Static inventory only; no code executed or published",
            "sites": len(config["sites"]), "type3_sites": sum(isinstance(s, dict) and s.get("type") == 3 for s in config["sites"]),
            "unclassified_reference_fields": skipped, "dependencies": refs, "possible_name_conflicts": conflicts}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("config", type=Path)
    p.add_argument("--base-url")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    source = args.config.resolve()
    target = args.output.resolve()
    if target == source:
        p.error("Output must differ from source")
    config = json.loads(read_limited(source).decode("utf-8-sig"))
    result = audit(config, source.parent, args.base_url)
    with target.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(result['dependencies'])} dependency references; review required")

if __name__ == "__main__":
    main()
