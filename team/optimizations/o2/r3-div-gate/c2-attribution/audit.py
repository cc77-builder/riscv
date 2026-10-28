"""Audit the read-only attribution files; never starts EDA or writes RTL."""
import argparse,ast,collections,datetime,hashlib,json,re,subprocess
from pathlib import Path
R=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
C=Path('/home/riscv/riscv-lab/o2-c1-owner-20261025/repo')
W=Path('/home/riscv/riscv-lab/o2-c2-attribution-20261025')
M=R/'team/optimizations/o2/r3-div-gate/c2-attribution'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,s):
    if not ok:raise ValueError(s)
def read(p):return json.loads(p.read_text())
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    need(not a.output.exists(),'new receipt required')
    pins={}
    for name,key in [('graph-01/inputs.json',None),('fixed-sta-review.json','inputs'),
                     ('review-side-paths/inputs.json',None),('review-semantics/predicate-audit.json','inputs'),
                     ('review-semantics/supplement-inputs.json',None)]:
        obj=read(W/name);obj=obj[key] if key else obj
        for path,h in obj.items():
            need(path not in pins or pins[path]==h,'conflicting input identity')
            pins[path]=h
    for p,h in pins.items():need(sha(Path(p))==h,'changed input '+p)
    seals={}
    for rel,h in [
      ('evidence/20261025-performance-cost/manifest.json','9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77'),
      ('c1/evidence/20261025-screen/manifest.json','ced265304d08b2ee3c7eb9a894eb009869bb494adb7c48e1ff72493ce4cb252e')]:
        p=R/'team/optimizations/o2/r3-div-gate'/rel;need(sha(p)==h,'old seal changed');seals[str(p)]=h
    repos=[]
    src=Path('src/main/scala/xiangshan/backend/exu/ExeUnit.scala')
    for root,head,h in [
      (R,'0f12df675378556670afd0dd2153f47fcb330610','fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa'),
      (C,'3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66','ac73f507ee2eaebf5c7c4f515a136e4eb256ac1aab4e2224895965c497513be0')]:
        need(git(root,'rev-parse','HEAD')==head,'HEAD moved')
        need(sha(root/src)==h,'ExeUnit changed')
        need(not git(root,'diff','HEAD','--','src'),'production source dirty')
        repos.append(dict(root=str(root),head=head,exeunit_sha256=h,tracked_src_diff_empty=True))
    fixed=read(W/'fixed-sta-review.json');arrivals={};missing=[]
    state=read(W/'fixed-sta-01/state.json')
    need(len(state['steps'])==2 and all(x['exit_code']==0 for x in state['steps']),'STA scope or error')
    need(read(W/'fixed-sta-command.json')['exit_code']==1,'retain parser failure')
    for version in ['before','after']:
        arrivals[version]={}
        for path in sorted((W/'fixed-sta-01'/version).glob('*.rpt')):
            t=path.read_text();expected=fixed['paths'][version][path.stem]
            if t.strip()=='No paths found.':
                need(not expected['exists'],'unexpected absent result');missing.append([version,path.stem]);continue
            vals=re.findall(r'(?m)^\s+(-?\d+\.\d+)\s+data arrival time\s*$',t)
            need(len(vals)==2 and abs(float(vals[0])+float(vals[1]))<1e-9,'arrival raw format')
            v=float(vals[0]);need(v==expected['arrival_ns'],'arrival differs')
            slack=re.findall(r'(?m)^\s+(-?\d+\.\d+)\s+slack \((?:MET|VIOLATED)\)\s*$',t)
            need(len(slack)==1 and float(slack[0])==expected['slack_ns'],'slack differs')
            arrivals[version][path.stem]=v
    need(missing==[['after','icg_from_hold_or_owner']],'no-path count')
    need(sum(map(len,arrivals.values()))==19,'valid count')
    target={
      'before':{'icg_all':1.128021,'vdot_lane4':1.356106,'vdot_lane6':1.355025,'ready_fixed':.247821},
      'after':{'icg_all':1.727299,'vdot_lane4':1.401305,'vdot_lane6':1.402385,'ready_fixed':.266115}}
    for ver,row in target.items():
        for k,v in row.items():need(arrivals[ver][k]==v,'reported key result')
    # Verify the owner QN path structurally, without an additional STA process.
    root=C.parent
    binding=read(root/'parent-sta-01/instance-binding.json')
    mapping=read(root/'parent-map-01/mapped.json')['modules']['CommonParentCostTop']
    cells=mapping['cells'];reverse={v:k for k,v in binding.items()}
    owner=cells[binding['c192128']];inv=cells[binding['c177229']]
    need(owner['connections']['QN']==inv['connections']['A'],'QN inverter link')
    sinks=collections.defaultdict(list)
    for name,c in cells.items():
        for p,direction in c['port_directions'].items():
            if direction=='input':
                for bit in c['connections'][p]:sinks[bit].append((name,p))
    start=owner['connections']['QN'][0];goal=mapping['netnames']['dut.ClockGate_1.E']['bits'][0]
    queue=collections.deque([(start,[])]);seen=set();found=None
    while queue:
        bit,trace=queue.popleft()
        if bit==goal:found=trace;break
        if bit in seen:continue
        seen.add(bit)
        for name,pin in sinks[bit]:
            cell=cells[name]
            if cell['type'].startswith(('DFF','DFFE','DLH','DLL','ClockGate')):continue
            for port,direction in cell['port_directions'].items():
                if direction=='output':
                    for b in cell['connections'][port]:
                        queue.append((b,trace+[dict(cell=reverse[name],type=cell['type'],input=pin,output=port)]))
    need(found is not None,'owner QN to integer E missing')
    trees={}
    for version,cell,nt,nmux,nbuf,depth in [('before','c103',697,675,77,5),('after','c100',563,524,62,16)]:
        x=read(W/'graph-01'/f'{version}.json')
        stage=next(s for s in x['path_stages'] if s['cell']==cell);t=stage['buffer_tree']
        nm=sum(v['pin']=='S' and v['type'].startswith('MUX2') for v in t['terminals'])
        need((t['terminal_count'],nm,t['buffer_count'],t['max_depth'])==(nt,nmux,nbuf,depth),'tree metrics')
        trees[version]=dict(root=cell,terminals=nt,mux_selects=nm,buffers=nbuf,max_depth=depth)
    sem=read(W/'review-semantics/predicate-audit.json')
    need(sem['trace']['cycles']==35075 and sem['trace']['idle_nonreset_samples']==17666,'trace counts')
    need(sem['trace']['idle_nonreset_notready']==0 and sem['trace']['naive_valid_gate_extra']==5321,'trace conclusion')
    need(sem['truth_table']['total']==6144 and sem['truth_table']['invariant_mismatches']==0,'truth-table')
    syntax=[]
    for p in list(M.glob('*.py'))+list(W.glob('review-*/*.py')):
        ast.parse(p.read_text(),filename=str(p));syntax.append(str(p))
    manifest=read(M/'evidence/manifest.json')
    for ent in manifest['files']:
        p=M/'evidence'/ent['path']
        need(p.stat().st_size==ent['bytes'] and sha(p)==ent['sha256'],'archive payload '+ent['path'])
        need(sha(W/ent['path'])==ent['sha256'],'archive source '+ent['path'])
    code=subprocess.run(['git','-C',str(R),'diff','--check'],capture_output=True,text=True)
    need(code.returncode==0,'diff check '+code.stdout+code.stderr)
    a.output.parent.mkdir(exist_ok=True)
    result=dict(status='C2_READONLY_ATTRIBUTION_AUDIT_PASS',time=datetime.datetime.now().astimezone().isoformat(),
      input_count=len(pins),inputs=pins,old_seals=seals,repos=repos,sta_processes=2,valid_reports=19,
      missing_queries=missing,raw_arrivals_ns=arrivals,owner_qn_to_integer_icg_path=found,graph_metrics=trees,
      semantic_trace_projection=sem['trace'],truth_table=sem['truth_table'],syntax_checked=syntax,
      archive_files=len(manifest['files']),archive_bytes=sum(x['bytes'] for x in manifest['files']),
      archive_manifest_sha256=sha(M/'evidence/manifest.json'),
      tracked_diff_check='PASS',new_rtl=False,new_synthesis=False,new_emu=False,new_nemu=False,
      c2_g0_proved=False,c2_implemented=False,github_write=False,
      decision='Continue only with C2-G0 invariant proof; no RTL implementation authorized by this attribution result.')
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','input_count','sta_processes','valid_reports','missing_queries','owner_qn_to_integer_icg_path','archive_files','archive_bytes']},indent=2))
if __name__=='__main__':main()
