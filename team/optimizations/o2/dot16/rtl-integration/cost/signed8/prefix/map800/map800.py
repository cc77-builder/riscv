#!/usr/bin/env python3
"""One feature1 remapping of the frozen prefix RTL, with unchanged 1ns STA."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

BASE = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056')
OLD = BASE / 'runs/dot16-prefix-20261107-main/local-01'
RUN = BASE / 'runs/dot16-prefix-map800-20261108-main'
LIB = Path('/home/lizufan/riscv-tools/nangate45/NangateOpenCellLibrary_typical.lib')
CONTRACT = 'dot16-prefix-feature1-map800-v1'
FIXED = {
    str(OLD/'result.json'): 'a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0',
    str(OLD/'inputs.json'): '1afacb22c143705355ffed93b62824b2a02153e799b003bcc7f92dba1b10c219',
    str(OLD/'final-artifact-pins.json'): '07d4a614ba2b7fd06652290d266023ae405881578cc370fa86d368086baa3451',
    str(OLD/'source-snapshot/process_helper.py'): 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3',
    str(OLD/'source-snapshot/cost_helpers.py'): 'bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209',
    '/usr/bin/yosys': 'dab84e88b53146fe22d675a142de32b1e545ee9b7fe1054238f6220245b24c8d',
    '/usr/bin/berkeley-abc': '9f8539df83c751324a16ee98878b0e7e200a7ed4916d5270da3d9b2390c5ffc7',
    '/usr/bin/sta': '9630070fdbcfd2a92a9d0dc6b6e5480f7be8e216b720f1fb32f447fb4cedc2ff',
    str(LIB): '8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1',
}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def derive(oldmap, oldsta, olddir, out):
    need(oldmap.count(' -D 1000 -constr ') == 1, 'one original mapping target')
    mapping = oldmap.replace(str(olddir), str(out)).replace(' -D 1000 -constr ', ' -D 800 -constr ', 1)
    timing = oldsta.replace(str(olddir), str(out))
    need(mapping.replace(' -D 800 -constr ', ' -D 1000 -constr ', 1).replace(str(out), str(olddir)) == oldmap,
         'mapping inverse differs')
    need(timing.replace(str(out), str(olddir)) == oldsta, 'STA inverse differs')
    return mapping, timing


def run(a):
    need(sys.dont_write_bytecode, 'invoke with -B to protect closed inputs')
    out = a.output
    need(out.is_absolute() and out == out.resolve() and out.parent == RUN and out.name == 'local-01',
         'fixed isolated output required')
    need(not out.exists() and not out.is_symlink(), 'output must be fresh')
    deadline = time.monotonic() + 420
    os.sched_setaffinity(0, {2})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    pins = dict(FIXED)
    for path, h in pins.items():
        need(sha(path) == h, 'fixed input differs: '+path)
    before = json.loads((OLD/'result.json').read_bytes())
    need(before['status'] == 'PREFIX_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE' and
         before['inputs_unchanged'] and before['all_children_reaped'], 'closed prefix baseline required')
    oldinputs = json.loads((OLD/'inputs.json').read_bytes())
    final = json.loads((OLD/'final-artifact-pins.json').read_bytes())
    olddir = OLD/'cost-feature1/mapped'
    rtl = OLD/'cost-feature1/rtl'
    required = [olddir/n for n in ('map.ys','timing.tcl','abc.constr')]
    required += [rtl/n for n in ('VDotCarrySaveRows.sv','VDotPrefixFinish20.sv','VDotElastic.sv','CommonFuCostTop.sv')]
    for p in required:
        need(str(p) in final, 'old final pin missing: '+str(p))
        pins[str(p)] = final[str(p)]
        need(sha(p) == pins[str(p)], 'old mapped input changed: '+str(p))
    for p in ('/usr/bin/yosys','/usr/bin/berkeley-abc','/usr/bin/sta',str(LIB)):
        need(oldinputs['originals'][p] == pins[p], 'tool or library differs from original recipe')
    base = before['cost_results'][1]
    need(base['feature'] == 1 and base['dff_cells'] == 1678 and
         abs(base['cell_area'] - 17965.374) < 1e-6, 'exact feature1 baseline')
    oldmap, oldsta = (olddir/'map.ys').read_text(), (olddir/'timing.tcl').read_text()
    mapping, timing = derive(oldmap, oldsta, olddir, out)
    need([x for x in mapping.splitlines() if x.startswith('read_verilog ')] ==
         ['read_verilog -sv -DSYNTHESIS '+str(p) for p in required[3:]], 'unchanged four RTL inputs')
    if not a.execute:
        print(json.dumps(dict(status='PLAN_ONLY', output=str(out), original_pins=pins,
                             map_script=mapping, sta_script=timing), indent=2))
        return
    util = module(OLD/'source-snapshot/process_helper.py', 'map800_process')
    helper = module(OLD/'source-snapshot/cost_helpers.py', 'map800_cost')
    out.mkdir(parents=True, exist_ok=False)
    tmp = out/'tmp'; tmp.mkdir()
    snap = out/'source-snapshot'; snap.mkdir()
    selfpins = {str(p):sha(p) for p in (Path(__file__), Path(__file__).with_name('CONTRACT.md'))}
    pins.update(selfpins)
    for p in required + [Path(__file__), Path(__file__).with_name('CONTRACT.md'),
                         OLD/'result.json', OLD/'inputs.json', OLD/'final-artifact-pins.json',
                         OLD/'source-snapshot/process_helper.py', OLD/'source-snapshot/cost_helpers.py']:
        name = 'original-'+p.name if p.parent == olddir else p.name
        need(not (snap/name).exists(), 'unique snapshot filename')
        (snap/name).write_bytes(p.read_bytes())
        need(sha(snap/name) == pins[str(p)], 'snapshot differs from pinned source: '+str(p))
    (out/'map.ys').write_text(mapping)
    (out/'timing.tcl').write_text(timing)
    (out/'abc.constr').write_bytes((olddir/'abc.constr').read_bytes())
    generated_pins = {str(p):sha(p) for p in [*snap.iterdir(), out/'map.ys',out/'timing.tcl',out/'abc.constr']}
    save(out/'inputs.json', dict(originals=pins, generated=generated_pins))
    result = dict(contract=CONTRACT, status='RUNNING', started=util.stamp(), commands=[],
                  cpu_affinity=[2], nice=5, budget_seconds=420, feature=1,
                  original_abc_delay_ps=1000, abc_delay_ps=800, sta_period_ns=1.0,
                  unchanged_rtl=True, rtl_functional_evidence_reused=True,
                  mapped_netlist_equivalence_tested=False,
                  new_rtl_compilations=0, new_fu_runs=0, new_core_runs=0,
                  application_performance_qualified=False, core_cost_qualified=False,
                  production_default_changed=False, baseline_cost=base)
    save(out/'result.json', result)
    pending = [None]
    def interrupt(sig, frame):
        pending[0] = sig
    def check():
        if pending[0] is not None:
            raise InterruptedError(str(pending[0]))
        need(time.monotonic() < deadline, 'total budget exhausted')
    prior = {sig:signal.signal(sig, interrupt) for sig in (signal.SIGTERM,signal.SIGINT)}
    env = dict(PATH='/usr/bin:/bin', LANG='C', LC_ALL='C', TZ='UTC', TMPDIR=str(tmp),
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    def command(label, argv, limit):
        check()
        row = dict(label=label, argv=list(map(str, argv)), started=util.stamp(), budget_seconds=min(limit,deadline-time.monotonic()))
        result['commands'].append(row); proc = None
        try:
            with (out/(label+'.log')).open('wb') as log:
                proc = subprocess.Popen(row['argv'], cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                row['pid'] = proc.pid; save(out/'result.json', result)
                until = time.monotonic()+row['budget_seconds']
                while proc.poll() is None:
                    check()
                    left = until-time.monotonic()
                    if left <= 0:
                        raise subprocess.TimeoutExpired(row['argv'], row['budget_seconds'])
                    try:
                        proc.wait(timeout=min(.25,left))
                    except subprocess.TimeoutExpired:
                        pass
                row['exit_code'] = proc.returncode
            check()
            need(time.monotonic() <= until, label+' stage budget exhausted')
            need(row['exit_code'] == 0, label+' failed')
            need(not util.group_exists(proc.pid), label+' left child processes')
        finally:
            if proc is not None:
                if util.group_exists(proc.pid):
                    row['cleanup_complete'] = util.stop_group(proc)
                row['reaped'] = proc.poll() is not None
                row['group_absent'] = not util.group_exists(proc.pid)
            row['finished'] = util.stamp(); save(out/'result.json', result)
        return (out/(label+'.log')).read_text(errors='replace')
    try:
        log = command('map-feature1', ['/usr/bin/yosys','-T','-s',out/'map.ys'], 300)
        design = json.loads((out/'mapped.json').read_bytes())['modules']['CommonFuCostTop']
        counts = Counter(c['type'] for c in design['cells'].values())
        areas = helper.library_areas(LIB)
        need(not set(counts)-set(areas), 'unmapped cell')
        area = sum(areas[k]*n for k,n in counts.items())
        printed = re.findall(r'Chip area for module.*?:\s*([0-9.]+)',log)
        need(printed and abs(float(printed[-1])-area)<.02, 'area sum mismatch')
        ports = {n:dict(direction=p['direction'],width=len(p['bits']),offset=p.get('offset',0)) for n,p in design['ports'].items()}
        need(ports == base['ports'], 'complete interface differs')
        dffs = sum(v for k,v in counts.items() if k.startswith('DFF'))
        need(dffs == base['dff_cells'], 'DFF count changed in mapping-only comparison')
        log = command('sta-feature1', ['/usr/bin/sta','-no_init','-exit',out/'timing.tcl'], 60)
        need(not re.search(r'(?m)^.*\bError:',log) and 'not found' not in log and
             log.splitlines().count('DOT16_GENERATED_FU_STA_COMPLETE') == 1, 'incomplete STA')
        paths = {n:helper.parse_path((out/(n+'.rpt')).read_text()) for n in ('r2r','i2r','r2o','i2o','ready')}
        need(all(p['exists'] for p in paths.values()), 'missing setup path class')
        constants = helper.constant_warnings((out/'setup-checks.rpt').read_text(), design)
        for p,h in {**pins,**generated_pins}.items():
            check(); need(sha(p) == h, 'input changed: '+p)
        result.update(cell_area=area, cell_count=sum(counts.values()), cell_histogram=dict(sorted(counts.items())),
                      dff_cells=dffs, ports=ports, timing=paths, reviewed_constant_endpoints=constants,
                      nominal_setup_met=all(p['slack_ns']>=0 for p in paths.values()),
                      delta_from_D1000=dict(cell_area=area-base['cell_area'],
                          timing={n:{k:paths[n][k]-base['timing'][n][k] for k in ('arrival_ns','slack_ns')} for n in paths}),
                      mapped_sha256=sha(out/'mapped.v'), mapped_json_sha256=sha(out/'mapped.json'),
                      inputs_unchanged=True, all_children_reaped=all(c['reaped'] and c['group_absent'] for c in result['commands']))
        check()
        result['status'] = 'PREFIX_FEATURE1_MAP800_COST_COMPLETE'
    except BaseException as exc:
        result.update(status='FAILED', error=repr(exc))
        raise
    finally:
        result['finished'] = util.stamp(); save(out/'result.json', result)
        for sig,h in prior.items():
            signal.signal(sig,h)
    print(json.dumps({k:v for k,v in result.items() if k not in ('baseline_cost','cell_histogram','ports')},indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true')
    run(p.parse_args())
