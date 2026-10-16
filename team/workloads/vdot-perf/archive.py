"""Create an immutable compact archive without deleting any live evidence."""
from check import require
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(a):
    base=a.base.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    accepted=json.loads((base/'runs/analysis-v1/result.json').read_text())
    require(accepted['status']=='T13_FAIR_CYCLE_COMPARISON_PASS', "Validation failed: accepted['status']=='T13_FAIR_CYCLE_COMPARISON_PASS'")
    copied=[]
    def copy(src,dst,compress=False):
        dst=out/dst;dst.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_bytes()
        if compress:dst=Path(str(dst)+'.gz');dst.write_bytes(gzip.compress(data,mtime=0))
        else:dst.write_bytes(data)
        copied.append(dict(path=str(dst.relative_to(out)),sha256=digest(dst),raw_sha256=hashlib.sha256(data).hexdigest(),raw_bytes=len(data)))
    for group in ('images-v3','images-stream-v4'):
        for src in (base/'runs'/group).rglob('*'):
            if not src.is_file():continue
            rel=src.relative_to(base/'runs'/group)
            if 'objects' in rel.parts:continue
            if src.name in ('vdot-perf.bin','vdot-perf.elf','vdot-perf.txt','build.log','build.json','images.json') or any(x in rel.parts for x in ('data','source')):
                copy(src,Path(group)/rel,src.suffix=='.log')
    external={}
    for group in ('campaign-v3','campaign-stream-v4'):
        for src in (base/'runs'/group).rglob('*'):
            if not src.is_file():continue
            if src.name not in ('stdout.log','stderr.log','runtime.json','result.json','campaign.json'):continue
            if src.name=='result.json':
                rec=json.loads(src.read_text());require(rec['exit_code']==0, "Validation failed: rec['exit_code']==0")
                for file,h in rec['files'].items():
                    if not file.endswith('/vdot-perf.bin'):external[file]=h
            copy(src,Path(group)/src.relative_to(base/'runs'/group),src.suffix=='.log')
    for group in ('analysis-v1','host-tests-01','reference-01','reference-02','preflight-old-emu-01','calibration-01','calibration-02','smoke-build-01','smoke-build-02'):
        source=base/'runs'/group
        for src in source.rglob('*'):
            if not src.is_file():continue
            rel=src.relative_to(source)
            if any(x in rel.parts for x in ('objects','__pycache__')):continue
            if src.name in ('plain','ubsan') or src.suffix in ('.o','.d'):continue
            copy(src,Path('support')/group/rel,src.suffix=='.log')
    for name in ('reference-01.log','reference-02.log'):
        src=base/'runs'/name
        if src.exists():copy(src,Path('support')/name,True)
    for src in (base/'build-evidence').iterdir():
        if src.is_file():copy(src,Path('hardware-build')/src.name,src.suffix=='.log')
    for file,h in external.items():require(digest(file)==h, 'Validation failed: digest(file)==h')
    (out/'external-artifacts.json').write_text(json.dumps(external,indent=2)+'\n')
    (out/'archive-files.json').write_text(json.dumps(dict(version=1,files=copied,scope='Raw log bytes compressed losslessly; fixed EMU/reference/flash binaries remain external and are pinned separately.'),indent=2)+'\n')
    print(json.dumps(dict(status='ARCHIVED',files=len(copied),stored_bytes=sum((out/p['path']).stat().st_size for p in copied))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
