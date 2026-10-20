import hashlib,json,runpy
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv')
base=Path('/home/amesotten/.cache/codex-rvinno/sync20')
native=Path((root/'team/out/sync20-rtl-pack-red-windows/build-copy.txt').read_text().strip())
h=runpy.run_path(str(root/'team/scripts/prepare-core-baseline.py'))
canonical=h['root_inputs'](root)
assert canonical==h['root_inputs'](native),'merged compiler inputs differ from actual tested source'
deps=h['modules'](root)
assert deps==h['modules'](native)
h['verify_dependencies'](native,deps)
physical={n:hashlib.sha256((native/n).read_bytes()).hexdigest() for n in canonical}
for n,d in json.loads((base/'green-overlays.json').read_text()).items():
 assert hashlib.sha256((native/n).read_bytes()).hexdigest()==d,n
result=dict(status='MERGED_COMPILER_SOURCE_BINDING_PASS',base='6ea846edb1e56f80d7e7858984a6f367be34bcf0',
 incoming='676ec737291b3818c0f4bf3d9f542f85fddb53c7',root_inputs=canonical,
 physical_native_sha256=physical,dependencies=deps,
 runner_limit='Green runner snapshot predates the added shared compiler-inventory pre/post guard; its exact version is archived. This independent final gate verifies the actual tested compiler inputs and all dependency pins.',
 fullcore_emu_executed=False,performance_measured=False)
(base/'merged-source-binding.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'],len(canonical),len(deps))
