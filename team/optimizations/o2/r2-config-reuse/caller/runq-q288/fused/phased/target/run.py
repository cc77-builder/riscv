"""Frozen FV/PV/FR target contract; reuses the established runtime and raw audit engines."""
from pathlib import Path
from types import SimpleNamespace
import argparse,importlib.util,json,os,re,shlex,struct,sys

HERE=Path(__file__).resolve().parent
Q=HERE.parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
previous=load('phased_target_previous_run',Q/'fused/target/run.py')
gen=load('phased_target_generator',HERE/'generate.py')
_saved_candidate=sys.modules.get('candidate');sys.modules['candidate']=gen.candidate
try:phased=load('phased_target_fixed_checker',HERE.parent/'screen.py')
finally:
    if _saved_candidate is None:sys.modules.pop('candidate',None)
    else:sys.modules['candidate']=_saved_candidate
ROOT,g,parent,old,base=previous.ROOT,previous.g,previous.parent,previous.old,previous.base
PARENT_DIR=previous.PARENT_DIR
read,now,digest,adapt=previous.read,previous.now,previous.digest,previous.adapt
fixture_gen=gen.parent
CONTRACT,MAX_CYCLES,GENERATED=gen.CONTRACT,gen.MAX_CYCLES,gen.FILES
OWN=('main.c','generate.py','run.py','archive.py','CONTRACT.md')
_OLD_SOURCES,_OLD_PATH,_OLD_PATHS,_OLD_VERIFY=previous.sources,previous.path,previous.paths_for_plan,previous.verification
_OLD_COMPILER=previous.compiler_commands
STATIC_PINS={'candidate.py':'2b487c60b53e25dbc04eba4c2eac4bd175e1573837863194de463d6a27df2399',
             'screen.py':'8537f85027ccc9164229c10a400a7d996d42c6711d30dc869835e5eb71a88fd9',
             'CONTRACT.md':'142f536df62d5d9a873732397e2a6725a409f069eae97dbbdfef2554aa417fd2'}

def sources(repo):
    found=_OLD_SOURCES(repo)
    for name,pin in STATIC_PINS.items():g.require(g.sha(HERE.parent/name)==pin,'unchanged existing phased source '+name)
    paths=[HERE/n for n in OWN]+[HERE.parent/n for n in STATIC_PINS]
    found.update({p.relative_to(repo).as_posix():g.sha(p) for p in paths})
    return found

def generate(repo,out):return gen.generate(repo,out)

def path(elf,row,fixture,dataset=0):
    if row['variant']!='phased':return _OLD_PATH(elf,row,fixture,dataset)
    # Explicitly select the independent 131-word checker; never use the old
    # check_full 140-word boundary for PV. Reuse only the actual-address setup.
    checked=phased.checker_class(previous.value_model,ROOT/'team/optimizations/o2/r2-safe-tail/machine_model.py')
    class TargetPhased(checked):
        def check_full(self,kind,golden):
            g.require(kind=='vdot','phased is the fixed vdot candidate')
            return self.check(golden)
    with adapt(previous.value_model,machine_class=lambda _:TargetPhased):
        return _OLD_PATH(elf,row,fixture,dataset)

def paths_for_plan(elf,manifest):
    with adapt(previous,path=path):return _OLD_PATHS(elf,manifest)

