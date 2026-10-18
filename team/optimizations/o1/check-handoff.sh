#!/usr/bin/env bash
# Real RTL runner. A missing tool or failed test must never produce a PASS record.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
if [[ $# != 1 || "$1" != /* || -e "$1" ]]; then
  echo 'Usage: check-handoff.sh /absolute/new/output-directory' >&2; exit 2
fi
out=$(realpath -m "$1")
case "$out/" in "$root/team/evidence/"*|"$root/team/optimizations/"*) echo 'Use a new work output directory, not source/evidence' >&2; exit 2;; esac
mkdir -p "$out"
exec > >(tee "$out/runner.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$out/runner.status"' EXIT
cd "$root"
source team/scripts/activate.sh
for tool in python3 java mill verilator clang++; do
  command -v "$tool" || { echo "O1_RTL_NOT_RUN_MISSING_TOOL=$tool"; exit 2; }
done
export CHISEL_FIRTOOL_PATH=${CHISEL_FIRTOOL_PATH:-"$HOME/.cache/llvm-firtool/1.62.1/bin"}
test -x "$CHISEL_FIRTOOL_PATH/firtool"
export JAVA_OPTS=${JAVA_OPTS:-"-Xmx12G -Xss16m"}
BUILD_JOBS=${BUILD_JOBS:-2}
[[ "$BUILD_JOBS" =~ ^[1-9][0-9]*$ ]] || exit 2
export BUILD_JOBS
# The old event schema is deliberately disabled; its mapper cannot accept O1 overlap.
export VDOT_T12_TRACE=0 VDOT_T13_TRACE=0
git rev-parse HEAD > "$out/source.commit"
git diff --binary HEAD > "$out/working-tree.patch"
# Untracked source cannot be reconstructed from HEAD plus a diff.
test -z "$(git ls-files --others --exclude-standard -- src team/rtl team/models team/optimizations/o1 team/scripts build.sc)" || {
  echo 'O1_SOURCE_NOT_FROZEN_UNTRACKED_INPUTS'; exit 2;
}
sha256sum src/main/scala/xiangshan/backend/fu/wrapper/VDot{,Handoff}.scala \
  src/main/scala/xiangshan/backend/exu/ExeUnit.scala \
  src/main/scala/xiangshan/backend/fu/{FuncUnit,FuConfig}.scala \
  src/main/scala/xiangshan/backend/fu/vector/{VecNonPipedFuncUnit,VDotDatapath}.scala \
  team/rtl/vdot/{GenerateVDotFu.scala,prepare_vectors.py,fu_test.cpp} \
  team/optimizations/o1/{handoff_test.cpp,check-handoff.sh} build.sc > "$out/source.sha256"
# Existing tests and input data stay unchanged and cover the default and T14 modes.
for fused in 0 1; do
  VDOT_O1_HANDOFF=0 VDOT_T14_FUSED_INPUT="$fused" VDOT_OUT_DIR="$out/legacy-$fused" \
    bash team/scripts/check-vdot-fu.sh
 done
export VDOT_T14_FUSED_INPUT=1 VDOT_O1_HANDOFF=1
cp "$out/legacy-1/vectors.tsv" "$out/vectors.tsv"
mill -i -j "$BUILD_JOBS" vdotFu.runMain team.vdot.GenerateVDotFu "$out/candidate-rtl" \
  > "$out/elaboration.log" 2>&1
# Also compiles XiangShan Scala, but the generated top instantiates only the real FU.
verilator --cc --exe --build --assert --top-module VDotFuTestTop \
  --Mdir "$out/candidate-obj" -j "$BUILD_JOBS" -CFLAGS '-std=c++17 -O2' \
  "$out/candidate-rtl/VDotFuTestTop.sv" "$root/team/optimizations/o1/handoff_test.cpp" \
  > "$out/verilator.log" 2>&1
binary="$out/candidate-obj/VVDotFuTestTop"
"$binary" "$out/vectors.tsv" | tee "$out/result.log"
grep -q '^O1_FU_ONLY_PASS ' "$out/result.log"
for fault in identity wen high cancel; do
  rc=0
  "$binary" "$out/vectors.tsv" "$fault" > "$out/inject-$fault.log" 2>&1 || rc=$?
  test "$rc" -eq 1
  grep -q "^O1_INJECT $fault$" "$out/inject-$fault.log"
  grep -q '^O1_FU_FAIL ' "$out/inject-$fault.log"
done
sha256sum -c "$out/source.sha256" > "$out/source-after.log"
echo 'O1_FU_RUNNER_PASS_PARENT_ELABORATION_AND_FULLCORE_PENDING'
