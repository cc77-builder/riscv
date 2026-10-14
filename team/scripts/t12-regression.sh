#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
cd "$TEAM_PROJECT_ROOT"
action=${1:?Usage: t12-regression.sh build-workload|run}
run_root=${T12_RUN_ROOT:?set T12_RUN_ROOT to a new absolute evidence directory}
case "$run_root" in /*) ;; *) echo 'T12_RUN_ROOT must be absolute' >&2; exit 2;; esac
case "$action" in
  build-workload)
    if test -e "$run_root"; then echo "Refusing to overwrite evidence: $run_root" >&2; exit 2; fi
    mkdir -p "$run_root/data"
    python3 -B team/workloads/vdot-regression/generate.py --output "$run_root/data" > "$run_root/generated.json"
    make -C team/workloads/vdot-regression ARCH=riscv64-xs MARCH=rv64gcv \
      T12_DATA="$run_root/data" T12_OBJ_ROOT="$run_root/objects" \
      BINARY="$run_root/vdot-regression" -j"${BUILD_JOBS:-2}" > "$run_root/build.log" 2>&1
    sha256sum team/workloads/vdot-regression/{generate.py,main.c,Makefile} \
      team/models/vdot/model.py "$run_root/data"/{sequences.S,sequences.h,manifest.json} \
      "$run_root/vdot-regression.bin" "$run_root/vdot-regression.elf" > "$run_root/inputs.sha256"
    git rev-parse HEAD > "$run_root/source.sha"
    git diff --binary > "$run_root/source.patch"
    git status --short > "$run_root/working-tree.txt"
    echo T12_BUILD_PASS
    ;;
  run)
    test -f "$run_root/inputs.sha256"
    if test -e "$run_root/run.log"; then echo 'Run log already exists; build a new run directory' >&2; exit 2; fi
    sha256sum -c "$run_root/inputs.sha256" > "$run_root/input-verification.txt"
    nemu=${T12_NEMU_ROOT:?set T12_NEMU_ROOT to the verified patched reference checkout}
    reference="$nemu/build/riscv64-nemu-interpreter-so"
    emu=${VDOT_EMU_BIN:-"$PWD/build/emu"}
    test -x "$emu"
    python3 -B team/scripts/artifact_guard.py nemu-runtime --repo "$nemu" \
      --binary "$reference" --mode reference > "$run_root/reference-verification.json"
    riscv64-linux-gnu-gcc -c -march=rv64gc -mabi=lp64d team/workloads/hello-vadd/boot-flash.S -o "$run_root/boot-flash.o"
    riscv64-linux-gnu-objcopy -O binary -j .text "$run_root/boot-flash.o" "$run_root/boot-flash.bin"
    sha256sum "$emu" "$reference" "$run_root/boot-flash.bin" > "$run_root/runtime.sha256"
    command=(timeout "${T12_TIMEOUT:-120m}" stdbuf -o0 -e0 "$emu" -i "$run_root/vdot-regression.bin"
      --flash="$run_root/boot-flash.bin" --ram-size=128MB --diff="$reference" --max-cycles=2000000)
    printf '%q ' "${command[@]}" > "$run_root/command.sh"
    printf '\n' >> "$run_root/command.sh"
    date -Is > "$run_root/started.txt"
    set +e
    "${command[@]}" > "$run_root/run.log" 2>&1
    rc=$?
    set -e
    printf '%s\n' "$rc" > "$run_root/exit-code.txt"
    date -Is > "$run_root/finished.txt"
    sha256sum -c "$run_root/runtime.sha256" > "$run_root/runtime-after.txt"
    python3 -B team/scripts/check-vdot-regression.py "$run_root/run.log" \
      --manifest "$run_root/data/manifest.json" --exit-code "$rc" --output "$run_root/result.json"
    ;;
  *) echo "Unknown action: $action" >&2; exit 2;;
esac
