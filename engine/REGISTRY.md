# V2.4 mixed adapter registry

One versioned manifest can now load four built-in adapter kinds: CMS snapshot, opt-in CMS network, JSON snapshot and HTML snapshot. All records use a single Catalog and TVBox type 1 gateway. Provider IDs must be unique. Manifest validation occurs before any network request; a failed data import discards that provider only. Rules and data must remain within the manifest directory. Each provider needs explicit permission review; JSON/HTML rule identity and authorization must match the manifest. No dynamically loaded plugins or remote executable code.

Run the synthetic three-provider integration example:

    python3 scripts/engine_server.py --mixed engine/examples/mixed/manifest.json

The example emits three searchable records in one category, one site in config.json, and three distinct provider IDs. example.com media URLs are placeholders, not playable. The CMS network adapter requires --allow-network and separately approved public HTTPS URLs/media hosts. This is startup ingestion, not live federated search. Cross-provider title equivalence is not assumed and not automatically deduplicated. Keep private snapshots local. Existing production and five-warehouse preview remain unchanged.

Next milestone: verify the exact TV client/plugin contract and licensing before selecting a Java/Android integration strategy. A JAR is not yet generated and the registry does not import existing third-party crawlers.
