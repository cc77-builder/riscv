"""Read-only C3-HF local qualification and source binding; no EDA invocation."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

BASELINE = "0f12df675378556670afd0dd2153f47fcb330610"
CANDIDATE = "77d0a1228f0da7d584d5c7375b404dcda9763cf3"
EXU_SHA = "150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7"
EXU = "src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
EXTERNAL_SOURCE_ROOTS = (
    Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/r3-div-gate/c2/parent"),
    Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/r3-div-gate/c3-hf/validation"),
)
EXTERNAL_SOURCE_FILES = {Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/r3-div-gate/c2/check_generated_cone.py")}
CHECKS = {"fu", "parent", "supplement", "state", "source_scope",
          "replay", "negative_controls", "audit"}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def at(value, keys):
    need(isinstance(keys, list) and keys, "empty assertion path")
    for key in keys:
        value = value[key]
    return value

def verify_check_shape(name, check):
    assertions = check.get("assertions")
    need(isinstance(assertions, list) and assertions, "missing assertions: " + name)
    def passes(x):
        keys, value = x.get("keys"), x.get("equals")
        if not isinstance(keys, list) or not keys:
            return False
        return ((keys[-1] == "passed" and value is True) or
                (keys[-1] == "status" and isinstance(value, str) and
                 re.search(r"(?:^|_)PASS(?:_|$)", value) is not None and
                 not re.search(r"FAIL|REJECT|NOT_PASS|BLOCKED", value)))
    need(any(passes(x) for x in assertions), "no explicit passing assertion: " + name)

def validate(path, pins):
    path = Path(path).resolve()
    def pin(p, expected=None):
        p = Path(p).resolve()
        actual = sha(p)
        need(expected is None or actual == expected, "qualification input changed: " + str(p))
        pins[str(p)] = actual
        return p
    pin(path)
    q = json.loads(path.read_text())
    need(q.get("schema") == "C3_HF_COST_QUALIFICATION_V1", "qualification schema")
    c = q["candidate"]
    need(c["baseline"] == BASELINE, "wrong baseline")
    need(c["head"] == CANDIDATE and c["exeunit_sha256"] == EXU_SHA, "wrong frozen C3-HF identity")
    need(re.fullmatch(r"[0-9a-f]{40}", c["head"]) is not None, "missing candidate commit")
    need(c["head"] not in [BASELINE, "3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66",
                           "6704ce3502a7235cdb81697638c01ed23f6914f6"], "old candidate identity")
    need(re.fullmatch(r"[0-9a-f]{64}", c["exeunit_sha256"]) is not None, "missing ExeUnit identity")
    repo = Path(c["repo"]).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    need(head == c["head"], "candidate HEAD differs")
    need(not subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=repo, text=True).strip(),
         "candidate checkout is not clean")
    pin(repo / EXU, c["exeunit_sha256"])
    need(set(q["checks"]) == CHECKS, "missing/extra local qualification categories")
    for name, record in q["checks"].items():
        verify_check_shape(name, record)
        p = pin(record["path"], record["sha256"])
        value = json.loads(p.read_text())
        for assertion in record["assertions"]:
            got = at(value, assertion["keys"])
            expected = assertion["equals"]
            need(type(got) is type(expected) and got == expected,
                 "local check differs: " + name + "/" + repr(assertion["keys"]))
        if name == "audit":
            need(value.get("candidate_head") == head or value.get("candidate", {}).get("head") == head,
                 "independent local audit not bound to candidate")
    need(set(q["source_manifests"]) == {"fu", "parent", "supplement"},
         "three local source manifests required")
    for stage, record in q["source_manifests"].items():
        p = pin(record["path"], record["sha256"])
        sources = json.loads(p.read_text())
        need(isinstance(sources, dict) and sources, "empty source manifest: " + stage)
        if stage in {"parent", "supplement"}:
            need(sources.get(EXU) == c["exeunit_sha256"], "local source manifest is not C3: " + stage)
        for name, expected in sources.items():
            target = (repo / name).resolve()
            if not target.is_relative_to(repo):
                need(any(target.is_relative_to(allowed.resolve()) for allowed in EXTERNAL_SOURCE_ROOTS) or
                     target in {allowed.resolve() for allowed in EXTERNAL_SOURCE_FILES},
                     "source manifest escapes declared validation roots")
                need(q["inputs"].get(str(target)) == expected,
                     "external validation source not explicitly pinned in qualification.inputs")
            pin(target, expected)
    need(isinstance(q["inputs"], dict) and q["inputs"], "missing local input pins")
    for name, expected in q["inputs"].items():
        pin(name, expected)
    # Pin every orchestration source and contract before a tool is launched.
    for f in sorted(Path(__file__).parent.glob("*.py")):
        pin(f)
    pin(Path(__file__).parent / "CONTRACT.md")
    pin(Path(__file__).parent.parent / "CONTRACT.md")
    return q
