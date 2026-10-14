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
  python3 - "$1" "$AM_HOME" <<'PY'
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('team/scripts').resolve()))
from artifact_guard import audit_repo
am=Path(sys.argv[2]); rev='086a238062fdfb3281b745a537b361983d0154b5'
paths=[*Path('team/workloads/vdot-integration').glob('*.[cS]'),Path('team/workloads/vdot-integration/Makefile'),
       *Path('team/workloads/vdot-exceptions').glob('*.[chS]'),
       Path('team/workloads/hello-vadd/boot-flash.S'),Path('team/tests/generate_vdot_cases.py'),
       Path('team/tests/vdot_model.py'),Path('team/scripts/vdot-core-smoke.sh'),Path('team/scripts/artifact_guard.py')]
record=dict(sources={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
            am_rev=rev,am_sources=audit_repo(am,rev,source_roots=('am/src','am/include','libs/klib/src','libs/klib/include')))
Path(sys.argv[1]).write_bytes((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
PY
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
  test "$(cat "$evidence/build.status")" = exit_code=0
  grep -q VDOT_CORE_SMOKE_BUILD_PASS "$evidence/build.log"
  snapshot "$evidence/source-run.json"
  cmp "$evidence/source-before.json" "$evidence/source-run.json"
  sha256sum -c "$evidence/workload.sha256" > "$evidence/workload-verification.log"
  core_evidence=${CORE_BUILD_EVIDENCE:?Set CORE_BUILD_EVIDENCE to current build evidence}
  test "$(cat "$core_evidence/build.status")" = exit_code=0
  grep -q CORE_BASELINE_BUILD_PASS "$core_evidence/build.log"
  sha256sum -c "$core_evidence/emu.sha256"
  sha256sum -c "$core_evidence/rtl.sha256" > "$evidence/rtl-verification.log"
  python3 - "$core_evidence" <<'PY'
import hashlib,json,shlex,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path('team/scripts').resolve()))
from artifact_guard import audit_repo
p=Path(sys.argv[1]); current=json.loads(Path('build/source-binding.json').read_bytes())
assert current==json.loads((p/'source-binding.json').read_bytes()),'Different source/build copy'
profile=json.loads((p/'compile-profile.json').read_bytes())
assert profile==json.loads(Path('build/emu-compile/core-compile-profile.json').read_bytes()),'Changed compilation profile'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert profile['source_pack_sha256']==current['source_pack_sha256'] and profile['rtl_manifest_sha256']==sha(p/'rtl.sha256')
args=shlex.split((p/'build-command.txt').read_text())
for key,field in (('CXX','cxx_sha256'),('CC','cc_sha256')):
    matches=[a.split('=',1)[1] for a in args if a.startswith(key+'=')]
    assert len(matches)==1 and sha(shutil.which(matches[0]))==profile[field],'Changed compiler tool'
for name,digest in profile['generated_source_sha256'].items():
    assert sha(Path('build/generated-src')/name)==digest,'Changed generated DiffTest source'
deps=json.loads((p/'dependency-sources.json').read_bytes())
assert not deps['failures'] and set(deps['sources'])==set(current['modules'])
for name,rev in current['modules'].items():
    assert audit_repo(Path(name),rev,source_roots=('src','macros/src','include','lib-include','source','generator'))==deps['sources'][name],'Changed dependency inputs'
for folder in ('src','macros','scripts'):
    for path in Path(folder).rglob('*'):
        if path.is_file():
            name=path.as_posix()
            if not any(name.startswith(mod+'/') for mod in current['modules']):
                assert name in current['physical_root_sha256'] and path.resolve().is_relative_to(Path.cwd()),'Unknown root compiler input'
PY
  export NEMU_HOME=${NEMU_HOME:?Set NEMU_HOME to candidate reference}
  reference="$NEMU_HOME/build/riscv64-nemu-interpreter-so"
  python3 team/scripts/artifact_guard.py nemu-runtime --repo "$NEMU_HOME" --binary "$reference" --mode reference > "$evidence/nemu-verification.json"
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
  /usr/bin/time -v timeout "${VDOT_RUN_TIMEOUT:-30m}" "${command[@]}" > "$evidence/emulator-output.log" 2>&1
  sha256sum -c "$evidence/runtime.sha256"
  sha256sum -c "$evidence/workload.sha256" > "$evidence/workload-after-run.log"
  snapshot "$evidence/source-after-run.json"
  cmp "$evidence/source-before.json" "$evidence/source-after-run.json"
  python3 - "$evidence" "$core_evidence" <<'PY'
import hashlib,json,re,sys
from pathlib import Path
p=Path(sys.argv[1]); core=Path(sys.argv[2]); log=(p/'emulator-output.log').read_text()
ids={'D03','D05','D07','L04-0-8-9','L04-10-0-9','L04-10-8-0','L04-0-0-9','L04-31-31-31','L05-3-ff','clean-vs',
     'X02-m2','X02-mf2','X03-vl0','X03-vl7','X04-vstart1','X05-vill','X06-VS-off','X07-vm0','X09-v0','X11-VS-1'}
rows=re.findall(r'^T10_CASE id=(\S+) result=(\S+) cause=(\d+) all32=(\d+) pre32=(\d+)$',log,re.M)
assert len(rows)==20 and {r[0] for r in rows}==ids,'Incomplete actual guest coverage'
assert all(r[1]=='PASS' and int(r[2])==(2 if r[0].startswith('X') else 0) and r[3:]==('1','1') for r in rows),'Guest state/trap judge failed'
assert log.count('T10_CORE_SMOKE_PASS legal=10 illegal=10 all32=20 pre32=20')==1
assert 'Difftest enabled' in log and 'HIT GOOD TRAP' in log and 'HIT BAD TRAP' not in log
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
record=dict(status='VDOT_T10_CORE_SMOKE_PASS',legal=10,illegal=10,all32_checked=20,pre32_checked=20,
            source_pack_sha256=json.loads((core/'source-binding.json').read_bytes())['source_pack_sha256'],
            source_manifest_sha256=sha(p/'source-before.json'),runtime_manifest_sha256=sha(p/'runtime.sha256'),
            workload_manifest_sha256=sha(p/'workload.sha256'),complete_t11=False,team_review_signed=False)
(p/'check.json').write_bytes((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(record,sort_keys=True))
PY
fi
