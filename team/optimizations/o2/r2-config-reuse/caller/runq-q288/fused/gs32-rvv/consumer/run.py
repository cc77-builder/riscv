"""Three bounded reference processes for the separate GS32 consumer entry.

The existing W2 whole-state numerical validator and owned-process launcher are
used unchanged. Only image identity is rebound through the existing bind helper.
No reference counter is called a XiangShan cycle measurement.
"""
from pathlib import Path
import argparse
import json
import os
import resource
import signal
import struct
import sys

import build as b
import derive

PASS = 'GS32_CONSUMER_REFERENCE_CAMPAIGN_PASS'
REFERENCE_SHA = '8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9'
need, read, save, digest = b.need, b.read, b.save, b.digest


def image(build, record, entry_tag, kind):
    need(entry_tag == derive.ENTRY_TAG and kind in ('normal', 'output'), 'separate entry protocol')
    raw = bytearray((build / (b.PREFIX + '.bin')).read_bytes())
    offset = record['control_offset']
    controls = [entry_tag, 3, int(kind == 'output'), 1]
    raw[offset:offset + 16] = struct.pack('<4I', *controls)
    return raw, dict(base_sha256=record['artifacts'][b.PREFIX + '.bin'], offset=offset,
        controls=controls, w2_pack_fault=False, w2_packed_offset=record['w2_packed_offset'],
        sha256=derive.sha(raw))


def validate(build, dest, record, negative, receipt, r):
    need(receipt.get('direct_child_reaped') is True, 'actual direct reference child reaped')
    original = r.b.bind(r.w.validate, image=image)(build, dest, record, derive.ENTRY_TAG,
                    'output' if negative else 'normal', receipt)
    expected_flags = record['scalar_flags'][:original['positions']]
    need(original['flags'] == expected_flags, 'all new flags equal re-audited original scalar flags')
    return dict(contract=b.CONTRACT, entry=derive.ENTRY, entry_tag=derive.ENTRY_TAG,
        status='EXPECTED_GS32_CONSUMER_STATE_REJECTION' if negative else 'GS32_CONSUMER_COMPLETE_REFERENCE_PASS',
        reused_validator=original, exact_scalar_flags=True, target_emu_runs=0,
        performance_qualified=False, stable_default_changed=False)


def verify_review(build, review_path, record, r):
    """Bind a concrete disassembly review to this ELF, never to a source claim.

    The review records the eight actual route calls and pointer evidence; this
    structural check does not pretend to be full consumer symbolic execution.
    """
    review = read(review_path)
    need(review['status'] == 'GS32_CONSUMER_ROUTING_REVIEW_PASS'
         and review['elf_sha256'] == record['artifacts'][b.PREFIX + '.elf']
         and review['disassembly_sha256'] == record['artifacts']['disassembly.stdout.log'],
         'actual new ELF routing review identity')
    elf = r.b.base.f.g.ELF((build / (b.PREFIX + '.elf')).read_bytes())
    pc, size, *_ = elf.symbols['consumer_gs32_cache']
    actual = [(address, target) for address, target in b.calls((build / 'disassembly.stdout.log').read_text())
              if pc <= address < pc + size and target == 'route_matmul']
    recorded = review['route_calls']
    need(len(actual) == len(recorded) == 8 and
         sorted(address for address, _ in actual) == sorted(int(row['pc'], 16) for row in recorded),
         'all eight actual new consumer route call sites, without omission')
    need(sum(row['kernel'] == 'q288_gs32_rvv' for row in recorded) == 7
         and sum(row['kernel'] == 'q288_fused_rvv4' for row in recorded) == 1,
         'seven K288 pointers and one retained W2 FR pointer')
    for row in recorded:
        need(int(row['kernel_address'], 16) == elf.symbols[row['kernel']][0],
             'actual resolved function pointer address')
        need(row['instruction_evidence'], 'nonempty actual pointer instruction evidence')
        for evidence in row['instruction_evidence']:
            address = int(evidence['pc'], 16)
            raw = bytes.fromhex(evidence['bytes'])
            need(raw and elf.read(address, len(raw)) == raw, 'review instruction evidence exists in ELF')
    need(review['w2_fr_selection']['kernel'] == 'q768_fr'
         and review['w2_fr_selection']['pointer_comparison'] == 'q288_fused_rvv4'
         and review['old_method_5_still_invalid'] is True,
         'retained old W2 selector and old invalid-method domain reviewed')
    need(review['w2_fr_selection']['instruction_evidence'], 'nonempty actual W2 selector evidence')
    for evidence in review['w2_fr_selection']['instruction_evidence']:
        raw = bytes.fromhex(evidence['bytes'])
        need(raw and elf.read(int(evidence['pc'], 16), len(raw)) == raw, 'actual old W2 selector bytes')
    return review


