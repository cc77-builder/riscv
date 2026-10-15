#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
out=${VDOT_OUT_DIR:-"$root/team/out/vdot-decode/$(date +%Y%m%d-%H%M%S)-$$"}
if test -d "$out" && test -n "$(ls -A "$out")"; then
  echo "Use a fresh VDOT_OUT_DIR; refusing existing results: $out" >&2
  exit 2
fi
mkdir -p "$out"
out=$(cd "$out" && pwd)
exec > >(tee "$out/check.log") 2>&1
trap 'rc=$?; printf "exit_code=%s end=%s\n" "$rc" "$(date -Is)" > "$out/check.status"' EXIT
cd "$root"
printf 'VDOT_DECODE_START date=%s output=%s\n' "$(date -Is)" "$out"
git rev-parse HEAD
git status --short
for tool in java mill verilator; do
  command -v "$tool" || { echo "MISSING_PREREQUISITE: $tool" >&2; exit 1; }
done
java -version
mill --version
verilator --version
sha256sum build.sc src/main/scala/xiangshan/{Parameters.scala,package.scala} \
  src/main/scala/xiangshan/backend/decode/{Instructions,VecDecoder,DecodeUnit,DecodeUnitComp,UopInfoGen,VecExceptionGen}.scala \
  src/main/scala/xiangshan/backend/decode/isa/bitfield/RiscvInst.scala \
  team/rtl/vdot/{GenerateVDotDecode.scala,decode_test.cpp} > "$out/source.sha256"
mill -i -j "${BUILD_JOBS:-2}" vdotDecode.runMain team.vdot.GenerateVDotDecode "$out/rtl" > "$out/elaboration.log" 2>&1
verilator --cc --exe --build --assert --top-module VDotDecodeTestTop \
  --Mdir "$out/obj_dir" -j "${BUILD_JOBS:-2}" -CFLAGS '-std=c++17 -O2' \
  "$out/rtl/VDotDecodeTestTop.sv" "$root/team/rtl/vdot/decode_test.cpp" > "$out/build.log" 2>&1
"$out/obj_dir/VVDotDecodeTestTop" | tee "$out/results.log"
sha256sum "$out/rtl/VDotDecodeTestTop.sv" > "$out/rtl.sha256"
sha256sum -c "$out/source.sha256"
