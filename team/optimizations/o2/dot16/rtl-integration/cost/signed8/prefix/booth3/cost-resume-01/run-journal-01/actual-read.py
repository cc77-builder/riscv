import os,json,hashlib
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/cost-resume-01")
def rec(p):
 b=p.read_bytes();return dict(path=str(p.relative_to(root)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
r=json.loads((root/'result.json').read_bytes())
r['result_file']=rec(root/'result.json')
r['top_files']=[rec(p) for p in sorted(root.iterdir()) if p.is_file()]
r['graph_audits']=[dict(file=rec(p),audit=json.loads(p.read_bytes())) for p in sorted(root.glob('feature*/serialized/graph-audit.json'))]
r['sta_logs']=[dict(file=rec(p),text=p.read_text(errors='replace')) for p in sorted(root.glob('sta-*.log'))]
print(json.dumps(r))
