#!/usr/bin/env python3
"""Isolated signed-byte expression screen; no production source is changed.

Reuses the completed common-FU mapping/STA scripts with path-only relocation.
The changed combinational product module is proved against its frozen original
before a new mapping is measured. This is not a core/performance qualification.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = 'dot16-common-fu-arithmetic-screen-v3'
GEN_SHA = '7b45921ee1b5ff564113daa61403c4e52ecb598305aad6c093f4ab5768fe0a09'
COST_SHA = '8c9a22771594565bfaa812309f68c84de4e8a213b02b9aba03440373f61e2e51'
PRODUCT_SHA = '0c1e566dd820f80382c64b98a74882ff400e5cb63cd511bcd19831759597178a'
REDUCE_SHA = 'ed09c5ac8ca7a0a910ac8d51000ef1de8f01dadca4bec544467d1678ebeaaf85'
HELPERS = {
    'helpers.py': ('team/optimizations/o2/dot16/cost_helpers.py', 'bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209'),
    'process_helper.py': ('team/optimizations/o2/dot16/rtl-integration/run_fu.py', 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'),
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def derive(raw, expression):
    need(hashlib.sha256(raw).hexdigest() == PRODUCT_SHA, 'frozen original product RTL')
    text = raw.decode()
    edits = []
    for lane in range(8):
        hi, lo = lane*8+7, lane*8
        matches = list(re.finditer(r'  assign io_products_' + str(lane) + r'\s*=.*?;', text, re.S))
        need(len(matches) == 1, 'one assignment per lane')
        before = matches[0].group()
        expected = ('assignio_products_' + str(lane) + '={{8{io_vs1[' + str(hi) + ']}},io_vs1['
                    + str(hi) + ':' + str(lo) + ']}*{{8{io_vs2[' + str(hi) + ']}},io_vs2['
                    + str(hi) + ':' + str(lo) + ']};')
        need(re.sub(r'\s+', '', before) == expected, 'exact existing unsigned sign-extension expression')
        after = (f'  assign io_products_{lane} = $signed(io_vs1[{hi}:{lo}])'
                 f' * $signed(io_vs2[{hi}:{lo}]);')
        if expression == 'sign15':
            # The exact signed-byte product fits signed16. Its sign is the
            # operand-sign XOR except that either zero operand makes zero.
            after = (f'  wire [14:0] low_product_{lane};\n'
                     f'  assign low_product_{lane} = $signed(io_vs1[{hi}:{lo}])'
                     f' * $signed(io_vs2[{hi}:{lo}]);\n'
                     f'  assign io_products_{lane} = {{((io_vs1[{hi}] ^ io_vs2[{hi}])'
                     f' & (|io_vs1[{hi}:{lo}]) & (|io_vs2[{hi}:{lo}])), low_product_{lane}}};')
        text = text.replace(before, after, 1)
        edits.append(dict(before=before, after=after))
    inverse = text
    for edit in reversed(edits):
        need(inverse.count(edit['after']) == 1, 'unique inverse')
        inverse = inverse.replace(edit['after'], edit['before'], 1)
    need(inverse.encode() == raw, 'whole original module reconstructed byte exactly')
    return text, edits


def derive_reduce(raw):
    need(hashlib.sha256(raw).hexdigest() == REDUCE_SHA, 'frozen original reduction RTL')
    text = raw.decode()
    start = text.index('  wire [16:0] sums17_0 =')
    end = text.index('endmodule', start)
    before = text[start:end]
    after = ('  wire signed [18:0] sum19 =\n    '
             + ' + '.join(f'$signed(io_products_{i})' for i in range(8))
             + ';\n  assign io_result = {96\'h0, {13{sum19[18]}}, sum19};\n')
    candidate = text[:start]+after+text[end:]
    need(candidate.replace(after,before,1).encode()==raw,'exact reduction inverse')
    return candidate, dict(before=before,after=after)


def main(a):
    pending_signal = [None]
    def interrupted(signum, frame):
        # Do not raise inside Popen or cleanup. Consume the first request at a
        # bounded safe point after the process object has been assigned.
        if pending_signal[0] is None:
            pending_signal[0] = signum
    def check_interrupt():
        if pending_signal[0] is not None:
            raise InterruptedError('received signal '+str(pending_signal[0]))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    os.sched_setaffinity(0, {a.cpu})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    deadline = time.monotonic() + a.budget_seconds
    repo, cost, out = (p.resolve() for p in (a.repo, a.cost_root, a.output))
    need(a.output.is_absolute() and Path(os.path.abspath(a.output)) == out and not out.exists(), 'fresh real output')
    need(not out.is_relative_to(repo) and not repo.is_relative_to(out), 'outside checkout')
    need(30 <= a.budget_seconds <= 600 and a.cpu in range(4), 'finite shared four-core budget')
    gen, baseline = cost/'generation-01', cost/'nominal-01'
    need(not any(out.is_relative_to(p) or p.is_relative_to(out) for p in (gen, baseline)),
         'preserve both frozen input trees')
    need(sha(gen/'result.json') == GEN_SHA and sha(baseline/'result.json') == COST_SHA, 'completed original identities')
    old = json.loads((baseline/'result.json').read_bytes())
    need(old['status'] == 'TWO_COMMON_FU_COSTS_RECORDED' and old['inputs_unchanged'], 'completed original mapping')
    point = old['results'][1]
    need(point['feature'] == 1 and point['sta_representation'] == 'original_mapped_bytes', 'original feature1 representation')
    source = gen/'feature1/rtl'
    contract = Path(__file__).with_name('ARITHMETIC_CONTRACT.md')
    pins = {str(p): sha(p) for p in (Path(__file__).resolve(), contract, gen/'result.json', baseline/'result.json')}
    for rec in json.loads((gen/'result.json').read_bytes())['generated'][1]['files']:
        p = gen/rec['path']
        need(p.parent == source and sha(p) == rec['sha256'] and p.stat().st_size == rec['bytes'], 'original RTL identity')
        pins[str(p)] = rec['sha256']
    need({Path(p).name for p in pins if Path(p).parent == source} == {'CommonFuCostTop.sv','VDotElastic.sv','VDotProducts.sv','VDotReduce.sv'}, 'closed original RTL')
    lib = Path(old['library']['path'])
    need(sha(lib) == old['library']['sha256'], 'same library')
    pins[str(lib)] = sha(lib)
    for rec in old['tools'].values():
        need(sha(rec['path']) == rec['sha256'], 'same installed tool')
        pins[rec['path']] = rec['sha256']
    for name, (rel, expected) in HELPERS.items():
        need(sha(repo/rel) == expected, 'unchanged helper '+name)
        pins[str(repo/rel)] = expected
    for name, key in [('map.ys','map_script_sha256'), ('timing.tcl','sta_script_sha256')]:
        p = baseline/'feature1'/name
        need(sha(p) == point[key], 'original exact mapping and timing template')
        pins[str(p)] = point[key]
    out.mkdir(parents=True)
    rtl = out/'generated-rtl'
    rtl.mkdir()
    snap = out/'source-snapshot'
    snap.mkdir()
    for name, (rel, _) in HELPERS.items():
        shutil.copyfile(repo/rel, snap/name)
    shutil.copyfile(Path(__file__), snap/'arithmetic_probe.py')
    shutil.copyfile(contract, snap/'ARITHMETIC_CONTRACT.md')
    helper = module(snap/'helpers.py', 'signed8_helpers')
    util = module(snap/'process_helper.py', 'signed8_process')
    for p in source.glob('*.sv'):
        shutil.copyfile(p, rtl/p.name)
    candidate, edits = derive((rtl/'VDotProducts.sv').read_bytes(), a.expression)
    (rtl/'VDotProducts.sv').write_text(candidate)
    save(out/'derivation.json', dict(expression=a.expression, edits=edits, original_sha256=PRODUCT_SHA,
         candidate_sha256=sha(rtl/'VDotProducts.sv'), exact_inverse=True))
    if a.reduction == 'flat19':
        reduction, reduce_edit = derive_reduce((rtl/'VDotReduce.sv').read_bytes())
        (rtl/'VDotReduce.sv').write_text(reduction)
        save(out/'reduction-derivation.json',dict(edit=reduce_edit,original_sha256=REDUCE_SHA,
             candidate_sha256=sha(rtl/'VDotReduce.sv'),exact_inverse=True))
    old_dir = str(baseline/'feature1')
    for name in ('map.ys','timing.tcl'):
        original = (baseline/'feature1'/name).read_text()
        changed = original.replace(old_dir, str(out))
        need(changed != original and changed.replace(str(out), old_dir) == original, 'path-only script relocation')
        (out/name).write_text(changed)
    (out/'abc.constr').write_text('set_driving_cell BUF_X1\nset_load 5.0\n')
    gold = (source/'VDotProducts.sv').read_text().replace('module VDotProducts(', 'module VDotProductsGold(', 1)
    gate = candidate.replace('module VDotProducts(', 'module VDotProductsGate(', 1)
    (out/'equivalence.sv').write_text(gold+'\n'+gate)
    (out/'prove.ys').write_text('\n'.join([
        'read_verilog -sv '+str(out/'equivalence.sv'),
        'miter -equiv -flatten VDotProductsGold VDotProductsGate product_miter',
        'prep -top product_miter -flatten',
        'sat -verify -prove trigger 0 -show-inputs -show-outputs'])+'\n')
    if a.reduction == 'flat19':
        rgold=(source/'VDotReduce.sv').read_text().replace('module VDotReduce(', 'module VDotReduceGold(', 1)
        rgate=reduction.replace('module VDotReduce(', 'module VDotReduceGate(', 1)
        (out/'reduce-equivalence.sv').write_text(rgold+'\n'+rgate)
        (out/'prove-reduce.ys').write_text('\n'.join([
            'read_verilog -sv '+str(out/'reduce-equivalence.sv'),
            'miter -equiv -flatten VDotReduceGold VDotReduceGate reduce_miter',
            'prep -top reduce_miter -flatten',
            'sat -verify -prove trigger 0 -show-inputs -show-outputs'])+'\n')
    snapshots = {str(p): sha(p) for p in out.rglob('*') if p.is_file()}
    save(out/'inputs.json', dict(originals=pins, snapshots=snapshots))
    result = dict(contract=CONTRACT, expression=a.expression, reduction=a.reduction, status='RUNNING', started=util.stamp(),
        cpu_affinity=[a.cpu], nice=5, budget_seconds=a.budget_seconds, jobs=1,
        boundary=old['boundary'], constraints=old['constraints'], commands=[],
        production_source_modified=False, new_elaborations=0, new_core_simulations=0,
        arithmetic_equivalent=False, products_equivalent=False, reduction_equivalent=False, functional_runtime_qualified=False,
        application_performance_qualified=False, core_cost_qualified=False,
        baseline_cost_receipt_sha256=COST_SHA)
    env = {**os.environ, 'LANG':'C','LC_ALL':'C','OMP_NUM_THREADS':'1',
           'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}

    def command(label, argv, limit):
        check_interrupt()
        remaining = deadline-time.monotonic()
        need(remaining > 1, 'total deadline before '+label)
        rec = dict(label=label, argv=list(map(str,argv)), started=util.stamp(),
                   budget_seconds=min(limit,remaining), exit_code=None)
        result['commands'].append(rec)
        proc = None
        try:
            with (out/(label+'.log')).open('wb') as log:
                proc = subprocess.Popen(rec['argv'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                rec['pid'] = proc.pid
                save(out/'result.json',result)
                command_deadline=time.monotonic()+rec['budget_seconds']
                while True:
                    check_interrupt()
                    left=command_deadline-time.monotonic()
                    if left<=0:
                        raise subprocess.TimeoutExpired(rec['argv'],rec['budget_seconds'])
                    try:
                        rec['exit_code']=proc.wait(timeout=min(0.25,left))
                        break
                    except subprocess.TimeoutExpired:
                        continue
            need(rec['exit_code'] == 0, label+' failed')
            need(not util.group_exists(proc.pid), label+' left children')
        finally:
            if proc is not None:
                if util.group_exists(proc.pid):
                    rec['cleanup_complete'] = util.stop_group(proc)
                rec['reaped'] = proc.poll() is not None
                rec['group_absent'] = not util.group_exists(proc.pid)
            rec['finished'] = util.stamp()
            save(out/'result.json',result)
        return (out/(label+'.log')).read_text(errors='replace')

    try:
        log = command('equivalence', [old['tools']['yosys']['path'],'-T','-s',out/'prove.ys'], 120)
        need('SAT proof finished - no model found: SUCCESS!' in log, 'complete all-input product equivalence proof')
        result['products_equivalent'] = True
        if a.reduction == 'flat19':
            log=command('equivalence-reduce',[old['tools']['yosys']['path'],'-T','-s',out/'prove-reduce.ys'],120)
            need('SAT proof finished - no model found: SUCCESS!' in log,'complete arbitrary-product reduction equivalence proof')
            result['reduction_equivalent']=True
        else:
            need(sha(rtl/'VDotReduce.sv')==REDUCE_SHA,'unchanged original reducer')
            result['reduction_equivalent']=True
        result['arithmetic_equivalent'] = True
        log = command('synthesis', [old['tools']['yosys']['path'],'-T','-s',out/'map.ys'], 180)
        design = json.loads((out/'mapped.json').read_bytes())['modules']['CommonFuCostTop']
        cells = Counter(c['type'] for c in design['cells'].values())
        areas = helper.library_areas(lib)
        need(not set(cells)-set(areas), 'all cells mapped')
        area = sum(areas[k]*v for k,v in cells.items())
        reported = re.findall(r'Chip area for module.*?:\s*([0-9.]+)',log)
        need(reported and abs(float(reported[-1])-area)<0.02, 'cell-area crosscheck')
        ports = {n:dict(direction=p['direction'],width=len(p['bits']),offset=p.get('offset',0)) for n,p in design['ports'].items()}
        need(ports == point['ports'], 'complete unchanged production port boundary')
        need(sum(v for k,v in cells.items() if k.startswith('DFF')) == point['dff_cells'], 'same complete state width')
        log = command('sta',[old['tools']['sta']['path'],'-no_init','-exit',out/'timing.tcl'],60)
        need(not re.search(r'(?m)^.*\bError:',log) and 'not found' not in log and log.splitlines().count('DOT16_GENERATED_FU_STA_COMPLETE')==1, 'complete error-free STA')
        timing = {n:helper.parse_path((out/(n+'.rpt')).read_text()) for n in ('r2r','i2r','r2o','i2o','ready')}
        need(all(x['exists'] for x in timing.values()), 'all existing path classes')
        constants = helper.constant_warnings((out/'setup-checks.rpt').read_text(),design)
        need(all(sha(p)==h for p,h in {**pins,**snapshots}.items()), 'all input and snapshot identities unchanged')
        need(time.monotonic()<deadline,'total deadline at final audit')
        check_interrupt()
        result.update(status='ARITHMETIC_EQUIVALENT_COST_SCREEN_COMPLETE',inputs_unchanged=True,
            cell_area=area,cell_count=sum(cells.values()),cell_histogram=dict(sorted(cells.items())),
            dff_cells=point['dff_cells'],area_delta=area-point['cell_area'],
            area_within_20000=area<=20000,timing=timing,reviewed_constant_endpoints=constants,
            nominal_setup_met=all(p['slack_ns']>=0 for p in timing.values()),
            mapped_sha256=sha(out/'mapped.v'),mapped_json_sha256=sha(out/'mapped.json'),
            candidate_product_sha256=sha(rtl/'VDotProducts.sv'))
    except BaseException as exc:
        result.update(status='FAILED',error=repr(exc))
        raise
    finally:
        result['finished']=util.stamp()
        save(out/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','cell_histogram','reviewed_constant_endpoints')},indent=2),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','cost-root','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expression', choices=('signed8','sign15'), required=True)
    p.add_argument('--reduction', choices=('unchanged','flat19'), required=True)
    p.add_argument('--cpu',type=int,choices=range(4),default=1)
    p.add_argument('--budget-seconds',type=int,default=540)
    main(p.parse_args())
