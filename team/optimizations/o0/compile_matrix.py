"""Build 18 O0 matrix images in an isolated Linux directory; do not run a DUT.

Use a fixed Git AM snapshot and the installed GNU RISC-V compiler. Receipts bind
the dirty working source bytes as well as generated inputs and compiled images.
These receipts deliberately are not unified campaign hardware acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

import generate_matrix as matrix

AM_REVISION = '086a238062fdfb3281b745a537b361983d0154b5'
ROOT = matrix.ROOT


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def check_elf(checker, elf, manifest):
    checker.check_compiled_cases(elf, manifest)
    kernels = checker.elf_kernels(elf)
    require(set(kernels) == set(range(len(manifest['rows']))), 'wrong compiled kernel inventory')
    records = []
    for i, row in enumerate(manifest['rows']):
        path = checker.walk(kernels[i])
        custom = [word for _, word in path if word & 0xfe00707f == 0x0200000b]
        reductions = [word for _, word in path if word & 0xfc00707f == 0xc4000057]
        require(len(custom) == (256 if row['method'] == 'vdot' else 0), 'compiled vdot work mismatch')
        require(len(reductions) == (256 if row['method'] == 'rvv' else 0), 'compiled RVV work mismatch')
        if custom:
            operands = [[(w >> 7) & 31, (w >> 15) & 31, (w >> 20) & 31] for w in custom]
            require(operands == row['lane_operands'] * row['iterations'], 'compiled vdot operand mismatch')
        records.append(dict(id=row['id'], dots=256, vdot_instructions=len(custom),
                            rvv_reductions=len(reductions), marker_path_instructions=len(path)))
    return records


def compile_all(am_repository, output):
    require(os.name == 'posix', 'run with native Linux/WSL tools')
    require(not output.exists(), 'output already exists')
    require(not output.resolve().is_relative_to((ROOT/'team/evidence').resolve()), 'build outside sealed evidence')
    compiler = shutil.which('riscv64-linux-gnu-gcc')
    require(compiler is not None, 'missing installed RISC-V compiler')
    output.mkdir(parents=True, exist_ok=False)
    source = output/'source'
    source.mkdir()
    files = [Path(__file__).resolve(), Path(matrix.__file__).resolve(), matrix.EMITTER]
    files += [ROOT/'team/workloads/unified-vdot'/name for name in ('main.c', 'Makefile', 'fixed-layout.ld', 'check.py')]
    files += [ROOT/'team/workloads/vdot-perf/check.py']
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in files}
    for path in files:
        dest = source/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    bundle = output/'nexus-am.tar'
    subprocess.run(['git', '-C', str(am_repository), 'archive', AM_REVISION, '-o', str(bundle)], check=True)
    am = output/'nexus-am'
    am.mkdir()
    with tarfile.open(bundle) as archive:
        archive.extractall(am, filter='data')
    env = dict(os.environ, AM_HOME=str(am), LINUX_GNU_TOOLCHAIN='1')
    spec = importlib.util.spec_from_file_location('o0_compile_checker', source/'team/workloads/unified-vdot/check.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    result = dict(status='RUNNING', new_hardware_run=False, am_revision=AM_REVISION,
                  am_archive_sha256=sha(bundle), source_sha256=hashes,
                  compiler=dict(path=compiler, sha256=sha(Path(compiler)),
                                version=subprocess.check_output([compiler, '--version'], text=True).splitlines()[0]), images=[])
    write(output/'result.json', result)
    for dataset in range(3):
        for shard in range(6):
            build = output/f'matrix-d{dataset}-s{shard:02d}'
            manifest = matrix.generate(build/'data', dataset, shard, 6)
            command = ['make', '-C', str(source/'team/workloads/unified-vdot'), 'ARCH=riscv64-xs', 'MARCH=rv64gcv',
                       'T13_DATA='+str(build/'data'), 'T13_OBJ_ROOT='+str(build/'objects'),
                       'BINARY='+str(build/'vdot-perf'), '-j1']
            with (build/'build.log').open('wb') as log:
                completed = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            receipt = dict(image=build.name, command=command, exit_code=completed.returncode)
            write(build/'build.json', receipt)
            require(completed.returncode == 0, 'compile failed; see '+str(build/'build.log'))
            receipt['static_kernel_checks'] = check_elf(checker, build/'vdot-perf.elf', manifest)
            receipt['sha256'] = {name: sha(build/name) for name in ('vdot-perf.bin', 'vdot-perf.elf', 'data/manifest.json', 'build.log')}
            receipt['status'] = 'COMPILED_STATIC_CHECK_PASS_NOT_DUT'
            write(build/'build.json', receipt)
            result['images'].append(receipt)
            write(output/'result.json', result)
            print(build.name + ': compiled, ELF constants and 256-dot paths verified', flush=True)
    require(hashes == {str(p.relative_to(ROOT)): sha(p) for p in files}, 'source changed during build')
    result.update(status='O0_MATRIX_18_IMAGES_COMPILED_NOT_EXECUTED', rows=36, planned_windows=216,
                  limits=['No DUT execution, calibration or measured performance is claimed.',
                          'Runner/provenance and matrix inventory acceptance must be added before hardware acceptance.'])
    write(output/'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--am-repository', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    compile_all(args.am_repository.resolve(), args.output.resolve())
