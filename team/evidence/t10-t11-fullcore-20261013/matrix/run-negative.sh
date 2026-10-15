#!/bin/bash
set -euo pipefail
b=/home/lizufan/xiangshan-t10-t11-supervisor-20261013
r="$b/closure-tval-repo";j="$b/runs/final-acceptance-20261013-2155";o="$j/negative-0"
test ! -e "$o";mkdir "$o"
exec > "$o/driver.log" 2>&1
trap 'exit 143' TERM
trap 'rc=$?; printf "driver_exit_code=%s\nfinished_at=%s\n" "$rc" "$(date -Is)" > "$o/driver.status"' EXIT
cd "$r"
image="$b/runs/closure-final-matrix/build-0/vdot-exceptions.bin";ref="$b/nemu-xs-tval/reference/build/riscv64-nemu-interpreter-so"
fixture="$j/negative/reference-bit100.so";flash="$b/runs/hello-vadd-real-core/boot-flash.bin"
python3 -B team/scripts/artifact_guard.py verify-build --kind vdot --mode full --data "$b/runs/closure-final-matrix/data-0" --image "$image" --evidence "$b/runs/closure-final-matrix/build-0" > "$o/image-verification.json"
python3 -B team/scripts/artifact_guard.py nemu-runtime --repo "$b/nemu-xs-tval/reference" --binary "$ref" --mode reference > "$o/reference-verification.json"
sha256sum "$image" "$b/repo/build/emu" "$fixture" "$ref" "$flash" > "$o/inputs.sha256"
set +e
XS_NEGATIVE_VECTOR_TARGET=vdot timeout --signal=TERM --kill-after=5s 1200s "$b/repo/build/emu" -i "$image" --flash="$flash" --ram-size=128MB --diff="$fixture" --max-cycles=1200000 > "$o/run.log" 2>&1
rc=$?
set -e
printf 'exit_code=%s\nfinished_at=%s\n' "$rc" "$(date -Is)" > "$o/status"
python3 - "$o" <<'PY'
import json,pathlib,re,sys
p=pathlib.Path(sys.argv[1]);s=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',(p/'run.log').read_text(errors='replace'))
assert 'exit_code=1' in (p/'status').read_text()
h=re.findall(r'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=(\d+) pc=(0x[0-9a-f]+) instruction=(0x[0-9a-f]+)',s);assert len(h)==1
vd,pc,word=h[0];assert int(word,16)&0xfe00707f==0x0200000b
m=re.search(r'v(\d+)_high different at pc = (0x[0-9a-f]+), right=\s*(0x[0-9a-f]+), wrong =\s*(0x[0-9a-f]+)',s);assert m
assert int(vd)==int(m[1]) and int(m[3],16)^int(m[4],16)==1<<36
assert 'Difftest enabled' in s and 'ABORT' in s
r={'status':'EXPECTED_DIFFERENTIAL_REJECTION','bit':100,'vd':int(vd),'pc':pc,'instruction':word,'negative_exit':1,'same_image_normal_control':'run-0, pending'}
(p/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
PY
