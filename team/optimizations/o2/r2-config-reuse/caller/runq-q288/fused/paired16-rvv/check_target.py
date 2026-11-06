"""Bind four actual functions, fixed inputs, one fullmin call, and ten windows.

The existing counter and O2 parsers are unchanged. Runtime analysis is serial;
the extra fullmin case is functional evidence, never a performance sample.
"""
from pathlib import Path
import argparse
import json
import re
import struct
import sys
import tempfile

import generate
import screen
import target

need,sha,save=generate.need,generate.sha,target.save
START,STOP=0x51300013,0x51400013
COUNTERS=(0xc0202773,0xc0002873,0xc00028f3,0xc02027f3)
PAIRED_SCREEN_ELF='fb3c030efa7aa347029a69f6aabe82c912cbbb85294b27cf407a01ea58a314f3'
PAIRED_SCREEN_RESULT='6a9e418223ad9b44235f5b4216419288e0d9f6302dfdfed0295e1d26130b5fa0'
GS32_SCREEN_ELF='8316e32939385653c1c4f7e257443529c19dc71df8b5991552a2ab1453069daa'
TIMER_REFERENCE='610c499f46f1fe73074f626d8990bdcbdbc5f78c30ce8fc4a835495b0e392faa'


def read(path):
    return json.loads(path.read_text())


def support(repo):
    modules=target.gs32_modules(repo)
    base=modules['check_target']
    model,qgen,(gs32,tail,fr)=base.support(repo)
    paired_model,helpers=screen.support(repo)
    paired,_=screen.machine_class(repo,paired_model)
    return dict(base=base,model=model,qgen=qgen,helpers=helpers,
                classes=(paired,gs32,tail,fr),modules=modules)


def helper(repo,relative):
    base=target.gs32_modules(repo)['check_target']
    return base.helper(repo,relative)


def expected_calls():
    calls=[dict(stage=0,arm=a,dataset=d) for a,d in
           zip(target.FUNCTIONAL_ORDER,target.FUNCTIONAL_DATASETS)]
    calls.append(dict(stage=0,arm=0,dataset=target.FULLMIN_DATASET))
    for arm in target.ORDER:
        calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    return calls


def arrays(elf,manifest,ctx):
    qgen=ctx['qgen']
    fixture=qgen.fixtures()
    _,min_golden=target.fullmin_fixture(ctx['model'],ctx['helpers'],qgen)
    guard=struct.pack('<2Q',target.GUARD,target.GUARD)
    pack=lambda values,code:struct.pack('<'+str(len(values))+code,*values)
    wanted={
        'q_weights':qgen.bytes8(fixture['weight']),
        'q_weight_scale':qgen.bytes32(fixture['weight_scale']),
        'q_inputs':b''.join(qgen.bytes8(v) for v in fixture['inputs']),
        'q_input_scale':b''.join(qgen.bytes32(v) for v in fixture['input_scale']),
        'q_golden':b''.join(qgen.bytes32(v) for v in fixture['golden']),
        'q_packed':guard+qgen.bytes8(fixture['packed'])+guard,
        'q_min_packed':guard+bytes([128])*82944+guard,
        'q_min_x':guard+bytes([128])*288+guard,
        'q_min_golden':pack(min_golden,'I'),
        'q_order':pack(target.ORDER,'I'),'q_methods':pack(target.METHODS,'I'),
        'q_functional_order':pack(target.FUNCTIONAL_ORDER,'I'),
        'q_functional_datasets':pack(target.FUNCTIONAL_DATASETS,'I'),
        'q_wrappers':pack([elf.symbols[n][0] for n in target.WRAPPERS],'Q'),
        'split_entries':pack([elf.symbols[n][0] for n in qgen.NEW],'Q'),
        'q_fault_probe':pack(qgen.PROBE_WORDS,'I'),
    }
    for name,raw in wanted.items():
        need(elf.symbol_data(name)==raw,'compiled array: '+name)
    need(manifest['contract']==target.CONTRACT and manifest['call_plan']==expected_calls(),
         'exact four-arm contract and 29-call plan')
    need(tuple(s['index'] for s in manifest['plan'])==target.ORDER,
         'all ten windows and four FR anchors')
    need(manifest['full_q_calls']==29 and manifest['expected_dots']==62209 and
         manifest['explicit_functional_calls']==9 and manifest['warmup_calls']==10 and
         manifest['timed_q_calls']==10,'bounded full-Q and custom counts')
    need(manifest['fullmin']==dict(dataset=3,arm=0,performance_sample=False,weight=-128,input=-128,
         group_dot=524288,scale_dataset=0,output_sha256=target.FULLMIN_OUTPUT_SHA),
         'explicit untimed fullmin identity')
    need(len(manifest['rows'])==4,'four method rows')
    for arm,row in enumerate(manifest['rows']):
        need(row['id']==arm and row['wrapper']==target.WRAPPERS[arm] and
             row['algorithm']==target.METHODS[arm] and row['leaf']==qgen.NEW[target.METHODS[arm]] and
             row['method']==('vdot' if arm==2 else 'rvv') and row['dots']==(10368 if arm==2 else 0),
             'exact arm metadata')
    need(manifest['anchor_threshold_ratio']==[101,100] and
         manifest['separation_threshold_ratio']==[199,200],'frozen comparison thresholds')
    return {name:sha(raw) for name,raw in wanted.items()}


