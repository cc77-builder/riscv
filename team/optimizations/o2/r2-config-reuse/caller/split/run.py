"""Build and run the split-input contract using unchanged team runtime helpers.

The build adapter reuses caller/experiment.py's AM commands and snapshots. The
execution sequence is derived from that frozen engine, with this new checker
and exact new first-vdot identity. Official sources and old gates are untouched.
"""
from pathlib import Path, PurePosixPath
from collections import Counter
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import statistics
import struct
import sys
import tempfile
import shlex

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
sys.path.insert(0,str(HERE.parent))
import experiment as old
g,parent=old.g,old.parent
sys.path.insert(0,str(HERE))
gen=g.load('split_generator',HERE/'generate.py')
traced=g.load('split_trace',HERE/'trace.py')
CONTRACT=gen.CONTRACT
MAX_CYCLES=3000000
GENERATED=gen.FILES
OWN=('split.h','split.c','main.c','generate.py','trace.py','run.py','dependencies.json','CONTRACT.md')
BASE_SOURCES=old.sources
read,now,digest=old.read,old.now,old.digest

def sources(repo):
    g.require(repo==ROOT,'selected split source root')
    found=BASE_SOURCES(repo)
    names=set(read(HERE/'dependencies.json'))|set(gen.INPUT_PINS)|{str(gen.REL/n) for n in OWN}
    names.add(str(gen.CONFIG/'evidence/runtime-v1/library/gemv.o'))
    found.update({p:g.sha(repo/p) for p in sorted(names)})
    return found

def generate(repo,out):
    base=g.parent.candidate.source(repo).load_base(repo)
    return gen.generate(repo,out,base.inputs)

def compiler_commands(log,record):
    root=PurePosixPath(record['build_root']);gcc=record['toolchain']['gcc']['path']
    lines=[shlex.split(s) for s in log.splitlines() if s.startswith(gcc+' ')]
    result={}
    for name in ('main','caller','split'):
        src=str(root/'source'/(name+'.c'));obj=str(root/'objects'/(name+'.o'))
        found=[line for line in lines if src in line]
        g.require(len(found)==1,'one real separate C command: '+name)
        cmd=found[0]
        g.require(cmd[-4:]==['-c','-o',obj,src] and all(cmd.count(flag)==1 for flag in old.C_REQUIRED),
                  'actual C flags/source/output: '+name)
        forbidden={'-flto','-fipa-cp','-fipa-icf','-foptimize-sibling-calls','-ftree-vectorize',
                   '-ftree-slp-vectorize','-ftree-loop-distribute-patterns','-mrelax'}
        g.require(not any(arg.split('=',1)[0] in forbidden or arg.startswith('@') or
            (arg.startswith('-march=') and arg!='-march=rv64gv') or
            (arg.startswith('-mabi=') and arg!='-mabi=lp64d') or
            (re.match(r'-O',arg) and arg!='-O2') for arg in cmd),'conflicting C option: '+name)
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
    with tempfile.TemporaryDirectory(prefix='split-regenerate-') as tmp:
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
        before=elf.symbol_data(name)
        g.require(before==reference.symbol_data(name),'qualified old leaf bytes differ: '+name)
        certs.append(gen.machine_certificate(before,elf.symbol_data(gen.NEW[i]),i))
    for name in old.PUBLIC_LEAVES:g.require(elf.symbol_data(name)==refs[0].symbol_data(name),'old full public library changed')
    g.require(elf.symbol_data('split_inputs')==bytes(v&255 for ds in manifest['inputs'] for v in ds),'compiled inputs')
    for table,names in (('packed_entries',[r[0] for r in gen.LEAVES]),('split_entries',gen.NEW)):
        g.require(elf.symbol_data(table)==struct.pack('<6Q',*(elf.symbols[n][0] for n in names)),'actual method table')
    paths={}
    for row in manifest['rows']:
        results=[traced.path(elf,row,bytes(v&255 for v in ds)) for ds in manifest['inputs'][:3]]
        g.require(results[0]==results[1]==results[2],'data-dependent measured path')
        path,detail=results[0]
        if row['mode']=='split':
            for offsets in ((97,35),(39,427)):
                for ds in manifest['inputs']:
                    _,foot=traced.path(elf,row,bytes(v&255 for v in ds),offsets)
                    g.require(foot['vector_reads']==detail['vector_reads'],'layout-dependent vector footprint')
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
    return dict(status='SPLIT_ELF_ADDRESS_AND_CALL_PATH_PASS',contract=CONTRACT,image_sha256=g.sha(build/'vdot-perf.bin'),
                certificates=certs,paths=paths,windows=len(manifest['plan']),actual_c_compilation=compiled,
                source_scope='new ABI; fixed arithmetic machine words; actual input footprints',runtime_not_run=True)

