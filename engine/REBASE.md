# V2.7 stage 4 — local preference update review

Generate a review-only migration report from two complete authorized local mixed snapshot manifests and the previous preferences file. Keep the original manifest and its snapshot files intact. If deduplication is used, supply the separately reviewed old/new selections. No network access, no automatic reapproval of dedupe decisions, no release pointer mutation.

    python3 scripts/engine_rebase.py /path/to/old/manifest.json /path/to/new/manifest.json --preferences /path/to/old-prefs.json --output /path/to/rebase-review.json

Warehouse name is retained. Individual edits are retained only for identical complete records (including authorization and episode URLs). Provider ordering is retained when at least one identical provider record remains; otherwise flagged. Category renames are retained only if category membership and all member records are unchanged. Additions, removals and changes are listed by stable ID. Conflicts include prior values where relevant. A new ID is never guessed from title similarity.

The output is deliberately not a valid preferences file. Review conflicts and additions, explicitly extract candidate_preferences into a new local preferences file, adjust if needed, and preview through engine_preferences.py before staging through engine_releases.py. A fresh fingerprint binds the candidate to the new catalog. Reports may contain personal labels; keep them private. Original inputs remain unchanged.

Native Java CMS/HTML ports and actual TV acceptance are incomplete. Existing subscriptions unchanged; none of the original 755 upstream interfaces are migrated by this feature.
