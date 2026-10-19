
from pathlib import Path
import subprocess,json,datetime,hashlib
w=Path('/home/riscv/riscv-lab/o1-performance-20261018')
r=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
o=w/'launch-01';o.mkdir()
command=['python3','-B',str(r/'team/optimizations/o1/performance/compare.py'),'--output',str(w/'campaign-01')]
d={'command':command,'cwd':str(r),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()}
(o/'command.json').write_text(json.dumps(d,indent=2)+'\n')
state=json.loads((w/'WORK_STATE.json').read_text());state.update(status='PAIRED_CAMPAIGN_RUNNING',matched_t14_emu_sha256='081247df2c8220a37ee77be47a2c032bd0da0dba3544cd5e7bf0f63aaad45142',launch=str(o),source_commit=d['source_commit'])
(w/'WORK_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
with (o/'stdout.log').open('wb') as so,(o/'stderr.log').open('wb') as se:
 d['exit_code']=subprocess.run(command,cwd=r,stdout=so,stderr=se).returncode
d.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_sha256={n:hashlib.sha256((o/n).read_bytes()).hexdigest() for n in ['stdout.log','stderr.log']})
(o/'result.json').write_text(json.dumps(d,indent=2)+'\n')
print('PAIRED_CAMPAIGN_EXIT',d['exit_code'])
print((o/'stdout.log').read_text()[-2500:]);print((o/'stderr.log').read_text()[-2500:])
raise SystemExit(d['exit_code'])
