# RC1 accelerated test entry

config-cn.json references only the original Harbor demo JAR via GH-Proxy, pinned to commit 7c17a07cde2caefec08b9f227ec4bef0878253bb. No external source, media or script is added. The original configuration, production index and five-reference preview are unchanged.

GH-Proxy is a third-party transport, not controlled by Harbor. Availability in mainland China is unverified. A proxy could alter the JSON and binary; the client may not verify SHA-256 automatically. Independently verify the downloaded JAR against the trusted original CI artifact before execution; do not run it if verification is unavailable or mismatched. Trusted original SHA-256: fe2f35d40dce3c5042d75dea7279012ddee5eeff539ed355d15b6e9f2b86c89f. This test uses two bundled open-film records. Media host reachability is separate from config/JAR reachability. No household server is required.
