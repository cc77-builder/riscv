"""Bounded 13 reused + 1 new fullcore acceptance; never repairs old campaign."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

REPLACEMENT = "o2-control-diagnostic"
SPAWN_FIELDS = ("name", "started", "command", "files", "negative_target", "cwd",
 "auxiliary_files", "environment_overrides", "process_started", "pid", "pid_kind",
 "actual_new_execution", "performance_measured", "exit_code", "timed_out", "terminated_returncode")

def require(value, message):
    if not value:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def save(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(path)

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def stamp():
    return dict(utc=now(), monotonic_ns=time.monotonic_ns(),
                boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip())

def capacity(rows, limit):
    events = []
    require(len({r["name"] for r in rows}) == len(rows), "duplicate process name")
    for row in rows:
        start, end = [dt.datetime.fromisoformat(row[k]) for k in ("started", "finished")]
        require(start.tzinfo is not None and end.tzinfo is not None and start < end, "bad UTC interval")
        events.extend([(start, 1, row["name"]), (end, -1, row["name"])])
    active, peak, violations = set(), 0, []
    for instant, kind, name in sorted(events):
        if kind == 1:
            active.add(name)
            peak = max(peak, len(active))
            if len(active) > limit:
                violations.append(dict(at=instant.isoformat(), active=sorted(active)))
        else:
            active.remove(name)
    return dict(status="PASS" if peak <= limit else "FAIL", limit=limit, peak=peak, violations=violations)

def binding(runtime, result):
    require(all(runtime.get(k) == result.get(k) and type(runtime.get(k)) is type(result.get(k))
                for k in SPAWN_FIELDS), "spawn/result binding")
    require(result.get("process_started") is True and type(result.get("pid")) is int and result["pid"] > 0
            and type(result.get("exit_code")) is int and result.get("timed_out") is False
            and result.get("terminated_returncode") is None
            and result.get("actual_new_execution") is True
            and result.get("performance_measured") is False, "invalid process receipt")

def clock_check(clock, raw):
    require(clock["pid"] == raw["pid"] and type(clock["pid"]) is int and clock["pid"] > 0, "clock PID differs")
    stamps = [clock[k] for k in ("before_popen", "after_popen", "before_wait", "after_wait")]
    require(len({s["boot_id"] for s in stamps}) == 1 and bool(stamps[0]["boot_id"]), "boot changed")
    values = [s["monotonic_ns"] for s in stamps]
    require(all(type(v) is int and v > 0 for v in values) and values == sorted(values)
            and values[-1] > values[0], "bad monotonic order")
    require(clock["command"] == raw["command"] and clock["cwd"] == raw["cwd"]
            and clock["exit_code"] == raw["exit_code"] and clock["raw_logs_sha256"] == raw["raw_logs_sha256"],
            "clock execution binding")
    utc = [dt.datetime.fromisoformat(s["utc"]) for s in stamps]
    require(all(v.tzinfo is not None for v in utc), "naive clock UTC")
    # UTC anomalies are reported, never hidden; monotonic envelopes remain authoritative for new phase.
    return dict(status="PASS", process_envelope_seconds=(values[-1]-values[0])/1e9,
                monotonic_peak=1, utc_nondecreasing=utc == sorted(utc),
                utc_minus_monotonic_seconds=(utc[-1]-utc[0]).total_seconds()-(values[-1]-values[0])/1e9)

def run(args):
    out, old, source = args.output.resolve(), args.old.resolve(), args.source.resolve()
    require(not out.exists(), "fresh output required")
    out.mkdir(parents=True)
    state = dict(status="PREFLIGHT", started=now(), operation_id="20261027-r5-g5-clock-supplement-01",
                 new_emu_runs=0, selected_old_runs=13, performance_measured=False,
                 controller_sha256=sha(__file__), contract_sha256=sha(Path(__file__).with_name("CONTRACT.md")))
    save(out/"state.json", state)
    try:
        sys.path.insert(0, str(args.adapter.resolve()))
        import current_clean_fullcore as adapter
        identity = read(args.identity)
        fc = adapter.configure(source, identity)
        ctx = fc.bind(source, identity, physical=True)
        fc.prepare(ctx, None, old/"negative-fixture")
        require(ctx.inputs == read(old/"runtime-inputs.json"), "original input closure differs")
        fc.ce.a.frozen_m.verify_files(ctx.inputs)
        save(out/"runtime-inputs.json", ctx.inputs)
        save(out/"identity.json", identity)
        old_state = read(old/"state.json")
        require(old_state["status"] == adapter.PASS and old_state["new_emu_runs"] == 14
                and old_state["new_emu_launch_attempts"] == 14 and not old_state["active"]
                and old_state["controller_sha256"] == sha(args.adapter/"current_clean_fullcore.py")
                and old_state["identity_sha256"] == sha(args.identity), "original campaign identity")
        require({p.name for p in (old/"runs").iterdir()} == fc.CORE | fc.SUPPLEMENTS, "original inventory")
        old_raw = {n: read(old/"runs"/n/"result.json") for n in ctx.jobs}
        require(read(old/"completed-runs.json") == sorted(old_raw.values(), key=lambda x:x["name"]), "original completed inventory")
        all_proof = capacity(list(old_raw.values()), old_state["jobs"])
        selected = [row for name,row in old_raw.items() if name != REPLACEMENT]
        selected_proof = capacity(selected, old_state["jobs"])
        require(all_proof["status"] == "FAIL" and all_proof["peak"] == 4, "expected old audit history differs")
        require(selected_proof["status"] == "PASS" and len(selected) == 13, "selected original capacity")
        save(out/"original-wall-clock.json", dict(original14=all_proof, selected13=selected_proof,
              original_campaign_status="WALL_CLOCK_LIMITED", original_not_repaired=True))
        audit = out/"old-rechecks"; audit.mkdir()
        rows, raws, origins = [], [], {}
        start,end = [dt.datetime.fromisoformat(old_state[k]) for k in ("started","finished")]
        for name,image,data,reference in ctx.jobs.values():
            if name == REPLACEMENT:
                continue
            raw = old_raw[name]
            binding(read(old/"runs"/name/"runtime.json"), raw)
            require(start <= dt.datetime.fromisoformat(raw["started"]) < dt.datetime.fromisoformat(raw["finished"]) <= end,
                    "old outside controller lifetime")
            row = fc.evaluate(ctx,name,image,data,reference,raw,old/"runs",audit)
            require(all(row.get(k) == raw.get(k) for k in fc.SEMANTIC if k in row), "original semantic drift")
            rows.append(row); raws.append(raw)
            origins[name] = dict(kind="REUSED_RAW_RECHECKED", path=str(old/"runs"/name),
                                 result_sha256=sha(old/"runs"/name/"result.json"))
        save(out/"original-rechecks.json", rows)
        state.update(status="OLD13_RECHECK_PASS"); save(out/"state.json",state)
        name,image,data,reference = ctx.jobs[REPLACEMENT]
        campaign = out/"runs"; directory = campaign/name; cwd = directory/"cwd"
        (cwd/"build").mkdir(parents=True)
        for filename,digest in fc.p.AUX.items():
            shutil.copyfile(Path(ctx.cfg["hardware_source"])/"build"/filename,cwd/"build"/filename)
            require(sha(cwd/"build"/filename)==digest,"auxiliary drift")
        raw = dict(name=name,status="RUNNING",started=now(),command=fc.command(ctx,image,reference),cwd=str(cwd),
                   files={str(path):sha(path) for path in (ctx.args.emu,ctx.paths["reference"],reference,ctx.paths["flash"],image)},
                   negative_target=None,auxiliary_files=fc.p.AUX,environment_overrides={"XS_NEGATIVE_VECTOR_TARGET":None},
                   process_started=False,pid_kind="timeout process-group leader",actual_new_execution=True,
                   performance_measured=False,timed_out=False,terminated_returncode=None)
        require(dt.datetime.fromisoformat(raw["started"]) > end, "new phase not after old completed batch")
        save(directory/"runtime.json",raw)
        clock = dict(command=raw["command"],cwd=str(cwd),before_popen=stamp())
        env = dict(os.environ); env.pop("XS_NEGATIVE_VECTOR_TARGET",None)
        with (directory/"stdout.log").open("wb") as stdout, (directory/"stderr.log").open("wb") as stderr:
            proc = subprocess.Popen(raw["command"],cwd=cwd,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
            clock.update(after_popen=stamp(),pid=proc.pid)
            raw.update(pid=proc.pid,process_started=True)
            save(directory/"runtime.json",raw)
            state.update(status="RUNNING_SUPPLEMENT",new_emu_runs=1,pid=proc.pid)
            save(out/"state.json",state)
            clock["before_wait"] = stamp(); save(directory/"clock.json",clock)
            try:
                raw["exit_code"] = proc.wait(timeout=7210)
            except subprocess.TimeoutExpired:
                raw["timed_out"] = True
                os.killpg(proc.pid,signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL); proc.wait()
                raw.update(exit_code=124,terminated_returncode=proc.returncode)
            clock["after_wait"] = stamp()
        raw["finished"] = now()
        (directory/"run.log").write_bytes((directory/"stderr.log").read_bytes()+(directory/"stdout.log").read_bytes())
        raw["raw_logs_sha256"]={n:sha(directory/n) for n in ctx.r.RAW_NAMES}
        raw["raw_sha256"]=dict(raw["raw_logs_sha256"])
        (directory/"exit-code.txt").write_text(str(raw["exit_code"])+"\n")
        raw["status"]="RAW_EMU_EXITED_AWAITING_RECHECK"
        clock.update(exit_code=raw["exit_code"],raw_logs_sha256=raw["raw_logs_sha256"])
        save(directory/"clock.json",clock); save(directory/"runtime.json",raw); save(directory/"result.json",raw)
        binding(read(directory/"runtime.json"),raw)
        require(raw["exit_code"] == 0 and not raw["timed_out"], "supplement process failed")
        clock_result = clock_check(clock,raw); save(out/"clock-audit.json",clock_result)
        audit = out/"new-rechecks"; audit.mkdir()
        row = fc.evaluate(ctx,name,image,data,reference,raw,campaign,audit)
        for key in fc.SEMANTIC:
            if key in row: raw[key]=row[key]
        save(directory/"result.json",raw)
        rows.append(row); raws.append(raw)
        origins[name]=dict(kind="NEW_EXECUTION",path=str(directory),result_sha256=sha(directory/"result.json"))
        # Frozen aggregation asserts architectural coverage and negative->same-image recovery.
        # Its original "14 fresh" counters do not describe this composite and are replaced explicitly.
        result = fc.aggregate(ctx,rows,raws)
        result.update(status="R5_G5_COMPOSITE_FULLCORE_PASS",contract="r5-g5-selected-candidate-v1",
                      new_emu_runs=1,reused_execution_verdicts=13,reused_raw_logs_reparsed=13,
                      fresh_14_campaign=False,origins=origins,old_campaign_clock_status="WALL_CLOCK_LIMITED",
                      selected_utc_capacity=capacity(raws,3),new_phase_clock=clock_result,
                      started=state["started"],finished=now())
        require(result["selected_utc_capacity"]["status"] == "PASS", "composite UTC capacity")
        fc.ce.a.frozen_m.verify_files(ctx.inputs)
        _,profile=fc.p.hardware_profile(source,ctx.cfg)
        require(profile==identity["hardware_profile"],"post hardware drift")
        save(out/"results.json",result)
        state.update(status=result["status"],finished=now(),active={})
        save(out/"state.json",state)
        print(json.dumps({k:v for k,v in result.items() if k not in ("records","origins")},indent=2))
    except BaseException as exc:
        state.update(status="FAILED",error=repr(exc),finished=now()); save(out/"state.json",state)
        raise

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    for key in ("source","adapter","identity","old","output"):
        parser.add_argument("--"+key,type=Path,required=True)
    run(parser.parse_args())
