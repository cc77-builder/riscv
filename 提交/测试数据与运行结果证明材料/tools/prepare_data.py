"""Derive tables from immutable evidence; this script performs no hardware runs."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
import csv,gzip,hashlib,json,re,statistics

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
def load(i):return json.loads(next((ROOT/'evidence').glob(i+'__*')).read_text(encoding='utf-8'))
def dump(name,obj):(DATA/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def table(name,rows):
    with (DATA/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def signed_lanes(value):
    n=int(value,16);return [b if b<128 else b-256 for b in ((n>>(8*i))&255 for i in range(8))]

vectors=[json.loads(line) for line in next((ROOT/'evidence').glob('D02__*')).read_text().splitlines()]
vector_rows=[]
for v in vectors:
    a,b=signed_lanes(v['vs1']),signed_lanes(v['vs2'])
    actual=sum(x*y for x,y in zip(a,b))
    assert actual==v['expected_sum'] and int(v['expected_vd'],16)==actual&0xffffffff
    vector_rows.append({'id':v['id'],'vs1_low8_signed':str(a),'vs2_low8_signed':str(b),'expected_signed_sum':actual,'expected_full128':v['expected_vd']})
table('定向测试数据.csv',vector_rows)

bench=[]
for d in range(3):
    for s in range(4):
        ident=f'B{d}{s}';result=load(ident)
        for v in result['samples']:
            bench.append({k:v[k] for k in ['scenario','method','dataset','repeat','phase','n','dots','cycles','instructions']}|{'evidence_id':ident,'seq':v['seq']})
table('微基准全部窗口.csv',bench)
groups=defaultdict(list)
for v in bench:
    if v['phase']=='measured':groups[v['scenario'],v['method']].append(v['cycles'])
bench_summary=[]
for scenario in ['single','chain','batch','stream']:
    v,r=groups[scenario,'vdot'],groups[scenario,'rvv'];assert len(v)==len(r)==12
    bench_summary.append({'scenario':scenario,'windows_per_method':len(v),'vdot_mean':statistics.mean(v),'rvv_mean':statistics.mean(r),'speedup':statistics.mean(r)/statistics.mean(v),'vdot_min':min(v),'vdot_max':max(v),'rvv_min':min(r),'rvv_max':max(r)})
table('微基准结果汇总.csv',bench_summary)

c8=load('P08');c8rows=[]
for sample in c8['summary']['samples']:
    c8rows.append({k:sample[k] for k in ['m','k','variant','software','method','dataset','repeat','phase','cycles','instructions','image_sha256']})
assert len(c8rows)==384
table('C8扩展矩阵正式窗口.csv',c8rows)
selected=[]
for label,variant,method in [('firstdot V2','firstdot','vdot'),('C8','config-reuse','vdot'),('最快 RVV','config-reuse','rvv')]:
    values=[e for e in c8rows if e['m']==8 and e['k']==32 and e['variant']==variant and e['software']=='reuse' and e['method']==method]
    assert len(values)==12
    for e in values:selected.append({'implementation':label,**e})
table('C8最终尺寸正式窗口.csv',selected)
c8_summary=[{'implementation':name,'windows':12,'mean':statistics.mean([e['cycles'] for e in selected if e['implementation']==name]),'minimum':min(e['cycles'] for e in selected if e['implementation']==name),'maximum':max(e['cycles'] for e in selected if e['implementation']==name)} for name in ['firstdot V2','C8','最快 RVV']]
assert [e['mean'] for e in c8_summary]==[282.25,273,299]
table('C8最终尺寸汇总.csv',c8_summary)

trace_path=next((ROOT/'evidence').glob('C02__*'))
lines=gzip.decompress(trace_path.read_bytes()).decode('utf-8').splitlines()
events=[];accept={};responses=[];counts=Counter()
for lineno,line in enumerate(lines,1):
    match=re.match(r'O2_(ACCEPT|MOVE|RESPONSE|KILL)\s',line)
    if not match:continue
    kind=match.group(1);counts[kind]+=1
    row=dict(re.findall(r'(\w+)=\s*([^\s]+)',line));row.update(event=kind,line=lineno)
    events.append(row)
    if kind=='ACCEPT':
        assert row['seq'] not in accept
        accept[row['seq']]=row
    if kind=='RESPONSE':responses.append(row)
checked=[]
for row in responses:
    a=accept[row['seq']]
    if row['illegal']!='0':continue
    left,right=signed_lanes(a['vs1']),signed_lanes(a['vs2'])
    expected=sum(x*y for x,y in zip(left,right));actual=int(row['data'],16)
    assert actual==(expected&0xffffffff),(row,expected)
    checked.append({'seq':int(row['seq']),'accept_cycle':int(a['cycle']),'response_cycle':int(row['cycle']),'vs1':a['vs1'],'vs2':a['vs2'],'expected_signed':expected,'actual_full128':row['data'],'accept_line':a['line'],'response_line':row['line']})
assert len(checked)==1590
assert counts=={'ACCEPT':1643,'MOVE':1615,'RESPONSE':1590,'KILL':53}
table('历史控制日志算术回读.csv',checked)
timeline=[{'event':e['event'],'cycle':int(e['cycle']),'seq':int(e['seq']),'line':e['line'],'slot':e.get('slot','')} for e in events if int(e['seq']) in [1,2,3,182,183]]
table('控制事件时间线.csv',timeline)
extract='\n'.join(f"L{e['line']}: {lines[e['line']-1]}" for e in events if int(e['seq']) in [1,2,3,182,183])+'\n'
(ROOT/'evidence/C02-selected-events.txt').write_text(extract,encoding='utf-8')
reanalysis={'status':'HISTORICAL_TRACE_ARITHMETIC_RECHECK_PASS','checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'source_log_sha256':hashlib.sha256(trace_path.read_bytes()).hexdigest(),'source_uncompressed_sha256':hashlib.sha256(gzip.decompress(trace_path.read_bytes())).hexdigest(),'counts':dict(counts),'legal_responses_checked':len(checked),'all_full128_results_match':True,'new_emu_runs':0,'sample':checked[0]}
assert reanalysis['source_uncompressed_sha256']==load('V02')['actual_execution']['new_process_result']['raw_logs_sha256']['run.log']
dump('历史日志离线回读.json',reanalysis)

sta=load('T05');sta_rows=[]
for p in sta['profiles']:
    sta_rows.append({'profile':p['profile'],'period_ns':p['period_ns'],'load_ff':p['load_ff'],'parent_r2r_slack_ns':p['paths']['r2r']['slack_ns'],'vdot_r2r_slack_ns':p['paths']['vdot_r2r']['slack_ns'],'ready_slack_ns':p['paths']['ready']['slack_ns']})
table('0f父级STA五组条件.csv',sta_rows)
dump('汇总数据.json',{'microbench':bench_summary,'c8':c8_summary,'c8_decisions':{k:v['decision'] for k,v in c8['decisions'].items()},'trace_recheck':reanalysis,'sta':sta_rows,'mapped_parent':{k:load('T04')[k] for k in ['cell_count','cell_area_sum','library_sha256','pass']},'dataset_seed_hex':hex(load('D01')['seed'])})
print(json.dumps({'microbench':bench_summary,'c8':c8_summary,'control_responses_rechecked':len(checked),'source_uncompressed_hash_matched':True},ensure_ascii=False))
