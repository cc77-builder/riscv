"""External tiny Verilator v1/v2 experiment; never touches the full-core build."""
from pathlib import Path
import json
import os
import shlex
import subprocess
import sys

base = Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
os.environ.clear()
os.environ.update(json.loads((base / 'native-environment.json').read_text()))
sys.path.insert(0, '/mnt/c/Code/RVInno/riscv/team/optimizations/o1')
import build_recipe as recipe
import split_recipe

out = base / 'native-clang-link-probe-08'
out.mkdir()
root = base / 'repo'
contract = recipe.capture(root, 'split-clang-v2')
recipe.validate(contract)
recipe.verify(root, contract)
split_recipe.verify_tools(contract, root)
(out / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
source = out / 'Probe.sv'
source.write_text('module Probe(input logic [31:0] a, output logic [31:0] b); assign b = a + 1; endmodule\n')
driver = out / 'main.cpp'
driver.write_text('#include "VProbe.h"\n#include <iostream>\nint main() { VProbe p; p.a=41; p.eval(); std::cout << p.b << "\\n"; return p.b == 42 ? 0 : 1; }\n')
rows = []
def run(label, command, cwd=out):
    result = subprocess.run(command, cwd=cwd, env=recipe.environment(), capture_output=True, text=True)
    (out / (label + '.stdout')).write_text(result.stdout)
    (out / (label + '.stderr')).write_text(result.stderr)
    row = dict(label=label, command=command, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
    rows.append(row)
    (out / 'commands.json').write_text(json.dumps(rows, indent=2) + '\n')
    return result

previous = json.loads((base / 'native-clang-link-probe-06/commands.json').read_text())[-1]
if previous['exit_code'] or '\ng++ ' not in previous['stdout'] or 'Archive ar -rcs' not in previous['stdout']:
    raise ValueError('previous v1 actual Make gap evidence missing')
for profile in ('split-clang-v2',):
    selected = recipe.capture(root, profile)
    folder = out / profile
    command = [contract['compilers']['verilator']['path'], '--cc', '--exe', '--top-module', 'Probe',
               '--Mdir', str(folder), '-CFLAGS', '-std=c++17', '-o', str(folder / 'sim'), str(source), str(driver)]
    generated = run(profile + '-generate', command)
    if generated.returncode:
        raise ValueError('mini Verilator generation failed')
    command = [contract['compilers']['make']['path'], '-f', 'VProbe.mk', 'VM_PARALLEL_BUILDS=1',
               'OPT_FAST=-O3', 'OPT_SLOW=-O0', '-j1', *recipe.make_overrides(selected)]
    built = run(profile + '-make', command, folder)
    if profile == 'split-clang-v2':
        if built.returncode:
            raise ValueError('v2 mini compile/link failed')
        result = run('v2-sim', [str(folder / 'sim')])
        if result.returncode or result.stdout != '42\n':
            raise ValueError('v2 mini simulator failed')
        ld = contract['compilers']['ld']['path']
        cxx = contract['compilers']['cxx']['path']
        selected_ld = run('v2-driver-link-selection', [cxx, '--ld-path=' + ld, '-###', str(folder / 'main.o'), '-o', str(out / 'unused')])
        if selected_ld.returncode or not any(shlex.split(line)[0] == ld for line in selected_ld.stderr.splitlines()
                                            if line.lstrip().startswith('"')):
            raise ValueError('clang driver did not select the bound linker')
        if contract['compilers']['ar']['path'] not in built.stdout or '--ld-path=' + ld not in built.stdout:
            raise ValueError('generated Make did not use the bound linker/archive tools')
recipe.verify(root, contract)
split_recipe.verify_tools(contract, root)
(out / 'result.json').write_text(json.dumps(dict(status='ACTUAL_VERILATOR_CLANG_V2_PASS',
    v1_status='PCH_PASS_UNBOUND_GCC_LINK_OBSERVED', runtime_support_files=len(contract['verilator_support']['files']),
    scope='Tiny real generated simulator, PCH, archive and linked C++ runtime; no full-core result'), indent=2) + '\n')
print('ACTUAL_VERILATOR_CLANG_V2_PASS', out)
