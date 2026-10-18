#!/usr/bin/env bash
set -euo pipefail
base=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018
source_dir=$base/source-6ee2e8f10475549e
mkdir -p "$base/tools"
test -e "$base/tools/mill"
test -e "$base/tools/clang++"
test -e "$base/tools/clang"
test -e "$base/tools/rg"
export PATH="$base/tools:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export JAVA_OPTS='-Xmx6G -Xss16m -XX:ActiveProcessorCount=2'
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export BUILD_JOBS=2
cd "$source_dir"
bash team/optimizations/o1/check-handoff.sh "$base/fu-attempt-03"
