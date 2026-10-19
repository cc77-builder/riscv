"""Build fixed T13 images and run isolated single-core EMUs; never publishes Git."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[3]


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()


def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n')


def build(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    images=[]
    for suite,dataset,shards in [('smoke',0,1),('functional',0,3)]+[('performance',i,4) for i in range(3)]:
        for shard in range(shards):
            if args.stream_only and not (suite=='performance' and shard == 3):
                continue
            name=f'{suite}-d{dataset}-s{shard:02d}';d=out/name;d.mkdir()
            extra=['--shared-stream','--variant',args.variant]
            subprocess.run(['python3','-B',str(Path(__file__).with_name('generate.py')),'--output',str(d/'data'),'--suite',suite,'--dataset',str(dataset),'--shard',str(shard),'--shards',str(shards)]+extra,check=True,stdout=subprocess.DEVNULL)
            cmd='source team/scripts/activate.sh\nexport AM_HOME='+shlex.quote(str(args.am.resolve()))+'\n'+shlex.join(['make','-C','team/workloads/unified-vdot','ARCH=riscv64-xs','MARCH=rv64gcv','T13_DATA='+str(d/'data'),'T13_OBJ_ROOT='+str(d/'objects'),'BINARY='+str(d/'vdot-perf'),'-j1'])
            (d/'source').mkdir()
            for filename in ('generate.py','main.c','Makefile','check.py','campaign.py','fixed-layout.ld'):
                (d/'source'/filename).write_bytes((Path(__file__).parent/filename).read_bytes())
            start=now()
            with (d/'build.log').open('wb') as f:r=subprocess.run(['bash','-c',cmd],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
            record=dict(source=source,command=['bash','-c',cmd],started=start,finished=now(),exit_code=r.returncode,am_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.am,text=True).strip(),software={str(p.relative_to(ROOT)):digest(p) for p in Path(__file__).parent.iterdir() if p.is_file()})
            if r.returncode==0:
                record['artifacts']={p.name:digest(p) for p in (d/'vdot-perf.bin',d/'vdot-perf.elf',d/'data/manifest.json')}
            save(d/'build.json',record)
            if r.returncode:raise RuntimeError('build failed: '+name)
            images.append(dict(name=name,suite=suite,dataset=dataset,shard=shard,path=str(d),replays=1))
            print('BUILT '+name,flush=True)
    save(out/'images.json',dict(source=source,images=images))


def run(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    images=json.loads((args.images/'images.json').read_text())['images']
    paths=[args.emu.resolve(),args.reference.resolve(),args.flash.resolve()]
    fixed={str(p):digest(p) for p in paths}
    tasks=[(image,replay) for image in images for replay in range(image['replays'])]
    def execute(task):
        image,replay=task;folder=out/(image['name']+f'-r{replay}');folder.mkdir()
        binary=Path(image['path'])/'vdot-perf.bin'
        command=['timeout','120m',str(paths[0]),'-i',str(binary),'--flash='+str(paths[2]),'--ram-size=128MB','--diff='+str(paths[1]),'--max-cycles=2000000','--seed=1']
        record=dict(image=image['name'],build=image['path'],replay=replay,started=now(),command=command,files=dict(fixed,**{str(binary):digest(binary)}),single_core=True,emu_threads=1,host_concurrency=args.jobs)
        save(folder/'runtime.json',record)
        with (folder/'stdout.log').open('wb') as o,(folder/'stderr.log').open('wb') as e:r=subprocess.run(command,cwd=ROOT,stdout=o,stderr=e)
        record.update(finished=now(),exit_code=r.returncode,raw_sha256={p.name:digest(p) for p in (folder/'stdout.log',folder/'stderr.log')})
        save(folder/'result.json',record)
        print('FINISHED '+folder.name+' exit='+str(r.returncode),flush=True)
        return dict(run=str(folder),exit_code=r.returncode)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results=[f.result() for f in as_completed([pool.submit(execute,t) for t in tasks])]
    save(out/'campaign.json',dict(tasks=len(tasks),results=results))
    if any(r['exit_code'] for r in results):raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    b=sub.add_parser('build');b.add_argument('--output',type=Path,required=True);b.add_argument('--am',type=Path,required=True)
    b.add_argument('--variant',choices=('ours','jade','shishui','redoop'),required=True)
    b.add_argument('--stream-only',action='store_true')
    r=sub.add_parser('run');r.add_argument('--output',type=Path,required=True);r.add_argument('--images',type=Path,required=True)
    for name in ('emu','reference','flash'):r.add_argument('--'+name,type=Path,required=True)
    r.add_argument('--jobs',type=int,default=8)
    a=p.parse_args();build(a) if a.action=='build' else run(a)
