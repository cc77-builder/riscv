"""Read-only audit of completed C1 receipts and raw STA reports; no EDA reruns."""
import argparse, hashlib, json, re, datetime
from pathlib import Path

PROFILES = ["nominal", "period050", "period200", "load001", "load020"]
KINDS = ["r2r", "i2r", "vdot_r2r", "vdot_i2r", "vdot_r2o", "ready"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def need(ok, message):
    if not ok:
        raise ValueError(message)

def parsed(path):
    text = path.read_text()
    def number(pattern):
        match = re.search(pattern, text)
        need(match is not None, "missing timing field " + str(path))
        return float(match[1])
    return dict(arrival_ns=number(r"([-0-9.]+)\s+data arrival time"),
                slack_ns=number(r"([-0-9.]+)\s+slack \("),
                startpoint=re.search(r"Startpoint: ([^\n]+)", text)[1],
                endpoint=re.search(r"Endpoint: ([^\n]+)", text)[1])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    need(not a.output.exists(), "new output required")
    read = lambda root, name: json.loads((root / name).read_text())
    campaign = read(a.work, "campaign-02.json")
    need(campaign["status"] == "LOCAL_AND_STANDARD_PPA_COMPLETE_AWAIT_SCREEN", "campaign incomplete")
    need(all(x["status"] == "passed" and x["exit_code"] == 0 for x in campaign["steps"]), "campaign failed")
    screen = a.work / "screen-01"
    result = read(screen, "result.json")
    state = read(screen, "state.json")
    need(len(state["steps"]) == 10 and all(x["exit_code"] == 0 for x in state["steps"]), "targeted STA incomplete")
    pins_count = {}
    for filename in ["inputs-02.json", "screen-01/inputs.json"]:
        pins = read(a.work, filename)
        for path, digest in pins.items():
            need(sha(Path(path)) == digest, "input changed: " + path)
        pins_count[filename] = len(pins)
    need(read(a.work, "state-proof.json")["status"] == "C1_ABSTRACT_STATE_EQUIVALENCE_PASS", "abstract state")
    replay = read(a.work, "state-trace-replay.json")
    need(replay["status"] == "C1_REAL_PARENT_STATE_REPLAY_PASS", "state replay")
    need(sha(a.work/"parent-01/result.log") == replay["baseline_log_sha256"] == replay["candidate_log_sha256"], "observations differ")
    negative_counts = {}
    for stage, expected in [("fu-02", 4), ("parent-01", 16)]:
        need(read(a.work, stage+"/runner.status.json")["passed"], "local runner")
        cmds = read(a.work, stage+"/commands.json")
        bad = [x for x in cmds if x["exit_code"] != 0]
        need(len(bad) == expected and all(x["exit_code"] == 1 and x["log"].startswith("inject-") for x in bad), "unexpected exit")
        for x in bad:
            checker = [c for c in cmds if c["log"] == x["log"].replace("inject-", "check-")]
            need(len(checker) == 1 and checker[0]["exit_code"] == 0, "negative checker")
        negative_counts[stage] = len(bad)
    mapping = {k: read(root, "parent-map-01/summary.json") for k, root in [("before", a.baseline), ("after", a.work)]}
    timing = {k: read(root, "parent-sta-01/summary.json") for k, root in [("before", a.baseline), ("after", a.work)]}
    need(mapping["before"]["ports"] == mapping["after"]["ports"], "port boundary")
    need(mapping["before"]["library_sha256"] == mapping["after"]["library_sha256"], "library")
    need(not mapping["after"]["unknown_cells"], "unknown cells")
    ordinary = {}; targeted = {}; report_count = 0
    for version, root in [("before", a.baseline), ("after", a.work)]:
        need(mapping[version]["pass"] and timing[version]["pass"], "tool receipt")
        need([x["profile"] for x in timing[version]["profiles"]] == PROFILES, "profile scope")
        ordinary[version] = {}; targeted[version] = {}
        for profile, summary in zip(PROFILES, timing[version]["profiles"]):
            ordinary[version][profile] = {}
            for kind in KINDS:
                value = parsed(root/"parent-sta-01"/profile/(kind+".rpt"))
                need(all(value[k] == summary["paths"][kind][k] for k in value), "ordinary summary differs")
                ordinary[version][profile][kind] = value
                report_count += 1
            queries = read(screen, version+"/"+profile+"/queries.json")
            paths = read(screen, version+"/"+profile+"/paths.json")
            standard = (root/"parent-sta-01"/profile/"timing.tcl").read_text().splitlines()
            prefix = standard[:next(i for i,x in enumerate(standard) if x.startswith("check_setup "))]
            actual = (screen/version/profile/"timing.tcl").read_text().splitlines()
            need(actual[:len(prefix)] == prefix, "targeted constraints changed")
            need(not any("false_path" in x or "multicycle_path" in x for x in actual), "timing waiver")
            targeted[version][profile] = {}
            for key, (selector, semantic) in queries.items():
                value = parsed(screen/version/profile/(key+".rpt"))
                need(all(value[k] == paths[key][k] for k in value), "targeted summary differs")
                need("/"+("D" if key.startswith("state") else "E") in selector, "wrong terminal")
                targeted[version][profile][key] = value
                report_count += 1
    fail_keys = []
    rows = []
    for profile in PROFILES:
        for kind in KINDS + ["icg0", "icg1", "icg2"]:
            source = ordinary if kind in KINDS else targeted
            b, c = source["before"][profile][kind], source["after"][profile][kind]
            ok = c["arrival_ns"] <= b["arrival_ns"]*1.01
            if kind.startswith("icg"):
                ok = ok and (b["slack_ns"] < 0 or c["slack_ns"] >= 0)
            expected = [x for x in result["comparisons"] if (x["profile"], x["path"]) == (profile, kind)]
            need(len(expected) == 1, "missing/duplicate metric")
            e = expected[0]
            need(e["pass_"] == ok and all(e["before"][k] == b[k] and e["after"][k] == c[k] for k in b), "gate differs")
            need(abs(e["delta_percent"]-(c["arrival_ns"]/b["arrival_ns"]-1)*100) < 1e-9, "delta differs")
            if not ok: fail_keys.append(profile+"/"+kind)
            rows.append(dict(profile=profile, path=kind, before=b["arrival_ns"], after=c["arrival_ns"], passed=ok))
    controls = {v:max(x["arrival_ns"] for k,x in targeted[v]["nominal"].items() if k.startswith("state")) for v in targeted}
    need(result["control_before_ns"] == controls["before"] and result["control_after_ns"] == controls["after"], "control max")
    area_ok = mapping["after"]["cell_area_sum"] <= mapping["before"]["cell_area_sum"]*1.001
    control_ok = controls["after"] <= 1.737526
    passed = not fail_keys and area_ok and control_ok
    need(result["status"] == ("C1_SCREEN_PASS" if passed else "C1_SCREEN_REJECT"), "wrong decision")
    need(result["fullcore_authorized_by_gate"] == passed, "wrong fullcore permission")
    need(len(result["comparisons"]) == 45 and len(result["failures"]) == len(fail_keys), "failure count")
    receipt = dict(status="C1_RAW_EVIDENCE_AUDIT_PASS", time=datetime.datetime.now().astimezone().isoformat(),
                   input_files_checked=pins_count, raw_reports_checked=report_count, comparisons=45,
                   negative_controls=negative_counts, failed_path_profiles=fail_keys,
                   control_before_ns=controls["before"], control_after_ns=controls["after"],
                   area_pass=area_ok, control_pass=control_ok, overall_decision=result["status"],
                   fullcore_started=False, nominal=[x for x in rows if x["profile"]=="nominal"],
                   source_sha256=sha(Path(__file__)),
                   note="Read-only receipt/raw report audit, not another hardware or netlist equivalence run.")
    a.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
