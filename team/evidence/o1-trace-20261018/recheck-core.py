#!/usr/bin/env python3
"""Recompute archived CPU observations; this does not launch another CPU run."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED = '0fc1f1b3a164683fbdd319f86a8b2308e4cf059c58266a77e02453ed3cc0d302'
EMU = '0748665846a3c34dcbc9c069edc7c28e9aa117fc0933743bb6bf7c0939a185a2'
REFERENCE = 'e8c9c9be7d798a348a0f8c5ad3a4c601c27511a1967ca3c4cc0af576233f52a1'
sys.path.insert(0, str(ROOT/'team/optimizations/o1'))
from check_trace import audit, require
from run_trace_core import control_check


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(out):
    archive = HERE/'core-validation.tar.gz'
    require(sha(archive) == EXPECTED, 'core archive changed')
    out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as source:
        seen, total = set(), 0
        for item in source:
            path = PurePosixPath(item.name)
            require(not path.is_absolute() and '..' not in path.parts and item.isfile()
                    and item.name not in seen, 'unsafe/duplicate member')
            total += item.size
            require(total < 512*1024**2, 'unexpected archive size')
            seen.add(item.name)
            target = out/path
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(item) as src, target.open('wb') as dst:
                shutil.copyfileobj(src, dst)
    inventory = json.loads((HERE/'core-payload.json').read_text())['files']
    require(set(inventory) == seen and all(sha(out/n) == h for n,h in inventory.items()), 'changed archive payload')
    require((out/'core-build/emu.sha256').read_text().split()[0] == EMU, 'wrong compiled EMU')
    require((out/'core-build/build.status').read_text().strip() == 'exit_code=0' and
            (out/'core-build/split-build.status').read_text().strip() == 'exit_code=0', 'build failure')
    def runtime(folder):
        receipt = json.loads((folder/'runtime.json').read_text())
        require(receipt['exit_code'] == 0, 'runtime failure')
        require(all(sha(folder/n) == h for n,h in receipt['raw_sha256'].items()), 'changed raw log')
        emu_paths = [p for p,h in receipt['files'].items() if p.endswith('/build/emu') and h == EMU]
        refs = [p for p,h in receipt['files'].items() if p.endswith('/riscv64-nemu-interpreter-so') and h == REFERENCE]
        require(len(emu_paths) == len(refs) == 1 and receipt['command'].count(emu_paths[0]) == 1 and
                receipt['command'].count('--diff='+refs[0]) == 1 and '--ram-size=128MB' in receipt['command'], 'wrong runtime roles')
        stdout = (folder/'stdout.log').read_text()
        stderr = (folder/'stderr.log').read_text()
        require(stdout.count('Difftest enabled.') == 1 and 'The reference model is '+refs[0] in stdout+stderr,
                'missing live reference')
        require(stdout.count('HIT GOOD TRAP') == 1 and not re.search(r'BAD TRAP|Assertion failed|different at pc', stdout+stderr),
                'failed workload')
        return receipt, stdout, stderr
    receipt, stdout, _ = runtime(out/'core-runs-01/hello')
    require(stdout.count('HELLO_VADD_PASS') == 1, 'hello/vadd failure')
    receipt, stdout, stderr = runtime(out/'core-runs-01/control')
    trace = audit(stderr.splitlines(), 2, 'fullcore')
    require(trace == json.loads((out/'core-runs-01/control/trace.json').read_text()), 'control trace mismatch')
    manifest = json.loads((out/'core-runs-01/images/control-pressure-v2/data/manifest.json').read_text())
    checked = control_check(stderr+stdout, trace, manifest, receipt['exit_code'])
    require(checked == json.loads((out/'core-runs-01/control/checked.json').read_text()), 'control result mismatch')
    control_trace = trace
    receipt, stdout, stderr = runtime(out/'batch-01')
    trace = audit(stderr.splitlines(), 2, 'fullcore')
    require(trace == json.loads((out/'batch-01/trace.json').read_text()), 'batch trace mismatch')
    manifest = json.loads((out/'batch-01/data/manifest.json').read_text())
    spec = importlib.util.spec_from_file_location('compiled_batch', ROOT/'team/workloads/vdot-perf/check.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    checker.check_compiled_cases(out/'batch-01/vdot-perf.elf', manifest)
    expected = sum(manifest['rows'][e['index']]['dots'] for e in manifest['plan'] if manifest['rows'][e['index']]['method'] == 'vdot')
    require(trace['rob']['committed'] == expected == 768 and trace['overlap'] > 0, 'missing batch handoff coverage')
    lines = [s for s in stdout.splitlines() if s.startswith('T13_')]
    require(len(lines) == 16 and lines[0] == 'T13_BEGIN suite=performance dataset=0 plan=12 contract=vdot-s8x8-r32-v0.1'
            and lines[-1] == 'T13_SUMMARY executed=12 failures=0 scratch_control=1', 'batch program envelope')
    require(lines.count('T13_CONTROLS detected=6 expected=6') == lines.count('T13_SCRATCH_CONTROL allowed=1') == 1,
            'missing program state/negative checks')
    samples = [s for s in lines if s.startswith('T13_P ')]
    require(len(samples) == 12, 'missing batch program records')
    for i, s in enumerate(samples):
        m = re.fullmatch(r'T13_P seq=([0-9]+) c=([0-9]+) i=([0-9]+)', s)
        require(m is not None and int(m[1]) == i and int(m[2]) > 0 and int(m[3]) > 0, 'bad batch program record')
    require(stdout.index('T13_SUMMARY') < stdout.index('HIT GOOD TRAP'), 'premature batch completion')
    result = dict(status='O1_CORE_ARCHIVE_RECHECK_PASS', new_cpu_runs=0, archived_cpu_runs=3,
                  control=control_trace, batch=trace, performance_accepted=False,
                  archive_sha256=EXPECTED, checker_sha256=sha(ROOT/'team/optimizations/o1/check_trace.py'))
    (out/'recheck.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=lambda x: Path(x).resolve())
    main(parser.parse_args().output)
