#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
action=${1:-virt}
data=${BASELINE_DATA:-"$root/team/out/t09-data"}
evidence=${TEAM_EVIDENCE_DIR:-"$root/team/out/t09-$action"}
mkdir -p "$evidence"
workload="$root/team/workloads/rvv-baseline"
harness="$root/team/workloads/vdot-exceptions"
generate() {
  python3 team/tests/generate_baseline.py --output "$data" \
    --random-count="${BASELINE_RANDOM_COUNT:-1000}" \
    --smoke-random-count="${BASELINE_SMOKE_RANDOM_COUNT:-1000}" > "$evidence/generated.json"
}
metadata() {
  git rev-parse HEAD > "$evidence/team.sha"
  git status --short > "$evidence/working-tree.txt"
  riscv64-linux-gnu-gcc --version > "$evidence/compiler.txt"
  cp "$data/manifest.json" "$evidence/data-manifest.json"
  cp "$data/baseline-manifest.json" "$evidence/baseline-manifest.json"
  sha256sum "$data"/{cases.jsonl,cases.h,baseline-sites.S,baseline-stubs.h,manifest.json,baseline-manifest.json} > "$evidence/inputs.sha256"
  sha256sum "$workload"/{main.c,baseline.S,Makefile} "$harness"/{harness.S,harness.h,layout.h,judge.c,diagnostics.c,diagnostics.h,virt-start.S,virt-platform.c,virt.ld} \
    team/tests/{generate_baseline.py,generate_vdot_cases.py,vdot_model.py} \
    team/scripts/{baseline-tests.sh,check-baseline-run.py,artifact_guard.py} > "$evidence/source.sha256"
}
check() {
  python3 team/scripts/check-baseline-run.py "$evidence/run.log" --exit-code "$run_rc" --data "$data" | tee "$evidence/check.json"
}
case "$action" in
  virt)
    generate
    riscv64-linux-gnu-gcc -std=gnu11 -O2 -g -Wall -Wextra -Werror -ffreestanding -fno-builtin \
      -fno-stack-protector -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns \
      -march=rv64gcv -mabi=lp64d -mcmodel=medany -nostdlib -static -DVDOT_VIRT=1 -I"$harness" -I"$data" \
      -Wl,-T,"$harness/virt.ld",--build-id=none "$harness/virt-start.S" "$harness/virt-platform.c" \
      "$workload/main.c" "$harness/judge.c" "$harness/diagnostics.c" "$harness/harness.S" "$workload/baseline.S" -o "$evidence/workload.elf"
    riscv64-linux-gnu-objdump -d "$evidence/workload.elf" > "$evidence/disassembly.txt"
    sha256sum "$evidence/workload.elf" > "$evidence/workload.sha256"
    metadata
    python3 team/scripts/artifact_guard.py capture-build --kind baseline --arch qemu-virt --mode full --data "$data" --evidence "$evidence"
    qemu-system-riscv64 --version > "$evidence/qemu-version.txt"
    printf 'platform=qemu-virt vlen=128 timeout=%s\n' "${BASELINE_RUN_TIMEOUT:-300s}" > "$evidence/runtime-parameters.txt"
    set +e
    timeout "${BASELINE_RUN_TIMEOUT:-300s}" qemu-system-riscv64 -machine virt \
      -cpu rv64,v=true,vlen=128,elen=64,vext_spec=v1.0 -m 128M -smp 1 -nographic -bios none \
      -kernel "$evidence/workload.elf" > "$evidence/run.log" 2>&1
    run_rc=$?
    set -e
    printf '%s\n' "$run_rc" > "$evidence/exit-code.txt"
    check
    ;;
  build-xs)
    generate
    export AM_HOME=${AM_HOME:-"${TEAM_XS_ENV_ROOT:-$HOME/riscv-lab/xs-env}/nexus-am"}
    export LINUX_GNU_TOOLCHAIN=1
    source team/versions.env
    test "$(git -C "$AM_HOME" rev-parse HEAD)" = "$AM_REV"
    git -C "$AM_HOME" diff --quiet HEAD --
    make -C "$workload" ARCH=riscv64-xs MARCH=rv64gcv VDOT_DATA="$data" \
      VDOT_OBJ_ROOT="$evidence/objects" BINARY="$evidence/rvv-baseline" -j"${BUILD_JOBS:-2}" > "$evidence/build.txt" 2>&1
    riscv64-linux-gnu-objdump -d "$evidence/rvv-baseline.elf" > "$evidence/disassembly.txt"
    metadata
    git -C "$AM_HOME" rev-parse HEAD > "$evidence/am.sha"
    sha256sum "$evidence"/rvv-baseline.{elf,bin} > "$evidence/workload.sha256"
    python3 team/scripts/artifact_guard.py capture-build --kind baseline --arch riscv64-xs --mode full --data "$data" --evidence "$evidence" --am "$AM_HOME"
    ;;
  run-nemu)
    image=${BASELINE_IMAGE:?set BASELINE_IMAGE to the build-xs rvv-baseline.bin}
    build_evidence=$(dirname "$image")
    python3 team/scripts/artifact_guard.py verify-build --kind baseline --mode full --data "$data" --image "$image" --evidence "$build_evidence" > "$evidence/build-verification.json"
    sha256sum -c "$build_evidence/inputs.sha256" > "$evidence/input-verification.txt"
    sha256sum -c "$build_evidence/workload.sha256" > "$evidence/image-verification.txt"
    sha256sum -c "$build_evidence/source.sha256" > "$evidence/source-verification.txt"
    nemu_bin=${VDOT_NEMU_BIN:?set VDOT_NEMU_BIN to a standalone NEMU executable}
    test -x "$nemu_bin"
    metadata
    sha256sum "$nemu_bin" > "$evidence/nemu-binary.sha256"
    export NEMU_HOME=${NEMU_HOME:?set NEMU_HOME to the actual verified candidate checkout}
    python3 team/scripts/artifact_guard.py nemu-runtime --repo "$NEMU_HOME" --binary "$nemu_bin" --mode standalone > "$evidence/nemu-verification.json"
    git -C "$NEMU_HOME" rev-parse HEAD > "$evidence/nemu.sha"
    cp "$NEMU_HOME/.config" "$evidence/nemu.config"
    cp "$NEMU_HOME/build/vdot-provenance.json" "$evidence/nemu-provenance.json"
    printf 'platform=nemu binary=%s timeout=%s\n' "$nemu_bin" "${BASELINE_RUN_TIMEOUT:-300s}" > "$evidence/runtime-parameters.txt"
    set +e
    timeout "${BASELINE_RUN_TIMEOUT:-300s}" "$nemu_bin" -b "$image" > "$evidence/run.log" 2>&1
    run_rc=$?
    set -e
    printf '%s\n' "$run_rc" > "$evidence/exit-code.txt"
    check
    ;;
  *) echo 'Usage: baseline-tests.sh {virt|build-xs|run-nemu}' >&2; exit 2;;
esac
echo "BASELINE_ACTION_DONE action=$action evidence=$evidence"
