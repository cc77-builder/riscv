"""Strict runq Q consumer adapter over the unchanged team build/runtime engine."""
from pathlib import Path, PurePosixPath
from contextlib import contextmanager
import argparse
import importlib.util
import json
import os
import re
import shlex
import struct
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
PARENT_DIR=HERE.parent/'split'
spec=importlib.util.spec_from_file_location('runq_split_engine',PARENT_DIR/'run.py')
up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
g,parent,old=up.g,up.parent,up.old
BASE_SOURCES=old.sources
sys.path.insert(0,str(HERE))
gen=g.load('runq_generator',HERE/'generate.py')
traced=g.load('runq_trace',HERE/'trace.py')
CONTRACT,MAX_CYCLES,GENERATED=gen.CONTRACT,gen.MAX_CYCLES,gen.FILES
OWN=('q288.h','q288.c','oracle.c','main.c','generate.py','trace.py','run.py','check.py','CONTRACT.md','LICENSE.llama2-c')
read,now,digest=old.read,old.now,old.digest


def sources(repo):
    g.require(repo==ROOT,'selected runq source root')
    found=BASE_SOURCES(repo)
    names=set(read(PARENT_DIR/'dependencies.json'))|set(gen.INPUT_PINS)
    names|={str(gen.CONFIG/'caller/split'/n) for n in up.OWN}
    names|={str(gen.REL/n) for n in OWN}
    # The frozen S1 gate reads this model during import and pins its content;
    # older caller manifests omitted it because a full checkout hid the gap.
    names.add('team/optimizations/o2/r2-safe-tail/machine_model.py')
    names.add(str(gen.CONFIG/'evidence/runtime-v1/library/gemv.o'))
    found.update({p:g.sha(repo/p) for p in sorted(names)})
    return found


def generate(repo,out):
    return gen.generate(repo,out)


@contextmanager
def adapt(module,**values):
    before={k:getattr(module,k) for k in values}
    try:
        for k,v in values.items():setattr(module,k,v)
        yield
    finally:
        for k,v in before.items():setattr(module,k,v)


def compiler_commands(log,record):
    root=PurePosixPath(record['build_root']);gcc=record['toolchain']['gcc']['path']
    lines=[shlex.split(s) for s in log.splitlines() if s.startswith(gcc+' ')]
    result={}
    for name in ('main','q288','oracle'):
        src=str(root/'source'/(name+'.c'));obj=str(root/'objects'/(name+'.o'))
        found=[line for line in lines if src in line]
        g.require(len(found)==1,'one real separate C command: '+name)
        cmd=found[0]
        g.require(cmd[-4:]==['-c','-o',obj,src] and all(cmd.count(flag)==1 for flag in old.C_REQUIRED+('-ffp-contract=off','-fno-fast-math')),
                  'actual C flags/source/output: '+name)
        forbidden={'-flto','-fipa-cp','-fipa-icf','-foptimize-sibling-calls','-ftree-vectorize',
                   '-ftree-slp-vectorize','-ftree-loop-distribute-patterns','-mrelax','-ffast-math','-fassociative-math'}
        g.require(not any(arg.split('=',1)[0] in forbidden or arg.startswith('@') or
            (arg.startswith('-march=') and arg!='-march=rv64gv') or
            (arg.startswith('-mabi=') and arg!='-mabi=lp64d') or
            (arg.startswith('-ffp-contract=') and arg!='-ffp-contract=off') or
            (re.match(r'-O',arg) and arg!='-O2') for arg in cmd),'conflicting C option: '+name)
        g.require(not any('HOST' in arg for arg in cmd),'no host substitutions in target build')
        result[name]=cmd
    return result

