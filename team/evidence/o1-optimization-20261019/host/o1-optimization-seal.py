"""Seal completed current-source validation, never include binaries or objects."""
import gzip,hashlib,io,json,tarfile
from pathlib import Path

root=Path('/mnt/c/Code/RVInno/riscv')
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-optimization-20261019')
out=root/'team/evidence/o1-optimization-20261019'
def sha(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(path.read_text())
for name in ('build.status','split-build.status'):
    assert (cache/'core-build'/name).read_text().strip()=='exit_code=0',name
assert (cache/'core-build/launch.status').read_text().strip()=='0'
extended=load(cache/'extended-01/campaign.json')
software=load(cache/'software-01/campaign.json')
assert extended['status']=='O1_CONTROL_MATRIX_COUNTER_PASS'
assert software['status']=='O1_SOFTWARE_PLANS_PASS'
assert len(extended['runs'])==13 and len(software['runs'])==2
assert len([r for r in extended['runs'] if r['exit_code']==1 and r['name']=='negative'])==1
assert all(r['exit_code']==0 for r in extended['runs'] if r['name']!='negative')
assert all(r['exit_code']==0 for r in software['runs'])
assert {r['baseline']:r['executed'] for r in software['runs']}=={'original':190,'lean':199}
assert software['emu_sha256']==extended['emu_sha256']
source=load(root/'team/out/o1-optimization-source-check-final-02.json')
recheck=load(cache/'software-recheck.json')
assert recheck['status']=='O1_SOFTWARE_REPLAY_AND_NEGATIVES_PASS'
assert len(recheck['negative_probes'])==6
assert load(cache/'extended-recheck.json')['status']=='O1_EXTENDED_RAW_REPLAY_PASS'
for path,digest in source['files'].items():
    assert sha((root/path).read_bytes())==digest,path
host=load(root/'team/out/o1-optimization-tests-02/results.json')
assert {row['name'] for row in host}=={'o1','events','audit','paired','project'}
assert all(row['exit_code']==0 for row in host)
assert 'Ran 88 tests' in (root/'team/out/o1-optimization-software-parallel.log').read_text()
assert '\nOK\n' in (root/'team/out/o1-optimization-software-parallel.log').read_text()
assert 'Ran 30 tests' in (root/'team/out/o1-optimization-paired-environment.log').read_text()
assert '\nOK\n' in (root/'team/out/o1-optimization-paired-environment.log').read_text()
assert load(root/'team/out/o1-optimization-recipe-probe-02.json')['environment_injection_rejected']
out.mkdir(parents=True,exist_ok=False)
mapping={}
def put(relative,data):
    target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
def save(relative,value):put(relative,(json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
def copy(path,relative):
    raw=path.read_bytes();stored=gzip.compress(raw,mtime=0) if path.suffix in ('.log','.txt') else raw
    name=relative+('.gz' if stored is not raw else '')
    put(name,stored)
    mapping[name]=dict(original_path=str(path),original_sha256=sha(raw),original_bytes=len(raw),
                       stored_sha256=sha(stored),stored_bytes=len(stored))
for name in ('core-build','extended-01','software-01'):
    folder=cache/name
    for path in sorted(folder.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(folder)
        if relative.parts[0]=='images':continue
        copy(path,name+'/'+relative.as_posix())
for folder in ('o1-optimization-tests-01','o1-optimization-tests-02'):
    for path in sorted((root/'team/out'/folder).rglob('*')):
        if path.is_file():copy(path,'host/'+folder+'/'+path.relative_to(root/'team/out'/folder).as_posix())
for name in ('o1-optimization-paired-final.log','o1-optimization-paired-environment.log',
             'o1-optimization-software-parallel.log',
             'o1-optimization-recipe-probe.json','o1-optimization-recipe-probe-02.json',
             'o1-optimization-source-check.json','o1-optimization-source-check-final.json',
             'o1-optimization-source-check-final-02.json','o1-optimization-recheck.py',
             'o1-optimization-diagnose.py',
             'o1-optimization-extended-recheck.py',
             'o1-optimization-reference-rejection.json',
             'o1-optimization-20261019-build.sh','o1-optimization-seal.py',
             'o1-optimization-run.py','o1-optimization-tests.py','o1-optimization-recipe-probe.sh'):
    copy(root/'team/out'/name,'host/'+name)
pack=root/'team/out/o1-optimization-20261019-pack'
copy(pack/'source-pack.json','source-pack.json')
copy(cache/'regression-progress.json','regression-progress.json')
copy(cache/'software-recheck.json','software-recheck.json')
copy(cache/'window-observations.json','window-observations.json')
copy(cache/'extended-recheck.json','extended-recheck.json')
for path in sorted(cache.glob('preflight-reference*')):
    if path.is_file():copy(path,'reference-preflight/'+path.name)
paths=[p for p in (root/'team/optimizations/o1').rglob('*') if p.is_file() and 'evidence' not in p.parts
       and p.suffix in ('.py','.sh','.cpp','.scala','.vlt')]
paths += [p for p in (root/'team/scripts').iterdir() if p.is_file() and p.suffix in ('.py','.sh')]
buf=io.BytesIO();inventory={}
with tarfile.open(fileobj=buf,mode='w') as archive:
    for path in sorted(paths):
        raw=path.read_bytes();name=path.relative_to(root).as_posix()
        info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644;info.mtime=0
        archive.addfile(info,io.BytesIO(raw));inventory[name]=sha(raw)
put('tooling-snapshot.tar.gz',gzip.compress(buf.getvalue(),mtime=0));save('tooling-snapshot.json',inventory)
save('review.json',dict(standards=dict(initial_blockers=1,closed=1,remaining_blockers=0),
                       spec=dict(initial_blockers=1,closed=1,remaining_blockers=0),
                       shared_finding='Unbound inherited build environment; closed with restricted environment for probe/build/resume',
                       no_hardware_performance_claim=True))
save('completion.json',dict(status='CURRENT_O1_SOFTWARE_AND_MATRIX_PASS',host_tests=383,
     hardware_revision='77caa4384909b5ada1f03263a6f247c38c426d57',
     source_pack_sha256=sha((pack/'source-pack.json').read_bytes()),emu_sha256=extended['emu_sha256'],
     actual_fullcore_launches=len(extended['runs'])+len(software['runs']),
     original_executed=190,lean_executed=199,actual_log_negative_probes=6,default_o1=False,performance_ab=False,
     new_events_contract_emu_build_executed=False))
put('.gitattributes',b'* -text -whitespace\n')
put('README.md',('''# 当前源码 O1 软件计划与回归证据

硬件固定本地合并77caa4384及source-pack.json；完整构建、13项矩阵/负控/控制窗口运行及original190、lean199完整计划在当前源码模拟器上实际执行。具体退出码、源码与工具身份、原始日志和独立检查见各运行回执。

host保留首次Windows环境失败、WSL重跑及环境隔离修复前后的探针；最终接受383项主机检查。tooling-snapshot保留实际工具源码。工作负载镜像/ELF/bin来自已固定的历史软件归档，未重复打包；模拟器和编译对象也不入Git，仅保留摘要。

本轮没有新events合同入口的完整EMU构建，也没有baseline/T14/O1全核性能A/B。O1默认关闭。历史20.02%不是本轮结果。
''').encode())
save('file-map.json',mapping)
files={p.relative_to(out).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
       for p in sorted(out.rglob('*')) if p.is_file()}
save('files.json',dict(files=files))
print('O1_OPTIMIZATION_EVIDENCE_SEALED',len(files))
