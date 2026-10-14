#!/usr/bin/env bash
# Resume compilation from source-bound, prepared SystemVerilog.
set -euo pipefail
root=$(pwd)
evidence=${TEAM_EVIDENCE_DIR:?Set TEAM_EVIDENCE_DIR}
evidence=$(cd "$evidence" && pwd)
rm -f -- "$evidence/check.json"
exec > >(tee "$evidence/build.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$evidence/build.status"' EXIT
source_pack=${CORE_SOURCE_PACK:?Set CORE_SOURCE_PACK}
source_repo=$(python3 -c 'import json; print(json.load(open("build/source-binding.json"))["source"])')
python3 team/scripts/prepare-core-baseline.py verify --source "$source_repo" --pack "$source_pack" --target "$root"
sha256sum -c "$evidence/fir-input.sha256"
sha256sum -c "$evidence/rtl.sha256" > "$evidence/prepared-rtl-check.log"
test -s build/rtl/SimTop.sv
test -s build/rtl/SimTop.sv.conf
export NOOP_HOME="$root"
export NEMU_HOME=${NEMU_HOME:?Set NEMU_HOME}
export AM_HOME=${AM_HOME:?Set AM_HOME}
export COURSIER_REPOSITORIES=${COURSIER_REPOSITORIES:-https://repo.maven.apache.org/maven2}
export JAVA_TOOL_OPTIONS=${JAVA_TOOL_OPTIONS:--XX:ActiveProcessorCount=2}
export JAVA_OPTS=${JAVA_OPTS:--Xmx1g -XX:ActiveProcessorCount=2}
mill_bin=${CORE_MILL:?Set CORE_MILL}
"$mill_bin" --version | tee "$evidence/mill-version.txt"
grep -q 'Mill Build Tool version 0.12.3' "$evidence/mill-version.txt"
java -version 2> "$evidence/java-version.txt"
verilator --version > "$evidence/verilator-version.txt"
cxx=${CORE_CXX:-clang++-19}
cc=${CORE_CC:-clang-19}
"$cxx" --version > "$evidence/compiler-version.txt"
"$cc" --version > "$evidence/c-compiler-version.txt"
free -h > "$evidence/memory.txt"
cp build/source-binding.json "$evidence/source-binding.json"
mkdir -p build/tools
printf '#!/bin/sh\nexec "%s" "$@"\n' "$mill_bin" > build/tools/mill
chmod +x build/tools/mill
export PATH="$root/build/tools:$PATH"
jobs=${CORE_COMPILE_JOBS:-2}
case "$jobs" in 1|2) ;; *) echo 'CORE_COMPILE_JOBS must be 1 or 2' >&2; exit 2;; esac
opt_fast=${CORE_OPT_FAST:--O1}
case "$opt_fast" in -O1|-O2|-O3) ;; *) echo 'CORE_OPT_FAST must be -O1, -O2 or -O3' >&2; exit 2;; esac
command=(make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 EMU_TRACE=fst
         JVM_XMX=6G JVM_XSS=16m WITH_CHISELDB=0 WITH_CONSTANTIN=0 WITH_ROLLINGDB=0
         "CXX=$cxx" "CC=$cc" "OPT_FAST=$opt_fast" OPT_SLOW=-O0 "-j$jobs")
python3 - "$cxx" "$cc" "$opt_fast" "$evidence" <<'PY'
import hashlib,json,shutil,sys
from pathlib import Path
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
cxx,cc,opt,evidence=sys.argv[1:]
binding=json.loads(Path('build/source-binding.json').read_bytes())
profile=dict(schema=1,source_pack_sha256=binding['source_pack_sha256'],
             rtl_manifest_sha256=digest(Path(evidence)/'rtl.sha256'),
             cxx_sha256=digest(shutil.which(cxx)),cc_sha256=digest(shutil.which(cc)),
             opt_fast=opt,opt_slow='-O0',config='MinimalConfig',num_cores=1,emu_threads=1,trace='fst',
             generated_source_sha256={p.name:digest(p) for p in sorted(Path('build/generated-src').iterdir()) if p.is_file()})
folder=Path('build/emu-compile')
folder.mkdir(exist_ok=True)
stamp=folder/'core-compile-profile.json'
outputs=any(folder.glob('*.o')) or any(folder.glob('*.gch')) or any(folder.glob('*.a')) or Path('build/emu').exists()
if outputs and (not stamp.exists() or json.loads(stamp.read_bytes())!=profile):
    raise SystemExit('Compiler/profile changed or unbound cached objects; move old .o/.gch/.a/emu outputs before rebuilding')
encoded=(json.dumps(profile,sort_keys=True,indent=2)+'\n').encode()
stamp.write_bytes(encoded)
(Path(evidence)/'compile-profile.json').write_bytes(encoded)
print('CORE_COMPILE_PROFILE_BOUND')
PY
printf '%q ' "${command[@]}" > "$evidence/build-command.txt"; printf '\n' >> "$evidence/build-command.txt"
sha256sum "$0" > "$evidence/compile-driver.sha256"
/usr/bin/time -v "${command[@]}"
# If Make regenerated RTL, do not silently reuse the previous lowering receipt.
sha256sum -c "$evidence/rtl.sha256" > "$evidence/compiled-rtl-check.log"
./build/emu --help > "$evidence/emu-help.txt" 2>&1
sha256sum build/emu > "$evidence/emu.sha256"
echo CORE_BASELINE_BUILD_PASS
