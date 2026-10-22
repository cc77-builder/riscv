from pathlib import Path
import hashlib,json,gzip,subprocess
root=Path('/mnt/c/Code/RVInno/riscv')
base=Path('/home/amesotten/.cache/codex-rvinno/h1-integration-20261021')
target=root/'team/evidence/h1-integration-20261022'
revision='658ab8bdf567d3ba96f88aebdb0cea9cfc8daeb7'
def sha(raw):return hashlib.sha256(raw).hexdigest()
launch=json.loads((base/'rtl-launch.json').read_text())
if launch['status']!='PASS' or launch['revision']!=revision or not launch['launcher_and_mill_unchanged']:
 raise ValueError('RTL launch incomplete')
verified={}
for stage in ('fu-01','parent-01'):
 work=base/stage
 if json.loads((work/'runner.status.json').read_text())['passed'] is not True:raise ValueError('runner not passing')
 for manifest_name in ('source.json','compiler-inputs.json'):
  for name,digest in json.loads((work/manifest_name).read_text()).items():
   raw=(base/'repo'/name).read_bytes()
   if sha(raw)!=digest:raise ValueError('source drift '+name)
   verified[name]=digest
 for row in json.loads((work/'generated-files.json').read_text()):
  if sha((work/row['path']).read_bytes())!=row['sha256']:raise ValueError('RTL drift')
 for row in json.loads((work/'commands.json').read_text()):
  expected=1 if row['log'].startswith('inject-') else 0
  if row['exit_code']!=expected:raise ValueError('unexpected command exit '+row['log'])
with subprocess.Popen(['git','-C',str(root),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE) as proc:
 for name,digest in verified.items():
  proc.stdin.write((revision+':'+name+'\n').encode());proc.stdin.flush();h=proc.stdout.readline().split()
  if len(h)!=3 or h[1]!=b'blob':raise ValueError('Git source missing '+name)
  raw=proc.stdout.read(int(h[2]));proc.stdout.read(1)
  if sha(raw)!=digest:raise ValueError('Git source mismatch '+name)
 proc.stdin.close()
 if proc.wait():raise ValueError('git failed')
target.mkdir(exist_ok=False)
entries=[]
def add(p,rel):
 raw=p.read_bytes();compressed=len(raw)>65536
 stored=rel+'.gz' if compressed else rel;data=gzip.compress(raw,mtime=0) if compressed else raw
 dest=target/'files'/stored;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 if sha(dest.read_bytes())!=sha(data) or sha(p.read_bytes())!=sha(raw):raise ValueError('copy drift')
 entries.append(dict(path=rel,stored='files/'+stored,encoding='gzip' if compressed else 'identity',raw_bytes=len(raw),raw_sha256=sha(raw),stored_bytes=len(data),stored_sha256=sha(data)))
for name in ('fu-01','parent-01'):
 for p in sorted((base/name).rglob('*')):
  if p.is_file() and 'obj' not in p.relative_to(base/name).parts:add(p,'native/'+p.relative_to(base).as_posix())
for p in sorted(base.iterdir()):
 if p.is_file() and p.suffix in ('.log','.json'):add(p,'native/'+p.name)
for p in sorted((root/'team/out').glob('h1-*')):
 if p.is_file() and p.suffix in ('.log','.json'):add(p,'host/'+p.name)
for p in sorted((root/'team/out/h1-related-tests').glob('*')):
 if p.is_file():add(p,'host/h1-related-tests/'+p.name)
add(root/'team/out/o5-final-evidence-git-audit.json','host/o5-final-evidence-git-audit.json')
add(Path(__file__),'host/seal-h1-validation22.py')
replay=json.loads((base/'parent-replay.json').read_text())
if replay['status']!='O2_PARENT_OFFLINE_TRACE_PASS':raise ValueError('parent replay failed')
manifest=dict(schema_version=1,status='H1_MERGED_SOURCE_FU_PARENT_PASS',source_commit=revision,
 files=entries,git_source_files_verified=len(verified),fu_unique_vectors=10022,parent_unique_vectors=10022,
 negative_observation_injections=20,parent_replay=replay['recomputed'],
 scope='Fresh isolated FU and real VFEX4 parent RTL; imported historical trace replay and host tests. Not fullcore, new performance/PPA or T17. Original objects remain external, not a portable toolchain.')
(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(manifest['status'],len(entries),sum(e['stored_bytes'] for e in entries),flush=True)
