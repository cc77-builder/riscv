from pathlib import Path
import hashlib,json,os,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo';assets=base/'inputs'
subprocess.run(['git','-C',str(root),'fetch','origin','James_Hotten'],check=True)
subprocess.run(['git','-C',str(root),'checkout','--detach','c2c3588e425aa5947cff2871bc9ce4a3f17be40f'],check=True)
env=json.loads((base/'native-environment.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,data):p.write_text(json.dumps(data,indent=2)+'\n')
supplements={}
for kind in ('diagnostic','control'):
    build=assets/('supplement-'+kind)
    command=['python3','-B','team/optimizations/o2/fullcore/workloads/build.py','--output',str(build),'--kind',kind]
    state=dict(command=command,environment=env,cwd=str(root),started=time.time())
    save(assets/('supplement-'+kind+'-launch.json'),state)
    with (assets/('supplement-'+kind+'-launch.log')).open('wb') as log:
        rc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    state.update(exit_code=rc,finished=time.time());save(assets/('supplement-'+kind+'-launch.json'),state)
    print(kind,rc,flush=True)
    if rc:raise RuntimeError('supplement failed')
    image=build/('o2-diag.bin' if kind=='diagnostic' else 'o2-control.bin')
    supplements[kind]=dict(build=str(build),sha256=sha(image))
prepared=json.loads((assets/'prepared.json').read_text())
files={}
def add(path,expected=None):
    path=Path(path);actual=sha(path)
    if expected is not None:assert expected==actual,(str(path),expected,actual)
    if str(path) in files:assert files[str(path)]==actual
    files[str(path)]=actual
paths={name:prepared[name] for name in ('reference','negative','hello','flash')}
for path in paths.values():add(path)
receipts={kind:prepared[kind+'_receipt'] for kind in ('negative','hello')}
for path in receipts.values():
    add(path);row=json.loads(Path(path).read_text())
    for group in ('files','tools'):
        for name,digest in row[group].items():add(name,digest)
reference=Path(paths['reference']);add(reference.parents[1]/'.config');add(reference.parent/'vdot-provenance.json')
nemu=json.loads((reference.parent/'vdot-provenance.json').read_text())
for name,digest in nemu['source_sha256'].items():
    add(Path(name[len('@system/'):]) if name.startswith('@system/') else reference.parents[1]/name,digest)
matrix=Path(prepared['t12'])/'runs/t11-matrix-canonical'
matrix_sha=[]
for index in range(8):
    build=matrix/f'build-{index}';receipt=build/'workload-provenance.json';add(receipt)
    row=json.loads(receipt.read_text())
    for group in ('source_sha256','inputs_sha256','images_sha256','am_libraries_sha256'):
        for name,digest in row[group].items():add(name,digest)
    for name,digest in row['am_source_sha256'].items():add(Path(row['am_home'])/name,digest)
    matrix_sha.append(sha(build/'vdot-exceptions.bin'))
for spec in supplements.values():
    build=Path(spec['build']);receipt=build/'build.json';add(receipt);row=json.loads(receipt.read_text())
    for group in ('source_sha256','generated_sha256','images_sha256','am_libraries_sha256'):
        for name,digest in row[group].items():add(Path(name) if Path(name).is_absolute() else build/name,digest)
add(root/'team/scripts/activate.sh')
value=dict(schema_version=1,contract='o2-g3-current-inputs-v1',source_commit=prepared['source_commit'],paths=paths,
           sha256={**{name:sha(path) for name,path in paths.items()},'matrix':matrix_sha},receipts=receipts,files=files,supplements=supplements)
destination=assets/'input-contract-v1.json'
assert not destination.exists();save(destination,value)
print('INPUT_CONTRACT_WRITTEN files='+str(len(files)),flush=True)
