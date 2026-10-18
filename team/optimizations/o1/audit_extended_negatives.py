"""Corrupt real O2 logs; demand precise rejection before certifying coverage."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from check_extended import extended_audit, record, HEX
from check_trace import require
from evidence_output import require_new_output, write_new_json


def emit(tag,row):
    return tag+' '+' '.join(f'{k}='+ (hex(v) if k in HEX else str(v)) for k,v in row.items())


def check(control, calibration, build, output):
    require_new_output(output)
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('negative_perf',root/'team/workloads/vdot-perf/check.py')
    perf=importlib.util.module_from_spec(spec);spec.loader.exec_module(perf)
    manifest=json.loads((build/'data/manifest.json').read_text())
    kernels=perf.elf_kernels(build/'vdot-perf.elf')
    sources={'control':control.read_text().splitlines(),'calibration':calibration.read_text().splitlines()}
    def validate(lines,kind):
        result,events=extended_audit(lines)
        if kind=='calibration':perf.trace_windows(events,manifest,kernels)
        return result
    for kind,lines in sources.items():validate(lines,kind)
    tests=[]
    def mutate(kind,name,tag,field,value):
        lines=sources[kind].copy()
        i=next(i for i,x in enumerate(lines) if x.startswith(tag+' '))
        t,r=record(lines[i]);r[field]=value(r[field]);lines[i]=emit(t,r)
        tests.append((name,kind,lines))
    mutate('control','ftq_flag','O2_FTQ_COMMIT','ftf',lambda v:v^1)
    mutate('control','ftq_offset','O2_FTQ_COMMIT','fto',lambda v:(v+1)%16)
    mutate('control','ftq_index_width','O2_FTQ_ENQ','ftv',lambda v:8)
    tests.append(('missing_all_ftq','control',[x for x in sources['control'] if not x.startswith('O2_FTQ_')]))
    mutate('calibration','csr_owner','O2_CSR_ISSUE','rv',lambda v:(v+1)%48)
    mutate('calibration','csr_sample_highbit','O2_CSR_SAMPLE','data',lambda v:v^(1<<63))
    mutate('calibration','csr_write_enable','O2_CSR_SAMPLE','wen',lambda v:v^1)
    mutate('calibration','counter_commit','O2_COUNTER_COMMIT','data',lambda v:v+1)
    mutate('calibration','retired_instruction_count','O2_RETIRE','count',lambda v:v+1)
    mutate('calibration','retired_pc','O2_RETIRE','pc',lambda v:v+4)
    # Change all three data copies consistently: lifecycle matching still holds,
    # so only the independent clock/retirement-work checks can reject it.
    for word,name in [(0xc00028f3,'consistent_cycle_delta'),(0xc02027f3,'consistent_instret_delta')]:
        lines=sources['calibration'].copy()
        parsed=[(i,*record(x)) for i,x in enumerate(lines) if x.startswith('O2_')]
        _,_,retired=next(x for x in parsed if x[1]=='O2_RETIRE' and x[2]['word']==word)
        issues=[r for _,t,r in parsed if t=='O2_CSR_ISSUE' and
                (r['rf'],r['rv'])==(retired['rf'],retired['rv']) and r['cycle']<retired['cycle']]
        issue=max(issues,key=lambda r:r['cycle'])
        changed=0
        for i,tag,row in parsed:
            match=(tag=='O2_CSR_SAMPLE' and row['cycle']==issue['cycle']) or (
                tag in ('O2_RETIRE','O2_COUNTER_COMMIT') and
                (row['cycle'],row['slot'])==(retired['cycle'],retired['slot']))
            if match:
                row['data']+=1;lines[i]=emit(tag,row);changed+=1
        require(changed==3,'could not construct consistent counter mutation')
        tests.append((name,'calibration',lines))
    for tag,name in [('O2_CSR_SAMPLE','missing_csr_sample'),('O2_CSR_OWNER_BEGIN','missing_owner_header'),('O2_RETIRE','missing_all_windows')]:
        lines=sources['calibration'].copy()
        lines=[x for x in lines if not x.startswith(tag+' ')]
        tests.append((name,'calibration',lines))
    results=[]
    for name,kind,lines in tests:
        try:validate(lines,kind)
        except (ValueError,KeyError) as error:
            results.append(dict(name=name,status='REJECTED',reason=str(error),
                                mutated_sha256=hashlib.sha256(('\n'.join(lines)+'\n').encode()).hexdigest()))
        else:raise ValueError('negative escaped: '+name)
    result=dict(status='O2_REAL_TRACE_NEGATIVES_PASS',count=len(results),
                source_sha256={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in [('control',control),('calibration',calibration)]},tests=results)
    write_new_json(output,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('control','calibration','build','output'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();print(check(a.control,a.calibration,a.build,a.output)['status'])
