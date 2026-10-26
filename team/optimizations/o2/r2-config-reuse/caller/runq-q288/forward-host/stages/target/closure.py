"""Inspect the selected static libm closure before any AM runtime adaptation."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import shutil
import signal

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('forward_stage_runtime_commands',HERE.parent/'check.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
need,sha,save,command=helper.need,helper.sha,helper.save,helper.command
CONTRACT='r2-s3-forward-math-closure-v1'


def run(output,prefix):
    need(not output.exists(),'fresh closure output')
    need(not output.is_relative_to(HERE.parents[8]),'output outside repository')
    output.mkdir(parents=True)
    state=dict(contract=CONTRACT,status='STARTED',started_at=helper.now(),target_emu_runs=0,
               target_runtime_ready=False,performance_qualified=False)
    save(output/'state.json',state)
    try:
        paths=[HERE/'closure.py',HERE/'probe.c',HERE/'CONTRACT.md',HERE.parent/'check.py',HERE.parent/'generate.py']
        pins={str(p):sha(p.read_bytes()) for p in paths}
        source=output/'source';source.mkdir()
        for p in paths:shutil.copyfile(p,source/p.name)
        save(output/'source-pins.json',pins)
        tools={name:shutil.which(prefix+name) for name in ('gcc','ld','nm','readelf','objdump','ar')}
        need(all(tools.values()),'complete installed cross toolchain')
        toolpins={name:dict(path=p,resolved=str(Path(p).resolve()),sha256=sha(Path(p).read_bytes())) for name,p in tools.items()}
        save(output/'tools.json',toolpins)
        command([tools['gcc'],'--version'],output,'compiler-version')
        command([tools['gcc'],'-print-file-name=libm.a'],output,'locate-libm')
        archive=Path((output/'locate-libm.stdout.log').read_text().strip()).resolve()
        need(archive.is_file(),'installed static libm archive')
        raw=archive.read_bytes();need(raw.startswith(b'!<arch>\n'),'actual libm is a normal archive, not an unexamined linker script')
        archive_pin=sha(raw)
        save(output/'archive.json',dict(path=str(archive),sha256=archive_pin,bytes=len(raw)))
        command([tools['ar'],'t',archive],output,'archive-members')
        flags=['-std=c11','-O2','-march=rv64gv','-mabi=lp64d','-mno-relax','-ffreestanding',
               '-fno-builtin','-fno-fast-math','-ffp-contract=off','-fno-lto','-fno-stack-protector']
        command([tools['gcc'],*flags,'-c',source/'probe.c','-o',output/'probe.o'],output,'compile-probe')
        command([tools['ld'],'-r','-Map='+str(output/'closure.map'),'-o',output/'closure.o',output/'probe.o',archive],output,'partial-link')
        command([tools['nm'],'-u',output/'closure.o'],output,'undefined')
        command([tools['readelf'],'-W','-h','-A','-s','-r',output/'closure.o'],output,'elf-metadata')
        command([tools['objdump'],'-drwC',output/'closure.o'],output,'disassembly')
        selected=sorted(set(re.findall(r'([^\s]+\.a)\(([^)\n]+)\)',(output/'closure.map').read_text())))
        need(selected and all(Path(p).resolve()==archive for p,_ in selected),'selected members come from fixed libm')
        members=[]
        for index,(_,name) in enumerate(selected):
            label='member-'+str(index)
            command([tools['ar'],'p',archive,name],output,label)
            data=(output/(label+'.stdout.log')).read_bytes()
            need(data.startswith(b'\x7fELF'),'selected member is a real ELF object')
            members.append(dict(name=name,raw_file=label+'.stdout.log',sha256=sha(data),bytes=len(data)))
        meta=(output/'elf-metadata.stdout.log').read_text()
        unresolved=(output/'undefined.stdout.log').read_text().splitlines()
        result=dict(contract=CONTRACT,status='STATIC_CLOSURE_INSPECTED',archive_sha256=archive_pin,
                    closure_sha256=sha((output/'closure.o').read_bytes()),selected_members=members,
                    unresolved_lines=unresolved,tls_relocation_lines=[s for s in meta.splitlines() if 'R_RISCV_' in s and ('TLS' in s or 'TPREL' in s)],
                    ifunc_symbol_lines=[s for s in meta.splitlines() if 'IFUNC' in s],
                    target_emu_runs=0,target_runtime_ready=False,performance_qualified=False)
        need(sha(archive.read_bytes())==archive_pin,'libm unchanged throughout inspection')
        need(all(sha(p.read_bytes())==pins[str(p)] for p in paths),'source unchanged throughout inspection')
        need(all(str(Path(t['path']).resolve())==t['resolved'] and sha(Path(t['path']).read_bytes())==t['sha256']
                 for t in toolpins.values()),'toolchain unchanged throughout inspection')
        receipts={p.name:json.loads(p.read_text()) for p in output.glob('*.command.json')}
        need(all(r['status']=='exited' and r['exit_code']==0 for r in receipts.values()),'all commands have successful terminal receipts')
        result['command_receipts']=receipts
        save(output/'result.json',result);state.update(status=result['status'],result_sha256=sha((output/'result.json').read_bytes()))
        return result
    except BaseException as error:
        state.update(status='FAILED',error=repr(error));raise
    finally:
        state['finished_at']=helper.now();save(output/'state.json',state)


if __name__=='__main__':
    def interrupted(signum,frame):raise InterruptedError('math closure signal '+str(signum))
    signal.signal(signal.SIGTERM,interrupted)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--cross-prefix',default='riscv64-linux-gnu-')
    args=p.parse_args()
    if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,[min(os.sched_getaffinity(0))])
    print(json.dumps(run(args.output.resolve(),args.cross_prefix),indent=2))
