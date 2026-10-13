"""Finite, source-bound T12 build/run driver; requires the approved Linux session.
Reuse existing AM/NEMU gates, existing EMU hash + identical src/build.sc.
No network, service setup, hardware rebuild or golden model changes.
"""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
PARENT='6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3'
HARDWARE='fcb16a8764d342339670df0bbf1bc67ef2028b86'
AM='086a238062fdfb3281b745a537b361983d0154b5'
EMU='43fd7b094a3fb8676395dc97ca08443fb2d2d37d1dbfea0d7b9078c67087718f'
REFERENCE='e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae'
FLASH='a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994'
SOURCES=('team/workloads/t12-perf/main.c','team/workloads/t12-perf/Makefile','team/workloads/t12-perf/sites.S',
         'team/workloads/vdot-exceptions/harness.S','team/workloads/vdot-exceptions/harness.h',
         'team/workloads/vdot-exceptions/layout.h','team/workloads/vdot-exceptions/judge.c',
         'team/tests/generate_t12.py','team/tests/test_t12.py','team/scripts/t12-tests.py',
         'team/scripts/check-t12-run.py','team/scripts/artifact_guard.py')

def now():return datetime.datetime.now().astimezone().isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,m):
    if not v:raise ValueError(m)
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.PIPE).decode().strip()

def child(cmd,out,timeout=60,env=None):
    start=now();t=time.monotonic();out=Path(out)
    with out.open('wb') as log:
        p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        pending=dict(pid=p.pid,command=list(map(str,cmd)),started_at=start,log=str(out),timeout_seconds=timeout)
        write(out.with_suffix(out.suffix+'.process.json'),pending)
        timed_out=False
        try:rc=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            import signal
            timed_out=True;os.killpg(p.pid,signal.SIGTERM)
            try:rc=p.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rc=p.wait(timeout=10)
        pending.update(finished_at=now(),exit_code=rc,timed_out=timed_out,elapsed_host_seconds=time.monotonic()-t)
        write(out.with_suffix(out.suffix+'.process.json'),pending)
    require(rc==0 and not timed_out,'child failed: '+str(out)+' exit='+str(rc))
    return pending

