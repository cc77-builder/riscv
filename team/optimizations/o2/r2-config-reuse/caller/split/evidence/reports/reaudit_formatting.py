import datetime,hashlib,json,os,pathlib,shutil,subprocess,zipfile
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
R=pathlib.Path('/home/lizufan/riscv-lab/r2s3-split-20261025-0716')
W=pathlib.Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/working-r2s3-split-20261025-0716')
M=pathlib.Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/monitor-r2s3-split-20261025-0716')
rel=pathlib.Path('team/optimizations/o2/r2-config-reuse/caller/split')
native=R/'source-v2'/rel
current=W/rel/'archive.py'; original=native/'archive.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
assert original.read_bytes()==current.read_bytes()+b'\n'
assert sha(original)=='399564150b305d4007a8679419ccc3b3cf4799748c390329795fb2dfe4c8644c'
assert sha(current)=='85d9823ef722e72310293d20eb731bd167804b9bd8c69e0ba0062ea16ca93990'
evidence=W/rel/'evidence'
manifest=json.loads((evidence/'manifest.json').read_text())
for row in manifest['files']:
 p=evidence/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],row['path']
locations=json.loads((evidence/'locations.json').read_text())
for n,pin in locations['runtime_source_sha256'].items():assert sha(W/n)==sha(R/'source-v2'/n)==pin
report={'started':now(),'scope':'one trailing newline removed from auxiliary auditor; frozen runtime source/build/run unchanged','old_auditor_sha256':sha(original),'new_auditor_sha256':sha(current),'commands':[],'new_emu_runs':0}
for label,args in [
 ('archive-v2-02',['--action','pack','--build',str(R/'build-04'),'--run',str(R/'run-02'),'--output',str(R/'archive-v2-02')]),
 ('archive-audit-v2-02',['--action','audit-archive','--archive',str(R/'archive-v2-02'),'--output',str(R/'archive-audit-v2-02.json')])]:
 code='import sys,runpy;sys.path.insert(0,'+repr(str(native))+');sys.argv='+repr([str(current),*args])+';runpy.run_path('+repr(str(current))+',run_name="__main__")'
 argv=['python3','-B','-c',code]
 rec={'argv':argv,'started':now()}
 with (R/(label+'-driver.stdout.log')).open('xb') as so,(R/(label+'-driver.stderr.log')).open('xb') as se:p=subprocess.run(argv,stdout=so,stderr=se)
 rec.update(exit_code=p.returncode,finished=now())
 rec['logs']={stream:sha(R/(label+'-driver.'+stream+'.log')) for stream in ('stdout','stderr')}
 (R/(label+'-driver.json')).write_text(json.dumps(rec,indent=2)+'\n')
 report['commands'].append(rec)
 assert p.returncode==0,(label,(R/(label+'-driver.stderr.log')).read_text())
 print(label,'PASS',flush=True)
old=R/'archive-v2-01';new=R/'archive-v2-02'
assert (old/'payload.zip').read_bytes()==(new/'payload.zip').read_bytes()
assert (old/'original-audit.json').read_bytes()==(new/'original-audit.json').read_bytes()
a=json.loads((new/'archive-manifest.json').read_text())
b=json.loads((old/'archive-manifest.json').read_text())
assert a['evidence_source_sha256']==sha(current)
assert {k:v for k,v in a.items() if k!='evidence_source_sha256'}=={k:v for k,v in b.items() if k!='evidence_source_sha256'}
audit=json.loads((R/'archive-audit-v2-02.json').read_text());assert audit['status']=='SPLIT_ARCHIVE_RAW_AUDIT_PASS'
backup=R/'formatting-v1.zip'
with zipfile.ZipFile(backup,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,p in [('archive.py',original),('archive-manifest.json',old/'archive-manifest.json'),('delivery-manifest.json',evidence/'manifest.json'),('git-stage-initial-failure.json',M/'git-stage-initial-failure.json')]:z.writestr(name,p.read_bytes())
with zipfile.ZipFile(backup) as z:
 assert z.read('archive.py')==original.read_bytes() and z.read('archive-manifest.json')==(old/'archive-manifest.json').read_bytes()
reports=evidence/'reports'
shutil.copyfile(backup,reports/'formatting-v1.zip')
shutil.copyfile(new/'archive-manifest.json',evidence/'split-input-v2/archive-manifest.json')
for label in ('archive-v2-02','archive-audit-v2-02'):
 for suffix in ('-driver.json','-driver.stdout.log','-driver.stderr.log'):
  shutil.copyfile(R/(label+suffix),reports/(label+suffix))
shutil.copyfile(R/'archive-audit-v2-02.json',reports/'archive-audit-v2-02.json')
shutil.copyfile(M/'reaudit_formatting.py',reports/'reaudit_formatting.py')
report.update(status='FORMATTING_REAUDIT_PASS',finished=now(),payload_sha256=sha(new/'payload.zip'),payload_bytes_unchanged=True,original_audit_bytes_unchanged=True,archive_manifest_sha256=sha(new/'archive-manifest.json'),backup_sha256=sha(backup))
(R/'formatting-reaudit-v2-02.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(R/'formatting-reaudit-v2-02.json',reports/'formatting-reaudit-v2-02.json')
files=[{'path':p.relative_to(evidence).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(evidence.rglob('*')) if p.is_file() and p!=evidence/'manifest.json']
manifest.update(created=now(),files=files,file_count=len(files),total_bytes=sum(p['bytes'] for p in files),revision_reason='Auxiliary auditor EOF normalization and fresh archive re-audit; prior exact identities retained in reports/formatting-v1.zip')
(evidence/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'report':report,'evidence_files':len(files),'evidence_bytes':manifest['total_bytes']},indent=2))