def paths(repo,elf,manifest,ctx):
    fixture=ctx['qgen'].fixtures()
    body=elf.symbol_data('split_measure')
    begin=elf.symbols['split_measure'][0]
    timer=[(begin+4*i,w) for i,(w,) in enumerate(struct.iter_unpack('<I',body))]
    need([i for i,(_,w) in enumerate(timer) if w==START]==[11] and
         [i for i,(_,w) in enumerate(timer) if w==STOP]==[26] and timer[20][1]==0x000a00e7,
         'unchanged timer marker and call sites')
    addr=lambda name:elf.symbols[name][0]
    streams,details,function_paths={},{},{}
    jobs=[(arm,dataset) for arm in range(4) for dataset in range(3)]+[(0,3)]
    for arm,dataset in jobs:
        is_min=dataset==3
        data,golden=target.fullmin_fixture(ctx['model'],ctx['helpers'],ctx['qgen']) if is_min else (
            fixture,fixture['golden'][dataset])
        actual_dataset=0 if is_min else dataset
        row=manifest['rows'][arm]
        machine=ctx['classes'][arm](data,actual_dataset,poison=0x1616288+arm*4+dataset)
        machine.addresses=dict(packed=addr('q_min_packed' if is_min else 'q_packed')+16,
            x=addr('q_min_x')+16 if is_min else addr('q_inputs')+288*dataset,
            ws=addr('q_weight_scale'),xs=addr('q_input_scale')+36*actual_dataset,
            y=addr('q_output')+16,slots=addr('q_slots')+16,context=addr('q_context'))
        machine.regions['context']=bytearray(struct.pack('<7Q',
            *(machine.addresses[n] for n in ('packed','x','ws','xs','y','slots')),addr(row['leaf'])))
        machine.original['context']=bytes(machine.regions['context'])
        machine.halt=timer[21][0]
        machine.x[1],machine.x[2]=machine.halt,0x87fff000-48
        machine.x[8]=machine.x[10]=addr('q_context')
        machine.x[9],machine.x[20]=addr('q_measurement'),addr(row['wrapper'])
        machine.saved={i:machine.x[i] for i in machine.saved}
        machine.execute_function(elf,row['wrapper'])
        if arm in (0,1):
            detail=machine.check_candidate(golden)
        elif arm==2:
            detail=machine.check(golden)
        else:
            detail=machine.check_full('rvv4',golden)
        key=f'{arm}:{dataset}'
        function_paths[key]=machine.path
        common=dict(detail,dataset=dataset,function_instructions=len(machine.path),
            function_path_sha256=sha(b''.join(struct.pack('<QI',pc,w) for pc,w in machine.path)),
            function_elf_addresses=True)
        if is_min:
            need(detail['path']=='fallback' and detail['wrapped_lanes']==0,
                 'fullmin takes complete safe fallback in actual-ELF host model')
            details[key]=dict(common,performance_sample=False,
                evidence_scope='host model of linked function; target functional verdict is separate',
                full_function_return_context='synthetic ABI state, not a recorded untimed guest callsite')
            continue
        stream=timer[11:21]+machine.path+timer[21:27]
        positions=[i for i,(_,w) in enumerate(stream) if w in COUNTERS]
        need([stream[i][1] for i in positions]==list(COUNTERS),'four counter sites in order')
        if dataset==0:
            streams[arm]=stream
        details[key]=dict(common,marker_instructions=len(stream),
            expected_csr_instret=positions[3]-positions[0],
            path_sha256=sha(b''.join(struct.pack('<QI',pc,w) for pc,w in stream)))
    need(set(streams)==set(range(4)),'dataset0 timed path for each actual arm')
    return streams,details,function_paths


