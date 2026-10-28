#!/usr/bin/env python3
"""Independent structural and timing-completeness checks on the parent pair."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--mapping',type=Path,required=True)
p.add_argument('--timing',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
timing=json.loads((a.timing/'result.json').read_text())
if timing['status']!='PARENT_DUAL_LIBRARY_SETUP_COVERAGE_PASS':raise ValueError('timing coverage incomplete')
report={'status':'PARENT_PAIR_REVIEW_PASS','platforms':{},'full_physical_signoff':False}
ports=None
for name in ['nangate45','asap7']:
    root=a.mapping/name
    module=json.loads((root/'mapped.json').read_text())['modules']['CommonParentCostTop']
    interface={n:(v['direction'],len(v['bits'])) for n,v in module['ports'].items()}
    if ports is None:ports=interface
    if ports!=interface:raise ValueError('cross-platform interface mismatch')
    gate=json.loads((root/'gate-audit.json').read_text())
    cells=module['cells']
    gates={n:c for n,c in cells.items() if c['type']==gate['cell']}
    if len(gates)!=3 or len(gate['transitions'])!=16:raise ValueError('missing gate coverage')
    if any(c['connections'][gate['clock_pin']]!=module['ports']['clock']['bits'] or c['connections']['SE']!=module['ports']['testEnable']['bits'] for c in gates.values()):raise ValueError('gate clock/test connectivity mismatch')
    flops={n:c for n,c in cells.items() if c['type'].startswith('DFF')}
    clock='CK' if name=='nangate45' else 'CLK'
    fanout={n:sum(c['connections'].get(clock)==g['connections'][gate['output_pin']] for c in flops.values()) for n,g in gates.items()}
    if not all(v>0 for v in fanout.values()):raise ValueError('gate bypassed or disconnected')
    vdot={n:c for n,c in flops.items() if '/VDotElastic.sv:' in c['attributes'].get('src','')}
    clocks={tuple(c['connections'][clock]) for c in vdot.values()}
    if len(vdot)!=1352 or len(clocks)!=1 or not clocks <= {tuple(c['connections'][gate['output_pin']]) for c in gates.values()}:raise ValueError('VDot source/clock coverage mismatch')
    profiles=timing['profiles'][name]
    if {r['profile'] for r in profiles}!={'nominal','period050','period200','load001','load020'} or len(profiles)!=5:raise ValueError('missing or duplicate timing profile')
    for r in profiles:
        if r['gates']!=3 or r['vdot_registers']!=len(vdot) or r.get('crpr_enabled') is not False or len(r['paths'])!=9 or not all(x['exists'] for x in r['paths'].values()):raise ValueError('incomplete path/clock checks or unqualified reconvergence credit')
    report['platforms'][name]={'flops':len(flops),'vdot_registers':len(vdot),'gate_fanout_flops':fanout,'timing_paths':45,'ports':len(interface),'netlist_sha256':hashlib.sha256((root/'canonical.v').read_bytes()).hexdigest()}
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
