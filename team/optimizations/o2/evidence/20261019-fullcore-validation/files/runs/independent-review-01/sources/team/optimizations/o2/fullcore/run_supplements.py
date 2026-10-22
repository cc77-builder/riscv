"""Run the two compiled O2 G3 supplements with pinned hardware and normal DiffTest.

Correctness/trace evidence only. This driver does not build or measure a fair A/B.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE))
import run_suite as suite

DEFAULT_BASE=Path("/home/riscv/riscv-lab/o2-fullcore-20261019")
JOBS={
    "o2-diagnostic": dict(kind="diagnostic",image="o2-diag.bin",commits=1158,
        image_sha256="ed35725a24708fc7ffb4efb617248fe5e6911f18c803280a6e75be3f8ad6dfc7",
        default=DEFAULT_BASE/"diagnostic-build-02"),
    "o2-control-diagnostic": dict(kind="control",image="o2-control.bin",commits=1208,
        image_sha256="45cdf2a6cb6848b3bcb56d860c36bc26a975a8aa96bfe1411d33dce6036bd305",
        default=DEFAULT_BASE/"control-diagnostic-build-04"),
}
EXPECTED_CHECK_STATUS={"diagnostic":"O2_DIAGNOSTIC_PASS","control":"O2_CONTROL_DIAGNOSTIC_PASS"}


def modules():
    analyze=suite.load_module("o2_supplement_analyze",HERE/"analyze.py")
    workload=suite.load_module("o2_supplement_workload",HERE/"workloads/check.py")
    return analyze,workload


def evaluate(text,exit_code,kind,manifest,reference,analyze,workload):
    """Pure post-run gate also used by offline rechecks; never runs hardware."""
    suite.require(kind in EXPECTED_CHECK_STATUS,"unknown supplement kind")
    suite.require(type(exit_code) is int and exit_code==0,"supplement EMU exit code is not zero")
    suite.validate_runtime(text,reference)
    suite.validate_failure_markers(text)
    observation=analyze.analyze(text,require_complete=True)
    suite.validate_observation(observation)
    _,uart=analyze.extract_events_and_uart(text)
    checker=workload.check if kind=="diagnostic" else workload.check_control
    result=checker(uart,manifest,exit_code,observation)
    suite.require(result.get("status")==EXPECTED_CHECK_STATUS[kind],"unexpected workload verdict")
    counts=observation.get("counts",{})
    expected=1158 if kind=="diagnostic" else 1208
    suite.require(type(manifest.get("expected_vdot_commits")) is int and
                  manifest["expected_vdot_commits"]==expected,"supplement manifest commit drift")
    suite.require(counts.get("COMMIT")==expected,"supplement complete retirement count mismatch")
    for name in suite.O2_REQUIRED_COVERAGE:
        value=counts.get(name,0)
        suite.require(type(value) is int and value>=0,"invalid observation coverage count")
    suite.require(observation.get("pending_count")==0 and observation.get("unfinished_rob_count")==0,
                  "supplement did not drain")
    return observation,uart,result


def validate_build(kind,build,workload):
    spec=JOBS["o2-diagnostic" if kind=="diagnostic" else "o2-control-diagnostic"]
    manifest=workload.verify_build(build)
    receipt=json.loads((build/"build.json").read_text())
    suite.require(receipt.get("kind")==kind,"wrong supplement build kind")
    suite.require(manifest.get("expected_vdot_commits")==spec["commits"],"supplement count changed")
    image=build/spec["image"]
    suite.require(suite.sha(image)==spec["image_sha256"],"supplement image is not frozen")
    return manifest,receipt,image


def verify_files(files):
    for name,digest in files.items():
        suite.require(suite.sha(name)==digest,"supplement artifact drift: "+name)


def run_job(name,build,image,manifest,paths,args,pins,receipt,analyze,workload):
    directory=args.output/name
    directory.mkdir()
    spec=JOBS[name]
    command=["timeout",args.timeout,"stdbuf","-o0","-e0",str(args.emu),"-i",str(image),
             "--flash="+str(paths["flash"]),"--ram-size=128MB","--diff="+str(paths["reference"]),
             "--max-cycles=5000000"]
    record=dict(name=name,kind=spec["kind"],status="RUNNING",started=suite.stamp(),
                command=command,expected_vdot_commits=spec["commits"],performance_measured=False,
                files={str(p):suite.sha(p) for p in [args.emu,paths["reference"],paths["flash"],image]},
                hardware_pins_sha256=receipt["hardware_pins_sha256"],
                build_source_commit=pins["source_commit"],input_manifest_sha256=suite.sha(build/"data/manifest.json"))
    suite.save(directory/"runtime.json",record)
    suite.save(directory/"input-manifest.json",manifest)
    record["archived_manifest_sha256"]=suite.sha(directory/"input-manifest.json")
    suite.save(directory/"runtime.json",record)
    suite.save(directory/"build-receipt.json",json.loads((build/"build.json").read_text()))
    def guard():
        suite.hardware_guard(pins,args.emu)
        suite.require(suite.sha(args.hardware_pins)==receipt["hardware_pins_sha256"],"hardware pins changed")
        verify_files(receipt["driver_files"])
        verify_files(receipt["input_files"])
        validate_build(spec["kind"],build,workload)
    try:
        guard()
        env=os.environ.copy()
        env.pop("XS_NEGATIVE_VECTOR_TARGET",None)
        rc,raw=suite.run_process(command,directory,env)
        record.update(exit_code=rc,raw_logs_sha256=raw,
                      log_format="separate-streams-v1; derived run.log = stderr.log + stdout.log")
        guard()
        text=(directory/"run.log").read_text(encoding="utf-8",errors="strict")
        observation,uart,result=evaluate(text,rc,spec["kind"],manifest,paths["reference"],analyze,workload)
        suite.save(directory/"observation.json",observation)
        suite.save(directory/"functional-result.json",result)
        (directory/"uart.log").write_text(uart,encoding="utf-8")
        record.update(status="O2_SUPPLEMENT_PASS",workload_status=result["status"],
                      observation_status=observation["status"],observation_counts=observation["counts"],
                      checked_register_bytes=result["checked_register_bytes"])
    except Exception as exc:
        record.update(status="FAILED",error=repr(exc))
    record["finished"]=suite.stamp()
    suite.save(directory/"result.json",record)
    print(name,record["status"],record.get("error",""),flush=True)
    return record


def assess(records):
    names=[r.get("name") for r in records]
    return (len(records)==2 and set(names)==set(JOBS) and
            all(r.get("status")=="O2_SUPPLEMENT_PASS" and
                r.get("observation_status")=="O2_TRACE_PASS" and
                r.get("exit_code")==0 and type(r.get("exit_code")) is int and
                r.get("observation_counts",{}).get("COMMIT")==JOBS[r["name"]]["commits"] and
                r.get("expected_vdot_commits")==JOBS[r["name"]]["commits"]
                for r in records))


def recheck_job(directory,analyze=None,workload=None):
    """Replay a sealed job using current identical checker sources, without EMU."""
    directory=Path(directory)
    record=json.loads((directory/"result.json").read_text())
    suite.require(record.get("name") in JOBS,"unknown stored supplement")
    spec=JOBS[record["name"]]
    suite.require(record.get("kind")==spec["kind"],"stored supplement kind changed")
    manifest=json.loads((directory/"input-manifest.json").read_text())
    suite.require(suite.sha(directory/"input-manifest.json")==record.get("archived_manifest_sha256"),
                  "stored manifest changed")
    runtime=json.loads((directory/"runtime.json").read_text())
    for name in ["name","kind","command","files","hardware_pins_sha256","build_source_commit",
                 "input_manifest_sha256","archived_manifest_sha256","expected_vdot_commits"]:
        suite.require(record.get(name)==runtime.get(name),"stored runtime identity changed: "+name)
    command=record["command"]
    suite.require(isinstance(command,list) and len(command)==12 and
                  command[0]=="timeout" and command[2:5]==["stdbuf","-o0","-e0"] and
                  command[6]=="-i" and command[9]=="--ram-size=128MB" and
                  command[11]=="--max-cycles=5000000","stored run command differs from contract")
    suite.require(record["files"].get(command[7])==spec["image_sha256"],"stored input image changed")
    for option,key in [(8,"flash"),(10,"reference")]:
        prefix="--flash=" if key=="flash" else "--diff="
        suite.require(command[option].startswith(prefix),"stored input command changed")
        suite.require(record["files"].get(command[option].split("=",1)[1])==suite.FROZEN[key],
                      "stored fixed input identity changed")
    build_receipt=json.loads((directory/"build-receipt.json").read_text())
    suite.require(build_receipt.get("kind")==spec["kind"] and
                  build_receipt.get("images_sha256",{}).get(spec["image"])==spec["image_sha256"],
                  "stored build receipt differs from frozen image")
    for name,digest in record.get("raw_logs_sha256",{}).items():
        suite.require(name in ["stdout.log","stderr.log","run.log"],"unknown raw stream")
        suite.require(suite.sha(directory/name)==digest,"stored raw stream changed")
    suite.require(set(record.get("raw_logs_sha256",{}))=={"stdout.log","stderr.log","run.log"},"missing raw stream identities")
    raw=(directory/"stderr.log").read_bytes()+(directory/"stdout.log").read_bytes()
    suite.require(raw==(directory/"run.log").read_bytes(),"derived transcript is not exact streams")
    exit_text=(directory/"exit-code.txt").read_text()
    suite.require(re.fullmatch(r"-?[0-9]+\n",exit_text) is not None,"stored exit code file malformed")
    rc=int(exit_text)
    suite.require(rc==record.get("exit_code") and type(record.get("exit_code")) is int,"stored exit code changed")
    references=[item.split("=",1)[1] for item in record["command"] if item.startswith("--diff=")]
    suite.require(len(references)==1,"stored reference command ambiguous")
    if analyze is None or workload is None:
        analyze,workload=modules()
    observation,_,result=evaluate(raw.decode("utf-8"),rc,spec["kind"],manifest,Path(references[0]),analyze,workload)
    suite.require(record.get("status")=="O2_SUPPLEMENT_PASS" and
                  record.get("observation_status")==observation["status"] and
                  record.get("observation_counts")==observation["counts"] and
                  record.get("workload_status")==result["status"],"stored verdict differs from replay")
    return dict(status="O2_SUPPLEMENT_OFFLINE_RECHECK_PASS",name=record["name"],new_emu_run=False,
                observation_counts=observation["counts"],observation_status=observation["status"],
                workload_status=result["status"],checked_register_bytes=result["checked_register_bytes"],
                raw_sha256=suite.sha(directory/"run.log"))


def recheck_supplements(campaign,expected_pins,expected_emu_sha,analyze=None,workload=None):
    """Recompute both qualified records from sealed raw streams; no external inputs."""
    campaign=Path(campaign)
    if isinstance(expected_pins,(str,Path)):
        expected_pins=json.loads(Path(expected_pins).read_text())
    suite.validate_pin_fields(expected_pins)
    pins=json.loads((campaign/"hardware-pins.json").read_text())
    suite.require(pins==expected_pins and pins["emu_sha256"]==expected_emu_sha,
                  "supplement hardware identity differs from primary campaign")
    preflight=json.loads((campaign/"preflight.json").read_text())
    state=json.loads((campaign/"campaign-state.json").read_text())
    expected_dirs={"tools","inputs"}|set(JOBS)
    suite.require({p.name for p in campaign.iterdir() if p.is_dir()}==expected_dirs,
                  "missing or extra supplement campaign directory")
    verify_files(preflight.get("input_files",{}))
    normal=suite.DEFAULT_T12/"nemu/reference/build/riscv64-nemu-interpreter-so"
    ref_guard=suite.load_module("o2_supplement_recheck_guard",ROOT/"team/scripts/artifact_guard.py")
    ref_guard.verify_nemu(suite.DEFAULT_T12/"nemu/reference",normal,"reference")
    suite.require(preflight.get("hardware_pins_sha256")==suite.sha(campaign/"hardware-pins.json") and
                  preflight.get("emu_sha256")==expected_emu_sha,"supplement campaign pins/hash changed")
    tool_commit=preflight.get("tool_source_commit","")
    suite.require(re.fullmatch(r"[0-9a-f]{40}",tool_commit) is not None,"missing tool source Git commit")
    portable=preflight.get("portable_input_files",{})
    suite.require(set(portable)==set(preflight.get("input_files",{})),"incomplete portable input snapshots")
    for name,item in portable.items():
        relative=Path(item["archive"])
        suite.require(not relative.is_absolute() and ".." not in relative.parts,"unsafe portable snapshot path")
        suite.require(item["sha256"]==preflight["input_files"][name] and
                      suite.sha(campaign/relative)==item["sha256"],"offline input artifact changed: "+name)
    expected_driver_paths={"team/optimizations/o2/fullcore/run_supplements.py",
        "team/optimizations/o2/fullcore/run_suite.py","team/optimizations/o2/fullcore/analyze.py",
        "team/optimizations/o2/fullcore/workloads/check.py","team/optimizations/o1/audit/runtime_gate.py",
        "team/scripts/artifact_guard.py"}
    driver_paths=set()
    for name,digest in preflight.get("driver_files",{}).items():
        original=Path(name)
        # The preserved suffix maps archived absolute source paths back to this checkout.
        parts=original.parts
        suite.require("team" in parts,"invalid checker path in receipt")
        relative=Path(*parts[parts.index("team"):])
        driver_paths.add(relative.as_posix())
        saved=campaign/"tools"/relative
        blob=subprocess.check_output(["git","show",tool_commit+":"+relative.as_posix()],cwd=ROOT)
        suite.require(suite.sha(saved)==digest and suite.sha(ROOT/relative)==digest and
                      hashlib.sha256(blob).hexdigest()==digest,
                      "offline checker bytes differ from original committed run tools: "+str(relative))
    suite.require(driver_paths==expected_driver_paths and len(preflight["driver_files"])==6,
                  "incomplete or unexpected offline checker identities")
    result=json.loads((campaign/"result.json").read_text())
    suite.require(result.get("status")=="O2_SUPPLEMENTS_PASS" and assess(result.get("runs",[])),
                  "stored supplement campaign did not pass")
    suite.require(state.get("status")==result["status"] and
                  all(state.get(k)==result.get(k) for k in ["started","finished","build_source_commit"]) and
                  result.get("hardware_pins_sha256")==preflight["hardware_pins_sha256"] and
                  result.get("emu_sha256")==expected_emu_sha and
                  result.get("build_source_commit")==pins["source_commit"] and
                  result.get("performance_measured") is False and result.get("new_emu_run") is True,
                  "incoherent supplement campaign receipts")
    if analyze is None or workload is None:
        analyze,workload=modules()
    records=[]
    for name in JOBS:
        directory=campaign/name
        replay=recheck_job(directory,analyze,workload)
        record=json.loads((directory/"result.json").read_text())
        suite.hardware_guard(pins,Path(record["command"][5]))
        original_build=Path(record["command"][7]).parent
        manifest,original_receipt,_=validate_build(JOBS[name]["kind"],original_build,workload)
        suite.require((original_build/"data/manifest.json").read_bytes()==(directory/"input-manifest.json").read_bytes() and
                      original_receipt==json.loads((directory/"build-receipt.json").read_text()),
                      "original and archived workload receipts disagree")
        build_manifest=[item for original,item in portable.items()
                        if original.endswith("/data/manifest.json") and
                        item["sha256"]==record.get("input_manifest_sha256")]
        suite.require(len(build_manifest)==1 and
                      suite.sha(directory/"input-manifest.json")==record["input_manifest_sha256"],
                      "archived job input manifest is not bound to original inputs")
        suite.require(record["hardware_pins_sha256"]==preflight["hardware_pins_sha256"] and
                      record["build_source_commit"]==pins["source_commit"] and
                      record["files"].get(record["command"][5])==expected_emu_sha,
                      "stored job used a different hardware identity")
        matches=[r for r in result["runs"] if r.get("name")==name]
        suite.require(matches==[record],"campaign and job receipts disagree")
        qualified=dict(record,status="O2_SUPPLEMENT_PASS",
                       observation_status=replay["observation_status"],
                       observation_counts=replay["observation_counts"],
                       workload_status=replay["workload_status"],
                       checked_register_bytes=replay["checked_register_bytes"])
        records.append(qualified)
    suite.require(suite.coverage_union(records)==result.get("coverage"),"stored coverage differs from replay")
    return dict(status="O2_SUPPLEMENT_OFFLINE_RECHECK_PASS",runs=records,records=records,
                coverage=suite.coverage_union(records),new_emu_run=False,
                emu_sha256=expected_emu_sha,hardware_pins_sha256=preflight["hardware_pins_sha256"])


def recheck_campaign(campaign,output,expected_pins,expected_emu_sha,analyze=None,workload=None):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    result=recheck_supplements(campaign,expected_pins,expected_emu_sha,analyze,workload)
    suite.save(output/"result.json",result)
    return result


def run(args):
    suite.require(args.output.is_absolute(),"output must be absolute")
    args.output=args.output.resolve()
    suite.require(not args.output.is_relative_to(ROOT),"output must be outside checkout")
    args.output.mkdir(parents=True,exist_ok=False)
    state=dict(status="PRECHECK_RUNNING",started=suite.stamp(),invocation=sys.argv,
               performance_measured=False,new_emu_run=True,emu=str(args.emu),jobs=args.jobs)
    suite.save(args.output/"campaign-state.json",state)
    records=[]
    try:
        analyze,workload=modules()
        for func in [workload.check,workload.check_control]:
            inspect.signature(func).bind("",{},0,{})
        pins=json.loads(args.hardware_pins.read_text())
        suite.hardware_guard(pins,args.emu)
        paths=dict(reference=suite.DEFAULT_T12/"nemu/reference/build/riscv64-nemu-interpreter-so",
                   flash=suite.DEFAULT_T12/"repo/team/workloads/hello-vadd/build/boot-flash.bin")
        for key,path in paths.items():
            suite.require(suite.sha(path)==suite.FROZEN[key],"frozen input changed: "+key)
        guard=suite.load_module("o2_supplement_artifact_guard",ROOT/"team/scripts/artifact_guard.py")
        reference_provenance=guard.verify_nemu(suite.DEFAULT_T12/"nemu/reference",paths["reference"],"reference")
        builds={"o2-diagnostic":args.diagnostic_build,"o2-control-diagnostic":args.control_build}
        manifests={}
        prepared={}
        inputs={str(p):suite.sha(p) for p in paths.values()}
        for name,build in builds.items():
            manifest,build_receipt,image=validate_build(JOBS[name]["kind"],build,workload)
            manifests[name]=manifest
            prepared[name]=(build,image,manifest)
            for group in ["source_sha256","generated_sha256","images_sha256","am_libraries_sha256"]:
                for path,digest in build_receipt[group].items():
                    actual=Path(path) if Path(path).is_absolute() else build/path
                    inputs[str(actual)]=digest
            inputs[str(build/"build.json")]=suite.sha(build/"build.json")
        drivers=[Path(__file__),HERE/"run_suite.py",HERE/"analyze.py",HERE/"workloads/check.py",
                 ROOT/"team/optimizations/o1/audit/runtime_gate.py",ROOT/"team/scripts/artifact_guard.py"]
        driver_files={str(p):suite.sha(p) for p in drivers}
        tool_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        for path,digest in driver_files.items():
            relative=Path(path).relative_to(ROOT).as_posix()
            blob=subprocess.check_output(["git","show",tool_commit+":"+relative],cwd=ROOT)
            suite.require(hashlib.sha256(blob).hexdigest()==digest,
                          "runtime checker must be committed before execution: "+relative)
        # Snapshot exact checker bytes with checkout-relative names for offline use.
        for path in drivers:
            target=args.output/"tools"/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
        compiler=shutil.which("riscv64-linux-gnu-gcc")
        suite.require(compiler is not None,"cross compiler unavailable for identity check")
        compiler=Path(compiler).resolve()
        toolchain=dict(path=str(compiler),sha256=suite.sha(compiler),
                       version=subprocess.check_output([str(compiler),"--version"],text=True))
        inputs[str(compiler)]=toolchain["sha256"]
        portable={}
        for index,(name,digest) in enumerate(sorted(inputs.items())):
            archive=Path("inputs")/(f"{index:04d}-"+Path(name).name)
            target=args.output/archive
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(name,target)
            suite.require(suite.sha(target)==digest,"portable input snapshot mismatch: "+name)
            portable[name]=dict(archive=archive.as_posix(),sha256=digest)
        receipt=dict(status="O2_SUPPLEMENT_INPUTS_VERIFIED",hardware_pins_sha256=suite.sha(args.hardware_pins),
                     emu_sha256=suite.sha(args.emu),input_files=inputs,driver_files=driver_files,
                     toolchain=toolchain,reference_provenance=reference_provenance,
                     portable_input_files=portable,tool_source_commit=tool_commit,
                     build_source_commit=pins["source_commit"])
        suite.save(args.output/"preflight.json",receipt)
        shutil.copyfile(args.hardware_pins,args.output/"hardware-pins.json")
        state.update(status="RUNNING",build_source_commit=pins["source_commit"])
        suite.save(args.output/"campaign-state.json",state)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures=[pool.submit(run_job,name,*prepared[name],paths,args,pins,receipt,analyze,workload)
                     for name in JOBS]
            for future in as_completed(futures):
                records.append(future.result())
                suite.save(args.output/"progress.json",records)
        suite.hardware_guard(pins,args.emu)
        verify_files(inputs)
        verify_files(driver_files)
        guard.verify_nemu(suite.DEFAULT_T12/"nemu/reference",paths["reference"],"reference")
        passed=assess(records)
        result=dict(status="O2_SUPPLEMENTS_PASS" if passed else "O2_SUPPLEMENTS_FAILED",
                    runs=records,coverage=suite.coverage_union(records),performance_measured=False,
                    started=state["started"],finished=suite.stamp(),new_emu_run=True,
                    hardware_pins_sha256=receipt["hardware_pins_sha256"],emu_sha256=receipt["emu_sha256"],
                    build_source_commit=pins["source_commit"],
                    scope="Two supplemental correctness jobs; does not independently certify all G3 gates")
        suite.save(args.output/"result.json",result)
        state.update(status=result["status"],finished=result["finished"])
        suite.save(args.output/"campaign-state.json",state)
        print(result["status"],flush=True)
        return 0 if passed else 1
    except Exception as exc:
        state.update(status="O2_SUPPLEMENTS_FAILED",error=repr(exc),finished=suite.stamp(),runs=records)
        suite.save(args.output/"campaign-state.json",state)
        suite.save(args.output/"result.json",state)
        print("O2_SUPPLEMENTS_FAILED",repr(exc),file=sys.stderr,flush=True)
        return 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--hardware-pins",type=Path,required=True)
    parser.add_argument("--emu",type=Path,required=True)
    parser.add_argument("--diagnostic-build",type=Path,default=JOBS["o2-diagnostic"]["default"])
    parser.add_argument("--control-build",type=Path,default=JOBS["o2-control-diagnostic"]["default"])
    parser.add_argument("--jobs",type=int,choices=[1,2],default=2)
    parser.add_argument("--timeout",default="120m")
    args=parser.parse_args()
    suite.require(re.fullmatch(r"[1-9][0-9]*(?:s|m|h)",args.timeout) is not None,"invalid timeout")
    for name in ["emu","hardware_pins","diagnostic_build","control_build"]:
        setattr(args,name,getattr(args,name).resolve())
    return run(args)

if __name__=="__main__":
    raise SystemExit(main())
