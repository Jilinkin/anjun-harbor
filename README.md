# Anjun Harbor · 0.4

Personal Resource Index / independent VOD configuration builder.

## Local manager

Download [manager.html](manager.html) and open it locally in a browser. Load [catalog.json](catalog.json) or import a strict JSON configuration as candidates. No imported code is executed. Review individual independent HTTPS type 0/1 APIs, record authorization, name and arrange them, then export catalog.json and replace the file in this repository. Never include private credentials in the public repository.

## Publication

The workflow tests and generates independent `warehouses/*.json` from approved entries only. It includes no live feeds or executable dependencies. The fixed entry remains:

https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/index.json

Empty groups are not published. With no approved entries, the existing legacy subscription remains active as a reversible fallback; it may include live TV. `legacy.json` preserves the original entry. Complex type 3/JAR/JS configurations require dependency review and a future controlled publishing system and are not imported as independent APIs. API reachability and playback are not established by format validation. This version does not test remote playback or automatically find resources.

## CLI

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build.py
python3 scripts/build.py --publish
```

Git history preserves prior versions. The daily workflow regenerates the catalog and validates configuration; it retries non-fast-forward push conflicts against the newest main without force-pushing. The old `sources.json` and `scripts/check.py` are retained as V0.1 reference only.

## Metadata health checks (0.3)

Enable probing explicitly per authorized entry in the manager or set `probe: true`. The daily job checks at most 24 distinct public HTTPS APIs with a bounded metadata-only list request; redirects are not followed, resolved non-public IPs are rejected and the connection is pinned to the resolved public IP. It does not fetch media or run third-party code. Results appear in `health.json`, which can be loaded into the manager.

Score: HTTP success 20, recognized metadata list 40, nonempty list 20, response speed up to 20. A score measures the observed metadata response only, not content legality, playback, picture quality or stability on the TV. Opt-out and unpublished entries have no score. No automatic deletion or reordering. Tests use mock data, not real providers.

Local optional check: `python3 scripts/probe.py`. Only enable network checks for APIs you have permission to query.

## Static dependency review (0.4)

Use Python 3.9+ locally with a configuration and dependency files you are authorized to inspect. No network access, code execution, extraction, or copying of dependencies is performed.

```sh
python3 scripts/audit_dependencies.py /path/to/config.json --base-url https://example.com/config.json --output dependency-report.json
```

The base URL is optional; the report inventories recognized JAR, JS, JSON and other file references, resolves relative paths, detects root escapes, reports missing local files, calculates SHA-256 for small local files, compares a supplied legacy MD5 value, and flags potential same-name conflicts. Remote references are unverified. Dynamic imports, inline or custom schemes and unknown formats are not comprehensively analyzed. A matching hash is not a safety or authorization verdict. Reports are local by default; review them for sensitive paths before sharing. Output must be a new file.

Load dependency-report.json into manager.html to inspect results. Type 3 publication remains disabled; the independent builder still publishes only reviewed type 0/1 entries. No third-party files are added to this repository.
