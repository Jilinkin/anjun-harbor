# Anjun Harbor · 0.3

Personal Resource Index / independent VOD configuration builder.

## Local manager

Download [manager.html](manager.html) and open it locally in a browser. Load [catalog.json](catalog.json) or import a strict JSON configuration as candidates. No imported code is executed. Review individual independent HTTPS type 0/1 APIs, record authorization, name and arrange them, then export catalog.json and replace the file in this repository. Never include private credentials in the public repository.

## Publication

The workflow tests and generates independent `warehouses/*.json` from approved entries only. It includes no live feeds or executable dependencies. The fixed entry remains:

https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/index.json

Empty groups are not published. With no approved entries, the existing legacy subscription remains active as a reversible fallback; it may include live TV. `legacy.json` preserves the original entry. Complex type 3/JAR/JS configurations require a future dependency review system and are not imported as independent APIs. API reachability and playback are not established by format validation. This version does not test remote playback or automatically find resources.

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
