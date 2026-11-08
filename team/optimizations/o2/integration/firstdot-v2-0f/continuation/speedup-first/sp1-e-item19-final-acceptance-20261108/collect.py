"""Pure-host collectors for final item19 roles; native target libraries are never loaded."""
from pathlib import Path
import argparse,collections,functools,hashlib,importlib.util,json,re,sys

def need(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text())
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bindings(events,manifest,elf_read,flushed):
 roles={r['pc']:r for r in manifest['pc_roles']};live={};accept={};response={};arch=[];group=collections.defaultdict(list)
 for cy,_,kind,row in events:
  if kind!='SCHEMA':group[cy].append((kind,row))
 for cy,rows in sorted(group.items()):
  # Retirement observes the previous allocation if a ROB index is reused this cycle.
  def age(a,b):return 0 if a['rob']==b['rob'] else 1 if flushed(a['rob'],b['rob'],0)else -1
  for row in sorted([r for k,r in rows if k=='COMMIT'],key=functools.cmp_to_key(age)):
   e=live[row['rob']];a=accept[e['seq']];out=response[e['seq']]
   need(row['pc']==e['pc'] and out['cycle']<=cy,'retirement allocation')
   arch.append(dict(pc=e['pc'],word=e['word'],vd=(e['word']>>7)&31,vs1=a['vs1']&((1<<64)-1),vs2=a['vs2']&((1<<64)-1),vl=a['vl'],result=out['data'],exception=out['exception']))
  for kind,row in rows:
   if kind=='ENQUEUE':
    r=roles.get(row['pc']);need(r is not None and r['word']==row['word']==int.from_bytes(elf_read(row['pc'],4),'little'),'frozen PC/word');live[row['rob']]=dict(row)
   elif kind=='ACCEPT':
    e=live[row['rob']];r=roles[e['pc']];vpu=row['vpu'];need(row['vl']==8 and row['illegal']==0 and (vpu>>187)&255==0 and (vpu>>178)&1==1 and (vpu>>170)&255==0,'legal configuration')
    need(row['vs1']&((1<<64)-1)==r['vs1_low64'] and row['vs2']&((1<<64)-1)==r['vs2_low64'],'active inputs')
    e['seq']=row['seq'];accept[row['seq']]=row
   elif kind=='RESPONSE':response[row['seq']]=row
 need([a['pc']for a in arch]==manifest['expected_retired_pc_sequence'],'exact full call retired sequence')
 need(len(arch)==77 and all(a['result']==int.from_bytes(bytes.fromhex(manifest['expected_dot128']),'little')and a['exception']==0 for a in arch),'full128 committed results')
 return arch

def supplement(text,mode,stage,reference,exit_code):
 stage=Path(stage);sys.path.insert(0,str(stage/'runtime'))
 a=load('frozen_supplement',stage/'runtime/adapter.py');c=a.C;m=a.M
 plain=a.runtime_gate.normalize_console(text)
 need(exit_code==0 and plain.count('HIT GOOD TRAP')==1 and 'HIT BAD TRAP'not in plain,'complete normal trap')
 need('SCHED_'not in plain,'plain functional EMU required')
 need(re.findall(r'^The image is ([^\n]+)$',plain,re.M)==[c['runtime']['bin']['path']],'frozen image')
 need(re.findall(r'^The reference model is ([^\n]+)$',plain,re.M)==[reference] and reference==c['runtime']['normal_reference']['path'],'normal reference')
 need(plain.count('The first instruction of core 0 has commited. Difftest enabled.')==1,'live DiffTest')
 a.runtime_gate.validate_failure_markers(plain,False)
 if mode=='candidate':
  detail=a.collect(plain,'candidate-normal',exit_code);need(detail['status']=='SUPPLEMENT_TRACE_HIT','same SP1 S0/S1 must hit');base=a.base
 else:
  base=load('supplement_legacy_o2',stage.parent/'sp1-e-g0/protection/host/legacy_o2.py')
  need(not re.search(r'SP1_(?:STATE|SCHEMA|ACCEPT|COMMIT)',plain),'mixed hardware observer')
  detail=base.analyze(plain,require_complete=True)
 events,uart=base.extract_events_and_uart(plain)
 rows=re.findall(r'OC19_[^\r\n]*',uart);need(rows==a.normal_adapter.expected_uart(m),'41 full ordered calls and actual CSR/ABI judge')
 arch=bindings(events,m,a.elf_read,base.flushed)
 guest=re.findall(r'Guest cycle spent:[ \t]*([0-9]+)',plain);instr=re.findall(r'Core-0 instrCnt = ([0-9]+), cycleCnt = ([0-9]+)',plain);need(len(guest)==len(instr)==1,'single completion counter')
 # Numeric cross-hardware equality uses active source bytes, full result, and identical ISA/configuration.
 # Same-hardware observer digest retains all original parsed fields (including raw inactive payload).
 material=dict(architectural_commit=[{k:x[k]for k in ['pc','word','vd','vl']}for x in arch],source=[[x['vs1'],x['vs2']]for x in arch],result=[[x['result'],x['exception']]for x in arch],observer=events,uart_checks=rows,csr_contract=dict(bin=c['runtime']['bin']['sha256'],csr=m['expected_caller_csrs'],checks=rows),div_events=[(k,r)for _,_,k,r in events if k.startswith('DIV_')],completion=dict(guest_cycles=int(guest[0]),instr_count=int(instr[0][0]),cycle_count=int(instr[0][1])))
 return dict(status='SUPPLEMENT_FULL_NORMAL_PASS',mode=mode,guest_cycles=int(guest[0]),detail=detail,commits=77,calls=41,full128=True,functional_replay={k:digest(v)for k,v in material.items()},cross_hardware_architecture=digest(arch),performance_measured=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['supplement','original'],required=True);p.add_argument('--stage',required=True);p.add_argument('--mode',choices=['candidate','baseline'],required=True);p.add_argument('--role-dir',required=True);p.add_argument('--reference',required=True);p.add_argument('--exit',type=int,required=True);p.add_argument('--out',required=True);a=p.parse_args()
 rd=Path(a.role_dir);text=(rd/'stdout.log').read_text()+(rd/'stderr.log').read_text()
 if a.kind=='supplement':result=supplement(text,a.mode,a.stage,a.reference,a.exit)
 else:
  original=load('original_numeric',Path(a.stage).parent/'sp1-e-b4-r4-20261106/numeric/adapter.py')
  result=original.collect(text,'o2-control',a.mode,a.reference,a.exit,rd.name)
 deps=sorted({str(Path(x.__file__).resolve())for x in sys.modules.values()if getattr(x,'__file__',None)and str(x.__file__).startswith('/home/')and str(x.__file__).endswith('.py')})
 Path(a.out).write_text(json.dumps(dict(collector=result,loaded_sources=deps),indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
