#!/usr/bin/env bash
# Final two-slot VDotElastic checks (O2 elastic + T14 fused input, O1 off).
#   fu      VDotElastic FU alone: all vectors, then each injected fault must be detected.
#   parent  VDot inside the VFEX4 parent with DIV/SQRT: positive replay, then every fault.
set -euo pipefail
stage=${1:-}
case "$stage" in fu|parent) ;; *) echo 'Usage: bash team/scripts/check-vdot-o2.sh {fu|parent}' >&2; exit 2;; esac
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
root="$TEAM_PROJECT_ROOT"
cd "$root"
export VDOT_O2_ELASTIC=1 VDOT_T14_FUSED_INPUT=1 VDOT_O1_HANDOFF=0
export VDOT_O2_TRACE=0 VDOT_O1_TRACE=0 VDOT_T12_TRACE=0 VDOT_T13_TRACE=0
export CHISEL_FIRTOOL_PATH=${CHISEL_FIRTOOL_PATH:-"$HOME/.cache/llvm-firtool/1.62.1/bin"}
export JAVA_OPTS=${JAVA_OPTS:-"-Xmx12G -Xss16m"}
jobs=${BUILD_JOBS:-2}
out=${VDOT_OUT_DIR:-"$root/team/out/vdot-o2-$stage/$(date +%Y%m%d-%H%M%S)-$$"}
mkdir -p "$out"
out=$(cd "$out" && pwd)
exec > >(tee "$out/check.log") 2>&1
trap 'rc=$?; printf "exit_code=%s end=%s\n" "$rc" "$(date -Is)" > "$out/check.status"' EXIT

if test "$stage" = fu; then
  target=vdotElasticFu; main=GenerateVDotElasticFu; top=VDotElasticFuTestTop
  bench=team/optimizations/o2/fu/fu_test.cpp; pass=O2_FU_PASS; fail=O2_FU_FAIL
  faults="identity wen high cancel"
else
  target=vdotElasticParent; main=GenerateVDotElasticParent; top=VDotElasticParentTestTop
  bench=team/optimizations/o2/parent/parent_test.cpp; pass=O2_PARENT_PASS; fail=O2_PARENT_FAIL
  faults=$(cd team/optimizations/o2/parent && python3 -B -c 'import check_negative; print(" ".join(check_negative.FAULTS))')
fi
printf 'VDOT_O2_CHECK_START stage=%s commit=%s output=%s\n' "$stage" "$(git rev-parse HEAD)" "$out"

python3 -B team/rtl/vdot/prepare_vectors.py team/models/vdot/data "$out/vectors.tsv"
mill -i -j "$jobs" "$target.runMain" "team.vdot.$main" "$out/rtl" > "$out/elaboration.log" 2>&1 \
  || { tail -n 60 "$out/elaboration.log"; exit 1; }
mapfile -t sources < <(find "$out/rtl" -type f \( -name '*.sv' -o -name '*.v' \) | sort)
test -s "$out/rtl/$top.sv"
verilator --cc --exe --build --assert --top-module "$top" --Mdir "$out/obj" -j "$jobs" \
  -CFLAGS '-std=c++17 -O2' "${sources[@]}" "$root/$bench" > "$out/verilator.log" 2>&1 \
  || { tail -n 60 "$out/verilator.log"; exit 1; }
bin="$out/obj/V$top"

"$bin" "$out/vectors.tsv" > "$out/positive.log" 2>&1
test "$(grep -c "^$pass" "$out/positive.log")" = 1
! grep -q "$fail" "$out/positive.log"
grep "^$pass" "$out/positive.log"
if test "$stage" = parent; then
  (cd team/optimizations/o2/parent && python3 -B check_negative.py --positive --return-code 0 --log "$out/positive.log") > "$out/positive-replay.json"
  echo 'O2_PARENT_POSITIVE_REPLAY_PASS'
fi

for fault in $faults; do
  set +e; "$bin" "$out/vectors.tsv" "$fault" > "$out/inject-$fault.log" 2>&1; rc=$?; set -e
  if test "$stage" = parent; then
    (cd team/optimizations/o2/parent && python3 -B check_negative.py --fault "$fault" --return-code "$rc" --log "$out/inject-$fault.log")
  else
    test "$rc" = 1 && grep -q "^$fail" "$out/inject-$fault.log" \
      || { echo "O2_FU_FAULT_ESCAPED $fault rc=$rc"; cat "$out/inject-$fault.log"; exit 1; }
    echo "O2_FU_FAULT_DETECTED $fault"
  fi
done
echo "VDOT_O2_CHECK_PASS stage=$stage faults=$(echo $faults | wc -w)"
