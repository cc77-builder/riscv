"""Run the isolated T15 model/Chisel/Verilator acceptance, preserving all commands."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASE="6fea2969d05dc4cb168795a60e2e6ee9ca1f9988"


def dump(path,value):
    path.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()


def check(output):
    output=output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    env["JAVA_HOME"]=env.get("JAVA_HOME","/opt/graalvm-jdk-21")
    env["PATH"]=env["JAVA_HOME"]+"/bin:/usr/local/llvm/bin:"+env["PATH"]
    env["CHISEL_FIRTOOL_PATH"]=env.get("CHISEL_FIRTOOL_PATH",str(Path.home()/".cache/llvm-firtool/1.62.1/bin"))
    env["JAVA_OPTS"]="-Xmx4G -Xss16m"
    commands=[]
    def run(label,command,expected=0,log=None):
        log=log or output/(label+".log")
        record=dict(label=label,command=[str(v) for v in command],expected_exit=expected,
                    started=datetime.datetime.now().astimezone().isoformat())
        with log.open("w",encoding="utf-8") as stream:
            process=subprocess.run(record["command"],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
        record.update(exit_code=process.returncode,finished=datetime.datetime.now().astimezone().isoformat())
        commands.append(record)
        dump(output/"commands.json",commands)
        print(label,"exit",process.returncode,flush=True)
        if process.returncode!=expected:
            raise RuntimeError(label+" unexpected exit: "+log.read_text(encoding="utf-8")[-8000:])
        return log
    if git("status","--porcelain"):
        raise ValueError("commit source before a formal T15 run")
    old_build=subprocess.check_output(["git","show",BASE+":build.sc"],cwd=ROOT)
    current_build=(ROOT/"build.sc").read_bytes()
    marker=b"\n// T15 independent parameter experiment; does not change production FU sources.\n"
    if current_build.split(marker)[0]!=old_build or current_build.count(marker)!=1:
        raise ValueError("build.sc is not an isolated-target-only addition")
    git("diff","--exit-code",BASE,"--","src","team/models/vdot","team/patches/nemu","team/workloads","team/rtl/vdot/fu_test.cpp")
    source_files=["build.sc","src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala",
                  "team/scripts/check-vdot-param.py","team/scripts/verify-t15.py","team/tests/test_t15_evidence.py"]
    for directory in ("team/rtl/vdot/param","team/models/vdot-param"):
        source_files += [str(p.relative_to(ROOT)) for p in (ROOT/directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    for name in ("directed.jsonl","random.jsonl"):
        source_files.append("team/models/vdot/data/"+name)
    pins=dict(source_commit=git("rev-parse","HEAD"),base_commit=BASE,
              production_src_tree=git("rev-parse","HEAD:src"),base_production_src_tree=git("rev-parse",BASE+":src"),
              build_target_addition_only=True,files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(source_files)},
              environment={key:env[key] for key in ("JAVA_HOME","JAVA_OPTS","CHISEL_FIRTOOL_PATH")})
    dump(output/"source.json",pins)
    for label,cmd in [("java",["java","-version"]),("mill",["mill","--version"]),
                      ("firtool",[str(Path(env["CHISEL_FIRTOOL_PATH"])/"firtool"),"--version"]),
                      ("verilator",["verilator","--version"]),("compiler",["g++","--version"]),("python",["python3","--version"])]:
        run("version-"+label,cmd)
    run("model-tests",["python3","-B","-m","unittest","discover","-s","team/models/vdot-param/tests","-v"])
    run("evidence-tests",["python3","-B","-m","unittest","discover","-s","team/tests","-p","test_t15_evidence.py","-v"])
    run("original-model",["bash","team/scripts/check-vdot-model.sh"])
    run("corpus",["python3","-B","team/models/vdot-param/generate.py","--check"])
    profiles={}
    metadata=json.loads((ROOT/"team/models/vdot-param/data/manifest.json").read_text())
    for name in ("s8x8","s16x8"):
        directory=output/name
        directory.mkdir()
        config=metadata["profiles"][name]
        run(name+"-elaboration",["mill","-i","-j","2","vdotParam.runMain","team.vdot.param.GenerateVDotParam",directory/"rtl",name])
        sv=directory/"rtl/VDotParamTestTop.sv"
        flags=f"-std=c++17 -O2 -DT15_BASELINE={int(name=='s8x8')} -DT15_COUNT={config['total']} -DT15_DIRECTED={config['directed']}"
        run(name+"-build",["verilator","--cc","--exe","--build","--assert","--top-module","VDotParamTestTop",
                           "--Mdir",directory/"obj_dir","-j","2","-CFLAGS",flags,sv,ROOT/"team/rtl/vdot/param/param_test.cpp"])
        executable=directory/"obj_dir/VVDotParamTestTop"
        vectors=ROOT/"team/models/vdot-param/data"/(name+".tsv")
        log=run(name+"-normal",[executable,vectors,directory/"actual"],log=directory/"result.log")
        result=json.loads(log.read_text())
        if result["status"]!="T15_RTL_PASS" or result["profile"]!=name or result["vectors"]!=config["total"]:
            raise ValueError("invalid run result")
        result["executable_sha256"]=hashlib.sha256(executable.read_bytes()).hexdigest()
        profiles[name]=result
        for fault in ("bit0","bit33","bit63","bit127","tag"):
            log=run(name+"-inject-"+fault,[executable,vectors,directory/("inject-"+fault),"--inject="+fault],expected=1,log=directory/("inject-"+fault+".log"))
            content=log.read_text()
            if "T15_READBACK_INJECTION fault="+fault not in content or "T15_RTL_FAIL" not in content:
                raise ValueError("injection did not reach comparison")
        bad=directory/"truncated.tsv"
        bad.write_bytes(vectors.read_bytes().splitlines(keepends=True)[0])
        log=run(name+"-truncated-input",[executable,bad,directory/"truncated"],expected=2)
        if "T15_INPUT_ERROR corpus count mismatch" not in log.read_text():
            raise ValueError("truncation was not diagnosed")
    for guard in ("result32","result34","result129","pairs0","pairs3","input-overflow","element","container"):
        label="guard-"+guard
        log=run(label,["mill","-i","-j","2","vdotParam.runMain","team.vdot.param.GenerateVDotParam",output/label,"invalid-"+guard],expected=1)
        if "T15_PARAMETER:" not in log.read_text():
            raise ValueError("unrelated failure does not prove parameter rejection")
    result=dict(status="T15_UNIT_CAMPAIGN_PASS",profiles=profiles,parameter_guard_rejections=8,
                scope="s8x8 and s16x8 standalone units; no ISA/NEMU/CPU or physical timing claims")
    dump(output/"result.json",result)
    # Raw hashes remain valid if traces/logs are later losslessly gzip-compressed.
    dump(output/"file-manifest.json",{"files":{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                                             for p in sorted(output.rglob("*")) if p.is_file() and "obj_dir" not in p.parts}})
    print(json.dumps(result),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    check(parser.parse_args().output)
