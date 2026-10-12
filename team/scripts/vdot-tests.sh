#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
action=${1:-host}
mode=${2:-full}
case "$mode" in full|selftest) ;; *) echo 'mode must be full or selftest' >&2; exit 2;; esac
case "$action" in virt-selftest) mode=selftest;; virt-full-negative) mode=full;; esac
data="$root/team/out/t05"
evidence=${TEAM_EVIDENCE_DIR:-"$root/team/out/t05e-$action-$mode"}
mkdir -p "$evidence"
python3 team/tests/generate_vdot_cases.py --output "$data" > "$evidence/data-manifest.json"
workload="$root/team/workloads/vdot-exceptions"

metadata() {
  git rev-parse HEAD > "$evidence/team.sha"
  git status --short > "$evidence/working-tree.txt"
  sha256sum "$data/cases.jsonl" "$data/cases.h" "$data/word-sites.S" "$data/stubs.h" > "$evidence/inputs.sha256"
  sha256sum "$workload"/*.[chS] "$workload/Makefile" "$workload/virt.ld" \
    "$root/team/scripts/vdot-tests.sh" "$root/team/scripts/check-vdot-run.py" > "$evidence/source.sha256"
  riscv64-linux-gnu-gcc --version > "$evidence/compiler.txt"
}
build_virt() {
  local selftest=$1
  riscv64-linux-gnu-gcc -std=gnu11 -O2 -g -Wall -Wextra -Werror -ffreestanding -fno-builtin \
    -fno-stack-protector -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns \
    -march=rv64gcv -mabi=lp64d -mcmodel=medany -nostdlib -static \
    -DVDOT_VIRT=1 -DVDOT_MODE_SELFTEST="$selftest" -I"$workload" -I"$data" \
    -Wl,-T,"$workload/virt.ld",--build-id=none \
    "$workload/virt-start.S" "$workload/virt-platform.c" "$workload/main.c" \
    "$workload/judge.c" "$workload/harness.S" "$workload/fixed-sites.S" -o "$evidence/workload.elf"
  riscv64-linux-gnu-objdump -d "$evidence/workload.elf" > "$evidence/disassembly.txt"
  sha256sum "$evidence/workload.elf" > "$evidence/workload.sha256"
  metadata
}
run_virt() {
  qemu-system-riscv64 --version > "$evidence/qemu-version.txt"
  set +e
  timeout 30s qemu-system-riscv64 -machine virt -cpu rv64,v=true,vlen=128,elen=64,vext_spec=v1.0 \
    -m 128M -smp 1 -nographic -bios none -kernel "$evidence/workload.elf" \
    > "$evidence/run.log" 2>&1
  run_rc=$?
  set -e
  printf '%s\n' "$run_rc" > "$evidence/exit-code.txt"
}
case "$action" in
  host)
    python3 -m unittest discover -s team/tests -p 'test_*.py' -v 2>&1 | tee "$evidence/model-tests.txt"
    gcc -std=c11 -Wall -Wextra -Werror -I"$workload" "$workload/judge.c" \
      team/tests/test_exception_judge.c -o "$evidence/judge-test"
    "$evidence/judge-test" | tee "$evidence/judge-tests.txt"
    ;;
  virt-selftest)
    build_virt 1; run_virt
    test "$run_rc" = 0
    python3 team/scripts/check-vdot-run.py "$evidence/run.log" --mode selftest --exit-code "$run_rc" --data "$data"
    ;;
  virt-full-negative)
    build_virt 0; run_virt
    test "$run_rc" = 3
    python3 team/scripts/check-vdot-run.py "$evidence/run.log" --mode full --exit-code "$run_rc" --data "$data" --expect-unextended-rejection
    ;;
  build-xs)
    export AM_HOME=${AM_HOME:-"${TEAM_XS_ENV_ROOT:-$HOME/riscv-lab/xs-env}/nexus-am"}
    export LINUX_GNU_TOOLCHAIN=1
    test "$(git -C "$AM_HOME" rev-parse HEAD)" = 086a238062fdfb3281b745a537b361983d0154b5
    if ! git -C "$AM_HOME" diff --quiet HEAD --; then echo 'nexus-am tracked files differ from pinned version' >&2; exit 2; fi
    make -C "$workload" ARCH=riscv64-xs MARCH=rv64gcv MODE="$mode" VDOT_DATA="$data" \
      VDOT_OBJ_ROOT="$evidence/objects" BINARY="$evidence/vdot-exceptions" -j"${BUILD_JOBS:-2}"
    metadata
    sha256sum "$evidence/vdot-exceptions.elf" "$evidence/vdot-exceptions.bin" > "$evidence/workload.sha256"
    ;;
  run-nemu|run-rtl)
    image=${VDOT_IMAGE:-"$root/team/out/t05e-build-xs-$mode/vdot-exceptions.bin"}
    build_evidence=$(dirname "$image")
    test -s "$image"
    sha256sum -c "$build_evidence/inputs.sha256" > "$evidence/input-verification.txt"
    sha256sum -c "$build_evidence/workload.sha256" > "$evidence/image-verification.txt"
    export NEMU_HOME=${NEMU_HOME:-"${TEAM_XS_ENV_ROOT:-$HOME/riscv-lab/xs-env}/NEMU"}
    git -C "$NEMU_HOME" rev-parse HEAD > "$evidence/nemu.sha"
    git -C "$NEMU_HOME" status --short > "$evidence/nemu-working-tree.txt"
    if test -f "$NEMU_HOME/.config"; then cp "$NEMU_HOME/.config" "$evidence/nemu.config"; fi
    metadata
    if test "$action" = run-nemu; then
      nemu_bin=${VDOT_NEMU_BIN:?set VDOT_NEMU_BIN to a standalone NEMU executable, not the shared reference library}
      test -x "$nemu_bin"
      sha256sum "$nemu_bin" > "$evidence/nemu-binary.sha256"
      set +e
      timeout "${VDOT_RUN_TIMEOUT:-120s}" "$nemu_bin" -b "$image" > "$evidence/run.log" 2>&1
      run_rc=$?
      set -e
      printf '%s\n' "$run_rc" > "$evidence/exit-code.txt"
      python3 team/scripts/check-vdot-run.py "$evidence/run.log" --mode "$mode" --exit-code "$run_rc" --data "$data"
    else
      emu_bin=${VDOT_EMU_BIN:-"$root/build/emu"}
      reference=${VDOT_NEMU_REF:-"$NEMU_HOME/build/riscv64-nemu-interpreter-so"}
      test -x "$emu_bin"; test -s "$reference"
      riscv64-linux-gnu-gcc -c -march=rv64gc -mabi=lp64d team/workloads/hello-vadd/boot-flash.S -o "$evidence/boot-flash.o"
      riscv64-linux-gnu-objcopy -O binary -j .text "$evidence/boot-flash.o" "$evidence/boot-flash.bin"
      sha256sum "$emu_bin" "$reference" "$evidence/boot-flash.bin" > "$evidence/runtime.sha256"
      set +e
      timeout "${VDOT_RUN_TIMEOUT:-20m}" "$emu_bin" -i "$image" --flash="$evidence/boot-flash.bin" \
        --ram-size=128MB --diff="$reference" --max-cycles="${VDOT_MAX_CYCLES:-5000000}" > "$evidence/run.log" 2>&1
      run_rc=$?
      set -e
      printf '%s\n' "$run_rc" > "$evidence/exit-code.txt"
      python3 team/scripts/check-vdot-run.py "$evidence/run.log" --mode "$mode" --exit-code "$run_rc" --data "$data" --require-diff
    fi
    ;;
  *) echo 'Usage: bash team/scripts/vdot-tests.sh {host|virt-selftest|virt-full-negative|build-xs|run-nemu|run-rtl} [full|selftest]' >&2; exit 2;;
esac
echo "VDOT_ACTION_DONE action=$action evidence=$evidence"
