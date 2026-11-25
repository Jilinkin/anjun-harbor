#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 generate.py
mkdir -p build/jvm-test
javac --release 8 -encoding UTF-8 -d build/jvm-test src/com/github/catvod/spider/HarborCatalog.java build/generated/HarborData.java tests/CatalogTest.java
java -cp build/jvm-test com.github.catvod.spider.CatalogTest
