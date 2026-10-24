"""Build/run one bounded directed corpus with explicit inputs, then audit raw data.

Use a native LF Linux checkout. Reuses an authenticated EMU, never builds RTL.
Isolated v4 runner retains the frozen v2 receipt format and guards.
No frozen v2/v3 source/input is modified or silently requalified.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE.parent))
import run_suite as suite
generator=suite.load_module('partial_generator',HERE/'generate.py')
checker=suite.load_module('partial_checker',HERE/'check.py')


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
def now():return datetime.now(timezone.utc).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_files(files):
    for name,digest in files.items():suite.require(sha(name)==digest,'input changed: '+name)


def check_output(out, roots):
    suite.require(out.is_absolute() and not out.exists() and not out.is_symlink(),'output must be absolute and new')
    suite.require(all(not out.resolve().is_relative_to(p.resolve()) and
                      not p.resolve().is_relative_to(out.resolve()) for p in roots),'output overlaps inputs')


def replay(out):
    receipt=json.loads((out/'receipt.json').read_text())
    suite.require(receipt['contract']==generator.CONTRACT,'wrong directed contract')
    runtime=receipt['runtime']
    expected=[receipt['emu'],'-i',str(out/'partial-v4.bin'),'--flash='+receipt['flash'],
              '--ram-size=128MB','--diff='+receipt['reference'],'--max-cycles=1000000','--seed=1']
    suite.require(runtime['command']==expected and runtime['cwd']==str(out/'runtime'),
                  'actual command/cwd differs from authenticated inputs')
    suite.require(runtime.get('process_started') is True and type(runtime.get('pid')) is int and runtime['pid']>0
                  and runtime.get('timed_out',False) is False,'incomplete actual execution')
    start,finish=(datetime.fromisoformat(runtime[k]) for k in ('started','finished'))
    suite.require(start.utcoffset() is not None and finish.utcoffset() is not None and start<=finish,'invalid execution times')
    suite.require([row['name'] for row in receipt['commands']]==['build','run'] and
                  receipt['commands'][-1]==runtime,'runtime command receipt differs')
    for path in (receipt['emu'],receipt['flash'],receipt['reference'],str(out/'partial-v4.bin')):
        suite.require(path in receipt['files'],'runtime input lacks pre-execution digest')
    verify_files(receipt['files'])
    for name,digest in receipt['artifacts'].items():suite.require(sha(out/name)==digest,'output artifact changed: '+name)
    generated,_=generator.corpus()
    for name,body in generated.items():
        suite.require((out/'data'/name).read_bytes()==body.encode(),'generated corpus differs: '+name)
    raw=(out/'run/stderr.log').read_bytes()+(out/'run/stdout.log').read_bytes()
    suite.require(raw==(out/'run/run.log').read_bytes(),'raw streams differ from derived log')
    result=checker.check(raw,receipt['runtime']['exit_code'],json.loads((out/'data/manifest.json').read_text()),receipt['reference'],
                         (out/'symbols.txt').read_text(),(out/'partial-v4.txt').read_text())
    suite.require(receipt['runtime']['environment']==dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',TZ='UTC'),
                  'runtime contract changed')
    return result


def run(args):
    out=args.output; hardware=args.hardware_root.resolve(); am=args.am_home.resolve()
    contract=json.loads(args.input_contract.read_text())
    paths={key:Path(value) for key,value in contract['paths'].items()}
    check_output(out,[ROOT,hardware,am,args.input_contract.parent,args.hardware_pins.parent,args.tool_bin])
    suite.require(sys.platform=='linux','native Linux/WSL required')
    out.mkdir(parents=True)
    state=dict(status='PREFLIGHT',contract=generator.CONTRACT,started=now(),new_emu_runs=0,
               hypothesis='Measured dependent VDOT adds seven cycles; one VDOT plus vadd.vi delays shared VDOT input while branch still reads v19. Actual delay must be observed.',
               budget='One 16-trial image, seed1, at most 600 seconds / 1000000 cycles; no automatic sweep.',
               performance_measured=False,defaults_changed=False)
    save(out/'state.json',state)
    files={str(args.input_contract):sha(args.input_contract),str(args.hardware_pins):sha(args.hardware_pins)}
    receipt=dict(contract=generator.CONTRACT,files=files,artifacts={},reference=str(paths['reference']),
                 emu=str(hardware/'build/emu'),flash=str(paths['flash']),commands=[],
                 source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    def persist():save(out/'receipt.json',receipt);save(out/'state.json',state)
    def command(label,argv,cwd,env,limit):
        directory=out/label;directory.mkdir()
        row=dict(name=label,command=list(map(str,argv)),cwd=str(cwd),environment=env,
                 started=now(),exit_code=None,process_started=False)
        receipt['commands'].append(row);persist()
        with (directory/'stdout.log').open('xb') as stdout,(directory/'stderr.log').open('xb') as stderr:
            proc=subprocess.Popen(row['command'],cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            try:
                row.update(pid=proc.pid,process_started=True)
                if label=='run':state['new_emu_runs']+=1
                persist()
                row['exit_code']=proc.wait(timeout=limit)
            except BaseException as exc:
                import os,signal
                if proc.poll() is None:
                    try:os.killpg(proc.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                proc.wait()
                row.update(exit_code=proc.returncode,terminated_on_error=type(exc).__name__,
                           timed_out=isinstance(exc,subprocess.TimeoutExpired))
                raise
            finally:row['finished']=now();persist()
        (directory/'run.log').write_bytes((directory/'stderr.log').read_bytes()+(directory/'stdout.log').read_bytes())
        return row
    try:
        pins=json.loads(args.hardware_pins.read_text());emu=hardware/'build/emu'
        suite.hardware_guard(pins,emu,root=hardware)
        suite.input_contract.validate(args.input_contract,paths,paths['reference'].parents[3]/'runs/t11-matrix-canonical',hardware)
        guard=suite.load_module('partial_artifact_guard',ROOT/'team/scripts/artifact_guard.py')
        suite.input_contract.verify_am(contract,guard)
        hello=json.loads(Path(contract['receipts']['hello']).read_text())
        suite.require(am==Path(hello['am_home']).resolve(),'AM differs from the authenticated input contract')
        provenance=guard.verify_nemu(paths['reference'].parents[1],paths['reference'],'reference')
        suite.input_contract.bind_reference(contract,paths['reference'],provenance)
        files.update(contract['files'])
        files.update({str(emu):sha(emu)})
        # Bind every repository Python module actually imported by this runner.
        for module in list(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path and Path(path).resolve().is_relative_to(ROOT):
                path=Path(path).resolve();files[str(path)]=sha(path)
        files[str(HERE/'main.c')]=sha(HERE/'main.c');files[str(HERE/'Makefile')]=sha(HERE/'Makefile')
        gate=ROOT/'team/optimizations/o1/audit/runtime_gate.py'
        files[str(gate)]=sha(gate)
        suite.verify_committed_drivers({p:h for p,h in files.items() if Path(p).is_relative_to(ROOT)},root=ROOT)
        data=generator.emit(out/'data');source=out/'source';source.mkdir()
        for name in ('main.c','Makefile'):shutil.copyfile(HERE/name,source/name)
        for path in list((out/'data').iterdir())+list(source.iterdir()):files[str(path)]=sha(path)
        tools={name:shutil.which(name,path=str(args.tool_bin)+':/usr/bin:/bin') for name in
               ('make','riscv64-linux-gnu-gcc','riscv64-linux-gnu-objdump','riscv64-linux-gnu-nm',
                'riscv64-linux-gnu-as','riscv64-linux-gnu-ld','riscv64-linux-gnu-ar','riscv64-linux-gnu-objcopy')}
        suite.require(all(tools.values()),'build tool missing')
        files.update({path:sha(path) for path in tools.values()})
        env=dict(PATH=str(args.tool_bin)+':/usr/bin:/bin',LANG='C',LC_ALL='C',TZ='UTC',
                 AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1')
        for name in ('cc1','collect2','liblto_plugin.so'):
            path=subprocess.check_output([tools['riscv64-linux-gnu-gcc'],'-print-prog-name='+name],env=env,text=True).strip()
            suite.require(Path(path).is_file(),'compiler dependency missing: '+name)
            files[str(Path(path).resolve())]=sha(path)
        build=command('build',[tools['make'],'-C',source,'ARCH=riscv64-xs','MARCH=rv64gcv',
            'CROSS_COMPILE='+tools['riscv64-linux-gnu-gcc'][:-3],
            'PARTIAL_DATA='+str(out/'data'),'PARTIAL_OBJECTS='+str(out/'objects'),
            'BINARY='+str(out/'partial-v4'),'-o','am','-o','klib','-j2','image'],ROOT,env,300)
        suite.require(build['exit_code']==0,'build failed')
        symbols=subprocess.check_output([tools['riscv64-linux-gnu-nm'],'--defined-only',str(out/'partial-v4.elf')],env=env,text=True)
        (out/'symbols.txt').write_text(symbols)
        checker.validate_layout(symbols,(out/'partial-v4.txt').read_text())
        verify_files(files)
        for path in list((out/'data').iterdir())+list(source.iterdir())+[
                out/('partial-v4'+ext) for ext in ('.elf','.bin','.txt')]+[out/'symbols.txt']:
            files[str(path)]=sha(path)
        cwd=out/'runtime';(cwd/'build').mkdir(parents=True)
        for name in ('constantin.txt','plusArgs'):
            src=hardware/'build'/name;files[str(src)]=sha(src);shutil.copyfile(src,cwd/'build'/name)
            files[str(cwd/'build'/name)]=sha(cwd/'build'/name)
        env=dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',TZ='UTC')
        argv=[emu,'-i',out/'partial-v4.bin','--flash='+str(paths['flash']),'--ram-size=128MB',
              '--diff='+str(paths['reference']),'--max-cycles=1000000','--seed=1']
        state.update(status='RUNNING',launch_attempts=1);persist()
        receipt['runtime']=command('run',argv,cwd,env,600)
        verify_files(files);suite.hardware_guard(pins,emu,root=hardware)
        receipt['artifacts']={str(p.relative_to(out)):sha(p) for p in out.rglob('*')
                              if p.is_file() and p.name not in ('state.json','receipt.json')}
        persist()
        result=replay(out);save(out/'result.json',result)
        state.update(status=result['status'],target_covered=result['target_covered'],finished=now());persist()
        return result
    except BaseException as exc:
        state.update(status='FAILED',error=repr(exc),finished=now());persist();raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action',choices=('run','check'),default='run')
    p.add_argument('--output',required=True,type=Path)
    for name in ('hardware-root','hardware-pins','input-contract','am-home','tool-bin'):
        p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    value=replay(a.output) if a.action=='check' else run(a)
    print(json.dumps({k:v for k,v in value.items() if k!='diagnosis'}))
