#!/usr/bin/env bash
set -euo pipefail
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/home/amesotten/.cache/codex-rvinno/o1-optimization-20261019/source-21dce14309ebe4d2/build/tools:$JAVA_HOME/bin:$PATH
python3 -B - <<'PY'
import json,sys,os,subprocess
from pathlib import Path
sys.path.insert(0, '/mnt/c/Code/RVInno/riscv/team/optimizations/o1')
import build_recipe
root=Path('/home/amesotten/.cache/codex-rvinno/o1-optimization-20261019/source-21dce14309ebe4d2')
contract=build_recipe.capture(root)
build_recipe.validate(contract)
build_recipe.verify(root,contract)
os.environ.update(L2_CACHE_SIZE='512',NO_DIFF='1',CPATH='/injected',PGO_CFLAGS='-O0',BASH_ENV='/injected.sh')
assert build_recipe.capture(root)==contract
output=subprocess.check_output(['bash','-c','env'],env=build_recipe.environment(),text=True)
assert not any(line.split('=',1)[0] in {'L2_CACHE_SIZE','NO_DIFF','CPATH','PGO_CFLAGS','BASH_ENV'} for line in output.splitlines())
out=Path('/mnt/c/Code/RVInno/riscv/team/out/o1-optimization-recipe-probe-02.json')
with out.open('x') as f:
    json.dump(dict(status='NATIVE_BUILD_RECIPE_PROBE_PASS', contract=contract, environment_injection_rejected=True,
                   command=build_recipe.make_command(contract, '/tmp/test build')),f,indent=2)
print('NATIVE_BUILD_RECIPE_PROBE_PASS')
PY
