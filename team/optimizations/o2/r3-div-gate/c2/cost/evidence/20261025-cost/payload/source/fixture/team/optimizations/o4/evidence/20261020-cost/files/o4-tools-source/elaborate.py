#!/usr/bin/env python3
"""Generate separate O1/O2 full production interfaces. Never overwrite an attempt."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(); p.add_argument("mode",choices=["o1","o2"]); p.add_argument("boundary",choices=["fu","parent"]); p.add_argument("output",type=Path); a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    flags={"VDOT_T14_FUSED_INPUT":"1","VDOT_O1_HANDOFF":"1" if a.mode=="o1" else "0","VDOT_O2_ELASTIC":"1" if a.mode=="o2" else "0",**{k:"0" for k in ["VDOT_T12_TRACE","VDOT_T13_TRACE","VDOT_O1_TRACE","VDOT_O2_TRACE"]}}
    # Source activation uses the established project JDK/Mill without changing global configuration.
    cmd=["bash","-lc",'source team/scripts/activate.sh && export CHISEL_FIRTOOL_PATH=/home/riscv/.cache/llvm-firtool/1.62.1/bin && exec mill -i -j 2 vdotCost.runMain team.vdot.GenerateVDotCost '+a.boundary+' '+str(a.output.resolve()/"rtl")]
    meta={"command":cmd,"flags":flags,"source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"boundary":a.boundary,"mode":a.mode,"start":time.time()}
    (a.output/"command.json").write_text(json.dumps(meta,indent=2)+"\n")
    with (a.output/"generate.log").open("w") as log:
        result=subprocess.run(cmd,cwd=ROOT,env={**os.environ,**flags},stdout=log,stderr=subprocess.STDOUT)
    meta.update(exit_code=result.returncode,end=time.time())
    meta["rtl"]={str(f.relative_to(a.output)):{"sha256":sha(f),"bytes":f.stat().st_size} for f in sorted((a.output/"rtl").glob("*")) if f.is_file()}
    (a.output/"result.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps({"output":str(a.output),"exit_code":result.returncode,"rtl_files":len(meta["rtl"])}))
    raise SystemExit(result.returncode)
if __name__=="__main__": main()
