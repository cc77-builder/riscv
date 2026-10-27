#!/usr/bin/env python3
"""Bounded R3 elaboration, actual generated-RTL proof and fixed FU screen.

Mapping, STA and FU tests use the existing team tools unchanged. This driver
never modifies production inputs and requires new outputs outside them.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

CONTRACT = "r3-vdot-csa-reduce-v1"
SOURCE = "src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala"
PINS = {
    "baseline": "161df70403fd131a3adf445230ed637dc7ad7c619d05c0a890aa8aa1791546d8",
    "candidate": "c9dc1fa8d89e22cf67f756c89f5a81b65ca0568312473461e199d152616adc30",
}


def require(ok, why):
    if not ok:
        raise ValueError(why)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, value):
    Path(p).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def read(p):
    return json.loads(Path(p).read_text())


def now():
    return datetime.now(timezone.utc).isoformat()


def fresh(out, inputs):
    out = out.resolve()
    require(not out.exists(), "output must be new")
    require(not any(out == p.resolve() or p.resolve() in out.parents for p in inputs),
            "output must be outside inputs")
    out.mkdir(parents=True)
    return out


def command(args, cwd, env, out, label, timeout):
    args = list(map(str, args))
    receipt = dict(command=args, cwd=str(cwd), started=now(), timeout_seconds=timeout)
    save(out / (label + ".command.json"), receipt)
    with (out / (label + ".log")).open("wb") as log:
        p = subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                             start_new_session=(os.name == "posix"))
        def cleanup():
            if os.name == "posix":
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(p.pid, sig)
                    except ProcessLookupError:
                        break
                    if sig == signal.SIGTERM:
                        time.sleep(0.2)
                receipt["owned_process_group_cleanup"] = True
            elif p.poll() is None:
                p.kill()
            p.wait()
        receipt.update(pid=p.pid, process_started=True)
        save(out / (label + ".command.json"), receipt)
        try:
            code = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            cleanup()
            receipt["timed_out"] = True
            code = 124
        except BaseException:
            cleanup()
            receipt.update(interrupted=True, exit_code=p.returncode, finished=now())
            save(out / (label + ".command.json"), receipt)
            raise
        if code:
            cleanup()
    receipt.update(exit_code=code, finished=now(), log_sha256=sha(out / (label + ".log")))
    save(out / (label + ".command.json"), receipt)
    return receipt


def snapshot(repo):
    scopes = ["build.sc", "src", "team/scripts/activate.sh",
              "team/optimizations/o4/GenerateVDotCost.scala",
              "team/optimizations/o4/reduce/CONTRACT.md", "team/optimizations/o4/reduce/candidate.patch",
              "team/optimizations/o4/reduce/experiment.py"]
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others",
                                   "--exclude-standard", "--", *scopes], cwd=repo)
    files = {n.decode(): sha(repo / n.decode()) for n in raw.split(b"\0")
             if n and (repo / n.decode()).is_file()}
    dependencies = []

    def walk(root, prefix=""):
        tree = subprocess.check_output(["git", "ls-tree", "-rz", "HEAD"], cwd=root)
        for entry in filter(None, tree.split(b"\0")):
            meta, name = entry.split(b"\t", 1)
            mode, _, pin = meta.decode().split()
            if mode != "160000":
                continue
            name = name.decode()
            child = root / name
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=child, text=True).strip()
            status = subprocess.check_output(["git", "status", "--porcelain=v1",
                                               "--untracked-files=normal"], cwd=child, text=True)
            require(head == pin and not status, "dirty/unpinned dependency " + prefix + name)
            dependencies.append(dict(path=prefix + name, pin=pin))
            walk(child, prefix + name + "/")

    walk(repo)
    return dict(files=files, dependencies=dependencies)


def elaborate(a):
    repo = a.repo.resolve()
    out = fresh(a.output, [repo])
    result = dict(contract=CONTRACT, variant=a.variant, mode="o2", boundary=a.boundary, source_root=str(repo),
                  started=now(), exit_code=1)
    try:
        require(sha(repo / SOURCE) == PINS[a.variant], "production source pin mismatch")
        changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=repo, text=True).splitlines()
        require(changed == ([] if a.variant == "baseline" else [SOURCE]), "unexpected tracked source changes")
        require(not subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "--", "src", "build.sc"], cwd=repo), "untracked production sources")
        before = snapshot(repo)
        save(out / "source.json", before)
        result["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        (out / "source-status.txt").write_bytes(subprocess.check_output(["git", "status", "--short"], cwd=repo))
        (out / "working-tree.patch").write_bytes(subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=repo))
        raw = subprocess.check_output(["bash", "-c", "source team/scripts/activate.sh >/dev/null; env -0"], cwd=repo)
        env = dict(item.decode().split("=", 1) for item in raw.split(b"\0") if item)
        flags = dict(VDOT_T14_FUSED_INPUT="1", VDOT_O1_HANDOFF="0", VDOT_O2_ELASTIC="1",
                     VDOT_T12_TRACE="0", VDOT_T13_TRACE="0", VDOT_O1_TRACE="0", VDOT_O2_TRACE="0")
        env.update(flags)
        selected = {k: env[k] for k in ("JAVA_HOME", "JAVA_OPTS", "JAVA_TOOL_OPTIONS",
                    "CHISEL_FIRTOOL_PATH", "PATH") if k in env}
        result.update(flags=flags, environment=selected, source_sha256=sha(out / "source.json"),
                      affinity=sorted(os.sched_getaffinity(0)))
        tools = {"java": ["java", "-version"], "mill": ["mill", "--version"],
                 "firtool": [str(Path(env["CHISEL_FIRTOOL_PATH"]) / "firtool"), "--version"]}
        for name, argv in tools.items():
            r = command(argv, repo, env, out, name + "-version", 90)
            require(r["exit_code"] == 0, name + " version failed")
        argv = ["mill", "-i", "-j", "2", "vdotCost.runMain", "team.vdot.GenerateVDotCost",
                a.boundary, out / "rtl"]
        result["command"] = list(map(str, argv))
        r = command(argv, repo, env, out, "generate", 1800)
        result["exit_code"] = r["exit_code"]
        require(r["exit_code"] == 0, "Chisel generation failed")
        require(snapshot(repo) == before, "sources/dependencies changed during generation")
        rtl = sorted(p for p in (out / "rtl").rglob("*") if p.is_file())
        require(rtl and any(p.name == "VDotReduce.sv" for p in rtl), "missing actual reduction RTL")
        result["rtl"] = {p.relative_to(out).as_posix(): dict(sha256=sha(p), bytes=p.stat().st_size) for p in rtl}
        result["source_unchanged"] = True
    except Exception as exc:
        result.update(exit_code=1, error=repr(exc))
        raise
    finally:
        result["finished"] = now()
        save(out / "result.json", result)
    return dict(status="R3_ELABORATION_PASS", variant=a.variant, files=len(result["rtl"]))


def generated(root, variant):
    r = read(root / "result.json")
    require(r["exit_code"] == 0 and r["variant"] == variant and r["source_unchanged"], "generation identity")
    for name, item in r["rtl"].items():
        require(sha(root / name) == item["sha256"], "generated RTL changed")
    candidates = list((root / "rtl").rglob("VDotReduce.sv"))
    require(len(candidates) == 1, "ambiguous reduction module")
    return candidates[0]


def formal(a):
    base, candidate = a.baseline.resolve(), a.candidate.resolve()
    roots = [Path(read(p / "result.json")["source_root"]) for p in (base, candidate)]
    out = fresh(a.output, [base, candidate, *roots])
    gold, gate = generated(base, "baseline"), generated(candidate, "candidate")
    result = dict(contract=CONTRACT, status="RUNNING", input_bits=128, output_bits=128,
                  baseline_rtl_sha256=sha(gold), candidate_rtl_sha256=sha(gate), started=now())
    save(out / "result.json", result)
    scripts = []
    try:
        # A wrapper changes only the high output bit on a disposable copy. This
        # proves the same miter observes all 128 bits, not only arithmetic bits.
        body, count = re.subn(r"\bmodule\s+VDotReduce\s*\(", "module VDotReduceCore(", gate.read_text(), count=1)
        require(count == 1, "generated module declaration not found")
        ports = ", ".join("input [15:0] io_products_" + str(i) for i in range(8))
        wires = ", ".join(".io_products_%d(io_products_%d)" % (i, i) for i in range(8))
        body += "\nmodule VDotReduce(" + ports + ", output [127:0] io_result);\n"
        body += "wire [127:0] value; VDotReduceCore dut(" + wires + ", .io_result(value));\n"
        body += "assign io_result = value ^ (128'h1 << 100);\nendmodule\n"
        negative = out / "negative-bit100.sv"
        negative.write_text(body)
        for label, rtl, expected in (("equivalence", gate, 0), ("negative-bit100", negative, 1)):
            script = out / (label + ".ys")
            script.write_text("\n".join([
                f"read_verilog -sv -DSYNTHESIS {gold}", "rename VDotReduce gold",
                f"read_verilog -sv -DSYNTHESIS {rtl}", "rename VDotReduce gate",
                "miter -equiv -make_assert -flatten gold gate miter", "prep -top miter",
                f"write_json {out / (label + '-miter.json')}",
                "sat -verify -prove-asserts -set-def-inputs -show-inputs -show-outputs -timeout 300",
            ]) + "\n")
            receipt = command([a.yosys, "-T", "-s", script], out, os.environ.copy(), out, label, 330)
            log = (out / (label + ".log")).read_text()
            require(receipt["exit_code"] == expected, label + " unexpected process result")
            marker = "SAT proof finished - no model found: SUCCESS!" if expected == 0 else "proof did fail"
            require(marker in log, label + " missing decisive proof result")
            scripts.append(dict(label=label, script_sha256=sha(script), log_sha256=sha(out / (label + ".log")), exit_code=expected))
        result.update(status="R3_GENERATED_REDUCTION_EQUIVALENCE_PASS", proofs=scripts,
                      negative_control="actual candidate output bit100 flip rejected")
    except Exception as exc:
        result.update(status="FAILED", error=repr(exc), proofs=scripts)
        raise
    finally:
        result["finished"] = now()
        save(out / "result.json", result)
    return result


def compare(a):
    out = a.output.resolve()
    require(not out.exists(), "comparison output must be new")
    require(not any(p.resolve() == out or p.resolve() in out.parents for p in
                    (a.baseline, a.candidate, a.baseline_sta, a.candidate_sta, a.formal, a.fu_test)),
            "comparison output must be outside inputs")
    bm, cm = read(a.baseline / "summary.json"), read(a.candidate / "summary.json")
    bt, ct = read(a.baseline_sta / "summary.json"), read(a.candidate_sta / "summary.json")
    proof, fu = read(a.formal / "result.json"), read(a.fu_test / "runner.status.json")
    require(all(r["pass"] for r in (bm, cm, bt, ct)), "incomplete mapping/STA")
    require(all(math.isfinite(m["cell_area_sum"]) and m["cell_area_sum"] > 0 for m in (bm, cm)), "invalid cell area")
    require(bm["boundary"] == cm["boundary"] == "fu" and bm["mode"] == cm["mode"] == "o2", "wrong comparison boundary")
    require(bm["ports"] == cm["ports"] and bm["library_sha256"] == cm["library_sha256"], "unfair interface/library")
    require(proof["status"] == "R3_GENERATED_REDUCTION_EQUIVALENCE_PASS" and fu["passed"] and fu["stage"] == "fu", "correctness gate not passed")
    require(read(a.fu_test / "source.json")[SOURCE] == PINS["candidate"], "FU test is not this candidate")
    source_snapshots, generation_records = [], []
    for variant, mapping_path, mapping, timing in (("baseline", a.baseline, bm, bt),
                                                  ("candidate", a.candidate, cm, ct)):
        generation = Path(mapping["generation"])
        require(out != generation and generation not in out.parents and
                Path(read(generation / "result.json")["source_root"]).resolve() not in out.parents,
                "comparison output is inside generation/source inputs")
        rtl = generated(generation, variant)
        require(mapping["generation_sha256"] == sha(generation / "result.json"), "mapping generation receipt changed")
        require(read(generation / "source.json")["files"][SOURCE] == PINS[variant], "generation source differs")
        source_snapshots.append(read(generation / "source.json"))
        generation_records.append(read(generation / "result.json"))
        require(proof[variant + "_rtl_sha256"] == sha(rtl), "proof uses another generated reduction")
        require(mapping["mapped_sha256"] == sha(mapping_path / "mapped.v") and
                mapping["mapped_json_sha256"] == sha(mapping_path / "mapped.json"), "mapped artifacts changed")
        require(timing["mapping_summary_sha256"] == sha(mapping_path / "summary.json") and
                timing["mapped_sha256"] == mapping["mapped_sha256"] and
                timing["library_sha256"] == mapping["library_sha256"], "STA mapping/library differs")
    bs, cs = source_snapshots
    require(bs["dependencies"] == cs["dependencies"] and set(bs["files"]) == set(cs["files"]), "AB source/dependency scope differs")
    require([n for n in bs["files"] if bs["files"][n] != cs["files"][n]] == [SOURCE], "AB changes more than the pinned reduction")
    bg, cg = generation_records
    require(all(bg[k] == cg[k] for k in ("flags", "environment", "source_commit", "boundary", "mode")), "AB generation conditions differ")
    ff = lambda m: sum(v for k, v in m["cell_histogram"].items() if k.startswith("DFF"))
    require(ff(bm) == ff(cm), "sequential state changed")
    require(bt["wire_load_model"] == ct["wire_load_model"], "wire-load mismatch")
    profiles = [("nominal", 1.0, 5), ("period050", 0.5, 5), ("period200", 2.0, 5),
                ("load001", 1.0, 1), ("load020", 1.0, 20)]
    path_names = {"r2r", "i2r", "r2o", "i2o", "ready"}
    for timing in (bt, ct):
        require([(p["profile"], p["period_ns"], p["load_ff"]) for p in timing["profiles"]] == profiles, "fixed profile coverage differs")
        for profile in timing["profiles"]:
            require(set(profile["paths"]) == path_names, "fixed path coverage differs")
            require(all(v["exists"] and math.isfinite(v["arrival_ns"]) and v["arrival_ns"] > 0
                        for v in profile["paths"].values()), "invalid path arrival")
    reasons, rows = [], []
    for bp, cp in zip(bt["profiles"], ct["profiles"]):
        require((bp["period_ns"], bp["load_ff"]) == (cp["period_ns"], cp["load_ff"]), "constraint mismatch")
        require(set(bp["paths"]) == set(cp["paths"]), "path scope mismatch")
        for name, b in bp["paths"].items():
            c = cp["paths"][name]
            require(b["exists"] and c["exists"], "missing required path")
            change = c["arrival_ns"] / b["arrival_ns"] - 1
            rows.append(dict(profile=bp["profile"], path=name, baseline=b, candidate=c, fractional_change=change))
            if name != "r2r" and change > 0.01 + 1e-9:
                reasons.append(bp["profile"] + "/" + name + " regresses over 1%")
            if bp["profile"] == "nominal" and name == "r2r" and change > -0.10 + 1e-9:
                reasons.append("nominal r2r improvement below 10%")
    if cm["cell_area_sum"] > bm["cell_area_sum"] + 1e-6:
        reasons.append("complete FU cell area increases")
    result = dict(contract=CONTRACT, status="R3_FU_SCREEN_COMPLETE", decision="STOP_SCREEN" if reasons else "NUMERIC_GATE_PASS_REQUIRES_PATH_REVIEW",
                  reasons=reasons, baseline_area=bm["cell_area_sum"], candidate_area=cm["cell_area_sum"],
                  dffs=ff(bm), ports=bm["ports"], paths=rows, source_proof=sha(a.formal / "result.json"),
                  fu_result_sha256=sha(a.fu_test / "runner.status.json"),
                  whole_core_frequency_or_application_claim=False)
    save(out, result)
    return {k: result[k] for k in ("status", "decision", "reasons", "baseline_area", "candidate_area", "dffs")}


def main():
    if os.name == "posix":
        def stop(signum, frame):
            raise InterruptedError("termination signal " + str(signum))
        signal.signal(signal.SIGTERM, stop)
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    el = sub.add_parser("elaborate")
    el.add_argument("--repo", type=Path, required=True)
    el.add_argument("--variant", choices=tuple(PINS), required=True)
    el.add_argument("--boundary", choices=("fu", "parent"), default="fu")
    el.add_argument("--output", type=Path, required=True)
    fo = sub.add_parser("formal")
    fo.add_argument("--baseline", type=Path, required=True)
    fo.add_argument("--candidate", type=Path, required=True)
    fo.add_argument("--output", type=Path, required=True)
    fo.add_argument("--yosys", type=Path, default=Path("/usr/bin/yosys"))
    co = sub.add_parser("compare")
    for name in ("baseline", "candidate", "baseline-sta", "candidate-sta", "formal", "fu-test", "output"):
        co.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(dict(elaborate=elaborate, formal=formal, compare=compare)[a.action](a), indent=2))


if __name__ == "__main__":
    main()
