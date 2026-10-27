"""Recompute completed stage qualifications from relocated frozen evidence.

Loads the campaign's frozen Python source closure, never starts an emulator,
and compares all recomputed validation fields with the original JSON values.
New projection diagnostics are written only in a fresh audit working view.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import sys
import types

sys.dont_write_bytecode=True
BASE=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages')
KINDS={
    'math':('target/run_smoke.py','MATH_TLS_DIFFTEST_CAMPAIGN_PASS'),
    'full':('full/run.py','FULL_RISCV_REFERENCE_CAMPAIGN_PASS'),
    'projection':('projection/run.py','FULL_PROJECTION_REFERENCE_CAMPAIGN_PASS'),
    'rope':('rope/run.py','ROPE_STAGE_DIFFTEST_CAMPAIGN_PASS'),
    'boundary':('projection/target/run.py','PROJECTION_BOUNDARY_DIFFTEST_CAMPAIGN_PASS'),
}
RUNS={
    'math':['normal','bad-golden','bad-guard','recovery','replay'],
    'full':['normal','bad-state','recovery','replay'],
    'projection':['normal','bad-tail','recovery','replay'],
    'rope':['bad-output','normal','recovery','replay'],
    'boundary':['bad-tail','normal','recovery','replay'],
}
MODES={'bad-golden':1,'bad-guard':2,'bad-output':1,'bad-tail':1}
COUNTER_RUNNER_SHA256='35bcaef3443b17cfaaa8fbd3bf0149d090b67425d89ccb8d88b6063121cb598a'


def need(ok,why):
    if not ok:raise ValueError(why)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def canonical(value):return json.loads(json.dumps(value,sort_keys=True))


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def rope_counter_function(audit,build,campaign,original_repo,original_build,records):
    """Reuse the exact later auditor without importing its unrelated builder."""
    raw=(audit/'runner-source.py').read_bytes()
    need(hashlib.sha256(raw).hexdigest()==COUNTER_RUNNER_SHA256,'fixed original post-run counter auditor')
    old=read(audit/'result.json')
    need(old==dict(status='ROPE_ALL_COUNTER_CHAINS_AND_EXACT_REPLAY_PASS',normal_windows=4,
        negative_windows=2,normal_counter_reads=16,negative_counter_reads=8,new_emu_runs=0,
        full_retirement_window_audited=False,runner_sha256=COUNTER_RUNNER_SHA256),'exact original extra audit scope')
    recorded=read(audit/'inputs.json')
    roots={str(Path(p).parents[2]) for p in recorded if p.endswith('/runs/bad-output/stderr.log')}
    need(len(roots)==1,'unique original RoPE campaign identity in counter audit')
    root=next(iter(roots));expected={}
    for rec in records:
        for name in ('stdout.log','stderr.log','validation.json'):
            expected[str(Path(root)/'runs'/rec['name']/name)]=digest(campaign/'runs'/rec['name']/name)
    expected.update({
        str(Path(original_repo)/BASE/'projection/target/run.py'):COUNTER_RUNNER_SHA256,
        str(Path(original_build)/'result.json'):digest(build/'result.json'),
        str(Path(original_build)/'rope-stage.elf'):digest(build/'rope-stage.elf'),
        str(Path(original_repo)/'team/optimizations/o2/fullcore/analyze.py'):digest(campaign/'source/team/optimizations/o2/fullcore/analyze.py'),
    })
    need(recorded==expected,'all extra audit raw, validator, ELF and observer inputs bound')
    tree=ast.parse(raw)
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='counter_audit']
    constants=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MAX_CYCLES' for t in n.targets)]
    need(len(funcs)==len(constants)==1 and not funcs[0].decorator_list,'one exact undecorated auditor and limit')
    need(ast.literal_eval(constants[0].value)==8000000,'preserved counter-only limit; original RoPE limit checked separately')
    namespace={'re':re,'struct':struct,'need':need}
    # Execute only the pinned original function definition and literal limit.
    # No unrelated top-level imports, builders, physical checks or run entry.
    exec(compile(ast.Module(body=[constants[0],funcs[0]],type_ignores=[]),str(audit/'runner-source.py'),'exec'),namespace)
    return namespace['counter_audit']


def run(kind,build,campaign,output,counter_audit=None):
    need(not output.exists() and not output.is_relative_to(build) and not output.is_relative_to(campaign),'fresh audit outside immutable evidence')
    need(counter_audit is None or (kind=='rope' and not output.is_relative_to(counter_audit)),'extra counter audit only for RoPE and outside its immutable inputs')
    entry,wanted_status=KINDS[kind];entry=BASE/entry
    state=read(campaign/'state.json');old=read(campaign/'results.json');inputs=read(campaign/'runtime-inputs.json')
    need(state['status']==old['status']==wanted_status and not state.get('active') and state.get('active_pid') is None,'completed original campaign')
    need([x['name'] for x in old['records']]==RUNS[kind],'exact original negative, normal, recovery and replay set')
    pids=[x.get('pid') for x in old['records']]
    need(all(type(pid) is int and pid>0 for pid in pids) and len(set(pids))==len(pids),'distinct recorded actual process identities')
    frozen=campaign/'source';need((frozen/entry).is_file(),'frozen original runner closure')
    source={str(p.relative_to(frozen)):digest(p) for p in frozen.rglob('*') if p.is_file()}
    candidates={str(Path(p).parents[len(entry.parts)-1]) for p in inputs if p.endswith('/'+str(entry))}
    roots=[root for root in candidates if all(inputs.get(str(Path(root)/rel))==value for rel,value in source.items())]
    need(len(roots)==1,'one exact original source identity for every frozen file')
    original_repo=roots[0]
    result=read(build/'result.json');pin=digest(build/'result.json')
    old_builds=[str(Path(p).parent) for p,value in inputs.items() if p.endswith('/result.json') and value==pin]
    need(len(old_builds)==1,'actual original build bound by campaign input hash')
    build_pins={'result.json':pin}
    for rel,value in result['source_pins'].items():
        need(digest(build/'source/repo'/rel)==value,'all original build source bytes')
        build_pins['source/repo/'+rel]=value
    for key,prefix in (('actual_source_pins','source/'),('fixtures','fixture/'),('artifacts','')):
        for name,value in result.get(key,{}).items():
            need(digest(build/(prefix+name))==value,'exact frozen build/fixture/artifact bytes')
            build_pins[prefix+name]=value
    output.mkdir(parents=True);save(output/'inputs.json',dict(kind=kind,original_source_root=original_repo,
        original_build=old_builds[0],source_pins=source,build_pins=build_pins,rechecker_sha256=digest(__file__)))
    status=dict(status='RECHECKING',kind=kind,new_emu_runs=0,new_reference_runs=0,
        performance_samples_added=0,physical_runtime_identity_rechecked=False)
    save(output/'state.json',status)
    try:
        mod=load('frozen_forward_runner',frozen/entry)
        need(mod.REPO==frozen,'runner imports resolved within relocated source root')
        gates=None
        if kind in ('math','rope','boundary'):
            gates=(load('frozen_banner',frozen/'team/optimizations/o2/fullcore/run_suite.py'),
                load('frozen_failure',frozen/'team/optimizations/o1/audit/runtime_gate.py'),
                load('frozen_fatal',frozen/'team/optimizations/o2/fullcore/recheck.py'),
                load('frozen_uart',frozen/'team/optimizations/o2/fullcore/analyze.py'))
            cfg=read(campaign/'parent-identity.json')['configuration']
        post=None;post_pins={};post_normals={}
        if counter_audit is not None:
            post_pins={str(p.relative_to(counter_audit)):digest(p) for p in counter_audit.rglob('*') if p.is_file()}
            post=rope_counter_function(counter_audit,build,campaign,original_repo,old_builds[0],old['records'])
            post_elf,inspection=mod.b.executable(build/'rope-stage.elf',build/'rope-stage.bin',build/'metadata.stdout.log')
            need(inspection['counter_sites']==result['counter_sites'],'redecoded original fenced counter sites')
            save(output/'rope-static-recheck.json',inspection)
            identity=read(output/'inputs.json');identity['extra_counter_audit_pins']=post_pins;save(output/'inputs.json',identity)
        records=[];normal_values={}
        for receipt in old['records']:
            name=receipt['name'];need(Path(name).name==name,'simple recorded run label')
            if kind in ('full','projection'):
                negative=name.startswith('bad-')
                need(type(receipt.get('negative')) is bool and receipt['negative']==negative,'fixed contract negative identity')
            else:
                mode=MODES.get(name,0)
                need(type(receipt.get('mode')) is int and receipt['mode']==mode,'fixed contract mode identity')
            dest=campaign/('runs' if kind in ('math','rope','boundary') else '')/name
            actual_receipt=read(dest/'result.json')
            need(canonical(receipt)==actual_receipt,'original campaign and leaf process receipt agree')
            for filename,value in receipt['raw_sha256'].items():
                need(Path(filename).name==filename and digest(dest/filename)==value,'actual complete recorded raw output')
            need(digest(dest/'validation.json')==receipt['validation_sha256'],'original validation identity')
            if kind in ('math','rope'):
                # Added offline gate; preserve the older runner unchanged.
                text=(dest/'stderr.log').read_text()+(dest/'stdout.log').read_text()
                unused,uart=gates[3].extract_events_and_uart(text);gates[2].reject_fatal_output(uart)
                del unused,uart,text
            if kind=='math':fresh=mod.validate(dest,result,mode,receipt,cfg,gates)
            elif kind in ('full','projection'):fresh=mod.validate(build,dest,negative,receipt)
            elif kind=='rope':fresh=mod.validate(dest,result,mode,receipt,cfg,gates)
            else:
                view=output/'work'/name;view.mkdir(parents=True)
                for filename in ('stdout.log','stderr.log'):
                    shutil.copyfile(dest/filename,view/filename)
                    need(digest(view/filename)==receipt['raw_sha256'][filename],'new raw audit view preserves original bytes')
                fresh=mod.validate(view,result,build,mode,receipt,cfg,gates)
                for filename in ('custom-commit-pcs.bin','counter-audit.json','protocol.json'):
                    need((view/filename).read_bytes()==(dest/filename).read_bytes(),'complete independently recomputed diagnostic bytes')
            fresh=canonical(fresh)
            need(fresh==read(dest/'validation.json'),'every recomputed validation field matches original')
            if post:
                text=(dest/'stderr.log').read_text()+(dest/'stdout.log').read_text()
                timing=canonical(post(text,post_elf,result['counter_sites'],
                    2 if mode else 4,fresh['samples'],gates[3]))
                del text
                need(timing==read(counter_audit/(name+'.json')),'every independently recomputed RoPE counter chain matches')
                save(output/(name+'-counter.json'),timing)
                if not mode:post_normals[name]=timing
            if name in ('normal','recovery','replay'):normal_values[name]=fresh
            save(output/(name+'.json'),fresh);records.append(dict(name=name,status=fresh['status'],validation_sha256=digest(output/(name+'.json'))))
            print(kind,name,fresh['status'],flush=True)
        need(len(records)==(5 if kind=='math' else 4),'complete original independent run set')
        need(normal_values['normal']==normal_values['recovery']==normal_values['replay'],'independent raw replay results remain exactly equal')
        if post:
            need(post_normals['normal']==post_normals['recovery']==post_normals['replay'],'complete RoPE counter chain replay')
            need(post_pins=={str(p.relative_to(counter_audit)):digest(p) for p in counter_audit.rglob('*') if p.is_file()},'extra audit originals unchanged')
        # Do not silently load a current workspace helper instead of the
        # campaign's frozen helper after sys.path or module-cache changes.
        queue=[mod,*(gates or ()),*list(sys.modules.values())];seen=set()
        while queue:
            m=queue.pop()
            if not isinstance(m,types.ModuleType) or id(m) in seen:continue
            seen.add(id(m));queue.extend(v for v in vars(m).values() if isinstance(v,types.ModuleType))
            filename=getattr(m,'__file__',None)
            if filename:
                p=Path(filename).resolve()
                if '/team/' in str(p) and p!=Path(__file__).resolve():need(p.is_relative_to(frozen),'all imported project helpers came from frozen closure')
        need(source=={str(p.relative_to(frozen)):digest(p) for p in frozen.rglob('*') if p.is_file()},'frozen source tree unchanged by recheck')
        for rel,value in build_pins.items():need(digest(build/rel)==value,'immutable build and fixtures unchanged')
        status.update(status='FROZEN_FORWARD_RAW_RECHECK_PASS',records=records,
            extra_rope_counter_audit_reproduced=post is not None,
            scope='existing raw qualification reproduced; no new execution or broader performance claim')
        save(output/'result.json',status)
    except BaseException as error:status.update(status='FAILED',error=repr(error));raise
    finally:save(output/'state.json',status)
    return status


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kind',choices=KINDS,required=True)
    for name in ('build','campaign','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--counter-audit',type=Path,help='optional frozen rope-counter-recheck directory; reproduces its exact later counter audit')
    a=p.parse_args();os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    print(json.dumps(run(a.kind,a.build.resolve(),a.campaign.resolve(),a.output.resolve(),a.counter_audit.resolve() if a.counter_audit else None),indent=2))
