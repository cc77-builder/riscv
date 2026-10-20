#!/usr/bin/env python3
"""Generate separate O1/O2 full production interfaces. Never overwrite an attempt."""
import argparse, hashlib, json, os, shlex, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT/"team/optimizations/o1"))
import build_inputs
import build_recipe
sys.path.append(str(ROOT/"team/optimizations/o2/fullcore"))
import live_inputs
SOURCE_PATHS=[*build_inputs.HARDWARE,"team/optimizations/o4/GenerateVDotCost.scala",
              "team/optimizations/o4/elaborate.py","team/optimizations/o1/build_recipe.py",
              "team/optimizations/o2/fullcore/live_inputs.py"]


def capture_sources(root):
    """Bind committed complete compiler inputs before any new generation."""
    root=Path(root)
    git=lambda *args:subprocess.check_output(["git","-C",str(root),*args])
    if git("diff","HEAD","--",*SOURCE_PATHS) or git("ls-files","--others","--exclude-standard","--",*SOURCE_PATHS):
        raise ValueError("commit O4 compiler/tooling changes before generation")
    dependencies,dependency_files=live_inputs.dependency_snapshot(root)
    files=build_inputs.hardware_files(root)
    for name in SOURCE_PATHS:
        path=root/name
        if path.is_file():files[name]=sha(path)
    return dict(source_commit=git("rev-parse","HEAD").decode().strip(),files=files,
                dependencies=dependencies,dependency_files=dependency_files)


def verify_sources(root, expected):
    if capture_sources(root)!=expected:raise ValueError("O4 compiler inputs changed during generation")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(); p.add_argument("mode",choices=["o1","o2"]); p.add_argument("boundary",choices=["fu","parent"]); p.add_argument("output",type=Path); a=p.parse_args()
    source_inputs=capture_sources(ROOT)
    native_contract=build_recipe.capture(ROOT)
    a.output.mkdir(parents=True,exist_ok=False)
    flags={"VDOT_T14_FUSED_INPUT":"1","VDOT_O1_HANDOFF":"1" if a.mode=="o1" else "0","VDOT_O2_ELASTIC":"1" if a.mode=="o2" else "0",**{k:"0" for k in ["VDOT_T12_TRACE","VDOT_T13_TRACE","VDOT_O1_TRACE","VDOT_O2_TRACE"]}}
    # Source activation uses the established project JDK/Mill without changing global configuration.
    cmd=["bash","-c",'source team/scripts/activate.sh && export CHISEL_FIRTOOL_PATH='+shlex.quote(str(Path(native_contract["compilers"]["firtool"]["path"]).parent))+' && exec mill -i -j 2 vdotCost.runMain team.vdot.GenerateVDotCost '+shlex.quote(a.boundary)+' '+shlex.quote(str(a.output.resolve()/"rtl"))]
    meta={"command":cmd,"flags":flags,"source_commit":source_inputs["source_commit"],"source_inputs":source_inputs,"native_build_contract":native_contract,"boundary":a.boundary,"mode":a.mode,"start":time.time()}
    environment={**build_recipe.environment(),**flags}
    meta["environment_sha256"]=hashlib.sha256(json.dumps(environment,sort_keys=True).encode()).hexdigest()
    (a.output/"command.json").write_text(json.dumps(meta,indent=2)+"\n")
    with (a.output/"generate.log").open("w") as log:
        result=subprocess.run(cmd,cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT)
    meta.update(tool_exit_code=result.returncode,exit_code=result.returncode,end=time.time())
    try:
        verify_sources(ROOT,source_inputs)
        build_recipe.verify(ROOT,native_contract)
        meta["source_inputs_unchanged"]=True
    except Exception as exc:
        meta.update(source_inputs_unchanged=False,verification_error=str(exc),exit_code=result.returncode or 1)
    meta["rtl"]={str(f.relative_to(a.output)):{"sha256":sha(f),"bytes":f.stat().st_size} for f in sorted((a.output/"rtl").glob("*")) if f.is_file()}
    (a.output/"result.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps({"output":str(a.output),"exit_code":meta["exit_code"],"tool_exit_code":result.returncode,"rtl_files":len(meta["rtl"])}))
    raise SystemExit(meta["exit_code"])
if __name__=="__main__": main()
