"""Serial, read-only re-audit of an already completed GS32 raw campaign.

This runs no EMU and edits no original receipt. It imports the controller
snapshot consumed by the campaign in one fresh Python process, then analyzes
negative/recovery/replay in order. Its purpose is to remove the initial runner's
shared-sys.modules concurrency risk from the accepted analysis evidence.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import os
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def recheck(repo, build, campaign, out):
    need(not out.exists() and not out.is_relative_to(repo)
         and not out.is_relative_to(campaign), 'fresh separate postprocessing directory')
    old_state = read(campaign/'state.json')
    need(old_state.get('finished') and old_state['status'] != 'RUNNING', 'original controller has terminated')
    inputs = read(campaign/'inputs.json')
    controller = campaign/'controller'
    for name in ('CONTRACT.md','generate.py','screen.py','target.py','check_target.py','run_target.py'):
        candidates = [p for p in inputs if p.endswith('/gs32-rvv/'+name)]
        need(len(candidates) == 1 and sha(controller/name) == inputs[candidates[0]],
             'actual frozen controller snapshot '+name)
    need(all(name not in sys.modules for name in ('generate','screen','target','check_target','run_target')),
         'fresh process with no preloaded controller modules')
    sys.path.insert(0,str(controller))
    runtime = importlib.import_module('run_target')
    check = importlib.import_module('check_target')
    runtime.verify_files(inputs)
    need(inputs[str(build/'gs32-target.elf')] == sha(build/'gs32-target.elf')
         and inputs[str(build/'gs32-target.bin')] == sha(build/'gs32-target.bin'), 'same original target bytes')
    out.mkdir(parents=True)
    reports, receipts = {}, {}
    state = dict(status='RUNNING',contract=runtime.target.CONTRACT,started=now(),
        original_campaign=str(campaign),original_state=old_state['status'],
        original_state_sha256=sha(campaign/'state.json'),input_inventory_sha256=sha(campaign/'inputs.json'),
        rechecker_sha256=sha(Path(__file__).resolve()),new_emu_runs=0,analysis_workers=1)
    save(out/'state.json',state)
    try:
        for name,core in (('negative',0),('recovery',0),('replay',1)):
            run = campaign/'runs'/name
            receipt = read(run/'runtime.json')
            receipts[name] = receipt
            negative = name == 'negative'
            reference = runtime.NEGATIVE if negative else runtime.REFERENCE
            expected = ['/usr/bin/taskset','-c',str(core),str(runtime.EMU),'-i',str(build/'gs32-target.bin'),
                '--flash='+str(runtime.FLASH),'--ram-size=128MB','--diff='+str(reference),
                '--max-cycles=12000000','--seed=1']
            need(receipt['command'] == expected and receipt['reference'] == str(reference)
                 and receipt['cwd'] == str(run/'cwd') and receipt['process_started']
                 and receipt.get('finished') and not receipt['timed_out'], 'complete exact runtime '+name)
            for raw_name in ('stdout.log','stderr.log'):
                need(sha(run/raw_name) == receipt['raw_sha256'][raw_name], 'unchanged raw log '+name+'/'+raw_name)
            text = (run/'stderr.log').read_text()+(run/'stdout.log').read_text()
            runtime.banner(text,reference)
            if negative:
                report = check.helper(repo,'team/optimizations/o1/audit/runtime_gate.py').validate_negative(text,receipt['exit_code'])
                check.helper(repo,'team/optimizations/o2/fullcore/recheck.py').reject_fatal_output(text)
                model,_,_ = check.support(repo)
                elf = model.ELF((build/'gs32-target.elf').read_bytes())
                need(int(report['pc'],16) == elf.symbols['q_fault_probe'][0]+20, 'same isolated negative probe')
                report.update(status='GS32_EXPECTED_BIT100_REJECTION')
            else:
                need(receipt['started'] >= receipts['negative']['finished'], 'negative terminated before normal run')
                report = check.analyze(repo,build,run,receipt)
            reports[name] = report
            save(out/(name+'.json'),report)
            print(json.dumps(dict(name=name,status=report['status'],at=now())),flush=True)
        need(len({r['pid'] for r in receipts.values()}) == 3, 'three distinct original EMU processes')
        a,b = reports['recovery'],reports['replay']
        replay_fields = ('samples','all_stage_custom_pc_sha256')
        need(all(a[key] == b[key] for key in replay_fields),
             'frozen contract deterministic counter and PC replay equality')
        # The original contract compares counter samples and custom PC paths.
        # protocol.input_sha256 hashes the entire host log, including text that
        # is not a simulated event. Preserve both hashes as provenance. The
        # richer event comparison is diagnostic, not a new acceptance gate.
        semantic_protocol = lambda report: {k:v for k,v in report['protocol'].items()
                                           if k != 'input_sha256'}
        protocol_replay_equal = semantic_protocol(a) == semantic_protocol(b)
        runtime.verify_files(inputs)
        summary = dict(status='GS32_TARGET_SERIAL_RAW_RECHECK_PASS',contract=runtime.target.CONTRACT,
            original_controller_state=old_state['status'],original_controller_error=old_state.get('error'),
            source_emu_runs=3,new_emu_runs=0,negative_before_recovery_and_replay=True,
            frozen_contract_replay_equal=True,replay_fields=list(replay_fields),
            semantic_protocol_replay_equal=protocol_replay_equal,
            raw_protocol_input_sha256={name:reports[name]['protocol']['input_sha256']
                                       for name in ('recovery','replay')},
            selection=a['selection'],
            reports_sha256={name:sha(out/(name+'.json')) for name in reports},
            original_raw_sha256={name:r['raw_sha256'] for name,r in receipts.items()},
            complete_timed_retirement_paths=True,full_application_performance_qualified=False)
        save(out/'result.json',summary)
        state.update(status=summary['status'],result_sha256=sha(out/'result.json'))
    except BaseException as error:
        state.update(status='FAILED',error=repr(error))
        raise
    finally:
        state['finished'] = now()
        save(out/'state.json',state)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for option in ('repo','build','campaign','output'):
        p.add_argument('--'+option,type=Path,required=True)
    args = p.parse_args()
    sys.dont_write_bytecode = True
    allowed = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0,[allowed[0]])
    result = recheck(args.repo.resolve(),args.build.resolve(),args.campaign.resolve(),args.output.resolve())
    print(json.dumps(result,indent=2))