def build(repo,identity,out):
    before={n:getattr(old,n) for n in ('CONTRACT','sources','generate','verification')}
    try:
        old.CONTRACT=CONTRACT;old.sources=sources;old.generate=generate;old.verification=verification
        return old.build(repo,identity,out)
    finally:
        for name,value in before.items():setattr(old,name,value)

def selection(samples,manifest):
    formal=[s for s in samples if s['phase']=='measured']
    methods=[]
    for row in manifest['rows'][:12]:
        ss=[s for s in formal if s['id']==row['id']]
        g.require(len(ss)==12 and {(s['dataset'],s['repeat']) for s in ss}=={(d,r) for d in range(3) for r in range(2,6)},'formal method coverage')
        methods.append(dict(id=row['id'],mode=row['mode'],algorithm=row['algorithm'],leaf=row['leaf'],
            total=sum(s['cycles'] for s in ss),mean=statistics.mean(s['cycles'] for s in ss),
            by_dataset=[sum(s['cycles'] for s in ss if s['dataset']==d) for d in range(3)],
            by_order=[sum(s['cycles'] for s in ss if s['order_group']==o) for o in range(2)],
            by_dataset_order=[sum(s['cycles'] for s in ss if s['dataset']==d and s['order_group']==o)
                              for d in range(3) for o in range(2)],
            cycles=[s['cycles'] for s in ss],instructions=sorted({s['instructions'] for s in ss})))
    pairs=[]
    for i in range(6):
        a,b=methods[i],methods[i+6]
        reductions=[1-y/x for x,y in zip(a['by_dataset'],b['by_dataset'])]
        reduction=1-b['total']/a['total']
        pairs.append(dict(algorithm=i,reduction=reduction,by_dataset=reductions,
                          passed=100*b['total']<=95*a['total'] and
                          all(100*y<=101*x for x,y in zip(a['by_dataset'],b['by_dataset']))))
    anchors=[]
    for d in range(3):
        groups=[]
        for o in range(2):
            for p in ('start','end'):
                ss=[s for s in formal if s['id']==12 and s['dataset']==d and s['order_group']==o and s['anchor_position']==p]
                g.require(len(ss)==2,'formal anchor coverage')
                groups.append(dict(order=o,position=p,total=sum(s['cycles'] for s in ss)))
        ratio=max(s['total'] for s in groups)/min(s['total'] for s in groups)-1
        anchors.append(dict(dataset=d,groups=groups,variation=ratio,
            passed=100*max(s['total'] for s in groups)<=101*min(s['total'] for s in groups)))
    winner=min(methods[7:12],key=lambda m:(m['total'],m['algorithm']))
    vdot=methods[6]
    vd=[1-x/y for x,y in zip(vdot['by_dataset'],winner['by_dataset'])]
    vo=[1-x/y for x,y in zip(vdot['by_order'],winner['by_order'])]
    cells=[1-x/y for x,y in zip(vdot['by_dataset_order'],winner['by_dataset_order'])]
    interface=all(p['passed'] for p in pairs)
    context=all(a['passed'] for a in anchors)
    vdot_qualified=all(1000*x<=995*y for x,y in zip(vdot['by_dataset_order'],winner['by_dataset_order']))
    decision=('STOP_INTERFACE' if not interface else 'HOLD_CONTEXT_VARIATION' if not context else
              'VDOT_PREFERRED_IN_THIS_PLAN' if vdot_qualified else 'KEEP_RVV_EXPLICIT')
    return dict(interface_qualified=interface,pairs=pairs,methods=methods,anchors=anchors,
                decision=decision,observed_lowest_rvv=winner['leaf'],vdot_reduction_by_dataset=vd,
                vdot_reduction_by_order=vo,selected_method=None if not context or not interface else
                (vdot['leaf'] if vdot_qualified else winner['leaf']),vdot_reduction_by_dataset_order=cells,
                stable_default_changed=False)

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
    paths={row['id']:traced.path(elf,row,bytes(v&255 for v in manifest['inputs'][0]))[0] for row in manifest['rows']}
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
        sample.update({k:step[k] for k in ('dataset','order_group','anchor_position')})
    expected=[f"SPLIT_BEGIN contract={CONTRACT} windows=252",'SPLIT_FUNCTIONAL calls=84 controls=6']
    expected += [f"SW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['SPLIT_END windows=252 failures=0']
    actual=[line for line in plain.splitlines() if line.startswith(('SPLIT_','SW '))]
    g.require(actual==expected and plain.count('HIT GOOD TRAP')==1,'raw UART/counter/oracle evidence differs')
    analysis=observer.analyze(stderr+stdout)
    g.require(analysis['status']=='O2_TRACE_PASS' and analysis['schema']['slots']==2 and
        all(analysis.get(k)==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
        analysis['counts'].get('COMMIT')==manifest['expected_dots'],'complete O2 protocol/commit count')
    return dict(status='SPLIT_DIFFTEST_COUNTER_PATH_PASS',contract=CONTRACT,windows=len(samples),
                functional_calls=84,judge_fault_controls=6,committed_vdot=analysis['counts']['COMMIT'],
                samples=samples,selection=selection(samples,manifest),hardware_changed=False,stable_default_changed=False)


def run(repo,identity_path,build_dir,out,operation):
    parent.outside_inputs(out,[repo,identity_path.parent,build_dir])
    ident,hardware,profile=parent.parent_identity(repo,identity_path,physical=True)
    cfg=ident["configuration"]
    parent.outside_inputs(out,[cfg["hardware_source"],cfg["build_record"],cfg["am_home"]])
    valid=verification(repo,build_dir)
    g.require(read(build_dir/"build.json")["accepted"] is True,"caller build not accepted")
    f,m=parent.runtime(repo,ident)
    out.mkdir(parents=True,exist_ok=False)
    state=dict(contract=CONTRACT,status="PREFLIGHT",operation_id=operation,started=now(),new_emu_runs=0,active_pid=None,active_result=None)
    persist=lambda:g.save(out/"state.json",state)
    persist()
    try:
        files=dict(hardware)
        files.update({str(repo/rel):sha for rel,sha in sources(repo).items()})
        files.update(m.checker_files(repo))
        files[str(identity_path)]=g.sha(identity_path)
        for n in ("build.json","elf-validation.json","vdot-perf.elf","vdot-perf.bin","gemv-reference.o"):
            files[str(build_dir/n)]=g.sha(build_dir/n)
        for n in GENERATED: files[str(build_dir/"source"/n)]=g.sha(build_dir/"source"/n)
        receipt=read(build_dir/"build.json")
        files.update(receipt["external_files"]);files.update({t["path"]:t["sha256"] for t in receipt["toolchain"].values()})
        g.save(out/"runtime-inputs.json",files);g.save(out/"configuration.json",cfg)
        g.save(out/"hardware-profile.json",profile);shutil.copyfile(identity_path,out/"parent-identity.json")
        fixture=m.build_negative(repo,cfg,out/"negative-fixture")
        records=[]
        for label in ("negative","recovery","replay"):
            negative=label=="negative";dest=out/"runs"/label;cwd=dest/"cwd";(cwd/"build").mkdir(parents=True)
            for name in m.AUX: shutil.copyfile(Path(cfg["hardware_source"])/"build"/name,cwd/"build"/name)
            reference=fixture["binary"] if negative else cfg["reference"]
            inputs=dict(files);inputs.update({str(cwd/"build"/n):h for n,h in m.AUX.items()})
            if negative:inputs[reference]=fixture["negative_sha256"]
            argv=[str(Path(cfg["hardware_source"])/"build/emu"),"-i",str(build_dir/"vdot-perf.bin"),"--flash="+cfg["flash"],
                  "--ram-size=128MB","--diff="+reference,"--max-cycles="+str(MAX_CYCLES),"--seed=1"]
            rec=dict(contract=CONTRACT,name=label,negative=negative,image_sha256=valid["image_sha256"],command=argv,cwd=str(cwd),
                     reference=reference,files=inputs,started=now(),process_started=False,exit_code=None,status="RUNNING")
            before=state["new_emu_runs"]
            def progress():
                g.save(dest/"result.json",rec)
                state.update(status=label.upper(),new_emu_runs=before+int(rec.get("process_started") is True),
                             active_pid=rec.get("pid") if "finished" not in rec else None,
                             active_result=str(dest/"result.json") if "finished" not in rec else None)
                persist()
            progress()
            try:
                m.verify_files(inputs)
                env=dict(os.environ);env.pop("XS_NEGATIVE_VECTOR_TARGET",None)
                if negative:env["XS_NEGATIVE_VECTOR_TARGET"]="vdot"
                rec["environment_overrides"]={"XS_NEGATIVE_VECTOR_TARGET":"vdot" if negative else None}
                with (dest/"stdout.log").open("wb") as stdout,(dest/"stderr.log").open("wb") as stderr:
                    f.spawn(argv,cwd,stdout,stderr,rec,progress,env,7200)
                banner=g.load("caller_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
                banner.validate_runtime((dest/"stdout.log").read_text()+(dest/"stderr.log").read_text(),reference)
                if negative:
                    detail=m.negative_check(repo,build_dir,dest,rec)
                    elf=g.ELF((build_dir/"vdot-perf.elf").read_bytes())
                    leaf=gen.NEW[0];raw=elf.symbol_data(leaf)
                    pc=elf.symbols[leaf][0]+next(i for i in range(0,len(raw),4) if int.from_bytes(raw[i:i+4],"little")&0xfe00707f==0x0200000b)
                    g.require(detail["vd"]==0 and detail["bit"]==100 and int(detail["pc"],16)==pc and detail["word"]=="0x0388000b","caller actual first vdot fault")
                    rec.update(status="EXPECTED_VDOT_HIGHBIT_REJECTION",negative_details=detail)
                else:
                    result=normal(repo,build_dir,dest,rec)
                    g.save(dest/"validation.json",result);rec.update(status="SPLIT_DIFFTEST_COUNTER_PATH_PASS",validation_sha256=g.sha(dest/"validation.json"))
                m.verify_files(inputs)
            except BaseException as exc:
                rec.update(status="FAILED",error=repr(exc));raise
            finally:
                rec.update(finished=now(),raw_sha256={n:g.sha(dest/n) for n in ("stdout.log","stderr.log") if (dest/n).is_file()});progress()
            records.append(rec);g.save(out/"completed-runs.json",records);print(label,rec["status"],flush=True)
        g.require(records[0]["image_sha256"]==records[1]["image_sha256"]==records[2]["image_sha256"] and
                  len({r["pid"] for r in records})==3,"caller recovery/replay process identity")
        g.require(read(out/"runs/recovery/validation.json")==read(out/"runs/replay/validation.json"),"caller complete replay differs")
        ident2,hardware2,profile2=parent.parent_identity(repo,identity_path,physical=True)
        g.require(ident==ident2 and hardware==hardware2 and profile==profile2,"caller fixed hardware drift")
        m.verify_files(files)
        state.update(status="SPLIT_CAMPAIGN_PASS",new_emu_runs=3,active_pid=None,active_result=None)
        g.save(out/"results.json",dict(contract=CONTRACT,records=records,validation=read(out/"runs/recovery/validation.json")))
    except BaseException as exc:
        state.update(status="FAILED",error=repr(exc));raise
    finally:
        state["finished"]=now();persist()
    return state

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--identity',type=Path)
    p.add_argument('--action',choices=('build','verify','run','audit'),required=True)
    p.add_argument('--build',type=Path);p.add_argument('--run',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--operation-id')
    args=p.parse_args();repo=args.repo.resolve();out=args.output.resolve()
    g.require(repo==ROOT and not out.exists(),'selected checkout and fresh output required')
    identity=(args.identity or repo/parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json').resolve()
    cfg=parent.parent_identity(repo,identity)['configuration']
    roots=[repo,identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')]
    roots += [v.resolve() for v in (args.build,args.run) if v]
    parent.outside_inputs(out,roots)
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    if args.action=='build':result=build(repo,identity,out)
    elif args.action=='run':
        g.require(args.build and args.operation_id,'build and operation required')
        result=run(repo,identity,args.build.resolve(),out,args.operation_id)
    elif args.action=='verify':
        g.require(args.build is not None,'build required')
        result=verification(repo,args.build.resolve());g.save(out,result)
    else:
        g.require(args.build and args.run,'build/run required')
        import archive
        result=archive.audit(repo,args.build.resolve(),args.run.resolve());g.save(out,result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
