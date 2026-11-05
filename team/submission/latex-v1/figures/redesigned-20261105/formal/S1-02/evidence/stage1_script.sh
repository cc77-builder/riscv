#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
ACTION=${1:-}
case "$ACTION" in nemu|emu|workload|run) ;; *) echo 'Usage: bash team/scripts/stage1.sh {nemu|emu|workload|run}' >&2; exit 2 ;; esac
BUILD_JOBS=${BUILD_JOBS:-2}
JVM_HEAP=${JVM_HEAP:-12G}
TEAM_ID=${TEAM_ID:-riscv-vdot-team}
mkdir -p "$TEAM_EVIDENCE_DIR"
exec > >(tee "$TEAM_EVIDENCE_DIR/$ACTION.log") 2>&1
trap 'rc=$?; printf "exit_code=%s end=%s\n" "$rc" "$(date -Is)" > "$TEAM_EVIDENCE_DIR/$ACTION.status"' EXIT
PS4='+ ${BASH_SOURCE}:${LINENO}: '
set -x
date -Is
git -C "$NOOP_HOME" rev-parse HEAD
git -C "$NOOP_HOME" status --short
case "$ACTION" in
  nemu)
    bash "$TEAM_PROJECT_ROOT/team/scripts/lock-nemu-extra-deps.sh"
    cd "$NEMU_HOME"
    make riscv64-xs-ref_defconfig
    /usr/bin/time -v make -j"$BUILD_JOBS"
    cp .config "$TEAM_EVIDENCE_DIR/nemu.config"
    sha256sum build/riscv64-nemu-interpreter-so > "$TEAM_EVIDENCE_DIR/nemu.sha256"
    echo NEMU_BUILD_PASS
    ;;
  emu)
    cd "$NOOP_HOME"
    /usr/bin/time -v make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 EMU_TRACE=fst JVM_XMX="$JVM_HEAP" -j"$BUILD_JOBS"
    ./build/emu --help
    sha256sum build/emu > "$TEAM_EVIDENCE_DIR/emu.sha256"
    echo XIANGSHAN_EMU_BUILD_PASS
    ;;
  workload)
    cd "$TEAM_WORKLOAD"
    export TEAM_ID
    python3 - <<'PY'
import ipaddress, json, os, subprocess
from pathlib import Path
addresses = subprocess.check_output(['hostname', '-I'], text=True).split()
ipv4 = next((a for a in addresses if ipaddress.ip_address(a).version == 4), 'unavailable')
Path('identity.h').write_text('#define TEAM_ID ' + json.dumps(os.environ['TEAM_ID']) + '\n#define HOST_IP ' + json.dumps(ipv4) + '\n')
PY
    make ARCH=riscv64-xs MARCH=rv64gcv -j"$BUILD_JOBS"
    riscv64-linux-gnu-gcc -c -march=rv64gc -mabi=lp64d boot-flash.S -o build/boot-flash.o
    riscv64-linux-gnu-objcopy -O binary -j .text build/boot-flash.o build/boot-flash.bin
    riscv64-linux-gnu-objdump -d build/boot-flash.o > "$TEAM_EVIDENCE_DIR/boot-flash-disassembly.txt"
    cp build/hello-vadd-riscv64-xs.txt "$TEAM_EVIDENCE_DIR/disassembly.txt"
    sha256sum build/hello-vadd-riscv64-xs.{elf,bin} build/boot-flash.bin > "$TEAM_EVIDENCE_DIR/workload.sha256"
    echo WORKLOAD_BUILD_PASS
    ;;
  run)
    cd "$NOOP_HOME"
    IMAGE="$TEAM_WORKLOAD/build/hello-vadd-riscv64-xs.bin"
    FLASH="$TEAM_WORKLOAD/build/boot-flash.bin"
    test -s "$IMAGE"
    test -s "$FLASH"
    test -x build/emu
    test -s "$NEMU_HOME/build/riscv64-nemu-interpreter-so"
    WAVE_ARGS=()
    if test "${DUMP_WAVE:-0}" = 1; then
      WAVE_ARGS=(--dump-wave --wave-path="$TEAM_EVIDENCE_DIR/hello-vadd.fst" -b 0 -e 2000000)
    fi
    /usr/bin/time -v timeout 20m ./build/emu -i "$IMAGE" --flash="$FLASH" --ram-size=128MB --diff="$NEMU_HOME/build/riscv64-nemu-interpreter-so" --max-cycles=2000000 "${WAVE_ARGS[@]}" > "$TEAM_EVIDENCE_DIR/emulator-output.log" 2>&1
    python3 "$TEAM_PROJECT_ROOT/team/scripts/summarize-run.py" "$TEAM_EVIDENCE_DIR/emulator-output.log" | tee "$TEAM_EVIDENCE_DIR/run-summary.log"
    if test "${DUMP_WAVE:-0}" = 1; then
      test -s "$TEAM_EVIDENCE_DIR/hello-vadd.fst"
      sha256sum "$TEAM_EVIDENCE_DIR/hello-vadd.fst" > "$TEAM_EVIDENCE_DIR/waveform.sha256"
    fi
    ;;
esac
echo "STAGE1_ACTION_PASS action=$ACTION evidence=$TEAM_EVIDENCE_DIR"