def fullmin_oracle(repo,ctx):
    q=repo/generate.REL.parent
    headers={'q288.h':q/'q288.h','caller.h':q.parent/'caller.h','split.h':q.parent/'split/split.h'}
    with tempfile.TemporaryDirectory(prefix='paired16-fullmin-oracle-') as temporary:
        lib=ctx['helpers'].oracle_library(q/'oracle.c',headers,Path(temporary)/'oracle')
        fixture,golden=target.fullmin_fixture(ctx['model'],ctx['helpers'],ctx['qgen'])
        need(ctx['helpers'].native_golden(lib,fixture,0)==golden,'independent C/Python fullmin target golden')
    return dict(output_sha256=target.FULLMIN_OUTPUT_SHA,group_dot=524288,
        slots_sha256=sha((struct.pack('<I',524288)+bytes(12))*8),independent_c_python_equal=True)


def verify(repo,build,paired_elf,paired_result,gs32_elf,gs32_result,timer_reference):
    ctx=support(repo)
    record=read(build/'build.json')
    elf=ctx['model'].ELF((build/'paired16-target.elf').read_bytes())
    need(record['contract']==target.CONTRACT and record['elf_sha256']==sha(elf.raw) and
         record['bin_sha256']==sha((build/'paired16-target.bin').read_bytes()),'recorded target build bytes')
    need(ctx['base'].binary(elf)==(build/'paired16-target.bin').read_bytes(),'complete ELF/BIN correspondence')
    for path,pin in record['immutable_am_inputs'].items():
        need(sha(Path(path).read_bytes())==pin,'immutable AM input '+path)
    producer_files={}
    for path,pin in read(build/'source/producer-inputs.json').items():
        source=Path(path)
        relative=source.relative_to(repo).as_posix()
        payload=ctx['qgen'].raw(repo,relative) if relative in ctx['qgen'].INPUT_PINS else source.read_bytes()
        if relative in ctx['qgen'].INPUT_PINS:
            need(pin==ctx['qgen'].INPUT_PINS[relative],'unchanged parent decoded-payload pin')
        need(sha(payload)==pin,'frozen producer input '+path)
        producer_files[relative]=dict(physical_sha256=sha(source.read_bytes()),payload_sha256=pin)
    p,g=read(paired_result),read(gs32_result)
    need(sha(paired_elf.read_bytes())==PAIRED_SCREEN_ELF==p['elf_sha256'] and
         sha(paired_result.read_bytes())==PAIRED_SCREEN_RESULT and
         p['status']=='PAIRED16_ACTUAL_ELF_NUMERIC_PASS' and len(p['numeric']['cases'])==19 and
         len(p['controls'])==6,'bound paired16 screened ELF and result')
    need(sha(gs32_elf.read_bytes())==GS32_SCREEN_ELF==g['elf_sha256'] and
         g['status']=='GS32_ACTUAL_ELF_NUMERIC_PASS' and len(g['numeric']['cases'])==8 and
         len(g['controls'])==6,'bound screened GS32v2 actual ELF and result')
    bodies={}
    for name,path in ((generate.NAME,paired_elf),('q288_gs32_rvv',gs32_elf)):
        screened=ctx['model'].ELF(path.read_bytes())
        need(elf.symbol_data(name)==screened.symbol_data(name),'complete screened function '+name)
        bodies[name]=sha(elf.symbol_data(name))
    for name,pin in target.FUNCTION_PINS.items():
        need(sha(elf.symbol_data(name))==pin,'unchanged qualified function '+name)
        bodies[name]=pin
    need(sha(timer_reference.read_bytes())==TIMER_REFERENCE,'fixed prior timer ELF')
    timer_elf=ctx['model'].ELF(timer_reference.read_bytes())
    need(elf.symbol_data('split_measure')==timer_elf.symbol_data('split_measure'),'unchanged complete timer')
    bodies['split_measure']=sha(elf.symbol_data('split_measure'))
    with tempfile.TemporaryDirectory(prefix='paired16-target-verify-') as temporary:
        fresh=Path(temporary)/'source'
        target.produce(repo,fresh)
        for path in fresh.iterdir():
            if path.name=='producer-inputs.json':
                continue
            need(path.is_file() and path.read_bytes()==(build/'source'/path.name).read_bytes(),
                 'source regeneration '+path.name)
    manifest=read(build/'source/manifest.json')
    bound_arrays=arrays(elf,manifest,ctx)
    streams,details,_=paths(repo,elf,manifest,ctx)
    controls=[]
    for name in ('q_wrappers','q_order','q_golden','q_packed','q_min_x','q_min_golden'):
        raw=bytearray(elf.raw)
        offset=elf.symbols[name][2]+(16 if name in ('q_packed','q_min_x') else 0)
        raw[offset]^=1
        try:
            arrays(ctx['model'].ELF(raw),manifest,ctx)
        except ValueError as error:
            need(str(error)=='compiled array: '+name,'specific target array rejection')
            controls.append(dict(name=name,offset=offset,error=str(error),mutant_sha256=sha(raw)))
        else:
            raise ValueError('target array mutation accepted: '+name)
    return dict(status='PAIRED16_TARGET_ELF_DATASET_TIMER_PATH_PASS',contract=target.CONTRACT,
        elf_sha256=sha(elf.raw),bin_sha256=sha(ctx['base'].binary(elf)),function_sha256=bodies,
        compiled_array_sha256=bound_arrays,paths=details,array_controls=controls,
        fullmin_oracle=fullmin_oracle(repo,ctx),producer_files=producer_files,
        producer_inventory_sha256=sha((build/'source/producer-inputs.json').read_bytes()),
        manifest_sha256=sha((build/'source/manifest.json').read_bytes()),
        paired_screened_elf_sha256=PAIRED_SCREEN_ELF,paired_numeric_result_sha256=PAIRED_SCREEN_RESULT,
        gs32_screened_elf_sha256=GS32_SCREEN_ELF,gs32_numeric_result_sha256=sha(gs32_result.read_bytes()),
        windows=10,full_q_calls=29,target_runtime_qualified=False,performance_qualified=False)


