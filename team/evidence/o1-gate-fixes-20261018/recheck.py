"""Recheck frozen full-core logs with authenticated hardened checkers.

No EMU is launched. Requires this checkout and a fresh --output directory.
Historical source/checker inventories remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MANIFEST='516556c1834a1379f0eefd4b366c82e1c799af503aed01d49d04892fef3a1cf9'
FULLCORE='ebfb0b7302017699c50a106988944be8038a9c4d8cbdb68f67bbfc3889d84a2c'
PARENT='fb309f5421c9f24b68350ecf6cfd53fc2d8368102f9a948bef2f8ca68fb084ec'


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


def run(output):
    require(sha(HERE/'checker-sources.json')==MANIFEST,'checker inventory changed')
    sources=read(HERE/'checker-sources.json')
    require(sha(HERE/'checker-sources.tar.gz')==sources['archive_sha256'],'checker archive changed')
    for name,digest in sources['files'].items():
        require(sha(ROOT/name)==digest,'reviewed input changed: '+name)
    old=ROOT/'team/evidence/o1-complete-20261018'
    require(sha(old/'validation.tar.gz')==FULLCORE,'full-core archive changed')
    parent=ROOT/'team/evidence/o1-parent-20261018/validation.tar.gz'
    require(sha(parent)==PARENT,'parent archive changed')
    output.mkdir(parents=True,exist_ok=False)
    raw=output/'raw';raw.mkdir()
    inventory={};total=0
    with tarfile.open(old/'validation.tar.gz') as archive:
        for member in archive:
            path=PurePosixPath(member.name)
            require(member.isfile() and not path.is_absolute() and '..' not in path.parts
                    and str(path)==member.name and ':' not in member.name and '\\' not in member.name
                    and member.name not in inventory,'unsafe archive member')
            total+=member.size;require(total<1024**3,'archive too large')
            target=raw/path;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.extractfile(member).read());inventory[member.name]=sha(target)
    require(inventory==read(old/'validation.tar.gz.json')['files'],'raw archive inventory differs')
    sys.path.insert(0,str(ROOT/'team/optimizations/o1'))
    from recheck_extended_run import recheck
    from audit_extended_negatives import check as corrupt
    from check_extended import extended_audit, record, key
    from check_trace import killed
    from check_parent_negative import check as negative
    from evidence_output import write_new_json
    runs=raw/'runs-01'
    result=recheck(runs)
    require(result==read(raw/'recheck.json'),'hardened checker changed original accepted result')
    write_new_json(output/'raw-recheck.json',result)
    mutations=corrupt(runs/'control/stderr.log',runs/'calibration/stderr.log',runs/'images/calibration',output/'original-negatives.json')
    require(mutations==read(raw/'negatives.json'),'previous mutation results differ')
    ftq=[]
    for shard in range(8):
        lines=(runs/f'matrix-{shard}/stderr.log').read_text().splitlines();live={};target=None
        for index,line in enumerate(lines):
            if not line.startswith('O2_FTQ_'):continue
            tag,row=record(line);ptr=key(row)
            if tag=='O2_FTQ_ENQ':live[ptr]=row
            elif tag=='O2_FTQ_COMMIT':live.pop(ptr,None)
            else:
                if row['self'] and ptr in live:
                    target=index,tag,row;break
                live={p:r for p,r in live.items() if not killed(p,(*ptr,row['self']),48)}
        require(target is not None,'no live VDot self-flush')
        index,tag,row=target
        for field in ('ftf','ftv','fto'):
            changed=dict(row);changed[field]^=1
            bad=lines.copy();bad[index]=tag+' '+' '.join(f'{k}={v}' for k,v in changed.items())
            try:extended_audit(bad)
            except ValueError as error:
                require('FTQ self-flush target identity mismatch' in str(error),'wrong FTQ rejection')
                ftq.append(dict(shard=shard,field=field,status='REJECTED',reason=str(error)))
            else:raise ValueError('FTQ mutation escaped')
    parent_checks=[]
    with tarfile.open(parent) as archive:
        for fault in ('identity','wen','high','cancel'):
            text=archive.extractfile(f'attempt-07/inject-{fault}.log').read().decode()
            parent_checks.append(negative(fault,1,text))
    receipt=dict(status='O1_HARDENED_ARCHIVE_RECHECK_PASS',new_cpu_runs=0,archived_cpu_runs=13,
                 ftq_mutations=ftq,previous_mutations=15,archived_parent_negatives=parent_checks,
                 default_o1=False,performance_ab=False,checker_manifest_sha256=MANIFEST,
                 fullcore_archive_sha256=FULLCORE,parent_archive_sha256=PARENT)
    write_new_json(output/'completion.json',receipt)
    return receipt['status']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    print(run(parser.parse_args().output))
