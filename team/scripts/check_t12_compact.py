"""Source-bound compact T12 transcript verification; no microarchitecture claims."""
import argparse,hashlib,json,re,struct
from pathlib import Path

PINS={'emu':'43fd7b094a3fb8676395dc97ca08443fb2d2d37d1dbfea0d7b9078c67087718f','reference':'e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae','flash':'a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994'}
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(data):
 data=Path(data);m=json.loads((data/'manifest.json').read_text())
 require(m['contract']=='vdot-s8x8-r32-v0.1','contract')
 for name,digest in m['files'].items():
  require(Path(name).name==name,'unsafe generated filename')
  require(sha(data/name)==digest,'input drift: '+name)
 rows=json.loads((data/'cases.json').read_text());byid={r['id']:r for r in rows}
 require(len(byid)==len(rows),'duplicate plan ID')
 return m,byid
def expected_digest(m,byid,start,limit):
 require(type(start)is int and type(limit)is int and 0<=start<len(m['schedule']) and limit>0,'slice bounds')
 h=0xcbf29ce484222325
 def mix(b):
  nonlocal h
  for value in b:h=((h^value)*0x100000001b3)&0xffffffffffffffff
 selected=m['schedule'][start:start+limit]
 for seq,item in enumerate(selected,start):
  row=byid[item['id']];mix(struct.pack('<QQ',seq,item['repeat']));mix(item['id'].encode()+b'\0')
  for r,value in enumerate(row['expected']):mix(bytes(16) if r in row['scratch'] else bytes.fromhex(value))
  bad=row['fault_vl'] is not None
  mix(struct.pack('<6Q',0,row['fault_vl'] if bad else 8,0,3,1,7))
  mix(struct.pack('<2Q',int(bad),2 if bad else 0))
  mix(struct.pack('<6Q',*([0,8,0,3,1,7] if bad else [0]*6)))
 return h,selected

def check(text,data,start,limit,exit_code):
 require(exit_code==0,'actual process did not exit zero')
 m,byid=load(data);expected,selected=expected_digest(m,byid,start,limit)
 text=re.sub(r'\x1b\[[0-9;]*m','',text);lines=text.splitlines()
 require(not re.search(r'\b(?:FAIL|BAD TRAP|ABORT|Assertion failed)\b',text),'failure marker')
 begins=[i for i,s in enumerate(lines) if s.startswith('T12C_BEGIN ')]
 ends=[i for i,s in enumerate(lines) if s.startswith('T12C_END ')]
 controls=[i for i,s in enumerate(lines) if s=='T12_CONTROLS high96=1 preserved=1 csr=1']
 good=[i for i,s in enumerate(lines) if 'HIT GOOD TRAP' in s]
 diff=[i for i,s in enumerate(lines) if 'Difftest enabled' in s]
 require(all(len(x)==1 for x in (begins,ends,controls,good,diff)),'missing/duplicate completion role')
 require(diff[0]<begins[0]<controls[0]<ends[0]<good[0],'completion order')
 require(lines[begins[0]]==f'T12C_BEGIN start={start} limit={limit}','wrong compiled slice')
 require(lines[ends[0]]==f'T12C_END executed={len(selected)} hash=0x{expected:016x}','state/order digest mismatch')
 metrics=[]
 for i,line in enumerate(lines):
  if not line.startswith('T12C_PERF '):continue
  require(begins[0]<i<ends[0],'perf outside run')
  match=re.fullmatch(r'T12C_PERF seq=(\d+) cy=(\d+),(\d+) ir=(\d+),(\d+)',line)
  require(match is not None,'malformed counters')
  seq,cb,ce,ib,ie=map(int,match.groups());require(start<=seq<start+len(selected),'perf outside slice')
  row=byid[m['schedule'][seq]['id']];require(row['kind']=='perf','wrong perf role')
  require(ce>cb and ie>ib,'nonpositive counters')
  metrics.append(dict(seq=seq,id=row['id'],scenario=row['scenario'],method=row['method'],repeat=m['schedule'][seq]['repeat'],dots=row['dots'],cycle_begin=cb,cycle_end=ce,instret_begin=ib,instret_end=ie,cycles=ce-cb,instret=ie-ib,input_sha256=hashlib.sha256(json.dumps(row['before']).encode()).hexdigest()))
 want=[seq for seq,item in enumerate(selected,start) if byid[item['id']]['kind']=='perf']
 require([r['seq'] for r in metrics]==want,'missing/extra/reordered perf')
 return dict(status='T12_ARCHITECTURAL_SLICE_PASS',start=start,limit=limit,executed=len(selected),digest=f'{expected:016x}',metrics=metrics,microarchitectural_events_observed=False)

def bind(meta,data,source):
 require(re.fullmatch('[0-9a-f]{40}',source or ''),'explicit source SHA required')
 require(meta['source']==source,'source mismatch')
 require(meta['manifest_sha256']==sha(Path(data)/'manifest.json'),'manifest mismatch')
 require(meta['runtime_pins']==PINS,'runtime pins mismatch')
 require(meta['exit_code']==0 and meta['completed'] is True,'incomplete runtime')
 require(meta['difftest'] is True and meta['ram']=='128MB','runtime mode')
 require(type(meta['pid']) is int and meta['pid']>0,'missing PID')
 from datetime import datetime
 start,end=(datetime.fromisoformat(meta[k]) for k in ('started_at','finished_at'))
 require(start.tzinfo is not None and end.tzinfo is not None and end>=start,'timestamps')
 require(re.fullmatch('[0-9a-f]{64}',meta['image_sha256']),'image hash')
 argv=meta['argv'];require('--diff' in argv and '--no-diff' not in argv,'DiffTest command')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('log','data','receipt','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--expected-source',required=True);a=p.parse_args()
 try:
  meta=json.loads(a.receipt.read_text());bind(meta,a.data,a.expected_source)
  result=check(a.log.read_text(),a.data,meta['start'],meta['limit'],meta['exit_code'])
  a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 except (ValueError,KeyError,TypeError,OSError) as e:raise SystemExit('T12C_REJECTED: '+str(e))
