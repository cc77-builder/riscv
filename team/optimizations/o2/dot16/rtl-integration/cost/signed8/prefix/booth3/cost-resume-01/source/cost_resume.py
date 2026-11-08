#!/usr/bin/env python3
"""One frozen Booth3 cost completion: existing f0 first, then first f1 mapping."""
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
ROOT = BASE/'runs/dot16-prefix-booth3-20261108-main'
OLD = ROOT/'local-02'
OUT = ROOT/'cost-resume-01'
PREFIX = BASE/'runs/dot16-prefix-20261107-main/local-01'
NOMINAL = BASE/'runs/dot16-production-cost-20261107-main/nominal-01'
EXACT = BASE/'runs/dot16-prefix-fa-20261108-main/input-serial-01/fa_serialization.py'
LIB = Path('/home/lizufan/riscv-tools/nangate45/NangateOpenCellLibrary_typical.lib')
CONTRACT = 'dot16-booth3-one-shot-cost-continuation-v1'


def need(ok, message):
    if not ok:
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


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main(execute):
    need(sys.dont_write_bytecode, 'invoke with -B')
    started = time.monotonic()
    deadline = started+300
    os.sched_setaffinity(0, {2})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    here = Path(__file__).resolve().parent
    need(here == ROOT/'input-cost-01', 'fixed independent input directory')
    need(not OUT.exists() and not OUT.is_symlink(), 'fresh sole output')
    pins = json.loads((here/'FIXED_INPUTS.json').read_bytes())
    need(pins[str(OLD/'result.json')] == '63cee9334942c7e60405cef939ef3020b1817e5ee147cc7e12b22339884d9121', 'fixed FAILED02 identity')
    need(pins[str(EXACT)] == '82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a', 'unchanged complete circuit comparator')

    def pin(path, expected):
        path = Path(path).resolve()
        need(not path.is_relative_to(OUT), 'input outside fresh output')
        need(str(path) not in pins or pins[str(path)] == expected, 'consistent input pin')
        need(sha(path) == expected, 'fixed input changed: '+str(path))
        pins[str(path)] = expected

    for path, expected in list(pins.items()):
        pin(path, expected)
    inherited = json.loads((OLD/'inputs.json').read_bytes())
    for section in ('originals', 'snapshots'):
        for path, expected in inherited[section].items():
            pin(path, expected)
    for path, expected in json.loads((OLD/'overlay-classes.json').read_bytes()).items():
        pin(path, expected)
    for path in sorted(here.rglob('*')):
        need(not path.is_symlink(), 'no input symlinks')
        if path.is_file():
            pin(path, sha(path))
    need(pins[str(PREFIX/'source-snapshot/process_helper.py')] == 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3', 'fixed process helper')
    need(pins[str(PREFIX/'source-snapshot/cost_helpers.py')] == 'bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209', 'fixed cost helper')
    exact = module(EXACT, 'unchanged_terminal_graph')
    util = module(PREFIX/'source-snapshot/process_helper.py', 'booth3_cost_process')
    helper = module(PREFIX/'source-snapshot/cost_helpers.py', 'booth3_cost_helpers')
    prior = json.loads((OLD/'result.json').read_bytes())
    need(prior['status'] == 'FAILED' and prior['contract'] == 'dot16-prefix-booth3-balanced-gold-v1', 'original FAILED preserved')
    need(prior['arithmetic_proof_completed'] and prior['fu_tests_completed'] and prior['all_actual_DUT_SV_bytes_match_previous_failed_attempt'], 'completed exact candidate stages')
    need(not prior['arithmetic_equivalent'] and not prior['fu_qualified'] and not prior['local_cost_recorded'] and not prior['cost_results'], 'do not rewrite prior overall qualification')
    need(len(prior['prefix_miters']) == 2 and all(x['status'] == 'PASS' and x['solver_equivalence_proved'] and not x['counterexample_found'] for x in prior['prefix_miters']), 'two completed new R proofs')
    need(len(prior['fu_results']) == 2 and all(x['passed'] for x in prior['fu_results']), 'both completed FU consumers')
    need(len(prior['commands']) == 32 and all(c['reaped'] and c['group_absent'] for c in prior['commands']), 'closed original command set')
    for pid in [35290]+[c['pid'] for c in prior['commands']]:
        need(not util.group_exists(pid), 'prior process group still present')
    for entry in prior['generated']:
        folder = OLD/(entry['kind']+'-feature'+str(entry['feature']))/'rtl'
        for rec in entry['files']:
            path = OLD/rec['path']
            need(path.parent == folder and path.stat().st_size == rec['bytes'], 'exact generated consumer identity')
            pin(path, rec['sha256'])
        pin(folder/'filelist.f', entry['filelist_sha256'])
        pin(folder/'firrtl_black_box_resource_files.f', entry['resource_manifest_sha256'])
    for m in prior['prefix_miters']:
        pin(OLD/('actual-prefix-'+str(m['width'])+'-miter.log'), m['log_sha256'])
    for f in prior['fu_results']:
        pin(OLD/('fu-feature'+str(f['feature']))/'obj/VVDotElasticFuTestTop', f['binary_sha256'])
    old_cost = json.loads((NOMINAL/'result.json').read_bytes())
    baseline = json.loads((PREFIX/'result.json').read_bytes())
    need(pins[str(NOMINAL/'result.json')] == '8c9a22771594565bfaa812309f68c84de4e8a213b02b9aba03440373f61e2e51', 'original cost reference')
    need(pins[str(PREFIX/'result.json')] == 'a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0', 'fixed prefix comparison')
    need(old_cost['library']['path'] == str(LIB), 'same library')
    pin(LIB, old_cost['library']['sha256'])
    for rec in old_cost['tools'].values():
        pin(rec['path'], rec['sha256'])
    need(old_cost['tools']['yosys']['path'] == '/usr/bin/yosys' and old_cost['tools']['sta']['path'] == '/usr/bin/sta', 'fixed actual tools')
    for feature in (0, 1):
        for name, key in (('map.ys', 'map_script_sha256'), ('timing.tcl', 'sta_script_sha256')):
            pin(NOMINAL/f'feature{feature}'/name, old_cost['results'][feature][key])
        constraint = NOMINAL/f'feature{feature}'/'abc.constr'
        need(str(constraint) in pins and constraint.read_bytes() == b'set_driving_cell BUF_X1\nset_load 5.0\n', 'fixed ABC boundary')
    need(not list((OLD/'cost-feature1/mapped').glob('*')), 'feature1 mapping has not run')
    need(time.monotonic() < deadline, 'preflight within total budget')
    if not execute:
        print(json.dumps(dict(status='PLAN_ONLY', contract=CONTRACT, original_pins=pins, output=str(OUT), cpu_affinity=[2], total_seconds=300, sta_seconds=30, order='f0 existing mapping -> f0 graph/STA -> f1 first mapping -> f1 graph/STA')))
        return
    OUT.mkdir()
    (OUT/'tmp').mkdir()
    snap = OUT/'source-snapshot'
    snap.mkdir()
    generated = {}
    for p in sorted(here.rglob('*')):
        if p.is_file():
            dst = snap/p.relative_to(here)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(p.read_bytes())
            generated[str(dst)] = sha(dst)
    save(OUT/'inputs.json', dict(originals=pins, snapshots=generated))
    result = dict(contract=CONTRACT, status='RUNNING', started=util.stamp(), commands=[], cost_results=[],
                  prior_result_sha256=pins[str(OLD/'result.json')], prior_status_preserved='FAILED',
                  reused_source_stage_evidence=True, new_rtl=False, new_gold=False, new_fu_runs=0,
                  new_core_runs=0, feature0_new_mapping_runs=0, feature1_new_mapping_runs=0,
                  local_cost_recorded=False, rtl_to_mapped_equivalence_claimed=False,
                  parent_qualified=False, fullcore_qualified=False, application_performance_qualified=False,
                  core_cost_qualified=False, production_default_changed=False, cpu_affinity=[2], nice=5,
                  budget_seconds=300, sta_budget_seconds=30)
    save(OUT/'result.json', result)
    pending = [None]

    def interrupted(sig, frame):
        pending[0] = sig

    handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}

    def check():
        if pending[0] is not None:
            raise InterruptedError(str(pending[0]))
        need(time.monotonic() < deadline, 'total budget')

    env = dict(PATH='/usr/bin:/bin', LANG='C', LC_ALL='C', TZ='UTC', TMPDIR=str(OUT/'tmp'),
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')

    def command(label, argv, limit):
        check()
        row = dict(label=label, argv=list(map(str, argv)), started=util.stamp(), budget_seconds=min(limit, deadline-time.monotonic()))
        until = min(deadline, time.monotonic()+row['budget_seconds'])
        result['commands'].append(row)
        proc = None
        try:
            with (OUT/(label+'.log')).open('wb') as log:
                proc = subprocess.Popen(row['argv'], cwd=OUT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                row['pid'] = proc.pid
                save(OUT/'result.json', result)
                while proc.poll() is None:
                    check()
                    left = until-time.monotonic()
                    if left <= 0:
                        raise subprocess.TimeoutExpired(row['argv'], row['budget_seconds'])
                    try:
                        proc.wait(timeout=min(.25, left))
                    except subprocess.TimeoutExpired:
                        pass
                row['exit_code'] = proc.returncode
            check()
            need(time.monotonic() <= until and proc.returncode == 0, label+' failed or exceeded budget')
            need(not util.group_exists(proc.pid), label+' remaining group')
        finally:
            if proc is not None:
                if util.group_exists(proc.pid):
                    row['cleanup_complete'] = util.stop_group(proc)
                row['exit_code'] = proc.poll()
                row['reaped'] = proc.poll() is not None
                row['group_absent'] = not util.group_exists(proc.pid)
            row['finished'] = util.stamp()
            save(OUT/'result.json', result)
        return (OUT/(label+'.log')).read_text(errors='replace')

    try:
        for feature in (0, 1):
            check()
            pointdir = OUT/f'feature{feature}'
            pointdir.mkdir()
            serial = pointdir/'serialized'
            serial.mkdir()
            if feature == 0:
                raw = OLD/'cost-feature0/mapped'
                map_log = (OLD/'map-0.log').read_text()
                template_dir = raw
                original_sta = (raw/'timing.tcl').read_text()
            else:
                need(len(result['cost_results']) == 1 and result['cost_results'][0]['feature'] == 0, 'f0 complete before any f1 mapping')
                raw = pointdir/'mapping'
                raw.mkdir()
                template_dir = NOMINAL/'feature1'
                original_rtl = template_dir/'generated-rtl'
                rtl = OLD/'cost-feature1/rtl'
                (raw/'abc.constr').write_bytes((template_dir/'abc.constr').read_bytes())
                original_map = (template_dir/'map.ys').read_text()
                changed = original_map.replace(str(original_rtl), str(rtl)).replace(str(template_dir), str(raw))
                old_lines = [line for line in changed.splitlines() if line.startswith('read_verilog ')]
                need(len(old_lines) == 4, 'original four-module map input list')
                old_block = '\n'.join(old_lines)+'\n'
                new_block = '\n'.join('read_verilog -sv -DSYNTHESIS '+str(rtl/n) for n in
                                      ('VDotCarrySaveRows.sv', 'VDotPrefixFinish20.sv', 'VDotElastic.sv', 'CommonFuCostTop.sv'))+'\n'
                need(changed.count(old_block) == 1, 'one contiguous original map read block')
                changed = changed.replace(old_block, new_block, 1)
                inverse = changed.replace(new_block, old_block, 1).replace(str(raw), str(template_dir)).replace(str(rtl), str(original_rtl))
                need(inverse == original_map, 'original complete D1000 map template recovered')
                (raw/'map.ys').write_text(changed)
                generated.update({str(p): sha(p) for p in (raw/'map.ys', raw/'abc.constr')})
                result['feature1_new_mapping_runs'] = 1
                save(OUT/'result.json', result)
                map_log = command('map-1', ['/usr/bin/yosys', '-T', '-s', raw/'map.ys'], 60)
                original_sta = (template_dir/'timing.tcl').read_text()
            original = json.loads((raw/'mapped.json').read_bytes())['modules']['CommonFuCostTop']
            graph = exact.circuit(original)
            counts = Counter(c['type'] for c in original['cells'].values())
            areas = helper.library_areas(LIB)
            need(not set(counts)-set(areas), 'complete actual standard cell mapping')
            area = sum(areas[k]*v for k, v in counts.items())
            printed = re.findall(r'Chip area for module.*?:\s*([0-9.]+)', map_log)
            need(printed and abs(float(printed[-1])-area) < .02, 'independent actual area sum')
            dff = sum(v for k, v in counts.items() if k.startswith('DFF'))
            if feature == 0:
                need(len(original['cells']) == 6236 and dff == 1658, 'fixed existing f0 mapped identity')
            ports = {n: dict(direction=p['direction'], width=len(p['bits']), offset=p.get('offset', 0)) for n, p in original['ports'].items()}
            reference = next(x for x in baseline['cost_results'] if x['feature'] == feature)
            need(ports == reference['ports'] and len(ports) == 220, 'unchanged complete FU boundary')
            serialize = ('read_json '+str(raw/'mapped.json')+'\nsplitnets\n'
                         'write_json '+str(serial/'split.json')+'\n'
                         'write_verilog -noattr -norename '+str(serial/'mapped.v')+'\n')
            reparse = ('read_liberty -lib '+str(LIB)+'\nread_verilog '+str(serial/'mapped.v')+'\n'
                       'hierarchy -check -top CommonFuCostTop\ncheck -assert\n'
                       'write_json '+str(serial/'reparsed.json')+'\n')
            need(original_sta.count(str(template_dir)) == 7, 'one netlist and six report paths only')
            sta = original_sta.replace(str(template_dir), str(serial))
            need(sta.replace(str(serial), str(template_dir)) == original_sta, 'exact complete same-constraint STA inverse')
            for name, value in (('serialize.ys', serialize), ('reparse.ys', reparse), ('timing.tcl', sta)):
                (serial/name).write_text(value)
                generated[str(serial/name)] = sha(serial/name)
            command(f'serialize-{feature}', ['/usr/bin/yosys', '-T', '-s', serial/'serialize.ys'], 30)
            need(not re.search(r'(?m)^\s*assign\s*\{', (serial/'mapped.v').read_text()), 'concat LHS remains')
            split = json.loads((serial/'split.json').read_bytes())['modules']['CommonFuCostTop']
            need(exact.circuit(split) == graph, 'splitnets changed complete terminal graph')
            command(f'reparse-{feature}', ['/usr/bin/yosys', '-T', '-s', serial/'reparse.ys'], 30)
            reparsed = json.loads((serial/'reparsed.json').read_bytes())['modules']['CommonFuCostTop']
            mapping = {n: ('\\'+n if n.startswith('$') else n) for n in original['cells']}
            need(len(set(mapping.values())) == len(mapping) and set(mapping.values()) == set(reparsed['cells']), 'complete collision-free explicit cell-name bijection')
            inverse_names = {v: k for k, v in mapping.items()}
            renamed = dict(reparsed)
            renamed['cells'] = {inverse_names[k]: v for k, v in reparsed['cells'].items()}
            need(exact.circuit(renamed) == graph, 'serialized complete graph differs after exact inverse cell names')
            save(serial/'cell-name-map.json', mapping)
            audit = dict(status='EXACT_TERMINAL_GRAPH_MATCH_UNDER_EXPLICIT_CELL_NAME_BIJECTION',
                         original_json_sha256=sha(raw/'mapped.json'), split_json_sha256=sha(serial/'split.json'),
                         reparsed_json_sha256=sha(serial/'reparsed.json'), mapped_verilog_sha256=sha(serial/'mapped.v'),
                         graph_sha256=object_sha(graph), inverse_graph_sha256=object_sha(exact.circuit(renamed)),
                         mapping_sha256=object_sha(sorted(mapping.items())), mapping_file_sha256=sha(serial/'cell-name-map.json'),
                         cells=len(graph['cells']), ports=len(graph['ports']), nets=len(graph['nets']),
                         terminal_count=sum(len(n['terminals']) for n in graph['nets']),
                         changed_cell_names=sum(k != v for k, v in mapping.items()), complete_bijection=True,
                         rule='Only an original dollar-prefixed cell name gets one literal leading backslash; no other names or circuit fields change.',
                         rtl_to_mapped_equivalence_claimed=False)
            save(serial/'graph-audit.json', audit)
            log = command(f'sta-{feature}', ['/usr/bin/sta', '-no_init', '-exit', serial/'timing.tcl'], 30)
            need(not re.search(r'(?m)^.*\bError:', log) and 'not found' not in log and
                 log.splitlines().count('DOT16_GENERATED_FU_STA_COMPLETE') == 1, 'complete error-free actual STA')
            timing = {n: helper.parse_path((serial/(n+'.rpt')).read_text()) for n in ('r2r', 'i2r', 'r2o', 'i2o', 'ready')}
            need(all(p['exists'] for p in timing.values()), 'all five timing classes')
            constants = helper.constant_warnings((serial/'setup-checks.rpt').read_text(), reparsed)
            result['cost_results'].append(dict(feature=feature, cell_area=area, cell_count=sum(counts.values()),
                dff_cells=dff, ports=ports, cell_histogram=dict(sorted(counts.items())), timing=timing,
                serialization_graph_audit=audit, reviewed_constant_endpoints=constants,
                nominal_setup_met=all(p['slack_ns'] >= 0 for p in timing.values()), area_within_20000=area <= 20000,
                delta_from_prefix=dict(cell_area=area-reference['cell_area'], dff_cells=dff-reference['dff_cells'],
                    timing={n: {k: timing[n][k]-reference['timing'][n][k] for k in ('arrival_ns', 'slack_ns')} for n in timing}),
                raw_mapped_json_sha256=sha(raw/'mapped.json'), serialized_verilog_sha256=sha(serial/'mapped.v'),
                same_constraints_path_only_inverse=True))
            save(OUT/'result.json', result)
        need(len(result['commands']) == 7 and result['feature1_new_mapping_runs'] == 1, 'exact single continuation sequence')
        result.update(status='BOOTH3_SERIALIZED_TWO_FEATURE_COST_COMPLETE', local_cost_recorded=True)
        check()
    except BaseException as exc:
        result.update(status='FAILED', error=repr(exc), local_cost_recorded=False)
        raise
    finally:
        changed = []
        for path, expected in {**pins, **generated}.items():
            try:
                if sha(path) != expected:
                    changed.append(path)
            except OSError:
                changed.append(path)
        result['changed_inputs'] = changed
        result['inputs_unchanged'] = not changed
        result['all_children_reaped'] = all(c.get('reaped') and c.get('group_absent') for c in result['commands'])
        artifacts = {}
        for path in sorted(OUT.rglob('*')):
            if path.is_file() and path.name not in ('result.json', 'artifact-pins.json'):
                artifacts[str(path.relative_to(OUT))] = dict(bytes=path.stat().st_size, sha256=sha(path))
        save(OUT/'artifact-pins.json', dict(scope='All produced artifacts, including partial failure evidence; not a success marker.', files=artifacts))
        result['elapsed_seconds'] = time.monotonic()-started
        result['total_budget_exceeded'] = time.monotonic() >= deadline
        if changed or not result['all_children_reaped'] or result['total_budget_exceeded'] or pending[0] is not None:
            result.update(status='FAILED', local_cost_recorded=False, finalization_error='input, process cleanup, total budget or pending signal failed')
        result['finished'] = util.stamp()
        save(OUT/'result.json', result)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    if time.monotonic() >= deadline or pending[0] is not None:
        result.update(status='FAILED', local_cost_recorded=False, total_budget_exceeded=time.monotonic() >= deadline,
                      finalization_error='deadline or pending signal after final result persistence')
        save(OUT/'result.json', result)
    need(result['status'] == 'BOOTH3_SERIALIZED_TWO_FEATURE_COST_COMPLETE', 'final continuation status')
    print(json.dumps(dict(status=result['status'], elapsed_seconds=result['elapsed_seconds'],
                          local_cost_recorded=True, area=[x['cell_area'] for x in result['cost_results']]), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    main(parser.parse_args().execute)

