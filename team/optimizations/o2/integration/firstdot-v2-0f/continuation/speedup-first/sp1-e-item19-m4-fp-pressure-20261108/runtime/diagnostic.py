"""Bounded streaming separation; preserves raw logs, legacy contracts and identity checks."""
from pathlib import Path
import json,hashlib
from common import need,save,read
import adapter,sched_trace
N=Path(__file__).resolve().parent.parent
C=read(N/'CONTRACT.json')

def project(paths,dest,cap=128*1024*1024):
    total=0;side=0
    with Path(dest).open('wb') as out:
        for path in paths:
            with Path(path).open('rb') as src:
                for line in src:
                    need(len(line)<=16384,'oversize log line')
                    if line.startswith(b'SCHED_'):side+=1;continue
                    total+=len(line);need(total<=cap,'legacy projection memory bound')
                    out.write(line)
    return {'legacy_bytes':total,'sideband_lines':side}

def collect(rd,role,exit_code):
    rd=Path(rd);projection=rd/'legacy-projection.log'
    info=project([rd/'stdout.log',rd/'stderr.log'],projection)
    need(info['sideband_lines']>0,'new observer absent')
    result=adapter.collect(projection.read_text(),role,exit_code)
    def lines():
        with (rd/'stderr.log').open() as f:yield from f
    with (rd/'sideband-responses.jsonl').open('w') as out:
        def sink(row):out.write(json.dumps(row)+'\n')
        side=sched_trace.audit_stream(lines(),require_complete=(role=='candidate-normal'),response_sink=sink)
    need(sorted(side['schemas'])==sorted(C['observer_expected_schemas']),'exact compiled observer schema set')
    save(rd/'sideband-audit.json',side)
    result.update(sideband=side,projection=info,item19_qualified=False)
    return result
