"""Finish fixed read-only audit and identity check, preserving the failed pipeline."""
from pathlib import Path
import importlib.util,json,hashlib,sys,os,time
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026");D=W/"reviews/config-reuse"
O=W/"config-reuse-clean02-02";FIX=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open("x") as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write("\n")
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    review=read(sys.argv[1]);assert review["approved"] is True and review["driver_sha256"]==sha(__file__)
    def check():
        assert all(sha(path)==digest for path,digest in review["pins"].items())
    check();assert not (O/"completion-02.json").exists() and not (O/"audit-02.json").exists()
    assert read(O/"state.json")["status"]=="FAILED"
    assert read(O/"state.json")["error"]=="ValueError('stage failed audit')"
    assert read(O/"audit-01.command.json")["exit_code"]==1
    assert "physical clean identity changed during audit" in (O/"audit-01.command.stderr.log").read_text()
    assert read(O/"run-01/state.json")["status"] in ["PERFORMANCE_CANDIDATE","REJECT","INCONCLUSIVE"]
    assert read(D/"audit-scope-tests-01.command.json")["exit_code"]==0
    os.environ["GIT_OPTIONAL_LOCKS"]="0"
    ex=load("fixed_audit_completion_executor",D/"execute_clean02_stage_v3.py")
    plan=read(D/"clean02-launch-plan-v4.json");ready=ex.gate_metadata(plan)
    assert ready==read(D/"actual-clean-readiness-01.json")
    ex.source_inputs(plan,imported=True);before=ex.capture_identity(plan)
    assert before==read(O/"identity-before.json")
    started=datetime.now(timezone.utc).isoformat();mono=time.monotonic_ns()
    sys.path.insert(0,str(D/"adapter-v3"));import probe
    fixed=load("fixed_raw_audit",FIX/"raw_audit_fixed.py")
    p=probe.Probe(W/"clean-02/checkout/source",W/"clean-02/identity/current.json",
        W/"clean-02/matrix-build-01",W/"clean-02/matrix-run-01")
    result=fixed.audit_probe(p,O/"build-01",O/"run-01")
    assert result["status"]=="PROBE_LOCAL_RAW_AUDIT_PASS"
    save(O/"audit-02.json",result)
    after=ex.capture_identity(plan);assert after==before
    ex.source_inputs(plan,imported=True);check()
    assert ex.gate_metadata(plan)==ready
    save(O/"identity-after-02.json",after)
    value=dict(status="PROBE_V3_RUNTIME_AND_FIXED_READONLY_AUDIT_PASS",performance_decision=result["performance"]["decision"],
      new_emu_runs=0,selected_actual_target_processes=5,actual_total_target_processes_including_V2=7,
      audit=dict(path=str(O/"audit-02.json"),sha256=sha(O/"audit-02.json")),
      fixed_auditor=dict(path=str(FIX/"raw_audit_fixed.py"),sha256=sha(FIX/"raw_audit_fixed.py")),
      preserved_failed_audit=dict(path=str(O/"audit-01.command.json"),sha256=sha(O/"audit-01.command.json")),
      preserved_failed_pipeline=dict(path=str(O/"state.json"),sha256=sha(O/"state.json")),
      identity_before_sha256=sha(O/"identity-before.json"),identity_after_sha256=sha(O/"identity-after-02.json"),
      physical_identity_unchanged=True,tracked_source_and_index_unchanged=True,
      started=started,finished=datetime.now(timezone.utc).isoformat(),started_monotonic_ns=mono,finished_monotonic_ns=time.monotonic_ns(),
      host_time_limit_inherited_from_clean_fullcore=ready["fullcore_capacity_qualification"],
      default_changed=False,production_RTL_changed=False,github_pushed=False)
    save(O/"completion-02.json",value);print(json.dumps({k:value[k] for k in ["status","performance_decision","new_emu_runs"]}))
if __name__=="__main__":main()