def compiled_arrays(elf,manifest):
    f=fixture_gen.fixtures();guard=struct.pack('<2Q',gen.GUARD,gen.GUARD)
    packed=lambda values,size:struct.pack('<'+str(len(values))+size,*values)
    arrays={
        'q_weights':fixture_gen.bytes8(f['weight']),'q_weight_scale':fixture_gen.bytes32(f['weight_scale']),
        'q_inputs':b''.join(fixture_gen.bytes8(x) for x in f['inputs']),
        'q_input_scale':b''.join(fixture_gen.bytes32(x) for x in f['input_scale']),
        'q_golden':b''.join(fixture_gen.bytes32(x) for x in f['golden']),
        'q_packed':guard+fixture_gen.bytes8(f['packed'])+guard,
        'q_order':packed(gen.ORDER,'I'),'q_methods':packed(gen.METHODS,'I'),
        'q_functional_order':packed(gen.FUNCTIONAL_ORDER,'I'),
        'q_functional_datasets':packed(gen.FUNCTIONAL_DATASETS,'I'),
        'q_wrappers':packed([elf.symbols[n][0] for n in gen.WRAPPERS],'Q'),
        'split_entries':packed([elf.symbols[n][0] for n in fixture_gen.NEW],'Q')}
    for name,raw in arrays.items():g.require(elf.symbol_data(name)==raw,'compiled array: '+name)
    calls=[dict(stage=0,arm=a,dataset=d) for a,d in zip(gen.FUNCTIONAL_ORDER,gen.FUNCTIONAL_DATASETS)]
    for arm in gen.ORDER:calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    g.require(manifest['call_plan']==calls and tuple(s['index'] for s in manifest['plan'])==gen.ORDER,
              'exact new warm/functional/measured plan')
    g.require(len(calls)==22 and manifest['full_q_calls']==22 and manifest['expected_dots']==124417,'new normal-run counts')
    return {n:digest(raw) for n,raw in arrays.items()}

def compiler_commands(log,record):
    result=_OLD_COMPILER(log,record);ld=record['toolchain']['ld']['path']
    commands=[shlex.split(line) for line in log.splitlines() if line.startswith(ld+' ')]
    g.require(len(commands)==1 and commands[0].count('--undefined=q288_full')==1 and
              commands[0].count('--gc-sections')==1 and '--whole-archive' not in commands[0],
              'single explicit legacy link root; ordinary GC preserved')
    result['link_legacy_root']=commands[0]
    return result

def verification(repo,build_dir):
    with adapt(previous,CONTRACT=CONTRACT,GENERATED=GENERATED,gen=gen,sources=sources,generate=generate,
               compiled_arrays=compiled_arrays,paths_for_plan=paths_for_plan,compiler_commands=compiler_commands):
        result=_OLD_VERIFY(repo,build_dir)
    elf=g.ELF((build_dir/'vdot-perf.elf').read_bytes());certificate=phased.certificate(elf)
    g.require(certificate['core_sha256']=='ada26193770cfcbf3de5871722055721ad3cbcee4875ef4f61ef7c4b4a37c74f',
              'same existing static phased core bytes')
    result.update(status='PHASED_TARGET_ELF_DATASET_AND_TIMER_PATH_PASS',windows=8,full_q_calls=22,
                  phased_certificate=certificate,phased_function_sha256=digest(elf.symbol_data('q288_phased_vdot')))
    return result

def selection(samples,manifest):
    methods=[]
    for i,row in enumerate(manifest['rows']):
        ss=[s for s in samples if s['id']==i];wanted=4 if i==2 else 2
        g.require(len(ss)==wanted and all(s['cycles']>0 for s in ss),'every planned observation retained')
        methods.append(dict(id=i,label=row['label'],wrapper=row['wrapper'],leaf=row['leaf'],
            cycles=[s['cycles'] for s in ss],instructions=[s['instructions'] for s in ss],
            mean_cycles=sum(s['cycles'] for s in ss)/wanted))
    anchors=methods[2]['cycles'];context=100*max(anchors)<=101*min(anchors)
    comparisons=[]
    for baseline,label in ((0,'phased-vs-current-fused-vdot'),(2,'phased-vs-named-fused-rvv4')):
        after,before=methods[1]['cycles'],methods[baseline]['cycles']
        gate=200*max(after)<=199*min(before)
        blocks=[]
        for block in range(2):
            a=[s['cycles'] for s in samples if s['id']==1 and s['block']==block]
            b=[s['cycles'] for s in samples if s['id']==baseline and s['block']==block]
            blocks.append(dict(block=block,worst_candidate=max(a),best_baseline=min(b),
                               reduction=1-max(a)/min(b),passed=200*max(a)<=199*min(b)))
        comparisons.append(dict(comparison=label,candidate=1,baseline=baseline,blocks=blocks,
            worst_candidate=max(after),best_baseline=min(before),reduction=1-max(after)/min(before),
            separation_gate=gate,qualified=context and gate))
    promote=context and all(c['separation_gate'] for c in comparisons)
    incumbent_vdot=200*max(methods[0]['cycles'])<=199*min(anchors)
    chosen=1 if promote else 0 if incumbent_vdot else 2
    return dict(decision='HOLD_CONTEXT_VARIATION' if not context else 'PHASED_PREFERRED_IN_FIXED_PLAN' if promote else 'KEEP_EXISTING_ENTRY',
        methods=methods,anchors=anchors,anchor_gate=context,software_comparisons=comparisons,
        phased_promoted=promote,selected_id=chosen if context else None,
        selected_method=methods[chosen]['wrapper'] if context else None,
        selected_label=methods[chosen]['label'] if context else None,
        selected_leaf=methods[chosen]['leaf'] if context else None,comparison_gate_pass=context,
        stable_default_changed=False,pack_included=False,hardware_changed=False,
        statistical_scope='two fixed reverse-order FV/PV observations; all four FR points; replay not an extra sample',
        application_scope='synthetic prepacked Q, same-method selfwarm, named FR only; no token/full-model/ASIC claim')

