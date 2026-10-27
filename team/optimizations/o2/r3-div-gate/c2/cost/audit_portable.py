"""Portable C2 recomputation over explicitly provided, unpacked evidence roots.

This script has no subprocess or EDA invocation. The threshold self-checks are
in-memory corruptions of observations, not silicon/formal/RTL mutation testing.
"""
import argparse
import collections
import copy
import hashlib
import json
import math
import re
from pathlib import Path

PROFILES = [("nominal", 1.0, 5), ("period050", 0.5, 5),
            ("period200", 2.0, 5), ("load001", 1.0, 1), ("load020", 1.0, 20)]
PATHS = ["r2r", "i2r", "vdot_r2r", "vdot_i2r", "vdot_r2o", "ready",
         "icg0", "icg1", "icg2"]
LIB = Path("/home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib")
BASE_AREA = 284614.946
CONTROL_LIMIT = 1.737526
MAX_AREA = BASE_AREA * 1.001

def need(x, message):
    if not x:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def obj(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def path_report(path):
    raw = Path(path).read_text(encoding="utf-8")
    starts = re.findall(r"^Startpoint:\s*(.+)$", raw, re.M)
    ends = re.findall(r"^Endpoint:\s*(.+)$", raw, re.M)
    arrivals = re.findall(r"^\s*([-+\d.]+)\s+data arrival time\s*$", raw, re.M)
    slacks = re.findall(r"^\s*([-+\d.]+)\s+slack \((MET|VIOLATED)\)", raw, re.M)
    need(len(starts) == len(ends) == len(slacks) == 1 and arrivals, "invalid report " + str(path))
    a, s = float(arrivals[0]), float(slacks[0][0])
    need(math.isfinite(a) and math.isfinite(s), "nonfinite report")
    need((s >= 0) == (slacks[0][1] == "MET"), "slack sign mismatch")
    return dict(arrival_ns=a, slack_ns=s, startpoint=starts[0], endpoint=ends[0])

def classify(data):
    expected = {(p[0], k) for p in PROFILES for k in PATHS}
    keys = [(x["profile"], x["path"]) for x in data["comparisons"]]
    need(len(keys) == 45 and set(keys) == expected, "missing/duplicate profile/path")
    need(math.isfinite(data["area_after"]) and data["area_after"] > 0, "invalid area")
    need(math.isfinite(data["control_after_ns"]) and data["control_after_ns"] >= 0, "invalid control arrival")
    failures = []
    if data["area_after"] > MAX_AREA:
        failures.append("area")
    if data["control_after_ns"] > CONTROL_LIMIT:
        failures.append("control")
    decisions = []
    for x in data["comparisons"]:
        for side in ["before", "after"]:
            for k in ["arrival_ns", "slack_ns"]:
                need(math.isfinite(x[side][k]), "nonfinite path observation")
        a, b = x["after"], x["before"]
        need(b["arrival_ns"] > 0 and a["arrival_ns"] >= 0, "invalid arrival")
        ok = a["arrival_ns"] <= b["arrival_ns"] * 1.01
        if x["path"].startswith("icg") and b["slack_ns"] >= 0:
            ok = ok and a["slack_ns"] >= 0
        decisions.append(ok)
        if not ok:
            failures.append(x["profile"] + "/" + x["path"])
    return dict(pass_=not failures, failures=failures, path_pass=decisions)

def self_check():
    good = dict(area_after=BASE_AREA, control_after_ns=CONTROL_LIMIT,
                comparisons=[dict(profile=p[0], path=k,
                             before=dict(arrival_ns=1.0, slack_ns=.1),
                             after=dict(arrival_ns=1.0, slack_ns=.1))
                             for p in PROFILES for k in PATHS])
    need(classify(good)["pass_"], "valid threshold fixture rejected")
    records = []
    def reject(name, changed, malformed=False):
        try:
            result = classify(changed)
        except ValueError:
            need(malformed, "unexpected fixture error")
            rejected = True
        else:
            rejected = not result["pass_"]
        need(rejected, "undetected observation corruption " + name)
        records.append(dict(mutation=name, rejected=True))
    for i, x in enumerate(good["comparisons"]):
        changed = copy.deepcopy(good)
        changed["comparisons"][i]["after"]["arrival_ns"] = 1.010001
        reject("arrival/" + x["profile"] + "/" + x["path"], changed)
    for field, value in [("area_after", MAX_AREA + .001), ("control_after_ns", CONTROL_LIMIT + .000001)]:
        changed = copy.deepcopy(good); changed[field] = value
        reject(field, changed)
    for i, x in enumerate(good["comparisons"]):
        if x["path"].startswith("icg"):
            changed = copy.deepcopy(good)
            changed["comparisons"][i]["after"]["slack_ns"] = -.000001
            reject("positive-slack/" + x["profile"] + "/" + x["path"], changed)
    changed = copy.deepcopy(good); changed["comparisons"].pop()
    reject("missing-comparison", changed, True)
    changed = copy.deepcopy(good); changed["comparisons"][-1] = changed["comparisons"][0]
    reject("duplicate-comparison", changed, True)
    changed = copy.deepcopy(good); changed["comparisons"][0]["after"]["arrival_ns"] = float("nan")
    reject("nan-arrival", changed, True)
    changed = copy.deepcopy(good); changed["area_after"] = float("nan")
    reject("nan-area", changed, True)
    return dict(status="PASS", valid_control=1, corruptions=len(records), records=records,
                scope="in-memory observation/threshold corruptions only; no RTL mutation")

def main():
    pa = argparse.ArgumentParser()
    pa.add_argument("--work", type=Path, required=True)
    pa.add_argument("--baseline", type=Path, required=True)
    pa.add_argument("--screen", type=Path, required=True)
    pa.add_argument("--output", type=Path, required=True)
    pa.add_argument("--library", type=Path, required=True)
    pa.add_argument("--exeunit-source", type=Path, required=True)
    pa.add_argument("--local-manifest", type=Path, required=True)
    pa.add_argument("--baseline-manifest", type=Path, required=True)
    a = pa.parse_args()
    global LIB
    LIB = a.library
    a.status_prefix = "C2"
    need(not a.output.exists(), "fresh audit output required")
    a.output.mkdir()
    inputs = {}
    def record(path):
        inputs[str(path)] = sha(path)
    record(Path(__file__))
    record(LIB)
    libs = {name:float(area) for name,area in re.findall(
        r"cell\s*\(\s*(\w+)\s*\)\s*\{.*?\barea\s*:\s*([0-9.eE+-]+)", LIB.read_text(encoding="utf-8"), re.S)}
    need(len(libs) > 100, "Liberty parsing failed")
    summaries = {}
    allpaths = {}
    states = {}
    semantics = {}
    normalized_constraints = {}
    original_roots = {}
    for version, root in [("before", a.baseline), ("after", a.work)]:
        mapdir, stadir = root/"parent-map-01", root/"parent-sta-01"
        m = obj(mapdir/"summary.json"); t = obj(stadir/"summary.json")
        original_roots[version] = m["generation"].rsplit("/",1)[0]
        for p in [mapdir/"summary.json", mapdir/"mapped.json", mapdir/"mapped.v",
                  stadir/"summary.json", stadir/"instance-binding.json", stadir/"sta-canonical.v",
                  stadir/"canonical-binding.json", mapdir/"map.ys", mapdir/"abc.constr"]:
            record(p)
        need(m["pass"] is True and t["pass"] is True and m["exit_code"] == 0, "incomplete PPA")
        need(m["library_sha256"] == t["library_sha256"] == sha(LIB), "different Liberty")
        need(m["mapped_json_sha256"] == sha(mapdir/"mapped.json"), "mapping JSON hash")
        need(m["mapped_sha256"] == t["mapped_sha256"] == sha(mapdir/"mapped.v"), "mapping V hash")
        need(t["mapping_summary_sha256"] == sha(mapdir/"summary.json"), "mapping summary hash")
        design = obj(mapdir/"mapped.json")["modules"]["CommonParentCostTop"]
        binding = obj(stadir/"instance-binding.json")
        reverse = {v:k for k,v in binding.items()}
        count = collections.Counter(c["type"] for c in design["cells"].values())
        need(not set(count)-set(libs), "unknown cells")
        need(not m["unknown_cells"] and count["CLKGATETST_X1"] == 3, "ICG/unknown metadata")
        area = sum(libs[c]*n for c,n in count.items())
        need(abs(m["cell_area_sum"]-area) < 1e-6, "wrong area sum")
        need(dict(count) == m["cell_histogram"], "cell histogram mismatch")
        ports = {k:dict(direction=v["direction"],width=len(v["bits"])) for k,v in design["ports"].items()}
        need(ports == m["ports"], "wrong boundary ports")
        summaries[version] = dict(mapping=m, timing=t, area=area)
        need([(p["profile"],p["period_ns"],p["load_ff"]) for p in t["profiles"]] == PROFILES,
             "missing/reordered/different profile")
        drivers = {}
        for cname, cell in design["cells"].items():
            for pin, direction in cell["port_directions"].items():
                if direction == "output":
                    for bit in cell["connections"][pin]:
                        if isinstance(bit,int):
                            need(bit not in drivers, "multiple drivers")
                            drivers[bit] = (cname,pin)
        wanted = ["dut.elasticDivOccupied_divBusy"] + (
            ["dut.uncer_en_reg","dut.uncer_en_reg_1"] if version == "before"
            else ["dut.elasticDivOccupied_divOwnerIsFp"])
        semantic_pins = {}
        for name in wanted:
            bits = design["netnames"][name]["bits"]
            need(len(bits)==1, "nonscalar control state")
            cname,pin = drivers[bits[0]]
            need(pin in ["Q","QN"] and design["cells"][cname]["type"].startswith("DFF"), "not DFF")
            semantic_pins[name] = reverse[cname]+"/D"
        need(obj(a.screen/(version+"-state-registers.json")) == semantic_pins, "state query omissions/misbindings")
        if version == "after":
            for old in ["dut.uncer_en_reg","dut.uncer_en_reg_1"]:
                if old in design["netnames"]:
                    cname,_ = drivers[design["netnames"][old]["bits"][0]]
                    need(not design["cells"][cname]["type"].startswith("DFF"), "remaining unqueried hold state")
        semantics[version] = semantic_pins
        allpaths[version], states[version], normalized_constraints[version] = {}, {}, {}
        for profile in t["profiles"]:
            name = profile["profile"]
            text = (stadir/name/"timing.tcl").read_text(encoding="utf-8").splitlines()
            prefix = text[:next(i for i,line in enumerate(text) if line.startswith("check_setup "))]
            normalized_constraints[version][name] = "\n".join(prefix).replace(original_roots[version],"<WORK>")
            targettext = (a.screen/version/name/"timing.tcl").read_text(encoding="utf-8").splitlines()
            need(targettext[:len(prefix)] == prefix, "targeted STA constraints differ")
            queries = obj(a.screen/version/name/"queries.json")
            expectedkeys = ["state"+str(i) for i in range(len(wanted))]+["icg"+str(i) for i in range(3)]
            need(set(queries)==set(expectedkeys), "targeted query omissions")
            for i,(semantic,pin) in enumerate(semantic_pins.items()):
                need(queries["state"+str(i)] == [f"-to [get_pins {{{pin}}}]", semantic], "state query mismatch")
            for i in range(3):
                cell = "dut.ClockGate"+("_"+str(i) if i else "")+".impl"
                need(queries["icg"+str(i)] == [f"-to [get_pins {{{reverse[cell]}/E}}]",cell], "ICG query mismatch")
            vals = {}
            for k in PATHS[:6]:
                p = stadir/name/(k+".rpt"); record(p); raw = path_report(p)
                for key in raw:
                    need(profile["paths"][k][key] == raw[key], "standard summary/raw disagreement")
                vals[k] = raw
            for k in PATHS[6:]:
                p = a.screen/version/name/(k+".rpt"); record(p); vals[k] = path_report(p)
                need(vals[k]["endpoint"].split()[0] == reverse[queries[k][1]], "wrong ICG endpoint")
            st = {}
            for k in expectedkeys:
                p = a.screen/version/name/(k+".rpt"); record(p)
                raw = path_report(p)
                if k.startswith("state"):
                    need(raw["endpoint"].split()[0] == semantic_pins[queries[k][1]].split("/")[0], "wrong state endpoint")
                    st[k] = raw
            allpaths[version][name], states[version][name] = vals, st
    need(normalized_constraints["before"] == normalized_constraints["after"], "constraint mismatch")
    map_before=(a.baseline/"parent-map-01/map.ys").read_text(encoding="utf-8").replace(original_roots["before"],"<WORK>")
    map_after=(a.work/"parent-map-01/map.ys").read_text(encoding="utf-8").replace(original_roots["after"],"<WORK>")
    need(map_before==map_after,"mapping commands differ")
    need((a.baseline/"parent-map-01/abc.constr").read_bytes()==(a.work/"parent-map-01/abc.constr").read_bytes(),"ABC constraints differ")
    need(summaries["before"]["mapping"]["ports"] == summaries["after"]["mapping"]["ports"], "boundary changed")
    need(abs(summaries["before"]["area"]-BASE_AREA)<1e-6, "baseline area drift")
    bc = max(x["arrival_ns"] for x in states["before"]["nominal"].values())
    ac = max(x["arrival_ns"] for x in states["after"]["nominal"].values())
    need(abs(bc-1.930584)<1e-9, "baseline control drift")
    data = dict(area_before=summaries["before"]["area"], area_after=summaries["after"]["area"],
                control_before_ns=bc, control_after_ns=ac,
                comparisons=[dict(profile=p[0],path=k,before=allpaths["before"][p[0]][k],after=allpaths["after"][p[0]][k])
                             for p in PROFILES for k in PATHS])
    verdict = classify(data)
    reported = obj(a.screen/"result.json"); record(a.screen/"result.json")
    for k in ["area_before","area_after","control_before_ns","control_after_ns"]:
        need(abs(reported[k]-data[k])<1e-6, "reported aggregate differs")
    need(len(reported["comparisons"])==45,"reported count differs")
    lookup = {(x["profile"],x["path"]):x for x in reported["comparisons"]}
    need(len(lookup)==45,"reported duplicate metrics")
    for x, ok in zip(data["comparisons"],verdict["path_pass"]):
        got = lookup[(x["profile"],x["path"])]
        for side in ["before","after"]:
            for key in ["arrival_ns","slack_ns","startpoint","endpoint"]:
                need(got[side][key]==x[side][key],"reported path differs")
        need(got["pass_"]==ok,"reported path decision differs")
    need(reported["fullcore_authorized_by_gate"]==verdict["pass_"],"wrong fullcore gate")
    need(reported["status"]==(a.status_prefix+"_SCREEN_PASS" if verdict["pass_"] else a.status_prefix+"_SCREEN_REJECT"),"wrong screen verdict")
    expected_head = "6704ce3502a7235cdb81697638c01ed23f6914f6"
    expected_exu = "febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6"
    expected_manifest = "5fe7ea1cd978cf14ef371380a51e64d942673e1c62c7ac3748698418237b1428"
    expected_baseline_manifest = "9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77"
    need(reported["candidate_head"]==expected_head,"wrong C2 candidate identity")
    need(sha(a.exeunit_source)==expected_exu,"candidate source identity mismatch")
    need(sha(a.local_manifest)==reported["local_manifest_sha256"]==expected_manifest,"local archive identity mismatch")
    need(sha(a.baseline_manifest)==reported["baseline_manifest_sha256"]==expected_baseline_manifest,"baseline archive identity mismatch")
    generation = a.work/"parent-cost-01/result.json"
    need(obj(generation)["source_commit"]==expected_head,"candidate generated from wrong revision")
    basepins={r["path"]:r["raw_sha256"] for r in obj(a.baseline_manifest)["files"]}
    expected_baseline_files={name[len("cost/"):] for name in basepins
        if any(name.startswith("cost/"+directory+"/") for directory in ["parent-map-01","parent-sta-01","parent-cost-01"])}
    actual_baseline_files=set()
    baseline_receipt_checks=0
    for directory in ["parent-map-01","parent-sta-01","parent-cost-01"]:
        for path in (a.baseline/directory).rglob("*"):
            if path.is_file():
                relative=path.relative_to(a.baseline).as_posix()
                need(basepins.get("cost/"+relative)==sha(path),"baseline source seal mismatch "+relative)
                actual_baseline_files.add(relative)
                baseline_receipt_checks+=1
    need(actual_baseline_files==expected_baseline_files,"baseline receipt set incomplete/unexpected")
    for path in [a.exeunit_source,a.local_manifest,a.baseline_manifest,generation]:
        record(path)
    identity=dict(candidate_head=expected_head,candidate_exeunit_sha256=expected_exu,
                  local_manifest_sha256=expected_manifest,baseline_manifest_sha256=expected_baseline_manifest,
                  baseline_receipt_checks=baseline_receipt_checks)
    rejected = self_check()
    for path,digest in inputs.items():
        need(sha(path)==digest,"input mutated during audit")
    result = dict(status="C2_PORTABLE_COST_AUDIT_PASS", screening_pass=verdict["pass_"],
                  failures=verdict["failures"], paths=45, path_pass_count=sum(verdict["path_pass"]),
                  area=data["area_after"], control=data["control_after_ns"], states=states, semantics=semantics,
                  threshold_observation_self_check=rejected, data=data,
                  input_files=len(inputs), input_hashes_unchanged=True,
                  screen_result_sha256=sha(a.screen/"result.json"), **identity,
                  scope="Portable unpacked-evidence recomputation; checks frozen identity, not live Git HEAD. No EDA/fullcore/performance run.")
    (a.output/"inputs.json").write_text(json.dumps(inputs,indent=2)+"\n",encoding="utf-8")
    (a.output/"audit.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ["data","states","semantics","threshold_observation_self_check"]},indent=2))
if __name__ == "__main__":
    main()