def verification(repo,build):
    record=read(build/'build.json')
    g.require(record['contract']==CONTRACT and record['software_files']==sources(repo) and record['exit_code']==0,
              'split build identity')
    for rel,pin in record['software_files'].items():
        g.require(g.sha(build/'source/repo'/rel)==pin,'snapshot drift: '+rel)
    g.require(set(record['artifacts'])=={'vdot-perf.elf','vdot-perf.bin','gemv-reference.o'},'artifact inventory')
    for name,pin in record['artifacts'].items():g.require(g.sha(build/name)==pin,'artifact drift')
    with tempfile.TemporaryDirectory(prefix='runq-regenerate-') as tmp:
        fresh=Path(tmp)/'source';manifest=generate(repo,fresh)
        for name in GENERATED:g.require((fresh/name).read_bytes()==(build/'source'/name).read_bytes(),'source regeneration: '+name)
    elf=g.ELF((build/'vdot-perf.elf').read_bytes())
    executable=g.load('split_executable',repo/'team/optimizations/o2/r2-select/entry_c_api.py')
    executable.executable(elf)
    g.require(elf.binary()==(build/'vdot-perf.bin').read_bytes(),'ELF/BIN mismatch')
    g.require(g.sha(build/'gemv-reference.o')==old.OBJECT_SHA,'old full reference object differs')
    refs=[g.ELF((build/'gemv-reference.o').read_bytes()),
          g.ELF(gen.raw(repo,str(gen.S0/'gemv-reference.o.gz'))),
          g.ELF(gen.raw(repo,str(gen.FIRST/'evidence/firstdot-v1/library/member-extract/stdout.log')))]
    certs=[]
    for i,row in enumerate(gen.LEAVES):
        name=row[0];reference=refs[1 if i in (1,2) else 2 if i==4 else 0]
        before=reference.symbol_data(name)
        certs.append(gen.machine_certificate(before,elf.symbol_data(gen.NEW[i]),i))
    fixture=gen.fixtures()
    compiled_arrays={
        'q_weights':gen.bytes8(fixture['weight']),
        'q_weight_scale':gen.bytes32(fixture['weight_scale']),
        'q_inputs':b''.join(gen.bytes8(x) for x in fixture['inputs']),
        'q_input_scale':b''.join(gen.bytes32(x) for x in fixture['input_scale']),
        'q_golden':b''.join(gen.bytes32(x) for x in fixture['golden']),
        'q_group_dots':gen.bytes32([v&0xffffffff for v in fixture['group_dots'][0]]),
        'q_order':struct.pack('<16I',*(s['index'] for s in manifest['plan'][1:])),
        'split_entries':struct.pack('<6Q',*(elf.symbols[n][0] for n in gen.NEW)),
    }
    for name,raw in compiled_arrays.items():g.require(elf.symbol_data(name)==raw,'compiled array: '+name)
    paths={}
    for row in manifest['rows']:
        path,detail=traced.path(elf,row,fixture)
        paths[str(row['id'])]=dict(detail,path_sha256=digest(b''.join(struct.pack('<QI',pc,w) for pc,w in path)))
    commands=record['commands']
    expected=old.build_commands({k:v['path'] for k,v in record['toolchain'].items()},PurePosixPath(record['build_root']))
    g.require(len(commands)==3,'build commands inventory')
    for (label,argv),cmd in zip(expected,commands):
        g.require(cmd.get('process_started') is True and cmd.get('exit_code')==0 and not cmd.get('timed_out') and
                  cmd['command']==argv and cmd['cwd']==record['source_root'] and read(build/label/'command.json')==cmd and
                  cmd['raw_sha256']=={n:g.sha(build/label/n) for n in ('stdout.log','stderr.log')},'actual build command evidence')
    compiled=compiler_commands((build/'make-command/stdout.log').read_text(),record)
    g.require(record['parent_identity_sha256']==parent.PARENT_IDENTITY_SHA and record['am_revision']==old.AM_COMMIT,
              'fixed parent/AM identity')
    return dict(status='RUNQ_Q288_ELF_ADDRESS_AND_CALL_PATH_PASS',contract=CONTRACT,image_sha256=g.sha(build/'vdot-perf.bin'),
                certificates=certs,paths=paths,windows=len(manifest['plan']),actual_c_compilation=compiled,
                source_scope='full 288x288 Q; strict grouped FP; one-time weight pack separately timed',runtime_not_run=True)

def selection(samples,manifest):
    formal=[s for s in samples if s['kind']=='Q']
    anchors=[s['cycles'] for s in formal if s['role'].startswith('anchor')]
    g.require(len(anchors)==4 and all(c>0 for c in anchors),'four positive anchors')
    context=100*max(anchors)<=101*min(anchors)
    blocks=[]
    for b in range(2):
        ss=[s for s in formal if s['block']==b and s['role']=='method']
        g.require(len(ss)==6 and {s['id'] for s in ss}==set(range(6)),'method coverage')
        vd=next(s['cycles'] for s in ss if s['id']==0)
        rv=min((s for s in ss if s['id']!=0),key=lambda s:(s['cycles'],s['id']))
        blocks.append(dict(block=b,vdot=vd,fastest_rvv_id=rv['id'],fastest_rvv=rv['cycles'],
                           reduction=1-vd/rv['cycles'],passed=200*vd<=199*rv['cycles']))
    vds=[s['cycles'] for s in formal if s['role']=='method' and s['id']==0]
    rvvs=[s['cycles'] for s in formal if s['role']=='method' and s['id']!=0]
    separated=200*max(vds)<=199*min(rvvs)
    methods=[]
    for i in range(6):
        ss=[s for s in formal if s['role']=='method' and s['id']==i]
        methods.append(dict(id=i,leaf=manifest['rows'][i]['leaf'],cycles=[s['cycles'] for s in ss],
                            instructions=[s['instructions'] for s in ss],total=sum(s['cycles'] for s in ss)))
    winner=min(methods[1:],key=lambda m:(m['total'],m['id']))
    decision='HOLD_CONTEXT_VARIATION' if not context else 'VDOT_PREFERRED_IN_FIXED_PLAN' if separated else 'KEEP_RVV_EXPLICIT'
    return dict(decision=decision,methods=methods,anchors=anchors,anchor_gate=context,blocks=blocks,
                worst_vdot=max(vds),best_any_rvv=min(rvvs),global_separation_gate=separated,
                fastest_rvv=winner['leaf'],selected_method=None if not context else gen.NEW[0] if separated else winner['leaf'],
                pack_cycles=samples[0]['cycles'],pack_instructions=samples[0]['instructions'],
                stable_default_changed=False,statistical_scope='two fixed-order observations; replay is not an extra sample',
                application_scope='prequantized Q projection with synthetic inputs; no token/full-model claim')


