#!/usr/bin/env python3
"""Finite GNU body/ABI qualification of one packed-Ws candidate. No guest run."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT='r3-dot16-np-packed-ws-v1'
MODEL_SHA='703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82'
HELPER_SHA='db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'
BUILD_SHA='3d855fa040c05c91e079a5b7c52e6ce783510332369e297150f301fb3d64b4c7'
ELF_SHA='62a73b9d16cea43ad03eec3ec09b27edfab7da90ce895d33baa72bf9d84723c4'
PARENTS={
 'dot16.S':'40d263b68ead735b84cb626086674463fbb81154ed9898eb8a340f95f102d671',
 'paired16.S':'452ecab3ae3122dd8ea3d5ae05140197a10bb14a9a5ab76437f7591b00b29caf',
 'w2_np.S':'fbe3a93f642ec3468da92ae776e1b547c29c527d4dffc30456191b437d1272c5',
}
FUNCTIONS={
 'q288_dot16_whole8_narrow':(312,'050bc3db3e2a70bd6e5409cbf9c139868008e8ccb18776b7e0e7104e6a554b75',252,1),
 'q288_paired16_rvv':(1096,'a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c',252,2),
 'q768_dot16_whole8_narrow':(312,'b4a0e512feafd3ae8ea7e4531e13e1a23b12f97d80b3b007be6c52c3bdea56be',672,1),
 'q768_paired16_rvv':(1096,'26f972751fb9882f92118ac30b98f2d0b4d1df9225be5d9cd136e7ed5c4629d3',672,2),
}
TOOLS={
 'gcc-11':'0c54895c55568be5b5fee49e2426abcc8fb05ca2c121ca5685dea2cbc24a1c13',
 'as':'30ab46dce94fa2120f9465dd2965784af831363f75fac42ea9999819f6d15953',
 'ld.bfd':'59db886faf252e5e2fb2e5341fd57c24ddbd216197f69296321fef913e5b64ba',
 'nm':'3f6c21492177e99a2a6db48d530d5ec310ed058c679bc71a743f80c86cb87b56',
 'objdump':'07a28885534079b220a44c7f787c0eecdd240fbe95c525b85e88cc7b88b70e82',
}

def need(ok,message):
    if not ok: raise ValueError(message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(path): return sha(Path(path).read_bytes())
def stamp(): return datetime.now(timezone.utc).isoformat()
def save(path,value): Path(path).write_text(json.dumps(value,indent=2)+'\n')
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj)
    return obj

def run(a):
    deadline=time.monotonic()+180
    os.sched_setaffinity(0,{1});os.setpriority(os.PRIO_PROCESS,0,5)
    source=a.source.resolve();build=a.frozen_build.resolve();out=a.output.resolve()
    need(not out.exists(),'fresh GNU output')
    for p in (source,build):
        need(out!=p and not out.is_relative_to(p) and not p.is_relative_to(out),'isolated output')
    pins={}
    def pin(path,expected=None):
        p=Path(path).absolute();h=digest(p)
        need(expected is None or h==expected,'input SHA '+str(p))
        pins[str(p)]=h;return p
    manifest=json.loads((source/'source-manifest.json').read_bytes())
    need(set(manifest['files'])=={'check_gnu.py','derive.py','pack.c','packed_ws.h',
        'CONTRACT.md','packed.S','source-derivation.json','model.py','process_helper.py'},
        'exact flat source manifest inventory')
    pin(source/'source-manifest.json')
    for n,h in manifest['files'].items():pin(source/n,h)
    need(manifest['files']['check_gnu.py']==digest(Path(__file__)),'actual controller manifest')
    pin(build/'result.json',BUILD_SHA)
    frozen=pin(build/'first-forward-w2np.elf',ELF_SHA)
    parent_files=[]
    for n,h in PARENTS.items():parent_files.append(pin(build/'source'/n,h))
    pin(source/'model.py',MODEL_SHA);pin(source/'process_helper.py',HELPER_SHA)
    tools={n:pin('/usr/bin/riscv64-linux-gnu-'+n,h) for n,h in TOOLS.items()}
    out.mkdir(parents=True);snap=out/'inputs';snap.mkdir()
    for n in manifest['files']:
        (snap/n).write_bytes((source/n).read_bytes())
        need(digest(snap/n)==pins[str((source/n).absolute())],'snapshot equals pinned source '+n)
    (snap/'source-manifest.json').write_bytes((source/'source-manifest.json').read_bytes())
    need(digest(snap/'source-manifest.json')==pins[str((source/'source-manifest.json').absolute())],
        'snapshot equals pinned source manifest')
    for p in parent_files:
        dest=snap/('parent-'+p.name);dest.write_bytes(p.read_bytes())
        need(digest(dest)==pins[str(p.absolute())],'parent snapshot equals pinned source '+p.name)
    snapshot_pins={str(p):digest(p) for p in snap.iterdir()}
    model=module(snap/'model.py','packed_ws_elf')
    helper=module(snap/'process_helper.py','packed_ws_process')
    old=model.ELF(frozen.read_bytes())
    (out/'parents.S').write_bytes(b'\n'.join(p.read_bytes() for p in parent_files))
    generated={str(out/'parents.S'):digest(out/'parents.S')}
    result=dict(contract=CONTRACT,status='BUILDING',started=stamp(),commands=[],
        cpu_affinity=[1],nice=5,budget_seconds=180,inputs=pins,snapshots=snapshot_pins,
        target_emu_runs=0,reference_runs=0,reference_qualified=False,
        target_runtime_qualified=False,performance_qualified=False,production_routes_modified=False)
    save(out/'result.json',result)
    pending=[None]
    def interrupt(signum,frame):
        if pending[0] is None:pending[0]=signum
    def check():
        if pending[0] is not None:raise InterruptedError('signal '+str(pending[0]))
    signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
    env={**os.environ,'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','OMP_NUM_THREADS':'1',
         'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(out)}
    for k in ('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','GCC_EXEC_PREFIX','COMPILER_PATH','LIBRARY_PATH'):
        env.pop(k,None)
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE)
    need(hard==resource.RLIM_INFINITY or hard>=32*1024*1024,'finite log cap')
    resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024*1024,hard))
    def command(label,argv):
        check();remaining=deadline-time.monotonic();need(remaining>0,'total deadline')
        rec=dict(label=label,argv=list(map(str,argv)),started=stamp(),budget_seconds=min(30,remaining))
        result['commands'].append(rec);proc=None
        try:
            with (out/(label+'.log')).open('wb') as log:
                proc=subprocess.Popen(rec['argv'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                rec['pid']=proc.pid;save(out/'result.json',result)
                end=time.monotonic()+rec['budget_seconds']
                while True:
                    check();left=end-time.monotonic()
                    if left<=0:raise subprocess.TimeoutExpired(rec['argv'],rec['budget_seconds'])
                    try:rec['exit_code']=proc.wait(timeout=min(.25,left));break
                    except subprocess.TimeoutExpired:continue
            need(rec['exit_code']==0,label+' failed')
            need(not helper.group_exists(proc.pid),label+' residual process group')
        finally:
            if proc is not None:
                if helper.group_exists(proc.pid):rec['cleanup_complete']=helper.stop_group(proc)
                rec['reaped']=proc.poll() is not None
                rec['group_absent']=not helper.group_exists(proc.pid)
            rec['finished']=stamp();save(out/'result.json',result)
        return (out/(label+'.log')).read_text(errors='replace')
    try:
        built={};nm_logs={}
        for name,assembly in (('parents',out/'parents.S'),('packed',snap/'packed.S')):
            command(name+'-assemble',[tools['gcc-11'],'-march=rv64gcv','-mabi=lp64d',
                '-mcmodel=medany','-mno-relax','-fno-pic','-ffreestanding','-c',assembly,'-o',out/(name+'.o')])
            entry='q288_dot16_whole8_narrow'+('_packed_ws' if name=='packed' else '')
            command(name+'-link',[tools['ld.bfd'],'--no-relax','--build-id=none','-Ttext=0x80000000',
                '-e',entry,'-o',out/(name+'.elf'),out/(name+'.o')])
            nm_logs[name]=command(name+'-nm',[tools['nm'],'--format=bsd','--print-size','--radix=x','--defined-only',out/(name+'.elf')])
            command(name+'-disassembly',[tools['objdump'],'-d','-M','no-aliases',out/(name+'.elf')])
            built[name]=model.ELF((out/(name+'.elf')).read_bytes())
        command('pack-compile',[tools['gcc-11'],'-std=gnu11','-O2','-march=rv64gcv','-mabi=lp64d',
            '-mno-relax','-fno-pic','-ffreestanding','-fno-builtin','-fno-fast-math','-ffp-contract=off',
            '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-tree-loop-distribute-patterns',
            '-Wall','-Wextra','-Werror','-c',snap/'pack.c','-o',out/'pack.o'])
        command('pack-disassembly',[tools['objdump'],'-dr','-M','no-aliases',out/'pack.o'])
        records={}
        def addi(value):return ((value&4095)<<20)|(14<<15)|(14<<7)|0x13
        old_load=(2<<26)|(1<<25)|(28<<20)|(14<<15)|(6<<12)|(12<<7)|7
        new_load=(1<<25)|(14<<15)|(6<<12)|(12<<7)|7
        for original,(length,h,tail,count) in FUNCTIONS.items():
            candidate=original+'_packed_ws'
            parent=built['parents'].symbol_data(original);actual=built['packed'].symbol_data(candidate)
            need(len(parent)==length and sha(parent)==h and old.symbol_data(original)==parent,'rebuilt complete parent equals actual common ELF '+original)
            need(len(actual)==length,'same candidate complete extent')
            before=list(struct.unpack('<'+'I'*(length//4),parent));after=list(struct.unpack('<'+'I'*(length//4),actual))
            changes={old_load:new_load,addi(4):addi(32),addi(tail):addi(0)}
            need(all(before.count(w)==count for w in changes),'exact independent source word multiplicities')
            expected=[changes.get(w,w) for w in before]
            need(expected==after,'all complete machine words equal independent fixed changes '+candidate)
            diffs=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
            need(len(diffs)==3*count,'only three changes per execution path')
            for key,symbol in (('parents',original),('packed',candidate)):
                rows=[line.split() for line in nm_logs[key].splitlines() if line.split() and line.split()[-1]==symbol]
                need(len(rows)==1 and len(rows[0])==4 and int(rows[0][0],16)==built[key].symbols[symbol][0]
                     and int(rows[0][1],16)==length,'independent GNU nm extent '+symbol)
            (out/(candidate+'.bin')).write_bytes(actual)
            records[candidate]=dict(parent=original,bytes=length,parent_sha256=h,sha256=sha(actual),
                changed_word_indices=diffs,changed_words=[dict(index=i,before=f'{before[i]:08x}',after=f'{after[i]:08x}') for i in diffs],
                frozen_common_elf_parent_equal=True,all_other_machine_words_equal=True)
        check()
        for p,h in {**pins,**snapshot_pins,**generated}.items():need(digest(p)==h,'unchanged input '+p)
        need(time.monotonic()<deadline,'deadline includes final audit')
        need(len(result['commands'])==10 and all(r['reaped'] and r['group_absent'] for r in result['commands']),'all finite GNU children reaped')
        result.update(status='PACKED_WS_FOUR_KERNEL_GNU_IDENTITY_PASS',functions=records,
            all_pins_unchanged=True,all_children_reaped=True,gnu_built=True,
            artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='result.json'})
    except BaseException as exc:
        result.update(status='FAILED',error=repr(exc));raise
    finally:
        result['finished']=stamp();save(out/'result.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','frozen-build','output'):p.add_argument('--'+name,type=Path,required=True)
    r=run(p.parse_args())
    print(json.dumps({k:r[k] for k in ('status','functions','all_pins_unchanged','all_children_reaped','started','finished')}))