def selection(samples,manifest):
    methods=[]
    for arm,row in enumerate(manifest['rows']):
        observations=[s for s in samples if s['id']==arm]
        need(len(observations)==(4 if arm==3 else 2) and all(s['cycles']>0 for s in observations),
             'all method observations retained')
        cycles=[s['cycles'] for s in observations]
        methods.append(dict(id=arm,wrapper=row['wrapper'],cycles=cycles,
            instructions=[s['instructions'] for s in observations],mean_cycles=sum(cycles)/len(cycles)))
    anchors=methods[3]['cycles']
    context=100*max(anchors)<=101*min(anchors)
    comparisons=[]
    for baseline in (1,2,3):
        candidate,before=methods[0]['cycles'],methods[baseline]['cycles']
        gate=200*max(candidate)<=199*min(before)
        comparisons.append(dict(candidate=0,baseline=baseline,worst_candidate=max(candidate),
            best_baseline=min(before),reduction=1-max(candidate)/min(before),
            separation_gate=gate,qualified=context and gate))
    promote=context and all(c['qualified'] for c in comparisons)
    return dict(decision='HOLD_CONTEXT_VARIATION' if not context else
        'PAIRED16_PREFERRED_IN_FIXED_PLAN' if promote else 'KEEP_EXISTING_ENTRY',
        methods=methods,anchors=anchors,anchor_gate=context,comparisons=comparisons,
        candidate_qualified=promote,stable_default_changed=False,hardware_changed=False,
        statistical_scope='two reversed P/G/TA observations and four FR anchors; replay is not an extra sample',
        application_scope='synthetic prepacked Q288 dataset0 fast path with selfwarm; fullmin is untimed functionality')


