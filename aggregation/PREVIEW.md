# Multi-warehouse preview

This separate TVBox index references the five user-supplied single-warehouse addresses whose underlying configurations were parsed in the first and second audits. It keeps upstream configuration URLs intact rather than copying third-party code, account fields, or media. YW remains first. Exact repeated index URLs are removed. This is a reference-only aggregation, not a consolidated or VOD-only configuration: upstream live sections and overlapping sites remain. The previous audits found 755 site records, one identical same-warehouse record, one matching independent API pair and 39 matching-key groups; no site records have been removed from upstream files. Playback, permissions, third-party code safety and network compatibility have not been verified. Only use sources you are authorized to access, and do not run untrusted dependencies. The official index.json and candidate release control are unchanged.

Preview: https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/aggregation-preview.json

Test steps: Import as a multi-warehouse address in a compatible client, confirm five warehouse names, switch between authorized sources, record actual client name/version and errors. To restore the previous index, import the existing index.json. No automatic expansion of inaccessible multi-warehouse addresses, no automatic promotion.
