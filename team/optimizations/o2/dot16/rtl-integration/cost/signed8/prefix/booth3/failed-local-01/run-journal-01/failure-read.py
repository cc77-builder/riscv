import os,json,hashlib
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
r=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/local-01")
p=r/'result.json';b=p.read_bytes();d=json.loads(b)
out={k:v for k,v in d.items() if k not in ('generated','commands','arithmetic_structure_proof','wrapper_bindings','fu_results','cost_results')}
out['result_identity']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
out['commands']=[{k:v for k,v in c.items() if k not in ('argv','input_pins','environment')} for c in d['commands']]
a=d.get('arithmetic_structure_proof',{});out['P_proof']={k:a.get(k) for k in ('status','rtl_sha256','all_inputs_equivalent','full_adders','half_adders','layers')}
out['miter_logs']={x.name:{'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'tail':x.read_text()[-12000:]} for x in sorted(r.glob('actual-prefix-*-miter.log'))}
assert p.read_bytes()==b
print(json.dumps(out,indent=2))
