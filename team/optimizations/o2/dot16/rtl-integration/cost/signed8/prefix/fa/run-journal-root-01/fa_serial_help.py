import os,json,hashlib,subprocess
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/local-01')
dst=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-fa-20261108-main/serialization-help-01')
assert not dst.exists()
tool=Path('/usr/bin/yosys');tb=tool.read_bytes();assert hashlib.sha256(tb).hexdigest()=='dab84e88b53146fe22d675a142de32b1e545ee9b7fe1054238f6220245b24c8d'
v=src/'mapped.v';b=v.read_bytes();lines=b.decode().splitlines(keepends=True)
tail=''.join(str(i+1)+': '+lines[i] for i in range(43658,min(len(lines),43690))).encode()
p=subprocess.run(['/usr/bin/yosys','-Q','-T','-p','help write_verilog'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
assert p.returncode==0
dst.mkdir(parents=True)
files={'mapped-lines.txt':tail,'write-verilog-help.log':p.stdout,'write-verilog-help.stderr':p.stderr}
for n,d in files.items():(dst/n).write_bytes(d)
assert v.read_bytes()==b and tool.read_bytes()==tb
audit=dict(status='CLOSED_NETLIST_SERIALIZATION_DIAGNOSIS',mapped=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()),tool_sha256=hashlib.sha256(tb).hexdigest(),help_exit=0,new_design_runs=0,files=[dict(name=n,bytes=len(d),sha256=hashlib.sha256(d).hexdigest()) for n,d in files.items()])
(dst/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
