# V2.7 stage 1 — reviewed catalog deduplication

This is title-level review over the already normalized, explicitly authorized local mixed catalog. It is distinct from upstream site/API deduplication (aggregation/service-graph.json). No network or third-party rule imports.

Preview:
    python3 scripts/engine_dedupe.py engine/examples/mixed/manifest.json --output review.json

Exact groups require identical title, category, year, description, license note, and ordered episode labels and URLs. Same normalized title and nonempty year is a weaker review hint only. No automatic deletion or merging of media lines. Preview omits raw media URLs; keep reports private because names and identifiers may still be sensitive.

Create a local selection JSON with version 1, catalog_fingerprint copied from the report, and decisions of the form {"group":"exact group ID","keep":"record ID","remove":["other record ID"],"approved":true}. Only exact groups may be acted on. A changed source catalog invalidates the selection. Empty decisions retain all records. Original data and stable IDs are preserved.

Validate selection:
    python3 scripts/engine_dedupe.py /path/to/manifest.json --selection /path/to/selection.json --output result.json

Serve the reviewed single-site catalog:
    python3 scripts/engine_server.py --mixed /path/to/manifest.json --dedupe-selection /path/to/selection.json

The change applies only to the local runtime view, not source files, production or five-warehouse preview. To restore, omit the selection. Refuses incomplete provider loads and network mode for selection. Does not infer content licensing or playable media from metadata. Tests use synthetic fixtures. Native Android runtime remains a limited open-film demo; no existing 755 upstream entries migrated.
