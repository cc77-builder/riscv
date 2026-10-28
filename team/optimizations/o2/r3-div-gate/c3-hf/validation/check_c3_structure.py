"""C3-HF generated binding and P-only cone check; no EDA or RTL mutation."""
import argparse,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[6]
PARSER=ROOT/'team/optimizations/o2/r3-div-gate/c2/check_generated_cone.py'
spec=importlib.util.spec_from_file_location('c2cone',PARSER)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def need(ok,why):
    if not ok:raise RuntimeError(why)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return re.sub(r'\s+','',s)
def bind(rtl):
    rtl=Path(rtl);trace=mod.Trace(rtl);exu=trace.modules['ExeUnit']
    raw=mod.clean((rtl/'ExeUnit.sv').read_text())
    need(not any('Owner' in x or 'owner' in x for x in exu['regs']),'unexpected owner state')
    result={}
    for label,typ in [('fp','VFDivSqrt'),('int','VIDiv')]:
        units=[(k,x) for k,x in exu['instances'].items() if x['type']==typ]
        need(len(units)==1,'nonunique '+typ);name,unit=units[0]
        gates=[(k,x) for k,x in exu['instances'].items() if x['type']=='ClockGate' and x['ports']['Q']==unit['ports']['clock']]
        need(len(gates)==1,'nonunique gate '+typ);gname,gate=gates[0]
        holds=set(mod.tokens(gate['ports']['E']))&exu['regs']
        need(len(holds)==1,'cannot bind sole hold in actual gate E')
        hold=next(iter(holds));need(hold.startswith('uncer_en_reg'),'wrong hold')
        assignments=re.findall(r'\b'+re.escape(hold)+r'\s*<=\s*(.*?);',raw,re.S)
        data=[s.strip() for s in assignments if norm(s)!="1'h0"]
        need(len(data)==1,'nonunique hold next expression')
        # Fixed firtool form: SET | ~(outfire | cancelled) & old_hold.
        m=re.fullmatch(r'\s*(.*?)\s*\|\s*~\(([^()]*)\)\s*&\s*'+re.escape(hold)+r'\s*',data[0],re.S)
        need(m is not None,'unreviewed hold assignment syntax: '+data[0])
        setnet,clear=m.groups()
        need('elasticDivCancelled' in mod.tokens(clear),'missing shared cancellation')
        ports=unit['ports']
        actualfire=f"({ports['io_in_valid']} & {ports['io_in_ready']})"
        actualoutfire=f"({ports['io_out_valid']} & {ports['io_out_ready']})"
        result[label]=dict(unit=name,gate=gname,hold=hold,set=setnet,clear=clear,
                          fire=actualfire,outfire=actualoutfire,gate_e=gate['ports']['E'],
                          ports=ports,update=data[0])
    need(result['fp']['hold']!=result['int']['hold'],'holds collapsed')
    need(bool(mod.tokens(result['fp']['set'])),'actual FP SET has no signal dependency')
    # Restrict to actual SET, never whole hold.D: release legitimately uses out.ready.
    trace.expr(trace.root,result['fp']['set'])
    need(not trace.forbidden,'FP SET ready dependency: '+repr(trace.forbidden))
    fp_set_nodes=sorted('.'.join(x) for x in trace.visited)
    fp_set_leaves=sorted(trace.leaves)
    need(any('divBusy' in x for x in fp_set_leaves),'P lost actual busy state')
    need(any('reset' in x for x in fp_set_leaves),'P lost reset')
    need(any('io_flush_valid' in x for x in fp_set_leaves),'P lost flush guard')
    need(any('pValid' in x for x in fp_set_leaves) and any('rValid' in x for x in fp_set_leaves),'P lost actual VDot occupancy')
    for label in ['fp','int']:
        # Old clocks must retain actual acceptance, not P.
        gate=trace.gate(result[label]['gate'])
        need(bool(gate['forbidden']),label+' gate unexpectedly lost ready/fire chain')
        result[label]['gate_cone']=gate
    need('elasticDivCancelled' in exu['drivers'],'cancel binding missing')
    return dict(status='C3_HF_GENERATED_HOLD_STRUCTURE_PASS',bindings=result,
                fp_set_nodes=fp_set_nodes,fp_set_leaves=fp_set_leaves,
                fp_set_forbidden=[],source=str(rtl/'ExeUnit.sv'),
                source_sha256=sha(rtl/'ExeUnit.sv'),parser_sha256=sha(PARSER),
                scope='Fixed split SV assignment/instance structure; not general formal equivalence or timing qualification.')
def main():
    a=argparse.ArgumentParser();a.add_argument('--rtl',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args()
    need(not x.output.exists(),'output exists')
    r=bind(x.rtl);x.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
if __name__=='__main__':main()
