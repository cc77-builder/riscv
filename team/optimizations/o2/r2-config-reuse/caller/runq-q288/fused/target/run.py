"""Actual target gates for five complete-Q methods under one frozen plan."""
from pathlib import Path, PurePosixPath
import argparse
import importlib.util
import json
import os
import re
import shlex
import struct
import tempfile
from types import SimpleNamespace
import zipfile

HERE=Path(__file__).resolve().parent
Q=HERE.parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
base=load('fused_target_previous',Q/'acc8/target/run.py')
gen=load('fused_target_generator',HERE/'generate.py')
value_model=load('fused_target_value_model',HERE.parent/'model.py')
fixture_gen=gen.parent
ROOT,g,parent,old=base.ROOT,base.g,base.parent,base.old
PARENT_DIR=base.PARENT_DIR
CONTRACT,MAX_CYCLES,GENERATED=gen.CONTRACT,gen.MAX_CYCLES,gen.FILES
read,now,digest,adapt=base.read,base.now,base.digest,base.adapt
OWN=('main.c','generate.py','run.py','archive.py','CONTRACT.md')
SCREEN=HERE.parent/'evidence/screen-v1/raw.zip'
SCREEN_SHA='201d0b2a01ab246338e6bdc80aaa486bed91254522bd8453c61e1d2de6d70df0'
FUSED_ELF_SHA='6975d57aecd77f9ec6337cbf3aa5b031033e8a7b86dcad4bcd7e78b33b2dc97d'


def sources(repo):
    found=base.sources(repo)
    paths=[HERE/n for n in OWN]+[HERE.parent/n for n in ('generate.py','model.py','screen.py','CONTRACT.md')]+[SCREEN]
    found.update({p.relative_to(repo).as_posix():g.sha(p) for p in paths})
    return found


def generate(repo,out):return gen.generate(repo,out)


def fused_reference():
    g.require(g.sha(SCREEN)==SCREEN_SHA,'frozen full-Q fusion screen archive')
    with zipfile.ZipFile(SCREEN) as z:raw=z.read('screen-03/fused.elf')
    g.require(digest(raw)==FUSED_ELF_SHA,'frozen GNU fusion ELF')
    return g.ELF(raw)


def path(elf,row,fixture,dataset=0):
    if row['variant']=='acc8':return base.path(elf,row,fixture,dataset)
    timer_body=elf.symbol_data('split_measure')
    g.require(timer_body==base.reference_images()[1].symbol_data('split_measure'),'complete common timer body')
    begin=elf.symbols['split_measure'][0]
    timer=[(begin+4*i,w) for i,(w,) in enumerate(struct.iter_unpack('<I',timer_body))]
    starts=[i for i,(_,w) in enumerate(timer) if w==base.base.traced.START]
    stops=[i for i,(_,w) in enumerate(timer) if w==base.base.traced.STOP]
    g.require(starts==[11] and stops==[26] and timer[20][1]==0x000a00e7,'fixed marker/call/return interval')
    cls=value_model.machine_class(ROOT/'team/optimizations/o2/r2-safe-tail/machine_model.py')
    m=cls(fixture,dataset,poison=0x28832)
    addr=lambda n:elf.symbols[n][0]
    m.addresses=dict(packed=addr('q_packed')+16,x=addr('q_inputs')+288*dataset,
                     ws=addr('q_weight_scale'),xs=addr('q_input_scale')+36*dataset,
                     y=addr('q_output')+16,slots=addr('q_slots')+16,context=addr('q_context'))
    m.regions['context']=bytearray(struct.pack('<7Q',*(m.addresses[n] for n in ('packed','x','ws','xs','y','slots')),addr(row['leaf'])))
    m.original['context']=bytes(m.regions['context'])
    m.halt=timer[21][0];m.x[1]=m.halt;m.x[2]=0x87fff000-48
    m.x[8]=m.x[10]=addr('q_context');m.x[9]=addr('q_measurement');m.x[20]=addr(row['wrapper'])
    m.saved={i:m.x[i] for i in m.saved}
    # The established ELF reader stores extra symbol metadata. Adapt its
    # address/size view without changing either frozen parser or value model.
    value_elf=SimpleNamespace(symbols={row['wrapper']:(*elf.symbols[row['wrapper']][:2],0)},
                              symbol_data=elf.symbol_data)
    m.execute_function(value_elf,row['wrapper'])
    detail=m.check_full('vdot' if row['method']=='vdot' else 'rvv4',fixture['golden'][dataset])
    stream=timer[11:21]+m.path+timer[21:27]
    g.require(len(stream)==len(m.path)+16,'same timer overhead')
    detail.update(instructions=len(stream),vdot=10368 if row['method']=='vdot' else 0,
                  leaf_calls=0,integer_core_executions=324,actual_elf_addresses=True,
                  common_timer_bytes_sha256=digest(timer_body),fp_values='exact finite RNE model plus independent host C/Python')
    return stream,detail


