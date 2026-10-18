import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
base=Path('/home/amesotten/.cache/codex-rvinno/o1-integration-20261018')
root=Path('/mnt/c/Code/RVInno/riscv')
out=root/'team/evidence/o1-integration-20261018'
native=base/'source-6ee2e8f10475549e'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x): p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
binding=json.loads((native/'build/source-binding.json').read_bytes())
physical={p:sha(native/p) for p in binding['physical_root_sha256']}
changed=[p for p,h in physical.items() if h!=binding['physical_root_sha256'][p]]
if changed!=['src/main/scala/xiangshan/backend/exu/ExeUnit.scala']: raise ValueError(changed)
actual_blobs={p:hashlib.sha1(b'blob '+str((native/p).stat().st_size).encode()+b'\0'+(native/p).read_bytes()).hexdigest() for p in physical}
save(out/'hardware-source-binding.json',dict(original=binding,reviewed_delta=changed,
     actual_compiler_sha256=physical,actual_compiler_git_blobs=actual_blobs,
     scope='Native frozen source plus explicit FuType.vdot.U fix; only FU tops elaborated'))
shutil.copyfile(root/'team/out/o1-futype-fix.patch',out/'hardware-futype-fix.patch')
shutil.copyfile(root/'team/out/o1-source-pack-nativegit/source-pack.json',out/'source-pack.json')
shutil.copyfile(root/'team/out/o1-source-pack-nativegit/changes.patch',out/'source-pack.patch')
shutil.copyfile(root/'team/out/run-o1-integration.sh',out/'run-hardware.sh')
shutil.copyfile(root/'team/out/o1-switch-validation.sh',out/'check-switches.sh')
source_names=set(physical)
for line in (base/'fu-attempt-03/source.sha256').read_text().splitlines():
    digest,name=line.split(maxsplit=1)
    if sha(native/name)!=digest: raise ValueError('source drift '+name)
    source_names.add(name)
for name in ('team/models/vdot/data/manifest.json','team/models/vdot/data/directed.jsonl','team/models/vdot/data/random.jsonl'):
    source_names.add(name)
with tarfile.open(out/'hardware-source.tar.gz','w:gz') as tar:
    for name in sorted(source_names): tar.add(native/name,arcname=name,recursive=False)
records={}
with tarfile.open(out/'hardware-validation.tar.gz','w:gz') as tar:
    for label in ('fu-attempt-01','fu-attempt-02','fu-attempt-03','switch-validation'):
        folder=base/label
        records[label]=(folder/'runner.status').read_text().strip()
        for p in sorted(folder.rglob('*')):
            if not p.is_file(): continue
            if any('obj' in part for part in p.relative_to(folder).parts):
                if p.name!='VVDotFuTestTop': continue
            tar.add(p,arcname=p.relative_to(base),recursive=False)
        shutil.copyfile(folder/'runner.log',out/(label+'.log'))
    for p in (base/'tools').glob('*.deb'): tar.add(p,arcname='local-tools/'+p.name,recursive=False)
if records['fu-attempt-03']!='exit_code=0' or records['switch-validation']!='exit_code=0': raise ValueError(records)
save(out/'hardware-validation.json',dict(attempts=records,fu_simulated=True,parent_simulated=False,
  fullcore_simulated=False,default_unset_equals_explicit_off=True,invalid_configurations_rejected=4,
  o1_accepted=False,source_commit=subprocess.check_output(['git','-C',str(native),'rev-parse','HEAD'],text=True).strip(),
  source_delta='hardware-futype-fix.patch',new_environment='Locally unpacked Ubuntu ripgrep 14.1.0-1; project cache only',
  tools={name:subprocess.check_output(command,stderr=subprocess.STDOUT,text=True).splitlines()[0] for name,command in {
    'verilator':['verilator','--version'],'clang':['clang++-19','--version'],'g++':['g++','--version'],
    'java':['/usr/lib/jvm/java-21-openjdk-amd64/bin/java','-version'],'python':['python3','--version']}.items()}))
print('O1_HARDWARE_EVIDENCE_PACKAGED')
