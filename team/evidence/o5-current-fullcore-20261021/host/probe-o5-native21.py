from pathlib import Path
import json, os, runpy

base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
env=json.loads((base/'native-environment.json').read_text())
os.environ.clear(); os.environ.update(env)
path=Path('/mnt/c/Code/RVInno/riscv/team/optimizations/o1/build_recipe.py')
recipe=runpy.run_path(str(path))
contract=recipe['capture'](base/'repo')
recipe['validate'](contract)
recipe['verify'](base/'repo',contract)
out=base/'native-probe-03.json'
with out.open('x') as stream:json.dump(contract,stream,indent=2);stream.write('\n')
print('ACTUAL_NATIVE_CONTRACT_PROBE_PASS',out)
print(recipe['make_command'](contract))
