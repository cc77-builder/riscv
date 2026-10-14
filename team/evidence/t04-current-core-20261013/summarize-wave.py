import csv
import json
from pathlib import Path
import re
import sys

folder=Path('/mnt/c/Code/RVInno/riscv/team/out/t04-current-20261013')
state={}
commits=[]
alu=[]
commit_scope=re.compile(r'(.+\.backend\.inner_ctrlBlock\.rob\.difftest_delayer(?:_\d+)?)\.i_valid$')
fu_scope=re.compile(r'(.+\.VialuFix)\.io_in_valid$')

def value(scope, suffix):
    bits=state.get(scope+'.'+suffix)
    if bits is None or not re.fullmatch('[01]+', bits):
        raise RuntimeError('Missing/unknown signal: '+scope+'.'+suffix)
    return int(bits,2)

def sample(cycle):
    for signal in list(state):
        match=commit_scope.fullmatch(signal)
        if match and state[signal]=='1':
            scope=match[1]
            pc=value(scope,'i_pc')
            if 0x8000012c<=pc<=0x80000142:
                commits.append(dict(cycle=cycle,scope=scope,pc=hex(pc),instruction=hex(value(scope,'i_instr')),
                                    vecwen=value(scope,'i_vecwen'),wdest=value(scope,'i_wdest')))
        match=fu_scope.fullmatch(signal)
        if not match: continue
        scope=match[1]
        if state[signal]=='1' and value(scope,'io_in_ready'):
            alu.append(dict(cycle=cycle,scope=scope,phase='in',fuOpType=value(scope,'io_in_bits_ctrl_fuOpType'),
                            vsew=value(scope,'io_in_bits_ctrl_vpu_vsew'),
                            src0=hex(value(scope,'io_in_bits_data_src_0')),src1=hex(value(scope,'io_in_bits_data_src_1')),result=''))
        if value(scope,'io_out_valid') and value(scope,'io_out_ready'):
            alu.append(dict(cycle=cycle,scope=scope,phase='out',fuOpType='',vsew='',src0='',src1='',result=hex(value(scope,'io_out_bits_res_data'))))

last=None
with (folder/'wave-events.csv').open(newline='') as handle:
    for row in csv.DictReader(handle):
        time=int(row['time'])
        if last is not None and time!=last:
            if time<last: raise RuntimeError('Unordered FST events')
            # Default --dump-wave uses architectural cycleCnt as its timestamp.
            for cycle in range(last,time): sample(cycle)
        last=time
        # FST bus names include a presentation suffix, e.g. "pc [63:0]".
        signal=re.sub(r' \[\d+:\d+\]$', '', row['signal'])
        state[signal]=row['value']
if last is not None: sample(last)
for name,rows,columns in (
    ('vadd-commit-events.csv',commits,['cycle','scope','pc','instruction','vecwen','wdest']),
    ('vector-fix-alu-events.csv',alu,['cycle','scope','phase','fuOpType','vsew','src0','src1','result'])):
    with (folder/name).open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=columns)
        writer.writeheader(); writer.writerows(rows)
vadd=[row for row in commits if row['instruction']=='0x21101d7']
incoming=[row for row in alu if row['phase']=='in']
outgoing=[row for row in alu if row['phase']=='out']
expected=[0x0909090909090909,0xf0f2f4f6f8fafcfe,0xfefe000000007f80]
if not len(vadd)==len(incoming)==len(outgoing)==3: raise RuntimeError('Wrong vadd event counts')
for i,(commit,request,response) in enumerate(zip(vadd,incoming,outgoing)):
    if request['scope']!=response['scope'] or request['fuOpType']!=64 or request['vsew']!=0: raise RuntimeError('Wrong FU mapping')
    if int(response['result'],16)&((1<<64)-1)!=expected[i]: raise RuntimeError('Wrong FU low64 result')
    if not request['cycle']<response['cycle']<=commit['cycle'] or commit['vecwen']!=1 or commit['wdest']!=3 or commit['pc']!='0x80000138': raise RuntimeError('Wrong commit order/destination')
record=dict(status='T04_VADD_WAVE_PATH_PASS',timestamp='DiffTrapEvent.cycleCnt; default --dump-wave sampling after rising-edge eval',
            commit_observation='ROB-side inputs of DiffTest delayer; excludes downstream instrumentation delay',
            events=[dict(case=i,input_cycle=a['cycle'],output_cycle=b['cycle'],commit_cycle=c['cycle'],result=b['result'],scope=a['scope'])
                    for i,(a,b,c) in enumerate(zip(incoming,outgoing,vadd))])
(folder/'wave-summary.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps(record,sort_keys=True))
