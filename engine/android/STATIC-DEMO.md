# Static-hosted Android demo (RC1)

Target architecture: GitHub static HTTPS files + Android TVBox local execution. No dedicated server, household computer, NAS or VPS required. GitHub Actions builds the original JAR; this pinned publication workflow copies the successful reviewed demo artifact without rebuilding. The demo is separate from index.json and aggregation-preview.json. No third-party source migration, no live channels, only the two open-film fixtures. No claims of physical playback or complete TVBox compatibility.

Once the publish workflow succeeds, import the single-site config at android-demo/rc1/config.json from raw.githubusercontent.com. Use a compatible CatVod host that supports type 3 / csp_Harbor and HTTPS JAR loading. Save the existing subscription first. If direct raw GitHub is unreachable or the host rejects the JAR, report the exact client name/version and error. Do not bypass client protections. The first test uses bundled metadata with no additional network adapter; media playback still needs access to the actual media host.

The RC1 versioned path must not be overwritten with different bytes. sha256.txt and provenance.json record build identity. The workflow does not update the production index or previous preview.
