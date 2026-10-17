"""Run a separately built T14 control sweep with the unchanged strict T12 gate."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main(args):
    args.output.mkdir(parents=True, exist_ok=False)
    pins = json.loads(args.pins.read_text())
    if sha(args.emu) != pins["emu_sha256"]:
        raise ValueError("EMU pin mismatch")
    expected = 2 if pins.get("VDOT_T14_FUSED_INPUT") == "1" else 3
    if args.latency != expected:
        raise ValueError("latency mismatch")
    image = args.build / "vdot-regression.bin"
    command = ["timeout", "120m", "stdbuf", "-o0", "-e0", str(args.emu),
               "-i", str(image), "--flash=" + str(args.flash), "--ram-size=128MB",
               "--diff=" + str(args.reference), "--max-cycles=5000000"]
    record = dict(name="control", status="RUNNING", started=datetime.datetime.now().astimezone().isoformat(),
                  command=command, files={str(path): sha(path) for path in
                      (args.emu, args.reference, args.flash, image)},
                  hardware_pins_sha256=sha(args.pins), latency=args.latency)
    save(args.output / "runtime.json", record)
    env = os.environ.copy()
    env.pop("XS_NEGATIVE_VECTOR_TARGET", None)
    with (args.output / "stdout.log").open("wb") as out, (args.output / "stderr.log").open("wb") as err:
        rc = subprocess.run(command, cwd=ROOT, env=env, stdout=out, stderr=err).returncode
    raw = {name: (args.output / name).read_bytes() for name in ("stdout.log", "stderr.log")}
    (args.output / "run.log").write_bytes(raw["stderr.log"] + raw["stdout.log"])
    (args.output / "exit-code.txt").write_text(str(rc) + "\n")
    record.update(exit_code=rc, raw_logs_sha256={name: hashlib.sha256(data).hexdigest() for name, data in raw.items()},
                  log_format="separate-streams-v1; derived run.log = stderr.log + stdout.log")
    try:
        if not all(sha(Path(name)) == digest for name, digest in record["files"].items()):
            raise ValueError("runtime input drift")
        text = (args.output / "run.log").read_text()
        if "The reference model is " + str(args.reference) not in text:
            raise ValueError("reference loader mismatch")
        spec = importlib.util.spec_from_file_location("t14_control", ROOT / "team/scripts/check-vdot-regression.py")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        result = checker.check(text, json.loads((args.build / "data/manifest.json").read_text()), rc, fu_latency=args.latency)
        save(args.output / "control-result.json", result)
        record["status"] = result["status"]
    except Exception as exc:
        record.update(status="FAILED", error=repr(exc))
    record["finished"] = datetime.datetime.now().astimezone().isoformat()
    save(args.output / "result.json", record)
    print(json.dumps(record))
    return 0 if record["status"] == "T12_CONTROL_REGRESSION_PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("build", "output", "emu", "pins", "reference", "flash"):
        parser.add_argument("--" + name, type=lambda x: Path(x).resolve(), required=True)
    parser.add_argument("--latency", type=int, choices=(2, 3), required=True)
    raise SystemExit(main(parser.parse_args()))
