"""Pure-host SP1-E protection contract/audit. Never executes or loads target code."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,math,re,struct,subprocess
import legacy_windows as windows
import runtime_gate as failure
import analyze as sp1
import legacy_o2 as o2
import legacy_workload
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
START,STOP=windows.START,windows.STOP
COUNTERS=windows.COUNTERS
FENCE=0x0330000f
OPS={'vdivu':0x8284a557,'vfdiv':0x82849557,'vfsqrt':0x4e801557}
VIDIV,VFDIV=1<<22,1<<26

def need(ok,message):
 if not ok:raise ValueError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def objsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def manifest():return json.loads((ROOT/'software/manifest.json').read_text())

def fp_value(bits):
 sign=bits>>63;exp=bits>>52&2047;mant=bits&((1<<52)-1)
 need(exp!=2047,'oracle finite input only')
 value=Fraction(mant+(1<<52 if exp else 0))*Fraction(2)**((exp-1023 if exp else -1022)-52)
 return -value if sign else value

def encode_exact(value,negative_zero=False):
 if not value:return int(negative_zero)<<63
 sign=int(value<0);value=abs(value);e=value.numerator.bit_length()-value.denominator.bit_length()
 while value<Fraction(2)**e:e-=1
 while value>=Fraction(2)**(e+1):e+=1
 need(-1022<=e<=1023,'oracle exact normal domain')
 significand=value/Fraction(2)**(e-52)
 need(significand.denominator==1,'oracle does not silently round')
 return sign<<63|(e+1023)<<52|(int(significand)-(1<<52))

def lane_oracle(op,a,b):
 if op=='vdivu':return ((1<<64)-1 if b==0 else a//b),0
 x=fp_value(a)
 if op=='vfdiv':
  y=fp_value(b)
  if not y:
   if not x:return 0x7ff8000000000000,16
   return (((a^b)>>63)<<63)|0x7ff0000000000000,8
  return encode_exact(x/y,((a^b)>>63)!=0),0
 need(op=='vfsqrt','oracle operator')
 if x<0:return 0x7ff8000000000000,16
 if not x:return a,0
 n,d=math.isqrt(x.numerator),math.isqrt(x.denominator)
 need(n*n==x.numerator and d*d==x.denominator,'oracle exact square input')
 return encode_exact(Fraction(n,d)),0

def oracle_cases(m):
 for case in m['cases']:
  lanes=[lane_oracle(case['op'],a,b) for a,b in zip(case['a'],case['b'])]
  need([x[0] for x in lanes]==case['out'],'independent full128 numerical oracle')
  need(lanes[0][1]|lanes[1][1]==case['fflags'],'independent exception oracle')
 return {'cases':len(m['cases']),'lanes':2*len(m['cases']),'status':'INTEGER_FRACTION_ORACLE_PASS','scope':'exact finite input suite and specified IEEE zero/invalid cases; no target execution'}

def static_audit(elf=None,m=None):
 m=m or manifest();elf=Path(elf or ROOT/'build-01/protection.elf')
 oracle=oracle_cases(m);symbols,read=windows.elf_data(elf);kernels={};details=[]
 expected_setup=[0x000062b7,0x6002829b,0x3002a073,0x00805073,0x00f3d073,0x00305073,0xc1817057,0x02057407,0x01050293,0x0202f487,0x02050293,0x0202f507,FENCE]
 for op,word in OPS.items():
  pc,size=symbols['sp1e_'+op];need(pc%16==0 and size==228,'leaf alignment/size')
  data=read(pc,size);values=list(struct.unpack('<'+str(size//4)+'I',data));need(values[:13]==expected_setup,'exact CSR/source/sentinel setup')
  need(all(x&3==3 for x in values),'no compressed leaf words')
  words={pc+4*i:v for i,v in enumerate(values)};path=windows.walk(words)
  expected=[START,FENCE,COUNTERS[0],FENCE,COUNTERS[1],FENCE]+[word]*8+[FENCE,COUNTERS[2],FENCE,COUNTERS[3],FENCE,STOP]
  need([w for _,w in path]==expected and len(path)==20,'exact 20-instruction marked operator sequence')
  need(next(i for i,x in enumerate(expected) if x==COUNTERS[3])-next(i for i,x in enumerate(expected) if x==COUNTERS[0])==15,'static instret delta')
  need(values[-24:]==[FENCE,0x0105b023,0x0115b423,0x00e5b823,0x00f5bc23,0xc20022f3,0x0255b023,0xc21022f3,0x0255b423,0x008022f3,0x0255b823,0x00f022f3,0x0255bc23,0x003022f3,0x0455b023,0x320022f3,0x0455b423,0x05058293,0x0202f527,0x06058293,0x0202f427,0x07058293,0x0202f4a7,0x00008067][-24:],'full128/result/source and complete fcsr stores')
  kernels[op]=words;details.append(dict(op=op,pc=hex(pc),bytes=size,word=hex(word),marked_instructions=20,measured_instret=15,clobber='t0,a4-a7,v8-v10; no stack or callee-saved register write',leaf_sha256=hashlib.sha256(data).hexdigest()))
 ca,cs=symbols['cases'];need(cs==9*72,'compiled Case ABI')
 for i,c in enumerate(m['cases']):
  need(list(struct.unpack('<9Q',read(ca+72*i,72)))==c['a']+c['b']+m['sentinel']+c['out']+[c['fflags']],'compiled operands and full128 oracle')
 pa,ps=symbols['plans'];need(ps==54*16,'compiled Plan ABI')
 for i,p in enumerate(m['plan']):need(list(struct.unpack('<4I',read(pa+16*i,16)))==[p['case'],p['dataset'],p['opid'],p['repeat']],'compiled plan/order')
 gp=symbols['sp1e_guard_dot'][0];need(read(gp,4)==bytes.fromhex('0b059402'),'guard exact PC/word')
 need(gp not in {pc for v in kernels.values() for pc,_ in windows.walk(v)},'guard outside every timed window')
 for name in ['guard_in','cases','result','guard_out']:need(symbols[name][0]%16==0,'128-bit memory alignment '+name)
 guard=dict(pc=hex(gp),word='0x0294050b',vd=10,bit=100,result_lo=16,result_hi=0)
 return dict(status='STATIC_FULL128_CSR_ABI_ELF_PASS',oracle=oracle,elf_sha256=sha(elf),bin_sha256=sha(ROOT/'build-01/protection.bin'),kernels=details,guard=guard,windows=54,vector_instructions=432,custom_commits=1,source_registers_checked=['v8','v9'],all_32_registers_checked=False,execution='NOT_TESTED'),kernels

def check_uart(uart,m,exit_code=0):
 need(exit_code==0,'normal exit')
 uart=failure.normalize_console(uart);failure.validate_failure_markers(uart)
 need('SP1E_FAIL' not in uart,'target protection failure')
 lines=[x for x in uart.splitlines() if x.startswith('SP1E_')]
 need(len(lines)==57,'exact begin/guard/54 windows/summary')
 need(lines[0]=='SP1E_BEGIN version=1 datasets=3 operators=3 windows=54 vl=2 sew=64','begin contract')
 need(lines[1]=='SP1E_GUARD lo=0000000000000010 hi=0000000000000000','guard full128')
 need(lines[-1]=='SP1E_SUMMARY windows=54 div=288 sqrt=144 full128=54 source128=108 csr=324 failures=0','full summary')
 need(uart.count('HIT GOOD TRAP')==1 and uart.index('HIT GOOD TRAP')>uart.index(lines[-1]),'unique final GOOD TRAP')
 rows=[];keys='seq d op r c i cb ce ib ie lo hi vl vt vs vc ff mc'.split()
 for line,p in zip(lines[2:-1],m['plan']):
  tokens=line.split();need(tokens[0]=='SP1E_WINDOW' and len(tokens)==len(keys)+1,'window fields')
  pairs=[x.split('=') for x in tokens[1:]];need([x[0] for x in pairs]==keys,'canonical window keys')
  need(all(re.fullmatch('[0-9a-f]{16}' if k in ('lo','hi') else '[0-9]+',v) for k,v in pairs),'window integer encoding')
  r={k:int(v,16 if k in ('lo','hi') else 10) for k,v in pairs};c=m['cases'][p['case']]
  need(all(0<=v<1<<64 for v in r.values()),'window integer width')
  need([r[k] for k in ('seq','d','op','r')]==[p['seq'],p['dataset'],p['opid'],p['repeat']],'window frozen order')
  need([r['lo'],r['hi']]==c['out'],'window full128 golden')
  need([r[k] for k in ('vl','vt','vs','vc','ff')]==[2,24,0,7,c['fflags']] and r['mc']&5==0,'exact CSR incl frm/RNE and fflags')
  need(r['ce']-r['cb']==r['c']>0 and r['ie']-r['ib']==r['i']==15,'exact CSR delta')
  rows.append(r)
 return rows

def t13_manifest(m):
 return dict(dataset='all-3',plan=[dict(index=p['opid'],phase=p['phase'],repeat=p['repeat']) for p in m['plan']],rows=[dict(id=x,scenario='protection',method=x,n=8,dots=0) for x in OPS],custom_mask=0xfe00707f,custom_match=0x0200000b)

def check_t13(events,m,kernels,rows):
 converted={i:kernels[x] for i,x in enumerate(OPS)}
 samples=windows.trace_windows(events,t13_manifest(m),converted)
 need(len(samples)==54,'54 bound measured windows')
 # These unrolled leaves contain no ADDI pair or legal ROB fusion. Never borrow the chain relaxation.
 retired=events['RETIRE'];group=[];groups=[];active=False
 for e in retired:
  if e['word']==START:need(not active,'nested start');active=True;group=[]
  if active:group.append(e)
  if e['word']==STOP:groups.append(group);active=False
 need(len(groups)==54 and not active,'complete marker groups')
 canonical=[];op_retires=[]
 for p,group,sample,row in zip(m['plan'],groups,samples,rows):
  need(all(e['count']==1 for e in group),'unrolled leaves require singleton ROB records')
  need(sample['cycles']==row['c'] and sample['instructions']==row['i'],'UART/T13 measured delta')
  need(sample['counter_values']==[row['ib'],row['cb'],row['ce'],row['ie']],'UART/CSR sample binding')
  need(sum(e['word']==OPS[p['op']] for e in group)==8,'eight exact operator retirements')
  canonical.append([dict(pc=e['pc'],word=e['word'],count=e['count'],data='COUNTER' if e['word'] in COUNTERS else e['data']) for e in group])
  op_retires.extend(e|dict(op=p['op'],dataset=p['dataset'],seq=p['seq']) for e in group if e['word']==OPS[p['op']])
 return dict(samples=samples,cross_control_sha256=objsha(canonical),operator_retirements=op_retires,retire_sha256=objsha(retired),counter_sha256=objsha({k:events[k] for k in ('COUNTER_ENQUEUE','CSR_SAMPLE')}),scope='single XLEN debug datum per ROB record is preserved exactly; not a full128 DIV/SQRT observation')

def bind_div_retirement(observer_events,operator_retires):
 accepts=[f for _,_,k,f in observer_events if k=='DIV_ACCEPT'];outputs=[f for _,_,k,f in observer_events if k=='DIV_OUTPUT' and f['ready'] and not f['cancelled']]
 used=set();bound=[]
 for e in operator_retires:
  rob=f"{e['flag']}:{e['rob']}";prior=[a for a in accepts if a['rob']==rob and a['cycle']<e['cycle']]
  need(prior,'DIV/SQRT retirement needs actual parent accept')
  a=max(prior,key=lambda a:a['cycle']);need(a['seq'] not in used,'one parent transaction per architectural vector instruction')
  expected=VIDIV if e['op']=='vdivu' else VFDIV
  need(a['fu']==expected,'integer/floating ownership binding')
  out=[o for o in outputs if o['seq']==a['seq'] and o['rob']==rob and a['cycle']<o['cycle']<e['cycle']]
  need(len(out)==1 and out[0]['fu']==a['fu'] and out[0]['pdest']==a['pdest'],'DIV completion/identity before retirement')
  used.add(a['seq']);bound.append(dict(pc=e['pc'],word=e['word'],fu=a['fu'],dataset=e['dataset'],window=e['seq']))
 need(len(bound)==432,'all 432 DIV/SQRT architectural operations bound')
 return dict(count=432,architectural_pc_word_ownership_sha256=objsha(bound),limitation='DIV observer has fu/ROB/pdest only, no opcode, lane result, fflags; opcode from ELF-bound T13, full128/CSR from target checks plus mandatory live DiffTest')

def normal_gate(text,exit_code,reference,mode):
 need(mode in ('baseline','candidate'),'explicit observer mode');plain=failure.normalize_console(text)
 need(plain.count('The first instruction of core 0 has commited. Difftest enabled.')==1,'exact live DiffTest enable')
 need(re.findall(r'The reference model is ([^\r\n]+)',plain)==[str(reference)],'exact reference path')
 need(not re.search(r'CRITICAL\s+ERROR|double\s+trap|PMA\s+check\s+failed',plain,re.I),'fatal diagnostic')
 failure.validate_failure_markers(plain);need(exit_code==0,'normal exit0')
 need(not re.search(r'O2_(?:SCHEMA|STATE|ACCEPT|ENQUEUE|DIV_)' if mode=='candidate' else r'SP1_(?:SCHEMA|STATE|ACCEPT|ENQUEUE|DIV_)',plain),'no mixed observer schema')
 obs=sp1 if mode=='candidate' else o2;analysis=obs.analyze(plain);events,uart=obs.extract_events_and_uart(plain)
 need(analysis['counts'].get('COMMIT')==1,'single guard custom commit')
 need(analysis.get('pending_count')==0 and analysis.get('pending_div_count')==0 and analysis.get('unfinished_rob_count')==0,'all parent queues drained')
 audit,kernels=static_audit();m=manifest();rows=check_uart(uart,m,exit_code)
 custom_commits=[f for _,_,k,f in events if k=='COMMIT'];custom_enq=[f for _,_,k,f in events if k=='ENQUEUE']
 need(custom_commits[0]['pc']==int(audit['guard']['pc'],0),'guard commit exact ELF PC')
 need(any(f['pc']==int(audit['guard']['pc'],0) and f['word']==int(audit['guard']['word'],0) for f in custom_enq),'guard exact enqueued opcode')
 commit=custom_commits[0];allocation=max((e for e in custom_enq if e['rob']==commit['rob'] and e['cycle']<commit['cycle']),key=lambda e:e['cycle'])
 accepted=[a for _,_,k,a in events if k=='ACCEPT' and a['rob']==commit['rob'] and allocation['cycle']<=a['cycle']<commit['cycle']]
 need(len(accepted)==1,'single accepted guard in allocation lifetime')
 ga=accepted[0];need(ga['vs1']==0xa5a5a5a5a5a5a5a50101010101010101 and ga['vs2']==0x5a5a5a5a5a5a5a5a0202020202020202 and ga['vl']==8 and ga['illegal']==0 and ga['vecwen']==1 and ga['v0wen']==0,'full128 frozen guard sources/config')
 gr=[r for _,_,k,r in events if k=='RESPONSE' and r['seq']==ga['seq']];need(len(gr)==1 and gr[0]['data']==16 and gr[0]['exception']==0,'full128 guard response')
 t13=''.join(x.group(0) for x in re.finditer(r'T13_(?:COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+[^\n]*\n',plain))
 bound=check_t13(windows.parse_events(t13),m,kernels,rows);div=bind_div_retirement(events,bound.pop('operator_retirements'))
 return dict(status='PROTECTION_NORMAL_PASS',mode=mode,rows=rows,t13=bound,div_binding=div,observation_sha256=objsha(events),observation_counts=analysis['counts'],elf_sha256=audit['elf_sha256'],bin_sha256=audit['bin_sha256'],manifest_sha256=sha(ROOT/'software/manifest.json'),reference=str(reference),full128_qualification='TARGET_EXACT_STORES_AND_LIVE_DIFFTEST',performance_qualification='single normal only; cross-hardware pairing and exact replay still required')

def negative_gate(text,exit_code,reference,mode='candidate'):
 need(mode in ('baseline','candidate'),'negative explicit schema')
 text=failure.normalize_console(text)
 need(text.count('The first instruction of core 0 has commited. Difftest enabled.')==1,'negative live DiffTest')
 need(re.findall(r'The reference model is ([^\r\n]+)',text)==[str(reference)],'negative exact wrapper reference')
 need(not re.search(r'CRITICAL\s+ERROR|double\s+trap|PMA\s+check\s+failed',text,re.I),'negative unrelated fatal')
 fault=failure.validate_negative(text,exit_code);audit,_=static_audit();want=audit['guard']
 need([fault[k] for k in ('pc','word','vd','bit')]==[want[k] for k in ('pc','word','vd','bit')],'protection guard fault tuple binding')
 obs=sp1 if mode=='candidate' else o2
 analysis=obs.analyze(text,require_complete=False);events,_=obs.extract_events_and_uart(text)
 enq=[f for _,_,k,f in events if k=='ENQUEUE'];commits=[f for _,_,k,f in events if k=='COMMIT']
 need(enq and commits and enq[0]['pc']==commits[0]['pc']==int(want['pc'],0) and enq[0]['word']==int(want['word'],0),'negative actual first guard enqueue/commit')
 need('SP1E_SUMMARY' not in text,'negative must stop before completion')
 return dict(fault=fault,observation_status=analysis['status'],scope='partial trace/expected-failure log only; physical wrapper and resource receipts required externally')

def compare(candidate,baseline,replay_candidate,replay_baseline):
 rs=[candidate,baseline,replay_candidate,replay_baseline]
 need([x.get('mode') for x in rs]==['candidate','baseline','candidate','baseline'],'four role order')
 need(all(x.get('status')=='PROTECTION_NORMAL_PASS' for x in rs),'four complete normal gates')
 for k in ('elf_sha256','bin_sha256','manifest_sha256','reference'):need(len({r[k] for r in rs})==1,'same image/reference '+k)
 for a,b in [(candidate,replay_candidate),(baseline,replay_baseline)]:
  need(a.get('run_id') and b.get('run_id') and a['run_id']!=b['run_id'],'distinct actual replay receipts')
  for k in ('rows','t13','div_binding','observation_sha256','observation_counts'):need(a[k]==b[k],'same hardware exact replay '+k)
 need(candidate['t13']['cross_control_sha256']==baseline['t13']['cross_control_sha256'],'exact cross-hardware PC/word/count/ordinary debug data')
 need(candidate['div_binding']==baseline['div_binding'],'DIV/SQRT architectural ownership equality')
 gates=[]
 for dataset in range(3):
  for op in range(3):
   def measure(r):
    rows=[x for x in r['rows'] if x['d']==dataset and x['op']==op and x['r'] in (2,3,4,5)]
    need(len(rows)==4 and all(x['c']>0 for x in rows),'four positive steady windows')
    return Fraction(sum(x['c'] for x in rows),4)
   cv,bv=measure(candidate),measure(baseline);reg=cv/bv-1
   gates.append(dict(dataset=dataset,op=list(OPS)[op],candidate_mean_cycles=float(cv),baseline_mean_cycles=float(bv),regression=float(reg),pass_limit_2_percent=reg<=Fraction(1,50)))
 return dict(status='PROTECTION_PERFORMANCE_PASS' if all(x['pass_limit_2_percent'] for x in gates) else 'PROTECTION_PERFORMANCE_NO_GO',gates=gates,speedup='NOT_APPLICABLE_pure_DIV_SQRT_protection',first_warmup_included=False)
