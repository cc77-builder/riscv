
from pathlib import Path
import subprocess,json,datetime,hashlib
w=Path('/home/riscv/riscv-lab/o1-performance-20261018')
r=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
o=w/'postprocess-launch-01';o.mkdir()
cmd=['python3','-B',str(r/'team/optimizations/o1/performance/results.py'),'--campaign',str(w/'campaign-01'),'--output',str(w/'results-01')]
d={'command':cmd,'cwd':str(r),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'new_emu_executed':False}
(o/'command.json').write_text(json.dumps(d,indent=2)+'\n')
with (o/'stdout.log').open('wb') as so,(o/'stderr.log').open('wb') as se:
 d['exit_code']=subprocess.run(cmd,cwd=r,stdout=so,stderr=se).returncode
d.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_sha256={n:hashlib.sha256((o/n).read_bytes()).hexdigest() for n in ['stdout.log','stderr.log']})
(o/'result.json').write_text(json.dumps(d,indent=2)+'\n')
print('POSTPROCESS_EXIT',d['exit_code']);print((o/'stdout.log').read_text()[-2000:]);print((o/'stderr.log').read_text()[-2500:])
raise SystemExit(d['exit_code'])
