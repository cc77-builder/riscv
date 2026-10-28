#!/usr/bin/env python3
"""Exercise library reading, FF/logic mapping and STA; not a VDot benchmark."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--environment', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--rtl', type=Path, help='Optional production cost RTL directory; never a test top')
    p.add_argument('--top', default='CommonFuCostTop', choices=['CommonFuCostTop','CommonParentCostTop'])
    a = p.parse_args()
    root = a.environment.resolve(); out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, LD_LIBRARY_PATH=str(root / 'tools/usr/lib/x86_64-linux-gnu'))
    env.pop('LD_PRELOAD', None)
    env['TCL_LIBRARY'] = str(root / 'tools/usr/share/tcltk/tcl8.6')
    exe = root / 'tools/usr/bin'
    (out / 'probe.v').write_text('module probe(input clock, input [7:0] a,b, output reg [7:0] q); always @(posedge clock) q <= a+b; endmodule\n')
    top = a.top if a.rtl else 'probe'
    report = {'status': 'RUNNING', 'synthetic_only': not bool(a.rtl), 'project_PPA_qualified': False, 'platforms': {}}
    try:
        for platform in ['nangate45', 'asap7']:
            run = out / platform; run.mkdir()
            libs = [root / 'libraries/NangateOpenCellLibrary_typical.lib'] if platform == 'nangate45' else sorted((root / 'libraries/asap7/lib/NLDM').glob('*.lib'))
            # ABC needs one library: preserve one header and all original cell blocks.
            texts = []
            for index, f in enumerate(libs):
                text = f.read_text()
                names = re.findall(r'\b\w*template\s*\(\s*(\w+)\s*\)', text)
                for name in set(names):
                    text = re.sub(r'\b' + re.escape(name) + r'\b', 'lib' + str(index) + '_' + name, text)
                texts.append(text)
            combined = texts[0]
            for s in texts[1:]:
                first = re.search(r'\bcell\s*\(', s)
                if first is None: raise ValueError('missing cells')
                templates = []
                for match in re.finditer(r'\b\w*template\s*\([^)]*\)\s*\{', s[:first.start()]):
                    end = match.end(); depth = 1
                    while depth:
                        depth += (s[end] == '{') - (s[end] == '}'); end += 1
                    templates.append(s[match.start():end])
                combined = combined[:combined.rfind('}')] + '\n'.join(templates) + s[first.start():s.rfind('}')] + '\n}\n'
            # Use the same explicit pin-load-only interconnect assumption in both libraries.
            combined = re.sub(r'\bdefault_wire_load\s*:[^;]*;', '', combined)
            combined = combined[:combined.rfind('}')] + '\nwire_load (rvinno_pin_only) { resistance : 0; capacitance : 0; area : 0; slope : 0; fanout_length (1, 0); fanout_length (1000, 0); }\ndefault_wire_load : "rvinno_pin_only";\n}\n'
            lib = run / 'combined.lib'; lib.write_text(combined)
            driver = 'BUF_X1' if platform == 'nangate45' else 'BUFx2_ASAP7_75t_R'
            (run / 'abc.constr').write_text('set_driving_cell '+driver+'\nset_load 5\n')
            rtl = sorted(a.rtl.resolve().glob('*.sv')) if a.rtl else [out/'probe.v']
            if not rtl: raise ValueError('empty RTL')
            report['rtl_sha256'] = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in rtl}
            gate = None
            if top == 'CommonParentCostTop':
                from gate_mapping import mapping
                originals = [f for f in rtl if f.name == 'ClockGate.sv']
                if len(originals)!=1: raise ValueError('expected one generated ClockGate')
                gate = mapping(platform, combined, originals[0].read_text(), run/'ClockGate.map.v')
                (run/'gate-audit.json').write_text(json.dumps(gate,indent=2)+'\n')
                rtl = [f for f in rtl if f not in originals]+[run/'ClockGate.map.v']
            script = [f'read_liberty -lib {lib}', *[f'read_verilog -sv -DSYNTHESIS {f}' for f in rtl], f'synth -top {top} -flatten -noabc', f'dfflibmap -liberty {lib}', f'abc -exe {exe / "berkeley-abc"} -liberty {lib} -D 1000 -constr {run / "abc.constr"}', 'clean', 'check -assert', f'write_json {run / "mapped.json"}', f'write_verilog -noattr -noexpr {run / "mapped.v"}']
            (run / 'map.ys').write_text('\n'.join(script)+'\n')
            with (run / 'map.log').open('w') as log:
                subprocess.run([str(exe/'yosys'), '-s', str(run/'map.ys')], stdout=log, stderr=subprocess.STDOUT, env=env, check=True, timeout=1800 if a.rtl else 120)
            design = json.loads((run/'mapped.json').read_text())['modules'][top]
            if gate and sum(c['type']==gate['cell'] for c in design['cells'].values()) != 3:
                raise ValueError('parent must preserve three real clock gates')
            types = {c['type'] for c in design['cells'].values()}
            known = set(re.findall(r'\bcell\s*\(\s*([^\s)]+)\s*\)', combined))
            if not types <= known: raise ValueError('unmapped cells: '+str(types-known))
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            import canonical
            binding = canonical.emit(design, top, run/'canonical.v')
            from compact import topology
            (run/'import.ys').write_text(f'read_liberty -lib {lib}\nread_verilog {run / "canonical.v"}\nhierarchy -check -top {top}\nwrite_json {run / "canonical.json"}\n')
            with (run/'import.log').open('w') as log:
                subprocess.run([str(exe/'yosys'), '-s', str(run/'import.ys')], stdout=log, stderr=subprocess.STDOUT, env=env, check=True, timeout=120)
            reread = json.loads((run/'canonical.json').read_text())['modules'][top]
            reread = canonical.bind(reread, design, binding)
            if topology(design) != topology(reread, True): raise ValueError('canonical topology changed')
            commands = [f'read_liberty {lib}', f'read_verilog {run / "canonical.v"}', f'link_design {top}', 'set_cmd_units -time ns -capacitance fF', 'set_wire_load_mode top', 'set_wire_load_model -name rvinno_pin_only', 'create_clock -name clk -period 1 [get_ports clock]', 'set_clock_uncertainty 0.05 [get_clocks clk]', 'set_clock_transition 0.05 [get_clocks clk]', 'set_input_delay 0.1 -clock clk [get_ports {'+' '.join(n for n,p in design['ports'].items() if p['direction']=='input' and n!='clock')+'}]', 'set_output_delay 0.1 -clock clk [all_outputs]', 'set_input_transition 0.05 [all_inputs]', 'set_load 5 [all_outputs]', 'report_checks -path_delay max -digits 6', 'exit']
            if gate:
                commands.insert(-2, 'set_case_analysis 0 [get_ports testEnable]')
            (run/'check.tcl').write_text('\n'.join(commands)+'\n')
            with (run/'sta.log').open('w') as log:
                subprocess.run([str(exe/'sta'), '-exit', str(run/'check.tcl')], stdout=log, stderr=subprocess.STDOUT, env=env, check=True, timeout=120)
            text = (run/'sta.log').read_text()
            if re.search(r'(?im)^(error|warning)', text) or 'slack' not in text: raise ValueError('STA did not produce a warning-free timing path')
            areas = dict((n,float(v)) for n,v in re.findall(r'cell\s*\(\s*(\w+)\s*\)\s*\{.*?\barea\s*:\s*([0-9.eE+-]+)',combined,re.S))
            report['platforms'][platform] = {'status':'PASS', 'mapped_cells':len(design['cells']), 'library_area_sum_raw':sum(areas[c['type']] for c in design['cells'].values()), 'slack_ns':float(re.findall(r'([-0-9.]+)\s+slack',text)[-1]), 'worst_reported_arrival_ns':float(re.findall(r'([0-9.]+)\s+data arrival time',text)[0]), 'library_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in libs}, 'mapped_types':sorted(types)}
        report['status'] = ('DUAL_LIBRARY_PARENT_PRELIMINARY_STA_PASS' if top=='CommonParentCostTop' else 'DUAL_LIBRARY_FU_PRELIMINARY_STA_PASS') if a.rtl else 'DUAL_LIBRARY_SYNTHESIS_STA_SMOKE_PASS'
    except BaseException as error:
        report.update(status='FAILED', error=repr(error))
        raise
    finally:
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__ == '__main__': main()
