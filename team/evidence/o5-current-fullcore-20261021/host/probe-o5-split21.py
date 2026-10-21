from pathlib import Path
import json,os,sys
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
os.environ.clear();os.environ.update(json.loads((base/'native-environment.json').read_text()))
sys.path.insert(0,'/mnt/c/Code/RVInno/riscv/team/optimizations/o1')
import build_recipe,split_recipe
contract=build_recipe.capture(base/'repo','split-v1')
build_recipe.validate(contract)
build_recipe.verify(base/'repo',contract)
split_recipe.verify_tools(contract,base/'repo')
out=base/'native-split-probe-04.json'
with out.open('x') as stream:json.dump(dict(contract=contract,commands=split_recipe.commands(contract)),stream,indent=2);stream.write('\n')
print('ACTUAL_SPLIT_NATIVE_PROBE_PASS',out)
