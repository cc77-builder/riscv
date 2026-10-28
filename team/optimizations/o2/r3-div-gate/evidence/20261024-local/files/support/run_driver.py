import datetime,json,subprocess,sys,hashlib
from pathlib import Path
stage,output=sys.argv[1:3]
repo=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
out=Path(output)
receipt=out.parent/(out.name+".driver.json")
def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
cmd=[sys.executable,"-B",str(repo/"team/optimizations/o2/run_rtl.py"),stage,str(out)]
r={"command":cmd,"cwd":str(repo),"started":stamp(),"status":"running","scope":"R3 O2 DIV gate local RTL verification, no whole-core"}
receipt.write_text(json.dumps(r,indent=2)+"\n")
try:
 p=subprocess.run(cmd,cwd=repo)
 r["exit_code"]=p.returncode
 r["status"]="completed" if p.returncode==0 else "failed"
finally:
 r["finished"]=stamp()
 receipt.write_text(json.dumps(r,indent=2)+"\n")
