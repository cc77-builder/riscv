#!/usr/bin/env python3
"""Validate T04 current-source evidence; publish a receipt only after all gates."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

from artifact_guard import audit_repo, digest, require, verify_nemu


def load_preparer():
    spec = importlib.util.spec_from_file_location('core_source', Path(__file__).with_name('prepare-core-baseline.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_hashes(manifest, base):
    result = {}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        expected, name = line.split('  ', 1)
        path = (base / name).resolve()
        require(digest(path) == expected, 'Artifact changed: ' + str(path))
        result[str(path)] = expected
    require(result, 'Empty artifact manifest: ' + str(manifest))
    return result


def check(args):
    evidence = args.evidence.resolve()
    receipt = evidence / 'check.json'
    receipt.unlink(missing_ok=True)
    target = args.target.resolve()
    load_preparer().verify(args.source.resolve(), args.pack.resolve(), target)
    binding = json.loads((target / 'build/source-binding.json').read_bytes())
    require(json.loads((evidence / 'source-binding.json').read_bytes()) == binding, 'Evidence source binding differs')
    # Reject ignored resource/header/HDL inputs as well as ignored Scala files.
    for folder in ('src', 'macros', 'scripts'):
        for path in (target / folder).rglob('*'):
            if path.is_file():
                name = path.relative_to(target).as_posix()
                # Resource submodules are inventoried separately against their pins.
                if any(name.startswith(module + '/') for module in binding['modules']):
                    continue
                require(name in binding['physical_root_sha256'],
                        'Unknown root compiler input (including ignored paths): ' + str(path))
                require(path.resolve().is_relative_to(target), 'External root source symlink: ' + str(path))
    dependencies = json.loads((evidence / 'dependency-sources.json').read_bytes())
    require(not dependencies['failures'] and set(dependencies['sources']) == set(binding['modules']), 'Incomplete dependency audit')
    for name, revision in binding['modules'].items():
        actual = audit_repo(target / name, revision,
                            source_roots=('src', 'macros/src', 'include', 'lib-include', 'source', 'generator'))
        require(actual == dependencies['sources'][name], 'Dependency compiler inputs changed: ' + name)
    for action in ('build', 'workload', 'run'):
        require((evidence / (action + '.status')).read_text().strip() == 'exit_code=0', action + ' did not exit successfully')
        require('CORE_BASELINE_' + action.upper() + '_PASS' in (evidence / (action + '.log')).read_text(encoding='utf-8'), action + ' has no completion marker')
    artifacts = verify_hashes(evidence / 'emu.sha256', target)
    if (evidence / 'split-build.log').exists() and not (evidence / 'compile-driver.sha256').exists():
        require((evidence / 'split-build.status').read_text().strip() == 'exit_code=0', 'Split build failed')
        require('CORE_SPLIT_BUILD_PASS' in (evidence / 'split-build.log').read_text(encoding='utf-8'), 'Split build has not completed')
    if (evidence / 'rtl.sha256').exists():
        for manifest in ('fir-input.sha256', 'rtl.sha256'):
            artifacts.update(verify_hashes(evidence / manifest, target))
    for manifest in ('split-driver.sha256', 'compile-driver.sha256'):
        if (evidence / manifest).exists():
            artifacts.update(verify_hashes(evidence / manifest, target))
    artifacts.update(verify_hashes(evidence / 'workload.sha256', target / 'team/workloads/hello-vadd'))
    am_libraries = verify_hashes(evidence / 'am-libraries.sha256', target)
    artifacts.update(am_libraries)
    am_library = [Path(p) for p in am_libraries if p.endswith('/am/build/am-riscv64-xs.a')]
    require(len(am_library) == 1 and len(am_libraries) == 2, 'Unexpected AM libraries')
    am_home = am_library[0].parents[2]
    am_sources = audit_repo(am_home, '086a238062fdfb3281b745a537b361983d0154b5',
                            source_roots=('am/src', 'am/include', 'libs/klib/src', 'libs/klib/include'))
    nemu = args.nemu.resolve()
    reference = verify_nemu(nemu, nemu / 'build/riscv64-nemu-interpreter-so', 'reference')
    require(reference == json.loads((evidence / 'nemu-verification.json').read_bytes()), 'Reference changed since run')
    build_args = shlex.split((evidence / 'build-command.txt').read_text())
    for flag in ('CONFIG=MinimalConfig', 'NUM_CORES=1', 'EMU_THREADS=1', 'EMU_TRACE=fst',
                 'WITH_CHISELDB=0', 'WITH_CONSTANTIN=0', 'WITH_ROLLINGDB=0'):
        require(flag in build_args, 'Unexpected baseline build profile: ' + flag)
    require('-j1' in build_args or '-j2' in build_args, 'Unexpected build parallelism')
    if (evidence / 'compile-profile.json').exists():
        profile = json.loads((evidence / 'compile-profile.json').read_bytes())
        require(profile == json.loads((target / 'build/emu-compile/core-compile-profile.json').read_bytes()), 'Compiler profile changed')
        require(profile['source_pack_sha256'] == binding['source_pack_sha256'] and
                profile['rtl_manifest_sha256'] == digest(evidence / 'rtl.sha256'), 'Compiler profile input mismatch')
        for flag in ('OPT_FAST=' + profile['opt_fast'], 'OPT_SLOW=' + profile['opt_slow']):
            require(flag in build_args, 'Compiler optimization differs from profile')
        for variable, key in (('CXX', 'cxx_sha256'), ('CC', 'cc_sha256')):
            choices = [flag.split('=', 1)[1] for flag in build_args if flag.startswith(variable + '=')]
            require(len(choices) == 1, 'Compiler command missing or ambiguous: ' + variable)
            binary = shutil.which(choices[0])
            require(binary is not None and digest(binary) == profile[key], 'Compiler binary changed: ' + variable)
        for name, expected in profile['generated_source_sha256'].items():
            require(digest(target / 'build/generated-src' / name) == expected, 'Generated DiffTest source changed: ' + name)
    run_args = shlex.split((evidence / 'run-command.txt').read_text())
    image = str(target / 'team/workloads/hello-vadd/build/hello-vadd-riscv64-xs.bin')
    flash = str(target / 'team/workloads/hello-vadd/build/boot-flash.bin')
    require(run_args[:3] == ['./build/emu', '-i', image], 'Wrong simulator or guest image')
    for flag in ('--flash=' + flash, '--ram-size=128MB', '--diff=' + str(nemu / 'build/riscv64-nemu-interpreter-so'), '--max-cycles=2000000'):
        require(flag in run_args, 'Missing runtime dependency: ' + flag)
    require('--no-diff' not in run_args, 'DiffTest disabled')
    raw = (evidence / 'emulator-output.log').read_text(encoding='utf-8', errors='replace')
    content = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', raw)
    subprocess.run(['python3', str(target / 'team/scripts/summarize-run.py'), str(evidence / 'emulator-output.log')], check=True, stdout=subprocess.DEVNULL)
    expected = ((9,) * 8, (254,252,250,248,246,244,242,240), (128,127,0,0,0,0,254,254))
    for case, values in enumerate(expected):
        matches = re.findall(r'vadd case=' + str(case) + r' output:([^\r\n]+)', content)
        require(len(matches) == 1, 'Missing or repeated case ' + str(case))
        require(matches[0].split() == [*(str(v) for v in values), 'PASS'], 'Incorrect lane data: ' + str(case))
    require('RVV VLEN=128 bits; SEW=8 LMUL=1 AVL=8' in content, 'Missing vector configuration')
    require(re.search(r'Exit status:\s*0\b', content) is not None, 'Emulator exit status is not zero')
    require(image in content and str(nemu / 'build/riscv64-nemu-interpreter-so') in content, 'Runtime paths not observed')
    waveform = None
    if '--dump-wave' in run_args:
        wave = evidence / 'hello-vadd.fst'
        require('--wave-path=' + str(wave) in run_args and wave.is_file() and wave.stat().st_size > 0, 'Waveform absent or mismatched')
        waveform = dict(path=str(wave), sha256=digest(wave), bytes=wave.stat().st_size)
        if (evidence / 'wave-summary.json').exists():
            require((evidence / 'wave-extract.status').read_text().strip() == 'exit_code=0', 'Wave extraction did not complete')
            wave_summary = json.loads((evidence / 'wave-summary.json').read_bytes())
            require(wave_summary['status'] == 'T04_VADD_WAVE_PATH_PASS' and len(wave_summary['events']) == 3, 'Invalid execution path summary')
            artifacts.update(verify_hashes(evidence / 'wave-artifacts.sha256', target))
            waveform['execution_path'] = wave_summary
    record = dict(schema=1, status='T04_CURRENT_CORE_BASELINE_PASS', source_pack_sha256=binding['source_pack_sha256'],
                  revision=binding['revision'], root_inputs=len(binding['physical_root_sha256']), modules=len(binding['modules']),
                  dependency_files=sum(map(len, dependencies['sources'].values())),
                  build_copy=str(target), artifacts_sha256=artifacts, reference_binary_sha256=reference['binary_sha256'],
                  am_home=str(am_home), am_source_sha256=am_sources,
                  cases=3, lanes=24, difftest=True, waveform=waveform,
                  evidence_sha256={p.name:digest(p) for p in sorted(evidence.iterdir()) if p.is_file() and p != receipt and p.suffix != '.fst'},
                  checker_sha256=digest(Path(__file__)), human_acceptance_complete=False, vdot_full_core=False)
    receipt.write_bytes((json.dumps(record, sort_keys=True, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(dict(status=record['status'], cases=3, lanes=24, source_pack_sha256=record['source_pack_sha256']), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'pack', 'target', 'evidence', 'nemu'):
        parser.add_argument('--' + name, required=True, type=Path)
    check(parser.parse_args())