def paths_for_plan(elf,manifest):
    fixture=fixture_gen.fixtures();paths={};details={}
    for call in manifest['call_plan']:
        row=manifest['rows'][call['arm']];dataset=call['dataset'];key=str(row['id'])+':'+str(dataset)
        if key in details:continue
        stream,detail=path(elf,row,fixture,dataset)
        if row['id'] in paths:g.require(paths[row['id']]==stream,'all datasets have the identical actual PC/word sequence')
        else:paths[row['id']]=stream
        counters=[i for i,(_,w) in enumerate(stream) if w in base.base.traced.COUNTERS]
        g.require(len(counters)==4,'four actual counter sites')
        details[key]=dict(detail,dataset=dataset,expected_csr_instret=counters[3]-counters[0],
                         path_sha256=digest(b''.join(struct.pack('<QI',pc,w) for pc,w in stream)))
    return paths,details


def compiled_arrays(elf,manifest):
    f=fixture_gen.fixtures();guard=struct.pack('<2Q',gen.GUARD,gen.GUARD)
    arrays={
        'q_weights':fixture_gen.bytes8(f['weight']),'q_weight_scale':fixture_gen.bytes32(f['weight_scale']),
        'q_inputs':b''.join(fixture_gen.bytes8(x) for x in f['inputs']),
        'q_input_scale':b''.join(fixture_gen.bytes32(x) for x in f['input_scale']),
        'q_golden':b''.join(fixture_gen.bytes32(x) for x in f['golden']),
        'q_packed':guard+fixture_gen.bytes8(f['packed'])+guard,
        'q_order':struct.pack('<12I',*gen.ORDER),'q_methods':struct.pack('<5I',*gen.METHODS),
        'q_functional_order':struct.pack('<4I',*gen.FUNCTIONAL_ORDER),
        'q_functional_datasets':struct.pack('<4I',*gen.FUNCTIONAL_DATASETS),
        'q_wrappers':struct.pack('<5Q',*(elf.symbols[n][0] for n in gen.WRAPPERS)),
        'split_entries':struct.pack('<6Q',*(elf.symbols[n][0] for n in fixture_gen.NEW)),
    }
    for name,raw in arrays.items():g.require(elf.symbol_data(name)==raw,'compiled array: '+name)
    expected_calls=[dict(stage=0,arm=a,dataset=d) for a,d in zip(gen.FUNCTIONAL_ORDER,gen.FUNCTIONAL_DATASETS)]
    for arm in gen.ORDER:expected_calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    g.require(manifest['call_plan']==expected_calls and tuple(s['index'] for s in manifest['plan'])==gen.ORDER,
              'exact warm/functional/measured plan')
    return {n:digest(raw) for n,raw in arrays.items()}


def compiler_commands(log,record):
    commands=base.base.compiler_commands(log,record)
    root=PurePosixPath(record['build_root']);gcc=record['toolchain']['gcc']['path']
    source=str(root/'source/fused.S');obj=str(root/'objects/fused.o')
    found=[shlex.split(line) for line in log.splitlines() if line.startswith(gcc+' ') and source in shlex.split(line)]
    g.require(len(found)==1 and found[0][-4:]==['-c','-o',obj,source],'actual separate GNU fused assembly command')
    commands['fused']=found[0]
    return commands


