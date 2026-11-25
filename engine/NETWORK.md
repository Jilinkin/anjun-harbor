# V2.1 network adapter

This is an opt-in startup metadata importer for authorized standard JSON CMS sources, not a live search proxy. It uses the V2.0 model and gateway. The default demo still makes no metadata network requests. A local configuration (never commit private URLs or credentials) may contain up to eight reviewed providers, three detail pages per provider and 300 records per provider. A source must return explicit single-line HTTPS play URLs from manually approved media hosts. No redirects, authentication bypass, remote code, media fetching, automatic discovery or third-party source migration. DNS is checked for public addresses and TLS is pinned to the resolved address; response reads are bounded. DNS and socket timeouts are not a strict whole-process deadline. Metadata failures discard the entire affected provider without interrupting other valid providers. Refresh by restarting; search covers imported records only.

Example synthetic configuration (not a real source):

```json
{"providers":[{"provider":"example","api":"https://example.com/cms","approved":true,"authorization":"Actual authorization evidence","media_hosts":["media.example.com"],"pages":1}]}
```

After replacing with a service you are authorized to query and use, run:

    python3 scripts/engine_server.py --providers /path/to/providers.json --allow-network

The existing local/explicit LAN restrictions apply. Do not publish the service to the Internet. Host allowlisting checks metadata URLs, not the destination reached by the TV after redirects; only use trusted services. Tests are mocked; no external media availability or actual TV playback is certified. Production and aggregation-preview.json are unchanged.
