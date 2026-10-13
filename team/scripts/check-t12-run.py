"""Strict ordered T12 evidence checker. Host fixtures are never DUT evidence."""
import argparse
import csv
import datetime
import hashlib
import json
import re
import statistics
from pathlib import Path

PARENT = '6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3'
EMU = '43fd7b094a3fb8676395dc97ca08443fb2d2d37d1dbfea0d7b9078c67087718f'
REFERENCE = 'e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae'
FLASH = 'a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994'

def require(v,m):
    if not v: raise ValueError(m)

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def fields(line,prefix):
    result={}
    require(line.startswith(prefix+' '),'wrong record role')
    for part in line[len(prefix)+1:].split():
        key,value=part.split('=',1)
        require(key not in result,'duplicate field')
        result[key]=value
    return result

def number(v):
    require(re.fullmatch(r'(?:0x[0-9a-f]+|[0-9]+)',v),'invalid integer')
    return int(v,16 if v.startswith('0x') else 10)

def csr(v):
    values=[number(x) for x in v.split('/')]
    require(len(values)==6,'six CSR fields required')
    return values

def validate_binding(source,build,runtime):
    require(re.fullmatch('[0-9a-f]{40}',source or ''),'explicit full expected source required')
    require(build.get('source')==runtime.get('source')==source,'source/binary mismatch')
    require(runtime.get('parent')==PARENT,'wrong parent')
    require(build.get('arch')=='riscv64-xs' and build.get('kind')=='t12','wrong build role')
    require(runtime.get('emu')==EMU and runtime.get('reference')==REFERENCE and runtime.get('flash')==FLASH,'runtime pins mismatch')
    require(runtime.get('image')==build.get('image') and re.fullmatch('[0-9a-f]{64}',runtime.get('image','')),'image/binary mismatch')
    require(runtime.get('manifest')==build.get('manifest') and re.fullmatch('[0-9a-f]{64}',runtime.get('manifest','')),'paired input mismatch')
    require(runtime.get('difftest') is True and runtime.get('ram')=='128MB','wrong runtime configuration')
    require(type(runtime.get('pid')) is int and runtime['pid']>0,'missing process PID')
    for k in ('started_at','finished_at'):
        t=datetime.datetime.fromisoformat(runtime.get(k,''));require(t.tzinfo is not None,'timestamp lacks timezone')
    require(datetime.datetime.fromisoformat(runtime['finished_at'])>=datetime.datetime.fromisoformat(runtime['started_at']),'end before start')
    require(runtime.get('exit_code')==0,'runtime failure')

