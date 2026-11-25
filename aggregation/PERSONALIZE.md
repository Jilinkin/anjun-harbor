# Single-warehouse personalization (local only)

Use an authorized local configuration snapshot and the actual effective original HTTPS configuration URL. Do not use the address of the newly generated file as the base. Review executable code, its license, site access and redistribution permissions separately; this utility does not establish these facts.

Example preference file (synthetic keys; replace after review):

```json
{"approved_keys":["example_a","example_b"],"authorization":"Actual permission or license","dependencies_reviewed":true,"hide":[],"priority":["example_b"],"rename":{"example_b":"Favorite"},"search_keys":["example_b"]}
```

```sh
python3 scripts/personalize.py /path/to/snapshot.json --base-url https://example.com/config.json --preferences /path/to/preferences.json --output /path/to/personal.json
```

The tool retains the approved subset and global settings, removes the top-level lives field, preserves site-specific options, resolves recognized relative reference fields against the original configuration URL (including legacy spider MD5 suffixes), and applies the preference order and names. It never enables disabled search capabilities. It refuses ambiguous keys or unrecognized relative-reference fields. It does not rewrite paths inside scripts, embedded JSON strings, custom protocols, or dynamically generated URLs; these require manual review. Removing lives does not guarantee that a third-party executable cannot expose live content. The result is private and local, not automatically uploaded. Existing independent release builder still accepts type 0/1 only. Complex warehouse production publication is not implemented by this utility.

For upstream updates, review changes and update the authorized selection before regenerating. No full remote snapshot or generated third-party config is committed.
