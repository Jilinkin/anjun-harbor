# V2.7 stage 3 — local release store

A private local content-addressed store for reviewed normalized snapshots, with independent candidate and active pointers. No remote publication, source modification, or execution of upstream code. macOS/Linux only (fcntl lock). Keep the store outside the Git repository and back it up; snapshots contain media URLs and permission notes. Trusted local filesystem only. A checksum detects changes, not content rights or trust.

Example workflow (synthetic example is metadata only):
    python3 scripts/engine_releases.py --store ~/harbor-local stage engine/examples/mixed/manifest.json
    python3 scripts/engine_releases.py --store ~/harbor-local status
    python3 scripts/engine_server.py --release-store ~/harbor-local --channel candidate --port 8899

After review, use the full candidate ID printed by status:
    python3 scripts/engine_releases.py --store ~/harbor-local promote CANDIDATE_ID --expected-active none
    python3 scripts/engine_server.py --release-store ~/harbor-local --channel active --port 8898

For future releases replace none with the current active ID, review diff first, and use rollback --expected-active CURRENT_ID to restore the previous active release. A running server reads a fixed snapshot at startup; restart after switching. Candidate and active may run on separate ports; LAN requires explicit private address and trusted network. No Internet-facing service. Promotion requires exact current pointers. Atomic state writes and content-addressed snapshots preserve prior versions. Rollback switches previous and active only, not candidate. Stage supports --dedupe-selection and --preferences, both must match the reviewed current catalog. Preference inheritance across changed data is not automatic; remains a future task.

Existing GitHub production and five-warehouse preview are untouched. No 755-entry third-party migration, complete Java CMS/HTML port or TV runtime acceptance. Tests use synthetic normalized records.
