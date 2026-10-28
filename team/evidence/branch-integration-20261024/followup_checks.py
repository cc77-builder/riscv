from pathlib import Path
import subprocess,json,os
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
o=Path(__file__).parent
env=os.environ.copy()
env["PATH"]=str(o/"lld-tool/extracted/usr/lib/llvm-19/bin")+":/usr/local/llvm/bin:"+env["PATH"]
jobs=[
("safe-tail-host-retry",["python3","-B","-m","unittest","discover","-s","team/optimizations/o2/r2-safe-tail","-p","test_*.py","-v"],r),
("selection-host-only",["python3","-B","-m","unittest","discover","-s","team/optimizations/o2/r2-select","-p","test_selection.py","-v"],r),
("entry-portable-host",["python3","-B","-m","unittest","-v","test_entry.CallPath","test_entry_c_api.Recovery"],r/"team/optimizations/o2/r2-select"),
("t12-host",["python3","-B","-m","unittest","discover","-s","team/tests","-p","test_t12*.py","-v"],r),
("t12-judge-build",["gcc","-std=c11","-O2","-Wall","-Wextra","-Iteam/workloads/vdot-exceptions","team/tests/test_t12_judge.c","team/workloads/vdot-exceptions/judge.c","-o",str(o/"test_t12_judge")],r),
("t12-judge-run",[str(o/"test_t12_judge")],r)]
res=[]
for name,cmd,cwd in jobs:
 print("START",name,flush=True)
 with (o/(name+".stdout")).open("w") as out,(o/(name+".stderr")).open("w") as err:
  p=subprocess.run(cmd,cwd=cwd,stdout=out,stderr=err,env=env)
 res.append(dict(name=name,command=cmd,cwd=str(cwd),returncode=p.returncode))
 (o/"checks-followup.json").write_text(json.dumps(res,indent=2)+"\n")
 print("DONE",name,"rc",p.returncode,flush=True)
 if p.returncode: print((o/(name+".stderr")).read_text()[-1500:],flush=True)