def analyze(repo,build,run,receipt):
    need(receipt['process_started'] and receipt['exit_code']==0 and not receipt['timed_out'],
         'complete normal target run')
    stdout,stderr=((run/name).read_text() for name in ('stdout.log','stderr.log'))
    ctx=support(repo)
    base=ctx['base']
    gate=base.helper(repo,'team/optimizations/o1/audit/runtime_gate.py')
    fatal=base.helper(repo,'team/optimizations/o2/fullcore/recheck.py')
    observer=base.helper(repo,'team/optimizations/o2/fullcore/analyze.py')
    for text in (stdout,stderr):
        gate.validate_failure_markers(text)
        fatal.reject_fatal_output(text)
    _,uart=observer.extract_events_and_uart(stderr+stdout)
    gate.validate_failure_markers(uart)
    fatal.reject_fatal_output(uart)
    plain=gate.normalize_console(uart)
    elf=ctx['model'].ELF((build/'paired16-target.elf').read_bytes())
    manifest=read(build/'source/manifest.json')
    arrays(elf,manifest,ctx)
    streams,details,function_paths=paths(repo,elf,manifest,ctx)
    counter=base.helper(repo,'team/workloads/unified-vdot/check.py')
    counter.walk=lambda path:path  # supply already expanded actual-ELF PC/word paths
    events=counter.parse_events(stderr)
    samples=counter.trace_windows(events,manifest,streams)
    windows,current=[],None
    for event in events['RETIRE']:
        if event['word']==START:
            need(current is None,'non-nested counter window')
            current=[]
        if current is not None:
            current.append(event)
        if event['word']==STOP:
            need(current is not None,'counter stop inside a window')
            windows.append(current)
            current=None
    need(current is None and len(windows)==len(samples)==10,'ten complete measured windows')
    for records,step,sample in zip(windows,manifest['plan'],samples):
        stream,pos=streams[step['index']],0
        for event in records:
            covered=stream[pos:pos+event['count']]
            if event['count']>1:
                need(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered),
                     'no hidden compressed control flow')
            pos+=event['count']
        need(pos==len(stream),'complete exact marker path')
        sample.update({k:step[k] for k in ('dataset','block','role')})
        need(sample['instructions']==details[str(step['index'])+':0']['expected_csr_instret'],
             'CSR/event/ELF complete instruction count')
    expected=[f'Q_BEGIN contract={target.CONTRACT} windows=10',
              'Q_MIN checked=1 outputs=288 slots=8',
              'Q_FUNCTIONAL calls=29 controls=5 outputs=8352 warm=10 extra=9']
    expected += [f"Q_CALL {i} {c['stage']} {c['arm']} {c['dataset']}" for i,c in enumerate(manifest['call_plan'])]
    expected += [f"QW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['Q_END windows=10 full_calls=29 leaf_calls=0 inline_calls=29 probe_dots=1 failures=0']
    need([line for line in plain.splitlines() if line.startswith(('Q_','QW '))]==expected and
         plain.count('HIT GOOD TRAP')==1,'complete UART/call/oracle/guard/CSR evidence')
    protocol=observer.analyze(stderr+stdout)
    need(protocol['status']=='O2_TRACE_PASS' and protocol['schema']['slots']==2 and
         all(protocol.get(k)==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
         protocol['counts'].get('COMMIT')==62209,'complete custom protocol and count')
    expected_pcs=[elf.symbols['q_fault_probe'][0]+20]
    for call in manifest['call_plan']:
        expected_pcs += [pc for pc,w in function_paths[f"{call['arm']}:{call['dataset']}"]
                         if w&0xfe00707f==0x0200000b]
    actual_pcs=[int(value,16) for value in re.findall(r'^O2_COMMIT [^\n]*pc=0x([0-9a-fA-F]+)',stderr,re.M)]
    need(actual_pcs==expected_pcs and len(actual_pcs)==62209,
         'entire functional/warm/timed custom PC sequence')
    return dict(status='PAIRED16_TARGET_DIFFTEST_COUNTER_PATH_PASS',contract=target.CONTRACT,
        windows=10,full_q_calls=29,judge_fault_controls=5,outputs_checked=8352,
        fullmin_functional_pass=True,fullmin_performance_sample=False,fullmin_retirement_trace_claim=False,
        committed_vdot=62209,all_stage_custom_pc_sha256=sha(b''.join(struct.pack('<Q',pc) for pc in actual_pcs)),
        samples=samples,selection=selection(samples,manifest),protocol=protocol,
        runtime_qualified=True,full_application_performance_qualified=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','build','paired-elf','paired-result','gs32-elf','gs32-result','timer-reference','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    sys.dont_write_bytecode=True
    need(not args.output.exists(),'fresh target verification report')
    result=verify(args.repo.resolve(),args.build.resolve(),args.paired_elf.resolve(),args.paired_result.resolve(),
                  args.gs32_elf.resolve(),args.gs32_result.resolve(),args.timer_reference.resolve())
    save(args.output,result)
    print(json.dumps(dict(status=result['status'],elf_sha256=result['elf_sha256'],
        instructions={key:value.get('expected_csr_instret') for key,value in result['paths'].items()},
        fullmin=result['fullmin_oracle']),indent=2))
