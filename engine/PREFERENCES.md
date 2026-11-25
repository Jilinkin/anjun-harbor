# V2.7 stage 2 — display preferences

Independent local preferences over an authorized normalized mixed catalog. Apply reviewed deduplication first (if used), then display preferences. Original records, stable title IDs, URLs, credits and provider identities remain untouched. Category names are hashed into category IDs; renaming categories changes their IDs. Search uses the displayed title; the preview retains original names. Positive record priority sorts earlier than zero, negative later. Provider priority breaks ties; original order breaks remaining ties. Missing priorities leave order unchanged. Hidden items are not served by the local catalog. No automatic deletion, new provider imports, remote publishing, or modification to third-party sources.

Generate a starting preference file:
    python3 scripts/engine_preferences.py engine/examples/mixed/manifest.json --output preferences.json

Edit warehouse_name, provider_priority (list of provider IDs), category_names (original-to-display mapping), and records (keyed by stable title ID, optional name, category, hidden, priority). Use the existing dedupe preview to find record IDs. If using dedupe, pass --dedupe-selection to both the template and serving commands. Preferences are fingerprint-bound to the full catalog after deduplication; changes require a new review.

Preview without launching:
    python3 scripts/engine_preferences.py engine/examples/mixed/manifest.json --preferences preferences.json --output preference-preview.json

Serve:
    python3 scripts/engine_server.py --mixed engine/examples/mixed/manifest.json --preferences preferences.json

The example uses synthetic metadata, not playable content. The configuration is local, no production update. Use only authorized inputs; reports and preferences may contain personal titles, so keep them local. Actual TV runtime and Java CMS/HTML port remain incomplete. Existing 755 upstream interfaces have not been migrated.
