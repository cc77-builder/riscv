"""Five-process first-dot screen on fixed bc9/e66 hardware; no RTL build.

The probe build has a distinct receipt and manifest contract. Its admission
replaces only build provenance; original O3 math/state/retirement/counter and
O2 transaction parsers run on the actual streams. No archived PASS is promoted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys

import admit as a

g, ROOT = a.g, a.ROOT
HERE = Path(__file__).resolve().parent
CONTRACT = "r2-first-dot-8x32-runtime-v2"
ADMISSION_SHA = "2e2d181b7962f7973af48e1b26424c46360437dd2b56c7fa7188b5bb3339d7f5"
suite = g.load("firstdot_input_suite", ROOT / "team/optimizations/o2/fullcore/run_suite.py")
identity = g.load("firstdot_hardware_identity", ROOT / "team/optimizations/o2/fullcore/g3_supplement/audit.py")
counter = g.load("firstdot_o3_counter", ROOT / "team/workloads/o3-gemv/check.py")
failure = g.load("firstdot_failure", ROOT / "team/optimizations/o1/audit/runtime_gate.py")
fatal = g.load("firstdot_fatal", ROOT / "team/optimizations/o2/fullcore/recheck.py")
observer = g.load("firstdot_observer", ROOT / "team/optimizations/o2/fullcore/analyze.py")
ENV = dict(PATH="/usr/bin:/bin", LANG="C", LC_ALL="C", TZ="UTC")
INJECT = re.compile(r"^DIFFTEST_FIRSTDOT_BIT64_INJECTED vd=(\d+) pc=(0x[0-9a-f]+) instruction=(0x[0-9a-f]+)$", re.M)
AUX = {"constantin.txt": "a1fd1d4de05919fec0257bacb550a3622c0f4ec2373e5cf230fc4233fb98c1bf",
       "plusArgs": "160d9702d313cbe66be84ae88c2f45c3df9ed7b61b65e3ddeea25133ac6765ff"}
PARENT = {
    "inputs.json": "7adbe1dedc86a9ceb5feb5ee8692db5842ffdaeede7840ddba1276b799538edd",
    "configuration.json": "e5db56795ff6a911bd2f1303d60de608ea99a3b81db1a037e4a6ec8a25c3636b",
    "state.json": "e6d1da1e073d3616b40794dcbbd80e5a6f6e55808910802f8a032b5d48e572f4",
    "runs/0-firstdot-negative/result.json": "d339cc40d4ff025f218bcd9730d46058e6af4490fbc262741c4ec63a682ba590",
    "negative-reference.so": "670f22d9e2f3b1f86329e9330f198bad18f341e370effe7206f6c788eb9ce95b",
}


def import_negative(parent, config):
    """Recheck one pinned failed-v1 run; never change its state or receipt.

    This is an explicit v2 continuation after a diagnostic parser failure,
    not a generic resume or a cached negative PASS. Only four new EMUs remain.
    """
    parent = Path(parent).resolve()
    files = {str(parent / name): digest for name, digest in PARENT.items()}
    verify_files(files)
    old = a.read(parent / "configuration.json")
    g.require(all(config[k] == v for k, v in old.items()), 'negative parent configuration differs')
    files.update(a.read(parent / "inputs.json"))
    verify_files(files)
    directory = parent / "runs/0-firstdot-negative"
    record = a.read(directory / "result.json")
    validate_record(record, directory, old, "firstdot", True, 0)
    stdout, stderr = ((directory / name).read_text() for name in ("stdout.log", "stderr.log"))
    suite.validate_runtime(stdout + stderr, record["reference"])
    record.update(negative_check(stdout, stderr, record["exit_code"], config["target"]))
    for name, digest in record["raw_sha256"].items():
        files[str(directory / name)] = digest
    for name, digest in AUX.items():
        files[str(Path(record["cwd"]) / "build" / name)] = digest
    return record, files


def bind_firstdot_group(plain, injection, mismatch, pc, word, vd, mismatch_pc):
    """Bind the fixed DiffTest ring, including counter skips and separate v0wen.

    bc9 Rob.scala exports v0wen separately; difftest.cpp's diagnostic wen ORs
    rfwen/fpwen/vecwen only. Thus this v0 VDOT prints wen=0, although the vector
    state comparison and the O2 transaction stream still check its writeback.
    A skip is allowed only on the four exact calibrated counter instructions.
    """
    row_pattern = re.compile(
        r'\[(\d+)\] commit pc ([0-9a-fA-F]{1,16}) inst ([0-9a-fA-F]{1,8}) '
        r'wen ([01]) dst (\d+) data ([0-9a-fA-F]{1,16}) idx ([0-9a-fA-F]+)'
        r'(?: \(([0-9a-fA-F]{2})\))?(?: \((S)\))?( <--)?[ \t]*')
    groups, rows, first_pcs, positions = {}, {}, {}, []
    latest_groups, latest_rows = [], []
    for line in re.finditer(r'[^\n]+', plain):
        text = line[0]
        if text.startswith('commit group '):
            parsed = failure.COMMIT_GROUP.fullmatch(text)
            g.require(parsed is not None, 'malformed commit group record')
            slot, group_pc, count, latest = parsed.groups()
            slot, group_pc, count = int(slot), int(group_pc, 16), int(count)
            g.require(0 <= slot < 16 and slot not in groups and 0 <= count <= 32,
                      'invalid/duplicate commit group slot or count')
            groups[slot] = (group_pc, count)
            if latest:
                latest_groups.append(slot)
        elif re.match(r'^\[[^\]]+\] (?:commit|exception|interrupt)\b', text):
            parsed = row_pattern.fullmatch(text)
            g.require(parsed is not None, 'malformed/unrepresentable instruction trace record')
            slot, row_pc, row_word, wen, dst, _, _, queue, skip, latest = parsed.groups()
            slot, row_pc, row_word, dst = int(slot), int(row_pc, 16), int(row_word, 16), int(dst)
            g.require(0 <= slot < 32 and slot not in rows and 0 <= dst < 32,
                      'invalid/duplicate instruction trace slot or destination')
            g.require(not skip or (row_word in counter.base.COUNTERS and queue is None),
                      'skip tag outside calibrated counter read')
            rows[slot] = (row_pc, row_word, int(wen), dst, skip, queue)
            if latest:
                latest_rows.append(slot)
        elif text.startswith('the first commit instr pc of '):
            parsed = re.fullmatch(r'the first commit instr pc of (DUT|REF) is (0x[0-9a-fA-F]{1,16})[ \t]*', text)
            g.require(parsed is not None and parsed[1] not in first_pcs, 'malformed/duplicate DUT or REF group PC')
            first_pcs[parsed[1]] = int(parsed[2], 16)
        else:
            continue
        positions.append((line.start(), line.end()))
    g.require(set(groups) == set(range(16)) and set(rows) == set(range(32)) and
              len(latest_groups) == len(latest_rows) == 1 and set(first_pcs) == {'DUT', 'REF'},
              'missing/ambiguous complete commit ring evidence')
    g.require(all(injection.end() < start and end < mismatch.start() for start, end in positions),
              'commit evidence must follow injection and precede mismatch')
    group_pc, count = groups[latest_groups[0]]
    g.require(0 < count <= 32 and group_pc == mismatch_pc == first_pcs['DUT'] == first_pcs['REF'],
              'negative mismatch belongs to another commit group')
    slots = [(latest_rows[0] - count + 1 + index) % 32 for index in range(count)]
    batch = [rows[slot] for slot in slots]
    g.require(batch[0][0] == group_pc and vd == 0 and (word >> 7) & 31 == vd and
              word & 0xfe00707f == 0x0200000b and batch.count((pc, word, 0, vd, None, None)) == 1,
              'injected v0 VDOT not uniquely bound to failing commit group')
    return dict(mismatch_pc=hex(mismatch_pc), group_pc=hex(group_pc), group_instructions=count,
                group_slots=slots, fault_pc_binding='unskipped v0 instruction bound to latest complete DiffTest ring')


def verify_rvv_work(body, row):
    """This fixed GEMV uses sixteen-lane RVV chunks, unlike dot8 microbenchmarks.

    Keep the original walked/retired stream; count its widening operations
    against both the exact-regenerated source and the 8x32 workload geometry.
    """
    g.require((row["m"], row["k"], row["scope"]) == (8, 32, "endtoend"), "bounded GEMV shape")
    expected = 16 if row["method"] == "rvv" else 0
    multiply = sum(w & 0xfc00707f == 0xec002057 for _, w in body)
    reduce = sum(w & 0xfc00707f == 0xc4000057 for _, w in body)
    source_multiply = sum(line.startswith("vwmul.vv ") for line in row["body"])
    source_reduce = sum(line.startswith("vwredsum.vs ") for line in row["body"])
    g.require(multiply == reduce == source_multiply == source_reduce == expected, "wrong firstdot GEMV RVV work")


counter.base._provenance.verify_rvv_work = verify_rvv_work


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_files(files):
    for path, digest in files.items():
        g.require(g.sha(path) == digest, "protected input drift: " + path)


def validate_record(record, directory, config, variant, negative, index):
    build = Path(config["admission"]) / "inputs" / ("s03-" + variant)
    reference = directory.parents[1] / "negative-reference.so" if negative else Path(config["reference"])
    image = build / "vdot-perf.bin"
    command = [config["emu"], "-i", str(image), "--flash=" + config["flash"], "--ram-size=128MB",
               "--diff=" + str(reference), "--max-cycles=2000000", "--seed=1"]
    g.require(record["command"] == command and record["environment"] == ENV and
              record["cwd"] == str(directory.parents[1] / ("cwd-" + str(index))) and
              record["variant"] == variant and record["negative"] is negative and
              record["reference"] == str(reference), "runtime command/environment/selection differs")
    roles = {str(p):g.sha(p) for p in (Path(config["emu"]), image, reference, Path(config["flash"]))}
    g.require(record["files"] == roles and record["image_sha256"] == g.sha(image), "runtime input roles differ")
    g.require(record.get("process_started") is True and type(record.get("pid")) is int and record["pid"] > 0 and
              record.get("timed_out") is False and record.get("single_core") is True and
              record.get("emu_threads") == 1 and record.get("cpu_affinity") == config["cpu_affinity"],
              "incomplete actual runtime or configuration")
    start, stop = (datetime.fromisoformat(record[k]) for k in ("started", "finished"))
    g.require(start.utcoffset() is not None and stop.utcoffset() is not None and start <= stop,
              "runtime timestamp order")
    g.require(set(record["raw_sha256"]) == {"stdout.log", "stderr.log"}, "raw transcript inventory")
    verify_files({str(directory / name):digest for name,digest in record["raw_sha256"].items()})
    for name, digest in AUX.items():
        g.require(g.sha(Path(record["cwd"]) / "build" / name) == digest, "runtime copied AUX differs")


def negative_check(stdout, stderr, code, target):
    g.require(code == 1, "negative must exit exactly 1")
    for text in (stdout, stderr):
        fatal.reject_fatal_output(text)
    plain = failure.normalize_console(stderr + stdout)
    g.require(failure.COMMON_FAILURES.search(plain) is None and "HIT GOOD TRAP" not in plain,
              "unrelated negative failure or unexpected success")
    injections = list(INJECT.finditer(plain))
    g.require(len(injections) == 1 and plain.count("DIFFTEST_FIRSTDOT_BIT64_INJECTED") == 1,
              "exactly one complete bit64 injection required")
    injected = injections[0]
    rd, pc, word = (int(x, 0) for x in injected.groups())
    g.require(rd == target["rd"] == 0 and pc == int(target["pc"], 16) and word == int(target["word"], 16),
              "injection target differs from admitted ELF")
    states, state_matches = [], []
    for label in ("BEFORE", "AFTER"):
        matches = list(re.finditer(r"^FIRSTDOT_STATE_" + label + r"=([0-9a-f]{2800})$", plain, re.M))
        g.require(len(matches) == 1 and plain.count("FIRSTDOT_STATE_" + label) == 1,
                  "complete ABI state evidence required")
        states.append(bytes.fromhex(matches[0][1]))
        state_matches.append(matches[0])
    delta = bytes(x ^ y for x, y in zip(*states))
    g.require(delta == bytes(808) + b"\x01" + bytes(591), "state corruption exceeds v0 bit64")
    g.require(plain.count("FIRSTDOT_REFERENCE_UNCHANGED=1") == 1, "underlying reference not checked")
    mismatches, aborts = list(failure.MISMATCH.finditer(plain)), list(failure.ABORT.finditer(plain))
    g.require(len(mismatches) == len(aborts) == 1 and plain.count("different at pc") == plain.count("ABORT") == 1,
              "exactly one high-half mismatch and ABORT required")
    mismatch, abort = mismatches[0], aborts[0]
    vd, group_pc, right, wrong = (int(v, 0) for v in mismatch.groups())
    g.require(vd == rd and right < 1 << 64 and wrong < 1 << 64 and right ^ wrong == 1,
              "mismatch is not exactly bit64 of v0")
    g.require(right == int.from_bytes(states[1][808:816], "little") and
              wrong == int.from_bytes(states[0][808:816], "little") and states[0][804:816] == bytes(12),
              "mismatch does not match the captured full-width VDOT result")
    g.require(injected.end() < state_matches[0].start() < state_matches[1].start() < mismatch.start(),
              "negative state evidence ordering")
    g.require(injected.end() < mismatch.start() < abort.start() and
              not plain[mismatch.end():abort.start()].strip(), "negative terminal chain")
    binding = bind_firstdot_group(plain, injected, mismatch, pc, word, rd, group_pc)
    analysis = observer.analyze(stderr + stdout, require_complete=False)
    g.require(analysis["status"] == "O2_PARTIAL_TRACE_AUDIT" and analysis["schema"]["slots"] == 2,
              "negative transaction trace failed")
    return dict(status="FIRSTDOT_EXACT_V0_BIT64_REJECTION_PASS", target=target, **binding,
                full_state_bytes=1400, only_bit64_changed=True, normal_reference_unchanged=True,
                abort_event_pc=abort[1], observation=analysis)


def normal_check(build, run, variant):
    a.verify_image(build, variant)
    manifest = a.read(build / "data/manifest.json")
    receipt = a.read(run / "result.json")
    g.require(receipt["exit_code"] == 0 and not receipt.get("timed_out"), "normal process failed/incomplete")
    verify_files(receipt["files"])
    verify_files({str(run / name): digest for name, digest in receipt["raw_sha256"].items()})
    stdout, stderr = ((run / n).read_text() for n in ("stdout.log", "stderr.log"))
    for text in (stdout, stderr):
        failure.validate_failure_markers(text)
        fatal.reject_fatal_output(text)
        g.require("FIRSTDOT_" not in text, "negative fixture output in normal run")
    suite.validate_runtime(stdout + stderr, receipt["reference"])
    # Explicit adapter: the old probe manifest identifies its new renderer,
    # while the already compiled harness still prints the frozen S1 contract.
    counter.base.check_compiled_cases(build / "vdot-perf.elf", manifest)
    samples = counter.base.trace_windows(counter.base.parse_events(stderr), manifest,
                                         counter.base.elf_kernels(build / "vdot-perf.elf"))
    uart_manifest = dict(manifest, contract=manifest["binary_harness_contract"])
    g.require(uart_manifest["contract"] == a.probe.c.CONTRACT, "unexpected binary harness contract")
    counter.base.check_uart(stdout, uart_manifest, samples)
    analysis = observer.analyze(stderr + stdout)
    expected = sum(manifest["rows"][p["index"]]["dots"] for p in manifest["plan"]
                   if manifest["rows"][p["index"]]["method"] == "vdot")
    g.require(analysis["status"] == "O2_TRACE_PASS" and analysis["schema"]["slots"] == 2 and
              all(analysis[k] == 0 for k in ("pending_count", "pending_div_count", "unfinished_rob_count")) and
              analysis["counts"].get("COMMIT") == expected == 384, "normal transaction/commit/drain gate")
    g.require(len(samples) == len(manifest["plan"]) == 24, "normal window inventory")
    for sample, entry in zip(samples, manifest["plan"]):
        sample.update(variant=variant, software=manifest["rows"][entry["index"]]["software"])
    return dict(status="FIRSTDOT_NORMAL_ARCHITECTURE_COUNTER_TRACE_PASS", samples=samples, observation=analysis)


def summarize(normal):
    g.require(len(normal) == 4 and [(r["variant"], r["replay"]) for r in normal] ==
              [("firstdot", 0), ("s1", 0), ("firstdot", 1), ("s1", 1)], "normal/replay inventory")
    for first, replay in zip(normal[:2], normal[2:]):
        signature = lambda r: [(s["seq"], s["cycles"], s["instructions"]) for s in r["samples"]]
        g.require(len(first["samples"]) == len(replay["samples"]) == 24 and signature(first) == signature(replay),
                  "cycle/instret replay differs")
    measured = [s for r in normal[:2] for s in r["samples"] if s["phase"] == "measured"]
    expected = {(v, sw, method, repeat) for v in ("s1", "firstdot") for sw in ("basic", "reuse")
                for method in ("vdot", "rvv") for repeat in range(2, 6)}
    keys = [(s["variant"], s["software"], s["method"], s["repeat"]) for s in measured]
    g.require(len(keys) == 32 and set(keys) == expected and all(s["dataset"] == 0 and
              type(s["cycles"]) is int and s["cycles"] > 0 and type(s["instructions"]) is int and
              s["instructions"] > 0 for s in measured), "formal sample inventory")
    rows = []
    for variant, software, method in sorted({key[:3] for key in keys}):
        samples = [s for s in measured if (s["variant"], s["software"], s["method"]) == (variant, software, method)]
        values = [s["cycles"] for s in samples]
        rows.append(dict(variant=variant, software=software, method=method, samples=4,
                         cycles=values, mean=statistics.mean(values), total=sum(values),
                         minimum=min(values), maximum=max(values), pstdev=statistics.pstdev(values),
                         instructions=[s["instructions"] for s in samples]))
    candidate = next(r for r in rows if (r["variant"], r["software"], r["method"]) == ("firstdot", "reuse", "vdot"))
    baseline = next(r for r in rows if (r["variant"], r["software"], r["method"]) == ("s1", "reuse", "vdot"))
    rvv = min((r for r in rows if r["method"] == "rvv"), key=lambda r: r["total"])
    return dict(formal_windows=32, replay_windows=48, rows=rows,
                candidate=candidate, baseline=baseline, fastest_rvv=rvv,
                reduction_vs_s1=1-candidate["total"]/baseline["total"],
                reduction_vs_fastest_rvv=1-candidate["total"]/rvv["total"],
                advance_to_matrix=candidate["total"] < min(baseline["total"], rvv["total"]))


def quiet_processes():
    data = subprocess.check_output(["ps", "-eo", "pid,comm"], text=True)
    forbidden = {"emu", "verilator", "verilator_bin", "java", "cc1plus", "clang", "clang++"}
    g.require(not any(line.split()[-1] in forbidden for line in data.splitlines()[1:]),
              "another heavy job is active; do not overlap performance runs")
    return data


def validate_output(out, roots):
    g.require(os.name == "posix" and not out.exists() and not out.is_symlink() and
              all(not out.resolve().is_relative_to(p) and not p.is_relative_to(out.resolve()) for p in roots),
              "new native output must not overlap protected inputs")


def run(args):
    g.require(HERE == ROOT / "team/optimizations/o2/r2-first-dot" and
              Path(a.__file__).resolve() == HERE / "admit.py" and not (HERE / "negative.c").is_symlink(),
              "runtime/admission/fixture must share the source root")
    g.require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == args.source_base,
              "source base differs from actual Git HEAD")
    out, admission, hardware = args.output.absolute(), args.admission.resolve(), args.hardware_root.resolve()
    pins_path, inputs_path = args.hardware_pins.resolve(), args.input_contract.resolve()
    roots = (ROOT, admission, hardware, pins_path.parent, inputs_path.parent)
    if args.negative_parent:
        roots += (args.negative_parent.resolve(),)
    validate_output(out, roots)
    g.require(g.sha(admission / "state.json") == ADMISSION_SHA, "unrecognized admission")
    g.require(g.sha(pins_path) == identity.PINS and g.sha(inputs_path) == identity.INPUTS, "hardware/input identity")
    out.mkdir(parents=True)
    state = dict(contract=CONTRACT, status="PREFLIGHT", started=now(), new_emu_runs=0, active_pid=None,
                 reused_emu_runs=0, defaults_changed=False, performance_measured=False, whole_matrix_qualified=False)
    persist = lambda: g.save(out / "state.json", state)
    persist()
    files = {}

    def command(label, argv, cwd, limit=180, emu=False, extra=None):
        launch_before = state["new_emu_runs"]
        directory = out / label
        directory.mkdir(parents=True, exist_ok=False)
        record = dict(command=list(map(str, argv)), cwd=str(cwd), environment=dict(ENV),
                      started=now(), exit_code=None, process_started=False, timed_out=False)
        if extra:
            record.update(extra)
        path = directory / ("result.json" if emu else "command.json")
        def save():
            if emu and record.get("process_started") and "cpu_affinity" not in record and "finished" not in record:
                record["cpu_affinity"] = sorted(os.sched_getaffinity(record["pid"]))
            g.save(path, record)
            if emu:
                state["new_emu_runs"] = launch_before + int(record["process_started"])
                state["active_pid"] = record.get("pid") if "finished" not in record else None
                persist()
        save()
        with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
            try:
                if emu:
                    g.require(state["new_emu_runs"] + state["reused_emu_runs"] < 5, "five-process budget exhausted")
                    (directory / "processes-before.txt").write_text(quiet_processes())
                a.probe.a.legacy_f.spawn(record["command"], cwd, stdout, stderr, record, save, env=ENV, timeout=limit)
            finally:
                record.update(finished=now(), raw_sha256={name:g.sha(directory / name) for name in ("stdout.log", "stderr.log")})
                save()
        if emu:
            (directory / "processes-after.txt").write_text(quiet_processes())
        else:
            g.require(record["exit_code"] == 0 and not record["timed_out"], "build command failed: " + label)
        return record

    try:
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
        state["cpu_affinity"] = sorted(os.sched_getaffinity(0))
        pins = a.read(pins_path)
        emu = hardware / "build/emu"
        g.require(pins["emu_sha256"] == identity.EMU, "wrong EMU")
        suite.hardware_guard(pins, emu, root=hardware)
        contract = a.read(inputs_path)
        paths = {key:Path(value) for key, value in contract["paths"].items()}
        suite.input_contract.validate(inputs_path, paths, paths["reference"].parents[3] / "runs/t11-matrix-canonical", hardware)
        guard = g.load("firstdot_nemu_guard", ROOT / "team/scripts/artifact_guard.py")
        suite.input_contract.verify_am(contract, guard)
        provenance = guard.verify_nemu(paths["reference"].parents[1], paths["reference"], "reference")
        suite.input_contract.bind_reference(contract, paths["reference"], provenance)
        files.update(contract["files"])
        for group in ("files", "dependency_files"):
            files.update({str(hardware / name):digest for name,digest in pins[group].items()})
        files.update({str(p):g.sha(p) for p in (emu, pins_path, inputs_path, admission / "state.json")})
        admitted = a.read(admission / "state.json")
        files.update({str(admission / "inputs" / name):digest for name,digest in admitted["input_sha256"].items()})
        for path in ROOT.joinpath("team").rglob("*.py"):
            if "evidence" not in path.parts and "out" not in path.parts:
                files[str(path)] = g.sha(path)
        files[str(HERE / "negative.c")] = g.sha(HERE / "negative.c")
        files[str(Path(__file__).resolve())] = g.sha(__file__)
        a.verify_sources()
        builds = {v:admission / "inputs" / ("s03-" + v) for v in ("s1", "firstdot")}
        reports = {v:a.verify_image(p, v) for v,p in builds.items()}
        g.save(out / "admission-recheck.json", dict(images=reports, pair=a.verify_pair(admission / "inputs")))
        target = reports["firstdot"]["first_custom_target"]
        negative = out / "negative-reference.so"
        cc = Path("/usr/bin/gcc")
        files[str(cc)] = g.sha(cc)
        command("fixture-build", [cc, "-shared", "-fPIC", "-O2", "-Wall", "-Wextra", "-Werror",
                '-DREF_SO="' + str(paths["reference"]) + '"', "-DTARGET_PC=" + target["pc"] + "ULL",
                "-DTARGET_WORD=" + target["word"] + "u", HERE / "negative.c", "-Wl,--no-as-needed",
                paths["reference"], "-ldl", "-o", negative], ROOT)
        command("fixture-linkage", ["/usr/bin/readelf", "-d", negative], ROOT)
        linkage = (out / "fixture-linkage/stdout.log").read_text()
        g.require("Shared library: [" + str(paths["reference"]) + "]" in linkage, "fixture must link normal NEMU directly")
        files[str(negative)] = g.sha(negative)
        for name, digest in AUX.items():
            g.require(g.sha(hardware / "build" / name) == digest, "qualified AUX drift: " + name)
            files[str(hardware / "build" / name)] = digest
        g.save(out / "inputs.json", files)
        configuration = dict(admission=str(admission), hardware_root=str(hardware),
               hardware_pins=str(pins_path), input_contract=str(inputs_path), reference=str(paths["reference"]),
               flash=str(paths["flash"]), emu=str(emu), target=target, source_base=args.source_base,
               cpu_affinity=state["cpu_affinity"])
        if args.negative_parent:
            configuration["negative_parent"] = str(args.negative_parent.resolve())
        g.save(out / "configuration.json", configuration)
        files[str(out / "configuration.json")] = g.sha(out / "configuration.json")
        records = []
        if args.negative_parent:
            imported, protected = import_negative(args.negative_parent, configuration)
            files.update(protected)
            records.append(imported)
            g.save(out / "negative-import.json", dict(parent=configuration["negative_parent"],
                   parent_sha256=PARENT, rechecked=imported, original_status="FAILED",
                   reason="v1 diagnostic ring parser rejected counter skip and separate v0wen"))
            files[str(out / "negative-import.json")] = g.sha(out / "negative-import.json")
            state["reused_emu_runs"] = 1
            persist()
        g.save(out / "inputs.json", files)
        for index, (variant, replay, is_negative) in enumerate([
                ("firstdot", 0, True), ("firstdot", 0, False), ("s1", 0, False),
                ("firstdot", 1, False), ("s1", 1, False)]):
            if is_negative and args.negative_parent:
                continue
            verify_files(files)
            state.update(status="RUNNING", stage=index)
            persist()
            label = "runs/" + str(index) + "-" + variant + ("-negative" if is_negative else "-normal")
            cwd = out / ("cwd-" + str(index))
            (cwd / "build").mkdir(parents=True)
            for name in ("constantin.txt", "plusArgs"):
                shutil.copyfile(hardware / "build" / name, cwd / "build" / name)
                g.require(g.sha(cwd / "build" / name) == AUX[name], "copied AUX drift")
                files[str(cwd / "build" / name)] = AUX[name]
            reference = negative if is_negative else paths["reference"]
            image = builds[variant] / "vdot-perf.bin"
            roles = {str(p):g.sha(p) for p in (emu, image, reference, paths["flash"])}
            argv = [emu, "-i", image, "--flash=" + str(paths["flash"]), "--ram-size=128MB",
                    "--diff=" + str(reference), "--max-cycles=2000000", "--seed=1"]
            record = command(label, argv, cwd, limit=1200, emu=True, extra=dict(variant=variant, replay=replay,
                       negative=is_negative, reference=str(reference), image_sha256=g.sha(image), files=roles,
                       single_core=True, emu_threads=1))
            verify_files(files)
            directory = out / label
            validate_record(record, directory, configuration, variant, is_negative, index)
            suite.validate_runtime((directory / "stdout.log").read_text() + (directory / "stderr.log").read_text(), str(reference))
            if is_negative:
                result = negative_check((directory / "stdout.log").read_text(), (directory / "stderr.log").read_text(), record["exit_code"], target)
            else:
                result = normal_check(builds[variant], directory, variant)
            record.update(result)
            g.save(directory / "result.json", record)
            records.append(record)
            g.save(out / "completed-runs.json", records)
        g.require(records[0]["image_sha256"] == records[1]["image_sha256"] and
                  records[0]["finished"] <= records[1]["started"] and records[0]["pid"] != records[1]["pid"], "recovery identity/order")
        summary = summarize(records[1:])
        suite.hardware_guard(pins, emu, root=hardware)
        verify_files(files)
        g.save(out / "inputs.json", files)
        g.save(out / "result.json", dict(contract=CONTRACT, status="FIRSTDOT_8X32_NEGATIVE_RECOVERY_PAIRED_SCREEN_PASS",
               negative=records[0], normal=records[1:], **summary))
        state.update(status="FIRSTDOT_8X32_NEGATIVE_RECOVERY_PAIRED_SCREEN_PASS", performance_measured=True,
                     advance_to_matrix=summary["advance_to_matrix"], formal_windows=32, replay_windows=48)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = now()
        persist()
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "admission", "hardware-root", "hardware-pins", "input-contract"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-base", required=True)
    parser.add_argument("--negative-parent", type=Path,
                        help="Explicit v2 continuation from the one pinned failed-v1 negative; four new runs only")
    print(json.dumps(run(parser.parse_args()), indent=2))
