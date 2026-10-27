#!/usr/bin/env python3
"""Negative/lifecycle checks using a real passed hello/vadd run as the fixture.

These are tool tests, not additional hardware cases. Every mutated fixture and
mock process is labelled and kept below the new --output directory.
"""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--wave", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    checker = module(scripts / "summarize-run.py", "stage1_checker")
    wave_checker = module(scripts / "stage1-wave.py", "stage1_wave")
    raw = (args.run / "emulator-output.log").read_bytes()
    errors = (args.run / "emulator-stderr.log").read_bytes()
    receipt = json.loads((args.run / "run.json").read_text())
    checker.validate(raw.decode(), receipt, digest(raw), errors.decode(), digest(errors))
    args.output.mkdir(parents=True, exist_ok=False)
    results = []

    def reject(name, change):
        item = {"stdout": raw.decode(), "stderr": errors.decode(), "receipt": copy.deepcopy(receipt)}
        change(item)
        subdir = args.output / name
        subdir.mkdir()
        for key in ("stdout", "stderr"):
            (subdir / (key + ".log")).write_text(item[key])
        (subdir / "receipt.json").write_text(json.dumps(item["receipt"], indent=2) + "\n")
        try:
            checker.validate(item["stdout"], item["receipt"], digest(item["stdout"].encode()),
                             item["stderr"], digest(item["stderr"].encode()))
        except (ValueError, KeyError) as error:
            results.append({"name": name, "status": "PASS", "observed_rejection": str(error)})
        else:
            raise AssertionError(name + " was accepted")

    def edit_log(item, old, new):
        item["stdout"] = item["stdout"].replace(old, new)
        item["receipt"]["log_sha256"] = digest(item["stdout"].encode())

    reject("log_hash_mismatch", lambda x: x.update(stdout=x["stdout"] + "modified\n"))
    reject("wrong_lane", lambda x: edit_log(x, "vadd case=0 output: 9 9", "vadd case=0 output: 8 9"))
    reject("missing_difftest", lambda x: edit_log(x, "Difftest enabled", "Difftest disabled"))
    reject("truncated_trap", lambda x: edit_log(x, "HIT GOOD TRAP", "TRUNCATED"))
    reject("duplicate_case", lambda x: edit_log(x, "vadd case=0 output:", "vadd case=0 output: vadd case=0 output:"))
    reject("nonzero_exit", lambda x: x["receipt"].update(exit_code=1))
    reject("timeout_receipt", lambda x: x["receipt"].update(timed_out=True))
    reject("changed_image", lambda x: x["receipt"]["inputs_after"]["image"].update(sha256="0" * 64))
    reject("changed_aux", lambda x: x["receipt"]["aux_after"].update({"plusArgs": "0" * 64}))

    def bad_stderr(item):
        item["stderr"] += "\nDIFFTEST FAIL\n"
        item["receipt"]["stderr_sha256"] = digest(item["stderr"].encode())
    reject("failure_in_stderr", bad_stderr)

    # Mock EMUs test runner lifecycle only; never interpreted as RTL results.
    mocks = args.output / "mock-inputs"
    (mocks / "build").mkdir(parents=True)
    for name in ("constantin.txt", "plusArgs"):
        (mocks / "build" / name).write_text("mock auxiliary input\n")
    for name in ("reference", "image", "flash"):
        (mocks / name).write_text("mock " + name + "\n")
    (mocks / "identity.json").write_text(json.dumps({"team_id": "MOCK", "host_ip": "unavailable", "status": "placeholder"}))
    empty = mocks / "empty-emu"
    empty.write_text("#!/usr/bin/env python3\n# MOCK, no hardware execution.\n")
    sleeper = mocks / "sleep-emu"
    sleeper.write_text("#!/usr/bin/env python3\n# MOCK, no hardware execution.\nimport time\ntime.sleep(30)\n")
    for p in (empty, sleeper):
        p.chmod(0o755)

    def run_mock(name, emu, extra, status):
        out = args.output / name
        cmd = [sys.executable, str(scripts / "stage1-run.py"), "--emu", str(emu),
               "--reference", str(mocks / "reference"), "--image", str(mocks / "image"),
               "--flash", str(mocks / "flash"), "--identity", str(mocks / "identity.json"),
               "--runtime-home", str(mocks), "--output", str(out), "--timeout", "1", *extra]
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)
        (args.output / (name + ".log")).write_text(result.stdout)
        record = json.loads((out / "run.json").read_text())
        assert result.returncode != 0 and record["status"] == status, (name, result, record)
        results.append({"name": name, "status": "PASS", "runner_status": record["status"]})
        return cmd, out, record

    command, output, _ = run_mock("empty_output", empty, [], "CHECK_FAILED")
    original = (output / "run.json").read_bytes()
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)
    (args.output / "overwrite_attempt.log").write_text(result.stdout)
    assert result.returncode != 0 and original == (output / "run.json").read_bytes()
    results.append({"name": "refuse_overwrite", "status": "PASS"})
    run_mock("missing_wave", empty, ["--wave-begin", "0", "--wave-end", "100"], "WAVE_FAILED")
    _, _, timed = run_mock("timeout_cleanup", sleeper, [], "RUN_FAILED")
    assert timed["timed_out"] is True
    try:
        os.kill(timed["pid"], 0)
    except ProcessLookupError:
        pass
    else:
        raise AssertionError("Timed-out mock process still exists")

    if args.wave:
        wave = json.loads(args.wave.read_text())
        assert wave["status"] == "PASS"
        assert len(wave["fu_scopes"]) == 2
        instruction = int(wave["instruction"], 16)
        wave_checker.check_events(wave["events"], instruction)
        missing_scope = {name: item for name, item in wave["selected_signals"].items()
                         if not name.startswith(wave["fu_scopes"][0] + ".")}
        (args.output / "wave_missing_fu_scope.json").write_text(json.dumps(missing_scope, indent=2) + "\n")
        try:
            wave_checker.select_signals(missing_scope)
        except ValueError as error:
            results.append({"name": "wave_missing_fu_scope", "status": "PASS", "observed_rejection": str(error)})
        else:
            raise AssertionError("A waveform missing one of the two candidate FUs was accepted")
        selected = args.wave.with_name("selected.vcd")
        selected_raw = selected.read_bytes()
        assert digest(selected_raw) == wave["artifacts"]["selected.vcd"]["sha256"]

        def replay(content):
            with open(os.devnull, "w") as sink:
                return wave_checker.extract(io.StringIO(content), sink, int(wave["pc"], 16), instruction)

        replayed = replay(selected_raw.decode())
        assert replayed["events"] == wave["events"]
        assert wave_checker.check_events(replayed["events"], instruction) == wave["cases"]
        results.append({"name": "selected_vcd_replay", "status": "PASS", "events": len(replayed["events"])})
        lines = selected_raw.decode().splitlines(keepends=True)
        times = [i for i, line in enumerate(lines) if line.startswith("#")]
        assert len(times) >= 3
        gap = "".join(lines[:times[1]] + lines[times[2]:])
        signal = wave["cases"][0]["fu"] + ".io_in_bits_data_src_0"
        sample = wave["cases"][0]["input_wave_time"] - 1
        start = next(i for i in times if lines[i].strip() == f"#{sample}")
        stop = next(i for i in times if i > start)
        unknown = "".join(lines[:stop]) + "bx " + wave["selected_signals"][signal]["code"] + "\n" + "".join(lines[stop:])
        for name, content in (("wave_missing_half_cycle", gap), ("wave_unknown_active_operand", unknown)):
            (args.output / (name + ".vcd")).write_text(content)
            try:
                replay(content)
            except ValueError as error:
                results.append({"name": name, "status": "PASS", "observed_rejection": str(error)})
            else:
                raise AssertionError(name + " was accepted")
        mutations = {
            "wave_missing_commit": lambda events: events.pop(next(i for i, e in enumerate(events) if e["kind"] == "dpic_commit")),
            "wave_wrong_writeback": lambda events: next(e for e in events if e["kind"] == "fu_out").update(data="0" * 32),
            "wave_wrong_destination": lambda events: next(e for e in events if e["kind"] == "dpic_commit").update(wdest=4),
            "wave_wrong_rob": lambda events: next(e for e in events if e["kind"] == "dpic_commit").update(rob_value=1023),
            "wave_wrong_operand": lambda events: next(e for e in events if e["kind"] == "fu_in").update(src0="0" * 32),
            "wave_wrong_input_tag": lambda events: next(e for e in events if e["kind"] == "fu_in").update(pdest=256),
        }
        for name, mutate in mutations.items():
            events = copy.deepcopy(wave["events"])
            mutate(events)
            (args.output / (name + ".json")).write_text(json.dumps(events, indent=2) + "\n")
            try:
                wave_checker.check_events(events, instruction)
            except ValueError as error:
                results.append({"name": name, "status": "PASS", "observed_rejection": str(error)})
            else:
                raise AssertionError(name + " was accepted")
    summary = {"schema": "hello-vadd-tool-tests-v1", "status": "PASS", "hardware_cases_added": 0,
               "tool_sources": {p.name: digest(p.read_bytes()) for p in (Path(__file__),
                   scripts / "stage1-run.py", scripts / "stage1-wave.py", scripts / "summarize-run.py")},
               "fixture_run_sha256": digest((args.run / "run.json").read_bytes()), "checks": results}
    if args.wave:
        summary["fixture_wave_sha256"] = digest(args.wave.read_bytes())
    (args.output / "tests.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
