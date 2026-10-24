"""Recheck the complete sealed full-only caller screen without any EMU.

Each campaign is restored and audited in a separate Python process because
the frozen caller engine is configured per case. Then recompute cross-image
layout, targeted rejections and the preregistered decisions from those copies.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

import checks
import screen

HERE = Path(__file__).resolve().parent
e, g = screen.e, screen.g


def need(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(name):
    path = PurePosixPath(name)
    need(name == path.as_posix() and not path.is_absolute() and name not in ("", ".") and
         ".." not in path.parts and "\\" not in name and ":" not in name, "unsafe evidence path")
    return path


def member(root, name, directory=False):
    rel = safe(name)
    path = root
    for part in rel.parts:
        path = path / part
        need(not path.is_symlink(), "linked evidence member or ancestor")
    resolved = path.resolve(strict=True)
    need(root.resolve() in resolved.parents, "evidence member escapes its root")
    kind = path.stat().st_mode
    need(stat.S_ISDIR(kind) if directory else stat.S_ISREG(kind), "evidence member type")
    return path


def support(path, root):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)), "duplicate support ZIP member")
        manifest = json.loads(archive.read("manifest.json"))
        expected = {"manifest.json"}
        for item in manifest["entries"]:
            rel = safe(item["path"])
            need(rel.parts[0] == "runtime" or rel.parts[0] in {"build-" + label + "-01" for label in checks.LABELS}, "support scope")
            name = str(rel)
            need(name not in expected, "duplicate support manifest path")
            expected.add(name)
            member = archive.getinfo(name)
            need(not member.is_dir() and member.external_attr >> 16 == 0o100644, "support file type")
            raw = archive.read(member)
            need(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "support bytes changed")
            target = root / name
            need(not target.exists(), "support target already exists")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        need(set(names) == expected, "support member inventory differs")
    return len(expected) - 1


def worker(label, archive, root):
    need(label in checks.LABELS, "unknown screen case")
    screen.configure("baseline" if label == "b4" else "hoisted", int(label[1]))
    screen.h.install()
    evidence = g.load("screen_recheck_evidence", e.HERE / "evidence.py")
    restored = root / ("restore-" + label)
    manifest = evidence.unpack(archive, restored)
    result = evidence.audit(restored / "build", restored / "run")
    need(result == read(archive / "original-audit.json"), "campaign raw audit differs")
    for role in ("build", "run"):
        target = root / (role + "-" + label + "-01")
        need(not target.exists(), "restored case collides")
        (restored / role).rename(target)
    restored.rmdir()
    return dict(label=label, audit=result, files=len(manifest["files"]),
                payload_sha256=manifest["payload_sha256"], raw_bytes=manifest["raw_bytes"])


def command(argv, log):
    with log.open("w") as stream:
        result = subprocess.run(list(map(str, argv)), stdout=stream, stderr=subprocess.STDOUT)
    need(result.returncode == 0, "recheck subprocess failed: " + log.read_text()[-6000:])


def context_observations(root, labels):
    """Post-hoc identity-bound observations, without changing selection rules.

    This bounded diagnostic supports individually retired custom instructions.
    Unsupported trace shapes produce UNAVAILABLE, not a changed gate verdict.
    The complete frozen raw audit has already run before this function.
    """
    observer = g.load("hoisted_context_observer", e.ROOT / "team/optimizations/o2/fullcore/analyze.py")
    counter = g.load("hoisted_context_counter", e.ROOT / "team/workloads/unified-vdot/check.py")

    def one(directory, manifest):
        validation = read(directory / "validation.json")
        stderr, stdout = ((directory / name).read_text() for name in ("stderr.log", "stdout.log"))
        events, _ = observer.extract_events_and_uart(stderr + stdout)
        allocations, accepts, responses, commits = {}, {}, {}, {}
        rob_of = lambda item: tuple(map(int, item["rob"].split(":")))
        identity = lambda item: (item["seq"], rob_of(item), item["pdest"])
        for _, _, kind, item in events:
            if kind == "ENQUEUE":
                allocations.setdefault(rob_of(item), []).append(item)
            elif kind == "RESPONSE":
                need(identity(item) not in responses, "diagnostic duplicate response identity")
                responses[identity(item)] = item
            elif kind == "COMMIT":
                key = (item["cycle"], rob_of(item), item["pc"])
                need(key not in commits, "diagnostic duplicate commit identity")
                commits[key] = item
        times = {rob: [item["cycle"] for item in rows] for rob, rows in allocations.items()}
        need(all(len(values) == len(set(values)) for values in times.values()), "diagnostic ambiguous allocation generation")
        for _, _, kind, item in events:
            if kind != "ACCEPT":
                continue
            rob = rob_of(item)
            position = bisect_right(times.get(rob, []), item["cycle"]) - 1
            need(position >= 0, "diagnostic accept without allocation")
            key = (rob, position)
            need(key not in accepts, "diagnostic duplicate allocation acceptance")
            accepts[key] = item
        windows, active = [], None
        for item in counter.parse_events(stderr)["RETIRE"]:
            if item["word"] == counter.START:
                need(active is None, "diagnostic nested marker")
                active = []
            if active is not None:
                active.append(item)
            if item["word"] == counter.STOP:
                need(active is not None, "diagnostic unbound stop marker")
                windows.append(active)
                active = None
        need(active is None and len(windows) == len(validation["samples"]) == 36, "diagnostic window inventory")
        rows = []
        for sample, retired in zip(validation["samples"], windows):
            if sample["method"] != "vdot" or sample["phase"] != "measured":
                continue
            start, end = sample["sample_ticks"][1:3]
            need(end - start == sample["cycles"], "diagnostic clock mismatch")
            dots = [item for item in retired if item["word"] & manifest["custom_mask"] == manifest["custom_match"]]
            need(len(dots) == 32 and all(item["count"] == 1 for item in dots),
                 "diagnostic requires 32 individually retired vdot instructions")
            a, r, c = [], [], []
            for item in dots:
                rob = (item["flag"], item["rob"])
                commit = commits.get((item["cycle"], rob, item["pc"]))
                need(commit is not None, "diagnostic T13/O2 commit identity mismatch")
                # The original O2 auditor processes commits before same-cycle
                # reallocation. Select the preceding allocation generation.
                position = bisect_left(times.get(rob, []), commit["cycle"]) - 1
                need(position >= 0, "diagnostic commit without preceding allocation")
                allocation = allocations[rob][position]
                need(all(allocation[k] == commit[k] for k in ("rob", "pc", "ftq")),
                     "diagnostic commit allocation identity mismatch")
                accept = accepts.get((rob, position))
                need(accept is not None, "diagnostic committed instruction without acceptance")
                response = responses.get(identity(accept))
                need(response is not None and accept["cycle"] < response["cycle"] <= commit["cycle"],
                     "diagnostic committed response order")
                a.append(accept); r.append(response); c.append(commit)
            need(len({identity(item) for item in a}) == 32, "diagnostic repeated committed transaction")
            latencies = [response["cycle"] - accept["cycle"] for accept, response in zip(a, r)]
            first, last = min(item["cycle"] for item in a), max(item["cycle"] for item in r)
            # No time filter is used to assign transactions. Preserve and flag
            # events outside CSR bounds if that is what the raw identity says.
            outside = sum(not (start <= accept["cycle"] <= response["cycle"] < end)
                          for accept, response in zip(a, r))
            rows.append(dict(seq=sample["seq"], dataset=sample["dataset"], repeat=sample["repeat"],
                             cycles=sample["cycles"], before_first_accept=first - start,
                             accept_span=max(item["cycle"] for item in a) - first,
                             response_envelope=last - first, after_last_response=end - last,
                             last_commit_from_start=max(item["cycle"] for item in c) - start,
                             transactions_outside_counter_bounds=outside,
                             response_latency_histogram={str(k): v for k, v in sorted(Counter(latencies).items())}))
        need(len(rows) == 12, "diagnostic formal sample count")
        fields = ("cycles", "before_first_accept", "response_envelope", "after_last_response")
        return dict(status="CONTEXT_OBSERVATIONS_AVAILABLE", windows=rows, by_dataset=[dict(dataset=d, **{
            field: sum(row[field] for row in rows if row["dataset"] == d) for field in fields}) for d in range(3)])

    cases = {}
    for label in labels:
        directory = root / ("run-" + label + "-01/runs")
        manifest = read(root / ("build-" + label + "-01/source/manifest.json"))
        try:
            normal, replay = one(directory / "recovery", manifest), one(directory / "replay", manifest)
            cases[label] = dict(status="CONTEXT_OBSERVATIONS_AVAILABLE", recovery=normal, replay=replay,
                                observations_identical=normal == replay)
        except ValueError as exc:
            cases[label] = dict(status="CONTEXT_OBSERVATIONS_UNAVAILABLE", reason=str(exc))
    return dict(scope="post-hoc formal full/vdot global-cycle observations of 32 retired instructions per window; selection rules unchanged",
                interpretation="first ACCEPT means the earliest acceptance among this window's retired vdot instructions, excluding squashed transactions; before/envelope/after partition the full window only when no transaction is outside counter bounds; otherwise values are signed coordinates; not separate pack/core/extract timings or causal attribution",
                parser_sha256=sha(e.ROOT / "team/optimizations/o2/fullcore/analyze.py"), cases=cases)


def audit(evidence):
    index = read(member(evidence, "index.json"))
    need(index["format"] == "hoisted-screen-v2-evidence-1", "unknown screen evidence format")
    for name, pin in index["helpers"].items():
        need(safe(name).name == name and sha(member(HERE, name)) == pin, "screen helper differs: " + name)
    need(set(index["helpers"]) == {"screen.py", "checks.py", "SCREEN_CONTRACT.md", "recheck.py"}, "helper scope")
    labels = [item["label"] for item in index["campaigns"]]
    need(len(labels) == len(set(labels)) and set(labels) in ({"b4", "h4"}, set(checks.LABELS)), "campaign scope")
    need(index["new_emu_runs"] == 3 * len(labels), "actual EMU count")
    support_file = member(evidence, index["support"]["path"])
    need(support_file.stat().st_size == index["support"]["bytes"] and sha(support_file) == index["support"]["sha256"], "support archive identity")
    with tempfile.TemporaryDirectory(prefix="hoisted-matrix-recheck-") as temporary:
        root = Path(temporary)
        support_count = support(support_file, root)
        cases = []
        for item in index["campaigns"]:
            label = item["label"]
            archive = member(evidence, item["path"], directory=True)
            need(set(item["files"]) == {"archive-manifest.json", "original-audit.json", "payload.zip"}, "campaign archive files")
            need({p.name for p in archive.iterdir()} == set(item["files"]), "campaign directory inventory")
            for name, meta in item["files"].items():
                path = member(archive, name)
                need(path.stat().st_size == meta["bytes"] and sha(path) == meta["sha256"], "campaign archive identity")
            output = root / (label + "-raw-recheck.json")
            command([sys.executable, "-B", __file__, "worker", "--label", label, "--archive", archive,
                     "--root", root, "--output", output], root / (label + "-raw-recheck.log"))
            cases.append(read(output))
        # The support ZIP includes complete builds for any unrun screen cases.
        fresh = checks.preflight(root, None)
        stored = read(root / "runtime/preflight-01.json")
        fresh.update(checker_sha256=sha(HERE / "checks.py"))
        fresh.pop("historical_reference")
        stored.pop("historical_reference")
        need(fresh == stored, "cross-image preflight differs")
        static_output = root / "binding-recheck.json"
        command([sys.executable, "-B", HERE / "checks.py", "rejections", "--root", root, "--output", static_output], root / "binding-recheck.log")
        need(read(static_output) == read(root / "runtime/rejections-01.json"), "binding rejections differ")
        for label in ("b4", "h4"):
            output = root / (label + "-selftest-recheck.json")
            command([sys.executable, "-B", HERE / "screen.py", "--caller", "baseline" if label == "b4" else "hoisted",
                     "--rvv", "4", "--repo", e.ROOT, "--action", "selftest", "--build", root / ("build-" + label + "-01"),
                     "--run", root / ("run-" + label + "-01"), "--output", output], root / (label + "-selftest-recheck.log"))
            need(read(output) == read(root / ("runtime/selftest-" + label + "-01.json")), "raw log rejection recheck differs")
        first = checks.stage1(root)
        first.update(checker_sha256=sha(HERE / "checks.py"))
        need(first == read(root / "runtime/stage1-01.json"), "stage1 decision differs")
        if first["decision"] == "CONTINUE_RVV_SCREEN":
            need(set(labels) == set(checks.LABELS), "missing expanded RVV campaigns")
            decision = checks.selection(root)
            decision.update(checker_sha256=sha(HERE / "checks.py"))
            decision = json.loads(json.dumps(decision))
            need(decision == read(root / "runtime/selection-01.json"), "selection decision differs")
        else:
            need(set(labels) == {"b4", "h4"}, "expanded despite stage1 stop")
            decision = first
        need(decision["decision"] == index["decision"], "index decision differs")
        observations = context_observations(root, labels)
    return dict(status="HOISTED_MATRIX_RECHECK_PASS", decision=decision["decision"],
                cases=cases, support_files=support_count, decision_details=decision,
                index_sha256=sha(evidence / "index.json"), verifier_sha256=sha(__file__),
                context_observations=observations,
                new_emu_runs=0, original_emu_runs=index["new_emu_runs"],
                physical_external_inputs_revalidated=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    normal = sub.add_parser("audit")
    normal.add_argument("evidence", type=Path)
    normal.add_argument("--output", type=Path, required=True)
    child = sub.add_parser("worker")
    child.add_argument("--label", required=True)
    child.add_argument("--archive", type=Path, required=True)
    child.add_argument("--root", type=Path, required=True)
    child.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists(), "output must be new")
    if args.action == "audit":
        need(not args.evidence.is_symlink(), "linked evidence root")
        evidence = args.evidence.resolve()
        need(evidence not in args.output.resolve().parents, "output inside sealed evidence")
        result = audit(evidence)
    else:
        result = worker(args.label, args.archive.resolve(), args.root.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
