#!/usr/bin/env bash
# T04 current-source full-core baseline; run in the verified native Linux copy.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
action=${1:?Usage: core-baseline.sh build|workload|run}
case "$action" in build|workload|run) ;; *) exit 2;; esac
evidence=${TEAM_EVIDENCE_DIR:?Set TEAM_EVIDENCE_DIR to the baseline evidence directory}
mkdir -p "$evidence"
evidence=$(cd "$evidence" && pwd)
exec > >(tee "$evidence/$action.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$evidence/$action.status"' EXIT
rm -f -- "$evidence/check.json"
export NOOP_HOME="$root"
export NEMU_HOME=${NEMU_HOME:?Set NEMU_HOME to the verified candidate reference checkout}
export AM_HOME=${AM_HOME:?Set AM_HOME to pinned nexus-am}
export LINUX_GNU_TOOLCHAIN=1
export COURSIER_REPOSITORIES=${COURSIER_REPOSITORIES:-https://repo.maven.apache.org/maven2}
export JAVA_TOOL_OPTIONS=${JAVA_TOOL_OPTIONS:--XX:ActiveProcessorCount=2}
export JAVA_OPTS=${JAVA_OPTS:--Xmx3g -XX:ActiveProcessorCount=2}
mill_bin=${CORE_MILL:?Set CORE_MILL to pinned Mill0.12.3}
"$mill_bin" --version | tee "$evidence/mill-version.txt"
grep -q 'Mill Build Tool version 0.12.3' "$evidence/mill-version.txt"
java -version 2> "$evidence/java-version.txt"
verilator --version | tee "$evidence/verilator-version.txt"
g++ --version > "$evidence/compiler-version.txt"
free -h > "$evidence/memory.txt"
test -f build/source-binding.json
cp build/source-binding.json "$evidence/source-binding.json"

case "$action" in
  build)
    # Make expects a mill launcher in PATH. This project-local shim does not
    # change the user's shell profile or any globally installed tool.
    mkdir -p build/tools
    # Make already supplies -i, Mill's interactive/no-server launch mode.
    printf '#!/bin/sh\nexec "%s" "$@"\n' "$mill_bin" > build/tools/mill
    chmod +x build/tools/mill
    export PATH="$root/build/tools:$PATH"
    command=(make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 EMU_TRACE=fst
             JVM_XMX="${CORE_JVM_HEAP:-6G}" JVM_XSS=16m WITH_CHISELDB=0 WITH_CONSTANTIN=0 WITH_ROLLINGDB=0 -j1)
    printf '%q ' "${command[@]}" > "$evidence/build-command.txt"; printf '\n' >> "$evidence/build-command.txt"
    /usr/bin/time -v "${command[@]}"
    ./build/emu --help > "$evidence/emu-help.txt" 2>&1
    sha256sum build/emu > "$evidence/emu.sha256"
    echo CORE_BASELINE_BUILD_PASS
    ;;
  workload)
    test "$(git -C "$AM_HOME" rev-parse HEAD)" = 086a238062fdfb3281b745a537b361983d0154b5
    export TEAM_ID=${TEAM_ID:-riscv-vdot-team}
    cd team/workloads/hello-vadd
    python3 - <<'PY'
import ipaddress,json,os,subprocess
from pathlib import Path
addresses=subprocess.check_output(['hostname','-I'],text=True).split()
ipv4=next((a for a in addresses if ipaddress.ip_address(a).version==4),'unavailable')
Path('identity.h').write_bytes(('#define TEAM_ID '+json.dumps(os.environ['TEAM_ID'])+'\n#define HOST_IP '+json.dumps(ipv4)+'\n').encode())
PY
    make ARCH=riscv64-xs MARCH=rv64gcv -j1
    riscv64-linux-gnu-gcc -c -march=rv64gc -mabi=lp64d boot-flash.S -o build/boot-flash.o
    riscv64-linux-gnu-objcopy -O binary -j .text build/boot-flash.o build/boot-flash.bin
    cp build/hello-vadd-riscv64-xs.txt "$evidence/disassembly.txt"
    cp identity.h "$evidence/identity.h"
    riscv64-linux-gnu-gcc --version > "$evidence/cross-compiler-version.txt"
    sha256sum "$AM_HOME/am/build/am-riscv64-xs.a" "$AM_HOME/libs/klib/build/klib-riscv64-xs.a" > "$evidence/am-libraries.sha256"
    sha256sum build/hello-vadd-riscv64-xs.{elf,bin} build/boot-flash.bin > "$evidence/workload.sha256"
    echo CORE_BASELINE_WORKLOAD_PASS
    ;;
  run)
    python3 team/scripts/artifact_guard.py nemu-runtime --repo "$NEMU_HOME" \
      --binary "$NEMU_HOME/build/riscv64-nemu-interpreter-so" --mode reference > "$evidence/nemu-verification.json"
    image="$root/team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin"
    flash="$root/team/workloads/hello-vadd/build/boot-flash.bin"
    sha256sum -c "$evidence/emu.sha256"
    (cd team/workloads/hello-vadd && sha256sum -c "$evidence/workload.sha256")
    command=(./build/emu -i "$image" --flash="$flash" --ram-size=128MB
             --diff="$NEMU_HOME/build/riscv64-nemu-interpreter-so" --max-cycles=2000000)
    if test "${DUMP_WAVE:-0}" = 1; then
      command+=(--dump-wave "--wave-path=$evidence/hello-vadd.fst" -b 0 -e 2000000)
    fi
    printf '%q ' "${command[@]}" > "$evidence/run-command.txt"; printf '\n' >> "$evidence/run-command.txt"
    /usr/bin/time -v timeout 20m "${command[@]}" > "$evidence/emulator-output.log" 2>&1
    python3 team/scripts/summarize-run.py "$evidence/emulator-output.log" | tee "$evidence/run-summary.log"
    echo CORE_BASELINE_RUN_PASS
    ;;
esac
