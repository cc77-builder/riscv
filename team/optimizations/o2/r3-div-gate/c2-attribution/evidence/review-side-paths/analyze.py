"""Read-only ready/VDot side-path attribution on frozen existing maps/reports."""
from pathlib import Path
import collections,datetime,hashlib,importlib.util,json,re,subprocess
ROOT=Path('/home/riscv/riscv-lab')
REPO=ROOT/'zjhwork2-review-20261018/repo'
OUT=ROOT/'o2-c2-attribution-20261025/review-side-paths'
HELPER=REPO/'team/optimizations/o2/r3-div-gate/timing-review/review.py'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('helper',HELPER); h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def leaf_labels(d,bit,kind):
    names=sorted(d.names.get(bit,[]))
    if not names and bit in d.drivers:
        cname,pin=d.drivers[bit]
        cell=d.mapping['cells'][cname]
        opposite='Q' if pin=='QN' else 'QN'
        if opposite in cell['connections']:
            names=['~'+n for b in cell['connections'][opposite] for n in d.names.get(b,[])]
    return {'kind':kind,'aliases':names or [str(bit)]}
def backcone(d, bits):
    seen=set();cells=set();leaves={}
    def visit(bit):
        if bit in seen:return
        seen.add(bit)
        if not isinstance(bit,int):
            leaves[str(bit)]=dict(kind='constant',aliases=[str(bit)]);return
        driver=d.drivers.get(bit)
        if not driver:
            aliases=[name+(f'[{idx}]' if len(port['bits'])>1 else '') for name,port in d.mapping['ports'].items() for idx,b in enumerate(port['bits']) if b==bit and port['direction']=='input']
            leaves[str(bit)]=dict(kind='input',aliases=aliases);return
        name,pin=driver;cell=d.mapping['cells'][name]
        if cell['type'].startswith(('DFF','DLH','DLL')) or 'CLKGATE' in cell['type']:
            leaves[str(bit)]=leaf_labels(d,bit,'sequential');return
        cells.add(name)
        for p,direction in cell['port_directions'].items():
            if direction=='input':
                for b in cell['connections'][p]:visit(b)
    for bit in bits:visit(bit)
    return dict(cell_count=len(cells),cell_types=dict(collections.Counter(d.mapping['cells'][c]['type'] for c in cells)),leaf_count=len(leaves),leaves=list(leaves.values()))
def details(d,path):
    p=d.parse(path);p['report_path']=str(path)
    for tag in ['startpoint','endpoint']:
        canon=p[tag].split()[0]
        p[tag+'_aliases']=d.pin_names(canon,'Q') if canon in d.binding else [canon]
    sinks=collections.defaultdict(list)
    for name,cell in d.mapping['cells'].items():
        for pin,direction in cell['port_directions'].items():
            if direction=='input':
                for bit in cell['connections'][pin]:
                    if isinstance(bit,int):sinks[bit].append(dict(cell=d.reverse[name],pin=pin,type=cell['type']))
    for stage in p['stages']:
        cell=d.mapping['cells'][stage['original_cell']]
        bit=cell['connections'][stage['pin']][0]
        stage['sinks']=sinks[bit]
        stage['fanout_input_pin_count']=len(sinks[bit])
        stage['input_aliases']={pin:sorted({n for b in bs for n in d.names.get(b,[])}) for pin,bs in cell['connections'].items() if cell['port_directions'][pin]=='input'}
        stage['output_aliases']=d.names.get(bit,[])
    p['cell_delay_ns']=sum(s['delay_ns'] for s in p['stages'])
    return p
inputs={str(HELPER):sha(HELPER),str(Path(__file__).resolve()):sha(__file__)}
results={};cones={};generated={}
for name,base in [('baseline',ROOT/'o2-r3-div-gate-cost-20261025'),('c1',ROOT/'o2-c1-owner-20261025')]:
    d=h.Design(base)
    for f in [base/'parent-map-01/mapped.json',d.sta/'instance-binding.json',d.sta/'sta-canonical.v',d.sta/'nominal/timing.tcl']:
        inputs[str(f)]=sha(f)
    results[name]={}
    for kind in ['ready','vdot_r2r']:
        p=d.sta/'nominal'/(kind+'.rpt');inputs[str(p)]=sha(p);results[name][kind]=details(d,p)
    end=results[name]['vdot_r2r']['endpoint'].split()[0]
    endcell=d.mapping['cells'][d.binding[end]]
    cones[name]={'ready':backcone(d,d.mapping['ports']['io_in_ready']['bits']), 'vdot_result18_d':backcone(d,endcell['connections']['D'])}
    generated[name]={f.name:sha(f) for f in (base/'parent-cost-01/rtl').glob('*.sv')}
    for f in (base/'parent-cost-01/rtl').glob('*.sv'):inputs[str(f)]=sha(f)
    # All five existing profiles: no fresh STA.
    results[name]['profiles']={}
    for profile in ['nominal','period050','period200','load001','load020']:
        results[name]['profiles'][profile]={}
        for kind in ['ready','vdot_r2r']:
            p=d.sta/profile/(kind+'.rpt');inputs[str(p)]=sha(p)
            q=d.parse(p);results[name]['profiles'][profile][kind]={k:q[k] for k in ['startpoint','endpoint','arrival_ns','buffer_count','buffer_delay_ns']}
source_diff=subprocess.run(['git','-C',str(ROOT/'o2-c1-owner-20261025/repo'),'diff','0f12df675378556670afd0dd2153f47fcb330610','3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66','--','src/main/scala/xiangshan/backend/exu/ExeUnit.scala'],text=True,capture_output=True,check=True).stdout
(OUT/'production-source.diff').write_text(source_diff)
save(OUT/'paths.json',results);save(OUT/'cones.json',cones)
save(OUT/'generated-comparison.json',dict(before=generated['baseline'],after=generated['c1'],changed=[n for n in generated['baseline'] if generated['baseline'][n]!=generated['c1'][n]]))
for p,digest in inputs.items():assert sha(p)==digest,p
save(OUT/'inputs.json',inputs)
summary={}
for name,rr in results.items():
    summary[name]={}
    for kind in ['ready','vdot_r2r']:
        p=rr[kind]
        summary[name][kind]={k:p[k] for k in ['arrival_ns','startpoint_aliases','endpoint_aliases','output_cell_count','buffer_count','buffer_delay_ns','cell_delay_ns']}
        summary[name][kind]['types']=[x['type'] for x in p['stages']]
    summary[name]['cone_summary']={k:{kk:vv for kk,vv in v.items() if kk!='leaves'} for k,v in cones[name].items()}
save(OUT/'summary.json',summary)
save(OUT/'status.json',dict(status='READ_ONLY_SIDE_PATH_ANALYSIS_COMPLETE',time=datetime.datetime.now().astimezone().isoformat(),inputs_unchanged=True,input_count=len(inputs),scope='Read existing netlists/reports only; no RTL write, synthesis, STA, regression, push or frozen artifact edits'))
print(json.dumps(summary,ensure_ascii=False,indent=2))
