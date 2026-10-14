"""Independently reread T12 bytes, Git blobs, commands and complete/partial coverage.
No runtime log or receipt is rewritten. Requires the original local artifacts.
"""
import argparse,gzip,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('check',Path(__file__).with_name('check_t12_compact.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
sha=c.sha;require=c.require
from t12_instruction_counts import counts as elf_counts
REQUIRED={'team/workloads/t12-perf/main.c','team/workloads/t12-perf/Makefile','team/workloads/t12-perf/sites.S','team/workloads/vdot-exceptions/harness.S','team/workloads/vdot-exceptions/harness.h','team/workloads/vdot-exceptions/layout.h','team/workloads/vdot-exceptions/judge.c','team/tests/generate_t12.py','team/scripts/t12-tests.py','team/scripts/check_t12_compact.py','team/scripts/artifact_guard.py'}
def verify(out,source,repo=ROOT):
 out=Path(out);receipt=json.loads((out/'receipt.json').read_text());build=Path(receipt['build']);b=json.loads((build/'build.json').read_text());data=build/'data'
 require(receipt['source']==b['source']==source,'source mismatch')
 require(sha(build/'build.json')==receipt['build_sha256'],'build receipt drift')
 require(sha(build/'test.bin')==b['image_sha256']==receipt['image_sha256'],'image mismatch')
 require(sha(build/'test.elf')==b['elf_sha256'],'ELF mismatch')
 require(sha(data/'manifest.json')==b['manifest_sha256']==receipt['manifest_sha256'],'plan mismatch')
 require(sha(out/'run.log')==receipt['run_log_sha256'],'log drift')
 require(gzip.decompress((out/'run.log.gz').read_bytes())==(out/'run.log').read_bytes(),'compressed log differs')
 require(set(b['sources'])==REQUIRED,'incomplete source binding')
 for name,digest in b['sources'].items():
  blob=subprocess.check_output(['git','-C',str(repo),'cat-file','blob',source+':'+name])
  require(hashlib.sha256(blob).hexdigest()==digest,'source blob mismatch: '+name)
 m,rows=c.load(data);require(m['generator_sha256']==b['sources']['team/tests/generate_t12.py'],'generator not compiled source')
 require(sha(build/'tools.json')==b['tools_sha256'],'tool record drift')
 for item in json.loads((build/'tools.json').read_text()).values():
  if 'path' in item:require(sha(item['path'])==item['sha256'],'tool binary drift')
 process=json.loads((out/'run.process.json').read_text())
 for key in ('pid','argv','cwd','exit_code','started_at','finished_at','timed_out'):
  require(process[key]==receipt[key],'process receipt mismatch: '+key)
 require(not process['timed_out'],'timeout')
 require((receipt['start'],receipt['limit'])==(b['start'],b['limit']),'wrong compiled slice')
 cmd=b['process']['argv'];require('T12_START='+str(b['start']) in cmd and 'T12_COUNT='+str(b['limit']) in cmd and '-j1' in cmd,'missing compiled bounds')
 require(b['process']['exit_code']==0 and not b['process']['timed_out'],'build failed')
 argv=receipt['argv'];require('--no-diff' not in argv and argv[argv.index('-i')+1]==str(build/'test.bin'),'runtime image/compare command')
 reuse=json.loads((out/'reuse.json').read_text());require(reuse['hardware_source']=='fcb16a8764d342339670df0bbf1bc67ef2028b86' and reuse['production_diff']=='' and reuse['production_rebuilt'] is False,'hardware provenance')
 for name,flag in (('emu',None),('reference','--diff'),('flash','--flash')):
  asset=reuse['assets'][name];require(sha(asset['path'])==asset['sha256']==c.PINS[name],'runtime binary drift')
  require((argv[0] if flag is None else argv[argv.index(flag)+1])==asset['path'],'runtime argv/pin mismatch')
 require(not subprocess.check_output(['git','-C',str(repo),'diff',reuse['hardware_source'],source,'--','src','build.sc']),'hardware changed')
 c.bind(receipt,data,source)
 result=c.check((out/'run.log').read_text(),data,b['start'],b['limit'],receipt['exit_code'])
 actual_counts=elf_counts(build/'test.elf')
 for metric in result['metrics']:
  require(metric['instret']==actual_counts[metric['id']]==c.expected_instret(rows[metric['id']]),'ELF execution amount mismatch')
 result['evidence']=dict(run=str(out.resolve()),receipt_sha256=sha(out/'receipt.json'),log_sha256=receipt['run_log_sha256'],image_sha256=receipt['image_sha256'])
 return result,data
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',nargs='+',type=Path,required=True);p.add_argument('--expected-source',required=True);p.add_argument('--repo',type=Path,default=ROOT);p.add_argument('--complete',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 try:
  require(re.fullmatch('[0-9a-f]{40}',a.expected_source),'full source required')
  paths=[]
  for parent in a.runs:paths += [parent] if (parent/'receipt.json').exists() else sorted(p.parent for p in parent.glob('run-*/receipt.json'))
  verified=[verify(p,a.expected_source,a.repo) for p in paths];require(verified,'no runs')
  results=[v[0] for v in verified]
  if a.complete:result=c.aggregate(results,verified[0][1])
  else:
   ids=[i for r in results for i in r['identities']];require(len({x['seq'] for x in ids})==len(ids),'duplicate partial identity')
   result=dict(status='T12_ARCHITECTURAL_PARTIAL_PASS',executed=len(ids),identities=ids)
  result.update(source=a.expected_source,evidence=[r['evidence'] for r in results],audit_script_sha256=sha(Path(__file__)),checker_sha256=sha(Path(c.__file__)))
  a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],executed=result['executed'],source=a.expected_source)))
 except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as e:raise SystemExit('T12_EVIDENCE_REJECTED: '+str(e))
