"""Recompute T15 full-width results, protocol events and structure from raw traces."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "team/models/vdot-param"))
import generate
from oracle import PROFILES, result


def require(ok, message):
    if not ok:
        raise ValueError(message)


def raw(path):
    if path.exists():
        return path.read_bytes()
    return gzip.decompress(path.with_name(path.name + ".gz").read_bytes())


def load(path):
    return json.loads(raw(path))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def records(path):
    return csv.DictReader(raw(path).decode("utf-8").splitlines(), delimiter=" ")


def replay(rows, vectors):
    pending = None
    counts = Counter()
    cancel_ages, reset_ages, first_ages = set(), set(), set()
    seen_valid = False
    functional_indices, intervals = [], []
    last_functional = None
    for tick, row in enumerate(rows):
        require(int(row["cycle"]) == tick, "missing/duplicate/reordered cycle")
        phase = row["phase"]
        require(phase in ("startup", "functional", "control", "random-control", "drain"), "unknown phase")
        counts[phase + "_cycles"] += 1
        index = int(row["index"])
        require(0 <= index < len(vectors), "input index out of range")
        bits = {}
        for field in ("reset", "flush", "in_valid", "in_ready", "out_valid", "out_ready"):
            bits[field] = int(row[field])
            require(bits[field] in (0, 1), "nonboolean event")
        reset, flush = bits["reset"], bits["flush"]
        want_ready = pending is None and not reset and not flush
        want_valid = pending is not None and tick - pending["cycle"] >= 2 and not reset and not flush
        require(bool(bits["in_ready"]) == want_ready, "ready/cancel/single-outstanding contract")
        require(bool(bits["out_valid"]) == want_valid, "response latency/cancellation contract")
        for field in ("tag_in", "tag_out"):
            require(0 <= int(row[field]) < 2**32, "tag width")
        require(re.fullmatch(r"[0-9a-f]{32}", row["result"]) is not None, "128-bit output format")
        if bits["out_valid"]:
            require(int(row["result"], 16) == int(vectors[pending["index"]]["expected_vd"], 16), "full-128-bit result mismatch")
            require(int(row["tag_out"]) == pending["tag"], "transaction identity mismatch")
            if not seen_valid:
                first_ages.add(tick - pending["cycle"])
                seen_valid = True
            if not bits["out_ready"]:
                counts["stall_cycles"] += 1
        if reset or flush:
            if pending:
                age = tick - pending["cycle"]
                (reset_ages if reset else cancel_ages).add(age)
                counts["reset_dropped" if reset else "killed"] += 1
            pending = None
            seen_valid = False
        else:
            if bits["out_valid"] and bits["out_ready"]:
                counts["responses"] += 1
                if pending["phase"] == "functional":
                    counts["functional_responses"] += 1
                pending = None
                seen_valid = False
            if bits["in_valid"] and bits["in_ready"]:
                require(pending is None, "overlapping transaction")
                counts["accepted"] += 1
                pending = dict(index=index, tag=int(row["tag_in"]), cycle=tick, phase=phase)
                seen_valid = False
                if phase == "functional":
                    functional_indices.append(index)
                    if last_functional is not None:
                        intervals.append(tick - last_functional)
                    last_functional = tick
        require(counts["accepted"] == counts["responses"] + counts["killed"] + counts["reset_dropped"] + (pending is not None), "conservation")
        counts["cycles"] += 1
    require(pending is None, "undrained transaction")
    return dict(counts= dict(counts), cancel_ages=sorted(cancel_ages), reset_ages=sorted(reset_ages),
                first_valid_ages=sorted(first_ages), functional_indices=functional_indices,
                minimum_functional_accept_interval=min(intervals) if intervals else None)


def structure(text, element_bits):
    def module(name):
        matches = re.findall(r"module " + name + r"\(.*?endmodule", text, re.S)
        require(len(matches) == 1, "missing/duplicate arithmetic module " + name)
        return matches[0]
    products, reduce, pipe = (module(name) for name in ("ParamProducts", "ParamReduce", "ParamPipe"))
    regs = {name: int(high) + 1 for high, name in re.findall(r"reg\s+\[(\d+):0\]\s+(\w+);", pipe)}
    widths = [int(high) + 1 for high in re.findall(r"wire\s+\[(\d+):0\]\s+\w+\s*=.*?\+.*?;", reduce, re.S)]
    product_bits = 2 * element_bits
    require(products.count(" * ") == 8 and reduce.count(" + ") == 7, "arithmetic operator count")
    require(widths == [product_bits+1]*4 + [product_bits+2]*2 + [product_bits+3], "widening tree widths")
    expected_regs = {"state":2, "resultReg":128, "tagReg":32,
                     **{f"productsReg_{i}":product_bits for i in range(8)}}
    require(regs == expected_regs, "pipeline register declaration mismatch")
    return dict(multiply_operators=8, mathematical_multiplier_input_bits=element_bits,
                product_bits=product_bits, add_operators=7, reduction_levels=3,
                adder_output_widths=widths, accumulator_bits=widths[-1],
                declared_register_bits=sum(regs.values()), register_declarations=regs,
                scope="One ParamPipe instance; excludes duplicate combinational/legacy test instances. RTL declarations are not physical area/flops/Fmax.")


def verify(run, output):
    manifest = load(run / "file-manifest.json")
    for name, sha in manifest["files"].items():
        path = (run / name).resolve()
        require(path.is_relative_to(run.resolve()), "run path escape")
        require(digest(raw(path)) == sha, "run raw hash mismatch: " + name)
    pins = load(run / "source.json")
    for name, sha in pins["files"].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT), "source path escape")
        require(digest(path.read_bytes()) == sha, "source changed: " + name)
    require(pins["production_src_tree"] == pins["base_production_src_tree"], "production hardware changed")
    require(pins["base_commit"] == "6fea2969d05dc4cb168795a60e2e6ee9ca1f9988", "wrong starting point")
    require(pins["build_target_addition_only"], "production build changed")
    generate.check(ROOT / "team/models/vdot-param/data")
    whole = load(run / "result.json")
    require(whole["status"] == "T15_UNIT_CAMPAIGN_PASS", "incomplete campaign")
    commands = load(run / "commands.json")
    require(all(item["exit_code"] == item["expected_exit"] for item in commands), "command exit mismatch")
    profiles = {}
    for name, p in PROFILES.items():
        vectors = [json.loads(line) for line in (ROOT / "team/models/vdot-param/data" / (name + ".jsonl")).read_text(encoding="utf-8").splitlines()]
        for vector in vectors:
            require(result(int(vector["vs1"],16),int(vector["vs2"],16),p) == int(vector["expected_vd"],16), "oracle mismatch")
        directory = run / name
        combination = list(records(directory / "actual-comb.tsv"))
        require(len(combination) == len(vectors), "combination inventory")
        for i, row in enumerate(combination):
            require(int(row["index"]) == i, "combination ordering")
            require(row["result"] == vectors[i]["expected_vd"], "combination full-width mismatch")
            if name == "s8x8":
                require(row["legacy"] == row["result"], "frozen production baseline mismatch")
        observed = replay(records(directory / "actual-cycles.tsv"), vectors)
        expected = whole["profiles"][name]
        counts = observed["counts"]
        for key in ("accepted", "responses", "killed", "reset_dropped", "stall_cycles", "cycles", "functional_cycles"):
            require(counts.get(key,0) == expected[key], "C++ / Python count mismatch: " + key)
        require(observed["functional_indices"] == list(range(len(vectors))), "functional pipeline inventory")
        require(counts["functional_responses"] == len(vectors), "functional response count")
        require(observed["first_valid_ages"] == [2], "first valid latency")
        require(observed["minimum_functional_accept_interval"] == 3, "minimum initiation interval")
        require({1,2,5}.issubset(observed["cancel_ages"]) and {1,2,5}.issubset(observed["reset_ages"]), "cancel/reset edge coverage")
        require(counts["random-control_cycles"] == 10000 and counts["startup_cycles"] == 2 and counts["drain_cycles"] == 4, "control inventory")
        for fault in ("bit0", "bit33", "bit63", "bit127", "tag"):
            log = raw(directory / ("inject-" + fault + ".log")).decode()
            require("T15_READBACK_INJECTION fault=" + fault in log and "T15_RTL_FAIL" in log and "T15_RTL_PASS" not in log, "readback negative control missing")
            cmd = [c for c in commands if c["label"] == name + "-inject-" + fault]
            require(len(cmd)==1 and cmd[0]["exit_code"]==1, "injection exit must be 1")
        require(expected["vectors"]==len(vectors) and expected["first_valid_latency"]==2 and expected["minimum_functional_accept_interval"]==3, "run summary inventory")
        metrics = structure(raw(directory / "rtl/VDotParamTestTop.sv").decode(),p.element_bits)
        profiles[name] = dict(vectors=len(vectors), first_valid_latency=2, minimum_accept_interval=3,
                              protocol={k:v for k,v in observed.items() if k!="functional_indices"}, structure=metrics,
                              legacy_production_compared=name=="s8x8")
    guards = [c for c in commands if c["label"].startswith("guard-")]
    require(len(guards)==8 and all(c["exit_code"]!=0 for c in guards), "parameter rejection inventory")
    for item in guards:
        require("T15_PARAMETER:" in raw(run/(item["label"]+".log")).decode(), "parameter guard marker missing")
    receipt = dict(status="T15_OFFLINE_RECHECK_PASS", source_commit=pins["source_commit"],
                   profiles=profiles, parameter_guard_rejections=len(guards), hardware_rerun=False,
                   scope="Standalone unit only; no new ISA, NEMU, CPU, Fmax or PPA validation.")
    require(not output.exists(), "output already exists")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in receipt.items() if k!="profiles"}))
    return receipt


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    verify(args.run.resolve(),args.output.resolve())
