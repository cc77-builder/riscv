import pathlib,subprocess,json,hashlib,gzip,os,datetime,shutil
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:4]))
root=pathlib.Path('/home/lizufan/riscv-lab/r3-perf-20261025-0001')
win=pathlib.Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/working-r3-perf-20261025-0001')
run=root/'run-02'
assert json.loads((run/'runner.status.json').read_text())['passed']
post=root/'post-source'
post.mkdir()
snap={}
for rel,sha in {
'team/optimizations/o4/perf/audit.py':'780f8daa1801fa378d3fa097029e2ddc393d9e906cf4f8a64e27023854326abe',
'team/optimizations/o2/parent/check_trace.py':'68ed6dda4eb513d4b96bf170fdbb666007c2858bd8dc6dd1e7e8592d921a6079',
'team/optimizations/o4/perf/CONTRACT.md':'246e1fb5acbc2daf95794d4957bd36226719832903f15cc3b422ff8470c57cef'}.items():
 raw=(win/rel).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==sha,rel
 dst=post/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
 snap[rel]=sha
(root/'post-source.json').write_text(json.dumps(snap,indent=2)+'\n')
compressed=root/'compressed-replay'
compressed.mkdir()
for name in ['result.log','metadata.log']:
 (compressed/(name+'.gz')).write_bytes(gzip.compress((run/name).read_bytes(),compresslevel=9,mtime=0))
records=[]
for form,control,meta in [('raw',run/'result.log',run/'metadata.log'),('gzip',compressed/'result.log.gz',compressed/'metadata.log.gz')]:
 command=['python3','-B',str(post/'team/optimizations/o4/perf/audit.py'),'--control',str(control),'--metadata',str(meta),'--negative-checks','--output',str(root/('post-'+form+'-audit.json'))]
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (root/('post-'+form+'-audit.log')).open('x') as log:
  proc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(command=command,exit_code=proc.returncode,start=start,end=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 (root/'post-audit-commands.json').write_text(json.dumps(records,indent=2)+'\n')
 if proc.returncode: print((root/('post-'+form+'-audit.log')).read_text()[-6000:]);raise SystemExit(proc.returncode)
 result=json.loads((root/('post-'+form+'-audit.json')).read_text())
 print(form,result['status'],result['counts'],len(result['evidence_mutations']),flush=True)
a=json.loads((root/'post-raw-audit.json').read_text());b=json.loads((root/'post-gzip-audit.json').read_text())
assert {k:v for k,v in a.items() if k!='inputs'}=={k:v for k,v in b.items() if k!='inputs'}
print('RAW_GZIP_SAME_RESULT',flush=True)