def verification(repo,build):
    record=read(build/'build.json')
    g.require(record['contract']==CONTRACT and record['software_files']==sources(repo) and record['exit_code']==0,'fused target build identity')
    for rel,pin in record['software_files'].items():g.require(g.sha(build/'source/repo'/rel)==pin,'snapshot drift: '+rel)
    g.require(set(record['artifacts'])=={'vdot-perf.elf','vdot-perf.bin','gemv-reference.o'},'artifact inventory')
    for name,pin in record['artifacts'].items():g.require(g.sha(build/name)==pin,'artifact drift: '+name)
    with tempfile.TemporaryDirectory(prefix='fused-target-regenerate-') as tmp:
        fresh=Path(tmp)/'source';manifest=generate(repo,fresh)
        for name in GENERATED:g.require((fresh/name).read_bytes()==(build/'source'/name).read_bytes(),'source regeneration: '+name)
    elf=g.ELF((build/'vdot-perf.elf').read_bytes())
    g.load('fused_target_executable',repo/'team/optimizations/o2/r2-select/entry_c_api.py').executable(elf)
    g.require(elf.binary()==(build/'vdot-perf.bin').read_bytes(),'ELF/BIN correspondence')
    g.require(elf.symbol_data('q_fault_probe')==struct.pack('<11I',*fixture_gen.PROBE_WORDS),'exact isolated fault probe')
    g.require(g.sha(build/'gemv-reference.o')==old.OBJECT_SHA,'complete fixed public object')
    refs=[g.ELF((build/'gemv-reference.o').read_bytes()),g.ELF(fixture_gen.raw(repo,str(fixture_gen.S0/'gemv-reference.o.gz'))),
          g.ELF(fixture_gen.raw(repo,str(fixture_gen.FIRST/'evidence/firstdot-v1/library/member-extract/stdout.log')))]
    certificates=[]
    for i,row in enumerate(fixture_gen.LEAVES):
        reference=refs[1 if i in (1,2) else 2 if i==4 else 0]
        certificates.append(fixture_gen.machine_certificate(reference.symbol_data(row[0]),elf.symbol_data(fixture_gen.NEW[i]),i))
    original,acc8=base.reference_images();fused=fused_reference();bodies={}
    for name in ('q288_full','split_measure',*fixture_gen.NEW):
        g.require(elf.symbol_data(name)==acc8.symbol_data(name),'unchanged complete acc8/timer/leaf body: '+name)
        bodies[name]=digest(elf.symbol_data(name))
    for name in ('q288_fused_vdot','q288_fused_rvv4'):
        g.require(elf.symbol_data(name)==fused.symbol_data(name),'unchanged screened fused body: '+name)
        bodies[name]=digest(elf.symbol_data(name))
    ref_words={n:refs[0].symbol_data(n).hex() for n in ('config_reuse_gemv_8x32_reuse_vdot','config_reuse_gemv_8x32_reuse_rvv')}
    fused_certs={kind:value_model.core_certificate(elf,ref_words,kind) for kind in ('vdot','rvv4')}
    arrays=compiled_arrays(elf,manifest);_,details=paths_for_plan(elf,manifest)
    expected=old.build_commands({k:v['path'] for k,v in record['toolchain'].items()},PurePosixPath(record['build_root']))
    g.require(len(record['commands'])==3,'build command inventory')
    for (label,argv),cmd in zip(expected,record['commands']):
        g.require(cmd.get('process_started') is True and cmd.get('exit_code')==0 and not cmd.get('timed_out') and
            cmd['command']==argv and cmd['cwd']==record['source_root'] and read(build/label/'command.json')==cmd and
            cmd['raw_sha256']=={n:g.sha(build/label/n) for n in ('stdout.log','stderr.log')},'actual build command evidence')
    compiled=compiler_commands((build/'make-command/stdout.log').read_text(),record)
    g.require(record['parent_identity_sha256']==parent.PARENT_IDENTITY_SHA and record['am_revision']==old.AM_COMMIT,'fixed parent/AM identity')
    return dict(status='FUSED_TARGET_ELF_DATASET_AND_TIMER_PATH_PASS',contract=CONTRACT,
        image_sha256=g.sha(build/'vdot-perf.bin'),certificates=certificates,fused_certificates=fused_certs,
        paths=details,unchanged_function_sha256=bodies,compiled_array_sha256=arrays,windows=12,full_q_calls=28,
        actual_compilation=compiled,runtime_not_run=True,performance_qualified=False)


