# Harbor Engine 2.0 / foundation

The B+C approach starts with a shared title/category/episode model, trusted adapter protocol and a CMS output gateway. The initial adapter reads authorized local CMS metadata snapshots. It does not fetch websites or run remote scripts. Two existing CC BY movie fixtures are exposed under one TVBox type 1 site, with shared search and categories.

Run from the repository with Python 3.9+:

    python3 scripts/engine_server.py

Local entry: http://127.0.0.1:8898/config.json . To test on a trusted household LAN, use the actual private IP of the machine:

    python3 scripts/engine_server.py --host 192.168.1.100 --allow-lan

Use the printed single-warehouse URL. Do not expose the demo to the internet. This is a development prototype, not a hardened server. The sample playback URLs are external and have not been verified on a TV. No JAR is generated; the server is a platform-independent first step, not an Android plugin. Existing five-warehouse preview and production subscriptions remain unchanged.

Next: design and validate declarative JSON adapters for authorized data sources, add bounded HTTP transport and independent failure handling, then validate the specific client plugin contract before building any Java plugin. Unknown third-party rules, access controls, code and redistribution permissions are not assumed compatible. No claim that the 755 upstream entries are migrated.
