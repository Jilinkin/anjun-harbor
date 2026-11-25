# Harbor RC1 — physical device acceptance (not production)

This package contains the original Android demo JAR, SHA-256 checksum, local test server and instructions. Only two reviewed open-film records are built in. It does not contain the previous 755 third-party interfaces. Actual media availability and Android host compatibility are not established by CI.

## macOS quick start

1. Download the artifact harbor-android-acceptance from the successful build for this revision and extract it into a local folder.
2. Open Terminal in the extracted directory. Run:

       python3 serve_test.py --jar harbor.jar --sha256 "$(awk '{print $1}' sha256.txt)"

   This tests loopback only. For TV access, find the Mac's actual private IPv4 in System Settings > Wi-Fi > Details > TCP/IP, then run the command again with --host YOUR_MAC_IPV4 --allow-lan. Replace YOUR_MAC_IPV4 with the actual address. Stop the first instance before restarting.
3. Save your original TVBox subscription before making changes. Import the Test subscription URL printed by the server into the test client. The test link is local, random per launch and not a permanent public URL. Do not expose the HTTP server to the Internet. Do not bypass client security restrictions.
4. Check that Harbor Android Test appears; open categories Animation and Sci-Fi, search Bunny, open its details, and attempt playback. Search Steel and attempt playback. Report results separately for each movie. No media availability promise.
5. Stop the server with Ctrl+C and restore the original subscription.

Record actual client name/version, Android version, JAR loading, homepage, category, search, detail, two playback attempts and error messages in ACCEPTANCE.md. Do not include private URLs or credentials in public issues. If the client cannot load a LAN HTTP JAR, stop and record the limitation.

## Release gate

Automated tests passed on revision aaf3adbc5d0526d92a2d9fc96b85092234a28887 (run 45579066148). This proves build and JVM/HTTP contracts, not Android execution. The new acceptance artifact must pass its own CI. Keep production index.json and aggregation-preview.json unchanged until actual acceptance, source permission review, and migration are completed. The five-warehouse preview is a list of references, not a unified deduplicated catalog. RC1 refers only to the original demo acceptance milestone, not a release of the full unified warehouse.
