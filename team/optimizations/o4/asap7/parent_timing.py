#!/usr/bin/env python3
"""Audit parent timing classes, real ICG enables and dynamic endpoint coverage."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import re

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from timing import parse_path, constant_warnings
from compact import topology
import canonical

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mapping',type=Path,required=True)
    p.add_argument('--environment',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,LD_LIBRARY_PATH=str(a.environment/'tools/usr/lib/x86_64-linux-gnu'),TCL_LIBRARY=str(a.environment/'tools/usr/share/tcltk/tcl8.6'))
    env.pop('LD_PRELOAD',None)
    result={'status':'RUNNING','profiles':{},'scope':'parent setup/coverage under pin-only reference models; no physical signoff'}
    try:
        for platform in ['nangate45','asap7']:
            root=a.mapping/platform
            original=json.loads((root/'mapped.json').read_text())['modules']['CommonParentCostTop']
            design=json.loads((root/'canonical.json').read_text())['modules']['CommonParentCostTop']
            names={'c'+str(i):n for i,n in enumerate(sorted(original['cells']))}
            design=canonical.bind(design,original,names)
            if topology(original)!=topology(design,True):raise ValueError('netlist connectivity mismatch')
            audit=json.loads((root/'gate-audit.json').read_text())
            gates={n:c for n,c in design['cells'].items() if c['type']==audit['cell']}
            if len(gates)!=3:raise ValueError('three ICGs required')
            def register_outputs(cell):
                return [pin for pin,direction in cell['port_directions'].items() if direction=='output']
            # ASAP7's DFFHQN has an inverted physical output; dfflibmap inserts
            # polarity correction. Original named Q bits need not be FF pins.
            # Select physical registers by preserved source provenance instead.
            vdot={n:c for n,c in design['cells'].items() if c['type'].startswith('DFF') and re.search(r'/VDotElastic\.sv:\d+',original['cells'][names[n]]['attributes'].get('src',''))}
            if len(vdot)<100:raise ValueError('VDot registers not identified: '+str(len(vdot)))
            # This adapter only names the equivalent gate type for the existing
            # constant-SE endpoint checker; it never changes the mapped netlist.
            checker=copy.deepcopy(design)
            for n in gates:checker['cells'][n]['type']='CLKGATETST_X1'
            test=design['ports']['testEnable']['bits']
            if any(c['connections'].get('SE')!=test for c in gates.values()):raise ValueError('ICG test pin not directly bound to testEnable')
            result['profiles'][platform]=[]
            for label,period,load in [('nominal',1,5),('period050',.5,5),('period200',2,5),('load001',1,1),('load020',1,20)]:
                dest=a.output/platform/label;dest.mkdir(parents=True)
                cmds=[f'read_liberty {root / "combined.lib"}',f'read_verilog {root / "canonical.v"}','link_design CommonParentCostTop','set_cmd_units -time ns -capacitance fF','set_wire_load_mode top','set_wire_load_model -name rvinno_pin_only',f'create_clock -name clk -period {period} [get_ports clock]','set_clock_uncertainty 0.05 [get_clocks clk]','set_clock_transition 0.05 [get_clocks clk]','set inputs {}','foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}','set outputs [all_outputs]','set_input_delay -max 0.1 -clock clk $inputs','set_output_delay -max 0.1 -clock clk $outputs','set_input_transition 0.05 $inputs',f'set_load {load} $outputs','set_case_analysis 0 [get_ports testEnable]',f'check_setup -verbose > {dest / "setup.rpt"}','set q [all_registers -output_pins]','set d [all_registers -data_pins]', 'set vq [get_pins {'+' '.join(n+'/'+pin for n,c in vdot.items() for pin in register_outputs(c))+'}]','set vd [get_pins {'+' '.join(n+'/D' for n in vdot)+'}]','set ge [get_pins {'+' '.join(n+'/'+audit['enable_pin'] for n in gates)+'}]']
                paths={'r2r':'-from $q -to $d','i2r':'-from $inputs -to $d','r2o':'-from $q -to $outputs','i2o':'-from $inputs -to $outputs','ready':'-from [get_ports io_out_ready] -to [get_ports io_in_ready]','vdot_r2r':'-from $vq -to $vd','vdot_i2r':'-from $inputs -to $vd','vdot_r2o':'-from $vq -to $outputs','gate_enable':'-to $ge'}
                # No unverified reconvergence credit for ideal clocks across
                # ICG library arcs in this old OpenSTA reference flow.
                cmds.insert(0, 'sta::set_crpr_enabled false')
                cmds.insert(1, 'if {[sta::crpr_enabled]} {error "CRPR must be disabled"}')
                cmds.insert(2, 'puts "CRPR_DISABLED_CONFIRMED"')
                for name,selectors in paths.items():cmds.append(f'report_checks {selectors} -path_delay max -group_count 1 -endpoint_count 1 -digits 6 > {dest / (name+".rpt")}')
                cmds+=['puts "PARENT_STA_COMPLETE"','exit']
                (dest/'timing.tcl').write_text('\n'.join(cmds)+'\n')
                with (dest/'sta.log').open('w') as log:subprocess.run([str(a.environment/'tools/usr/bin/sta'),'-no_init','-exit',str(dest/'timing.tcl')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
                log=(dest/'sta.log').read_text()
                if re.search(r'(?im)^(error|warning)',log) or log.count('PARENT_STA_COMPLETE')!=1 or log.count('CRPR_DISABLED_CONFIRMED')!=1:raise ValueError('STA diagnostics: '+log[-2000:])
                parsed={n:parse_path((dest/(n+'.rpt')).read_text()) for n in paths}
                if not all(v['exists'] for v in parsed.values()):raise ValueError('missing required path')
                allowed=constant_warnings((dest/'setup.rpt').read_text(),checker,['testEnable'])
                result['profiles'][platform].append({'profile':label,'period_ns':period,'load_ff':load,'crpr_enabled':False,'paths':parsed,'allowed_constant_endpoints':allowed,'vdot_registers':len(vdot),'gates':len(gates)})
        result['status']='PARENT_DUAL_LIBRARY_SETUP_COVERAGE_PASS'
    except BaseException as error:
        result.update(status='FAILED',error=repr(error));raise
    finally:(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])

if __name__=='__main__':main()
