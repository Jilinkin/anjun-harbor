# Anjun Harbor

Personal Resource Index.

## Usage

Import the following address into a client that supports the `urls` multi-repository format:

```
https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/index.json
```

## Maintenance

- Edit `sources.json` to add, rename, remove or reorder authorized source configurations.
- `scripts/check.py` validates the list, deduplicates exact URLs, checks reachability and generates `index.json` and `status.json`.
- The GitHub Actions workflow runs daily at 02:23 UTC (10:23 China time), on relevant changes, or manually.
- Unreachable or nonstandard sources remain in the index; review status before removing them.
- The index does not merge source scripts, host videos, or collect separate live-TV feeds. A referenced upstream configuration may still include live TV.
- HTTP success and a recognizable configuration do not establish playback, security or content authorization. Only use sources you are authorized to access; review third-party executable scripts before use.
- Do not add credentials or secret URLs to this public repository.

## Manual refresh

```sh
python3 scripts/check.py
```
