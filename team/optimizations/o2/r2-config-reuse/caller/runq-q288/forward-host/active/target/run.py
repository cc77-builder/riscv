"""New FP32-to-QKV contract on the unmodified existing build/runtime engines."""
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
import argparse,importlib.util,json,os,re,shlex,struct
HERE=Path(__file__).resolve().parent
Q=HERE.parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
tail=load('active_qkv_old_target',Q/'fused/phased/tail/target/run.py')
gen=load('active_qkv_generator',HERE/'generate.py')
traced=load('active_qkv_path',HERE/'path.py')
active=load('active_qkv_consumer',HERE.parent/'check.py')
ROOT,g,parent,old=tail.ROOT,tail.g,tail.parent,tail.old
read,now,digest,adapt=tail.read,tail.now,tail.digest,tail.adapt
CONTRACT,MAX_CYCLES,GENERATED=gen.CONTRACT,gen.MAX_CYCLES,gen.FILES
OWN=('main.c','boundary.h','boundary.S','generate.py','path.py','run.py','prepare.py','oracle.c','CONTRACT.md')
OLD_SOURCES,OLD_VERIFY,OLD_COMPILER=tail.sources,tail.verification,tail.compiler_commands

def sources(repo):
    g.require(repo==ROOT and HERE==(repo/active.Q/'forward-host/active/target').resolve(),'selected source identity')
    found=OLD_SOURCES(repo);found.update(active.source_identity(repo))
    paths=[HERE/n for n in OWN]+[gen.FIXTURE,HERE/'evidence/input-v1/result.json']
    found.update({p.relative_to(repo).as_posix():g.sha(p) for p in paths});return found
def generate(repo,out):return gen.generate(repo,out)

def paths_for_plan(elf,manifest):
    f=gen.fixtures();model=tail.previous.value_model;paths={};details={}
    for call in manifest['call_plan']:
        row=manifest['rows'][call['arm']];d=call['dataset'];key=str(row['id'])+':'+str(d)
        if key in details:continue
        stream,detail=traced.path(ROOT,elf,row,f,d,tail.phased,model)
        if row['id'] in paths:g.require(paths[row['id']]==stream,'identical path across actual activations')
        else:paths[row['id']]=stream
        details[key]=dict(detail,dataset=d)
    return paths,details

def compiled_arrays(elf,manifest):
    f=gen.fixtures();raw=f['raw']
    pack=lambda values:struct.pack('<'+str(len(values))+'I',*values)
    arrays={
        'qkv_weights':b''.join(raw[f'weight-{i}.bin'] for i in range(3)),
        'qkv_packed':b''.join(raw[f'packed-{i}.bin'] for i in range(3)),
        'qkv_weight_scale':b''.join(raw[f'scale-{i}.bin'] for i in range(3)),
        'qkv_fp':b''.join(raw[f'fp-{i}.bin'] for i in range(3)),
        'qkv_expected_x':b''.join(raw[f'quant-{i}.bin'][:288] for i in range(3)),
        'qkv_expected_xs':b''.join(raw[f'quant-{i}.bin'][288:] for i in range(3)),
        'qkv_expected_y':b''.join(raw[f'y-{d}-{i}.bin'] for d in range(2) for i in range(3)),
        'qkv_order':pack(gen.ORDER),
        'qkv_kernels':struct.pack('<2Q',*(elf.symbols[n][0] for n in gen.WRAPPERS)),
        'split_entries':struct.pack('<6Q',*(elf.symbols[n][0] for n in gen.parent.NEW))}
    for name,value in arrays.items():g.require(elf.symbol_data(name)==value,'compiled array: '+name)
    calls=[dict(stage=0,arm=i,dataset=1) for i in range(2)]
    for arm in gen.ORDER:calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    g.require(manifest['call_plan']==calls and [s['index'] for s in manifest['plan']]==list(gen.ORDER) and
        manifest['boundary_calls']==14 and manifest['full_q_calls']==42 and manifest['expected_dots']==155521,
        'exact new complete-boundary call plan')
    return {n:digest(v) for n,v in arrays.items()}

