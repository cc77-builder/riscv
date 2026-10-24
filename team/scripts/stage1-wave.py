#!/usr/bin/env python3
"""Extract and check hello/vadd FU and delayed DPIC events from a full FST.

Requires GTKWave fst2vcd/vcd2fst. Original FST and execution receipt stay intact.
Sample the settled low-clock state immediately before each observed rising edge;
do not mistake post-eval ports or the delayed DPIC timestamp for ROB retire time.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

TOP = "TOP.SimTop"
ROB = TOP + ".l_soc.core_with_l2.core.backend.inner_ctrlBlock.rob"
FU = re.compile(re.escape(TOP) + r"\.l_soc\.core_with_l2\.core\.backend\.inner_vfExuBlock\.exus(?:_\d+)?\.VialuFix$")
COMMIT = re.compile(re.escape(ROB) + r"\.difftest_module(?:_\d+)?\.dpic$")
COMMIT_PORTS = ("clock", "enable", "io_valid", "io_pc", "io_instr", "io_vecwen",
                "io_wdest", "io_wpdest", "io_robIdx")
FU_PORTS = ("clock", "reset", "io_in_ready", "io_in_valid", "io_in_bits_ctrl_fuOpType",
            "io_in_bits_ctrl_vpu_vsew", "io_in_bits_ctrl_vpu_vm", "io_in_bits_ctrl_vpu_vuopIdx",
            "io_in_bits_data_src_0", "io_in_bits_data_src_1", "io_out_ready", "io_out_valid",
            "io_out_bits_ctrl_vecWen", "io_out_bits_ctrl_robIdx_flag", "io_out_bits_ctrl_robIdx_value",
            "io_out_bits_ctrl_pdest", "io_out_bits_res_data", "io_out_bits_res_vxsat")
PARENT_PORTS = ("clock", "reset", "io_in_ready", "io_in_valid", "io_in_bits_robIdx_flag",
                "io_in_bits_robIdx_value", "io_in_bits_pdest", "io_in_bits_vecWen")
INPUTS = (
    ((1, 2, 3, 4, 5, 6, 7, 8), (8, 7, 6, 5, 4, 3, 2, 1)),
    ((255, 254, 253, 252, 251, 250, 249, 248), (255, 254, 253, 252, 251, 250, 249, 248)),
    ((127, 128, 255, 0, 1, 128, 127, 255), (1, 255, 1, 0, 255, 128, 127, 255)),
)
MASK64 = (1 << 64) - 1


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def packed(values):
    return int.from_bytes(bytes(values), "little")


def parse_header(stream):
    scopes, signals, header = [], {}, []
    for raw in stream:
        line = raw.strip()
        words = line.split()
        if line.startswith("$scope "):
            scopes.append(words[2])
        elif line.startswith("$upscope"):
            scopes.pop()
        elif line.startswith("$var "):
            name = ".".join(scopes + [words[4]])
            signals[name] = {"width": int(words[2]), "code": words[3]}
        elif line.startswith("$enddefinitions"):
            return signals, header
        elif not scopes:
            header.append(raw)
    raise ValueError("Missing VCD enddefinitions")


def select_signals(signals):
    fus = sorted({name.rsplit(".", 1)[0] for name in signals if FU.fullmatch(name.rsplit(".", 1)[0])})
    commits = sorted({name.rsplit(".", 1)[0] for name in signals
                      if name.endswith(".io_instr") and COMMIT.fullmatch(name.rsplit(".", 1)[0])})
    timers = [name for name in signals if name.startswith(ROB + ".") and name.endswith(".dpic.io_cycleCnt")]
    if len(fus) != 2 or len(commits) != 8 or len(timers) != 1:
        raise ValueError(f"Unsupported hierarchy: FU={len(fus)}, commit={len(commits)}, timers={len(timers)}")
    names = [TOP + ".clock", TOP + ".reset", timers[0]]
    names += [scope + "." + port for scope in fus for port in FU_PORTS]
    names += [scope.rsplit(".", 1)[0] + "." + port for scope in fus for port in PARENT_PORTS]
    names += [scope + "." + port for scope in commits for port in COMMIT_PORTS]
    missing = set(names) - signals.keys()
    if missing:
        raise ValueError("Missing waveform signals: " + ", ".join(sorted(missing)))
    return {name: signals[name] for name in sorted(set(names))}, fus, commits, timers[0]


def frames(stream, selected, output):
    """Stream numeric VCD changes, keeping only selected IDs and complete time slots."""
    codes = {item["code"] for item in selected.values()}
    values, timestamp, changed = {}, None, []
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        if line[0] == "#":
            next_time = int(line[1:])
            if timestamp is not None:
                if next_time <= timestamp:
                    raise ValueError("Non-increasing waveform time")
                output.write(f"#{timestamp}\n" + "".join(changed))
                yield timestamp, values.copy()
                changed = []
            timestamp = next_time
        elif line[0] in "01xzXZ":
            code, value = line[1:], line[0]
            if code in codes:
                values[code] = int(value) if value in "01" else None
                changed.append(raw)
        elif line[0] in "bB":
            value, code = line[1:].split()
            if code in codes:
                values[code] = int(value, 2) if not re.search("[xzXZ]", value) else None
                changed.append(raw)
    if timestamp is not None:
        output.write(f"#{timestamp}\n" + "".join(changed))
        yield timestamp, values.copy()


def extract(stream, selected_vcd, target_pc, target_instr):
    signals, header = parse_header(stream)
    selected, fus, commits, timer = select_signals(signals)
    # Keep hierarchy and alias IDs so the derivative opens normally in GTKWave.
    selected_vcd.writelines(header)
    tree = {}
    for name, item in selected.items():
        node = tree
        *scopes, leaf = name.split(".")
        for scope in scopes:
            node = node.setdefault(scope, {})
        node[leaf] = item

    def write_scope(node):
        for name, item in node.items():
            if "code" in item:
                selected_vcd.write(f"$var wire {item['width']} {item['code']} {name} $end\n")
            else:
                selected_vcd.write(f"$scope module {name} $end\n")
                write_scope(item)
                selected_vcd.write("$upscope $end\n")

    write_scope(tree)
    selected_vcd.write("$enddefinitions $end\n")

    def value(state, name):
        number = state.get(selected[name]["code"])
        if number is None:
            raise ValueError("Unknown/uninitialized required signal: " + name)
        return number

    events, previous, previous_time, edges = [], None, None, 0
    for timestamp, current in frames(stream, selected, selected_vcd):
        if previous is not None and (timestamp != previous_time + 1 or
                value(previous, TOP + ".clock") == value(current, TOP + ".clock")):
            raise ValueError("Incomplete full waveform: timestamps must be contiguous and TOP.clock must alternate")
        if previous is not None and value(previous, TOP + ".clock") == 0 and value(current, TOP + ".clock") == 1:
            if value(previous, TOP + ".reset") == 0 and value(current, TOP + ".reset") == 0:
                edges += 1
                base = {"wave_time": timestamp, "sample_time": previous_time,
                        "cycle_before_edge": value(previous, timer), "cycle_after_edge": value(current, timer)}
                for scope in fus:
                    get = lambda port: value(previous, scope + "." + port)
                    active = get("clock") == 0 and value(current, scope + ".clock") == 1 and get("reset") == 0
                    if active and get("io_in_valid") and get("io_in_ready"):
                        # VIAluFix gets current controls/data from a combinational
                        # Dispatcher, but tags from ExeUnit's separate ctrlPipe_1.
                        # Sample the parent input tag at this same accepted edge.
                        parent = scope.rsplit(".", 1)[0]
                        parent_get = lambda port: value(previous, parent + "." + port)
                        if not (parent_get("io_in_valid") and parent_get("io_in_ready") and
                                parent_get("clock") == 0 and value(current, parent + ".clock") == 1 and
                                parent_get("reset") == 0 and parent_get("io_in_bits_vecWen") == 1):
                            raise ValueError("FU input lacks a matching parent ExeUnit acceptance")
                        events.append(dict(base, kind="fu_in", scope=scope, fuop=get("io_in_bits_ctrl_fuOpType"),
                            vsew=get("io_in_bits_ctrl_vpu_vsew"), vm=get("io_in_bits_ctrl_vpu_vm"),
                            uop=get("io_in_bits_ctrl_vpu_vuopIdx"),
                            rob_flag=parent_get("io_in_bits_robIdx_flag"), rob_value=parent_get("io_in_bits_robIdx_value"),
                            pdest=parent_get("io_in_bits_pdest"),
                            src0=f"{get('io_in_bits_data_src_0'):032x}", src1=f"{get('io_in_bits_data_src_1'):032x}"))
                    if active and get("io_out_valid") and get("io_out_ready"):
                        events.append(dict(base, kind="fu_out", scope=scope, vecwen=get("io_out_bits_ctrl_vecWen"),
                            rob_flag=get("io_out_bits_ctrl_robIdx_flag"), rob_value=get("io_out_bits_ctrl_robIdx_value"),
                            pdest=get("io_out_bits_ctrl_pdest"), data=f"{get('io_out_bits_res_data'):032x}",
                            vxsat=get("io_out_bits_res_vxsat")))
                for scope in commits:
                    get = lambda port: value(previous, scope + "." + port)
                    active = get("clock") == 0 and value(current, scope + ".clock") == 1
                    if active and get("enable") and get("io_valid") and get("io_pc") == target_pc:
                        events.append(dict(base, kind="dpic_commit", scope=scope, pc=f"{get('io_pc'):016x}",
                            instr=f"{get('io_instr'):08x}", vecwen=get("io_vecwen"), wdest=get("io_wdest"),
                            pdest=get("io_wpdest"), rob_value=get("io_robIdx")))
        previous, previous_time = current, timestamp
    if not edges:
        raise ValueError("No full rising edges observed; use --dump-wave-full")
    return {"selected_signals": selected, "fu_scopes": fus, "commit_scopes": commits,
            "timer_signal": timer, "rising_edges": edges,
            "events": events}


def check_events(events, target_instr):
    incoming = [e for e in events if e["kind"] == "fu_in"]
    outgoing = [e for e in events if e["kind"] == "fu_out"]
    commits = [e for e in events if e["kind"] == "dpic_commit"]
    if (len(incoming), len(outgoing), len(commits)) != (3, 3, 3):
        raise ValueError(f"Expected exactly 3 FU inputs/outputs/vadd commits, got {len(incoming)}/{len(outgoing)}/{len(commits)}")
    used_outputs, used_commits, cases = set(), set(), []
    for index, (inp, operands) in enumerate(zip(incoming, INPUTS)):
        if (inp["fuop"], inp["vsew"], inp["vm"], inp["uop"]) != (64, 0, 1, 0):
            raise ValueError(f"Case {index}: unexpected FU controls")
        observed = sorted([int(inp[key], 16) & MASK64 for key in ("src0", "src1")])
        if observed != sorted(map(packed, operands)):
            raise ValueError(f"Case {index}: wrong input lanes")
        expected = packed([(a + b) & 255 for a, b in zip(*operands)])
        matches = [(i, e) for i, e in enumerate(outgoing) if e["scope"] == inp["scope"]
                   and all(e[key] == inp[key] for key in ("rob_flag", "rob_value", "pdest"))
                   and e["wave_time"] > inp["wave_time"] and int(e["data"], 16) & MASK64 == expected]
        if len(matches) != 1 or matches[0][0] in used_outputs:
            raise ValueError(f"Case {index}: missing or ambiguous FU output")
        oi, out = matches[0]
        if out["vecwen"] != 1 or out["vxsat"] != 0:
            raise ValueError(f"Case {index}: invalid writeback controls")
        matches = [(i, e) for i, e in enumerate(commits) if e["wave_time"] > out["wave_time"]
                   and e["rob_value"] == out["rob_value"] and e["pdest"] == out["pdest"]
                   and e["instr"] == f"{target_instr:08x}" and e["vecwen"] == 1 and e["wdest"] == 3]
        if len(matches) != 1 or matches[0][0] in used_commits:
            raise ValueError(f"Case {index}: missing or ambiguous delayed DPIC commit")
        ci, commit = matches[0]
        used_outputs.add(oi)
        used_commits.add(ci)
        cases.append({"case": index, "fu": inp["scope"], "input_cycle": inp["cycle_before_edge"],
                      "output_cycle": out["cycle_before_edge"], "dpic_cycle": commit["cycle_before_edge"],
                      "input_wave_time": inp["wave_time"], "output_wave_time": out["wave_time"],
                      "dpic_wave_time": commit["wave_time"], "low64": f"{expected:016x}",
                      "rob_flag": out["rob_flag"], "rob_value": out["rob_value"], "pdest": out["pdest"]})
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("fst", "receipt", "disassembly", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    if receipt.get("status") != "PASS" or receipt.get("checker_exit_code") != 0 or "--dump-wave-full" not in receipt.get("command", []):
        parser.error("Require a passed full-wave hello/vadd execution receipt")
    original_hash = sha256(args.fst)
    if receipt.get("waveform", {}).get("sha256") != original_hash:
        parser.error("FST does not match the execution receipt")
    instructions = re.findall(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+vadd\.vv\s+v3,v1,v2\s*$",
                              args.disassembly.read_text(), re.M)
    if len(instructions) != 1:
        parser.error("Require exactly one vadd.vv v3,v1,v2 in the supplied disassembly")
    pc, instruction = (int(x, 16) for x in instructions[0])
    converters = {name: shutil.which(name) for name in ("fst2vcd", "vcd2fst")}
    if not all(converters.values()):
        parser.error("GTKWave fst2vcd and vcd2fst are required")
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"schema": "hello-vadd-wave-v1", "status": "RUNNING", "original_fst": str(args.fst.resolve()),
              "original_sha256": original_hash, "run_receipt_sha256": sha256(args.receipt),
              "disassembly_sha256": sha256(args.disassembly), "extractor_sha256": sha256(Path(__file__)),
              "converters": {name: {"path": path, "sha256": sha256(Path(path))} for name, path in converters.items()},
              "pc": f"{pc:016x}", "instruction": f"{instruction:08x}",
              "sampling": "settled low-clock values immediately before each observed local rising edge",
              "cycle_definition": "DifftestTrapEvent.io_cycleCnt sampled before that edge; raw FST time retained",
              "commit_definition": "DPIC observation after ROB delay=3; commit robIdx has value only, no flag",
              "limits": "three hello/vadd cases; no tail-lane, architectural latency, throughput, PPA or performance claim"}
    result = args.output / "wave.json"
    result.write_text(json.dumps(record, indent=2) + "\n")
    process = None
    try:
        selected = args.output / "selected.vcd"
        with (args.output / "fst2vcd.log").open("x") as errors, selected.open("x") as output:
            process = subprocess.Popen([converters["fst2vcd"], str(args.fst)], stdout=subprocess.PIPE,
                                       stderr=errors, text=True, bufsize=1024 * 1024)
            record.update(extract(process.stdout, output, pc, instruction))
            process.stdout.close()
            if process.wait() != 0:
                raise ValueError("fst2vcd failed; see fst2vcd.log")
        record["cases"] = check_events(record["events"], instruction)
        if sha256(args.fst) != original_hash:
            raise ValueError("Original waveform changed during extraction")
        with (args.output / "cases.csv").open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(record["cases"][0]))
            writer.writeheader()
            writer.writerows(record["cases"])
        with (args.output / "vcd2fst.log").open("x") as log:
            subprocess.run([converters["vcd2fst"], str(selected), str(args.output / "selected.fst")],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        if not (args.output / "selected.fst").is_file() or (args.output / "selected.fst").stat().st_size == 0:
            raise ValueError("vcd2fst produced no nonempty selected waveform")
        record["artifacts"] = {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size}
                               for p in (selected, args.output / "selected.fst", args.output / "cases.csv")}
        record["status"] = "PASS"
        print(json.dumps(record["cases"], indent=2))
        print("HELLO_VADD_WAVE_PASS cases=3 lanes=24")
    except BaseException as error:
        record.update(status="FAILED", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        result.write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
