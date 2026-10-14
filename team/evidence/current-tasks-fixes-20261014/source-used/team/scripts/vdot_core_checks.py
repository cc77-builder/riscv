"""Fail-closed T10 source, artifact and guest checks shared by delivery entries."""
import argparse
import json
import re
import shlex
import shutil
from pathlib import Path

from artifact_guard import audit_repo, digest, require, verify_nemu


DATA_FILES = ('cases.h', 'cases.jsonl', 'exceptions.json', 'manifest.json', 'stubs.h', 'word-sites.S')
CASE_IDS = {'D03', 'D05', 'D07', 'L04-0-8-9', 'L04-10-0-9', 'L04-10-8-0',
            'L04-0-0-9', 'L04-31-31-31', 'L05-3-ff', 'clean-vs', 'X02-m2',
            'X02-mf2', 'X03-vl0', 'X03-vl7', 'X04-vstart1', 'X05-vill',
            'X06-VS-off', 'X07-vm0', 'X09-v0', 'X11-VS-1'}
AM_REV = '086a238062fdfb3281b745a537b361983d0154b5'


def write_json(path, value):
    path.write_bytes((json.dumps(value, sort_keys=True, indent=2) + '\n').encode())


def verify_manifest(manifest, base, expected):
    """Verify both bytes and the exact resolved files actually consumed."""
    entries = {}
    for line in manifest.read_text().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64}) [ *](.+)', line)
        require(match is not None, 'Malformed artifact manifest: ' + str(manifest))
        path = (base / match[2]).resolve()
        require(path not in entries, 'Duplicate artifact path: ' + str(path))
        entries[path] = match[1]
    expected = {p.resolve() for p in expected}
    require(bool(expected) and set(entries) == expected,
            'Artifact paths differ from actual selected inputs: ' + str(manifest))
    for path, value in entries.items():
        require(digest(path) == value, 'Artifact digest mismatch: ' + str(path))
    return {str(path): value for path, value in entries.items()}


def workload_inputs(evidence, am):
    return [evidence / name for name in ('vdot-integration.elf', 'vdot-integration.bin', 'boot-flash.bin')] + [
        evidence / 'data' / name for name in DATA_FILES] + [
        am / 'am/build/am-riscv64-xs.a', am / 'libs/klib/build/klib-riscv64-xs.a']


def snapshot_sources(root, am):
    paths = [*root.joinpath('team/workloads/vdot-integration').glob('*.[chS]'),
             root / 'team/workloads/vdot-integration/Makefile',
             *root.joinpath('team/workloads/vdot-exceptions').glob('*.[chS]')]
    paths += [root / name for name in (
        'team/workloads/hello-vadd/boot-flash.S', 'team/tests/generate_vdot_cases.py',
        'team/tests/vdot_model.py', 'team/scripts/vdot-core-smoke.sh',
        'team/scripts/vdot_core_checks.py', 'team/scripts/artifact_guard.py')]
    return dict(sources={str(p.resolve()): digest(p) for p in sorted(set(paths))}, am_rev=AM_REV,
                am_sources=audit_repo(am, AM_REV,
                                     source_roots=('am/src', 'am/include', 'libs/klib/src', 'libs/klib/include')))


