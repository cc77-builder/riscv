from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,sys
HERE=Path(__file__).resolve().parent
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def now():return datetime.now(timezone.utc).isoformat()
stages=["summarize","integrate","final_qa"]
for stage in stages:
 p=HERE/(stage+".command.json");assert not p.exists(),p
 cmd=[sys.executable,"-B",str(HERE/(stage+".py"))]
 r=dict(command=cmd,cwd=str(HERE),started=now(),exit_code=None)
 save(p,r)
 with (HERE/(stage+".command.stdout.log")).open("wb") as out,(HERE/(stage+".command.stderr.log")).open("wb") as err:
  proc=subprocess.Popen(cmd,cwd=HERE,stdout=out,stderr=err);r["pid"]=proc.pid;save(p,r)
  r["exit_code"]=proc.wait()
 r["finished"]=now();save(p,r)
 print(stage,r["exit_code"],flush=True)
 if r["exit_code"]:raise SystemExit(r["exit_code"])
print("C8_POSTPROCESS_COMPLETE",flush=True)