def selection(samples,manifest):
    methods=[]
    for i,row in enumerate(manifest['rows']):
        ss=[s for s in samples if s['id']==i];wanted=4 if i==2 else 2
        g.require(len(ss)==wanted and all(s['cycles']>0 for s in ss),'all valid observations retained')
        methods.append(dict(id=i,label=row['label'],wrapper=row['wrapper'],leaf=row['leaf'],
                            cycles=[s['cycles'] for s in ss],instructions=[s['instructions'] for s in ss],
                            mean_cycles=sum(s['cycles'] for s in ss)/wanted))
    anchors=methods[2]['cycles'];context=100*max(anchors)<=101*min(anchors)
    gains=[]
    for candidate,baseline,label in ((3,0,'vdot-software-fusion'),(4,2,'rvv4-software-fusion')):
        after,before=methods[candidate]['cycles'],methods[baseline]['cycles']
        blocks=[]
        for block in range(2):
            a=[s['cycles'] for s in samples if s['id']==candidate and s['block']==block]
            b=[s['cycles'] for s in samples if s['id']==baseline and s['block']==block]
            blocks.append(dict(block=block,candidate=max(a),baseline_best=min(b),
                               reduction=1-max(a)/min(b),passed=200*max(a)<=199*min(b)))
        gains.append(dict(comparison=label,candidate=candidate,baseline=baseline,blocks=blocks,
            worst_candidate=max(after),best_baseline=min(before),worst_to_best_reduction=1-max(after)/min(before),
            separation_gate=200*max(after)<=199*min(before),qualified=context and 200*max(after)<=199*min(before)))
    rvv=[v for i in (1,2,4) for v in methods[i]['cycles']]
    fused_vdot=methods[3]['cycles'];fused_separation=200*max(fused_vdot)<=199*min(rvv)
    best_rvv=min((methods[i] for i in (1,2,4)),key=lambda m:(m['mean_cycles'],m['id']))
    eligible_vdot=[methods[i] for i in (0,3) if 200*max(methods[i]['cycles'])<=199*min(rvv)]
    vdot_separation=bool(eligible_vdot)
    chosen=min(eligible_vdot,key=lambda m:(m['mean_cycles'],m['id'])) if eligible_vdot else best_rvv
    return dict(decision='HOLD_CONTEXT_VARIATION' if not context else
                'VDOT_PREFERRED_IN_FIXED_PLAN' if vdot_separation else 'KEEP_RVV_EXPLICIT',
        methods=methods,anchors=anchors,anchor_gate=context,software_comparisons=gains,
        fused_vdot_vs_all_rvv=dict(worst_fused_vdot=max(fused_vdot),best_any_rvv=min(rvv),
            reduction=1-max(fused_vdot)/min(rvv),separation_gate=fused_separation,qualified=context and fused_separation),
        selected_id=chosen['id'] if context else None,selected_label=chosen['label'] if context else None,
        selected_method=chosen['wrapper'] if context else None,selected_leaf=chosen['leaf'] if context else None,
        eligible_vdot_ids=[m['id'] for m in eligible_vdot],comparison_gate_pass=context,
        stable_default_changed=False,pack_included=False,hardware_changed=False,
        statistical_scope='two fixed reverse-order method observations; all four AR4 points; replay is not an extra sample',
        application_scope='synthetic prepacked Q, one same-method selfwarm; only the named three-RVV set; no token/full-model claim')