def inputs(build, adapter, identity_path, review_path, support_snapshot=None):
    record = read(build / 'result.json')
    need(record['contract'] == b.CONTRACT and record['status'] == b.STATIC
         and record['entry'] == derive.ENTRY and record['entry_tag'] == derive.ENTRY_TAG,
         'explicit new build identity')
    r, files = b.support(Path(record['parent_campaign']), support_snapshot)
    fixed = read(build / 'inputs.json')
    need(digest(build / 'inputs.json') == record['inputs_sha256'], 'recorded exact build inputs')
    for path, value in fixed.items():
        b.pin(files, path, value)
    for group, folder in (('artifacts', build), ('actual_source_pins', build / 'source'),
                          ('fixtures', build / 'fixture')):
        for name, value in record[group].items():
            b.pin(files, folder / name, value)
    for name in ('result.json', 'inputs.json', 'tools.json'):
        b.pin(files, build / name)
    if support_snapshot is None:
        identity = r.old.r.parent.parent_identity(r.b.REPO, identity_path)
    else:
        # The old checker reads fixed Git objects with `git show BASE:path`.
        # A source-only snapshot is not a checkout; expose only the existing
        # metadata directory while this unchanged read-only checker executes.
        closure = read(support_snapshot / 'support-identity.json')
        saved = {name: os.environ.get(name) for name in ('GIT_DIR', 'GIT_WORK_TREE')}
        try:
            os.environ['GIT_DIR'] = closure['git_metadata_dir']
            os.environ.pop('GIT_WORK_TREE', None)
            identity = r.old.r.parent.parent_identity(r.b.REPO, identity_path)
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
    reference = Path(identity['configuration']['reference'])
    b.pin(files, reference, REFERENCE_SHA)
    need(identity['reference_sha256'] == REFERENCE_SHA, 'same fixed normal reference identity')
    original = read(adapter / 'build.json')
    need(original['status'] == 'REFERENCE_ADAPTER_BUILD_PASS' and
         original['inputs_sha256'] == digest(adapter / 'inputs.json'), 'actual original reference caller build')
    need(set(original['artifacts']) == {'reference-runner', 'reference_runner.c', 'runner.d',
         'compile.command.json', 'compile.stdout.log', 'compile.stderr.log', 'nemu.config'},
         'complete original reference caller inventory')
    for name, value in original['artifacts'].items():
        b.pin(files, adapter / name, value)
    for path, value in read(adapter / 'inputs.json')['files'].items():
        b.pin(files, path, value)
    command = read(adapter / 'compile.command.json')
    need(command.get('exit_code') == 0 and command.get('status') == 'exited'
         and command.get('process_group_absent_after_exit') is True
         and str(adapter / 'reference_runner.c') in command['argv']
         and command['argv'][-2:] == ['-o', str(adapter / 'reference-runner')], 'actual successful original adapter compile')
    need((adapter / 'reference_runner.c').read_bytes() ==
         (r.b.REPO / b.STAGES / 'target/reference_runner.c').read_bytes(), 'unchanged original caller source')
    for path in (adapter / 'build.json', adapter / 'inputs.json', identity_path, review_path, Path(__file__)):
        b.pin(files, path)
    for name in ('build.py', 'derive.py', 'consumer_gs32.h', 'CONTRACT.md'):
        b.pin(files, Path(__file__).resolve().parent / name)
    review = verify_review(build, review_path, record, r)
    r.b.base.f.executable(build / (b.PREFIX + '.elf'), build / (b.PREFIX + '.bin'),
                          build / 'metadata.stdout.log', record['tls_errno_offset'])
    need(digest(build / b.CORE) == digest(build / 'source' / b.CORE) ==
         record['derivation']['combined_object_sha256'], 'same pure consumer object actually linked')
    return record, r, identity, files, review