def validate(content,exit_code,data,require_diff=True):
    require(exit_code==0,'failed exit')
    data=Path(data)
    manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8-sig'))
    for name,want in manifest['files'].items(): require(digest(data/name)==want,'generated input changed: '+name)
    rows=json.loads((data/'cases.json').read_text(encoding='utf-8-sig'))
    byid={r['id']:r for r in rows}
    require(len(byid)==len(rows),'duplicated plan ID')
    lines=content.splitlines()
    require(not any(re.search(r'\b(?:FAIL|BAD TRAP|ABORT|Assertion failed)\b',x) for x in lines),'failure in log')
    begins=[i for i,x in enumerate(lines) if x=='T12_BEGIN contract=vdot-s8x8-r32-v0.1']
    ends=[i for i,x in enumerate(lines) if x.startswith('T12_SUMMARY ')]
    controls=[i for i,x in enumerate(lines) if x=='T12_CONTROLS high96=1 preserved=1 csr=1']
    require(len(begins)==len(ends)==len(controls)==1 and begins[0]<controls[0]<ends[0],'incomplete begin/control/summary')
    goods=[i for i,x in enumerate(lines) if 'HIT GOOD TRAP' in x]
    starts=[i for i,x in enumerate(lines) if 'Difftest enabled' in x]
    if require_diff:
        require(len(goods)==len(starts)==1 and starts[0]<begins[0]<ends[0]<goods[0],'missing ordered actual DiffTest completion')
    located=[(i,fields(x,'T12_CASE')) for i,x in enumerate(lines) if x.startswith('T12_CASE ')]
    require(all(begins[0]<i<ends[0] for i,_ in located),'case outside workload')
    parsed=[r for _,r in located]
    require([dict(id=r['id'],repeat=number(r['repeat'])) for r in parsed]==manifest['schedule'],'missing/extra/reordered case')
    summary=fields(lines[ends[0]],'T12_SUMMARY')
    require(summary==dict(executed=str(len(parsed)),failed='0'),'wrong final count')
    metrics=[]
    for r in parsed:
        plan=byid[r['id']]
        require(r['result']=='PASS' and r['verdict']=='0','nonpass case')
        require(all(r[k]=='1' for k in ('pre32_checked','vectors_checked','csr_checked','guards')),'unchecked state')
        require(number(r['scratch'])==sum(1<<v for v in plan['scratch']),'wrong scratch domain')
        expected=[int.from_bytes(bytes.fromhex(plan['expected'][i]),'little') for i in range(10,14)]
        actual=[int(x,16) for x in r['dests'].split('/')]
        require(len(actual)==4 and actual==expected,'wrong full-width result')
        require(all(re.fullmatch('[0-9a-f]{32}',x) for x in r['dests'].split('/')),'noncanonical full-width result')
        require(csr(r['pre_csr'])==[0,8,0,3,1,7],'bad initial CSR')
        if plan['fault_vl'] is not None:
            require(number(r['traps'])==1 and number(r['cause'])==2,'not one precise illegal trap')
            require(number(r['epc'])==number(r['expected_pc']) and number(r['epc'])>=0x80000000,'wrong fault PC')
            require(number(r['tval'])==0,'wrong runtime VL tval')
            require(csr(r['post_csr'])==[0,plan['fault_vl'],0,3,1,7],'wrong fault CSRs')
            require(csr(r['recovered_csr'])==[0,8,0,3,1,7],'missing legal recovery')
        else:
            require(number(r['traps'])==0 and number(r['cause'])==0,'unexpected trap')
            require(csr(r['post_csr'])==[0,8,0,3,1,7],'wrong final CSR')
        cb,ce,ib,ie=[number(r[k]) for k in ('cycle_begin','cycle_end','instret_begin','instret_end')]
        if plan['kind']=='perf':
            require(ce>cb and ie>ib,'nonpositive performance')
            metrics.append(dict(scenario=plan['scenario'],method=plan['method'],repeat=number(r['repeat']),
                                dots=plan['dots'],cycle_begin=cb,cycle_end=ce,instret_begin=ib,instret_end=ie,
                                cycles=ce-cb,instret=ie-ib,input_id=hashlib.sha256(json.dumps(plan['before']).encode()).hexdigest()))
        else: require(cb==ce==ib==ie==0,'nonperf counters contaminated')
    analysis={}
    for scenario in ('complete','known-config','independent-batch'):
        subset=[r for r in metrics if r['scenario']==scenario]
        pairs=[]
        for repeat in range(manifest['repeats']):
            pair=[r for r in subset if r['repeat']==repeat and r['method']!='empty']
            require(len(pair)==2 and {r['method'] for r in pair}=={'vdot','rvv'},'incomplete pair')
            require(len({(r['dots'],r['input_id']) for r in pair})==1,'pair input/count mismatch')
            vd=next(r for r in pair if r['method']=='vdot');rv=next(r for r in pair if r['method']=='rvv')
            pairs.append(dict(repeat=repeat,vdot_cycles=vd['cycles'],rvv_cycles=rv['cycles'],rvv_over_vdot=rv['cycles']/vd['cycles']))
        analysis[scenario]=dict(pairs=pairs,median_ratio=statistics.median(r['rvv_over_vdot'] for r in pairs),
            empty_cycles=[r['cycles'] for r in subset if r['method']=='empty'],overhead_subtracted=False,
            interpretation='raw uncalibrated counter window with result stores/fence, not FU latency')
    return dict(status='T12_ARCHITECTURAL_PASS',executed=len(parsed),microarchitectural_observed=False,
                metrics=metrics,analysis=analysis)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--log',type=Path,required=True);p.add_argument('--data',type=Path,required=True)
    p.add_argument('--exit-code',type=int,required=True);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True);p.add_argument('--expected-source',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:
        build=json.loads(a.build.read_text());runtime=json.loads(a.runtime.read_text())
        validate_binding(a.expected_source,build,runtime)
        require(digest(a.data/'manifest.json')==build['manifest'],'wrong data source')
        result=validate(a.log.read_text(),a.exit_code,a.data)
        require(a.exit_code==runtime['exit_code'],'wrapper/runtime exit mismatch')
        a.output.mkdir(parents=True,exist_ok=True)
        (a.output/'analysis.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        with (a.output/'raw.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(result['metrics'][0]));writer.writeheader();writer.writerows(result['metrics'])
        print(json.dumps(dict(status=result['status'],executed=result['executed'],microarchitectural_observed=False)))
    except (ValueError,OSError,KeyError,TypeError) as e: raise SystemExit('T12_REJECTED: '+str(e))
