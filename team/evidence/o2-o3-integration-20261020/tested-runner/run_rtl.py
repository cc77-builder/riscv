#!/usr/bin/env python3
"""Run O2 G1 or G2, retaining commands, failures, source and generated manifests."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("fu", "parent"):
        raise SystemExit("usage: run_rtl.py fu|parent /absolute/new/output")
    stage, out = sys.argv[1], Path(sys.argv[2])
    if not out.is_absolute() or out.exists() or out.resolve().is_relative_to(ROOT):
        raise SystemExit("output must be new, absolute, and outside checkout")
    out = out.resolve()
    out.mkdir(parents=True)
    os.chdir(ROOT)
    # Activate first, before resolving any executable; do not persist environment secrets.
    activated = subprocess.check_output(["bash", "-c", "source team/scripts/activate.sh >/dev/null; env -0"])
    env = dict(item.decode().split("=", 1) for item in activated.split(b"\0") if item)
    env.update(VDOT_O2_TRACE="0", VDOT_O2_ELASTIC="1", VDOT_T14_FUSED_INPUT="1", VDOT_O1_HANDOFF="0",
               VDOT_T12_TRACE="0", VDOT_T13_TRACE="0", VDOT_O1_TRACE="0",
               JAVA_OPTS="-Xmx12G -Xss16m", BUILD_JOBS="2")
    env.setdefault("CHISEL_FIRTOOL_PATH", str(Path.home()/".cache/llvm-firtool/1.62.1/bin"))
    selected = {k: env[k] for k in ("VDOT_O2_TRACE", "VDOT_O2_ELASTIC", "VDOT_T14_FUSED_INPUT", "VDOT_O1_HANDOFF",
        "VDOT_T12_TRACE", "VDOT_T13_TRACE", "VDOT_O1_TRACE", "JAVA_OPTS", "BUILD_JOBS", "CHISEL_FIRTOOL_PATH", "PATH", "JAVA_HOME")}
    (out/"run.env.json").write_text(json.dumps(selected, indent=2)+"\n")
    records = []
    def run(log, args, expected=0):
        start = stamp()
        with (out/log).open("wb") as stream:
            proc = subprocess.run(list(map(str,args)), env=env, stdout=stream, stderr=subprocess.STDOUT)
        records.append(dict(command=list(map(str,args)), start=start, end=stamp(), exit_code=proc.returncode, log=log))
        (out/"commands.json").write_text(json.dumps(records, indent=2)+"\n")
        print(f"COMMAND exit={proc.returncode} log={log} "+shlex.join(list(map(str,args))), flush=True)
        if expected is not None and proc.returncode != expected:
            print((out/log).read_text(errors="replace")[-6000:], flush=True)
            raise RuntimeError(f"{log} failed, exit {proc.returncode}")
        return proc.returncode
    def modules(repo, prefix=""):
        result=[]
        tree=subprocess.check_output(["git","-C",str(repo),"ls-tree","-rz","HEAD"]).split(b"\0")
        for entry in filter(None,tree):
            meta,name=entry.split(b"\t",1)
            mode,_,pin=meta.decode().split()
            if mode!="160000": continue
            name=name.decode(); sub=repo/name
            head=subprocess.check_output(["git","-C",str(sub),"rev-parse","HEAD"],text=True).strip()
            status=subprocess.check_output(["git","-C",str(sub),"status","--porcelain=v1","--untracked-files=normal"],text=True)
            if head!=pin or status: raise RuntimeError(f"dirty/unpinned dependency {prefix+name}")
            result.append(dict(path=prefix+name,pin=pin,head=head,status=status))
            result.extend(modules(sub,prefix+name+"/"))
        return result
    status={"started_utc":stamp(),"stage":stage,"passed":False}
    try:
        for name,args in {
            "git":["git","--version"],"java":["java","-version"],"mill":["mill","--version"],
            "verilator":["verilator","--version"],"cxx":["g++","--version"],"clang":["clang++","--version"],
            "make":["make","--version"],"firtool":[str(Path(env["CHISEL_FIRTOOL_PATH"])/"firtool"),"--version"]
        }.items(): run(name+"-version.log",args)
        run("source-commit.log",["git","rev-parse","HEAD"])
        run("source-status.log",["git","status","--short"])
        run("working-tree.patch",["git","diff","--binary","HEAD"])
        names=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard","--",
            "build.sc","src","team/scripts/activate.sh","team/rtl/vdot","team/models/vdot",
            *["team/optimizations/o2/"+stage+"/"+name for name in
                (("GenerateVDotElasticFu.scala","fu_test.cpp") if stage=="fu" else
                 ("GenerateVDotElasticParent.scala","parent_test.cpp","check_negative.py","test_negative.py"))],
            "team/optimizations/o2/run_rtl.py",
            "team/optimizations/o2/check_negative_fu.py","team/optimizations/o2/test_negative_fu.py"]).split(b"\0")
        source={s.decode():digest(ROOT/s.decode()) for s in names if s and (ROOT/s.decode()).is_file()}
        (out/"source.json").write_text(json.dumps(source,indent=2)+"\n")
        (out/"source.sha256").write_text("".join(f"{h}  {n}\n" for n,h in source.items()))
        deps=modules(ROOT)
        (out/"dependencies.json").write_text(json.dumps(deps,indent=2)+"\n")
        run("vectors.log",["python3","-B","team/rtl/vdot/prepare_vectors.py","team/models/vdot/data",out/"vectors.tsv"])
        if stage=="fu":
            run("negative-gate-tests.log",["python3","-B","-m","unittest","discover","-s","team/optimizations/o2","-p","test_negative_fu.py","-v"])
        else:
            run("negative-gate-tests.log",["python3","-B","-m","unittest","discover","-s","team/optimizations/o2/parent","-p","test_negative.py","-v"])
        suffix="Fu" if stage=="fu" else "Parent"
        top="VDotElastic"+suffix+"TestTop"
        target="vdotElastic"+suffix
        run("elaboration.log",["mill","-i","-j","2",target+".runMain","team.vdot.GenerateVDotElastic"+suffix,out/"rtl"])
        rtl=out/"rtl"
        sources=sorted({p.resolve() for pattern in ("*.sv","*.v") for p in rtl.rglob(pattern)})
        if rtl/(top+".sv") not in sources: raise RuntimeError("missing top")
        for p in sources:
            if not p.is_relative_to(rtl) or b'// ----- 8< ----- FILE "' in p.read_bytes():
                raise RuntimeError("external or virtual HDL source")
        generated=list(sources)
        if stage=="parent":
            manifest=rtl/"firrtl_black_box_resource_files.f"
            tokens=shlex.split(manifest.read_text(),comments=True)
            resources=[(Path(t) if Path(t).is_absolute() else rtl/t).resolve() for t in tokens]
            if not any(p.name=="ClockGate.sv" for p in resources) or not set(resources).issubset(sources):
                raise RuntimeError("missing real generated ClockGate blackbox")
            generated.append(manifest)
        (out/"generated-files.json").write_text(json.dumps([
            dict(path=p.relative_to(out).as_posix(),sha256=digest(p),bytes=p.stat().st_size) for p in generated],indent=2)+"\n")
        lint_args = []
        if stage == "parent":
            # Reuse the exact production-divider waiver from the O1 parent.
            # Tool versions may place its unchanged expression at line 37/46.
            divider = rtl / "IterBlockI8Nr4.sv"
            lines = divider.read_text().splitlines()
            expression = "_GEN[{1'h0, io_pre_w[8]} + 2'h1] + {io_pre_w[7:0], io_pre_w_low[7]};"
            positions = [i + 1 for i, line in enumerate(lines) if line.strip() == expression]
            if len(positions) != 1 or positions[0] not in (37, 46):
                raise RuntimeError("reviewed divider width waiver no longer matches")
            waiver = out / "divider-width.vlt"
            waiver.write_text('`verilator_config\nlint_off -rule WIDTHEXPAND -file "*/IterBlockI8Nr4.sv" -lines '
                              + str(positions[0]) + '\n')
            lint_args = [waiver]
        run("lint.log", ["verilator", "--lint-only", "--assert", "--top-module", top, *lint_args, *sources])
        run("verilator.log",["verilator","--cc","--exe","--build","--assert","--top-module",top,
            "--Mdir",out/"obj","-j","2","-CFLAGS","-std=c++17 -O2",*lint_args,*sources,
            ROOT/"team/optimizations/o2"/stage/(stage+"_test.cpp")])
        binary=out/"obj"/("V"+top)
        run("result.log",[binary,out/"vectors.tsv"])
        text=(out/"result.log").read_text()
        prefix="O2_"+stage.upper()
        passes=[line for line in text.splitlines() if line.startswith(prefix+"_PASS")]
        if len(passes)!=1 or any(x in text for x in (prefix+"_FAIL",prefix+"_INJECT",prefix+"_FAULT_ESCAPED")):
            raise RuntimeError("positive completion gate")
        print(passes[0],flush=True)
        if stage=="parent":
            run("positive-replay.log",["python3","-B","team/optimizations/o2/parent/check_negative.py",
                "--positive","--return-code","0","--log",out/"result.log"])
        faults=("identity","wen","high","cancel") if stage=="fu" else ("identity","rob","high","metadata","wen","stall","route","double","clock","occupancy","kill_p","kill_r","survivor","duplicate","missing","reset")
        checker=ROOT/"team/optimizations/o2"/("check_negative_fu.py" if stage=="fu" else "parent/check_negative.py")
        for fault in faults:
            log="inject-"+fault+".log"
            rc=run(log,[binary,out/"vectors.tsv",fault],expected=None)
            run("check-"+fault+".log",["python3","-B",checker,"--fault",fault,"--return-code",str(rc),"--log",out/log])
        if source!={n:digest(ROOT/n) for n in source}: raise RuntimeError("source changed during test")
        if deps!=modules(ROOT): raise RuntimeError("dependencies changed during test")
        (out/"source-after.status").write_text("SOURCE_AND_DEPENDENCIES_UNCHANGED\n")
        artifacts=[out/"vectors.tsv",binary]
        (out/"artifacts.json").write_text(json.dumps([
            dict(path=p.relative_to(out).as_posix(),sha256=digest(p),bytes=p.stat().st_size) for p in artifacts],indent=2)+"\n")
        status["passed"]=True
        print(prefix+"_RUNNER_PASS isolated_not_fullcore",flush=True)
    finally:
        status["finished_utc"]=stamp()
        (out/"runner.status.json").write_text(json.dumps(status,indent=2)+"\n")
if __name__=="__main__": main()
