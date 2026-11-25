# V2.2 declarative JSON adapter

Map locally saved, authorized JSON metadata snapshots into the shared model using field paths (arrays of literal object keys or array indexes). No expression evaluation, regular expressions, scripts, remote rule fetching, page scraping, or access-control bypass. Rules must be reviewed and specify allowed media hosts. A failing provider is discarded rather than partially imported. These are static snapshots, not live remote search. Existing CMS network mode remains separate.

See engine/examples/json-rule/ for a synthetic example. Run:

    python3 scripts/engine_server.py --rules engine/examples/json-rule/manifest.json

The example uses reserved example.com URLs and is for metadata tests only, not playback. To test on TV use the existing explicitly enabled private LAN mode. Do not expose the server publicly. A rule maps item, ID, title, category, optional year/description and episode arrays. Only explicit HTTPS media URLs are supported. Files are restricted to the manifest directory; private snapshots should never be committed. Actual media permission, network availability and TV compatibility require separate review.

The five-warehouse preview and production subscriptions remain unchanged. No existing complex third-party crawler is migrated.
