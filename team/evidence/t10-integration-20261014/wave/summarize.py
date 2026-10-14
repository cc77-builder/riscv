from pathlib import Path
import csv,re,json,hashlib
p=Path('C:/Code/RVInno/riscv/team/out/t10-positive-wave-20261014')
state={}; requests=[]; responses=[]; commits=[]; traps=[]; last=None
fu='TOP.SimTop.l_soc.core_with_l2.core.backend.inner_vfExuBlock.exus_1.funcUnits_4'
csr='TOP.SimTop.l_soc.core_with_l2.core.backend.inner_intExuBlock.exus_7.csr.csrMod'
def v(scope,name):
 bits=state.get(scope+'.'+name)
 assert bits is not None and re.fullmatch('[01]+',bits),(scope,name,bits)
 return int(bits,2)
def rid(direction):return v(fu,'io_'+direction+'_bits_ctrl_robIdx_flag')*64+v(fu,'io_'+direction+'_bits_ctrl_robIdx_value')
def sample(cycle):
 if v(fu,'io_in_valid') and v(fu,'io_in_ready'):
  requests.append(dict(cycle=cycle,rob=rid('in'),pdest=v(fu,'io_in_bits_ctrl_pdest'),src0=v(fu,'io_in_bits_data_src_0'),src1=v(fu,'io_in_bits_data_src_1'),vl=v(fu,'io_in_bits_data_src_4')))
 if v(fu,'io_out_valid') and v(fu,'io_out_ready'):
  responses.append(dict(cycle=cycle,rob=rid('out'),pdest=v(fu,'io_out_bits_ctrl_pdest'),result=v(fu,'io_out_bits_res_data'),illegal=v(fu,'io_out_bits_ctrl_exceptionVec_2'),vecwen=v(fu,'io_out_bits_ctrl_vecWen'),v0wen=v(fu,'io_out_bits_ctrl_v0Wen')))
 for signal in list(state):
  if re.fullmatch(r'.+\.rob\.difftest_delayer(?:_\d+)?\.i_valid',signal) and state[signal]=='1':
   scope=signal.rsplit('.',1)[0]; word=v(scope,'i_instr')
   if word&0xfe00707f==0x0200000b:commits.append(dict(cycle=cycle,pc=hex(v(scope,'i_pc')),instruction=hex(word)))
 if v(csr,'diffArchEvent_delayer.o_valid'):
  traps.append(dict(cycle=cycle,pc=hex(v(csr,'diffArchEvent_delayer.o_exceptionPC')),instruction=hex(v(csr,'diffArchEvent_delayer.o_exceptionInst')),cause=v(csr,'diffArchEvent_delayer.o_exception'),mcause=v(csr,'diffCSRState_module.io_bits_mcause'),mepc=hex(v(csr,'diffCSRState_module.io_bits_mepc')),mtval=hex(v(csr,'diffCSRState_module.io_bits_mtval'))))
with (p/'events.csv').open(newline='') as f:
 for row in csv.DictReader(f):
  time=int(row['time'])
  if last is not None and time!=last:
   assert time>=last
   for cycle in range(last,time):sample(cycle)
  last=time;state[re.sub(r' \[\d+:\d+\]$','',row['signal'])]=row['value']
if last is not None:sample(last)
matched=[]
for b in responses:
 a=[a for a in requests if (a['rob'],a['pdest'])==(b['rob'],b['pdest']) and a['cycle']<b['cycle']<=a['cycle']+2]
 if not a:continue
 assert len(a)==1; a=a[0]
 if b['illegal']:assert b['vecwen']==b['v0wen']==0
 else:
  signed=lambda x:x-256 if x>=128 else x
  expected=sum(signed((a['src0']>>(8*i))&255)*signed((a['src1']>>(8*i))&255) for i in range(8))&0xffffffff
  assert b['result']==expected and b['vecwen']+b['v0wen']==1
 matched.append(dict(request=a,response=b))
legal=[x for x in matched if not x['response']['illegal']]; illegal=[x for x in matched if x['response']['illegal']]
assert legal and illegal and commits and len(traps)>=2
for t in traps:
 assert t['cause']==t['mcause']==2 and t['instruction']==t['mtval'] and t['pc']==t['mepc'],t
 assert not any(c['pc']==t['pc'] and abs(c['cycle']-t['cycle'])<8 for c in commits),'Faulting VDOT committed'
for label,rows in (('fu-requests',requests),('fu-responses',responses),('vdot-commits',commits),('precise-traps',traps)):
 with (p/(label+'.csv')).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
smoke=p.parent/'t10-smoke-final-20261014/check.json'
assert json.loads(smoke.read_bytes())['status']=='VDOT_T10_CORE_SMOKE_PASS'
record=dict(status='T10_BOUNDED_WAVE_PATH_PASS',timestamp='DiffTrapEvent.cycleCnt after rising-edge eval',matched=matched,commits=commits,traps=traps,complete_guest=True,full_capture=False,smoke_check_sha256=hashlib.sha256(smoke.read_bytes()).hexdigest(),scope=fu,raw_events_sha256=hashlib.sha256((p/'events.csv').read_bytes()).hexdigest(),limitations='Bounded excerpt; no redirect/dependency/fault-injection claim. ROB commit is observed through DiffTest delayer input, without an independently traced commit ROB tag.')
(p/'wave-summary.json').write_bytes((json.dumps(record,indent=2,sort_keys=True)+'\n').encode())
print(json.dumps(dict(status=record['status'],legal=len(legal),illegal=len(illegal),commits=len(commits),traps=len(traps))))
