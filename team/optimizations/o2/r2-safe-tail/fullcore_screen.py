#!/usr/bin/env python3
"""S0/S2 canonical ELF build -> B0/H1 smoke -> paired screening.

No simulator rebuild, no --no-diff fallback, no branch operations. Results only
come from real subprocess exits and the existing strict trace/checker modules.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import tempfile

import linked_gate as g

AM_COMMIT='086a238062fdfb3281b745a537b361983d0154b5'
EMU={'b0':'ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57',
     'h1':'e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747'}
REFERENCE='efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4'
FLASH='a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994'
PIN_SHA={'b0':'3752438404f544b9006c52b4234f5f05906b2de0fe4fbfa63c2006a30884dbf9',
         'h1':'39f525c9a9e2a068aee04ef1e08878af3f4056da24115a1236ddacf09b893666'}
H1DIR=Path('team/optimizations/o2/result-width/h1/performance')
CHECKER_PATHS=[g.O3/'check.py',Path('team/workloads/unified-vdot/check.py'),H1DIR/'build_profile.py',
               Path('team/optimizations/o2/fullcore/analyze.py'),
               Path('team/optimizations/o1/audit/runtime_gate.py'),
               Path('team/optimizations/o2/fullcore/workloads/check.py'),
               Path('team/optimizations/o2/r2-kernel-audit/audit.py')]


def now():
    return datetime.now(timezone.utc).isoformat()


def read_config(path, repo):
    value=json.loads(Path(path).read_text())
    fields={'am_home','cross_prefix','b0_products','h1_products','b0_build','h1_build','reference','flash'}
    g.require(set(value)==fields,'unexpected/missing configuration fields')
    for key in fields-{'cross_prefix'}:
        value[key]=str(Path(value[key].replace('${REPO}',str(Path(repo).resolve()))).expanduser().resolve())
    return value


def pinned_modules(repo):
    """Read-only comparison against the inspected source base, not a floating HEAD."""
    for p in CHECKER_PATHS:
        original=subprocess.check_output(['git','show',g.BASE+':'+str(p)],cwd=repo)
        g.require((Path(repo)/p).read_bytes()==original,'checker drift: '+str(p))


def preflight(repo, cfg):
    repo=Path(repo).resolve(); build_errors=[]; runtime_errors=[]; found={}
    def check(path, errors, expected=None):
        p=Path(path)
        if not p.is_file():
            errors.append('missing: '+str(p)); return
        actual=g.sha(p);found[str(p)]=actual
        if expected and actual!=expected:
            errors.append('hash mismatch: '+str(p))
    am=Path(cfg['am_home'])
    for p in ('Makefile.app','Makefile.compile','Makefile.check','am/arch/riscv64-xs.mk',
              'am/build/am-riscv64-xs.a','libs/klib/build/klib-riscv64-xs.a'):
        check(am/p,build_errors)
    tools={}
    for name in ('gcc','ld','ar','objcopy','objdump','readelf'):
        p=shutil.which(cfg['cross_prefix']+name)
        if not p:build_errors.append('missing tool: '+cfg['cross_prefix']+name)
        else:tools[name]=p;check(p,build_errors)
    make=shutil.which('make')
    if make is None:build_errors.append('missing tool: make')
    else:tools['make']=make;check(make,build_errors)
    if (am/'.git').exists():
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=am,text=True).strip()
        if revision!=AM_COMMIT:build_errors.append('nexus-am source commit mismatch')
        if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=am,text=True).strip():
            build_errors.append('modified tracked nexus-am sources')
    else:build_errors.append('nexus-am Git identity unavailable')
    try:g.verify_sources(repo)
    except (OSError,ValueError) as exc:build_errors.append(str(exc))
    for mode in ('b0','h1'):
        check(Path(cfg[mode+'_products'])/'emu',runtime_errors,EMU[mode])
        check(Path(cfg[mode+'_build'])/'hardware-inputs.json',runtime_errors,PIN_SHA[mode])
        for name in ('constantin.txt','plusArgs'):check(Path(cfg[mode+'_products'])/name,runtime_errors)
    # EMU reads these relative to cwd, not relative to its executable.
    for name in ('constantin.txt','plusArgs'):
        actual=repo/'build'/name;selected=Path(cfg['h1_products'])/name
        check(actual,runtime_errors)
        if actual.is_file() and selected.is_file() and g.sha(actual)!=g.sha(selected):
            runtime_errors.append('cwd auxiliary mismatch: '+str(actual))
    # The unchanged provenance checker explicitly binds these historical receipts.
    for path in ('/home/riscv/riscv-lab/o2-fullcore-20261019/recheck-02/result.json',
                 '/home/riscv/riscv-lab/o2-h1-fullcore-20261021/final-validation.json'):
        check(path,runtime_errors)
    check(cfg['reference'],runtime_errors,REFERENCE);check(cfg['flash'],runtime_errors,FLASH)
    for path in CHECKER_PATHS:check(repo/path,runtime_errors)
    return dict(status='PREFLIGHT_READY' if not build_errors and not runtime_errors else 'PREFLIGHT_BLOCKED',
                build_ready=not build_errors,runtime_ready=not runtime_errors,
                build_errors=build_errors,runtime_errors=runtime_errors,tools=tools,files=found,
                new_emu_runs=0,performance_measured=False,checked_at=now())


def inventory():
    return ([dict(suite='smoke',dataset=0,shard=7,variant=v) for v in ('s0','s2')]+
            [dict(suite='performance',dataset=d,shard=s,variant=v)
             for s in (4,5,6,7) for d in (0,1,2) for v in ('s0','s2')])


def image_name(item):
    return f"{item['suite']}-{item['variant']}-d{item['dataset']}-s{item['shard']:02d}"


def spawn(command, cwd, stdout, stderr, receipt, persist, env=None, timeout=600):
    """Keep a real launch receipt; terminate the whole process group on timeout."""
    receipt['process_started']=False
    persist()
    proc=subprocess.Popen(command,cwd=cwd,env=env,stdout=stdout,stderr=stderr,
                          start_new_session=(os.name=='posix'))
    receipt.update(process_started=True,pid=proc.pid)
    persist()
    try:
        receipt['exit_code']=proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        receipt['timed_out']=True
        if os.name=='posix':
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        else:proc.kill()
        receipt['terminated_returncode']=proc.wait()
        receipt['exit_code']=None  # Not a normal, completed program exit.
    except BaseException:
        if os.name=='posix':
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        else:proc.kill()
        proc.wait()
        raise
    finally:persist()


def command(command, cwd, directory, env=None, timeout=600):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=False)
    receipt=dict(command=list(map(str,command)),cwd=str(cwd),started=now(),exit_code=None)
    persist=lambda:g.save(directory/'command.json',receipt)
    persist()
    try:
        with (directory/'stdout.log').open('wb') as a,(directory/'stderr.log').open('wb') as b:
            spawn(command,cwd,a,b,receipt,persist,env,timeout)
    finally:
        receipt['finished']=now()
        receipt['raw_sha256']={n:g.sha(directory/n) for n in ('stdout.log','stderr.log') if (directory/n).exists()}
        persist()
    g.require(receipt['exit_code']==0 and not receipt.get('timed_out'),'command failed/incomplete: '+str(directory))
    return receipt


def build_one(repo, cfg, out, item, tools):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'source/repo'
    for name in g.PINNED:
        target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((Path(repo)/name).read_bytes())
    g.verify_sources(snapshot)
    for name in ('main.c','Makefile','fixed-layout.ld'):
        shutil.copyfile(snapshot/g.O3/name,out/'source'/name)
    candidate=g.load('r2_build_candidate',snapshot/g.REL/'candidate.py')
    manifest=candidate.generate(snapshot,out/'data',item['variant'],item['dataset'],item['shard'],item['suite'])
    # Do NOT let Make mutate/rebuild the preserved AM libraries.
    am=Path(cfg['am_home']); libraries=[am/'am/build/am-riscv64-xs.a',am/'libs/klib/build/klib-riscv64-xs.a']
    frozen={str(p):g.sha(p) for p in libraries}
    env=os.environ.copy()
    for name in ('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS',
                 'CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD'):
        env.pop(name,None)
    env.update(AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1')
    prefix=str(Path(tools['gcc']))[:-3]
    cmd=[tools['make'],'-C',str(out/'source'),'ARCH=riscv64-xs','MARCH=rv64gcv',
         'CROSS_COMPILE='+prefix,'T13_DATA='+str(out/'data'),'T13_OBJ_ROOT='+str(out/'objects'),
         'BINARY='+str(out/'vdot-perf'),'-o','am','-o','klib','-j1','image']
    record=dict(kind='nexus-am-riscv64-xs',source_base=g.BASE,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
                selection=item,exit_code=None,am_revision=AM_COMMIT,external_files=frozen,commands=[],artifacts={})
    g.save(out/'build.json',record)
    try:
        record['commands'].append(command(cmd,repo,out/'make-command',env))
        reference=[tools['gcc'],'-march=rv64gcv','-mabi=lp64d','-mno-relax','-c',str(out/'data/kernels.S'),'-o',str(out/'kernels-reference.o')]
        record['commands'].append(command(reference,repo,out/'reference-command',env))
        for p,digest in frozen.items():g.require(g.sha(p)==digest,'preserved library changed: '+p)
        record['exit_code']=0
        record['artifacts']={p:g.sha(out/p) for p in ('vdot-perf.elf','vdot-perf.bin','kernels-reference.o','data/manifest.json')}
        record['toolchain']={name:{'path':p,'sha256':g.sha(p)} for name,p in tools.items()}
        g.save(out/'build.json',record)
        result=g.verify_build(out,repo);g.save(out/'elf-validation.json',result)
    except Exception as exc:
        record['error']=repr(exc);record['accepted']=False;g.save(out/'build.json',record);raise
    record['accepted']=True;g.save(out/'build.json',record)
    return dict(item,name=image_name(item),path=str(out),image_sha256=g.sha(out/'vdot-perf.bin'))


def validate_controls(images, repo):
    # A new S0 is measured, but its runtime/library/toolchain must match S2.
    identity=None
    for image in images:
        receipt=json.loads((Path(image['path'])/'build.json').read_text())
        current={k:receipt[k] for k in ('kind','source_base','source_commit','am_revision','external_files','toolchain')}
        if identity is None:identity=current
        g.require(current==identity,'mixed build environment across images')
        for path,digest in current['external_files'].items():g.require(g.sha(path)==digest,'AM library drift')
    by={(x['suite'],x['dataset'],x['shard'],x['variant']):x for x in images}
    for item in images:
        if item['variant']!='s2':continue
        a=Path(by[(item['suite'],item['dataset'],item['shard'],'s0')]['path']);b=Path(item['path'])
        ea,eb=(g.ELF((p/'vdot-perf.elf').read_bytes()) for p in (a,b))
        for index in (1,3):
            n=f't13_kernel_{index}'
            g.require(ea.symbols[n][0]==eb.symbols[n][0] and ea.symbol_data(n)==eb.symbol_data(n),'RVV code/address changed')
        if item['shard'] in (4,5):
            g.require((a/'vdot-perf.bin').read_bytes()==(b/'vdot-perf.bin').read_bytes(),'16x64 control load image changed')
    return True


def runtime_profile(repo,cfg):
    pinned_modules(repo)
    profile=g.load('r2_frozen_h1_profile',Path(repo)/H1DIR/'build_profile.py')
    profile.ROOT=Path(repo);profile.B0_PRODUCTS=Path(cfg['b0_products']);profile.H1_PRODUCTS=Path(cfg['h1_products'])
    files,details=profile.build_profile(Path(cfg['b0_build']),Path(cfg['h1_build']))
    files.update({cfg['reference']:REFERENCE,cfg['flash']:FLASH})
    # Bind both the historical validators and this batch's adapters for every run.
    for relative in CHECKER_PATHS+[g.REL/n for n in ('candidate.py','linked_gate.py','fullcore_screen.py')]:
        path=Path(repo)/relative;files[str(path)]=g.sha(path)
    for leaf in ('constantin.txt','plusArgs'):
        path=Path(repo)/'build'/leaf
        g.require(path.read_bytes()==(Path(cfg['h1_products'])/leaf).read_bytes(),'cwd auxiliary drift')
        files[str(path)]=g.sha(path)
    for p,digest in files.items():g.require(g.sha(p)==digest,'runtime input drift: '+p)
    return files,details


def verify_runtime(repo,build,run):
    g.verify_build(build,repo)
    check=g.load('r2_o3_counter_adapter',Path(repo)/g.O3/'check.py')
    # Only the generator hook changes; all UART, CSR, retirement and compiled
    # golden checks remain the original implementation in an isolated module.
    def strict_generation(b,manifest):
        actual=g.regenerate(b)
        g.require(actual==manifest,'manifest changed during runtime validation')
    check.base.verify_generation=strict_generation
    windows=check.verify(build,run)
    guard=g.load('r2_frozen_failure_gate',Path(repo)/'team/optimizations/o1/audit/runtime_gate.py')
    fatal=g.load('r2_frozen_fatal_check',Path(repo)/'team/optimizations/o2/fullcore/workloads/check.py')
    stdout=check.base.read_text(Path(run)/'stdout.log');stderr=check.base.read_text(Path(run)/'stderr.log')
    for stream in (stdout,stderr):
        guard.validate_failure_markers(stream);fatal.reject_fatal_output(stream)
    record=json.loads((Path(run)/'result.json').read_text())
    paths=[s.strip() for s in re.findall(r'The reference model is ([^\r\n]+)',guard.normalize_console(stdout+stderr))]
    g.require(paths==[record['reference']],'wrong/ambiguous loaded DiffTest model')
    observer=g.load('r2_frozen_o2_observer',Path(repo)/'team/optimizations/o2/fullcore/analyze.py')
    analysis=observer.analyze(stderr+stdout)
    manifest=json.loads((Path(build)/'data/manifest.json').read_text())
    expected=sum(manifest['rows'][p['index']]['dots'] for p in manifest['plan'] if manifest['rows'][p['index']]['method']=='vdot')
    g.require(analysis['status']=='O2_TRACE_PASS' and analysis['schema']['slots']==2,'O2 trace/schema failed')
    g.require(all(analysis.get(k)==0 for k in ('pending_count','pending_div_count','unfinished_rob_count')),'incomplete transaction drain')
    g.require(analysis['counts'].get('COMMIT',0)==expected,'custom committed count mismatch')
    return windows,analysis


def execute(repo,cfg,image,mode,out,files,replay=0):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    build=Path(image['path']);emu=Path(cfg[mode+'_products'])/'emu'
    reference=cfg['reference'];flash=cfg['flash']
    inputs=dict(files);inputs.update({str(emu):EMU[mode],str(build/'vdot-perf.bin'):image['image_sha256']})
    cmd=[str(emu),'-i',str(build/'vdot-perf.bin'),'--flash='+flash,'--ram-size=128MB',
         '--diff='+reference,'--max-cycles=2000000','--seed=1']
    record=dict(image,mode=mode,replay=replay,command=cmd,cwd=str(repo),files=inputs,
                reference=reference,exit_code=None,process_started=False,status='RUNNING',started=now())
    g.save(out/'result.json',record)
    try:
        g.verify_build(build,repo)
        for p,digest in inputs.items():g.require(g.sha(p)==digest,'pre-run artifact drift: '+p)
        with (out/'stdout.log').open('wb') as a,(out/'stderr.log').open('wb') as b:
            spawn(cmd,repo,a,b,record,lambda:g.save(out/'result.json',record),timeout=7200)
        record['raw_sha256']={p:g.sha(out/p) for p in ('stdout.log','stderr.log')}
        g.save(out/'result.json',record)
        g.require(record['exit_code']==0,'EMU incomplete or nonzero exit')
        windows,analysis=verify_runtime(repo,build,out)
        manifest=json.loads((build/'data/manifest.json').read_text())
        samples=[]
        for sample,entry in zip(windows['samples'],manifest['plan']):
            row=manifest['rows'][entry['index']]
            samples.append(dict(sample,mode=mode,variant=image['variant'],shard=image['shard'],software=row['software'],
                                m=row['m'],k=row['k'],scope=row['scope'],image_sha256=g.sha(build/'vdot-perf.bin')))
        for p,digest in inputs.items():g.require(g.sha(p)==digest,'post-run artifact drift: '+p)
        record.update(status='R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS',samples=samples)
        g.save(out/'windows.json',windows);g.save(out/'observation.json',analysis)
    except Exception as exc:record.update(status='FAILED',error=repr(exc))
    record['raw_sha256']={p:g.sha(out/p) for p in ('stdout.log','stderr.log') if (out/p).is_file()}
    record['finished']=now();g.save(out/'result.json',record)
    g.require(record['status']=='R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS','runtime gate failed: '+str(out))
    return record


def summarize(records):
    samples=[s for r in records if r['suite']=='performance' and r['replay']==0 for s in r['samples'] if s['phase']=='measured']
    g.require(len(samples)==768,'missing/extra measured samples')
    keys={}
    for s in samples:
        key=(s['mode'],s['variant'],s['shard'],s['software'],s['method'],s['dataset'],s['repeat'])
        g.require(key not in keys,'duplicate sample');keys[key]=s
    rows=[]
    for shard in (4,5,6,7):
        for mode in ('b0','h1'):
            for variant in ('s0','s2'):
                for software in ('basic','reuse'):
                    row=dict(shard=shard,mode=mode,variant=variant,software=software)
                    for method in ('vdot','rvv'):
                        values=[]
                        for dataset in range(3):
                            for repeat in range(2,6):
                                s=keys[(mode,variant,shard,software,method,dataset,repeat)]
                                other=keys[('h1' if mode=='b0' else 'b0',variant,shard,software,method,dataset,repeat)]
                                g.require((s['image_sha256'],s['instructions'],s['seq'])==(other['image_sha256'],other['instructions'],other['seq']),'cross-hardware ELF/work mismatch')
                                g.require(type(s['cycles']) is int and s['cycles']>0,'invalid cycle sample')
                                if shard in (4,5):
                                    control=keys[(mode,'s2' if variant=='s0' else 's0',shard,software,method,dataset,repeat)]
                                    g.require(all(s[k]==control[k] for k in ('image_sha256','instructions','seq','cycles')),'16x64 invariant control diverged')
                                values.append(s['cycles'])
                        row[method]=dict(samples=12,total=sum(values),mean=statistics.mean(values),minimum=min(values),maximum=max(values),pstdev=statistics.pstdev(values))
                    row['rvv_over_vdot']=row['rvv']['total']/row['vdot']['total'];rows.append(row)
    best=[]
    for shard in (4,5,6,7):
        for mode in ('b0','h1'):
            eligible=[r for r in rows if r['shard']==shard and r['mode']==mode]
            rvv=min(eligible,key=lambda r:r['rvv']['total'])
            for r in eligible:
                best.append(dict(shard=shard,mode=mode,variant=r['variant'],software=r['software'],
                                 rvv_variant=rvv['variant'],rvv_software=rvv['software'],
                                 faster_rvv_over_vdot=rvv['rvv']['total']/r['vdot']['total']))
    return dict(samples=samples,rows=rows,faster_rvv_comparison=best)


def run(repo,cfg,out,action):
    repo=Path(repo).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    state=dict(status='PREFLIGHT',new_emu_runs=0,linked_elfs=0,performance_measured=False,source_base=g.BASE,started=now())
    g.save(out/'state.json',state)
    try:
        pre=preflight(repo,cfg);g.save(out/'preflight.json',pre)
        if action=='preflight':
            state.update(status=pre['status']);g.save(out/'state.json',state);return state
        g.require(pre['build_ready'],'canonical build dependencies unavailable; see preflight.json')
        if action=='all':g.require(pre['runtime_ready'],'B0/H1 runtime unavailable; see preflight.json')
        images=[];records=[];profile_files={}
        if action=='all':
            profile_files,details=runtime_profile(repo,cfg)
            profile_files.update(pre['files'])
            g.save(out/'build-profile.json',details)
            g.save(out/'runtime-inputs.json',profile_files)
        for stage in ('smoke','performance'):
            for item in [i for i in inventory() if i['suite']==stage]:
                image=build_one(repo,cfg,out/'images'/image_name(item),item,pre['tools'])
                images.append(image);state['linked_elfs']=len(images);g.save(out/'images.json',dict(images=images));g.save(out/'state.json',state)
            validate_controls(images,repo)
            if action=='build':continue
            state['stage']=stage;g.save(out/'state.json',state)
            for n,image in enumerate([i for i in images if i['suite']==stage]):
                for mode in (('b0','h1') if n%2==0 else ('h1','b0')):
                    record=execute(repo,cfg,image,mode,out/'runs'/mode/(image['name']+'-r0'),profile_files)
                    records.append(record);state['new_emu_runs']=len(records);g.save(out/'state.json',state)
            # No performance image is built or launched before all four smoke jobs pass.
            if stage=='smoke':g.require(len(records)==4,'smoke gate incomplete')
        if action=='build':
            state['status']='CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN';g.save(out/'state.json',state);return state
        for image in [i for i in images if i['suite']=='performance' and i['dataset']==0 and i['shard'] in (5,7)]:
            for mode in ('b0','h1'):
                record=execute(repo,cfg,image,mode,out/'runs'/mode/(image['name']+'-r1'),profile_files,1)
                prior=next(r for r in records if r['name']==image['name'] and r['mode']==mode and r['replay']==0)
                signature=lambda r:[(s['seq'],s['cycles'],s['instructions']) for s in r['samples']]
                g.require(signature(record)==signature(prior),'deterministic replay mismatch')
                records.append(record);state['new_emu_runs']=len(records);g.save(out/'state.json',state)
        g.require(len(images)==26 and len(records)==60,'campaign inventory incomplete')
        stats=summarize(records);g.save(out/'results.json',dict(status='R2_S2_SMALL_SCREEN_PASS',runs=records,**stats))
        state.update(status='R2_S2_SMALL_SCREEN_PASS',performance_measured=True)
    except Exception as exc:
        state.update(status='BLOCKED_OR_FAILED',error=repr(exc))
        g.save(out/'state.json',state)
        raise
    finally:
        # Count launched failures/timeouts too, never only successful receipts.
        receipts=[json.loads(p.read_text()) for p in (out/'runs').glob('*/*/result.json')]
        state['new_emu_runs']=sum(r.get('process_started') is True for r in receipts)
        state['failed_or_incomplete_emu_runs']=sum(r.get('process_started') is True and r.get('status')!='R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS' for r in receipts)
        state['finished']=now();g.save(out/'state.json',state)
    return state


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',required=True,type=Path);p.add_argument('--config',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);p.add_argument('--action',choices=('preflight','build','all'),default='preflight')
    a=p.parse_args()
    try:
        value=run(a.repo,read_config(a.config,a.repo),a.output,a.action)
        print(json.dumps(value,ensure_ascii=False))
        if value['status']=='PREFLIGHT_BLOCKED':p.exit(2)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:
        p.exit(2,'R2_VALIDATION_STOPPED: '+str(exc)+'\n')
