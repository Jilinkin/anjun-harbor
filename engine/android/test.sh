#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 generate.py
mkdir -p build/jvm-test
javac --release 8 -encoding UTF-8 -d build/jvm-test src/com/github/catvod/spider/HarborCatalog.java build/generated/HarborData.java tests/CatalogTest.java
java -cp build/jvm-test com.github.catvod.spider.CatalogTest

# Test Android-compatible JSON logic with JVM org.json, separate from android.jar stubs.
if [ -n "${HARBOR_JSON_JAR:-}" ]; then
  javac --release 8 -encoding UTF-8 -cp "build/jvm-test:$HARBOR_JSON_JAR" -d build/jvm-test src/com/github/catvod/spider/HarborRules.java tests/RulesTest.java
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.RulesTest
fi
