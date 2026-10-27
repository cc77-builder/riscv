#!/usr/bin/env python3
"""Run one hello/vadd image with explicit inputs and a durable receipt."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("emu", "reference", "image", "flash", "identity", "runtime-home", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--max-cycles", type=int, default=2000000)
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--wave-begin", type=int)
    parser.add_argument("--wave-end", type=int)
    args = parser.parse_args()
    if args.max_cycles <= 0 or args.timeout <= 0:
        parser.error("Positive cycle and timeout limits are required")
    wave = args.wave_begin is not None or args.wave_end is not None
    if wave and (args.wave_begin is None or args.wave_end is None or
                 not 0 <= args.wave_begin < args.wave_end <= args.max_cycles):
        parser.error("Require 0 <= wave-begin < wave-end <= max-cycles")
    paths = {key: getattr(args, key).resolve(strict=True)
             for key in ("emu", "reference", "image", "flash")}
    inputs = {key: {"path": str(path), "sha256": sha256(path)} for key, path in paths.items()}
    identity = json.loads(args.identity.read_text())
    if set(identity) != {"team_id", "host_ip", "status"}:
        parser.error("Unexpected identity manifest")
    aux_paths = {name: (args.runtime_home.resolve() / "build" / name).resolve(strict=True)
                 for name in ("constantin.txt", "plusArgs")}
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    work = out / "work"
    (work / "build").mkdir(parents=True)
    aux = {}
    for name, source in aux_paths.items():
        dest = work / "build" / name
        shutil.copyfile(source, dest)
        aux[name] = {"source": str(source), "sha256": sha256(dest)}
    log = out / "emulator-output.log"
    stderr = out / "emulator-stderr.log"
    command = [str(paths["emu"]), "-i", str(paths["image"]),
               "--flash=" + str(paths["flash"]), "--ram-size=128MB",
               "--diff=" + str(paths["reference"]), "--max-cycles=" + str(args.max_cycles)]
    if wave:
        command += ["--dump-wave-full", "--wave-path=" + str(out / "hello-vadd.fst"),
                    "-b", str(args.wave_begin), "-e", str(args.wave_end)]
    record = {"schema": "hello-vadd-run-v1", "status": "RUNNING", "started": now(),
              "command": command, "inputs": inputs, "identity": identity, "aux": aux,
              "cwd": str(work), "cpu_affinity": sorted(os.sched_getaffinity(0)),
              "timeout_seconds": args.timeout, "wave_window": [args.wave_begin, args.wave_end],
              "source_sha256": {p.name: sha256(p) for p in
                                  (Path(__file__), Path(__file__).with_name("summarize-run.py"))},
              "timed_out": False, "exit_code": None}
    receipt = out / "run.json"

    def save():
        temp = receipt.with_suffix(".tmp")
        temp.write_text(json.dumps(record, indent=2) + "\n")
        temp.replace(receipt)

    save()
    environment = dict(os.environ, NOOP_HOME=str(work))
    process = None
    start = time.monotonic()
    try:
        with log.open("xb") as stream, stderr.open("xb") as errors:
            process = subprocess.Popen(command, cwd=work, env=environment, stdout=stream,
                                       stderr=errors, start_new_session=True)
            record["pid"] = process.pid
            save()
            try:
                record["exit_code"] = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                record["exit_code"] = process.returncode
    except BaseException as error:
        record["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            record["exit_code"] = process.returncode
        record["finished"] = now()
        record["elapsed_seconds"] = round(time.monotonic() - start, 3)
        record["inputs_after"] = {key: {"path": str(path), "sha256": sha256(path)}
                                  for key, path in paths.items()}
        record["log_sha256"] = sha256(log) if log.exists() else None
        record["stderr_sha256"] = sha256(stderr) if stderr.exists() else None
        record["aux_after"] = {name: sha256(work / "build" / name) for name in aux}
        record["status"] = ("PROCESS_FINISHED" if record["exit_code"] == 0 and not record["timed_out"]
                            else "RUN_FAILED")
        save()
    if record["exit_code"] != 0 or record["timed_out"]:
        record["error"] = "timeout" if record["timed_out"] else "nonzero process exit"
        save()
        raise SystemExit("hello/vadd process failed; see run.json and original log")
    if wave:
        waveform = out / "hello-vadd.fst"
        if not waveform.is_file() or waveform.stat().st_size == 0:
            record.update(status="WAVE_FAILED", error="EMU produced no nonempty FST")
            save()
            raise SystemExit("No waveform produced; the EMU must be built with EMU_TRACE=fst")
        record["waveform"] = {"sha256": sha256(waveform), "bytes": waveform.stat().st_size}
        record["waveform_event_validation"] = "NOT_CHECKED"
        save()
    checker = Path(__file__).with_name("summarize-run.py")
    with (out / "run-summary.log").open("x") as summary:
        checked = subprocess.run([os.sys.executable, str(checker), str(log), "--receipt", str(receipt),
                                  "--stderr", str(stderr)],
                                 stdout=summary, stderr=subprocess.STDOUT)
    record["checker_exit_code"] = checked.returncode
    record["status"] = "PASS" if checked.returncode == 0 else "CHECK_FAILED"
    save()
    print((out / "run-summary.log").read_text(), end="")
    if checked.returncode:
        raise SystemExit(checked.returncode)


if __name__ == "__main__":
    main()
