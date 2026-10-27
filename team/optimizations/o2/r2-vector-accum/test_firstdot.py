"""Targeted firstdot transformation, parallel isolation and artifact rejection."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import firstdot_candidate as c
import firstdot_gate as g
import first_dot_probe as probe
import firstdot_experiment as experiment


def rejected(fn):
    try:
        fn()
    except (ValueError, AssertionError):
        return
    raise AssertionError("corrupt input was accepted")


def check(repo, build=None):
    g.bind(repo)
    assert g.sha(repo / c.REL / "first_dot_probe.py") == "0bb3de513d8a542829be8ca11f19b55b477ca3dff63949469fefe6978f1042d8"
    s1 = c.module("firstdot_test_s1", repo / c.REL / "candidate.py")
    base = s1.load_base(repo)
    count = 0
    for m, k in ((4, 8), (8, 32), (16, 64), (4, 13)):
        for software in ("basic", "reuse"):
            for method in ("vdot", "rvv"):
                for scope in ("core", "endtoend"):
                    body = s1.kernel(base, m, k, method, software, scope, "s1")
                    before = list(body)
                    transformed = c.first_dot(body, m, k, method, software)
                    assert transformed == probe.first_dot(body, m, k, method, software)
                    assert body == before
                    if method == "rvv":
                        assert transformed == body
                    elif k == 13:
                        extract = next(i for i, line in enumerate(transformed) if line.startswith("vmv.x.s"))
                        assert transformed[extract - 1] == "vsetivli zero, 4, e32, m1, tu, mu"
                    count += 1
    body = s1.kernel(base, 8, 32, "vdot", "reuse", "endtoend", "s1")
    changed = list(body)
    changed[changed.index(".word 0x03880a0b")] = ".word 0x03880a8b"
    rejected(lambda: c.first_dot(changed, 8, 32, "vdot", "reuse"))
    changed = list(body)
    changed.remove("vmv.v.i v0, 0")
    rejected(lambda: c.first_dot(changed, 8, 32, "vdot", "reuse"))
    sparse = experiment.inventory([3], [0]) + experiment.inventory([1], [1]) + experiment.inventory([5, 7], [2])
    repeat = [dict(name=experiment.name(i), replay=1) for i in sparse if i["dataset"] == 0]
    incomplete = experiment.qualification(sparse, repeat, True, True)
    assert not incomplete["full_matrix"] and not incomplete["all_window_replay"]
    full = experiment.inventory([1, 3, 5, 7], [0, 1, 2])
    full_repeat = [dict(name=experiment.name(i), replay=1) for i in full if i["dataset"] == 0]
    complete = experiment.qualification(full, full_repeat, True, True)
    assert complete["full_matrix"] and complete["all_window_replay"]
    rejected(lambda: experiment.outside_inputs(repo / "new-output", [repo]))
    rejected(lambda: experiment.outside_inputs(repo.parent, [repo]))
    malformed = dict(sparse[0], name="../escape", path=str(repo.parent / "escape"))
    rejected(lambda: experiment.validate_image(malformed, repo))
    with tempfile.TemporaryDirectory(prefix="firstdot-parallel-") as temp:
        root = Path(temp)
        items = [(s, d, v) for s in (1, 3, 5, 7) for d in range(3) for v in ("s1", "firstdot")]
        def generate(item, prefix):
            s, d, v = item
            out = root / f"{prefix}-{s}-{d}-{v}"
            manifest = c.generate(repo, out, v, d, s)
            assert manifest["firstdot_contract"] == c.CONTRACT and manifest["contract"] == c.HARNESS
            return (manifest, {name: (out / name).read_bytes() for name in c.FILES})
        serial = {i: generate(i, "serial") for i in items}
        with ThreadPoolExecutor(max_workers=4) as pool:
            actual = list(pool.map(lambda i: (i, generate(i, "parallel")), items))
        for i, value in actual:
            assert value == serial[i]
        for s in (1, 3, 5, 7):
            for d in range(3):
                left, right = serial[(s, d, "s1")], serial[(s, d, "firstdot")]
                assert left[0]["plan"] == right[0]["plan"]
                assert left[1]["cases.h"] == right[1]["cases.h"]
                assert left[1]["gemv.h"] == right[1]["gemv.h"]
    artifacts = []
    if build is not None:
        original = next(Path(i["path"]) for i in json.loads((build / "images.json").read_text())["images"]
                        if i["variant"] == "firstdot")
        g.verify_build(original, repo)
        with tempfile.TemporaryDirectory(prefix="firstdot-reject-") as temp:
            for case in ("manifest-contract", "manifest-body", "source-snapshot", "compiled-public"):
                dest = Path(temp) / case
                shutil.copytree(original, dest)
                if case.startswith("manifest"):
                    path = dest / "data/manifest.json"
                    value = json.loads(path.read_text())
                    if case == "manifest-contract":
                        value["firstdot_contract"] = c.HARNESS
                    else:
                        value["rows"][0]["body"][0] = "nop"
                    path.write_text(json.dumps(value, indent=2) + "\n")
                    receipt = json.loads((dest / "build.json").read_text())
                    receipt["artifacts"]["data/manifest.json"] = g.sha(path)
                    g.save(dest / "build.json", receipt)
                elif case == "source-snapshot":
                    path = dest / "source/repo" / c.REL / "firstdot_candidate.py"
                    path.write_bytes(path.read_bytes() + b"\n# changed\n")
                else:
                    path = dest / "gemv-reference.o"
                    elf = g.ELF(path.read_bytes())
                    raw = bytearray(path.read_bytes())
                    raw[elf.named[".text"][4] + 8] ^= 1
                    path.write_bytes(raw)
                    receipt = json.loads((dest / "build.json").read_text())
                    receipt["artifacts"]["gemv-reference.o"] = g.sha(path)
                    g.save(dest / "build.json", receipt)
                rejected(lambda: g.verify_build(dest, repo))
                artifacts.append(case)
    return dict(status="FIRSTDOT_TARGETED_TESTS_PASS", frozen_transform_comparisons=count,
                concurrent_generations=24, serial_generations=24, rejected_shape_drift=2,
                sparse_cohort_not_qualified=True, output_and_name_rejections=3,
                artifact_rejections=artifacts, live_difftest=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--build", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    value = check(a.repo.resolve(), a.build.resolve() if a.build else None)
    a.output.write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps(value))
