"""Read completed suite logs; never run hardware or change source/log bytes."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT = Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
SUITE = ROOT.parent/'runs/o1-fullcore-suite-01'
OUT = Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('job',choices=('hello-vadd','negative-vdot','functional-0'))
args=parser.parse_args()
job=SUITE/args.job
runtime=json.loads((job/'result.json').read_text())
assert runtime['status'] not in ('RUNNING','FAILED'), runtime
assert 'finished' in runtime, 'job has no completion receipt'
target=OUT/args.job
target.mkdir(exist_ok=False)
path=ROOT/'team/optimizations/o1/fullcore/analyze.py'
spec=importlib.util.spec_from_file_location('independent_o1_audit',path)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
raw=(job/'run.log').read_bytes()
text=(job/'run.log').read_text(encoding='utf-8',errors='strict')
partial=args.job=='negative-vdot'
result=a.analyze(text,require_complete=not partial)
original=json.loads((job/'observation.json').read_text())
assert result==original,'structural or text-input hash divergence from suite observation'
expected='O1_PARTIAL_TRACE_AUDIT' if partial else 'O1_TRACE_PASS'
assert result['status']==expected
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(text.encode('utf-8'))==result['input_sha256']
# A second call deliberately preserves CRLF bytes as decoded text. Its only
# permitted difference is the digest of that different input string.
raw_result=a.analyze(raw.decode('utf-8'),require_complete=not partial)
raw_digest=raw_result.pop('input_sha256')
normalized_without_digest={k:v for k,v in result.items() if k!='input_sha256'}
assert raw_result==normalized_without_digest,'newline treatment changed observer semantics'
assert raw_digest==sha(raw)
(target/'observation.json').write_text(json.dumps(result,indent=2)+'\n')
receipt={
 'status':'COMPLETED_LOG_INDEPENDENT_AUDIT_PASS',
 'job':args.job,'suite_job_status':runtime['status'],'suite_exit_code':runtime['exit_code'],
 'observation_status':result['status'],'require_complete':not partial,
 'command':[sys.executable,'-B',str(Path(__file__).resolve()),args.job],
 'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'checker_path':str(path),'checker_sha256':sha(path.read_bytes()),
 'audit_script_sha256':sha(Path(__file__).read_bytes()),
 'input_files_sha256':{str(job/name):sha((job/name).read_bytes()) for name in
     ('run.log','stderr.log','stdout.log','result.json','observation.json')},
 'schema':result['schema'],'counts':result['counts'],
 'original_run_log_crlf_count':raw.count(b'\r\n'),
 'raw_bytes_sha256':sha(raw),'analyze_text_sha256_after_read_text':result['input_sha256'],
 'independent_result_identical_to_suite_observation':True,
 'raw_decode_and_universal_newline_semantics_identical_except_input_sha256':True,
 'new_emulator_started_by_audit':False,'entire_suite_complete':False,
 'limits':['input_sha256 identifies the exact UTF-8 text argument to analyze; original file bytes remain separately bound by raw SHA256.',
           'Only the named completed job is audited. A partial negative audit is not a normal-run or full-suite pass.',
           'No raw log or frozen source file was modified.'],
}
(target/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'job':args.job,'suite_job_status':runtime['status'],
                  'observation_status':result['status'],'counts':result['counts'],
                  'crlf_count':raw.count(b'\r\n')},indent=2))
