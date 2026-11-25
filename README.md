# Anjun Harbor · 0.8

Personal Resource Index / independent VOD configuration builder.

## Local manager

Download [manager.html](manager.html) and open it locally in a browser. Load [catalog.json](catalog.json) or import a strict JSON configuration as candidates. No imported code is executed. Review individual independent HTTPS type 0/1 APIs, record authorization, name and arrange them, then export catalog.json and replace the file in this repository to stage a test release. Never include private credentials in the public repository.

## Publication

The workflow tests and stages immutable independent `releases/<id>/warehouses/*.json` from approved entries only. It includes no live feeds or executable dependencies. The fixed entry remains:

https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/index.json

Empty groups are not published. With no approved entries, the test index is empty and the selected production release remains unchanged. The initial legacy release may include live TV. `legacy.json` preserves the original entry. Complex type 3/JAR/JS configurations require dependency review and a future controlled publishing system and are not imported as independent APIs. API reachability and playback are not established by format validation. This version does not test remote playback or automatically find resources.

## CLI

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build.py
python3 scripts/release.py
```

Git history preserves prior versions. The daily workflow stages the catalog and validates configuration; it retries non-fast-forward push conflicts against the newest main without force-pushing. The old `sources.json` and `scripts/check.py` are retained as V0.1 reference only.

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

## Upstream snapshot review (0.5)

Save two versions of an authorized upstream strict JSON configuration locally. Compare them directly in manager.html or generate a separate report with:

```sh
python3 scripts/compare_upstream.py old.json new.json --output diff-report.json
```

The report identifies added, removed, changed and reordered sites by stable key, changed field names, global configuration changes, dependency-review hints, and SHA-256 fingerprints of snapshots and changed entries. Duplicate or missing keys are rejected. It does not download upstream configurations, apply changes to the catalog, or enable type 3 publishing. Keep the old and new snapshots locally and review changes individually using the existing import and audit tools. Report keys and field names can still contain private information; do not publish reports without review. The browser comparison is a local preview, without fingerprints.

## Manager workspace (0.6)

Seven navigation areas: overview, import, interface library, quality, dependencies, changes, and publication. Search and filter interfaces, move them between groups, and preview generated VOD JSON before exporting. Save or restore a draft explicitly using local browser storage; availability varies for file URLs and private browsing, and export remains the portable backup. Importing a catalog or restoring a draft asks before replacing current edits. No automatic upload or GitHub credentials are required. Preview is client-side; the Python builder and CI remain authoritative. Static markup checks and JavaScript syntax checks run in CI; real browser and TV behavior still require manual testing.

## Quality-assisted organization (0.7)

In the quality panel, load health.json and generate an organization preview. Only matching, explicitly opted-in checks within seven days contribute scores. Primary suggestions have recognized nonempty metadata and score >=80; backup includes lower scores or empty lists; untested/stale entries remain unknown; observed failures are flagged for review. Sort suggestions are stable within each warehouse, preserve locked and disabled positions, and never change approval, move between warehouses, or delete entries. Exact repeated API strings are reported across groups, not automatically removed. The thresholds are initial metadata heuristics, not playback quality metrics. Applying a preview changes only the current local draft; export and publication are separate. Any edit or report change invalidates the preview. The lock affects automatic organization only, not manual edits. JavaScript tests use synthetic fixtures.

## Staged release management (0.8)

Stable production entry: `index.json`. Stable test entry: `test.json`. The test channel contains only the latest reviewed, nonempty independent configurations; an empty candidate has no warehouses.

Actions stages a content-addressed snapshot under `releases/<SHA-256>/` and writes `release-status.json`. Test the candidate on your client first. To promote, edit `release-control.json` and set `active` to the full candidate ID from the report. The next successful workflow verifies the snapshot and switches the production index. To roll back, select a prior verified release ID or explicitly select `legacy`. Changing the catalog alone never changes production. Direct build.py --publish is retired. Release comparison counts refer to index URLs, so new snapshot addresses can appear as added/removed even if the logical group is unchanged.

Old snapshots are retained in the public repository; review all data before committing and do not publish private URLs. Rollback restores configuration, not upstream availability or permissions. If a resource becomes unauthorized or unsafe, do not roll back to a snapshot containing it. No automatic promotion. Git history and release directories record prior versions. The manager can display the release report, but cannot directly push or promote. Tests use synthetic data.
