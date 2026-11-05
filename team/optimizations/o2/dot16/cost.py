"""Comparable pre-layout cost of the three independent arithmetic prototypes.

Reuses the project's area/report parsers and its Nangate45 nominal constraints.
This boundary has simplified control and external kill decisions; no result is a
production FU/parent/core PPA result, clock-frequency commitment, or power value.
"""
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
from types import SimpleNamespace
import json
import os
import re
import shutil
import subprocess
import sys

LIB_SHA = '8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1'
UPSTREAM_PARSER_FILES = {
    'team/optimizations/o4/synthesize.py': '3c91dd6cb6b196611e6a1227ea431234a20266b847ea75ac98da7633b0c80aa7',
    'team/optimizations/o4/timing.py': 'e7eae15000ad8df05ac93dba150ebc55ddb46ed1a2db0f996a8c519abe543917',
}
HELPER_SHA = 'bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def require(ok, text):
    if not ok:
        raise ValueError(text)


def simple_output_assignments(text, design):
    """Legalize the one known sign-extension alias for old OpenSTA syntax.

    This is a netlist representation change, not a circuit edit. The caller
    additionally re-reads both files with Yosys and requires the complete module
    graph to be identical after removal of source-location attributes.
    """
    lines = re.findall(r'(?m)^[ \t]*assign \{[^\n]*;[ \t]*$', text)
    if not lines:
        return text, False
    port = design['ports']['io_result']
    bits = port['bits']
    require(port['direction'] == 'output' and port.get('offset', 0) == 0 and len(bits) == 128,
            'known architectural output port')
    require(bits[32:] == ['0'] * 96 and isinstance(bits[31], int)
            and all(b == bits[31] for b in bits[19:32]), 'mapped constant/sign-extension identity')
    rhs = "96'h000000000000000000000000, " + ', '.join(['io_result[31]'] * 12)
    old = '  assign { io_result[127:32], io_result[30:19] } = { ' + rhs + ' };'
    require(lines == [old], 'only the reviewed concatenated output alias is normalized')
    new = "  assign io_result[127:32] = 96'h000000000000000000000000;\n"
    new += '  assign io_result[30:19] = { ' + ', '.join(['io_result[31]'] * 12) + ' };'
    return text.replace(old, new, 1), True


def without_source_attributes(value):
    if isinstance(value, dict):
        return {k: without_source_attributes(v) for k, v in value.items() if k != 'attributes'}
    if isinstance(value, list):
        return [without_source_attributes(v) for v in value]
    return value