def campaign(build, adapter, identity_path, review_path, output, support_snapshot=None):
    need(len(os.sched_getaffinity(0)) == 1 and not output.exists(), 'fresh campaign, one coordinated CPU')
    record, r, identity, files, review = inputs(build, adapter, identity_path, review_path, support_snapshot)
    r.old.r.parent.outside_inputs(output, [build, adapter, r.b.REPO, identity_path.parent,
        identity['configuration']['am_home'], identity['configuration']['hardware_source']])
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    limit = 128 * 1024 * 1024
    need(hard == resource.RLIM_INFINITY or hard >= limit, 'whole binary/dump file budget')
    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, hard))
    output.mkdir(parents=True)
    save(output / 'runtime-inputs.json', files)
    now = r.b.base.f.h.now
    state = dict(contract=b.CONTRACT, status='RUNNING', started=now(), records=[],
        reference_runs=0, active_pid=None, active_result=None,
        cpu_affinity=sorted(os.sched_getaffinity(0)), max_concurrent_reference=1,
        schedule='negative_then_recovery_then_replay', target_emu_runs=0, performance_qualified=False)
    persist = lambda: save(output / 'state.json', state)
    persist(); validations = {}
    try:
        for label, negative in (('negative', True), ('recovery', False), ('replay', False)):
            dest = output / label
            dest.mkdir()
            raw, controls = image(build, record, derive.ENTRY_TAG, 'output' if negative else 'normal')
            (dest / 'image.bin').write_bytes(raw)
            save(dest / 'image-control.json', controls)
            del raw
            local_inputs = dict(files)
            b.pin(local_inputs, dest / 'image.bin'); b.pin(local_inputs, dest / 'image-control.json')
            save(dest / 'runtime-inputs.json', local_inputs)
            argv = [str(adapter / 'reference-runner'), identity['configuration']['reference'],
                    str(dest / 'image.bin'), str(dest), 'builtin', str(r.w.MAX_CALLS), '600',
                    str(build / 'dump-plan.txt'), '1']
            receipt = dict(contract=b.CONTRACT, name=label, entry=derive.ENTRY,
                entry_tag=derive.ENTRY_TAG, negative=negative, command=argv, cwd=str(dest),
                started=now(), process_started=False, exit_code=None, status='RUNNING',
                cpu_affinity=sorted(os.sched_getaffinity(0)), max_api_calls=r.w.MAX_CALLS,
                wall_limit_seconds=600, external_timeout_seconds=630, max_output_file_bytes=limit)
            before = state['reference_runs']
            state['records'].append(receipt)
            def progress():
                save(dest / 'result.json', receipt)
                state['reference_runs'] = before + int(receipt.get('process_started') is True)
                live = receipt.get('process_started') and not receipt.get('process_group_absent_after_exit')
                state['active_pid'] = receipt.get('pid') if live else None
                state['active_result'] = str(dest / 'result.json') if live else None
                persist()
            progress()
            try:
                b.verify(local_inputs)
                with (dest / 'stdout.log').open('wb') as stdout, (dest / 'stderr.log').open('wb') as stderr:
                    r.old.previous.spawn(argv, dest, stdout, stderr, receipt, progress, dict(os.environ), 630)
                checked = validate(build, dest, record, negative, receipt, r)
                save(dest / 'validation.json', checked)
                validations[label] = checked
                b.verify(local_inputs)
                receipt.update(status=checked['status'], validation_sha256=digest(dest / 'validation.json'))
                print(json.dumps(dict(case=label, status=checked['status'], at=now(),
                    retired=checked['reused_validator']['retired'])), flush=True)
            except BaseException as error:
                receipt.update(status='FAILED', error=repr(error))
                raise
            finally:
                receipt['finished'] = now(); progress()
        need(validations['recovery'] == validations['replay'], 'complete state/flags/retirement/reference-counter replay')
        need(len({row['pid'] for row in state['records']}) == 3 and state['reference_runs'] == 3,
             'three actually independent reference processes')
        need(all(row['direct_child_reaped'] and row['process_group_absent_after_exit']
                 and not row.get('residual_process_group') for row in state['records']), 'complete owned process cleanup')
        b.verify(files)
        save(output / 'results.json', dict(contract=b.CONTRACT, status=PASS, validations=validations,
            entry=derive.ENTRY, entry_tag=derive.ENTRY_TAG, build_sha256=digest(build / 'result.json'),
            routing_review_sha256=digest(review_path), exact_scalar_flags=True,
            reused_validator_sha256=digest(Path(r.w.__file__)),
            reused_process_owner_sha256=digest(Path(r.old.previous.__file__)),
            reference_runs=3, target_emu_runs=0, performance_qualified=False, stable_default_changed=False))
        state.update(status=PASS, active_pid=None, active_result=None,
                     results_sha256=digest(output / 'results.json'))
    except BaseException as error:
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        state['finished'] = now(); persist()
    return state


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('GS32 consumer reference')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'adapter', 'identity', 'routing-review', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--support-snapshot', type=Path)
    args = parser.parse_args()
    result = campaign(*(getattr(args, name.replace('-', '_')).resolve() for name in
                        ('build', 'adapter', 'identity', 'routing-review', 'output')),
                      support_snapshot=args.support_snapshot.resolve() if args.support_snapshot else None)
    print(json.dumps({key: result[key] for key in ('contract', 'status', 'reference_runs', 'active_pid')}), flush=True)
