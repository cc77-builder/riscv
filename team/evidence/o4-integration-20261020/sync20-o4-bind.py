from pathlib import Path
import runpy,hashlib,json
root=Path('/mnt/c/Code/RVInno/riscv')
base=Path('/home/amesotten/.cache/codex-rvinno/sync20')
native=base/'source-d13def17dc8de4b8'
h=runpy.run_path(str(root/'team/scripts/prepare-core-baseline.py'))
a=h['root_inputs'](root);b=h['root_inputs'](native)
if a!=b:raise ValueError('current compiler inputs differ')
deps=h['modules'](root)
if deps!=h['modules'](native):raise ValueError('dependency pins differ')
h['verify_dependencies'](native,deps)
name='team/optimizations/o4/GenerateVDotCost.scala'
source=(root/name).read_bytes().replace(b'\r\n',b'\n')
if source!=(native/name).read_bytes():raise ValueError('cost harness differs')
record=dict(status='CURRENT_O4_COMPILE_INPUTS_PASS',base_checkpoint='769b3b4b1',incoming='9b6cf074951dbd51e1670c5fbc7111a97c362b3f',root_inputs=a,dependencies=deps,cost_harness_sha256=hashlib.sha256(source).hexdigest(),scope='Mill compile only; no new RTL generation, mapping, STA, EMU or performance run')
(base/'o4-compile-binding.json').write_text(json.dumps(record,indent=2)+'\n')
print(record['status'],len(a),len(deps))
