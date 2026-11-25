# V2.3 offline HTML adapter

This adapter maps authorized, locally saved, static HTML into the V2.0 title model. Supports a small, explicit subset of CSS (tag, class, ID, descendant) and relative XPath (child, descendant, simple attribute predicates). Fields must match exactly one node. Supports text and explicit attributes; does not execute JavaScript, follow links, fetch pages, resolve players, or bypass access restrictions. HTML parsing is a bounded standard-library implementation, not a full browser DOM or HTML5 parser. Only explicit approved HTTPS media links are accepted; reserved example.com links below do not play.

Run:
    python3 scripts/engine_server.py --html-rules engine/examples/html-rule/manifest.json

Use existing private LAN option only if needed. Input files are restricted to the manifest directory. Use only material you have permission to process. No third-party upstream interface has been migrated. Existing production and five-warehouse preview remain unchanged. Next: unify CMS, JSON and HTML provider modes into a trusted local adapter registry so one warehouse can contain mixed adapters.
