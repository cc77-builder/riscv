"""Preserve literal command hyphens in a fresh document build directory.

Reuses the two unaffected completed booklets by exact bytes, with their original
logs and source identity. Does not rerun figures, engineering programs or tests.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage', type=Path, required=True)
args = parser.parse_args()
stage = args.stage.resolve()
base = stage / 'build-08'
out = stage / 'build-09'
root = out / 'source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
started = datetime.now(timezone.utc).isoformat()
frozen = json.loads((base / 'frozen-sources.json').read_text(encoding='utf-8'))
assert all(sha(base / 'source' / key) == value for key, value in frozen.items()), 'Base-build input changed'
fix = stage / 'build09-technical-stage3.json'
assert sha(fix) == 'c3e957c21c6ac5b7fafc03027f33b60c0e07c24378c31c7eda03f63e9ec5e2a9'
assert sha(base / 'source/content/technical-stage3.json') == 'd3536a813f2583475d8996f57c13e9050edcf32567f572eb0861c0dc85188139'
old = json.loads((base / 'source/content/technical-stage3.json').read_text(encoding='utf-8'))
cmd = 'python -X utf8 -B performance/portable.py --archive evidence/20261019-performance-ab --campaign campaign-01 --output /absolute/new/portable-verification.json'
assert old[1][2].count('    ' + cmd) == 1
old[1][2] = old[1][2].replace('    ' + cmd, '```text\n' + cmd + '\n```')
cmd2 = 'package_evaluation.py --verify ARCHIVE --receipt NEW_JSON'
assert old[2][2].count(cmd2) == 1
old[2][2] = old[2][2].replace(cmd2, '`' + cmd2 + '`')
assert old[4][2].count('objcopy --strip-debug') == 1
old[4][2] = old[4][2].replace('objcopy --strip-debug', '`objcopy --strip-debug`')
assert json.loads(fix.read_text(encoding='utf-8')) == old
assert not out.exists(), 'Preserve existing output before recovery'
out.mkdir()
shutil.copytree(base / 'source', root, ignore=shutil.ignore_patterns('output', '__pycache__'))
shutil.copy2(fix, root / 'content/technical-stage3.json')
subprocess.run([sys.executable, '-X', 'utf8', str(root / 'expand_reports.py')], check=True)
changed = [key for key, value in frozen.items() if sha(root / key) != value]
assert set(changed) == {'content/technical-stage3.json', 'sections/stage3.tex'}, changed
new_freeze = {key: sha(root / key) for key in frozen}
(out / 'frozen-sources.json').write_text(json.dumps(new_freeze, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
compiler = Path(r'D:\Programs\texlive\2026\bin\windows\xelatex.exe')
names = {'main': '三阶段技术文档_合订本.pdf', 'stage1': '第一阶段_执行日志与过程文档.pdf',
         'stage2': '第二阶段_设计与基础测试文档.pdf', 'stage3': '第三阶段_协同仿真与性能分析.pdf'}
reused = []
for key in ('stage1', 'stage2'):
    source = base / key / names[key]
    assert source.is_file() and (base / key / (key + '-pass3.txt')).is_file()
    shutil.copytree(base / key, out / key)
    assert sha(out / key / names[key]) == sha(source)
    reused.append({'document': key, 'from_build': 'build-08' if key == 'stage1' else 'build-07', 'sha256': sha(source),
                   'basis': 'Only stage3 command markup/section changed; all other frozen source bytes and these booklet entry points are unchanged.'})

def build(key):
    start = time.monotonic()
    p = subprocess.run([sys.executable, '-X', 'utf8', str(root / 'build.py'),
                        '--compiler', str(compiler), '--output-dir', str(out / key),
                        '--documents', key], capture_output=True)
    (out / (key + '-driver.log')).write_bytes(p.stdout + p.stderr)
    print(json.dumps({'document': key, 'exit': p.returncode, 'seconds': round(time.monotonic()-start, 3)}), flush=True)
    return key, p.returncode

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(build, ('main', 'stage3')))
assert all(code == 0 for _, code in results), results
assert all(sha(root / key) == value for key, value in new_freeze.items()), 'Report source changed during build'
assert all(sha(base / 'source' / key) == value for key, value in frozen.items()), 'Base-build source changed'
delivery = out / 'delivery'
delivery.mkdir()
files = []
for key, name in names.items():
    target = delivery / name
    shutil.copy2(out / key / name, target)
    files.append({'document': key, 'build_origin': {'main':'build-09','stage1':'build-08','stage2':'build-07','stage3':'build-09'}[key],
                  'path': str(target), 'bytes': target.stat().st_size, 'sha256': sha(target)})
receipt = {'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
           'driver_sha256': sha(Path(__file__)), 'original_delta_sha256': '843ac7ff9efb6a6f641e597ed8c470300301d5d41cf92343b5ae60eccf303d55',
           'source_fix_sha256': sha(fix), 'base_build': 'build-08',
           'rebuilt_documents': ['main','stage3'], 'reused_documents': reused,
           'parallel_documents': 2, 'passes_per_rebuilt_document': 3,
           'changed_source_paths': changed, 'source_unchanged_during_build': True,
           'base_build_preserved': True,
           'scope': 'Three existing command fragments receive code markup to preserve double hyphens. Command bytes and engineering facts are unchanged. 31 figure assets reused unchanged. No new engineering execution.',
           'files': files}
(out / 'build-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-X','utf8',str(root/'qa/inspect_reports.py'),
               '--compiled-dir',str(delivery),'--logs-dir',str(out),
               '--result-dir',str(out/'qa'),'--render-dir',str(out/'qa-render')],check=True)
inspection=json.loads((out/'qa/pdf-inspection.json').read_text(encoding='utf-8'))
assert set(inspection['reports']) == set(names)
for key,record in inspection['reports'].items():
    assert record['a4_all_pages'] and record['figure_captions_unique'], key
    for field in ('final_log_diagnostics','outside_text','footer_mismatches','placeholder_pages'):
        assert not record[field], (key,field,record[field])
shutil.copy2(out/'qa/pdf-inspection.json',root/'qa/pdf-inspection.json')
shutil.copy2(out/'qa/page-map.json',root/'figures/page-map.json')
(root/'交付校验.json').write_text(json.dumps({'build':'build-09','status':'AUTOMATED_INSPECTION_COMPLETE_VISUAL_REVIEW_PENDING',
    'inspection':'qa/pdf-inspection.json','reports':inspection['reports'],'scope':receipt['scope']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'publication-manifest.json').write_text(json.dumps({'build':'build-09','status':'BUILD_CANDIDATE_VISUAL_REVIEW_PENDING','files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
metadata=out/'metadata.zip'
with zipfile.ZipFile(metadata,'w',zipfile.ZIP_DEFLATED) as archive:
    for key in names:
        for ext in ('.log','.aux','-pass3.txt'):
            archive.write(out/key/(key+ext),str(PurePosixPath(key)/(key+ext)))
    for name in ('build-receipt.json','frozen-sources.json'):
        archive.write(out/name,name)
    for p in sorted((root/'figures').glob('*.pdf')):
        archive.write(p,'source/figures/'+p.name)
    for rel in ('figures/screenshot-layout.json','figures/diagram-layout.json','figures/evidence-20261105/generated-figures.json'):
        archive.write(root/rel,'source/'+rel)
    for p in sorted((out/'qa').glob('*.json')):
        archive.write(p,'qa/'+p.name)
files.append({'document':'metadata','path':str(metadata),'bytes':metadata.stat().st_size,'sha256':sha(metadata)})
print(json.dumps({'files':files},ensure_ascii=False),flush=True)
