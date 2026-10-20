"""Freeze the compiler/test subset for integration RTL checks; omit imported logs."""
import hashlib,json,runpy,subprocess
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv');out=root/'team/out/sync20-rtl-pack-red'
out.mkdir(exist_ok=False)
h=runpy.run_path(str(root/'team/scripts/prepare-core-baseline.py'))
selected=['src','macros','scripts','build.sc','.gitattributes','team/rtl/vdot',
          'team/optimizations/o2/fu','team/optimizations/o2/parent','team/optimizations/o2/run_rtl.py',
          'team/optimizations/o2/check_negative_fu.py','team/optimizations/o2/test_negative_fu.py']
patch=subprocess.check_output(['git','-C',str(root),'diff','--binary','--ignore-submodules=dirty','HEAD','--',*selected])
(out/'changes.patch').write_bytes(patch)
deps=h['modules'](root);h['verify_dependencies'](root,deps)
record=dict(schema=1,revision=h['git'](root,'rev-parse','HEAD').decode().strip(),
            canonical_root_inputs=h['root_inputs'](root),modules=deps,
            patch_sha256=hashlib.sha256(patch).hexdigest(),untracked_sha256={})
(out/'source-pack.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print('RTL_SUBSET_SOURCE_PACK_PASS',len(record['canonical_root_inputs']),len(deps),flush=True)
h['materialize'](root,out,Path('/home/amesotten/.cache/codex-rvinno/sync20'))
