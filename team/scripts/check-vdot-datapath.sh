#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"

repo_root="$TEAM_PROJECT_ROOT"
test_root="$repo_root/team/rtl/vdot"
out_dir=${VDOT_OUT_DIR:-"$repo_root/team/out/vdot-datapath/$(date +%Y%m%d-%H%M%S)-$$"}
mkdir -p "$out_dir"
out_dir=$(cd "$out_dir" && pwd)
export CHISEL_FIRTOOL_PATH=${CHISEL_FIRTOOL_PATH:-"$HOME/.cache/llvm-firtool/1.62.1/bin"}
build_jobs=${BUILD_JOBS:-2}
exec > >(tee "$out_dir/check.log") 2>&1
trap 'rc=$?; printf "exit_code=%s end=%s\n" "$rc" "$(date -Is)" > "$out_dir/check.status"' EXIT

cd "$repo_root"
printf 'VDOT_DATAPATH_CHECK_START date=%s output=%s\n' "$(date -Is)" "$out_dir"
git rev-parse HEAD
git status --short
for tool in java mill python3 verilator g++ clang++ rg; do
  command -v "$tool"
done
test -x "$CHISEL_FIRTOOL_PATH/firtool"
java -version
mill --version
"$CHISEL_FIRTOOL_PATH/firtool" --version
verilator --version
g++ --version
clang++ --version
python3 --version

sha256sum build.sc \
  src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala \
  team/rtl/vdot/GenerateVDot.scala team/rtl/vdot/datapath_test.cpp \
  team/rtl/vdot/prepare_vectors.py team/scripts/check-vdot-datapath.sh \
  team/models/vdot/data/{manifest.json,directed.jsonl,random.jsonl} \
  > "$out_dir/source.sha256"

set -x
python3 -B "$test_root/prepare_vectors.py" \
  "$repo_root/team/models/vdot/data" "$out_dir/vectors.tsv"
mill -i -j "$build_jobs" vdotDatapath.runMain team.vdot.GenerateVDot "$out_dir/rtl"
test -s "$out_dir/rtl/VDotDatapath.sv"
sha256sum "$out_dir/rtl/VDotDatapath.sv" > "$out_dir/rtl.sha256"
verilator --cc --exe --build --top-module VDotDatapath \
  --Mdir "$out_dir/obj_dir" -j "$build_jobs" \
  -CFLAGS '-std=c++17 -O2' \
  "$out_dir/rtl/VDotDatapath.sv" "$test_root/datapath_test.cpp" \
  > "$out_dir/verilator-build.log" 2>&1 || {
    cat "$out_dir/verilator-build.log"
    exit 1
  }
"$out_dir/obj_dir/VVDotDatapath" "$out_dir/vectors.tsv" | tee "$out_dir/results.log"

# Inject a readback error, not a change to the production RTL or golden vectors.
# Both low result bits and the otherwise-zero high 96 bits must be compared.
for bit in 0 127; do
  if "$out_dir/obj_dir/VVDotDatapath" "$out_dir/vectors.tsv" "--inject-bit=$bit" \
      > "$out_dir/inject-$bit.log" 2>&1; then
    echo "FAULT_DETECTION_FAIL: injected bit $bit escaped comparison" >&2
    exit 1
  else
    rc=$?
  fi
  test "$rc" -eq 1
  rg -q '^VDOT_DATAPATH_MISMATCH ' "$out_dir/inject-$bit.log"
  cat "$out_dir/inject-$bit.log"
  printf 'FAULT_DETECTION_PASS bit=%s expected_exit=1\n' "$bit"
done
set +x
echo 'VDOT_DATAPATH_CHECK_PASS (combinational RTL only; no FU protocol/CPU/NEMU validation)'
