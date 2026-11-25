# Offline aggregation (V1.1 development)

1. Save configurations you have permission to inspect and use to a private local folder. No automatic downloading or script execution is performed. Do not upload snapshots or reports with private URLs to this public repository.
2. Create manifest.json alongside the files:
```json
{"roots":["https://example.com/index.json"],"snapshots":[{"url":"https://example.com/index.json","file":"index.json"},{"url":"https://example.com/a.json","file":"a.json"}]}
```
3. Run from the repository:
```sh
python3 scripts/aggregate.py /path/to/manifest.json --output /path/to/dedup-report.json
```
It expands nested lists using locally supplied snapshots only, detects cycles, and recognizes strict JSON and JSON with comments/trailing commas. Missing snapshots are reported, never guessed. Report entries contain stable IDs and private source metadata. Identical configuration content and matching keys/API addresses are candidates, not proof that behavior or dependencies are equivalent.
4. For independent, reviewed type 0/1 APIs only, create a local selection file:
```json
{"entries":[{"id":"COPY_REPORT_ID","group":"featured","group_name":"Harbor · 精选","approved":true,"independent_confirmed":true,"authorization":"Record actual permission or license here"}]}
```
```sh
python3 scripts/aggregate.py /path/to/manifest.json --selection /path/to/selection.json --output /path/to/catalog.json
```
Order the selection by preference (YW first if appropriate). Exact same type + API is kept once. Additional per-site options and incompatible search flags are rejected; review global dependencies separately before confirming independence. Type 3 scripts and proprietary or unverified sources are not merged. The resulting catalog is compatible with the existing staged release builder. Review before replacing the existing catalog. The production index stays unchanged until explicit promotion.
