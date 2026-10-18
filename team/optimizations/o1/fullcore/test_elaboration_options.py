"""Probe the actually compiled VDotHandoff Scala object without invoking Mill.

A tiny Java source launcher calls the production methods in fresh processes.
This checks elaboration-option behavior, not RTL elaboration or hardware.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
KEYS = ("VDOT_O1_HANDOFF", "VDOT_T14_FUSED_INPUT", "VDOT_O1_TRACE",
        "VDOT_T12_TRACE", "VDOT_T13_TRACE")
SOURCE = "src/main/scala/xiangshan/backend/fu/wrapper/VDotHandoff.scala"
JAVA_SOURCE = r'''import xiangshan.backend.fu.wrapper.VDotHandoff;
class O1OptionProbe {
  public static void main(String[] args) {
    try {
      boolean trace = VDotHandoff.traceEnabled();
      boolean handoff = VDotHandoff.enabled();
      System.out.println("O1_OPTIONS_ALLOW handoff=" + (handoff ? 1 : 0) + " trace=" + (trace ? 1 : 0));
    } catch (IllegalArgumentException error) {
      System.out.println("O1_OPTIONS_REJECT " + error.getMessage());
      System.exit(10);
    }
  }
}
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_ref(ref):
    return Path(ref.split(":", 3)[3])


def cases():
    f = {"VDOT_T14_FUSED_INPUT": "1"}
    h = dict(f, VDOT_O1_HANDOFF="1")
    t = dict(f, VDOT_O1_TRACE="1")
    ht = dict(h, VDOT_O1_TRACE="1")
    return [
        ("default", {}, (0, 0)),
        ("explicit_zero", dict.fromkeys(KEYS, "0"), (0, 0)),
        ("t14", f, (0, 0)),
        ("legacy_t12", dict(f, VDOT_T12_TRACE="1"), (0, 0)),
        ("legacy_t13", dict(f, VDOT_T13_TRACE="1"), (0, 0)),
        ("legacy_t12_t13", dict(f, VDOT_T12_TRACE="1", VDOT_T13_TRACE="1"), (0, 0)),
        ("o1_handoff_no_trace", h, (1, 0)),
        ("t14_o1_trace", t, (0, 1)),
        ("t14_o1_trace_t13", dict(t, VDOT_T13_TRACE="1"), (0, 1)),
        ("o1_trace", ht, (1, 1)),
        ("o1_trace_t13", dict(ht, VDOT_T13_TRACE="1"), (1, 1)),
        ("o1_t12_no_new_trace", dict(h, VDOT_T12_TRACE="1"), "O1 handoff cannot use T12"),
        ("o1_t13_no_new_trace", dict(h, VDOT_T13_TRACE="1"), "T13 requires VDOT_O1_TRACE=1"),
        ("o1_t12_t13_no_new_trace", dict(h, VDOT_T12_TRACE="1", VDOT_T13_TRACE="1"), "O1 handoff cannot use T12"),
        ("o1_trace_t12", dict(ht, VDOT_T12_TRACE="1"), "frozen T12 observer schema"),
        ("o1_trace_t12_t13", dict(ht, VDOT_T12_TRACE="1", VDOT_T13_TRACE="1"), "frozen T12 observer schema"),
        ("t14_trace_t12", dict(t, VDOT_T12_TRACE="1"), "frozen T12 observer schema"),
        ("o1_missing_fused", {"VDOT_O1_HANDOFF": "1"}, "VDOT_O1_HANDOFF=1 requires"),
        ("o1_zero_fused", dict(h, VDOT_T14_FUSED_INPUT="0"), "VDOT_O1_HANDOFF=1 requires"),
        ("trace_missing_fused", {"VDOT_O1_TRACE": "1"}, "VDOT_O1_TRACE=1 requires"),
        ("trace_zero_fused", dict(t, VDOT_T14_FUSED_INPUT="0"), "VDOT_O1_TRACE=1 requires"),
        ("trace_invalid_fused", dict(t, VDOT_T14_FUSED_INPUT="2"), "VDOT_O1_TRACE=1 requires"),
        *[("invalid_trace_" + label, dict(f, VDOT_O1_TRACE=value), "VDOT_O1_TRACE must be 0 or 1")
          for label, value in (("two", "2"), ("empty", ""), ("text", "true"), ("negative", "-1"))],
        *[("invalid_handoff_" + label, dict(f, VDOT_O1_HANDOFF=value), "VDOT_O1_HANDOFF must be 0 or 1")
          for label, value in (("two", "2"), ("empty", ""), ("text", "true"), ("negative", "-1"))],
    ]


def main(output, java):
    output = output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        raise ValueError("use a fresh output directory outside the checkout")
    compile_json = ROOT / "out/xiangshan/compile.json"
    cp_json = ROOT / "out/xiangshan/compileClasspath.json"
    classes = decode_ref(json.loads(compile_json.read_text())["value"]["classes"])
    libraries = [decode_ref(ref) for ref in json.loads(cp_json.read_text())["value"]
                 if "/scala-library/" in ref and ref.endswith(".jar")]
    if len(libraries) != 1:
        raise ValueError("need exactly one compiled Scala runtime dependency")
    bound_files = [classes / ("xiangshan/backend/fu/wrapper/VDotHandoff" + suffix)
                   for suffix in (".class", "$.class")]
    bound_files += [libraries[0], compile_json, cp_json, ROOT / SOURCE, Path(__file__)]
    before = {str(p): digest(p) for p in bound_files}
    output.mkdir(parents=True)
    helper = output / "O1OptionProbe.java"
    helper.write_text(JAVA_SOURCE, encoding="utf-8")
    version = subprocess.run([java, "-version"], capture_output=True, text=True, check=True)
    (output / "java-version.log").write_text(version.stdout + version.stderr, encoding="utf-8")
    command = [java, "-Xmx64m", "-cp", str(classes) + os.pathsep + str(libraries[0]), str(helper)]
    result = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "source_sha256": before[str(ROOT / SOURCE)], "bound_files_sha256": before,
              "helper_sha256": digest(helper), "command": command, "cases": [],
              "scope": "actual compiled Scala option methods; no RTL elaboration or hardware execution"}
    for name, selected, expected in cases():
        env = {key: value for key, value in os.environ.items() if key not in KEYS}
        env.update(selected)
        proc = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
        (output / (name + ".stdout.log")).write_text(proc.stdout, encoding="utf-8")
        (output / (name + ".stderr.log")).write_text(proc.stderr, encoding="utf-8")
        if isinstance(expected, tuple):
            wanted = "O1_OPTIONS_ALLOW handoff=%d trace=%d\n" % expected
            passed = proc.returncode == 0 and proc.stdout == wanted and not proc.stderr
        else:
            passed = (proc.returncode == 10 and proc.stdout.startswith("O1_OPTIONS_REJECT ")
                      and expected in proc.stdout and proc.stdout.count("\n") == 1 and not proc.stderr)
        result["cases"].append(dict(name=name, flags=selected, expected=expected,
                                    exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr, passed=passed))
    result["bound_files_unchanged"] = all(digest(p) == before[str(p)] for p in bound_files)
    result["passed"] = sum(case["passed"] for case in result["cases"])
    result["total"] = len(result["cases"])
    result["status"] = ("O1_ELABORATION_OPTIONS_PASS" if result["passed"] == result["total"]
                        and result["bound_files_unchanged"] else "O1_ELABORATION_OPTIONS_FAIL")
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"], str(result["passed"]) + "/" + str(result["total"]), flush=True)
    return 0 if result["status"].endswith("PASS") else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--java", default=shutil.which("java"))
    args = parser.parse_args()
    if not args.java:
        parser.error("java is unavailable; source team/scripts/activate.sh first")
    raise SystemExit(main(args.output, args.java))