def verify_core(root, evidence):
    binding = json.loads((root / 'build/source-binding.json').read_bytes())
    require(binding == json.loads((evidence / 'source-binding.json').read_bytes()), 'Different source/build copy')
    require(Path(binding['build_copy']).resolve() == root.resolve(), 'Selected build copy differs')
    profile = json.loads((evidence / 'compile-profile.json').read_bytes())
    require(profile == json.loads((root / 'build/emu-compile/core-compile-profile.json').read_bytes()),
            'Changed compilation profile')
    require(profile['source_pack_sha256'] == binding['source_pack_sha256'], 'Compiler source binding differs')
    require(profile['rtl_manifest_sha256'] == digest(evidence / 'rtl.sha256'), 'Compiler RTL binding differs')
    args = shlex.split((evidence / 'build-command.txt').read_text())
    for key, field in (('CXX', 'cxx_sha256'), ('CC', 'cc_sha256')):
        matches = [a.split('=', 1)[1] for a in args if a.startswith(key + '=')]
        require(len(matches) == 1, 'Missing/ambiguous compiler: ' + key)
        tool = shutil.which(matches[0])
        require(tool is not None and digest(tool) == profile[field], 'Changed compiler tool: ' + key)
    generated = root / 'build/generated-src'
    require({p.name for p in generated.iterdir() if p.is_file()} == set(profile['generated_source_sha256']),
            'Generated DiffTest source inventory changed')
    for name, value in profile['generated_source_sha256'].items():
        require(Path(name).name == name and digest(generated / name) == value, 'Changed generated DiffTest source')
    deps = json.loads((evidence / 'dependency-sources.json').read_bytes())
    require(not deps['failures'] and set(deps['sources']) == set(binding['modules']), 'Dependency inventory differs')
    for name, rev in binding['modules'].items():
        actual = audit_repo(root / name, rev,
                            source_roots=('src', 'macros/src', 'include', 'lib-include', 'source', 'generator'))
        require(actual == deps['sources'][name], 'Changed dependency inputs: ' + name)
    for name, value in binding['physical_root_sha256'].items():
        path = root / name
        require(path.resolve().is_relative_to(root.resolve()) and digest(path) == value,
                'Changed root compiler input: ' + name)
    for folder in ('src', 'macros', 'scripts'):
        for path in (root / folder).rglob('*'):
            if path.is_file():
                name = path.relative_to(root).as_posix()
                if not any(name.startswith(mod + '/') for mod in binding['modules']):
                    require(name in binding['physical_root_sha256'], 'Unknown root compiler input: ' + name)
    verify_manifest(evidence / 'emu.sha256', root, [root / 'build/emu'])
    verify_manifest(evidence / 'fir-input.sha256', root, [root / 'build/rtl/SimTop.fir'])
    verify_manifest(evidence / 'rtl.sha256', root, list((root / 'build/rtl').glob('*.sv')))
    require((evidence / 'build.status').read_text().strip() == 'exit_code=0', 'Core build did not succeed')
    require('CORE_BASELINE_BUILD_PASS' in (evidence / 'build.log').read_text(), 'Core build lacks completion marker')
    return binding


def check_guest_log(log):
    log = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', log)
    rows = re.findall(r'^T10_CASE id=(\S+) result=(\S+) cause=(\d+) all32=(\d+) pre32=(\d+)$', log, re.M)
    require(len(rows) == 20 and {row[0] for row in rows} == CASE_IDS, 'Incomplete actual guest coverage')
    require(len(re.findall(r'^T10_CASE\b', log, re.M)) == 20, 'Extra/malformed guest case record')
    require(all(row[1] == 'PASS' and int(row[2]) == (2 if row[0].startswith('X') else 0)
                and row[3:] == ('1', '1') for row in rows), 'Guest state/trap judge failed')
    require(log.count('T10_CORE_SMOKE_PASS legal=10 illegal=10 all32=20 pre32=20') == 1,
            'Missing/duplicate guest summary')
    require('Difftest enabled' in log and 'HIT GOOD TRAP' in log and 'HIT BAD TRAP' not in log,
            'Missing successful actual DiffTest completion')
    require(re.findall(r'Exit status:\s*(\d+)\b', log) == ['0'], 'Emulator exit status is not uniquely zero')


def verify_run_command(root, evidence, reference):
    args = shlex.split((evidence / 'run-command.txt').read_text())
    require(len(args) >= 3 and args[:2] == ['./build/emu', '-i'], 'Wrong actual emulator/image')
    require((root / args[2]).resolve() == (evidence / 'vdot-integration.bin').resolve(), 'Wrong actual image')
    require(args.count('-i') == 1, 'Ambiguous runtime image')
    for prefix, selected in (('--flash=', evidence / 'boot-flash.bin'), ('--diff=', reference)):
        values = [a[len(prefix):] for a in args if a.startswith(prefix)]
        require(len(values) == 1 and (root / values[0]).resolve() == selected.resolve(),
                'Missing/ambiguous/wrong runtime input: ' + prefix)
    for flag in ('--ram-size=128MB', '--max-cycles=2000000'):
        require(args.count(flag) == 1, 'Missing/duplicate runtime dependency: ' + flag)
    require('--no-diff' not in args and not any(a.startswith('--no-diff=') for a in args), 'DiffTest disabled')
    for prefix in ('--flash=', '--diff=', '--ram-size=', '--max-cycles='):
        require(sum(a.startswith(prefix) for a in args) == 1, 'Ambiguous runtime input: ' + prefix)
    verify_manifest(evidence / 'runtime.sha256', root, [root / 'build/emu', reference])