def compiler_commands(log,record):
    result=OLD_COMPILER(log,record);root=PurePosixPath(record['build_root']);gcc=record['toolchain']['gcc']['path']
    source=str(root/'source/boundary.S');obj=str(root/'objects/boundary.o')
    commands=[shlex.split(line) for line in log.splitlines() if line.startswith(gcc+' ') and source in shlex.split(line)]
    g.require(len(commands)==1 and commands[0][-4:]==['-c','-o',obj,source] and
              '-mno-relax' in commands[0] and '-mabi=lp64d' in commands[0],'actual separate boundary assembly compilation')
    result['boundary']=commands[0];return result

def verification(repo,build_dir):
    with adapt(tail,CONTRACT=CONTRACT,GENERATED=GENERATED,gen=gen,sources=sources,generate=generate,
               compiled_arrays=compiled_arrays,paths_for_plan=paths_for_plan,compiler_commands=compiler_commands):
        result=OLD_VERIFY(repo,build_dir)
    elf=g.ELF((build_dir/'vdot-perf.elf').read_bytes())
    result.update(status='ACTUAL_QKV_ELF_INPUT_ROUTE_AND_COMPLETE_PATH_PASS',contract=CONTRACT,
        windows=6,full_q_calls=42,boundary_calls=14,quantize_calls_in_boundaries=14,standalone_quantize_probes=3,
        new_function_sha256={n:digest(elf.symbol_data(n)) for n in ('qkv_boundary','qkv_quantize')})
    return result

def selection(samples,manifest):
    methods=[]
    for i,row in enumerate(manifest['rows']):
        group=[s for s in samples if s['id']==i]
        g.require(len(group)==(2 if i==0 else 4) and all(s['cycles']>0 for s in group),'all planned observations retained')
        methods.append(dict(id=i,label=row['label'],kernel=row['kernel'],cycles=[s['cycles'] for s in group],
            instructions=[s['instructions'] for s in group],mean_cycles=sum(s['cycles'] for s in group)/len(group)))
    ta,fr=methods[0]['cycles'],methods[1]['cycles'];stable=100*max(fr)<=101*min(fr)
    separated=200*max(ta)<=199*min(fr);blocks=[]
    for block in range(2):
        a=[s['cycles'] for s in samples if s['id']==0 and s['block']==block]
        b=[s['cycles'] for s in samples if s['id']==1 and s['block']==block]
        blocks.append(dict(block=block,ta=a,fr=b,reduction=1-max(a)/min(b)))
    chosen=0 if separated else 1
    return dict(decision='HOLD_CONTEXT_VARIATION' if not stable else 'TA_QKV_PREFERRED' if separated else 'FR_QKV_PREFERRED',
        methods=methods,anchors=fr,anchor_gate=stable,separation_gate=separated,
        selected_id=chosen if stable else None,selected_method=gen.WRAPPERS[chosen] if stable else None,
        worst_ta=max(ta),best_fr=min(fr),reduction=1-max(ta)/min(fr),blocks=blocks,
        qualified=stable,hardware_changed=False,stable_default_changed=False,pack_included=False,
        includes_quantization=True,application_scope='one fixed ELF, actual layer0 pos0, prepacked FP32-to-QKV, shared scalar quantizer',
        full_forward_qualified=False,trained_model_quality_qualified=False,replay_is_additional_sample=False)

