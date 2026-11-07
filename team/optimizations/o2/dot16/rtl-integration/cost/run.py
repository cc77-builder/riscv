#!/usr/bin/env python3
"""Two nominal costs for separately generated, full-production-IO FU RTL.

The v2 generation receipt binds the prior source evidence and unchanged O4
generator. This mapping stage adds no functional, parent/core or power claim.
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
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = 'dot16-production-common-fu-cost-v2'
TOP = 'CommonFuCostTop'
LIB_SHA = '8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1'
SOURCE_SHA = '80637d38348fbecd928f6442fd0c69fab763a918ac8da8642a5a3667dacdc9c2'
HELPERS = {
    'helpers.py': ('team/optimizations/o2/dot16/cost_helpers.py', 'bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209'),
    'canonical.py': ('team/optimizations/o4/canonical.py', 'afdcb91be728520ffae6b468f46db87cd3d680694f9bfe6935bc9566d10ab688'),
    'compact.py': ('team/optimizations/o4/compact.py', '07a4f3a2b49af280e33f6c145ea7462f4184d1d27e2f890857a365543a90b572'),
    'process_helper.py': ('team/optimizations/o2/dot16/rtl-integration/run_fu.py', 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'),
}
TOOLS = {
    'yosys': ('/usr/bin/yosys', 'dab84e88b53146fe22d675a142de32b1e545ee9b7fe1054238f6220245b24c8d'),
    'abc': ('/usr/bin/berkeley-abc', '9f8539df83c751324a16ee98878b0e7e200a7ed4916d5270da3d9b2390c5ffc7'),
    'sta': ('/usr/bin/sta', '9630070fdbcfd2a92a9d0dc6b6e5480f7be8e216b720f1fb32f447fb4cedc2ff'),
}
VARIANTS = (('feature0', 0), ('feature1', 1))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def main(a):
    os.sched_setaffinity(0, {a.cpu})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    started = time.monotonic()
    deadline = started + a.budget_seconds
    repo, generation, out, lib = (x.resolve() for x in (a.repo, a.generation, a.output, a.library))
    need(a.output.is_absolute() and Path(os.path.abspath(a.output)) == out and not out.exists(), 'fresh real absolute output')
    need(not out.is_relative_to(repo) and not repo.is_relative_to(out), 'output outside repository')
    need(not out.is_relative_to(generation) and not generation.is_relative_to(out), 'preserve completed generation')
    need(30 <= a.budget_seconds <= 900 and a.cpu in range(4), 'finite four-core resource contract')
    need(re.fullmatch(r'[0-9a-f]{64}', a.generation_sha256), 'explicit complete generation receipt identity')
    gen_receipt = generation/'result.json'
    need(sha(gen_receipt) == a.generation_sha256 and sha(lib) == LIB_SHA, 'fixed generation and Nangate45 library')
    previous = json.loads(gen_receipt.read_bytes())
    need(previous.get('contract') == 'dot16-production-fu-cost-generation-v2' and
         previous.get('status') == 'TWO_COST_INPUTS_GENERATED_AND_PARSED' and
         previous.get('top') == TOP and previous.get('original_rtl_reproduced_byte_exact') is True and
         previous.get('input_identity_unchanged') is True and previous.get('functional_qualified') is False,
         'completed applicable generation, with original reproduction and no inherited functional PASS')
    expected_commands = ['java-version', 'firtool-version', 'reproduce-original-feature1',
                         'compile-cost-generator', 'generate-feature0', 'parse-feature0',
                         'generate-feature1', 'parse-feature1']
    need([x['label'] for x in previous['commands']] == expected_commands and
         all(x['exit_code'] == 0 and x['reaped'] is True and x['group_absent'] is True
             for x in previous['commands']), 'all generation commands completed and reaped')
    contract = Path(__file__).with_name('CONTRACT.md')
    pins = {str(p): sha(p) for p in (Path(__file__).resolve(), contract, gen_receipt, lib)}
    generation_pins = {
        'source-snapshot/elaborate.py': '28d2eab98b5ca45a34d9b3ffc67fd347240b4b0dc96b3aa2bbe20efe53e9ad0e',
        'source-snapshot/GENERATION_CONTRACT.md': '09a4f1984373f81e533cf4216a7d92276e54b7c92c138dfde40e56274a4fd895',
        'source-snapshot/GenerateVDotCost.scala': 'de06a6f46d19d6d4a42cbcff19f081e7423747578951c9b341d50076a913e97b',
        'source-snapshot/original-source.json': SOURCE_SHA,
        'source-snapshot/old-classpath.json': 'ab6aaa12cb8b9508d1a1bf994d63561a08f2112ea6d9d48b30ac7916fc1dfdde',
    }
    for rel, expected in generation_pins.items():
        p = generation/rel
        need(sha(p) == expected, 'fixed generation input snapshot '+rel)
        pins[str(p)] = expected
    for rel in ('inputs.json', 'classpath-before.json'):
        pins[str(generation/rel)] = sha(generation/rel)
    for rel, expected in HELPERS.values():
        p = repo/rel
        need(sha(p) == expected, 'fixed team helper '+rel)
        pins[str(p)] = expected
    for p, expected in TOOLS.values():
        need(sha(p) == expected, 'fixed installed tool '+p)
        pins[p] = expected
    need([r['feature'] for r in previous['generated']] == [0, 1], 'ordered two-point generation')
    generated = {}
    flags = []
    for point in previous['generated']:
        label = 'feature'+str(point['feature'])
        names = []
        for rec in point['files']:
            p = (generation/rec['path']).resolve()
            need(p.parent == generation/label/'rtl' and p.is_file() and
                 p.stat().st_size == rec['bytes'] and sha(p) == rec['sha256'], 'exact generated RTL within its closed directory')
            names.append(p)
            pins[str(p)] = rec['sha256']
        need({p.name for p in names} == {'CommonFuCostTop.sv', 'VDotElastic.sv', 'VDotProducts.sv', 'VDotReduce.sv'}
             and len(names) == 4, 'closed four-file RTL set')
        generated[label] = names
        config = dict(point['flags'])
        need(config.pop('VDOT_DOT16') == str(point['feature']), 'explicit feature flag')
        flags.append(config)
    need(flags[0] == flags[1] == dict(VDOT_O2_ELASTIC='1', VDOT_T14_FUSED_INPUT='1',
         VDOT_O1_HANDOFF='0', VDOT_T12_TRACE='0', VDOT_T13_TRACE='0', VDOT_O1_TRACE='0', VDOT_O2_TRACE='0'),
         'only dot16 feature differs')
    need(sha(generation/'feature0/rtl/CommonFuCostTop.sv') ==
         sha(generation/'feature1/rtl/CommonFuCostTop.sv'), 'identical complete production top interface and connections')

    out.mkdir(parents=True)
    snap = out/'source-snapshot'
    snap.mkdir()
    shutil.copyfile(Path(__file__), snap/'run.py')
    shutil.copyfile(contract, snap/'CONTRACT.md')
    for name, (rel, _) in HELPERS.items():
        shutil.copyfile(repo/rel, snap/name)
        need(sha(snap/name) == pins[str(repo/rel)], 'copied helper identity')
    need(sha(snap/'run.py') == pins[str(Path(__file__).resolve())] and
         sha(snap/'CONTRACT.md') == pins[str(contract)], 'copied controller identity')
    for rel in ['result.json', 'inputs.json', 'classpath-before.json', *generation_pins]:
        dest = out/'generation-evidence'/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generation/rel, dest)
        need(sha(dest) == pins[str(generation/rel)], 'copied generation evidence')
    sys.path.insert(0, str(snap))
    util = module(snap/'process_helper.py', 'common_fu_process_helper')
    helpers = module(snap/'helpers.py', 'common_fu_cost_helpers')
    canonical = module(snap/'canonical.py', 'common_fu_canonical')
    compact = module(snap/'compact.py', 'compact')
    sys.modules['compact'] = compact
    for label, _ in VARIANTS:
        d = out/label/'generated-rtl'
        d.mkdir(parents=True)
        for f in generated[label]:
            shutil.copyfile(f, d/f.name)
            need(sha(d/f.name) == pins[str(f)], 'copied generated RTL')
    snapshots = {str(p): sha(p) for p in out.rglob('*') if p.is_file()}
    save(out/'inputs.json', {'originals': pins, 'snapshots': snapshots})

    tmp = out/'tmp'
    tmp.mkdir()
    env = {**os.environ, 'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC', 'PYTHONDONTWRITEBYTECODE': '1',
           'TMPDIR': str(tmp),
           'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    result = dict(contract=CONTRACT, status='RUNNING', started=util.stamp(), cpu_affinity=[a.cpu], nice=5,
                  budget_seconds=a.budget_seconds, command_limit_seconds=300, jobs=1,
                  top=TOP, boundary='CommonFuCostTop complete production IO, without observation outputs',
                  source_elaboration='new v2 generation from original FU-validated sources; new top not functionally tested',
                  generation_sha256=a.generation_sha256, functional_qualified=False,
                  constraints=dict(period_ns=1.0, uncertainty_ns=0.05, clock_transition_ns=0.05,
                                   input_delay_ns=0.1, output_delay_ns=0.1, input_transition_ns=0.05,
                                   load_fF=5.0, wire_load='5K_hvratio_1_1', abc_delay_ps=1000),
                  tools={n: {'path': p, 'sha256': h} for n, (p, h) in TOOLS.items()},
                  library={'path': str(lib), 'sha256': LIB_SHA}, commands=[], results=[],
                  parent_cost_qualified=False, core_cost_qualified=False, power_measured=False,
                  application_performance_qualified=False, new_elaborations=0, new_simulations=0)
    save(out/'result.json', result)

    def command(d, label, argv):
        remaining = deadline - time.monotonic()
        need(remaining > 1, 'total finite budget exhausted before ' + label)
        rec = dict(label=label, argv=list(map(str, argv)), started=util.stamp(), cpu_affinity=[a.cpu],
                   nice=5, budget_seconds=min(300, remaining), exit_code=None)
        result['commands'].append(rec)
        proc = None
        try:
            with (d/(label+'.log')).open('wb') as log:
                proc = subprocess.Popen(rec['argv'], cwd=d, env=env, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                rec['pid'] = proc.pid
                save(out/'result.json', result)
                rec['exit_code'] = proc.wait(timeout=rec['budget_seconds'])
            need(rec['exit_code'] == 0, label + ' failed')
            need(not util.group_exists(proc.pid), label + ' left a process group')
        finally:
            if proc is not None:
                if util.group_exists(proc.pid):
                    rec['cleanup_complete'] = util.stop_group(proc)
                rec['reaped'] = proc.poll() is not None
                rec['group_absent'] = not util.group_exists(proc.pid)
            rec['finished'] = util.stamp()
            save(out/'result.json', result)
        return (d/(label+'.log')).read_text(errors='replace')

    try:
        areas = helpers.library_areas(lib)
        interfaces = []
        for label, feature in VARIANTS:
            d = out/label
            rtls = [d/'generated-rtl'/n for n in ('VDotElastic.sv', 'VDotProducts.sv', 'VDotReduce.sv', 'CommonFuCostTop.sv')]
            (d/'abc.constr').write_text('set_driving_cell BUF_X1\nset_load 5.0\n')
            ys = [f'read_liberty -lib {lib}', *[f'read_verilog -sv -DSYNTHESIS {p}' for p in rtls],
                  f'hierarchy -check -top {TOP}', 'proc', 'opt', f'synth -top {TOP} -flatten -noabc',
                  f'dfflibmap -liberty {lib}',
                  f'abc -exe {TOOLS["abc"][0]} -liberty {lib} -D 1000 -constr {d/"abc.constr"}',
                  'clean', 'check -assert', f'stat -liberty {lib}',
                  f'write_json {d/"mapped.json"}', f'write_verilog -noattr {d/"mapped.v"}']
            (d/'map.ys').write_text('\n'.join(ys)+'\n')
            log = command(d, 'synthesis', [TOOLS['yosys'][0], '-T', '-s', d/'map.ys'])
            design = json.loads((d/'mapped.json').read_bytes())['modules'][TOP]
            cells = Counter(c['type'] for c in design['cells'].values())
            need(not set(cells)-set(areas), 'unmapped cells')
            area = sum(areas[k]*v for k, v in cells.items())
            reported = re.findall(r'Chip area for module.*?:\s*([0-9.]+)', log)
            need(reported and abs(float(reported[-1])-area) < 0.02, 'area cross-check')
            interface = {n: {'direction': p['direction'], 'width': len(p['bits']), 'offset': p.get('offset', 0)}
                         for n, p in design['ports'].items()}
            interfaces.append(interface)
            need(all(n in interface for n in ('clock', 'reset', 'io_in_ready', 'io_out_ready',
                 'io_out_bits_res_data', 'io_in_bits_perfDebugInfo_renameTime',
                 'io_out_bits_perfDebugInfo_issueTime')), 'retained complete production FU boundary')
            topology = compact.topology(design)
            sta_netlist, reread = d/'mapped.v', design
            representation = 'original_mapped_bytes'
            # This exact syntax failed with the same installed OpenSTA in the
            # preserved independent-prototype experiment. Do not rewrite RTL.
            if re.search(r'(?m)^\s*assign\s*\{', (d/'mapped.v').read_text()):
                sta_netlist = d/'sta-canonical.v'
                by_instance = canonical.emit(design, TOP, sta_netlist)
                save(d/'instance-binding.json', by_instance)
                verify = [f'read_liberty -lib {lib}', f'read_verilog {sta_netlist}',
                          f'hierarchy -check -top {TOP}', 'check -assert', f'write_json {d/"sta-reread.json"}']
                (d/'verify-serialization.ys').write_text('\n'.join(verify)+'\n')
                command(d, 'verify-serialization', [TOOLS['yosys'][0], '-T', '-s', d/'verify-serialization.ys'])
                reread = json.loads((d/'sta-reread.json').read_bytes())['modules'][TOP]
                reread = canonical.bind(reread, design, by_instance)
                need(topology == compact.topology(reread, True), 'canonical connectivity changed')
                need(Counter(c['type'] for c in reread['cells'].values()) == cells, 'canonical cell count changed')
                need(interface == {n: {'direction': p['direction'], 'width': len(p['bits']), 'offset': p.get('offset', 0)}
                                   for n, p in reread['ports'].items()}, 'canonical port boundary changed')
                representation = 'existing_canonical_emitter_graph_verified'
            paths = {'r2r': '-from $q -to $d', 'i2r': '-from $inputs -to $d',
                     'r2o': '-from $q -to $outputs', 'i2o': '-from $inputs -to $outputs',
                     'ready': '-from [get_ports io_out_ready] -to [get_ports io_in_ready]'}
            tcl = ['fconfigure stdout -buffering line', f'read_liberty {lib}',
                   'set_cmd_units -time ns -capacitance fF', 'set_wire_load_mode top',
                   'set_wire_load_model -name 5K_hvratio_1_1', f'read_verilog {sta_netlist}',
                   f'link_design {TOP}', 'set inputs {}',
                   'foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}',
                   'set outputs [all_outputs]', 'create_clock -name core_clk -period 1.0 [get_ports clock]',
                   'set_clock_uncertainty 0.05 [get_clocks core_clk]',
                   'set_clock_transition 0.05 [get_clocks core_clk]',
                   'set_input_delay -max 0.1 -clock core_clk $inputs',
                   'set_output_delay -max 0.1 -clock core_clk $outputs',
                   'set_input_transition 0.05 $inputs', 'set_load 5.0 $outputs',
                   f'check_setup -verbose > {d/"setup-checks.rpt"}',
                   'set q [all_registers -output_pins]', 'set d [all_registers -data_pins]']
            for name, select in paths.items():
                tcl.append(f'report_checks {select} -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {{capacitance slew input_pin net}} -digits 6 -no_line_splits > {d/(name+".rpt")}')
            tcl += ['puts "DOT16_GENERATED_FU_STA_COMPLETE"', 'exit']
            (d/'timing.tcl').write_text('\n'.join(tcl)+'\n')
            log = command(d, 'sta', [TOOLS['sta'][0], '-no_init', '-exit', d/'timing.tcl'])
            need(not re.search(r'(?m)^.*\bError:', log) and 'not found' not in log and
                 log.splitlines().count('DOT16_GENERATED_FU_STA_COMPLETE') == 1, 'complete error-free STA execution')
            parsed = {n: helpers.parse_path((d/(n+'.rpt')).read_text()) for n in paths}
            need(all(p['exists'] for p in parsed.values()), 'all five path classes present')
            constants = helpers.constant_warnings((d/'setup-checks.rpt').read_text(), reread)
            point = dict(feature=feature, generation_sha256=a.generation_sha256, status='COMMON_FU_COST_RECORDED',
                         cell_area=area, cell_count=sum(cells.values()), dff_cells=sum(v for k,v in cells.items() if k.startswith('DFF')),
                         cell_histogram=dict(sorted(cells.items())), timing=parsed, ports=interface,
                         reviewed_constant_endpoints=constants, topology_sha256=topology,
                         mapped_sha256=sha(d/'mapped.v'), mapped_json_sha256=sha(d/'mapped.json'),
                         sta_representation=representation, sta_netlist_sha256=sha(sta_netlist), map_script_sha256=sha(d/'map.ys'),
                         sta_script_sha256=sha(d/'timing.tcl'), nominal_setup_met=all(p['slack_ns'] >= 0 for p in parsed.values()))
            save(d/'result.json', point)
            result['results'].append(point)
            save(out/'result.json', result)
        need(interfaces[0] == interfaces[1], 'same two-point complete production FU interface')
        need(all(sha(p) == h for p,h in {**pins, **snapshots}.items()), 'inputs and snapshots unchanged')
        need(time.monotonic() < deadline, 'total finite budget exhausted during final input checks')
        result.update(status='TWO_COMMON_FU_COSTS_RECORDED', inputs_unchanged=True,
                      generated_fu_cost_recorded=True, same_interface=True,
                      area_delta=result['results'][1]['cell_area']-result['results'][0]['cell_area'])
    except BaseException as e:
        result.update(status='FAILED', error=repr(e))
        raise
    finally:
        result['finished'] = util.stamp()
        result['elapsed_seconds'] = time.monotonic()-started
        save(out/'result.json', result)
    print(json.dumps({k: v for k,v in result.items() if k not in ('commands','results')}, indent=2))
    print(json.dumps({'points': [{k:p[k] for k in ('feature','cell_area','cell_count','dff_cells','timing','nominal_setup_met')}
                                 for p in result['results']]}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'generation', 'output', 'library'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--generation-sha256', required=True)
    p.add_argument('--cpu', type=int, choices=range(4), default=1)
    p.add_argument('--budget-seconds', type=int, default=900)
    main(p.parse_args())
