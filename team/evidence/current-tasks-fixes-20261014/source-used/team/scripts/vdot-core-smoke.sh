#!/usr/bin/env bash
# Small T10 integration run; full T11/T12 uses vdot-tests.sh run-rtl.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
action=${1:?Usage: vdot-core-smoke.sh build|run}
case "$action" in build|run) ;; *) exit 2;; esac
evidence=${TEAM_EVIDENCE_DIR:?Set TEAM_EVIDENCE_DIR}
mkdir -p "$evidence"
evidence=$(cd "$evidence" && pwd)
rm -f -- "$evidence/check.json"
exec > >(tee "$evidence/$action.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$evidence/$action.status"' EXIT
export AM_HOME=${AM_HOME:?Set AM_HOME to pinned nexus-am}
export LINUX_GNU_TOOLCHAIN=1
data="$evidence/data"
snapshot() {
  python3 team/scripts/vdot_core_checks.py snapshot --root "$root" --evidence "$evidence" \
    --am "$AM_HOME" --output "$1"
}
if test "$action" = build; then
  snapshot "$evidence/source-before.json"
  python3 team/tests/generate_vdot_cases.py --output "$data" --coverage-profile=legacy --random-count=0 --smoke-random-count=0 > "$evidence/data-manifest.json"
  make -C team/workloads/vdot-integration ARCH=riscv64-xs MARCH=rv64gcv VDOT_DATA="$data" \
    VDOT_OBJ_ROOT="$evidence/objects" BINARY="$evidence/vdot-integration" -j2
  riscv64-linux-gnu-gcc -c -march=rv64gc -mabi=lp64d team/workloads/hello-vadd/boot-flash.S -o "$evidence/boot-flash.o"
  riscv64-linux-gnu-objcopy -O binary -j .text "$evidence/boot-flash.o" "$evidence/boot-flash.bin"
  snapshot "$evidence/source-after.json"
  cmp "$evidence/source-before.json" "$evidence/source-after.json"
  sha256sum "$evidence"/vdot-integration.{elf,bin} "$evidence/boot-flash.bin" "$data"/* \
    "$AM_HOME/am/build/am-riscv64-xs.a" "$AM_HOME/libs/klib/build/klib-riscv64-xs.a" > "$evidence/workload.sha256"
  riscv64-linux-gnu-gcc --version > "$evidence/cross-compiler.txt"
  echo VDOT_CORE_SMOKE_BUILD_PASS
else
  source_pack=${CORE_SOURCE_PACK:?Set CORE_SOURCE_PACK}
  source_repo=$(python3 -c 'import json; print(json.load(open("build/source-binding.json"))["source"])')
  python3 team/scripts/prepare-core-baseline.py verify --source "$source_repo" --pack "$source_pack" --target "$root" > "$evidence/core-source-verification.json"
  snapshot "$evidence/source-run.json"
  core_evidence=${CORE_BUILD_EVIDENCE:?Set CORE_BUILD_EVIDENCE to current build evidence}
  export NEMU_HOME=${NEMU_HOME:?Set NEMU_HOME to candidate reference}
  reference="$NEMU_HOME/build/riscv64-nemu-interpreter-so"
  python3 team/scripts/vdot_core_checks.py preflight --root "$root" --evidence "$evidence" \
    --core "$core_evidence" --am "$AM_HOME" --nemu "$NEMU_HOME" > "$evidence/workload-verification.log"
  sha256sum build/emu "$reference" > "$evidence/runtime.sha256"
  command=(./build/emu -i "$evidence/vdot-integration.bin" --flash="$evidence/boot-flash.bin" \
           --ram-size=128MB --diff="$reference" --max-cycles=2000000)
  if test "${DUMP_WAVE:-0}" = 1; then
    wave_begin=${VDOT_WAVE_BEGIN:-0}
    wave_end=${VDOT_WAVE_END:-2000000}
    [[ "$wave_begin" =~ ^[0-9]+$ && "$wave_end" =~ ^[0-9]+$ ]]
    (( 10#$wave_begin < 10#$wave_end ))
    command+=(--dump-wave "--wave-path=$evidence/vdot-integration.fst" -b "$wave_begin" -e "$wave_end")
  fi
  printf '%q ' "${command[@]}" > "$evidence/run-command.txt"; printf '\n' >> "$evidence/run-command.txt"
  set +e
  /usr/bin/time -v timeout "${VDOT_RUN_TIMEOUT:-30m}" "${command[@]}" > "$evidence/emulator-output.log" 2>&1
  emulator_rc=$?
  set -e
  printf 'exit_code=%s\n' "$emulator_rc" > "$evidence/emulator.status"
  test "$emulator_rc" = 0
  snapshot "$evidence/source-after-run.json"
  python3 team/scripts/vdot_core_checks.py finish --root "$root" --evidence "$evidence" \
    --core "$core_evidence" --am "$AM_HOME" --nemu "$NEMU_HOME"

fi
