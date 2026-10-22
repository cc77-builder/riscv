"""Paired O3 full-core application campaign: immutable images, live DiffTest."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from threading import Lock

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g4=load("o3_g4_identity_helpers",ROOT/"team/optimizations/o2/performance/compare.py")
check=load("o3_app_counter_check",HERE/"check.py")
def now():return datetime.now(timezone.utc).isoformat()
def save(path,value):
    path=Path(path);temp=path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");temp.replace(path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def verify_hashes(files):
    for name,digest in files.items():require(sha(name)==digest,"artifact drift "+name)

def summarize(records):
    measured=[s for r in records if r["suite"]=="performance" and r["replay"]==0 for s in r["samples"] if s["phase"]=="measured"]
    require(len(measured)==768,"O3 measured cardinality")
    output=[]
    for shard in range(8):
        for software in ("basic","reuse"):
            groups={}
            for mode in ("o1","o2"):
                methods={}
                for method in ("vdot","rvv"):
                    ss=[s for s in measured if s["shard"]==shard and s["software"]==software and s["mode"]==mode and s["method"]==method]
                    keys={(s["dataset"],s["repeat"]):s for s in ss}
                    require(len(ss)==len(keys)==12,"O3 missing/duplicate samples")
                    methods[method]=keys
                require(methods["vdot"].keys()==methods["rvv"].keys(),"method pairing")
                groups[mode]=methods
            for method in ("vdot","rvv"):
                for key,a in groups["o1"][method].items():
                    b=groups["o2"][method][key]
                    require(all(a[k]==b[k] for k in ("instructions","image_sha256","m","k","seq")),"cross-mode code/work mismatch")
            row={"shard":shard,"software":software}
            for mode in ("o1","o2"):
                row[mode]={}
                for method,values in groups[mode].items():
                    cycles=[v["cycles"] for v in values.values()]
                    row[mode][method]=dict(mean_cycles=sum(cycles)/12,sum_cycles=sum(cycles),min_cycles=min(cycles),max_cycles=max(cycles),samples=12)
                row[mode]["rvv_over_vdot"]=row[mode]["rvv"]["sum_cycles"]/row[mode]["vdot"]["sum_cycles"]
            example=next(iter(groups["o1"]["vdot"].values()))
            row.update(m=example["m"],k=example["k"],scope=example["scope"],
                       o2_vdot_cycle_reduction=1-row["o2"]["vdot"]["sum_cycles"]/row["o1"]["vdot"]["sum_cycles"],
                       o2_rvv_cycle_reduction=1-row["o2"]["rvv"]["sum_cycles"]/row["o1"]["rvv"]["sum_cycles"])
            output.append(row)
    # Best RVV is selected only within the same shape/scope/hardware, show both constituent rows too.
    best=[]
    for shard in range(8):
        rows=[v for v in output if v["shard"]==shard]
        for mode in ("o1","o2"):
            rv=min(rows,key=lambda v:v[mode]["rvv"]["sum_cycles"])
            vd=min(rows,key=lambda v:v[mode]["vdot"]["sum_cycles"])
            best.append(dict(shard=shard,mode=mode,m=rv["m"],k=rv["k"],scope=rv["scope"],
                             rvv_software=rv["software"],vdot_software=vd["software"],
                             rvv_over_vdot=rv[mode]["rvv"]["sum_cycles"]/vd[mode]["vdot"]["sum_cycles"]))
    return dict(rows=output,best_rvv_comparison=best,measured_samples=measured)

def run(args):
    out=args.output;out.mkdir(parents=True,exist_ok=False)
    lock=Lock();records=[]
    state=dict(status="PREFLIGHT",source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
               started_utc=now(),new_emu_jobs=0,planned_jobs=56,github_pushed=False,images=str(args.images))
    save(out/"state.json",state)
    try:
        pins={m:json.loads(p.read_text()) for m,p in (("o1",g4.O1_PINS),("o2",g4.O2_PINS))}
        g4.validate_pair(pins["o1"],pins["o2"])
        files,profile=g4.build_profile(g4.O1_PINS.parent,g4.O2_PINS.parent)
        save(out/"build-profile.json",profile)
        for group in ("files","dependency_files"):files.update({str(ROOT/name):digest for name,digest in pins["o2"][group].items()})
        for mode in ("o1","o2"):
            files[pins[mode]["emu_path"]]=pins[mode]["emu_sha256"];save(out/(mode+"-hardware-pins.json"),pins[mode])
        files[str(g4.REFERENCE)]="efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4"
        files[str(g4.FLASH)]="a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994"
        for path in (ROOT/"build/constantin.txt",ROOT/"build/plusArgs"):files[str(path)]=sha(path)
        drivers=[*HERE.glob("*.py"),HERE/"CONTRACT.md",HERE/"main.c",HERE/"Makefile",HERE/"fixed-layout.ld",
                 ROOT/"team/workloads/unified-vdot/check.py",ROOT/"team/workloads/unified-vdot/generate.py",
                 ROOT/"team/optimizations/o2/performance/compare.py",ROOT/"team/optimizations/o2/performance/build_profile.py",
                 ROOT/"team/optimizations/o1/fullcore/analyze.py",ROOT/"team/optimizations/o2/fullcore/analyze.py",
                 ROOT/"team/optimizations/o1/audit/runtime_gate.py",ROOT/"team/optimizations/o2/fullcore/workloads/check.py"]
        for path in drivers:
            body=subprocess.check_output(["git","show",state["source_commit"]+":"+path.relative_to(ROOT).as_posix()],cwd=ROOT)
            require(hashlib.sha256(body).hexdigest()==sha(path),"driver not committed "+str(path))
            files[str(path)]=sha(path)
            target=out/"source"/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        # Calibration is intentionally reused, with immutable G4 provenance.
        calibration=Path("/home/riscv/riscv-lab/o2-performance-20261019/campaign-01")
        for mode in ("o1","o2"):
            path=calibration/mode/"smoke"/"smoke-d0-s00-r0"/"result.json"
            rec=json.loads(path.read_text())
            require(rec["status"]=="PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS" and rec["files"][pins[mode]["emu_path"]]==pins[mode]["emu_sha256"],"calibration mode mismatch")
            files[str(path)]=sha(path)
        images=json.loads((args.images/"images.json").read_text())["images"]
        expected=[("smoke",0,s) for s in (0,7)]+[("performance",d,s) for d in range(3) for s in range(8)]
        require([(x["suite"],x["dataset"],x["shard"]) for x in images]==expected,"exact image inventory")
        files[str(args.images/"images.json")]=sha(args.images/"images.json")
        for image in images:
            build=Path(image["path"]);require(build==args.images/image["name"],"foreign image")
            manifest=json.loads((build/"data/manifest.json").read_text())
            require(manifest["contract"]=="o3-gemv-s8-r32-v1","wrong application contract")
            check.base.verify_generation(build,manifest);check.base.check_compiled_cases(build/"vdot-perf.elf",manifest)
            for p in build.rglob("*"):
                if p.is_file() and "objects" not in p.relative_to(build).parts:files[str(p)]=sha(p)
        save(out/"artifact-pins.json",files);verify_hashes(files)
        observers={m:load("o3_observer_"+m,ROOT/("team/optimizations/"+m+"/fullcore/analyze.py")) for m in ("o1","o2")}
        gate=load("o3_strict_runtime",ROOT/"team/optimizations/o1/audit/runtime_gate.py")
        fatal=load("o3_fatal_output",ROOT/"team/optimizations/o2/fullcore/workloads/check.py")
        state.update(status="RUNNING",preflight_finished_utc=now());save(out/"state.json",state)
        def execute(mode,image,replay):
            build=Path(image["path"]);directory=out/mode/(image["name"]+f"-r{replay}");directory.mkdir(parents=True)
            command=["timeout","120m","stdbuf","-o0","-e0",pins[mode]["emu_path"],"-i",str(build/"vdot-perf.bin"),
                     "--flash="+str(g4.FLASH),"--ram-size=128MB","--diff="+str(g4.REFERENCE),"--max-cycles=2000000","--seed=1"]
            record=dict(mode=mode,image=image["name"],suite=image["suite"],shard=image["shard"],dataset=image["dataset"],
                        build=str(build),replay=replay,command=command,cwd=str(ROOT),started_utc=now(),status="RUNNING",
                        files={str(p):files[str(p)] for p in (Path(pins[mode]["emu_path"]),g4.REFERENCE,g4.FLASH,build/"vdot-perf.bin")})
            save(directory/"runtime.json",record)
            try:
                verify_hashes(files)
                with (directory/"stdout.log").open("wb") as a,(directory/"stderr.log").open("wb") as b:
                    rc=subprocess.run(command,cwd=ROOT,stdout=a,stderr=b).returncode
                record.update(exit_code=rc,raw_sha256={name:sha(directory/name) for name in ("stdout.log","stderr.log")})
                (directory/"exit-code.txt").write_text(str(rc)+"\n");save(directory/"result.json",record)
                require(rc==0,"nonzero EMU exit")
                stdout=(directory/"stdout.log").read_text();stderr=(directory/"stderr.log").read_text()
                for stream in (stdout,stderr):fatal.reject_fatal_output(stream);gate.validate_failure_markers(stream)
                g4.validate_loaded_reference(stderr+stdout,g4.REFERENCE,gate.normalize_console)
                windows=check.verify(build,directory)
                manifest=json.loads((build/"data/manifest.json").read_text())
                analysis=observers[mode].analyze(stderr+stdout)
                g4.observer_gate(mode,analysis,g4.expected_commits(manifest))
                samples=[]
                for sample,entry in zip(windows["samples"],manifest["plan"]):
                    row=manifest["rows"][entry["index"]]
                    samples.append(dict(sample,mode=mode,shard=image["shard"],software=row["software"],m=row["m"],k=row["k"],
                                        scope=row["scope"],image_sha256=sha(build/"vdot-perf.bin")))
                record.update(status="O3_IMAGE_DIFFTEST_STATE_WINDOWS_AND_PROTOCOL_PASS",samples=samples,observation_counts=analysis["counts"])
                save(directory/"windows.json",windows);save(directory/"observation.json",analysis);verify_hashes(files)
            except Exception as exc:record.update(status="FAILED",error=repr(exc))
            record["finished_utc"]=now();save(directory/"result.json",record)
            with lock:
                records.append(record);state["new_emu_jobs"]=len(records)
                save(out/"progress.json",[{k:v for k,v in x.items() if k!="samples"} for x in records]);save(out/"state.json",state)
                print(mode,image["name"],replay,record["status"],record.get("error",""),flush=True)
            return record
        def pair(task):
            number,image,replay=task
            order=("o1","o2") if (number+replay)%2==0 else ("o2","o1")
            answer=[]
            for mode in order:
                value=execute(mode,image,replay);answer.append(value)
                if value["status"]=="FAILED":break
            return answer
        for stage in ("smoke","performance","replay"):
            state["stage"]=stage;save(out/"state.json",state)
            if stage=="replay":
                image=next(i for i in images if i["suite"]=="performance" and i["dataset"]==0 and i["shard"]==5)
                tasks=[(100,image,r) for r in (1,2)]
            else:tasks=[(n,i,0) for n,i in enumerate(images) if i["suite"]==stage]
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=[f.result() for f in as_completed([pool.submit(pair,t) for t in tasks])]
            require(all(len(v)==2 and all(x["status"]=="O3_IMAGE_DIFFTEST_STATE_WINDOWS_AND_PROTOCOL_PASS" for x in v) for v in results),"stage failed "+stage)
            print(stage,"O3_STAGE_PASS",flush=True)
        require(len(records)==56,"job cardinality")
        for mode in ("o1","o2"):
            rows=[r for r in records if r["mode"]==mode and r["image"]=="performance-d0-s05"]
            base=next(x for x in rows if x["replay"]==0)
            for replay in (1,2):
                value=next(x for x in rows if x["replay"]==replay)
                require([(s["seq"],s["cycles"],s["instructions"]) for s in value["samples"]]==[(s["seq"],s["cycles"],s["instructions"]) for s in base["samples"]],"non-deterministic representative replay")
        stats=summarize(records);verify_hashes(files)
        result=dict(status="O3_PAIRED_APPLICATION_CAMPAIGN_PASS",source_commit=state["source_commit"],runs=records,**stats,
                    real_emu_jobs=len(records),validated_windows=sum(len(r["samples"]) for r in records),measured_windows=768,
                    replay_jobs=4,performance_measured=True,github_pushed=False,finished_utc=now())
        save(out/"result.json",result);state.update(status=result["status"],finished_utc=now());save(out/"state.json",state)
        print(result["status"],flush=True)
    except Exception as exc:
        state.update(status="FAILED",error=repr(exc),finished_utc=now());save(out/"state.json",state);raise

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",required=True,type=Path);p.add_argument("--images",required=True,type=Path)
    run(p.parse_args())
