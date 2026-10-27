#!/usr/bin/env python3
"""Restore a sealed R3 ZIP and rerun raw evidence audits without EDA or EMU.

Uses the unchanged O4 gzip/manifest format and O4 raw mapping/STA auditors.
Relocation redirects only reads from the recorded runtime prefix; original
evidence bytes and embedded path strings are never rewritten.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from types import SimpleNamespace
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import audit
import experiment as d
import structural_proof as proof
import sta_compat


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def need(ok, why):
    if not ok:
        raise ValueError(why)


def safe(name):
    p = PurePosixPath(name)
    need(name == p.as_posix() and not p.is_absolute() and ".." not in p.parts
         and "\\" not in name and ":" not in name, "unsafe archive path")
    return p


def restore(archive, root):
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        need(len(set(names)) == len(names), "duplicate ZIP member")
        for name in names:
            safe(name)
        manifest = json.loads(z.read("manifest.json"))
        expected = {"manifest.json", "external-artifacts.json"}
        raw_names, stored_names = set(), set()
        for item in manifest["entries"]:
            rel, stored = safe(item["path"]), safe(item["stored"])
            need(str(rel) not in raw_names and str(stored) not in stored_names, "duplicate manifest path")
            raw_names.add(str(rel)); stored_names.add(str(stored))
            member = "files/" + str(stored)
            expected.add(member)
            payload = z.read(member)
            need(len(payload) == item["stored_bytes"] and hashlib.sha256(payload).hexdigest() == item["stored_sha256"],
                 "stored evidence changed")
            raw = gzip.decompress(payload) if item["gzip"] else payload
            need(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "raw evidence changed")
            target = root / str(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        need(set(names) == expected, "ZIP member scope differs")
        need(not json.loads(z.read("external-artifacts.json"))["entries"], "unexpected seal exclusions")
    return len(raw_names)


def verify(root):
    assessment = read(root / "assessment.json")
    need(assessment["audit_pass"] and assessment["contract"] == d.CONTRACT, "assessment contract")
    for relative, path in [("experiment.py", HERE / "experiment.py"), ("structural_proof.py", HERE / "structural_proof.py"),
                           ("sta_compat.py", HERE / "sta_compat.py")]:
        need(sha(path) == sha(root / "source/reduce" / relative), "proof helper version differs")
    for name in ("audit.py", "synthesize.py", "timing.py", "compact.py", "canonical.py"):
        need(sha(HERE.parent / name) == sha(root / "source/o4" / name), "O4 auditor version differs")
    facts = {}
    for variant in ("baseline", "candidate"):
        generation = root / (variant + "-gen-01")
        original, compatible = (root / (variant + x) for x in ("-map-01", "-map-02"))
        timing = root / (variant + "-sta-02")
        mapping, design = audit.mapping_audit(original, root / "work/library/NangateOpenCellLibrary_typical.lib")
        need(sha(original / "map.ys") == mapping["map_script_sha256"], "mapping script identity")
        audit.timing_audit(timing, compatible, design)
        g = read(generation / "result.json")
        need(mapping["generation_sha256"] == sha(generation / "result.json") and g["source_sha256"] == sha(generation / "source.json"),
             "generation/source binding")
        for name in g["rtl"]:
            safe(name)
        rtl = d.generated(generation, variant)
        need(read(generation / "source.json")["files"][d.SOURCE] == d.PINS[variant], "reduction source pin")
        need((original / "mapped.json").read_bytes() == (compatible / "mapped.json").read_bytes(), "serialization changed mapped JSON")
        text, changes = sta_compat.split_assignments((original / "mapped.v").read_text())
        serial = read(compatible / "serialization.json")
        need(text == (compatible / "mapped.v").read_text() and changes == serial["changes"], "serialization edits differ")
        need(serial["original_summary_sha256"] == sha(original / "summary.json")
             and serial["original_verilog_sha256"] == sha(original / "mapped.v"), "serialization original identity")
        need(serial["original_json_sha256"] == sha(original / "mapped.json")
             and serial["adapter_sha256"] == sha(HERE / "sta_compat.py"), "serialization implementation/input identity")
        expected_summary = dict(mapping)
        expected_summary.update(mapped_sha256=sha(compatible / "mapped.v"),
                                serialization_sha256=sha(compatible / "serialization.json"),
                                serialization="scalar assignment split; full structural readback equality; no logic remap")
        need(read(compatible / "summary.json") == expected_summary, "compatible mapping summary changes more than serialization")
        for label in ("original", "compatible"):
            need(serial["readbacks"][label] == sha(compatible / (label + "-readback.json")), "serialization readback changed")
        need(sta_compat.canonical(read(compatible / "original-readback.json")) ==
             sta_compat.canonical(read(compatible / "compatible-readback.json")), "serialization graph differs")
        facts[variant] = dict(area=mapping["cell_area_sum"], reduction_rtl_sha256=sha(rtl),
                             registers=audit.register_groups(read(original / "structure.json"), "o2"))
    formal = root / "formal-struct-01"
    result = read(formal / "result.json")
    need(result["status"] == "R3_GENERATED_REDUCTION_EQUIVALENCE_PASS" and result["proof_driver_sha256"] == sha(HERE / "structural_proof.py"),
         "formal identity/status")
    cert = {}
    for variant, action in (("baseline", proof.prove_baseline), ("candidate", proof.prove_candidate)):
        need(result[variant + "_rtl_sha256"] == facts[variant]["reduction_rtl_sha256"]
             and result[variant + "_json_sha256"] == sha(formal / (variant + ".json")), "formal RTL/JSON binding")
        cert[variant] = action(proof.Graph(read(formal / (variant + ".json"))))
    need(json.loads(json.dumps(cert)) == read(formal / "certificate.json") and
         result["certificate_sha256"] == sha(formal / "certificate.json"), "arithmetic certificate differs")
    negatives = read(formal / "negative-controls.json")
    negative_labels = {"bit100", "zero-extended-lane", "carry-shift", "low32-sign", "duplicate-lane"}
    need(len(negatives) == 5 and {n["label"] for n in negatives} == negative_labels
         and result["negative_controls_sha256"] == sha(formal / "negative-controls.json"), "negative coverage")
    extra = read(root / "proof-audit-01/result.json")
    need(extra["status"] == "PASS" and extra["proof_result_sha256"] == sha(formal / "result.json"), "independent negative audit binding")
    need(len(extra["negative_yosys_evaluations"]) == 5 and
         {n["label"] for n in extra["negative_yosys_evaluations"]} == negative_labels, "independent negative label coverage")
    expected_negatives = proof.negative_sources((root / "candidate-gen-01/rtl/VDotReduce.sv").read_text())
    for item in negatives:
        label = "negative-" + item["label"]
        need((formal / (label + ".sv")).read_bytes() == expected_negatives[item["label"]].encode(), "negative is not the declared candidate mutation")
        need(sha(formal / (label + ".sv")) == item["rtl_sha256"] and sha(formal / (label + ".json")) == item["json_sha256"], "negative identity")
        document = read(formal / (label + ".json"))
        try:
            proof.prove_candidate(proof.Graph(document))
        except ValueError as exc:
            need(str(exc) == item["rejection"], "negative rejection changed")
        else:
            raise ValueError("negative accepted")
        need(proof.Graph(document, strict=False).evaluate(item["inputs"]) == item["actual"]
             and item["expected"] == (sum(item["inputs"]) & 0xffffffff) and item["actual"] != item["expected"], "negative counterexample differs")
        independent = next(x for x in extra["negative_yosys_evaluations"] if x["label"] == item["label"])
        log = root / "proof-audit-01" / (item["label"] + ".log")
        need(sha(log) == independent["log_sha256"], "negative eval log changed")
        bits = re.findall(r"Eval result:.*io_result = 128'([01]+)", log.read_text())
        need(len(bits) == 1 and len(bits[0]) == 128 and int(bits[0], 2) == item["actual"], "Yosys counterexample differs")
    fu = root / "candidate-fu-01"
    checker_path = HERE.parent.parent / "o2/check_negative_fu.py"
    need(sha(checker_path) == sha(root / "source/o2/check_negative_fu.py"), "FU checker version differs")
    spec = importlib.util.spec_from_file_location("r3_fu_check", checker_path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    commands = read(fu / "commands.json")
    for fault in checker.FAULTS:
        records = [r for r in commands if r["log"] == "inject-" + fault + ".log"]
        need(len(records) == 1, "FU negative command coverage")
        checker.check(fault, records[0]["exit_code"], (fu / records[0]["log"]).read_text())
    artifacts = read(fu / "artifacts.json")
    need(len(artifacts) == 2 and {i["path"] for i in artifacts} == {"vectors.tsv", "obj/VVDotElasticFuTestTop"}, "FU artifact scope")
    generated = read(fu / "generated-files.json")
    need(generated and len({i["path"] for i in generated}) == len(generated)
         and "rtl/VDotElasticFuTestTop.sv" in {i["path"] for i in generated}, "FU generated scope")
    need({i["path"] for i in generated} == {p.relative_to(fu).as_posix() for p in (fu / "rtl").rglob("*")
                                           if p.is_file() and p.suffix in (".sv", ".v")}, "FU HDL manifest incomplete")
    for item in artifacts + generated:
        path = fu / str(safe(item["path"]))
        need(path.stat().st_size == item["bytes"] and sha(path) == item["sha256"], "FU vector/binary identity")
    positive = [r for r in commands if r["log"] == "result.log"]
    need(len(positive) == 1 and positive[0]["exit_code"] == 0 and
         re.fullmatch(r"O2_FU_PASS(?: [a-z0-9_]+=[0-9]+)+\n", (fu / "result.log").read_text()), "FU positive execution")
    # Reuse the frozen comparison, including all source/flags/profile gates.
    old_root = Path(assessment["runtime_root"])
    def relocate(path):
        path = Path(path)
        need(".." not in path.parts, "parent traversal in evidence read")
        if path == root or root in path.parents:
            target = path
        else:
            need(old_root in path.parents, "unsealed external read: " + str(path))
            target = root / path.relative_to(old_root)
        target = target.resolve()
        need(target == root.resolve() or root.resolve() in target.parents, "read escapes restored root")
        need(target.is_file() or target.is_dir(), "missing relocated evidence")
        return target
    old_read, old_sha, old_generated = d.read, d.sha, d.generated
    d.read = lambda p: old_read(relocate(p))
    d.sha = lambda p: old_sha(relocate(p))
    d.generated = lambda p, v: old_generated(relocate(p), v)
    target = root / "comparison-recheck.json"
    try:
        d.compare(SimpleNamespace(baseline=root / "baseline-map-02", candidate=root / "candidate-map-02",
                  baseline_sta=root / "baseline-sta-02", candidate_sta=root / "candidate-sta-02",
                  formal=formal, fu_test=root / "candidate-fu-01", output=target))
    finally:
        d.read, d.sha, d.generated = old_read, old_sha, old_generated
    need(read(target) == read(root / "comparison-01.json"), "decision or metrics differ on replay")
    return dict(status="R3_SEALED_RECHECK_PASS", decision=read(target)["decision"], facts=facts,
                proof_negative_controls=len(negatives), fu_negative_controls=4, raw_sta_profiles=10, new_emu_runs=0)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    need(not a.output.exists(), "output must be new")
    with tempfile.TemporaryDirectory(prefix="r3-sealed-recheck-") as temporary:
        root = Path(temporary)
        count = restore(a.archive, root)
        result = verify(root)
    result.update(files=count, archive_sha256=sha(a.archive), verifier_sha256=sha(__file__))
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
