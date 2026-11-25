#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 generate.py
mkdir -p build/jvm-test
javac --release 8 -encoding UTF-8 -d build/jvm-test src/com/github/catvod/spider/HarborCatalog.java build/generated/HarborData.java tests/CatalogTest.java
java -cp build/jvm-test com.github.catvod.spider.CatalogTest

# Test Android-compatible JSON logic with JVM org.json, separate from android.jar stubs.
if [ -n "${HARBOR_JSON_JAR:-}" ]; then
  javac --release 8 -encoding UTF-8 -cp "build/jvm-test:$HARBOR_JSON_JAR" -d build/jvm-test src/com/github/catvod/spider/HarborRules.java src/com/github/catvod/spider/HarborRegistry.java src/com/github/catvod/spider/HarborLoadResult.java src/com/github/catvod/spider/HarborNetwork.java src/com/github/catvod/spider/HarborCache.java src/com/github/catvod/spider/HarborHtml.java tests/RulesTest.java tests/NetworkTest.java tests/HtmlTest.java tests/CacheTest.java
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.RulesTest
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.NetworkTest
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.HtmlTest
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.CacheTest
  javac --release 8 -encoding UTF-8 -cp "build/jvm-test:$HARBOR_JSON_JAR" -d build/jvm-test tests/stub/android/content/Context.java stub/com/github/catvod/crawler/Spider.java src/com/github/catvod/spider/Harbor.java src/com/github/catvod/spider/Init.java tests/PluginTest.java tests/RegistryTest.java tests/IsolationTest.java
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.PluginTest
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.RegistryTest
  java -cp "build/jvm-test:$HARBOR_JSON_JAR" com.github.catvod.spider.IsolationTest
fi
