"""Seal integration validation with exact raw/stored byte identities."""
import gzip,hashlib,io,json,re,tarfile
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv');cache=Path('/home/amesotten/.cache/codex-rvinno/sync20')
out=root/'team/evidence/o2-o3-integration-20261020'
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(p.read_text())
assert not out.exists()
assert load(cache/'parent-red-01/runner.status.json')['passed'] is False
assert 'canceled DIV retained idle clock hold' in (cache/'parent-red-01/result.log').read_text()
assert load(cache/'parent-green-01/runner.status.json')['passed'] is True
assert 'cancel_idle_clock_on=0' in (cache/'parent-green-01/result.log').read_text()
assert load(cache/'parent-green-01/independent-trace.json')['status']=='O2_PARENT_OFFLINE_TRACE_PASS'
assert (cache/'legacy-frames-01/runner.status').read_text().strip()=='exit_code=0'
assert 'VFEX4_PARENT_RUNNER_PASS_FULLCORE_PENDING' in (cache/'legacy-frames-01/runner.log').read_text()
assert load(cache/'options-01/results.json')['status']=='COMPILED_MODE_OPTION_PASS'
assert len(load(cache/'options-01/results.json')['cases'])==28
assert load(cache/'options-01/valid-mode-recheck.json')['status']=='VALID_MODE_OUTPUTS_PASS'
assert load(cache/'merged-source-binding.json')['status']=='MERGED_COMPILER_SOURCE_BINDING_PASS'
assert load(root/'team/out/sync20-imported-bytes.json')['mismatches']==[]
for name,status in [('g3','ARCHIVE_BYTES_AND_TRACE_AUDIT'),('g4','ARCHIVE_O1_O2_WINDOWS_RECHECK_PASS'),('o3','O3_NATIVE_OFFLINE_RECHECK_PASS')]:
 p=root/'team/out'/('sync20-'+name+'-replay'+('-final' if name=='o3' else '')+'.json')
 assert load(p)['status']==status
old=load(root/'team/out/sync20-host-02/results.json');delta=load(root/'team/out/sync20-final-deltas/results.json')
assert len(old)==11 and len(delta)==4 and all(r['exit_code']==0 for r in old+delta)
counts={}
for r in old:
 raw=(root/'team/out/sync20-host-02'/r['log']).read_bytes()
 assert sha(raw)==r['sha256']
 counts[r['suite']]=int(re.findall(rb'Ran (\d+) tests?',raw)[-1])
for r in delta:
 raw=(root/'team/out/sync20-final-deltas'/r['log']).read_bytes()
 assert sha(raw)==r['sha256'];counts[r['suite']]=r['tests']
assert sum(counts.values())==631,counts
sources=load(root/'team/out/sync20-final-source.json')['files']
for name,digest in sources.items():assert sha((root/name).read_bytes())==digest,name
out.mkdir(parents=True)
mapping={}
def put(name,raw):
 p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
