#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"

repo_root="$TEAM_PROJECT_ROOT"
test_root="$repo_root/team/rtl/vdot"
out_dir=${VDOT_OUT_DIR:-"$repo_root/team/out/vdot-fu/$(date +%Y%m%d-%H%M%S)-$$"}
mkdir -p "$out_dir"
out_dir=$(cd "$out_dir" && pwd)
export CHISEL_FIRTOOL_PATH=${CHISEL_FIRTOOL_PATH:-"$HOME/.cache/llvm-firtool/1.62.1/bin"}
export JAVA_OPTS=${JAVA_OPTS:-"-Xmx12G -Xss16m"}
build_jobs=${BUILD_JOBS:-2}
exec > >(tee "$out_dir/check.log") 2>&1
trap 'rc=$?; printf "exit_code=%s end=%s\n" "$rc" "$(date -Is)" > "$out_dir/check.status"' EXIT
cd "$repo_root"
printf 'VDOT_FU_CHECK_START date=%s output=%s\n' "$(date -Is)" "$out_dir"
git rev-parse HEAD
git status --short
for tool in java mill python3 verilator clang++ rg; do command -v "$tool"; done
test -x "$CHISEL_FIRTOOL_PATH/firtool"
java -version
mill --version
"$CHISEL_FIRTOOL_PATH/firtool" --version
verilator --version
clang++ --version
python3 --version
sha256sum build.sc \
  src/main/scala/xiangshan/backend/fu/{FuType.scala,FuConfig.scala,FuncUnit.scala} \
  src/main/scala/xiangshan/backend/fu/vector/{VDotDatapath.scala,VecNonPipedFuncUnit.scala,VecPipedFuncUnit.scala} \
  src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala \
  src/main/scala/xiangshan/backend/rob/RobBundles.scala \
  team/rtl/vdot/{GenerateVDotFu.scala,fu_test.cpp,prepare_vectors.py} \
  team/scripts/check-vdot-fu.sh team/models/vdot/data/{manifest.json,directed.jsonl,random.jsonl} \
  > "$out_dir/source.sha256"

set -x
python3 -B "$test_root/prepare_vectors.py" "$repo_root/team/models/vdot/data" "$out_dir/vectors.tsv"
mill -i -j "$build_jobs" vdotFu.runMain team.vdot.GenerateVDotFu "$out_dir/rtl" \
  > "$out_dir/elaboration.log" 2>&1 || { cat "$out_dir/elaboration.log"; exit 1; }
cat "$out_dir/elaboration.log"
test -s "$out_dir/rtl/VDotFuTestTop.sv"
sha256sum "$out_dir/rtl/VDotFuTestTop.sv" > "$out_dir/rtl.sha256"
verilator --cc --exe --build --assert --top-module VDotFuTestTop \
  --Mdir "$out_dir/obj_dir" -j "$build_jobs" -CFLAGS '-std=c++17 -O2' \
  "$out_dir/rtl/VDotFuTestTop.sv" "$test_root/fu_test.cpp" \
  > "$out_dir/verilator-build.log" 2>&1 || { cat "$out_dir/verilator-build.log"; exit 1; }
"$out_dir/obj_dir/VVDotFuTestTop" "$out_dir/vectors.tsv" | tee "$out_dir/results.log"

for fault in identity cancel-leak; do
  if "$out_dir/obj_dir/VVDotFuTestTop" "$out_dir/vectors.tsv" "--inject-$fault" \
      > "$out_dir/inject-$fault.log" 2>&1; then
    echo "FAULT_DETECTION_FAIL: $fault escaped comparison" >&2
    exit 1
  else
    rc=$?
  fi
  test "$rc" -eq 1
  rg -q "^VDOT_FU_FAULT_INJECTION $fault" "$out_dir/inject-$fault.log"
  rg -q '^VDOT_FU_FAIL case=' "$out_dir/inject-$fault.log"
  cat "$out_dir/inject-$fault.log"
  printf 'FU_FAULT_DETECTION_PASS fault=%s expected_exit=1\n' "$fault"
done

if mill -i -j "$build_jobs" vdotFu.runMain team.vdot.GenerateVDotFu \
    "$out_dir/invalid-vlen" --invalid-vlen > "$out_dir/invalid-vlen.log" 2>&1; then
  echo 'VLEN_GUARD_FAIL: accepted unsupported VLEN=256' >&2
  exit 1
fi
rg -q 'VDot requires VLEN=128' "$out_dir/invalid-vlen.log"
echo 'VLEN_GUARD_PASS unsupported=256'
set +x
echo 'VDOT_FU_CHECK_PASS (real FU RTL and RobPtr; no EXU/CPU/NEMU integration validation)'
