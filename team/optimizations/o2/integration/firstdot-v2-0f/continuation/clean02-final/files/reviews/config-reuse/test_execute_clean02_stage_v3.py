
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("stage_executor",HERE/"execute_clean02_stage_v3.py")
e=importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
START="2026-10-27T00:00:00+00:00"
FINISH="2026-10-27T00:01:00+00:00"

def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+"\n")

class Gates(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name); self.clean=self.work/"clean-02"
        self.repo=self.clean/"checkout/source";self.repo.mkdir(parents=True)
        self.output=self.work/"config-output"
        self.identity=self.clean/"identity/current.json"
        put(self.identity,dict(contract="zjhwork-0f-firstdot-v2-clean-identity-v1",
            source_commit=e.SOURCE,hardware_profile=dict(emu_sha256=e.EMU),
            reference_sha256=e.NEMU,configuration=dict(hardware_source=str(self.repo))))
        ident_sha=e.sha(self.identity)
        self.plan=dict(paths=dict(work=str(self.work),clean=str(self.clean),repo=str(self.repo),
                output_root=str(self.output)),identity=dict(path=str(self.identity),sha256=ident_sha,
                emu_sha256=e.EMU,reference_sha256=e.NEMU),source_commit=e.SOURCE,
                adapter_copy=dict(source=str(self.work/"adapter-v2"),files={"probe.py":"a"*64}))
        state=self.clean/"fullcore-run-01/state.json"
        put(state,{"status":"CURRENT_CLEAN_FULLCORE_PASS"})
        (state.parent/"identity.json").write_bytes(self.identity.read_bytes())
        put(state.parent/"results.json",{"functional_status":"FUNCTIONAL_PASS"})
        phys=dict(status="CURRENT_CLEAN_PHYSICAL_RAW_AUDIT_PASS_WALL_CLOCK_LIMITED",source_run=str(state.parent),
            source_result_sha256=e.sha(state.parent/"results.json"),identity_sha256=ident_sha,
            source_new_emu_runs=14,new_emu_runs=0)
        pp=self.clean/"fullcore-physical-02/current-archive-physical.json";put(pp,phys)
        manifest=self.clean/"fullcore-archive-02/archive-manifest.json";put(manifest,{"files":["fixture"]})
        body=dict(files=1,archive_manifest_sha256=e.sha(manifest),new_emu_runs=0)
        pack=self.clean/"fullcore-pack-02.json";put(pack,dict(status="CURRENT_CLEAN_ARCHIVE_BYTES_SEALED_WALL_CLOCK_LIMITED",**body))
        byte=self.clean/"fullcore-bytes-02.json";put(byte,dict(status="CURRENT_CLEAN_ARCHIVE_BYTES_ONLY_PASS_WALL_CLOCK_LIMITED",**body))
        livephys=self.clean/"fullcore-archive-audit-02/current-archive-physical.json";put(livephys,phys)
        live=self.clean/"fullcore-archive-audit-02/archive-live-recheck.json"
        put(live,dict(status="CURRENT_CLEAN_ARCHIVE_LIVE_RAW_AUDIT_PASS_WALL_CLOCK_LIMITED",source_new_emu_runs=14,
            raw_audit_receipt_sha256=e.sha(livephys),**body))
        matrix=self.clean/"matrix-run-01/state.json"
        put(matrix,dict(status="CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS",new_emu_runs=33))
        combined=self.clean/"combination-audit-03/state.json"
        put(combined,dict(status="CURRENT_FIRSTDOT_RAW_RECOMPUTATION_AND_ARCHIVE_PASS",
            source_commit=e.SOURCE,emu_sha256=e.EMU,original_emu_processes=36,
            matrix_original_emu_processes=33,c_original_emu_processes=3,
            formal_windows=384,c_normal_case_executions=96))
        comparison=self.clean/"full-reproduction-comparison-03.json"
        put(comparison,dict(status="CURRENT_CLEAN_PROGRAMS_AND_ALL_WINDOWS_EQUAL",
            identities=dict(clean=ident_sha,clean_emu=e.EMU),windows=dict(compared_windows=768),
            audits=[{},dict(audit_sha256=e.sha(combined),status=e.read(combined)["status"])]))
        self.plan["release_gate"]=dict(all_required=True,json=[
            dict(path=str(p),expected={"status":e.read(p)["status"]})
            for p in (state,pp,pack,byte,live,matrix,combined,comparison)])
        post_plan=dict(repo=str(self.repo),identity=str(self.identity),stages={})
        def receipt(path,cmd):
            put(path,dict(command=cmd,cwd=str(self.repo),started=START,finished=FINISH,
                exit_code=0,pid=100,child_pid=101))
        for name in ("fullcore","matrix","ordinary_c"):
            cmd=["python3",name];path=self.clean/(name+".command.json")
            receipt(path,cmd);post_plan["stages"][name]=dict(command=cmd,receipt=str(path))
        stages=[]
        for name in e.POST_JOBS:
            cmd=["python3",name];path=self.clean/(name.replace("_","-")+("-02.command.json" if name in e.POST_JOBS[:4] else "-03.command.json"))
            receipt(path,cmd);post_plan["stages"][name]=cmd
            stages.append(dict(name=name,exit_code=0,receipt_sha256=e.sha(path),started=START,finished=FINISH))
        postplan=self.work/"clean-02-postbuild-plan-v3.json";put(postplan,post_plan)
        put(self.clean/"postprocess-03/state.json",dict(status="COMMANDS_EXIT_ZERO_REVIEW_PENDING",
            active=None,commands_started=3,reused_commands=4,stages=stages,started=START,finished=FINISH,
            plan_sha256=e.sha(postplan)))
        self.planpath=self.work/"plan.json";put(self.planpath,self.plan)
        self.marker=self.work/"marker.json"
        self.complete_limited_fixture()
        self.complete_retry_fixture()


    def complete_retry_fixture(self):
        post_path=self.clean/"postprocess-03/state.json";post=e.read(post_path)
        pp=self.work/"clean-02-postbuild-plan-v3.json";plan=e.read(pp)
        for i,row in enumerate(post["stages"]):row["reused"]=i<4
        oldrows=[{k:v for k,v in row.items() if k!="reused"} for row in post["stages"][:4]]
        oldrows.append(dict(name="finalize_c",exit_code=1))
        prior=self.clean/"postprocess-02/state.json"
        put(prior,dict(status="FAILED",commands_started=5,stages=oldrows))
        failed=self.clean/"finalize-c-02.command.json";put(failed,dict(exit_code=1))
        err=self.clean/"finalize-c-02.command.stderr.log";err.write_text("independent C outer launcher chronology differs")
        oldstate=self.clean/"c-run-01/state.json"
        put(oldstate,dict(status="R4_C_APPLICATION_CALLS_PASS",new_emu_runs=3,finished="2026-10-27T00:01:02.455386+00:00"))
        outer=self.clean/"c-run-01.command.json";put(outer,dict(finished=FINISH))
        preserved={str(p):e.sha(p) for p in (prior,failed,err,oldstate,outer)}
        pins={}
        for rel in ("orchestration/finalize_c.py","audit/audit_combination.py","audit/orchestration_receipt.py","reproduction/compare_reproduction.py"):
            p=self.repo/e.COMBO/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("strict semantic fixture "+rel)
            pins[str(p)]=e.sha(p)
        plan["preserved_c_failed_attempt"]=preserved;plan["frozen_semantic_source_files"]=pins
        plan["reused_fullcore_stages"]=copy.deepcopy(post["stages"][:4])
        plan["reused_fullcore_evidence"]={str(self.clean/"fullcore-pack-02.json"):e.sha(self.clean/"fullcore-pack-02.json")}
        newcmd=["python3","ordinary_c",str(self.clean/"c-run-02")]
        newreceipt=self.clean/"c-run-02.command.json"
        put(newreceipt,dict(command=newcmd,cwd=str(self.repo),started=START,finished=FINISH,exit_code=0,pid=200,child_pid=201))
        plan["stages"]["ordinary_c"]=dict(command=newcmd,receipt=str(newreceipt))
        put(self.clean/"c-run-02/state.json",dict(status="R4_C_APPLICATION_CALLS_PASS",new_emu_runs=3,active_pid=None,active_result=None))
        put(pp,plan)
        post["source_files"].update(preserved|pins|plan["reused_fullcore_evidence"])
        post["source_files"][str(pp)]=e.sha(pp);post["plan_sha256"]=e.sha(pp);put(post_path,post)
        self.plan["retry_evidence"]=dict(preserved=preserved,unchanged_semantic_sources=pins,
            selected_c_run=str(self.clean/"c-run-02"),previous_c_run=str(self.clean/"c-run-01"),
            C_chronology_contract_relaxed=False,old_C_original_processes=3)
        self.plan["postprocess_control"]["plan_sha256"]=e.sha(pp)
        put(self.planpath,self.plan)

    def test_retry_cannot_relax_chronology(self):
        self.plan["retry_evidence"]["C_chronology_contract_relaxed"]=True;self.refused()
    def test_retry_cannot_select_old_run(self):
        self.plan["retry_evidence"]["selected_c_run"]=str(self.clean/"c-run-01");self.refused()
    def test_retry_original_failure_kept(self):
        self.change("postprocess-02/state.json",lambda x:x.update(status="PASS"));self.refused()
    def test_retry_original_timestamp_kept(self):
        self.change("c-run-01/state.json",lambda x:x.update(finished=FINISH));self.refused()
    def test_retry_actual_fresh_c_must_finish(self):
        self.change("c-run-02/state.json",lambda x:x.update(active_pid=88));self.refused()
    def test_retry_actual_fresh_c_count(self):
        self.change("c-run-02/state.json",lambda x:x.update(new_emu_runs=2));self.refused()
    def test_retry_actual_commands_not_claimed_seven(self):
        self.change("postprocess-03/state.json",lambda x:x.update(commands_started=7));self.refused()
    def test_retry_reused_count_must_four(self):
        self.change("postprocess-03/state.json",lambda x:x.update(reused_commands=3));self.refused()
    def test_retry_old_stage_cannot_change(self):
        self.change("postprocess-03/state.json",lambda x:x["stages"][0].update(finished=START));self.refused()
    def test_retry_new_stage_cannot_be_reused(self):
        self.change("postprocess-03/state.json",lambda x:x["stages"][-1].update(reused=True));self.refused()
    def test_retry_semantic_validator_bytes_locked(self):
        path=self.repo/e.COMBO/"audit/orchestration_receipt.py";path.write_text("weakened validator");self.refused()
    def test_retry_failure_source_file_missing(self):
        (self.clean/"finalize-c-02.command.stderr.log").unlink();self.refused()


    def complete_limited_fixture(self):
        folder=self.work/"reviews/clean-fullcore-audit-v2";folder.mkdir(parents=True)
        oldplan=self.work/"clean-02-postbuild-plan.json";put(oldplan,{"preserved":True})
        olddriver=self.work/"finish_clean_validation.py";olddriver.write_text("frozen old driver")
        failure=self.clean/"fullcore-physical-01.command.json"
        put(failure,{"exit_code":1})
        stderr=self.clean/"fullcore-physical-01.command.stderr.log";stderr.write_text("recorded concurrency exceeds worker budget")
        stdout=self.clean/"fullcore-physical-01.command.stdout.log";stdout.write_text("")
        oldpost=self.clean/"postprocess-01/state.json"
        put(oldpost,dict(status="FAILED",commands_started=1,stages=[dict(name="fullcore_physical",exit_code=1)]))
        outerstdout=self.clean/"fullcore-run-01.command.stdout.log";outerstdout.write_text("fixture output")
        failed={str(p):e.sha(p) for p in (oldplan,olddriver,failure,stderr,stdout,oldpost)}
        evidence=failed|{str(outerstdout):e.sha(outerstdout),
            str(self.clean/"fullcore-run-01/results.json"):e.sha(self.clean/"fullcore-run-01/results.json"),
            str(self.clean/"fullcore-run-01/identity.json"):e.sha(self.clean/"fullcore-run-01/identity.json")}
        for i in range(71-len(evidence)):
            path=self.work/"case-evidence"/(str(i)+".txt");path.parent.mkdir(exist_ok=True);path.write_text(str(i))
            evidence[str(path)]=e.sha(path)
        case=dict(schema="current-clean-exact-wall-capacity-case-v1",run=str(self.clean/"fullcore-run-01"),
            repo=str(self.repo),source_commit=e.SOURCE,emu_sha256=e.EMU,jobs=3,recorded_peak=4,
            source_new_emu_runs=14,anomaly=dict(microseconds=80119,start=START,finish=FINISH),
            files=evidence,source_files={str(olddriver):e.sha(olddriver)},original_failure_command=str(failure),
            original_post_state=str(oldpost),original_failure_stderr=str(stderr),outer_stdout=str(outerstdout),
            expected_names=["job-"+str(i) for i in range(14)])
        put(folder/"exact-case.json",case)
        for name in ("current_clean_archive_v2.py","capacity_proof.py","runtime-source-lock.json"):
            (folder/name).write_text("frozen fixture "+name)
        files={name:e.sha(folder/name) for name in ("current_clean_archive_v2.py","capacity_proof.py","runtime-source-lock.json","exact-case.json")}
        closure=dict(contract="clean-fullcore-v2-runtime-closure-v1",files={str(folder/k):v for k,v in files.items()})
        put(folder/"runtime-closure.json",closure)
        for name,value in (("AUDITOR_FILES",files),("CAPACITY_CASE_SHA",files["exact-case.json"]),("CLOSURE_SHA",e.sha(folder/"runtime-closure.json"))):
            patcher=patch.object(e,name,value);patcher.start();self.addCleanup(patcher.stop)
        proof=dict(status=e.CAPACITY_STATUS,source_new_emu_runs=14,new_emu_runs=0,jobs=3,max_workers=3,
            recorded_peak=4,wall_clock_capacity="FAIL",source_bound_worker_capacity="PASS",
            os_monotonic_capacity_measured=False,clock_cause="UNCONFIRMED",exact_anomaly=case["anomaly"],
            exact_case_sha256=e.CAPACITY_CASE_SHA,original_v1_failure="FAIL_PRESERVED",
            original_wall_gate_verdict_preserved=True,timestamps_modified=False,records_reordered=False,
            tolerance_applied=False,semantic_raw_audit_granted=False,evidence_inputs=evidence,
            source_sha256=case["source_files"],original_failure_receipt_sha256=evidence[str(failure)],
            original_post_state_sha256=evidence[str(oldpost)],controller_stdout_sha256=evidence[str(outerstdout)],
            records={n:{"pid":i+1} for i,n in enumerate(case["expected_names"])})
        binding=dict(status="CURRENT_CLEAN_PROCESS_RECEIPTS_PASS_WALL_CLOCK_LIMITED",
            source_new_emu_runs=14,new_emu_runs=0,negative_recovery_same_image=True,
            source_bound_capacity_proof=proof,**e.LIMITED_FLAGS)
        for path in (self.clean/"fullcore-physical-02",self.clean/"fullcore-archive-audit-02"):
            put(path/"process-bindings.json",binding);put(path/"results.json",{"raw":"pass"})
            receipt=e.read(path/"current-archive-physical.json")
            receipt.update(contract=e.LIMITED_CONTRACT,**e.LIMITED_FLAGS,
                process_bindings_sha256=e.sha(path/"process-bindings.json"),raw_result_sha256=e.sha(path/"results.json"),
                auditor_sha256=files["current_clean_archive_v2.py"],capacity_source_sha256=files["capacity_proof.py"],
                capacity_case_sha256=e.CAPACITY_CASE_SHA)
            put(path/"current-archive-physical.json",receipt)
        for rel in ("fullcore-pack-02.json","fullcore-bytes-02.json","fullcore-archive-audit-02/archive-live-recheck.json"):
            path=self.clean/rel;value=e.read(path);value.update(contract=e.LIMITED_CONTRACT,**e.LIMITED_FLAGS)
            if "raw_audit_receipt_sha256" in value:
                value["raw_audit_receipt_sha256"]=e.sha(path.parent/"current-archive-physical.json")
            put(path,value)
        selected=dict(contract=e.LIMITED_CONTRACT,runtime_closure=dict(path=str(folder/"runtime-closure.json"),sha256=e.CLOSURE_SHA,files=closure["files"]),
            preserved_failed_attempt=failed)
        self.plan["fullcore_limited_audit"]=selected
        driver=self.work/"finish_clean_validation_v3.py";driver.write_text("frozen new driver")
        postplan=self.work/"clean-02-postbuild-plan-v3.json";value=e.read(postplan)
        value.update(contract="clean-02-postbuild-plan-v3-strict-c-retry",
            external_runtime_closure=selected["runtime_closure"],preserved_failed_attempt=failed,
            postprocess_receipts={name:str(self.clean/(name.replace("_","-")+("-02.command.json" if name in e.POST_JOBS[:4] else "-03.command.json"))) for name in e.POST_JOBS})
        put(postplan,value)
        self.plan["postprocess_control"]=dict(plan=str(postplan),plan_sha256=e.sha(postplan),
            driver=str(driver),driver_sha256=e.sha(driver))
        post=self.clean/"postprocess-03/state.json";value=e.read(post)
        value.update(contract="clean-postprocess-v3-strict-c-retry",source_sha256=e.sha(driver),
            source_files={str(driver):e.sha(driver), str(postplan):e.sha(postplan),
                str(folder/"runtime-closure.json"):e.CLOSURE_SHA,
                **closure["files"],**failed},plan_sha256=e.sha(postplan));put(post,value)
        put(self.planpath,self.plan)
        self.case=case;self.binding=binding

    def change(self,path,update):
        path=self.clean/path;v=e.read(path);update(v);put(path,v)
    def refused(self):
        with self.assertRaises((e.GateError,KeyError)):
            e.gate_metadata(self.plan)
        self.assertFalse(self.output.exists())
    def approval(self):
        ready=e.gate_metadata(self.plan)
        review=dict(contract=e.REVIEW_CONTRACT,status="ROOT_REVIEW_APPROVED",
            decision=e.REVIEW_DECISION,scope=e.REVIEW_SCOPE,reviewer="codex:/root",
            review_id="fixture-01",reviewed_at=FINISH,approved_stages=["import","after-audit"],
            plan_sha256=e.sha(self.planpath),executor_sha256=e.sha(e.__file__),
            identity_sha256=self.plan["identity"]["sha256"],source_commit=e.SOURCE,emu_sha256=e.EMU,
            adapter_files={str(Path(self.plan["adapter_copy"]["source"])/k):v for k,v in self.plan["adapter_copy"]["files"].items()})
        review.update({k:ready[k] for k in ("gate_files","completion_receipts","postprocess_state","postbuild_plan","fullcore_capacity_qualification","failed_attempts","fullcore_audit_runtime","c_retry_provenance")})
        rp=self.work/"review.json";put(rp,review)
        return ready,rp
    def test_complete_small_fixture(self):
        r=e.gate_metadata(self.plan)
        self.assertEqual((len(r["gate_files"]),len(r["completion_receipts"])),(8,10))
        self.assertFalse(self.output.exists())
    def test_missing_result(self):
        (self.clean/"fullcore-bytes-02.json").unlink();self.refused()
    def test_failed_status_even_if_plan_weakened(self):
        self.change("matrix-run-01/state.json",lambda v:v.update(status="FAILED"))
        self.plan["release_gate"]["json"][5]["expected"]={}
        self.refused()
    def test_matrix_count(self):
        self.change("matrix-run-01/state.json",lambda v:v.update(new_emu_runs=32));self.refused()
    def test_combined_count(self):
        self.change("combination-audit-03/state.json",lambda v:v.update(c_original_emu_processes=2));self.refused()
    def test_wrong_identity(self):
        self.change("identity/current.json",lambda v:v.update(source_commit="0"*40));self.refused()
    def test_comparison_identity(self):
        self.change("full-reproduction-comparison-03.json",lambda v:v["identities"].update(clean="0"*64));self.refused()
    def test_comparison_window_count(self):
        self.change("full-reproduction-comparison-03.json",lambda v:v["windows"].update(compared_windows=767));self.refused()
    def test_comparison_audit_sha(self):
        self.change("full-reproduction-comparison-03.json",lambda v:v["audits"][1].update(audit_sha256="0"*64));self.refused()
    def test_archive_chain(self):
        self.change("fullcore-bytes-02.json",lambda v:v.update(archive_manifest_sha256="0"*64));self.refused()
    def test_live_raw_binding(self):
        self.change("fullcore-archive-audit-02/archive-live-recheck.json",lambda v:v.update(raw_audit_receipt_sha256="0"*64));self.refused()
    def test_outer_command_unfinished(self):
        self.change("matrix.command.json",lambda v:v.pop("finished"));self.refused()
    def test_outer_command_failure(self):
        self.change("matrix.command.json",lambda v:v.update(exit_code=1));self.refused()
    def test_postprocess_still_active(self):
        self.change("postprocess-03/state.json",lambda v:v.update(active="full_comparison"));self.refused()
    def test_missing_review(self):
        with self.assertRaises(e.GateError):
            e.validate_review(self.plan,self.planpath,None,e.gate_metadata(self.plan),"import")
        self.assertFalse(self.output.exists())
    def test_valid_review_readonly(self):
        ready,rp=self.approval()
        with patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"import")
        self.assertFalse(self.marker.exists());self.assertFalse(self.output.exists())
    def test_review_wrong_plan(self):
        ready,rp=self.approval();v=e.read(rp);v["plan_sha256"]="0"*64;put(rp,v)
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"import")
        self.assertFalse(self.output.exists())
    def test_review_changed_gate(self):
        ready,rp=self.approval();ready["gate_files"][str(self.clean/"fullcore-pack-02.json")]="0"*64
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"import")
        self.assertFalse(self.output.exists())
    def test_review_consumed(self):
        ready,rp=self.approval();put(self.marker,{})
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"import")
        self.assertFalse(self.output.exists())
    def test_afteraudit_requires_approved_import(self):
        ready,rp=self.approval()
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
        self.assertFalse(self.output.exists())

    def imported_fixture(self):
        self.plan["source_import"]={"new_files":[{"path":"fixture-"+str(i)} for i in range(26)]}
        put(self.planpath,self.plan)
        ready,rp=self.approval()
        put(self.marker,dict(review_sha256=e.sha(rp),plan_sha256=e.sha(self.planpath),output_root=str(self.output)))
        preflight=self.output/"preflight"
        put(preflight/"identity-before.json",{"physical_inputs":{"fixture":"a"*64}})
        put(preflight/"identity-after-import.json",{"physical_inputs":{"fixture":"a"*64}})
        put(preflight/"import.json",dict(status="CONFIG_REUSE_UNTRACKED_IMPORT_IDENTITY_UNCHANGED",
            review_sha256=e.sha(rp),review_consumption_sha256=e.sha(self.marker),plan_sha256=e.sha(self.planpath),
            before_identity_sha256=e.sha(preflight/"identity-before.json"),
            after_identity_sha256=e.sha(preflight/"identity-after-import.json"),
            source_commit=e.SOURCE,emu_sha256=e.EMU,imported_files=26,dependencies_verified=39,
            imported=self.plan["source_import"]["new_files"],adapter_files=self.plan["adapter_copy"]["files"],
            git_index_unchanged=True,tracked_worktree_unchanged=True,staged=False,committed=False,
            main_imported=False,new_emu_runs=0,fullcore_capacity_qualification=ready["fullcore_capacity_qualification"],c_retry_provenance=ready["c_retry_provenance"]))
        return ready,rp,preflight
    def test_afteraudit_approved_import_bindings(self):
        ready,rp,preflight=self.imported_fixture()
        with patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
        self.assertFalse((preflight/"identity-after-audit.json").exists())
    def test_afteraudit_before_snapshot_tampered(self):
        ready,rp,preflight=self.imported_fixture()
        put(preflight/"identity-before.json",{"physical_inputs":{"fixture":"b"*64}})
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
    def test_afteraudit_after_snapshot_tampered(self):
        ready,rp,preflight=self.imported_fixture()
        put(preflight/"identity-after-import.json",{"physical_inputs":{"fixture":"b"*64}})
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
    def test_afteraudit_different_snapshots_even_with_matching_hashes(self):
        ready,rp,preflight=self.imported_fixture()
        put(preflight/"identity-after-import.json",{"physical_inputs":{"fixture":"b"*64}})
        value=e.read(preflight/"import.json")
        value["after_identity_sha256"]=e.sha(preflight/"identity-after-import.json")
        put(preflight/"import.json",value)
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
    def test_afteraudit_wrong_import_count(self):
        ready,rp,preflight=self.imported_fixture()
        value=e.read(preflight/"import.json");value["imported_files"]=25;put(preflight/"import.json",value)
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
    def test_afteraudit_wrong_import_source(self):
        ready,rp,preflight=self.imported_fixture()
        value=e.read(preflight/"import.json");value["source_commit"]="0"*40;put(preflight/"import.json",value)
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
    def test_afteraudit_wrong_import_emu(self):
        ready,rp,preflight=self.imported_fixture()
        value=e.read(preflight/"import.json");value["emu_sha256"]="0"*64;put(preflight/"import.json",value)
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")
    def test_afteraudit_wrong_import_adapter(self):
        ready,rp,preflight=self.imported_fixture()
        value=e.read(preflight/"import.json");value["adapter_files"]={};put(preflight/"import.json",value)
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"after-audit")

    def test_check_does_not_physical_or_create_output(self):
        ready,rp=self.approval()
        receipt=HERE/"test-receipts"/("fixture-check-"+str(__import__("os").getpid())+".json")
        self.addCleanup(lambda:receipt.unlink(missing_ok=True))
        with patch.object(e,"validate_plan",return_value={k:Path(v) for k,v in self.plan["paths"].items()}), \
             patch.object(e,"review_marker",return_value=self.marker), \
             patch.object(e,"capture_identity",side_effect=AssertionError("physical forbidden")), \
             patch.object(e,"source_inputs",side_effect=AssertionError("source scan forbidden")):
            code=e.main(["--stage","import","--plan",str(self.planpath),"--review",str(rp),"--receipt",str(receipt)])
        self.assertEqual(code,0);self.assertFalse(self.output.exists());self.assertFalse(self.marker.exists())


    def test_limited_status_cannot_be_standard_pass(self):
        self.change("fullcore-physical-02/current-archive-physical.json",lambda v:v.update(status="CURRENT_CLEAN_PHYSICAL_RAW_AUDIT_PASS"))
        self.refused()
    def test_wall_clock_claim_cannot_be_pass(self):
        self.change("fullcore-pack-02.json",lambda v:v.update(wall_clock_capacity="PASS"));self.refused()
    def test_monotonic_measurement_cannot_be_claimed(self):
        self.change("fullcore-bytes-02.json",lambda v:v.update(os_monotonic_capacity_measured=True));self.refused()
    def test_recorded_peak_cannot_be_relabelled_three(self):
        self.change("fullcore-pack-02.json",lambda v:v.update(recorded_peak_overlapping_intervals=3));self.refused()
    def test_original_failure_exit_must_remain_one(self):
        self.change("fullcore-physical-01.command.json",lambda v:v.update(exit_code=0));self.refused()
    def test_original_failure_state_cannot_be_pass(self):
        self.change("postprocess-01/state.json",lambda v:v.update(status="PASS"));self.refused()
    def test_proof_exact_anomaly_not_tolerance(self):
        b=copy.deepcopy(self.binding);b["source_bound_capacity_proof"]["exact_anomaly"]["microseconds"]=80120
        with self.assertRaises(e.GateError):e.validate_limited_proof(b,self.case)
    def test_proof_no_timestamp_rewrite(self):
        b=copy.deepcopy(self.binding);b["source_bound_capacity_proof"]["timestamps_modified"]=True
        with self.assertRaises(e.GateError):e.validate_limited_proof(b,self.case)
    def test_proof_requires_exact_71_inputs(self):
        b=copy.deepcopy(self.binding);b["source_bound_capacity_proof"]["evidence_inputs"].pop(next(iter(self.case["files"])))
        with self.assertRaises(e.GateError):e.validate_limited_proof(b,self.case)
    def test_proof_cannot_grant_raw_semantics(self):
        b=copy.deepcopy(self.binding);b["source_bound_capacity_proof"]["semantic_raw_audit_granted"]=True
        with self.assertRaises(e.GateError):e.validate_limited_proof(b,self.case)
    def test_runtime_closure_drift(self):
        p=self.work/"reviews/clean-fullcore-audit-v2/capacity_proof.py";p.write_text("changed")
        self.refused()
    def test_review_wrong_failure_binding(self):
        ready,rp=self.approval();v=e.read(rp);v["failed_attempts"]={};put(rp,v)
        with self.assertRaises(e.GateError),patch.object(e,"review_marker",return_value=self.marker):
            e.validate_review(self.plan,self.planpath,rp,ready,"import")
        self.assertFalse(self.output.exists())

if __name__=="__main__":
    unittest.main()
