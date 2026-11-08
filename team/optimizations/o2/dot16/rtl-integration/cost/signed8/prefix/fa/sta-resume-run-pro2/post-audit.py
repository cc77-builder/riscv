import datetime,hashlib,json,os,pathlib,signal,time
signal.alarm(25);os.sched_setaffinity(0,{3});os.setpriority(os.PRIO_PROCESS,0,5)
base=pathlib.Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main')
out=base/'sta-resume-01';t0=time.monotonic()
planpath=base/'input-sta-02/PLAN_ONLY.json';planraw=planpath.read_bytes()
assert len(planraw)==16512 and hashlib.sha256(planraw).hexdigest()=='cf80fbb5908e93b4faa8beece2774c84038f31bd0ad289da9227a42230fa7d3f'
plan=json.loads(planraw)
records={}
for name in ('result.json','graph-audit.json','inputs.json','timing.tcl','sta.log','setup-checks.rpt','r2r.rpt','i2r.rpt','r2o.rpt','i2o.rpt','ready.rpt'):
 p=out/name
 if not p.exists(): records[name]=dict(exists=False);continue
 b=p.read_bytes();records[name]=dict(exists=True,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),text=b.decode())
result=json.loads(records['result.json']['text'])
inputs=json.loads(records['inputs.json']['text'])
assert inputs['originals']==plan['original_pins']
pins={**inputs['originals'],**inputs['generated']}
checks=[]
for p,h in pins.items():
 b=pathlib.Path(p).read_bytes();actual=hashlib.sha256(b).hexdigest()
 checks.append(dict(path=p,bytes=len(b),expected_sha256=h,actual_sha256=actual,match=actual==h))
pgids=[32266]+[c['pid'] for c in result['commands'] if 'pid' in c]
groups=[]
for pgid in pgids:
 try:os.killpg(pgid,0);exists=True
 except ProcessLookupError:exists=False
 groups.append(dict(pgid=pgid,absent=not exists))
members=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  raw=(p/'stat').read_text();tail=raw.rsplit(') ',1)[1].split();pgid=int(tail[2])
  if pgid in pgids:members.append(dict(pid=int(p.name),pgrp=pgid,state=tail[0]))
 except FileNotFoundError:pass
inventory=[]
for p in sorted(out.rglob('*')):
 assert not p.is_symlink(),'unexpected symlink'
 if p.is_file():
  b=p.read_bytes();inventory.append(dict(path=str(p.relative_to(out)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
unchanged_records=all(not r['exists'] or hashlib.sha256((out/n).read_bytes()).hexdigest()==r['sha256'] for n,r in records.items())
report=dict(status='CLOSED_STA_TIMEOUT_AUDIT',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),
 source_operation='0250d6044ba18f5fd71831ae3131d2ce.1c1e4dfba5c51505431803f9fd594a56',
 input_count=len(checks),input_checks=checks,all_inputs_match=all(c['match'] for c in checks),
 process_groups=groups,independent_proc_members=members,all_process_groups_absent=all(g['absent'] for g in groups) and not members,
 records_unchanged_after_read=unchanged_records,inventory=inventory,records=records,
 no_new_eda_runs=True,elapsed_seconds=time.monotonic()-t0)
assert report['all_inputs_match'] and report['all_process_groups_absent'] and unchanged_records
print(json.dumps(report,indent=2))