def normal(repo,build,run,receipt):
    g.require(receipt.get('process_started') is True and receipt.get('exit_code')==0 and not receipt.get('timed_out'),'complete execution required')
    manifest=read(build/'source/manifest.json')
    stdout,stderr=((run/n).read_text() for n in ('stdout.log','stderr.log'))
    gate=g.load('split_failures',repo/'team/optimizations/o1/audit/runtime_gate.py')
    fatal=g.load('split_fatal',repo/'team/optimizations/o2/fullcore/recheck.py')
    observer=g.load('split_protocol',repo/'team/optimizations/o2/fullcore/analyze.py')
    for stream in (stdout,stderr):gate.validate_failure_markers(stream);fatal.reject_fatal_output(stream)
    _,uart=observer.extract_events_and_uart(stderr+stdout)
    gate.validate_failure_markers(uart);fatal.reject_fatal_output(uart)
    plain=gate.normalize_console(uart)
    counter=g.load('split_counters',repo/'team/workloads/unified-vdot/check.py')
    elf=g.ELF((build/'vdot-perf.elf').read_bytes())
    fixture=gen.fixtures()
    paths={row['id']:traced.path(elf,row,fixture)[0] for row in manifest['rows']}
    counter.walk=lambda path:path
    events=counter.parse_events(stderr);samples=counter.trace_windows(events,manifest,paths)
    windows=[];current=None
    for event in events['RETIRE']:
        if event['word']==traced.START:current=[]
        if current is not None:current.append(event)
        if event['word']==traced.STOP:windows.append(current);current=None
    for records,step in zip(windows,manifest['plan']):
        path=paths[step['index']];pos=0
        for event in records:
            covered=path[pos:pos+event['count']]
            if event['count']>1:g.require(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered),'control hidden by ROB compression')
            pos+=event['count']
    for sample,step in zip(samples,manifest['plan']):
        sample.update({k:step[k] for k in ('dataset','block','role')})
        sample['kind']=manifest['rows'][step['index']]['kind']
    expected=[f"Q_BEGIN contract={CONTRACT} windows=17",'Q_FUNCTIONAL calls=8 controls=6 groups=2592','Q_WARMUP calls=6']
    expected += [f"QW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['Q_END windows=17 full_calls=46 leaf_calls=15229 failures=0']
    actual=[line for line in plain.splitlines() if line.startswith(('Q_','QW '))]
    g.require(actual==expected and plain.count('HIT GOOD TRAP')==1,'raw UART/counter/oracle evidence differs')
    analysis=observer.analyze(stderr+stdout)
    g.require(analysis['status']=='O2_TRACE_PASS' and analysis['schema']['slots']==2 and
        all(analysis.get(k)==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
        analysis['counts'].get('COMMIT')==manifest['expected_dots'],'complete O2 protocol/commit count')
    return dict(status='RUNQ_Q288_DIFFTEST_COUNTER_PATH_PASS',contract=CONTRACT,windows=len(samples),
                functional_calls=manifest['functional_calls'],judge_fault_controls=6,committed_vdot=analysis['counts']['COMMIT'],
                samples=samples,selection=selection(samples,manifest),hardware_changed=False,stable_default_changed=False)

def build(repo,identity,out):
    with adapt(old,CONTRACT=CONTRACT,sources=sources,generate=generate,verification=verification):
        return old.build(repo,identity,out)


def run(repo,identity,build_dir,out,operation):
    with adapt(up,CONTRACT=CONTRACT,MAX_CYCLES=MAX_CYCLES,GENERATED=GENERATED,
               sources=sources,verification=verification,gen=gen,normal=normal):
        return up.run(repo,identity,build_dir,out,operation)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--identity',type=Path)
    p.add_argument('--action',choices=('build','verify','run'),required=True)
    p.add_argument('--build',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--operation-id')
    args=p.parse_args();repo=args.repo.resolve();out=args.output.resolve()
    g.require(repo==ROOT and not out.exists(),'selected checkout and fresh output required')
    identity=(args.identity or repo/parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json').resolve()
    cfg=parent.parent_identity(repo,identity)['configuration']
    roots=[repo,identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    if args.build:roots.append(args.build.resolve())
    parent.outside_inputs(out,roots)
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if args.action=='build':result=build(repo,identity,out)
    elif args.action=='verify':
        g.require(args.build is not None,'build required')
        result=verification(repo,args.build.resolve());g.save(out,result)
    else:
        g.require(args.build and args.operation_id,'build and operation required')
        result=run(repo,identity,args.build.resolve(),out,args.operation_id)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
