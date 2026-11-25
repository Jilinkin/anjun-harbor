#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
test -n "$SDK"
PLATFORM="$SDK/platforms/android-35/android.jar"
D8="$SDK/build-tools/35.0.0/d8"
test -f "$PLATFORM"
test -x "$D8"
mkdir -p build
rm -rf build/stub build/classes build/dex
mkdir -p build/stub build/classes build/dex
javac --release 8 -classpath "$PLATFORM" -d build/stub $(find stub -name "*.java")
python3 generate.py
javac --release 8 -encoding UTF-8 -classpath "$PLATFORM:build/stub" -d build/classes $(find src build/generated -name "*.java")
jar cf build/abi.jar -C build/stub .
jar cf build/jvm.jar -C build/classes .
"$D8" --min-api 21 --lib "$PLATFORM" --classpath build/abi.jar --output build/dex build/jvm.jar
jar cf build/harbor.jar -C build/dex classes.dex
python3 verify.py
