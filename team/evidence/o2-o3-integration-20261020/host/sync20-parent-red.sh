#!/usr/bin/env bash
set -euo pipefail
base=/home/amesotten/.cache/codex-rvinno/sync20
native=$(cat /mnt/c/Code/RVInno/riscv/team/out/sync20-rtl-pack-red-windows/build-copy.txt)
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$JAVA_HOME/bin:$PATH
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export CHISEL_FIRTOOL_PATH=/home/amesotten/.cache/llvm-firtool/1.62.1/bin
cd "$native"
cp /mnt/c/Code/RVInno/riscv/team/optimizations/o2/run_rtl.py team/optimizations/o2/run_rtl.py
python3 -B team/optimizations/o2/run_rtl.py parent "$base/parent-red-01"