def guard_module():
    spec=importlib.util.spec_from_file_location('t12_artifact_guard',ROOT/'team/scripts/artifact_guard.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def check_source(source):
    require(re.fullmatch('[0-9a-f]{40}',source or ''),'supply the fixed implementation SHA')
    require(git('rev-parse','HEAD')==source,'HEAD differs from supplied implementation SHA')
    require(not git('status','--porcelain=v1','--untracked-files=all'),'source must be committed and clean; no automatic reset/stash')
    subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',PARENT,source],check=True)
    require(not git('diff',HARDWARE,source,'--','src','build.sc'),'production hardware/build differs from accepted EMU source')
    return {name:sha(ROOT/name) for name in SOURCES}

def no_active_am_build(am):
    # Inspect only whether a build command refers to AM; do not dump other users' command lines.
    found=[]
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            parts=path.read_bytes().split(b'\0')
            executable=Path(parts[0].decode(errors='replace')).name
            if executable in ('make','gmake') and any(str(am).encode() in x for x in parts[1:]):found.append(int(path.parent.name))
        except (OSError,ValueError):continue
    require(not found,'AM build already active at PIDs '+','.join(map(str,found)))

def build(a):
    sources=check_source(a.expected_source)
    ev=a.output.resolve();require(not ev.exists(),'fresh output directory required');ev.mkdir(parents=True)
    am=a.am.resolve();g=guard_module()
    g.audit_repo(am,AM,source_roots=('am/src','am/include','libs/klib/src','libs/klib/include'))
    no_active_am_build(am)
    data=ev/'data'
    child([sys.executable,'-B','team/tests/generate_t12.py','--output',str(data)],ev/'generate.log')
    image=ev/'t12-perf.bin';elf=ev/'t12-perf.elf'
    env=dict(os.environ,AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1')
    child(['make','-C','team/workloads/t12-perf','ARCH=riscv64-xs','MARCH=rv64gcv',
           'T12_DATA='+str(data),'VDOT_OBJ_ROOT='+str(ev/'objects'),'BINARY='+str(ev/'t12-perf'),'-j1'],
          ev/'build.log',timeout=300,env=env)
    child(['riscv64-linux-gnu-objdump','-d',str(elf)],ev/'disassembly.txt')
    child(['riscv64-linux-gnu-gcc','--version'],ev/'compiler.txt')
    require(check_source(a.expected_source)==sources,'source changed during build')
    def sums(path,paths):path.write_text(''.join(sha(p)+'  '+str(p)+'\n' for p in paths))
    sums(ev/'source.sha256',[ROOT/n for n in SOURCES])
    sums(ev/'inputs.sha256',sorted(data.iterdir()))
    sums(ev/'workload.sha256',[image,elf])
    g.capture_build(ev,data,'t12','riscv64-xs','full',am)
    b=dict(source=a.expected_source,parent=PARENT,arch='riscv64-xs',kind='t12',image=sha(image),
           manifest=sha(data/'manifest.json'),sources=sources,started_at=json.loads((ev/'build.log.process.json').read_text())['started_at'],finished_at=now())
    write(ev/'t12-build.json',b)
    print('T12_BUILD_DONE '+str(ev))

def run(a):
    sources=check_source(a.expected_source);g=guard_module()
    build_dir=a.build.resolve();b=json.loads((build_dir/'t12-build.json').read_text())
    require(b['source']==a.expected_source and b['sources']==sources,'source/binary mismatch')
    data=build_dir/'data';image=build_dir/'t12-perf.bin'
    ev=a.output.resolve();require(not ev.exists(),'fresh output directory required');ev.mkdir(parents=True)
    verification=g.verify_build(build_dir,image,data,'t12','full');write(ev/'build-verification.json',verification)
    require(sha(image)==b['image'] and sha(data/'manifest.json')==b['manifest'],'image/input mismatch')
    emu=a.emu.resolve();reference=a.reference.resolve();flash=a.flash.resolve()
    require(sha(emu)==EMU,'EMU hash differs from accepted binary')
    require(sha(reference)==REFERENCE,'reference hash differs from accepted 1.1.0 reference')
    require(sha(flash)==FLASH,'flash differs from common accepted flash')
    reference_check=g.verify_nemu(a.nemu.resolve(),reference,'reference');write(ev/'nemu-verification.json',reference_check)
    write(ev/'reuse.json',dict(emu=str(emu),emu_sha256=EMU,source=HARDWARE,src_build_sc_identical_to=a.expected_source,
                              reference=str(reference),reference_sha256=REFERENCE,flash=str(flash),flash_sha256=FLASH,
                              configuration='accepted MinimalConfig, unchanged binary',production_rebuilt=False))
    cmd=[str(emu),'-i',str(image),'--flash='+str(flash),'--ram-size=128MB','--diff='+str(reference),'--max-cycles=5000000']
    # The process receipt is always finalized even on failure. No wrapper exit0 fallback.
    try:process=child(cmd,ev/'run.log',timeout=1200)
    except ValueError:
        p=json.loads((ev/'run.log.process.json').read_text());write(ev/'runtime-failed.json',p);raise
    require(check_source(a.expected_source)==sources,'source changed during execution')
    g.verify_build(build_dir,image,data,'t12','full')
    runtime=dict(source=a.expected_source,parent=PARENT,image=sha(image),manifest=sha(data/'manifest.json'),
                 emu=sha(emu),reference=sha(reference),flash=sha(flash),ram='128MB',difftest=True,**process)
    write(ev/'runtime.json',runtime)
    child([sys.executable,'-B','team/scripts/check-t12-run.py','--log',str(ev/'run.log'),'--data',str(data),
           '--exit-code',str(process['exit_code']),'--build',str(build_dir/'t12-build.json'),'--runtime',str(ev/'runtime.json'),
           '--expected-source',a.expected_source,'--output',str(ev/'checked')],ev/'checker.log')
    with (ev/'run.log').open('rb') as src,(ev/'run.log.gz').open('wb') as dst:
        with gzip.GzipFile(fileobj=dst,mode='wb',mtime=0,filename='') as gz:
            while chunk:=src.read(1024*1024):gz.write(chunk)
    print('T12_FULLCORE_ARCHITECTURAL_DONE '+str(ev)+'; microarchitecture remains unobserved')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('build','run'))
    p.add_argument('--expected-source',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--am',type=Path);p.add_argument('--build',type=Path);p.add_argument('--emu',type=Path)
    p.add_argument('--nemu',type=Path);p.add_argument('--reference',type=Path);p.add_argument('--flash',type=Path)
    a=p.parse_args()
    try:
        require(os.name=='posix' and platform.system()=='Linux','requires approved Linux execution; does not start WSL or bypass denials')
        required=('am',) if a.action=='build' else ('build','emu','nemu','reference','flash')
        for name in required:require(getattr(a,name) is not None,'missing --'+name)
        build(a) if a.action=='build' else run(a)
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as e:raise SystemExit('T12_REJECTED: '+str(e))