def main(repo, prototype, control, output, library, jobs):
    require(jobs in (1, 2), 'at most two CPUs')
    require(not output.exists() and not output.is_relative_to(repo), 'fresh external output')
    require(sha(library) == LIB_SHA, 'fixed Nangate45 typical library')
    helper_path = Path(__file__).resolve().with_name('cost_helpers.py')
    helper_raw = helper_path.read_bytes()
    require(hashlib.sha256(helper_raw).hexdigest() == HELPER_SHA, 'frozen pure report helpers')
    namespace = {'__name__': 'dot16_cost_helpers'}
    exec(compile(helper_raw, str(helper_path), 'exec'), namespace)
    helpers = SimpleNamespace(**namespace)
    tools = {name: shutil.which(name) for name in ('yosys', 'berkeley-abc', 'sta', 'taskset')}
    require(all(tools.values()), 'mapping/STA tools must exist in the supplied environment')
    cpus = sorted(os.sched_getaffinity(0))[:jobs]
    require(bool(cpus), 'CPU affinity')
    os.sched_setaffinity(0, cpus)
    output.mkdir(parents=True)
    (output / 'cost_helpers.py').write_bytes(helper_raw)
    shutil.copyfile(Path(__file__).resolve(), output / 'cost.py')
    env = os.environ.copy()
    env.update(LANG='C', LC_ALL='C', TZ='UTC', PYTHONDONTWRITEBYTECODE='1')
    common = dict(started=now(), library_sha256=LIB_SHA,
                  helpers={str(helper_path): HELPER_SHA}, upstream_parser_files=UPSTREAM_PARSER_FILES,
                  cost_source_sha256=sha(output / 'cost.py'),
                  tools={name: dict(path=path, sha256=sha(Path(path))) for name, path in tools.items()},
                  constraints=dict(period_ns=1.0, uncertainty_ns=0.05, clock_transition_ns=0.05,
                                   input_delay_ns=0.1, output_delay_ns=0.1, input_transition_ns=0.05,
                                   load_fF=5.0, wire_load='5K_hvratio_1_1', abc_delay_ps=1000),
                  production_fu=False, parent=False, core=False, power_measured=False)
    (output / 'manifest.json').write_text(json.dumps(common, indent=2) + '\n')
    areas = helpers.library_areas(library)

    def one(variant, cpu):
        before = json.loads((prototype / variant / 'result.json').read_text())
        checked = json.loads((control / variant / 'result.json').read_text())
        require(before['status'] == 'INDEPENDENT_DOT16_PROTOTYPE_PASS', 'elaborated prototype')
        require(before['variant'] == checked['variant'] == variant, 'tested variant identity')
        if checked['status'] == 'INDEPENDENT_DOT16_PROTOTYPE_PASS':
            checker_pins = [h for p, h in checked['source_files'].items() if p.endswith('/prototype_test.cpp')]
            require(checker_pins == ['d8b7de85f73c04f89f3bcc945e098aac51e7a7b834c1f6c7053df566272f976e'],
                    'directed ready/flush checker identity')
            summary = checked.get('test_summary', '')
            for field in ('ready_kill_r', 'redirect_responses'):
                count = re.findall(r'\b' + field + r'=(\d+)', summary)
                require(len(count) == 1 and int(count[0]) >= 2, 'control edge coverage ' + field)
        else:
            require(checked['status'] == 'PROTOTYPE_READY_FLUSH_CHECKER_PASS', 'control edge check')
        rtl = prototype / variant / 'rtl/Dot16Prototype.sv'
        require(sha(rtl) == before['rtl_sha256'] == checked['rtl_sha256'], 'same tested RTL')
        d = output / variant
        d.mkdir()
        result = dict(variant=variant, status='RUNNING', started=now(), cpu=cpu,
                      rtl_sha256=sha(rtl), prototype_result_sha256=sha(prototype / variant / 'result.json'),
                      control_result_sha256=sha(control / variant / 'result.json'), commands=[])

        def command(args, label):
            args = [tools['taskset'], '-c', str(cpu)] + [str(a) for a in args]
            start = now()
            with (d / (label + '.log')).open('wb') as log:
                rc = subprocess.run(args, env=env, cwd=d, stdout=log, stderr=subprocess.STDOUT, timeout=300).returncode
            result['commands'].append(dict(args=args, label=label, start=start, finish=now(), exit=rc))
            require(rc == 0, label + ' failed')
            return (d / (label + '.log')).read_text(errors='replace')

        try:
            shutil.copyfile(rtl, d / 'input.sv')
            (d / 'abc.constr').write_text('set_driving_cell BUF_X1\nset_load 5.0\n')
            ys = [f'read_liberty -lib {library}', f'read_verilog -sv -DSYNTHESIS {d / "input.sv"}',
                  'hierarchy -check -top Dot16Prototype', 'proc', 'opt',
                  f'synth -top Dot16Prototype -flatten -noabc', f'dfflibmap -liberty {library}',
                  f'abc -exe {tools["berkeley-abc"]} -liberty {library} -D 1000 -constr {d / "abc.constr"}',
                  'clean', 'check -assert', f'stat -liberty {library}',
                  f'write_json {d / "mapped.json"}', f'write_verilog -noattr {d / "mapped.v"}']
            (d / 'map.ys').write_text('\n'.join(ys) + '\n')
            log = command([tools['yosys'], '-T', '-s', d / 'map.ys'], 'synthesis')
            design = json.loads((d / 'mapped.json').read_text())['modules']['Dot16Prototype']
            cells = Counter(c['type'] for c in design['cells'].values())
            require(not set(cells) - set(areas), 'unmapped cell')
            area = sum(areas[k] * v for k, v in cells.items())
            reported = re.findall(r'Chip area for module.*?:\s*([0-9.]+)', log)
            require(reported and abs(float(reported[-1]) - area) < 0.02, 'area recomputation mismatch')
            normalized, changed = simple_output_assignments((d / 'mapped.v').read_text(), design)
            (d / 'sta-readable.v').write_text(normalized)
            if changed:
                reread = []
                for name in ('mapped', 'sta-readable'):
                    reread += ['design -reset', f'read_liberty -lib {library}',
                               f'read_verilog {d / (name + ".v")}',
                               'hierarchy -check -top Dot16Prototype', 'check -assert',
                               f'write_json {d / (name + "-reread.json")}']
                (d / 'verify-representation.ys').write_text('\n'.join(reread) + '\n')
                command([tools['yosys'], '-T', '-s', d / 'verify-representation.ys'], 'verify-representation')
                graphs = [without_source_attributes(json.loads((d / (name + '-reread.json')).read_text())['modules']['Dot16Prototype'])
                          for name in ('mapped', 'sta-readable')]
                require(graphs[0] == graphs[1], 'normalized module graph differs from original mapped circuit')
                graph_sha = hashlib.sha256(json.dumps(graphs[0], sort_keys=True).encode()).hexdigest()
            else:
                require(sha(d / 'mapped.v') == sha(d / 'sta-readable.v'), 'unchanged netlist byte identity')
                graph_sha = None
            result['sta_representation'] = dict(changed=changed, module_graph_equal=True,
                                               verified_graph_sha256=graph_sha, sta_netlist_sha256=sha(d / 'sta-readable.v'))
            paths = {'r2r': '-from $q -to $d', 'i2r': '-from $inputs -to $d',
                     'r2o': '-from $q -to $outputs', 'i2o': '-from $inputs -to $outputs',
                     'ready': '-from [get_ports io_out_ready] -to [get_ports io_in_ready]'}
            tcl = ['fconfigure stdout -buffering line', f'read_liberty {library}',
                   'set_cmd_units -time ns -capacitance fF', 'set_wire_load_mode top',
                   'set_wire_load_model -name 5K_hvratio_1_1', f'read_verilog {d / "sta-readable.v"}',
                   'link_design Dot16Prototype', 'set inputs {}',
                   'foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}',
                   'set outputs [all_outputs]', 'create_clock -name core_clk -period 1.0 [get_ports clock]',
                   'set_clock_uncertainty 0.05 [get_clocks core_clk]',
                   'set_clock_transition 0.05 [get_clocks core_clk]',
                   'set_input_delay -max 0.1 -clock core_clk $inputs',
                   'set_output_delay -max 0.1 -clock core_clk $outputs',
                   'set_input_transition 0.05 $inputs', 'set_load 5.0 $outputs',
                   f'check_setup -verbose > {d / "setup-checks.rpt"}',
                   'set q [all_registers -output_pins]', 'set d [all_registers -data_pins]']
            for name, select in paths.items():
                tcl.append(f'report_checks {select} -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {{capacitance slew input_pin net}} -digits 6 -no_line_splits > {d / (name + ".rpt")}')
            tcl += ['puts "DOT16_STA_COMPLETE"', 'exit']
            (d / 'timing.tcl').write_text('\n'.join(tcl) + '\n')
            sta = command([tools['sta'], '-no_init', '-exit', d / 'timing.tcl'], 'sta')
            require(not re.search(r'(?m)^.*\bError:', sta) and sta.splitlines().count('DOT16_STA_COMPLETE') == 1,
                    'STA error or incomplete Tcl execution')
            path_data = {name: helpers.parse_path((d / (name + '.rpt')).read_text()) for name in paths}
            require(all(p['exists'] for p in path_data.values()), 'required timing path absent')
            constants = helpers.constant_warnings((d / 'setup-checks.rpt').read_text(), design)
            result.update(status='INDEPENDENT_PROTOTYPE_COST_RECORDED', cell_count=sum(cells.values()),
                          cell_area=area, dff_cells=sum(v for k, v in cells.items() if k.startswith('DFF')),
                          cells=dict(sorted(cells.items())), timing=path_data, allowed_constant_endpoints=constants,
                          mapped_sha256=sha(d / 'mapped.v'), map_script_sha256=sha(d / 'map.ys'),
                          sta_script_sha256=sha(d / 'timing.tcl'))
        except BaseException as error:
            result.update(status='FAILED', error=repr(error))
            raise
        finally:
            result['finished'] = now()
            (d / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        return result

    variants = ['baseline8', 'direct16', 'split16']
    # Each slot owns one CPU. A slot processes its list serially, so the third
    # design cannot collide with an occupied CPU or exceed the two-CPU budget.
    def slot(index):
        return [one(v, cpus[index]) for v in variants[index::len(cpus)]]
    with ThreadPoolExecutor(max_workers=len(cpus)) as pool:
        futures = [pool.submit(slot, i) for i in range(len(cpus))]
        results = [result for future in futures for result in future.result()]
    require(sha(helper_path) == HELPER_SHA and sha(library) == LIB_SHA and sha(Path(__file__).resolve()) == common['cost_source_sha256'],
            'cost inputs changed')
    for name, tool in common['tools'].items():
        require(sha(Path(tool['path'])) == tool['sha256'], 'cost tool changed ' + name)
    summary = dict(common, finished=now(), status='THREE_INDEPENDENT_PROTOTYPE_COSTS_RECORDED', results=results)
    (output / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({v['variant']: dict(area=v['cell_area'], dff=v['dff_cells'], timing=v['timing']) for v in results}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--prototype', type=Path, required=True)
    p.add_argument('--control', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--jobs', type=int, default=2)
    a = p.parse_args()
    main(a.repo.resolve(), a.prototype.resolve(), a.control.resolve(), a.output.resolve(), a.library.resolve(), a.jobs)