def normal(repo,build_dir,run_dir,receipt):
    g.require(receipt.get('process_started') is True and receipt.get('exit_code')==0 and not receipt.get('timed_out'),'complete execution required')
    manifest=read(build_dir/'source/manifest.json')
    stdout,stderr=((run_dir/n).read_text() for n in ('stdout.log','stderr.log'))
    gate=g.load('phased_target_failure',repo/'team/optimizations/o1/audit/runtime_gate.py')
    fatal=g.load('phased_target_fatal',repo/'team/optimizations/o2/fullcore/recheck.py')
    observer=g.load('phased_target_protocol',repo/'team/optimizations/o2/fullcore/analyze.py')
    for stream in (stdout,stderr):gate.validate_failure_markers(stream);fatal.reject_fatal_output(stream)
    _,uart=observer.extract_events_and_uart(stderr+stdout);gate.validate_failure_markers(uart);fatal.reject_fatal_output(uart)
    plain=gate.normalize_console(uart)
    counter=g.load('phased_target_counter',repo/'team/workloads/unified-vdot/check.py')
    elf=g.ELF((build_dir/'vdot-perf.elf').read_bytes());paths,details=paths_for_plan(elf,manifest)
    counter.walk=lambda stream:stream;events=counter.parse_events(stderr);samples=counter.trace_windows(events,manifest,paths)
    windows=[];current=None
    for event in events['RETIRE']:
        if event['word']==base.base.traced.START:current=[]
        if current is not None:current.append(event)
        if event['word']==base.base.traced.STOP:windows.append(current);current=None
    g.require(current is None and len(windows)==len(samples)==len(manifest['plan'])==8,'exact new measured window inventory')
    for records,step in zip(windows,manifest['plan']):
        stream=paths[step['index']];pos=0
        for event in records:
            covered=stream[pos:pos+event['count']]
            if event['count']>1:g.require(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered),'control hidden by ROB compression')
            pos+=event['count']
        g.require(pos==len(stream),'complete marker path')
    for sample,step in zip(samples,manifest['plan']):
        sample.update({k:step[k] for k in ('dataset','block','role')});row=manifest['rows'][step['index']]
        sample.update(kind='Q',variant=row['variant'],label=row['label'],leaf=row['leaf'])
        g.require(sample['instructions']==details[str(row['id'])+':0']['expected_csr_instret'],'actual CSR instret vs exact complete path')
    expected=[f'Q_BEGIN contract={CONTRACT} windows=8','Q_FUNCTIONAL calls=22 controls=5 outputs=6336 warm=8 extra=6']
    expected += [f"Q_CALL {i} {c['stage']} {c['arm']} {c['dataset']}" for i,c in enumerate(manifest['call_plan'])]
    expected += [f"QW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['Q_END windows=8 full_calls=22 leaf_calls=0 inline_calls=22 probe_dots=1 failures=0']
    actual=[line for line in plain.splitlines() if line.startswith(('Q_','QW '))]
    g.require(actual==expected and plain.count('HIT GOOD TRAP')==1,'complete UART/call-plan/counter/oracle evidence')
    analysis=observer.analyze(stderr+stdout)
    g.require(analysis['status']=='O2_TRACE_PASS' and analysis['schema']['slots']==2 and
        all(analysis.get(k)==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
        analysis['counts'].get('COMMIT')==124417,'complete O2 protocol and all-stage custom total')
    probe=elf.symbols['q_fault_probe'][0]+5*4;expected_pcs=[probe];phases=[]
    for i,call in enumerate(manifest['call_plan']):
        pcs=[pc for pc,w in paths[call['arm']] if w&0xfe00707f==0x0200000b]
        phases.append(dict(seq=i,**call,vdot_count=len(pcs),first_commit_index=len(expected_pcs)));expected_pcs.extend(pcs)
    actual_pcs=[int(v,16) for v in re.findall(r'^O2_COMMIT [^\n]*pc=0x([0-9a-fA-F]+)',stderr,re.M)]
    g.require(actual_pcs==expected_pcs and len(actual_pcs)==124417,'entire functional/warm/timed custom PC sequence')
    g.require(len(events['COUNTER_ENQUEUE'])==len(events['CSR_SAMPLE'])==32,'exact new counter totals')
    return dict(status='PHASED_TARGET_DIFFTEST_AND_PLAN_PASS',contract=CONTRACT,windows=8,
        full_q_calls=22,functional_calls=22,explicit_functional_calls=6,timed_q_calls=8,selfwarm_calls=8,
        extra_functional_calls=6,judge_fault_controls=5,committed_vdot=124417,timed_vdot=41472,custom_phases=phases,
        all_stage_custom_pc_sha256=digest(b''.join(struct.pack('<Q',p) for p in actual_pcs)),
        counter_enqueues=32,csr_samples=32,samples=samples,selection=selection(samples,manifest),
        hardware_changed=False,stable_default_changed=False,replay_and_archive_required_for_completion=True)

def build(repo,identity,out):
    with adapt(old,CONTRACT=CONTRACT,sources=sources,generate=generate,verification=verification):
        return old.build(repo,identity,out)

def run(repo,identity,build_dir,out,operation):
    with adapt(base.base.up,CONTRACT=CONTRACT,MAX_CYCLES=MAX_CYCLES,GENERATED=GENERATED,
               sources=sources,verification=verification,gen=SimpleNamespace(NEW=('q_fault_probe',)),normal=normal):
        return base.base.up.run(repo,identity,build_dir,out,operation)

def selector_control(manifest):
    def data(fv,pv,fr):
        result=[]
        for i,s in enumerate(manifest['plan']):
            arm=s['index'];value=(fv,pv,fr)[arm]
            if isinstance(value,list):value=value[s['block']]
            result.append(dict(seq=i,id=arm,cycles=value,instructions=1,block=s['block'],role=s['role']))
        return result
    positive=selection(data(100000,98000,110000),manifest)
    g.require(positive['phased_promoted'] and positive['selected_id']==1,'positive bounded promotion')
    counter=data(110000,99400,100000)
    for s in counter:
        if s['id']==2 and s['role']=='anchor_end':s['cycles']=99100
    included=selection(counter,manifest)
    g.require(included['anchor_gate'] and not included['phased_promoted'] and
              not included['software_comparisons'][1]['separation_gate'],'fast end anchors retained in denominator')
    unstable=[dict(s,cycles=97000 if s['id']==2 and s['role']=='anchor_end' else s['cycles']) for s in counter]
    held=selection(unstable,manifest)
    g.require(held['decision']=='HOLD_CONTEXT_VARIATION' and held['selected_id'] is None and
              not any(c['qualified'] for c in held['software_comparisons']),'bad anchor forbids all promotion')
    loses_incumbent=selection(data(98000,99000,100000),manifest)
    g.require(loses_incumbent['software_comparisons'][1]['qualified'] and not loses_incumbent['phased_promoted'] and
              loses_incumbent['selected_id']==0,'beating RVV alone cannot displace faster FV')
    noisy=selection(data(105000,[90000,110000],110000),manifest)
    g.require(not noisy['phased_promoted'] and noisy['selected_id']==0,'mean cannot hide worst-observation failure')
    return dict(status='PHASED_ALL_ANCHORS_AND_INCUMBENT_CONTROLS_PASS',positive=positive,
                fast_end_anchor=included,unstable_context=held,incumbent=loses_incumbent,noisy=noisy)

def elf_controls(build_dir,out):
    positive=verification(ROOT,build_dir);out.mkdir(parents=True,exist_ok=False)
    raw=(build_dir/'vdot-perf.elf').read_bytes();elf=g.ELF(raw);manifest=read(build_dir/'source/manifest.json')
    controls=[]
    for name,at,size in (('q_wrappers',0,8),('q_order',4,4),('q_functional_datasets',0,4),('q_golden',0,4),('q_packed',16,1)):
        body=elf.symbol_data(name);offset=raw.find(body)
        g.require(offset>=0 and raw.find(body,offset+1)<0,'unique array mutation region')
        value=elf.symbols['q288_phased_vdot'][0] if name=='q_wrappers' else int.from_bytes(body[at:at+size],'little')^1
        changed=bytearray(raw);changed[offset+at:offset+at+size]=value.to_bytes(size,'little')
        g.require(bytes(changed)!=raw,'nonempty actual target array mutation')
        (out/(name+'.elf')).write_bytes(changed)
        try:compiled_arrays(g.ELF(bytes(changed)),manifest)
        except ValueError as error:
            g.require(str(error)=='compiled array: '+name,'specific target array rejection')
            controls.append(dict(name=name,file_offset=offset+at,mutated_elf_sha256=digest(changed),error=str(error)))
        else:raise ValueError('actual target array mutant accepted: '+name)
    for arm in range(3):
        row=manifest['rows'][arm];body=elf.symbol_data(row['wrapper']);offset=raw.find(body)
        g.require(offset>=0 and raw.find(body,offset+1)<0,'unique full-Q function mutation region')
        words=[w for w, in struct.iter_unpack('<I',body)]
        at=next(i for i,w in enumerate(words) if w&127==0x57 and w>>26==0x24 and (w>>12)&7==1)
        changed=bytearray(raw);struct.pack_into('<3I',changed,offset+4*at,words[at+1],words[at+2],words[at])
        g.require(bytes(changed)!=raw,'nonempty FP order mutation')
        label=row['label']+'-rounding-order';(out/(label+'.elf')).write_bytes(changed)
        try:path(g.ELF(bytes(changed)),row,fixture_gen.fixtures(),0)
        except ValueError as error:
            wanted='actual phased full-Q bitwise output' if arm==1 else 'actual ELF full-Q bitwise output'
            g.require(str(error)==wanted,'specific target FP order rejection')
            controls.append(dict(name=label,pc=hex(elf.symbols[row['wrapper']][0]+4*at),
                file_offset=offset+4*at,mutated_elf_sha256=digest(changed),error=str(error)))
        else:raise ValueError('target FP order mutant accepted')
    model,helpers=phased.support(ROOT)
    semantic=phased.controls(ROOT,out/'phased-semantics',model.ELF(raw),model,helpers)
    result=dict(status='PHASED_TARGET_ACTUAL_ELF_CONTROLS_PASS',contract=CONTRACT,positive=positive,
                controls=controls,phased_semantic_controls=semantic,selector_regression=selector_control(manifest),new_emu_runs=0)
    g.save(out/'result.json',result);return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--identity',type=Path)
    p.add_argument('--action',choices=('build','verify','run','elf'),required=True)
    p.add_argument('--build',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--operation-id')
    a=p.parse_args();repo=a.repo.resolve();out=a.output.resolve()
    g.require(repo==ROOT and not out.exists(),'selected checkout and fresh output required')
    identity=(a.identity or repo/parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json').resolve()
    cfg=parent.parent_identity(repo,identity)['configuration']
    roots=[repo,identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    if a.build:roots.append(a.build.resolve())
    parent.outside_inputs(out,roots)
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if a.action=='build':result=build(repo,identity,out)
    elif a.action=='verify':
        g.require(a.build is not None,'build required');result=verification(repo,a.build.resolve());g.save(out,result)
    elif a.action=='elf':
        g.require(a.build is not None,'build required');result=elf_controls(a.build.resolve(),out)
    else:
        g.require(a.build is not None and a.operation_id,'build and operation required')
        result=run(repo,identity,a.build.resolve(),out,a.operation_id)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