def check(root, evidence, core, am, nemu, finish=False):
    # Both entry phases revoke a stale receipt before inspecting any input.
    receipt = evidence / 'check.json'
    receipt.unlink(missing_ok=True)
    before = json.loads((evidence / 'source-before.json').read_bytes())
    for name in ('source-after.json', 'source-run.json') + (('source-after-run.json',) if finish else ()):
        require(before == json.loads((evidence / name).read_bytes()), 'Workload source snapshot differs: ' + name)
    require(before == snapshot_sources(root, am), 'Current workload/AM source differs from build')
    require((evidence / 'build.status').read_text().strip() == 'exit_code=0', 'Workload build failed')
    require('VDOT_CORE_SMOKE_BUILD_PASS' in (evidence / 'build.log').read_text(), 'Workload build has no marker')
    verify_manifest(evidence / 'workload.sha256', root, workload_inputs(evidence, am))
    binding = verify_core(root, core)
    reference = nemu / 'build/riscv64-nemu-interpreter-so'
    provenance = verify_nemu(nemu, reference, 'reference')
    if not finish:
        write_json(evidence / 'nemu-verification.json', provenance)
        return dict(status='VDOT_T10_PREFLIGHT_PASS')
    require(provenance == json.loads((evidence / 'nemu-verification.json').read_bytes()), 'Reference changed during run')
    require((evidence / 'emulator.status').read_text().strip() == 'exit_code=0', 'Emulator did not exit successfully')
    verify_run_command(root, evidence, reference)
    check_guest_log((evidence / 'emulator-output.log').read_text())
    result = dict(status='VDOT_T10_CORE_SMOKE_PASS', legal=10, illegal=10, all32_checked=20, pre32_checked=20,
                  source_pack_sha256=binding['source_pack_sha256'],
                  source_manifest_sha256=digest(evidence / 'source-before.json'),
                  runtime_manifest_sha256=digest(evidence / 'runtime.sha256'),
                  workload_manifest_sha256=digest(evidence / 'workload.sha256'),
                  checker_sha256=digest(Path(__file__)), complete_t11=False, team_review_signed=False)
    write_json(receipt, result)
    return result


def select_decode_rtl(root, destination):
    matches = list(root.rglob('VdotDecodeHarness.sv'))
    require(len(matches) == 1, 'Missing/ambiguous actual tested DecodeStage RTL')
    shutil.copyfile(matches[0], destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('snapshot', 'preflight', 'finish', 'select-decode-rtl'))
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--core', type=Path)
    parser.add_argument('--am', type=Path)
    parser.add_argument('--nemu', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root, evidence = args.root.resolve(), args.evidence.resolve()
    if args.action == 'snapshot':
        require(args.am is not None and args.output is not None, 'Snapshot requires AM and output')
        write_json(args.output, snapshot_sources(root, args.am.resolve()))
    elif args.action == 'select-decode-rtl':
        select_decode_rtl(root / 'out/xiangshan/test/testOnly.dest/sandbox/test_run_dir',
                          evidence / 'rtl/VdotDecodeHarness.sv')
    else:
        # Clear receipt even when command-line dependencies are absent.
        (evidence / 'check.json').unlink(missing_ok=True)
        require(all(p is not None for p in (args.core, args.am, args.nemu)), 'Missing runtime dependencies')
        print(json.dumps(check(root, evidence, args.core.resolve(), args.am.resolve(), args.nemu.resolve(),
                               finish=args.action == 'finish'), sort_keys=True))


if __name__ == '__main__':
    main()