def normal(repo,build_dir,run_dir,receipt):
    g.require(receipt.get('process_started') is True and receipt.get('exit_code')==0 and not receipt.get('timed_out'),'complete execution required')
    manifest=read(build_dir/'source/manifest.json')
    stdout,stderr=((run_dir/n).read_text() for n in ('stdout.log','stderr.log'))
    gate=g.load('qkv_target_failure',repo/'team/optimizations/o1/audit/runtime_gate.py')
    fatal=g.load('qkv_target_fatal',repo/'team/optimizations/o2/fullcore/recheck.py')
    observer=g.load('qkv_target_protocol',repo/'team/optimizations/o2/fullcore/analyze.py')
    for stream in (stdout,stderr):gate.validate_failure_markers(stream);fatal.reject_fatal_output(stream)
    _,uart=observer.extract_events_and_uart(stderr+stdout);gate.validate_failure_markers(uart);fatal.reject_fatal_output(uart)
    plain=gate.normalize_console(uart)
    counter=g.load('qkv_target_counter',repo/'team/workloads/unified-vdot/check.py')
    elf=g.ELF((build_dir/'vdot-perf.elf').read_bytes());paths,details=paths_for_plan(elf,manifest)
    counter.walk=lambda stream:stream;events=counter.parse_events(stderr);samples=counter.trace_windows(events,manifest,paths)
    windows=[];current=None
    for event in events['RETIRE']:
        if event['word']==traced.START:current=[]
        if current is not None:current.append(event)
        if event['word']==traced.STOP:windows.append(current);current=None
    g.require(current is None and len(windows)==len(samples)==len(manifest['plan'])==6,'exact complete-boundary window inventory')
    for records,step in zip(windows,manifest['plan']):
        stream=paths[step['index']];pos=0
        for event in records:
            covered=stream[pos:pos+event['count']]
            if event['count']>1:g.require(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered),'control hidden by ROB compression')
            pos+=event['count']
        g.require(pos==len(stream),'complete marker path')
    for sample,step in zip(samples,manifest['plan']):
        sample.update({k:step[k] for k in ('dataset','block','role')});row=manifest['rows'][step['index']]
        sample.update(kind='QKV',variant=row['variant'],label=row['label'],kernel=row['kernel'])
        g.require(sample['instructions']==details[str(row['id'])+':0']['expected_csr_instret'],'CSR instret vs complete actual path')
    expected=[f'QKV_BEGIN contract={CONTRACT} windows=6','QKV_FUNCTIONAL boundaries=14 projections=42 outputs=12096 quantizer_probes=3 controls=6']
    expected += [f"QKV_CALL {i} {c['stage']} {c['arm']} {c['dataset']}" for i,c in enumerate(manifest['call_plan'])]
    expected += [f"QKVW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['QKV_END windows=6 boundaries=14 projections=42 probe_dots=1 failures=0']
    actual=[line for line in plain.splitlines() if line.startswith(('QKV_','QKVW '))]
    g.require(actual==expected and plain.count('HIT GOOD TRAP')==1,'complete UART/call-plan/quantizer/output evidence')
    analysis=observer.analyze(stderr+stdout)
    g.require(analysis['status']=='O2_TRACE_PASS' and analysis['schema']['slots']==2 and
        all(analysis.get(k)==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
        analysis['counts'].get('COMMIT')==155521,'complete protocol and all-stage custom total')
    probe=elf.symbols['q_fault_probe'][0]+5*4;expected_pcs=[probe];phases=[]
    for i,call in enumerate(manifest['call_plan']):
        pcs=[pc for pc,w in paths[call['arm']] if w&0xfe00707f==0x0200000b]
        phases.append(dict(seq=i,**call,vdot_count=len(pcs),first_commit_index=len(expected_pcs)));expected_pcs.extend(pcs)
    actual_pcs=[int(v,16) for v in re.findall(r'^O2_COMMIT [^\n]*pc=0x([0-9a-fA-F]+)',stderr,re.M)]
    g.require(actual_pcs==expected_pcs and len(actual_pcs)==155521,'entire functional/warm/timed custom PC sequence')
    g.require(len(events['COUNTER_ENQUEUE'])==len(events['CSR_SAMPLE'])==24,'exact complete-boundary counter totals')
    return dict(status='ACTUAL_QKV_DIFFTEST_AND_COMPLETE_PLAN_PASS',contract=CONTRACT,windows=6,
        boundary_calls=14,full_q_calls=42,projection_outputs=12096,quantizer_probes=3,judge_fault_controls=6,
        committed_vdot=155521,timed_vdot=62208,custom_phases=phases,
        all_stage_custom_pc_sha256=digest(b''.join(struct.pack('<Q',p) for p in actual_pcs)),
        counter_enqueues=24,csr_samples=24,samples=samples,selection=selection(samples,manifest),
        hardware_changed=False,stable_default_changed=False,replay_and_archive_required_for_completion=True)

def build(repo,identity,out):
    with adapt(old,CONTRACT=CONTRACT,sources=sources,generate=generate,verification=verification):return old.build(repo,identity,out)
def run(repo,identity,build_dir,out,operation):
    with adapt(tail.base.base.up,CONTRACT=CONTRACT,MAX_CYCLES=MAX_CYCLES,GENERATED=GENERATED,
               sources=sources,verification=verification,gen=SimpleNamespace(NEW=('q_fault_probe',)),normal=normal):
        return tail.base.base.up.run(repo,identity,build_dir,out,operation)

def selector_controls(manifest):
    def sample(ta,fr):return [dict(seq=i,id=s['index'],cycles=ta if s['index']==0 else fr,
        instructions=1,block=s['block'],role=s['role']) for i,s in enumerate(manifest['plan'])]
    yes=selection(sample(98000,100000),manifest);g.require(yes['selected_id']==0,'selector positive')
    no=selection(sample(100000,100000),manifest);g.require(no['selected_id']==1,'no separation retains FR')
    fast=sample(99400,100000)
    for s in fast:
        if s['role']=='anchor_end':s['cycles']=99100
    end=selection(fast,manifest);g.require(end['anchor_gate'] and end['selected_id']==1,'fast ending anchors included')
    unstable=sample(98000,100000);unstable[-1]['cycles']=97000
    hold=selection(unstable,manifest);g.require(hold['selected_id'] is None and not hold['qualified'],'unstable anchor forbids selection')
    return dict(status='QKV_SELECTOR_CONTROLS_PASS',positive=yes,no_gain=no,all_anchors=end,unstable=hold)

def elf_controls(build_dir,out):
    out.mkdir(parents=True,exist_ok=False);raw=(build_dir/'vdot-perf.elf').read_bytes();elf=g.ELF(raw)
    manifest=read(build_dir/'source/manifest.json');positive=compiled_arrays(elf,manifest);cases=[]
    for name in ('qkv_fp','qkv_kernels','qkv_expected_xs'):
        body=elf.symbol_data(name);offset=raw.find(body);g.require(offset>=0 and raw.find(body,offset+1)<0,'unique mutation region')
        mutant=bytearray(raw);mutant[offset]^=1;(out/(name+'.elf')).write_bytes(mutant)
        try:compiled_arrays(g.ELF(bytes(mutant)),manifest)
        except ValueError as error:
            g.require(str(error)=='compiled array: '+name,'specific data/route rejection');cases.append(dict(name=name,error=str(error),sha256=digest(mutant)))
        else:raise ValueError('accepted altered input/route')
    body=elf.symbol_data('qkv_quantize');offset=raw.find(body);g.require(offset>=0 and raw.find(body,offset+1)<0,'unique quantizer')
    matches=[(i,w) for i,(w,) in enumerate(struct.iter_unpack('<I',body)) if w&127==0x53 and w>>25==0x60]
    g.require(len(matches)==1,'one static quantizer conversion');i,w=matches[0]
    mutant=bytearray(raw);struct.pack_into('<I',mutant,offset+4*i,w&~(7<<12));(out/'wrong-rounding.elf').write_bytes(mutant)
    try:traced.path(ROOT,g.ELF(bytes(mutant)),manifest['rows'][0],gen.fixtures(),0,tail.phased,tail.previous.value_model)
    except ValueError as error:
        g.require(str(error)=='explicit signed RMM integer conversion','specific wrong-rounding rejection');cases.append(dict(name='wrong-rounding',error=str(error),sha256=digest(mutant)))
    else:raise ValueError('accepted wrong quantizer rounding')
    result=dict(status='ACTUAL_QKV_ELF_NEGATIVE_CONTROLS_PASS',contract=CONTRACT,positive_arrays=positive,
        controls=cases,selector=selector_controls(manifest),new_emu_runs=0);g.save(out/'result.json',result);return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--identity',type=Path)
    p.add_argument('--action',choices=('build','verify','run','elf'),required=True);p.add_argument('--build',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--operation-id');a=p.parse_args()
    repo=a.repo.resolve();out=a.output.resolve();g.require(repo==ROOT and not out.exists(),'selected checkout and fresh output')
    identity=(a.identity or repo/parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json').resolve()
    cfg=parent.parent_identity(repo,identity)['configuration'];roots=[repo,identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    if a.build:roots.append(a.build.resolve())
    parent.outside_inputs(out,roots)
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if a.action=='build':result=build(repo,identity,out)
    elif a.action=='verify':result=verification(repo,a.build.resolve());g.save(out,result)
    elif a.action=='elf':result=elf_controls(a.build.resolve(),out)
    else:g.require(a.operation_id,'operation id required');result=run(repo,identity,a.build.resolve(),out,a.operation_id)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
