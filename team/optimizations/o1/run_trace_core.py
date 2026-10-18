#!/usr/bin/env python3
"""Run source-bound O1 observation smoke/control, using frozen software images.

This is an observation milestone, not the complete T12/T13 or CPU performance
acceptance gate. The old observers and their acceptance profiles stay frozen.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile

from check_trace import TraceError, audit, require

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE_SHA256 = "d7717d1ef9d36b40d92c39aa6b8534e8ac1a0f968e57c1a45a4c13d9c39a53fb"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def now():
    return datetime.datetime.now().astimezone().isoformat()


def control_check(text, trace, manifest, exit_code):
    require(exit_code == 0, "control runtime failed")
    require(not re.search(r'T12_(?:MISMATCH|CSR_FAIL|SPEC_FAIL)|HIT BAD TRAP|Assertion failed|different at pc', text),
            "control failure in raw log")
    begins = list(re.finditer(r'^T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1$', text, re.M))
    groups = list(re.finditer(r'^T12_GROUP_PASS id=(\d+) checkpoints=32 bytes=16384$', text, re.M))
    ends = list(re.finditer(r'^T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0$', text, re.M))
    require(len(begins) == len(ends) == 1 and text.count('T12_BEGIN') == text.count('T12_SUMMARY') == 1,
            "incomplete/duplicate control summary")
    require([m[1] for m in groups] == ['0', '1', '2', '3'] and text.count('T12_GROUP_PASS') == 4,
            "incomplete/reordered control groups")
    require(begins[0].start() < groups[0].start() < groups[-1].start() < ends[0].start(), "control order")
    require('HIT GOOD TRAP' in text[ends[0].end():], "missing GOOD TRAP after control summary")
    expected = sum(g['vdot_count'] for g in manifest['groups']) + manifest['speculation']['expected_architectural_vdot']
    require(trace['scope'] == 'fullcore' and trace['mode'] == 2 and trace['rob']['committed'] == expected,
            "control retirement count disagrees with frozen software")
    coverage = dict(atomic_handoff=trace['overlap'] > 0,
                    accepted_younger_squashed=trace['rob'].get('accepted_squashed', 0) > 0,
                    inflight_vdot_killed=trace['vdot_canceled'] > 0,
                    shared_fu_kinds=sum(n > 0 for n in trace['accepted_by_kind'].values()) >= 2,
                    parent_backpressure=trace['waits'] > 0,
                    vdot_writeback_backpressure=trace['vdot_stalls'] > 0,
                    repeated_rob_wrap=trace['rob'].get('rob_wraps', 0) >= 8)
    return dict(status='O1_CONTROL_OBSERVATION_PASS_T12_ACCEPTANCE_PENDING',
                expected_vdot_commits=expected, coverage=coverage,
                missing_observation=['FTQ wrap: schema 1 does not record FTQ'],
                limitations=['No full functional/exception matrix or DiffTest fault injection in this entry',
                             'No calibrated T13 performance comparison; O1 remains default off'])


def main(args):
    args.output.mkdir(parents=True, exist_ok=False)
    build = args.receipt
    require((build/'build.status').read_text().strip() == 'exit_code=0' and
            (build/'split-build.status').read_text().strip() == 'exit_code=0', "source-bound build incomplete")
    require('CORE_BASELINE_BUILD_PASS' in (build/'build.log').read_text(), "missing build completion")
    env = (build/'environment.txt').read_text().splitlines()
    for item in ('VDOT_O1_TRACE=1', 'VDOT_O1_HANDOFF=1', 'VDOT_T14_FUSED_INPUT=1', 'VDOT_T12_TRACE=0', 'VDOT_T13_TRACE=0'):
        require(item in env, "wrong elaboration environment: " + item)
    emu = args.core/'build/emu'
    expected_emu = (build/'emu.sha256').read_text().split()[0]
    require(sha(emu) == expected_emu, "EMU differs from completed build")
    binding = json.loads((args.core/'build/source-binding.json').read_text())
    profile = json.loads((build/'compile-profile.json').read_text())
    require((build/'source-binding.json').read_bytes() == (args.core/'build/source-binding.json').read_bytes(),
            'receipt belongs to another source snapshot')
    require(profile == json.loads((args.core/'build/emu-compile/core-compile-profile.json').read_text()) and
            profile['source_pack_sha256'] == binding['source_pack_sha256'] and
            profile['rtl_manifest_sha256'] == sha(build/'rtl.sha256') and
            (profile['config'], profile['num_cores'], profile['emu_threads']) == ('MinimalConfig', 1, 1),
            'compile profile/source/RTL binding mismatch')
    with (args.output/'rtl-before.log').open('wb') as log:
        subprocess.run(['sha256sum', '-c', str(build/'rtl.sha256')], cwd=args.core,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    # Use the existing strict physical/canonical source and dependency check.
    command = ['python3', '-B', str(ROOT/'team/scripts/prepare-core-baseline.py'), 'verify',
               '--source', str(ROOT), '--pack', str(args.pack), '--target', str(args.core)]
    with (args.output/'source-before.log').open('wb') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    sys.path.insert(0, str(ROOT/'team/scripts'))
    import artifact_guard
    reference = args.reference_root/'build/riscv64-nemu-interpreter-so'
    save(args.output/'reference-before.json', artifact_guard.verify_nemu(args.reference_root, reference, 'reference'))
    archive = ROOT/'team/evidence/james-fullcore-20261016/workloads.tar.gz'
    require(sha(archive) == ARCHIVE_SHA256, "frozen software archive changed")
    selected = ('hello-vadd.bin', 'boot-flash.bin', 'control-pressure-v2/vdot-regression.bin',
                'control-pressure-v2/data/manifest.json')
    images = args.output/'images'
    images.mkdir()
    with tarfile.open(archive, 'r:gz') as source:
        for name in selected:
            matches = [m for m in source if m.name == name]
            require(len(matches) == 1 and matches[0].isfile(), "missing/duplicate archived workload")
            target = images/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.extractfile(matches[0]).read())
    pins = {str(images/name): sha(images/name) for name in selected}
    pins.update({str(emu): expected_emu, str(reference): sha(reference), str(archive): ARCHIVE_SHA256})
    for path in (Path(__file__), Path(__file__).with_name('check_trace.py')):
        pins[str(path)] = sha(path)
    for name in ('source-binding.json', 'compile-profile.json', 'environment.txt', 'rtl.sha256', 'emu.sha256'):
        pins[str(build/name)] = sha(build/name)
    save(args.output/'inputs.json', dict(files=pins, source_binding_sha256=sha(build/'source-binding.json'),
                                     compile_profile_sha256=sha(build/'compile-profile.json'),
                                     parser_sha256=sha(Path(__file__).with_name('check_trace.py')),
                                     driver_sha256=sha(Path(__file__))))
    def run(name, image):
        folder = args.output/name
        folder.mkdir()
        cmd = ['timeout', '30m', 'stdbuf', '-o0', '-e0', str(emu), '-i', str(image),
               '--flash=' + str(images/'boot-flash.bin'), '--ram-size=128MB', '--diff=' + str(reference),
               '--max-cycles=2000000', '--seed=1']
        receipt = dict(command=cmd, cwd=str(args.core), started=now(), status='RUNNING', files=pins)
        save(folder/'runtime.json', receipt)
        runtime_env = dict(os.environ)
        runtime_env.pop('XS_NEGATIVE_VECTOR_TARGET', None)
        with (folder/'stdout.log').open('wb') as out, (folder/'stderr.log').open('wb') as err:
            code = subprocess.run(cmd, cwd=args.core, env=runtime_env, stdout=out, stderr=err).returncode
        receipt.update(exit_code=code, finished=now(), raw_sha256={n:sha(folder/n) for n in ('stdout.log', 'stderr.log')})
        # Save the real exit before checking, including all failed attempts.
        save(folder/'runtime.json', receipt)
        try:
            require(all(sha(Path(p)) == digest for p, digest in pins.items()), 'runtime artifact changed')
            text = (folder/'stderr.log').read_text() + (folder/'stdout.log').read_text()
            require(code == 0 and text.count('Difftest enabled.') == 1 and
                    'The reference model is ' + str(reference) in text, 'DiffTest execution/reference failure')
            require('HIT GOOD TRAP' in text and not re.search(r'HIT BAD TRAP|Assertion failed|different at pc', text),
                    'runtime failure')
            if name == 'hello':
                require(text.count('HELLO_VADD_PASS') == 1, 'hello/vadd result missing')
                result = dict(status='O1_HELLO_VADD_SMOKE_PASS', vdot_coverage=False)
            else:
                trace = audit((folder/'stderr.log').read_text().splitlines(), 2, 'fullcore')
                save(folder/'trace.json', trace)
                manifest = json.loads((images/'control-pressure-v2/data/manifest.json').read_text())
                result = control_check(text, trace, manifest, code)
            save(folder/'checked.json', result)
            receipt['status'] = result['status']
        except Exception as error:
            receipt.update(status='FAILED', error=repr(error))
        save(folder/'result.json', receipt)
        print(name, receipt['status'], flush=True)
        return receipt
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, 'hello', images/'hello-vadd.bin'),
                   pool.submit(run, 'control', images/'control-pressure-v2/vdot-regression.bin')]
        results = [f.result() for f in futures]
    with (args.output/'source-after.log').open('wb') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    save(args.output/'reference-after.json', artifact_guard.verify_nemu(args.reference_root, reference, 'reference'))
    require(all(r['status'] != 'FAILED' for r in results), 'runtime/observer check failed; see result.json')
    save(args.output/'completion.json', dict(status='O1_CORE_OBSERVATION_MILESTONE_PASS', actual_core_runs=2,
                                           emu_sha256=expected_emu, default_enabled=False,
                                           full_T12_T13_acceptance=False))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('core', 'receipt', 'pack', 'reference-root', 'output'):
        parser.add_argument('--'+key, type=lambda x: Path(x).resolve(), required=True)
    raise SystemExit(main(parser.parse_args()))
