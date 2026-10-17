"""Archive completed current-source runs without rewriting raw evidence."""
import gzip,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
repo=Path('/mnt/c/Code/RVInno/riscv')
output=repo/'team/out/james-fullcore-20261016'
destination=repo/'team/evidence/james-fullcore-20261016'
completion=json.loads((cache/'runs/completion.json').read_text())
if completion['status']!='CURRENT_FULLCORE_REVALIDATION_PASS':raise RuntimeError('unfinished validation')
destination.mkdir(exist_ok=False)
def save(path,value):path.write_bytes((json.dumps(value,indent=2)+'\n').encode())
def sha(data):return hashlib.sha256(data).hexdigest()
inventories={}
reviewer=cache/'reviewer-source';reviewer.mkdir(exist_ok=False)
for name,digest in json.loads((cache/'runs/reviewer-inputs.json').read_text()).items():
    data=(repo/name).read_bytes().replace(b'\r\n',b'\n')
    if sha(data)!=digest:raise ValueError('reviewer source drift '+name)
    target=reviewer/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
(reviewer/'tracked-changes.patch').write_bytes(subprocess.check_output(['git','diff','--binary','d3706f0b86ecfdfbb24cb34cbcf2c18a0314f7f9','--','team/scripts','team/tests','team/workloads'],cwd=repo))
for name in ('hardware','hardware-after','source-pack','nemu-build','workloads','runs','reviewer-source'):
    base=cache/name
    items={}
    with tarfile.open(destination/(name+'.tar.gz'),'w:gz') as archive:
        for path in sorted(base.rglob('*')):
            rel=path.relative_to(base)
            if not path.is_file() or any(p in ('objects','obj','__pycache__') for p in rel.parts):continue
            data=path.read_bytes();items[rel.as_posix()]=dict(sha256=sha(data),bytes=len(data))
            archive.add(path,arcname=rel.as_posix(),recursive=False)
    inventories[name]=items
save(destination/'bundle-files.json',inventories)
# Preserve the external driver records and unmodified stdout/stderr build logs.
logs={}
for path in sorted(output.iterdir()):
    if not path.is_file() or path.suffix not in ('.py','.json','.log','.exit','.txt'):continue
    data=path.read_bytes()
    if path.suffix=='.log':
        (destination/(path.name+'.gz')).write_bytes(gzip.compress(data,mtime=0))
        logs[path.name]=dict(sha256=sha(data),bytes=len(data))
    else:(destination/path.name).write_bytes(data)
save(destination/'raw-build-logs.json',logs)
save(destination/'driver-roles.json',dict(executed=['build-core.py','prepare-workloads.py','run-current.py','retry-negative.py','diagnose-control.py','repro-control.py','diagnose-response.py','recheck-negative.py','control-pressure-probe.py','finish-t12-phase.py','continue-regression.py','verify-software-plans.py','inspect-progress.py','check-live-metrics.py','audit-t13-progress.py','validation-record.py','seal-current.py'],unexecuted_drafts=['recover-and-continue.py'],offline_verification='verify-current.py',note='drafts are retained for provenance, never claimed as executed commands'))
for source,name in [(cache/'runs/completion.json','completion.json'),(cache/'runs/hardware-inputs.json','hardware-inputs.json'),(cache/'runs/reference-provenance.json','reference-provenance.json'),(cache/'runs/calibration-check.json','calibration-check.json'),(cache/'runs/analysis/result.json','t13-result.json'),(cache/'runs'/completion.get('t12_suite_directory','t12-suite')/'result.json','t12-result.json')]:
    shutil.copyfile(source,destination/name)
save(destination/'packaging.json',dict(source=completion['source'],bundles={k:len(v) for k,v in inventories.items()},omitted='build objects and full EMU/NEMU binaries; executable digests and exact native paths are retained',actual_fullcore_runs=completion['actual_fullcore_runs']))
(destination/'.gitattributes').write_bytes(b'* -text\n')
(destination/'README.md').write_text('''# James 当前源码全核复验（2026-10-17）

执行硬件固定 d3706f0b86ecfdfbb24cb34cbcf2c18a0314f7f9，报告见
[全核复验](../../docs/james-fullcore-20261016.md)。源码、工具与镜像摘要随包保存。

- `hardware*`、`source-pack`、`nemu-build`：完整构建来源与依赖审计。
- `workloads`：构建镜像、ELF、生成数据及来源；含未执行的原 stream 镜像。
- `runs`：143次实际启动（141次接受、2次排除），包含原始流、失败回执、重判与派生汇总。
- `reviewer-source`：本轮修复检查器/压力序列的源码快照；不冒充硬件重建来源。
- `file-manifest.json`、`bundle-files.json`：容器与每个成员的字节长度/摘要。

软件计划为original190和lean199，两个计划有重叠。T13为126运行、108功能调用、
1404性能窗口，39配对配置；固定seed的三次重放不是独立统计样本。
原负控装载中止与原控制覆盖不足均排除，原stream布局27次未执行。
未代替人工签字、STA/PPA、虚拟化或官方规格验收。

在仓库根目录用Python 3.10+离线复核（需要RISC-V objdump）：

```sh
python3 -B team/evidence/james-fullcore-20261016/verify-current.py \\
  --archive team/evidence/james-fullcore-20261016 \\
  --repo . --output /tmp/james-fullcore-fresh-recheck
```

输出目录必须尚不存在；命令不启动DUT。完整EMU/NEMU可执行文件仅留本机缓存，
归档保存其摘要、构建配方、来源和实际命令，镜像与原始日志可独立复算。
''',encoding='utf-8')
save(destination/'file-manifest.json',{'files':{p.name:sha(p.read_bytes()) for p in sorted(destination.iterdir()) if p.is_file()}})
print('CURRENT_FULLCORE_EVIDENCE_SEALED',flush=True)