def normal(repo,build,run,receipt):
    g.require(receipt.get('process_started') is True and receipt.get('exit_code')==0 and not receipt.get('timed_out'),'complete execution required')
    manifest=read(build/'source/manifest.json');stdout,stderr=((run/n).read_text() for n in ('stdout.log','stderr.log'))
    gate=g.load('fused_target_failure',repo/'team/optimizations/o1/audit/runtime_gate.py')
    fatal=g.load('fused_target_fatal',repo/'team/optimizations/o2/fullcore/recheck.py')
    observer=g.load('fused_target_protocol',repo/'team/optimizations/o2/fullcore/analyze.py')
    for stream in (stdout,stderr):gate.validate_failure_markers(stream);fatal.reject_fatal_output(stream)
    _,uart=observer.extract_events_and_uart(stderr+stdout);gate.validate_failure_markers(uart);fatal.reject_fatal_output(uart)
    plain=gate.normalize_console(uart)
    counter=g.load('fused_target_counter',repo/'team/workloads/unified-vdot/check.py')
    elf=g.ELF((build/'vdot-perf.elf').read_bytes());paths,details=paths_for_plan(elf,manifest)
    counter.walk=lambda path:path;events=counter.parse_events(stderr);samples=counter.trace_windows(events,manifest,paths)
    windows=[];current=None
    for event in events['RETIRE']:
        if event['word']==base.base.traced.START:current=[]
        if current is not None:current.append(event)
        if event['word']==base.base.traced.STOP:windows.append(current);current=None
    for records,step in zip(windows,manifest['plan']):
        stream=paths[step['index']];pos=0
        for event in records:
            covered=stream[pos:pos+event['count']]
            if event['count']>1:g.require(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered),'control hidden by ROB compression')
            pos+=event['count']
    for sample,step in zip(samples,manifest['plan']):
        sample.update({k:step[k] for k in ('dataset','block','role')});row=manifest['rows'][step['index']]
        sample.update(kind='Q',variant=row['variant'],label=row['label'],leaf=row['leaf'])
        g.require(sample['instructions']==details[str(row['id'])+':0']['expected_csr_instret'],'actual CSR instret vs exact complete path')
    expected=[f'Q_BEGIN contract={CONTRACT} windows=12','Q_FUNCTIONAL calls=28 controls=5 outputs=8064 warm=12 extra=4']
    expected += [f"Q_CALL {i} {c['stage']} {c['arm']} {c['dataset']}" for i,c in enumerate(manifest['call_plan'])]
    expected += [f"QW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['Q_END windows=12 full_calls=28 leaf_calls=5184 fused_calls=12 probe_dots=1 failures=0']
    actual=[line for line in plain.splitlines() if line.startswith(('Q_','QW '))]
    g.require(actual==expected and plain.count('HIT GOOD TRAP')==1,'complete UART/call-plan/counter/oracle evidence')
    analysis=observer.analyze(stderr+stdout)
    g.require(analysis['status']=='O2_TRACE_PASS' and analysis['schema']['slots']==2 and
        all(analysis.get(k)==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
        analysis['counts'].get('COMMIT')==103681,'complete O2 protocol and all-stage custom total')
    probe=elf.symbols['q_fault_probe'][0]+5*4
    expected_pcs=[probe];phases=[]
    for i,call in enumerate(manifest['call_plan']):
        pcs=[pc for pc,w in paths[call['arm']] if w&0xfe00707f==0x0200000b]
        phases.append(dict(seq=i,**call,vdot_count=len(pcs),first_commit_index=len(expected_pcs)))
        expected_pcs.extend(pcs)
    actual_pcs=[int(v,16) for v in re.findall(r'^O2_COMMIT [^\n]*pc=0x([0-9a-fA-F]+)',stderr,re.M)]
    g.require(actual_pcs==expected_pcs and len(actual_pcs)==103681,'entire functional/warm/timed custom PC sequence')
    g.require(len(events['COUNTER_ENQUEUE'])==len(events['CSR_SAMPLE'])==48,'exact counter event totals')
    return dict(status='FUSED_TARGET_DIFFTEST_AND_PLAN_PASS',contract=CONTRACT,windows=12,functional_calls=28,
        timed_q_calls=12,selfwarm_calls=12,extra_functional_calls=4,judge_fault_controls=5,
        committed_vdot=103681,timed_vdot=41472,custom_phases=phases,
        all_stage_custom_pc_sha256=digest(b''.join(struct.pack('<Q',p) for p in actual_pcs)),
        counter_enqueues=48,csr_samples=48,samples=samples,selection=selection(samples,manifest),
        hardware_changed=False,stable_default_changed=False,replay_and_archive_required_for_completion=True)


def build(repo,identity,out):
    with adapt(old,CONTRACT=CONTRACT,sources=sources,generate=generate,verification=verification):
        return old.build(repo,identity,out)


def run(repo,identity,build_dir,out,operation):
    with adapt(base.base.up,CONTRACT=CONTRACT,MAX_CYCLES=MAX_CYCLES,GENERATED=GENERATED,
               sources=sources,verification=verification,gen=SimpleNamespace(NEW=('q_fault_probe',)),normal=normal):
        return base.base.up.run(repo,identity,build_dir,out,operation)


def selector_control(manifest):
    # This is the concrete role-exclusion counterexample found in review.
    samples=[]
    for i,step in enumerate(manifest['plan']):
        arm=step['index'];cycle={0:110000,1:105000,2:100000,3:90000,4:99400}[arm]
        if arm==2 and step['role']=='anchor_end':cycle=99100
        samples.append(dict(seq=i,id=arm,cycles=cycle,instructions=1,block=step['block'],role=step['role']))
    result=selection(samples,manifest)
    g.require(result['anchor_gate'] and not result['software_comparisons'][1]['separation_gate'] and
              not result['software_comparisons'][1]['qualified'],'faster end anchor cannot be excluded from software gate')
    changed=[dict(s,cycles=97000 if s['id']==2 and s['role']=='anchor_end' else s['cycles']) for s in samples]
    held=selection(changed,manifest)
    g.require(held['decision']=='HOLD_CONTEXT_VARIATION' and held['selected_method'] is None and
              not any(v['qualified'] for v in held['software_comparisons']),'context failure blocks every software preference')
    adversarial=[dict(s,cycles=(80000 if s['block']==0 else 120000) if s['id']==0 else
                         101000 if s['id']==3 else 110000) for s in samples]
    eligible=selection(adversarial,manifest)
    g.require(eligible['fused_vdot_vs_all_rvv']['qualified'] and eligible['selected_id']==3 and
              eligible['decision']=='VDOT_PREFERRED_IN_FIXED_PLAN','qualify both vdot candidates before ranking by mean')
    return dict(status='ALL_FOUR_ANCHORS_AND_HOLD_REGRESSION_PASS',counterexample=result,
                failed_context_decision=held['decision'],qualified_before_ranking=eligible)


def elf_controls(build_dir,out):
    positive=verification(ROOT,build_dir);out.mkdir(parents=True,exist_ok=False)
    raw=(build_dir/'vdot-perf.elf').read_bytes();elf=g.ELF(raw);manifest=read(build_dir/'source/manifest.json')
    controls=[]
    for name,at,size,value in (('q_wrappers',0,8,elf.symbols['q288_fused_vdot'][0]),
                              ('q_order',4,4,3),('q_functional_datasets',0,4,0),
                              ('q_golden',0,4,1),('q_packed',16,1,1)):
        body=elf.symbol_data(name);offset=raw.find(body)
        g.require(offset>=0 and raw.find(body,offset+1)<0,'unique array mutation region')
        changed=bytearray(raw);changed[offset+at:offset+at+size]=value.to_bytes(size,'little')
        g.require(bytes(changed)!=raw,'nonempty actual target array mutation')
        (out/(name+'.elf')).write_bytes(changed)
        try:compiled_arrays(g.ELF(bytes(changed)),manifest)
        except ValueError as error:
            g.require(str(error)=='compiled array: '+name,'specific target array rejection')
            controls.append(dict(name=name,pc=None,file_offset=offset+at,mutated_elf_sha256=digest(changed),error=str(error)))
        else:raise ValueError('actual target array mutant accepted: '+name)
    for arm in (3,4):
        row=manifest['rows'][arm];body=elf.symbol_data(row['wrapper']);offset=raw.find(body)
        g.require(offset>=0 and raw.find(body,offset+1)<0,'unique fused function mutation region')
        words=[w for w, in struct.iter_unpack('<I',body)]
        at=next(i for i,w in enumerate(words) if w&127==0x57 and w>>26==0x24 and (w>>12)&7==1)
        changed=bytearray(raw);struct.pack_into('<3I',changed,offset+4*at,words[at+1],words[at+2],words[at])
        label=row['label']+'-rounding-order';(out/(label+'.elf')).write_bytes(changed)
        try:path(g.ELF(bytes(changed)),row,fixture_gen.fixtures(),0)
        except ValueError as error:
            g.require(str(error)=='actual ELF full-Q bitwise output','specific target numeric/order rejection')
            controls.append(dict(name=label,pc=hex(elf.symbols[row['wrapper']][0]+4*at),
                file_offset=offset+4*at,mutated_elf_sha256=digest(changed),error=str(error)))
        else:raise ValueError('target rounding-order mutant accepted')
    result=dict(status='FUSED_TARGET_ACTUAL_ELF_CONTROLS_PASS',contract=CONTRACT,positive=positive,
                controls=controls,selector_regression=selector_control(manifest),new_emu_runs=0)
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
