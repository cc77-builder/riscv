"""Read-only raw audit of explicitly counted firstdot continuation campaigns.

All original process records retain their actual directories and CWDs. Interrupted
attempts are preserved by controller seals and never enter successful samples.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

LEAF = Path("team/optimizations/o2/integration/firstdot-v2-0f")
CONTRACT = "zjhwork-0f-firstdot-continuation-raw-audit-v2-wall-clock-limited"
BASE_SHA = "1daf43dcebba9c40569af8b767c42ecb2360ac387be6d7834d46244bebdbe980"
MATRIX_PASS = "CURRENT_FIRSTDOT_RESUMED_PAIRED_C_ABI_PASS"
C_PASS = "CURRENT_FIRSTDOT_C_CONTINUATION_PASS"
FINAL_PASS = "CURRENT_FIRSTDOT_CONTINUATION_FUNCTIONAL_CYCLES_AUDIT_PASS_WALL_CLOCK_LIMITED"

def load(name,path):
    path=Path(path)
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(),str(path),"exec"),value.__dict__)
    return value

def helpers(repo):
    base=load("_resume_base_audit",repo/LEAF/"audit/audit_combination.py")
    base.require(base.sha(base.__file__)==BASE_SHA,"frozen base audit changed")
    # This private module changes only the envelope label used by its byte
    # archive helper. No underlying runtime or historical disk file is edited.
    base.CONTRACT=CONTRACT
    return base

def matrix_order(combo,images):
    target=next(i for i in images if (i["shard"],i["dataset"],i["variant"])==(3,0,"firstdot"))
    order=[("negative-firstdot-8x32",target,True,0),("recovery-firstdot-8x32",target,False,0)]
    for image in sorted(images,key=lambda i:(i["shard"],i["dataset"],
                         combo.VARIANTS.index(i["variant"]) ^ ((i["shard"]+i["dataset"])%2))):
        if image["name"]!=target["name"]:
            order.append(("formal-"+image["name"],image,False,0))
    order.extend(("replay-"+i["name"],i,False,1) for i in images if i["dataset"]==0)
    return order

CONTROLLER_SHA = "cefc280fe142428b79c858eb83cc4db59aeb011dd8165b4b69c188ec71d35482"
MERGED_SCREEN = Path("team/optimizations/o2/r2-safe-tail/merged_screen.py")
MERGED_SCREEN_SHA = "ff75464c5b0f75349fc4321bdd80a7a85985a54ae415ad347c3ce04fdf4bd885"

def private_matrix_qualify(a, controller, repo, identity_path, build, run):
    """Correct exactly two read-only module paths without editing the controller."""
    source_path = Path(controller.__file__).resolve()
    a.require(a.sha(source_path) == CONTROLLER_SHA, "unrecognized frozen continuation controller")
    target = repo / MERGED_SCREEN
    a.require(a.sha(target) == MERGED_SCREEN_SHA
              and a.read(run / "runtime-inputs.json").get(str(target)) == MERGED_SCREEN_SHA,
              "corrected checker is not the actual frozen runtime dependency")
    source = source_path.read_text()
    function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "qualify")
    original = "\n".join(source.splitlines()[function.lineno-1:function.end_lineno]) + "\n"
    old = 'repo/"team/optimizations/o2/r2-vector-accum/merged_screen.py"'
    new = 'repo/"team/optimizations/o2/r2-safe-tail/merged_screen.py"'
    a.require(original.count(old) == 2, "qualification path substitution sites differ")
    patched = original.replace(old, new)
    namespace = dict(vars(controller))
    # __file__ intentionally remains the real frozen controller location, so its
    # existing source-lock, snapshot, process, replay and count checks all run.
    exec(compile(patched, str(source_path) + ":read-only-path-adapter", "exec"), namespace)
    proof = namespace["qualify"](repo, identity_path, build, run)
    a.require(a.sha(source_path) == CONTROLLER_SHA and a.sha(target) == MERGED_SCREEN_SHA,
              "qualification controller/checker changed during read-only audit")
    adaptation = dict(
        status="CURRENT_FIRSTDOT_QUALIFICATION_PATH_ADAPTER_PASS",
        frozen_controller=str(source_path), frozen_controller_sha256=CONTROLLER_SHA,
        corrected_checker=str(target), corrected_checker_sha256=MERGED_SCREEN_SHA,
        original_function_sha256=hashlib.sha256(original.encode()).hexdigest(),
        private_function_sha256=hashlib.sha256(patched.encode()).hexdigest(),
        substitutions=2, change="r2-vector-accum/merged_screen.py to existing r2-safe-tail/merged_screen.py",
        retained_actual_file_binding=True, controller_source_modified=False,
        runtime_records_modified=False, new_emu_runs=0)
    return proof, adaptation

def raw_matrix(a,combo,repo,identity_path,build,run,controller,output):
    qualification, qualification_adapter = private_matrix_qualify(a,controller,repo,identity_path,build,run)
    a.save(output/"matrix-qualification-adapter.json",qualification_adapter)
    identity,hardware,profile=combo.parent_identity(repo,identity_path,physical=True)
    f,m=combo.runtime(repo,identity);cfg=identity["configuration"]
    images=a.read(build/"images.json")["images"]
    combo.verify_build_scope(repo,build,images,identity_path)
    a.require(len(images)==24,"incomplete matrix images")
    for image in images:
        combo.validate_image(image,build);combo.g.verify_build(Path(image["path"]),repo)
        m.validate_selection(image,a.read(Path(image["path"])/"data/manifest.json"),
                             a.read(Path(image["path"])/"build.json"))
    pairs=combo.pairs(images,repo)
    a.require(pairs==a.read(build/"pairs.json"),"matrix paired layout differs")
    common=a.matrix_common(combo,repo,identity_path,build,images,hardware,m)
    cached=a.read(run/"results.json")
    a.require(cached["status"]==MATRIX_PASS,"continuation matrix incomplete")
    locations=a.read(run/"run-locations.json")
    ordered=matrix_order(combo,images)
    a.require(set(locations)=={r[0] for r in ordered},"matrix location inventory")
    negative_root=Path(locations["negative-firstdot-8x32"]).parents[1]
    fixture=a.negative_fixture(negative_root,cfg,m)
    suite=combo.g.load("_resume_matrix_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
    normal=[];all_records=[];negative=None;inputs=dict(common)
    for label,image,rejected,replay in ordered:
        directory=Path(locations[label]).resolve()
        a.require(str(directory)==locations[label] and directory.name==label,"matrix actual directory binding")
        record=a.read(directory/"result.json")
        wanted=a.process_receipt(record,image,directory,common,cfg,m,rejected,fixture,replay)
        inputs=a.merge_inputs(inputs,wanted)
        suite.validate_runtime((directory/"stdout.log").read_text()+(directory/"stderr.log").read_text(),
                               record["reference"])
        if rejected:
            with tempfile.TemporaryDirectory(prefix="resumed-firstdot-negative-") as td:
                temp=Path(td)
                for name in ("stdout.log","stderr.log"):shutil.copyfile(directory/name,temp/name)
                detail=m.negative_check(repo,Path(image["path"]),temp,record)
                a.require(detail==record["negative_details"]==a.read(directory/"negative.json")
                          and a.read(temp/"observation.json")==a.read(directory/"observation.json"),"matrix negative raw differs")
                a.require(detail["vd"]==0 and detail["bit"]==100 and detail["word"]=="0x0388000b","wrong firstdot negative")
            negative=record
        else:
            windows,analysis=f.verify_runtime(repo,Path(image["path"]),directory)
            a.require(a.plain(windows)==a.read(directory/"windows.json")
                      and a.plain(analysis)==a.read(directory/"observation.json"),"matrix raw window/observation drift")
            manifest=a.read(Path(image["path"])/"data/manifest.json")
            a.require(len(windows["samples"])==len(manifest["plan"])==24,"matrix sample plan inventory")
            samples=[]
            for sample,plan in zip(windows["samples"],manifest["plan"]):
                row=manifest["rows"][plan["index"]]
                samples.append(dict(sample,mode="merged",variant=image["variant"],shard=image["shard"],
                    software=row["software"],m=row["m"],k=row["k"],scope=row["scope"],image_sha256=image["image_sha256"]))
            a.require(a.plain(samples)==record["samples"],"matrix samples differ from raw")
            normal.append(record)
        all_records.append(record)
        print(label,"RAW_RECOMPUTED",flush=True)
    a.require(len(normal)==32 and cached["runs"]==normal and cached["negative"]==negative,"matrix cached records differ")
    m.validate_recovery(negative,normal[0])
    by={r["name"]:r for r in normal if r["replay"]==0}
    for repeated in (r for r in normal if r["replay"]==1):
        a.require(m.signature(repeated)==m.signature(by[repeated["name"]]),"matrix all-window replay differs")
    summary=combo.summarize(normal)
    a.require(all(cached[k]==v for k,v in summary.items()),"matrix recomputed summary differs")
    a.require(cached["qualification"]==combo.qualification(images,normal,True,True),"matrix original coverage differs")
    chronology=load("_resume_chronology",Path(__file__).with_name("chronology.py"))
    chronology_proof,chronology_inputs=chronology.verify(a,repo,run,[r[0] for r in ordered],all_records,locations)
    inputs=a.merge_inputs(inputs,chronology_inputs)
    a.save(output/"chronology-proof.json",chronology_proof)
    a.require(len({(r["pid"],r["started"],r["cwd"]) for r in all_records})==33,"duplicate completed matrix process")
    a.verify_files(inputs)
    proof=dict(status="CURRENT_FIRSTDOT_RESUMED_MATRIX_RAW_PASS_WALL_CLOCK_LIMITED",qualified_processes=33,
               actual_launched_processes=34,interrupted_processes=1,new_emu_runs=0,
               process_identity="pid+started+actual cwd; PID alone may repeat after WSL restart",
               qualification=qualification,qualification_adapter=qualification_adapter,chronology=chronology_proof,**summary)
    a.save(output/"matrix-raw-proof.json",proof)
    return identity,proof,inputs

def c_common(a,combo,repo,identity,build):
    base=combo.c_adapter(repo,identity)
    files=base.a.frozen_m.checker_files(repo)
    files.update({str(repo/rel):digest for rel,digest in base.source_files(repo).items()})
    hardware,profile=base.a.frozen_m.hardware_profile(repo,identity["configuration"]);files.update(hardware)
    for name in ("build.json","elf-validation.json","vdot-perf.elf","vdot-perf.bin","gemv-reference.o"):
        files[str(build/name)]=a.sha(build/name)
    for name in base.FILES:files[str(build/"source"/name)]=a.sha(build/"source"/name)
    receipt=a.read(build/"build.json");files.update(receipt["external_files"])
    files.update({row["path"]:row["sha256"] for row in receipt["toolchain"].values()})
    return base,files,profile

def c_receipt(a,record,directory,common,cfg,fixture,base,build,label,validation):
    negative=label=="negative";m=base.a.frozen_m
    reference=fixture["binary"] if negative else cfg["reference"]
    cwd=directory/"cwd";wanted=dict(common)
    wanted.update({str(cwd/"build"/n):digest for n,digest in m.AUX.items()})
    if negative:wanted[reference]=fixture["negative_sha256"]
    argv=[str(Path(cfg["hardware_source"])/"build/emu"),"-i",str(build/"vdot-perf.bin"),
          "--flash="+cfg["flash"],"--ram-size=128MB","--diff="+reference,"--max-cycles=2000000","--seed=1"]
    a.require(record["name"]=="r4-c-api-s1" and record["contract"]==base.CONTRACT
              and record["negative"] is negative and record["replay"]==int(label=="replay")
              and record["cwd"]==str(cwd) and record["command"]==argv and record["reference"]==reference,
              "C execution selection/command differs")
    a.require(record["files"]==wanted and record["image_sha256"]==validation["image_sha256"]
              and record["environment_overrides"]=={"XS_NEGATIVE_VECTOR_TARGET":"vdot" if negative else None},
              "C execution input closure differs")
    a.require(record["process_started"] is True and type(record["pid"]) is int and record["pid"]>0
              and not record.get("timed_out") and type(record["exit_code"]) is int
              and record["exit_code"]==(1 if negative else 0) and record["performance_measured"] is False
              and record["status"]==(m.NEGATIVE_PASS if negative else "R4_C_APPLICATION_DIFFTEST_PASS"),
              "C execution did not complete as expected")
    a.require(record["raw_sha256"]=={n:a.sha(directory/n) for n in ("stdout.log","stderr.log")},"C raw hash differs")
    a.timeline(record)
    return wanted

def raw_c(a,combo,repo,identity_path,identity,matrix_build,build,run,controller,output):
    qualification=controller.qualify(repo,identity_path,matrix_build,build,run)
    base,common,profile=c_common(a,combo,repo,identity,build);cfg=identity["configuration"]
    validation=base.verify_build(repo,build)
    a.require(a.read(build/"elf-validation.json")==validation and a.read(build/"build.json").get("accepted") is True,
              "C build validation differs")
    anchor=combo.library_anchor(repo,build,matrix_build)
    a.require(anchor==a.read(build/"matrix-anchor.json"),"C matrix leaf anchor differs")
    a.require(a.read(build/"combination-c-build.json")==dict(contract=combo.CONTRACT,adapter_files=combo.adapter_files()),
              "C build adapters differ")
    cached=a.read(run/"results.json");a.require(cached["status"]==C_PASS,"C continuation incomplete")
    locations=cached["record_locations"]
    a.require(set(locations)=={"negative","recovery","replay"},"C actual record inventory")
    negative_root=Path(locations["negative"]).parents[1]
    fixture=a.negative_fixture(negative_root,cfg,base.a.frozen_m)
    suite=combo.g.load("_resume_c_banner",repo/"team/optimizations/o2/fullcore/run_suite.py")
    records=[];inputs=dict(common)
    for label in ("negative","recovery","replay"):
        directory=Path(locations[label]).resolve()
        a.require(str(directory)==locations[label] and directory.name==label,"C actual directory binding")
        record=a.read(directory/"result.json")
        inputs=a.merge_inputs(inputs,c_receipt(a,record,directory,common,cfg,fixture,base,build,label,validation))
        suite.validate_runtime((directory/"stdout.log").read_text()+(directory/"stderr.log").read_text(),record["reference"])
        if label=="negative":
            with tempfile.TemporaryDirectory(prefix="resumed-c-negative-") as td:
                scratch=Path(td)
                for name in ("stdout.log","stderr.log"):shutil.copyfile(directory/name,scratch/name)
                details=base.a.frozen_m.negative_check(repo,build,scratch,record)
                a.require(details==record["negative_details"]==a.read(directory/"negative.json")
                          and a.read(scratch/"observation.json")==a.read(directory/"observation.json"),"C negative raw differs")
                elf=combo.g.ELF((build/"vdot-perf.elf").read_bytes());pc=int(details["pc"],16)
                a.require(any(elf.symbols[r["api_symbol"]][0]<=pc<sum(elf.symbols[r["api_symbol"]][:2])
                              for r in a.read(build/"source/manifest.json")["rows"]),"C negative outside public function")
        else:
            checked,analysis=base.normal_check(repo,build,directory,record)
            a.require(checked==record["validation"]==a.read(directory/"validation.json")
                      and a.plain(analysis)==a.read(directory/"observation.json"),"C raw case outputs differ")
        records.append(record);print("ordinary-C",label,"RAW_RECOMPUTED",flush=True)
    base.validate_recovery(records[0],records[1])
    a.require(records[1]["validation"]==records[2]["validation"],"C case replay differs")
    a.require(cached["runs"]==records and all(a.timeline(x)[1]<=a.timeline(y)[0] for x,y in zip(records,records[1:])),
              "C records/chronology differ")
    a.verify_files(inputs)
    proof=dict(status="CURRENT_FIRSTDOT_RESUMED_C_RAW_AUDIT_PASS",qualified_processes=3,
               actual_launched_processes=4,interrupted_processes=1,normal_case_executions=96,distinct_cases=48,
               public_functions=16,performance_measured=False,qualification=qualification,matrix_anchor=anchor,new_emu_runs=0)
    a.save(output/"c-raw-proof.json",proof)
    return proof,inputs


def collect_continuation_inputs(a,matrix_run,c_run,matrix_controller,c_controller,interruption_receipt):
    binding=a.read(matrix_run/"continuation-inputs.json")
    prior_matrix=Path(binding["prior_root"])
    c_prior=a.read(c_run/"prior-interruption.json")
    prior_c=Path(c_prior["prior_root"])
    extras=dict(binding["controller_files"])
    extras.update(c_prior["frozen_files"])
    for path in (matrix_controller,c_controller,interruption_receipt):
        a.require(Path(path).is_file() and not Path(path).is_symlink(),"invalid continuation control source")
        extras[str(path)]=a.sha(path)
    a.verify_files(extras)
    return prior_matrix,prior_c,extras

def run(args):
    paths={k:Path(v).resolve() for k,v in vars(args).items() if v is not None}
    repo=paths["repo"];output=paths["output"];a=helpers(repo);combo=a.load_combination(repo)
    identity_path=paths["identity"];matrix_build=paths["matrix_build"];matrix_run=paths["matrix_run"]
    c_build=paths["c_build"];c_run=paths["c_run"]
    a.fresh_output(output,[p for k,p in paths.items() if k!="output"])
    output.mkdir(parents=True)
    state=dict(contract=CONTRACT,status="RUNNING",started=datetime.now(timezone.utc).isoformat(),
               audit_tool_sha256=a.sha(__file__),base_audit_sha256=BASE_SHA,
               new_emu_runs=0,new_nemu_runs=0,standalone_raw_recomputation=False,
               independent_clean_reproduction=False,interrupted_results_counted_as_pass=False)
    a.save(output/"state.json",state)
    try:
        matrix_controller=load("_resume_matrix_controller",paths["matrix_controller"])
        c_controller=load("_resume_c_controller",paths["c_controller"])
        prior_matrix,prior_c,extra=collect_continuation_inputs(a,matrix_run,c_run,paths["matrix_controller"],
                                                             paths["c_controller"],paths["interruption_receipt"])
        roots=(matrix_build,matrix_run,c_build,c_run,prior_matrix,prior_c)
        evidence={str(p):a.sha(p) for root in roots for p in a.tree_files(root)}
        a.save(output/"evidence-inputs.json",evidence)
        identity,matrix_proof,matrix_inputs=raw_matrix(a,combo,repo,identity_path,matrix_build,matrix_run,matrix_controller,output)
        c_proof,c_inputs=raw_c(a,combo,repo,identity_path,identity,matrix_build,c_build,c_run,c_controller,output)
        inputs=a.merge_inputs(matrix_inputs,c_inputs,extra)
        for path in (Path(__file__),Path(__file__).with_name("chronology.py"),repo/LEAF/"audit/audit_combination.py",repo/LEAF/"audit/orchestration_receipt.py"):
            inputs[str(path)]=a.sha(path)
        a.verify_files(inputs);a.verify_files(evidence)
        a.save(output/"external-inputs.json",inputs)
        a.save(output/"combination-qualification.json",dict(
            contract=CONTRACT,status="CURRENT_FIRSTDOT_CONTINUATION_COMBINATION_PASS_WALL_CLOCK_LIMITED",
            functional_validation="PASS",target_cycle_validation="PASS",
            wall_clock_chronology="FAIL",causal_serial_order="PASS",
            chronology_proof_sha256=a.sha(output/"chronology-proof.json"),
            hardware_identity_sha256=a.sha(identity_path),
            matrix=matrix_proof["qualification"],ordinary_c=c_proof["qualification"],
            qualified_processes=36,actual_launched_processes=38,interrupted_processes=2,
            inherited_launched_processes=15,continuation_new_emu_processes=23,
            formal_windows=384,normal_case_executions=96,hardware_changed=False,
            stable_default_changed=False,clean_reproduction=False,new_emu_runs=0))
        selected=a.archive_inputs(repo,identity_path,identity,matrix_build,matrix_run,c_build,c_run,inputs,output,combo)
        for label,root in (("prior-matrix-run",prior_matrix),("prior-c-run",prior_c)):
            for p in a.tree_files(root):selected[label+"/"+p.relative_to(root).as_posix()]=p
        for label,path in (("matrix",paths["matrix_controller"]),("ordinary-c",paths["c_controller"])):
            for p in sorted(path.parent.iterdir()):
                if p.is_file() and p.suffix in (".py",".md"):
                    selected["continuation-tools/"+label+"/"+p.name]=p
        selected["continuation-tools/audit/resume_audit.py"]=Path(__file__)
        selected["continuation-tools/audit/chronology.py"]=Path(__file__).with_name("chronology.py")
        selected["raw-audit/chronology-proof.json"]=output/"chronology-proof.json"
        for i,(path,digest) in enumerate(sorted(extra.items())):
            selected[f"continuation-controls/{i:04d}/"+Path(path).name]=Path(path)
        selected["raw-audit/combination-qualification.json"]=output/"combination-qualification.json"
        selected["raw-audit/matrix-qualification-adapter.json"]=output/"matrix-qualification-adapter.json"
        archive=a.pack_archive(selected,output/"archive")
        a.verify_files(evidence);a.verify_files(inputs)
        state.update(status=FINAL_PASS,qualified_processes=36,actual_launched_processes=38,
                     functional_validation="PASS",target_cycle_validation="PASS",
                     wall_clock_chronology="FAIL",causal_serial_order="PASS",
                     chronology_proof_sha256=a.sha(output/"chronology-proof.json"),
                     interrupted_processes=2,continuation_new_emu_processes=23,inherited_launched_processes=15,
                     formal_windows=384,c_normal_case_executions=96,archive=archive,
                     hardware_source_commit=identity["source_commit"],emu_sha256=identity["hardware_profile"]["emu_sha256"],
                     matrix_raw_proof_sha256=a.sha(output/"matrix-raw-proof.json"),
                     c_raw_proof_sha256=a.sha(output/"c-raw-proof.json"),
                     combination_qualification_sha256=a.sha(output/"combination-qualification.json"))
    except BaseException as exc:
        state.update(status="FAILED",error=repr(exc));raise
    finally:
        state["finished"]=datetime.now(timezone.utc).isoformat();a.save(output/"state.json",state)
    return state

def verify_archive(repo,path):
    return helpers(Path(repo).resolve()).verify_archive(Path(path).resolve())

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("repo","identity","matrix-build","matrix-run","c-build","c-run",
                 "matrix-controller","c-controller","interruption-receipt","output"):
        p.add_argument("--"+name,type=Path,required=True)
    print(json.dumps(run(p.parse_args()),indent=2))