def save(name,value):put(name,(json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
def copy(p,name):
 raw=p.read_bytes();data=gzip.compress(raw,mtime=0) if p.suffix in ('.log','.patch','.txt') else raw
 stored=name+('.gz' if data is not raw else '')
 put(stored,data);mapping[stored]=dict(source=str(p),raw_bytes=len(raw),raw_sha256=sha(raw),stored_bytes=len(data),stored_sha256=sha(data))
for folder in ('parent-red-01','parent-green-01','legacy-frames-01','options-01'):
 for p in sorted((cache/folder).rglob('*')):
  if not p.is_file():continue
  relative=p.relative_to(cache/folder)
  if any(x in ('obj','rtl') for x in relative.parts):continue
  copy(p,folder+'/'+relative.as_posix())
for name in ('green-overlays.json','merged-source-binding.json'):copy(cache/name,name)
native=Path((root/'team/out/sync20-rtl-pack-red-windows/build-copy.txt').read_text().strip())
runner=native/'team/optimizations/o2/run_rtl.py'
green_sources=load(cache/'parent-green-01/source.json')
assert sha(runner.read_bytes())==green_sources['team/optimizations/o2/run_rtl.py']
copy(runner,'tested-runner/run_rtl.py')
for folder in ('sync20-host-01','sync20-host-02','sync20-final-deltas'):
 for p in sorted((root/'team/out'/folder).rglob('*')):
  if p.is_file():copy(p,'host/'+folder+'/'+p.relative_to(root/'team/out'/folder).as_posix())
for name in ('sync20-g3-replay.json','sync20-g4-replay.json','sync20-o3-replay-final.json','sync20-imported-bytes.json',
             'sync20-final-source.json','sync20-tests.py','sync20-tests-final.py','sync20-final-deltas.py',
             'sync20-parent-red.sh','sync20-parent-green.sh','sync20-options.py','sync20-bind-final.py',
             'sync20-seal.py','sync20-prepare-rtl.py','sync20-prepare-rtl.log','sync20-prepare-windows.log',
             'sync20-materialize-red.log','sync20-bind-final.log','sync20-parent-red.log','sync20-parent-green.log'):
 copy(root/'team/out'/name,'host/'+name)
for p in sorted((root/'team/out/sync20-rtl-pack-red-windows').rglob('*')):
 if p.is_file():copy(p,'red-source-pack/'+p.relative_to(root/'team/out/sync20-rtl-pack-red-windows').as_posix())
inventory={};buf=io.BytesIO()
paths=set(sources)|{'team/optimizations/o1/build_inputs.py','team/optimizations/o1/build_recipe.py','team/scripts/prepare-core-baseline.py'}
with tarfile.open(fileobj=buf,mode='w') as archive:
 for name in sorted(paths):
  raw=(root/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o644;info.mtime=0
  archive.addfile(info,io.BytesIO(raw));inventory[name]=sha(raw)
put('active-source-snapshot.tar.gz',gzip.compress(buf.getvalue(),mtime=0));save('active-source-snapshot.json',inventory)
save('completion.json',dict(status='O2_O3_INTEGRATION_VALIDATION_PASS',base='6ea846edb1e56f80d7e7858984a6f367be34bcf0',
 incoming='676ec737291b3818c0f4bf3d9f542f85fddb53c7',incoming_commits=40,host_tests=sum(counts.values()),suites=counts,
 compiled_options=28,parent_accepted=13515,parent_negative_checks=16,legacy_frame_modes=3,legacy_negative_checks=4,
 imported_evidence_files=3446,new_fullcore_emu_runs=0,new_performance_measurement=False,o1_default=False,o2_default=False,
 limits='Native contract build paths have host gates, not a fresh full EMU build. Imported G3/G4/O3 results retain their original hardware identities. Green runner version and later inventory-only delta are separately bound.'))
put('README.md',('# O2/O3 整合验证证据（2026-10-20）\n\n本目录保留合并后软件检查、导入证据复算、真实父级红灯/绿灯、16类O2观察负控、三模式frames及4类负控和28组已编译开关检查。原始失败和检查器版本均保留；不包含EMU、编译对象或生成RTL。\n\n631项相关主机检查通过。O2父级取消后空闲时钟为0。O1/O2均默认关闭。\n\n本次新增全核EMU运行0次，没有新的性能或PPA测量。旧G3/G4/O3归档未改，原实验绑定不升级为本轮合并源码。绿灯runner完成后增加的库存校验与实际受测编译输入由merged-source-binding.json单独核对。\n').encode())
put('.gitattributes',b'* -text -whitespace\n')
save('file-map.json',mapping)
save('files.json',dict(files={p.relative_to(out).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(out.rglob('*')) if p.is_file()}))
print('O2_O3_INTEGRATION_EVIDENCE_SEALED',len(mapping),sum(counts.values()))
