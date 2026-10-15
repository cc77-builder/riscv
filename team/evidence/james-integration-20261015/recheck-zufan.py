import gzip,hashlib,importlib.util,json,subprocess,sys,tarfile,io
from pathlib import Path
root=Path.cwd();out=root/'team/out/integration-20261015'
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blob(ref,name):return subprocess.check_output(['git','show',ref+':'+name])
spec=importlib.util.spec_from_file_location('compact',root/'team/scripts/check_t12_compact.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
base=root/'team/evidence/t12-r2-20261014';result={'scope':'offline archived-byte, plan regeneration and transcript recheck; no new DUT execution; original runtime binaries not present'}
for folder in [base,root/'team/evidence/t12-zufan-integration-20261014']:
 lines=(folder/'SHA256SUMS').read_text().splitlines()
 for line in lines:
  digest,name=line.split('  ',1);require(sha(folder/name)==digest,'archive digest: '+name)
 result[folder.name]={'sha256_entries':len(lines)}
for name in ['t12-r2-independent-20261014','t12-zufan-integration-20261014']:
 folder=root/'team/evidence'/name;meta=json.loads((folder/'archive.json').read_text());archive=folder/meta['archive']
 require(sha(archive)==meta['sha256'],'bad tar digest')
 with tarfile.open(archive,'r:gz') as t:
  files=t.getmembers()
  for f in files:
   if f.isfile():t.extractfile(f).read()
 result.setdefault(name,{})['tar_members_read']=len(files)
matrices=json.loads((base/'matrix-summary.json').read_text())
for plan,info in matrices.items():
 target=out/(plan+'-regenerated');target.mkdir(exist_ok=False)
 generator=target/'generate.py';generator.write_bytes(blob(info['source'],'team/tests/generate_t12.py'))
 data=target/'data';cmd=[sys.executable,'-B',str(generator),'--output',str(data)]
 if 'lean' in plan:cmd+=['--baseline','lean','--include-chain']
 subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
 parts=[]
 for row in info['slices']:
  suffix=str(row['start']).zfill(3);build=base/plan/('build-'+suffix);run=base/plan/('run-'+suffix)
  saved=build/'data/manifest.json';require(sha(saved)==sha(data/'manifest.json'),'regenerated manifest differs')
  receipt=json.loads((run/'receipt.json').read_text());c.bind(receipt,data,info['source'])
  raw=gzip.decompress((run/'run.log.gz').read_bytes());require(hashlib.sha256(raw).hexdigest()==row['log_sha256']==receipt['run_log_sha256'],'log drift')
  parts.append(c.check(raw.decode(),data,row['start'],row['count'],row['exit_code']))
 aggregate=c.aggregate(parts,data)
 result[plan]={k:aggregate[k] for k in ('status','executed')};result[plan]['slices']=len(parts);result[plan]['source']=info['source'];result[plan]['input_regeneration_exact']=True
(out/'zufan-offline-recheck.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
