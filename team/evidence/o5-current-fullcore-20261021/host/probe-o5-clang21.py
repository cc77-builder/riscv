"""Real native compiler probe only; do not modify or build the native checkout."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

base = Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
os.environ.clear()
os.environ.update(json.loads((base / 'native-environment.json').read_text()))
sys.path.insert(0, '/mnt/c/Code/RVInno/riscv/team/optimizations/o1')
import build_recipe
import split_recipe

for module in (build_recipe, split_recipe):
    if b'\r' in Path(module.__file__).read_bytes():
        raise ValueError('probe helper must have LF bytes: ' + module.__file__)
contract = build_recipe.capture(base / 'repo', 'split-clang-v1')
build_recipe.validate(contract)
build_recipe.verify(base / 'repo', contract)
split_recipe.verify_tools(contract, base / 'repo')
out = base / 'native-clang-probe-05'
out.mkdir()
source = out / 'hello.cpp'
source.write_text('#include <iostream>\nint main() { std::cout << "CLANG_CPP_DRIVER_LINK_PASS\\n"; }\n')
binary = out / 'hello'
command = [contract['compilers']['cxx']['path'], '-std=c++17', '-O3', str(source), '-o', str(binary)]
compiled = subprocess.run(command, env=build_recipe.environment(), capture_output=True, text=True)
run = subprocess.run([str(binary)], capture_output=True, text=True) if compiled.returncode == 0 else None
record = dict(contract=contract, commands=split_recipe.commands(contract), probe_command=command,
    compile_exit=compiled.returncode, compile_stdout=compiled.stdout, compile_stderr=compiled.stderr,
    run_exit=run.returncode if run else None, run_stdout=run.stdout if run else None,
    run_stderr=run.stderr if run else None,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    scope='Actual installed Clang 19 driver capture, tool verification and C++ std::cout linking; no hardware build or EMU run')
with (out / 'receipt.json').open('x') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
if compiled.returncode or run is None or run.returncode or run.stdout != 'CLANG_CPP_DRIVER_LINK_PASS\n':
    raise ValueError('actual Clang C++ driver probe failed; preserve receipt')
print('ACTUAL_CLANG_NATIVE_PROBE_PASS', out / 'receipt.json')
print(json.dumps({role: contract['compilers'][role] for role in ('cxx', 'cc')}, indent=2))
