#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
ACTION=${1:-}
case "$ACTION" in nemu|emu|workload|run) ;; *) echo 'Usage: bash team/scripts/stage1.sh {nemu|emu|workload|run}' >&2; exit 2 ;; esac
BUILD_JOBS=${BUILD_JOBS:-2}
JVM_HEAP=${JVM_HEAP:-12G}
TEAM_ID=${TEAM_ID:-riscv-vdot-team}
mkdir -p "$TEAM_EVIDENCE_DIR"
TEAM_EVIDENCE_DIR=$(cd "$TEAM_EVIDENCE_DIR" && pwd)
# One invocation owns each action's evidence; failed attempts remain intact.
for existing in "$ACTION.log" "$ACTION.status"; do
  test ! -e "$TEAM_EVIDENCE_DIR/$existing" || { echo "Evidence already exists: $existing; choose a new directory" >&2; exit 2; }
done
mkdir "$TEAM_EVIDENCE_DIR/.$ACTION.claimed" || { echo 'Action already claimed; choose a new evidence directory' >&2; exit 2; }
TEAM_WORKLOAD=${TEAM_STAGE1_WORKLOAD_DIR:-"$TEAM_EVIDENCE_DIR/workload"}
exec > >(tee "$TEAM_EVIDENCE_DIR/$ACTION.log") 2>&1
trap 'rc=$?; printf "exit_code=%s end=%s\n" "$rc" "$(date -Is)" > "$TEAM_EVIDENCE_DIR/$ACTION.status"' EXIT
PS4='+ ${BASH_SOURCE}:${LINENO}: '
set -x
date -Is
if git -C "$NOOP_HOME" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$NOOP_HOME" rev-parse HEAD
  git -C "$NOOP_HOME" status --short
fi
sha256sum "$TEAM_PROJECT_ROOT/team/scripts/stage1.sh" "$TEAM_PROJECT_ROOT/team/workloads/hello-vadd/"{main.c,vadd.S,Makefile,boot-flash.S}
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
    mkdir "$TEAM_WORKLOAD" || { echo 'Workload directory must be new' >&2; exit 2; }
    cp "$TEAM_PROJECT_ROOT/team/workloads/hello-vadd/"{main.c,vadd.S,Makefile,boot-flash.S} "$TEAM_WORKLOAD/"
    cd "$TEAM_WORKLOAD"
    export TEAM_ID
    python3 - <<'PY'
import ipaddress, json, os, subprocess
from pathlib import Path
addresses = subprocess.check_output(['hostname', '-I'], text=True).split()
ipv4 = next((a for a in addresses if ipaddress.ip_address(a).version == 4), 'unavailable')
team = os.environ['TEAM_ID']
if not team or not team.isprintable():
    raise SystemExit('TEAM_ID must be nonempty and printable')
status = 'placeholder' if team == 'riscv-vdot-team' else 'configured'
identity = dict(team_id=team, host_ip=ipv4, status=status)
Path('identity.json').write_text(json.dumps(identity, indent=2) + '\n')
Path('identity.h').write_text('#define TEAM_ID ' + json.dumps(team) + '\n#define HOST_IP ' + json.dumps(ipv4) + '\n#define IDENTITY_STATUS ' + json.dumps(status) + '\n')
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
    EMU=${TEAM_STAGE1_EMU:-"$NOOP_HOME/build/emu"}
    REF=${TEAM_STAGE1_REF:-"$NEMU_HOME/build/riscv64-nemu-interpreter-so"}
    WAVE_ARGS=()
    if test "${DUMP_WAVE:-0}" = 1; then
      WAVE_ARGS=(--wave-begin "${WAVE_BEGIN:-0}" --wave-end "${WAVE_END:-${MAX_CYCLES:-2000000}}")
    fi
    python3 "$TEAM_PROJECT_ROOT/team/scripts/stage1-run.py" \
      --emu "$EMU" --reference "$REF" \
      --image "$TEAM_WORKLOAD/build/hello-vadd-riscv64-xs.bin" \
      --flash "$TEAM_WORKLOAD/build/boot-flash.bin" --identity "$TEAM_WORKLOAD/identity.json" \
      --runtime-home "${TEAM_STAGE1_RUNTIME_HOME:-$NOOP_HOME}" --output "$TEAM_EVIDENCE_DIR/run" \
      --max-cycles "${MAX_CYCLES:-2000000}" --timeout "${RUN_TIMEOUT:-1200}" "${WAVE_ARGS[@]}"
    ;;
esac
echo "STAGE1_ACTION_PASS action=$ACTION evidence=$TEAM_EVIDENCE_DIR"
