"""Qualify V2 source selection and a relocatable firstdot library package.

The frozen firstdot C audit runs unchanged, including its single complete matrix
audit. A private adapter observes that returned matrix to derive the selection.
Real GNU builds then prove whole-object, caller and relocatable-link equivalence.
No EMU is started and no new final application performance is claimed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import types

REL = Path("team/optimizations/o2/r2-select")
S1 = Path("team/optimizations/o2/r2-vector-accum")
EVIDENCE = S1 / "evidence/firstdot-v1"
CONTRACT = "r5-selected-firstdot-gemv-v2"
IDENTITY = Path("team/optimizations/o2/repro/evidence/clean-reproduction-v1/reports/identity-02.json")
SHAPES = ((4, 8), (8, 32), (16, 64), (4, 13))
MATRIX_SHA = "0c8d3159c91aa3c934c7bfb7f2640906844246e812c0b5bfc556cdfb86d0d3b4"
C_SHA = "47859f1c12d5311ef554803c6976c8699ebafc164e2bdd876cfd0c6a6f2a2ec1"
OBJECT_SHA = "b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af"
REQUIRED_INPUTS = {
    str(REL / name) for name in (
        "verify_firstdot_stable.py", "FIRSTDOT_STABLE_CONTRACT.md", "public/firstdot/selected_gemv.h",
        "public/firstdot/Makefile", "public/firstdot/example.c", "STABLE_MANIFEST.json", "verify_stable.py",
        "public/gemv.S", "public/gemv.h", "public/selected_gemv.h", "public/Makefile")
} | {str(S1 / name) for name in (
    "firstdot/public/gemv.S", "firstdot/public/gemv.h", "firstdot_c_evidence.py", "firstdot_library.py")
} | {str(EVIDENCE / name) for name in (
    "matrix-archive/archive-manifest.json", "c-archive/archive-manifest.json", "library/library.json",
    "reports/c-audit-01.json", "reports/matrix-audit-01.json")
} | {str(IDENTITY)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat()


def hardware_identity(manifest, identity):
    """Bind the public hardware claim to the already hash-pinned T17 identity."""
    expected = dict(source_commit=identity["source_commit"],
                    emu_sha256=identity["hardware_profile"]["emu_sha256"],
                    reference_sha256=identity["reference_sha256"])
    require(manifest.get("hardware") == expected, "V2 manifest T17 hardware identity")
    return expected


def selection(matrix):
    """Derive deployed choices and the strongest comparator as separate facts."""
    require(matrix["status"] == "FIRSTDOT_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS" and
            matrix["contract"] == "r2-s1-firstdot-c-abi-v1" and
            matrix["qualification_scope"] == "matrix" and
            matrix["archive"]["archive_manifest_sha256"] == MATRIX_SHA and
            matrix["formal_images"] == 24 and matrix["measured_windows"] == 384 and
            matrix["all_window_replay_comparisons"] == 192, "firstdot matrix qualification")
    require([tuple(row["shape"]) for row in matrix["rows"]] == list(SHAPES), "matrix shape inventory")
    wanted = {(v, s, m) for v in ("s1", "firstdot") for s in ("basic", "reuse") for m in ("vdot", "rvv")}
    result = []
    for row in matrix["rows"]:
        require(row["datasets"] == [0, 1, 2] and row["scope"] == "endtoend-with-c-abi-call", "matrix measurement scope")
        candidates = row["candidates"]
        by_key = {(r["variant"], r["software"], r["method"]): r for r in candidates}
        require(len(candidates) == len(by_key) == 8 and set(by_key) == wanted, "complete comparison inventory")
        require(all(type(r["total"]) is int and r["total"] > 0 and r["samples"] == 12 and
                    r["mean"] == r["total"] / 12 for r in candidates), "candidate samples/arithmetic")
        fallback = by_key["firstdot", "reuse", "rvv"]
        default = min((by_key["firstdot", "reuse", m] for m in ("rvv", "vdot")), key=lambda r: r["total"])
        minimum = min(r["total"] for r in candidates)
        require(default["total"] == minimum, "deployed default is not a qualified minimum")
        rvv_min = min(r["total"] for r in candidates if r["method"] == "rvv")
        fair = sorted((dict(variant=r["variant"], software=r["software"], total=r["total"], mean=r["mean"])
                       for r in candidates if r["method"] == "rvv" and r["total"] == rvv_min),
                      key=lambda r: (r["variant"] != "s1", r["software"]))
        shape = tuple(row["shape"])
        if shape != (4, 13):
            require(default["method"] == "vdot" and default["total"] < rvv_min and
                    default["total"] < by_key["s1", "reuse", "vdot"]["total"], "vdot adoption gate")
        else:
            require(default["method"] == "rvv", "K13 must keep RVV")
        stem = "firstdot_gemv_%dx%d_reuse_" % shape
        result.append(dict(shape=list(shape), alias="xs_gemv_%dx%d" % shape,
            default_symbol=stem + default["method"], rvv_symbol=stem + "rvv",
            default_total=default["total"], default_mean=default["mean"],
            deployed_rvv_total=fallback["total"], deployed_rvv_mean=fallback["mean"],
            fastest_qualified_rvv=fair, samples_per_candidate=12,
            performance_scope="historical firstdot endtoend-with-c-abi-call windows"))
    return result


def raw_qualification(repo, output):
    sys.path.insert(0, str(repo / S1))
    import firstdot_c_evidence as ce
    import firstdot_library as library
    identity_path = repo / IDENTITY
    identity = ce.a.parent_identity(repo, identity_path)
    matrix = repo / EVIDENCE / "matrix-archive"
    c_archive = repo / EVIDENCE / "c-archive"
    parent, portable = ce.adapter(repo, identity, matrix)
    original_modules = parent.archive_modules
    observed = []

    def modules(root):
        evidence, archive_type = original_modules(root)
        proxy = types.SimpleNamespace(**vars(evidence))
        original_audit = proxy.audit

        def observe(*args, **kwargs):
            answer = original_audit(*args, **kwargs)
            observed.append(answer)
            return answer

        proxy.audit = observe
        return proxy, archive_type

    parent.archive_modules = modules
    proof = parent.audit_archive(repo, c_archive, matrix)
    require(len(observed) == 1, "capture exactly one unchanged matrix audit")
    require(proof["status"] == "R4_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS" and
            proof["matrix_status"] == observed[0]["status"] and
            proof["matrix_manifest_sha256"] == MATRIX_SHA and
            proof["archive"]["archive_manifest_sha256"] == C_SHA and
            proof["distinct_cases"] == 48 and proof["public_functions"] == 16 and
            proof["normal_case_executions"] == 96, "firstdot C qualification")
    report = dict(status="FIRSTDOT_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS", contract=ce.c.CONTRACT, proof=proof)
    save(output / "c-raw-audit.json", report)
    save(output / "matrix-raw-audit.json", observed[0])
    require(report == read(repo / EVIDENCE / "reports/c-audit-01.json") and
            observed[0] == read(repo / EVIDENCE / "reports/matrix-audit-01.json"), "raw audit differs from qualified evidence")
    sealed = portable.Archive(c_archive)
    obj = sealed.raw("build/gemv-reference.o")
    require(len(obj) == 27416 and hashlib.sha256(obj).hexdigest() == OBJECT_SHA, "qualified complete object")
    source = repo / S1 / "firstdot/public"
    require(all(sealed.raw("build/source/" + name) == (source / name).read_bytes()
                for name in ("gemv.S", "gemv.h")), "published firstdot source identity")
    library_result = library.byte_check(repo / EVIDENCE / "library")
    require(library_result["object_sha256"] == OBJECT_SHA and
            read(repo / EVIDENCE / "library/library.json")["c_archive_proof"] == proof, "library runtime binding")
    save(output / "qualified-library-check.json", library_result)
    return observed[0], obj, library


def caller_source(rows, force, aliases):
    lines = ['#include "' + ("selected_gemv.h" if aliases else "firstdot_gemv.h") + '"']
    if aliases:
        lines.append('_Static_assert(XS_GEMV_STABLE_API_VERSION == 2, "GEMV API V2 required");')
    for row in rows:
        for fallback in (False, True):
            target = row["rvv_symbol"] if force or fallback else row["default_symbol"]
            name = row["alias"] + ("_rvv" if fallback else "") if aliases else target
            lines.append("void call_%dx%d_%s(const int8_t *a, void *b) { %s(a, b); }" %
                         (*row["shape"], "rvv" if fallback else "default", name))
    return "\n".join(lines) + "\n"


def verify(args, output, started):
    repo = args.repo.resolve()
    require(Path(__file__).resolve() == repo / REL / "verify_firstdot_stable.py", "verifier checkout identity")
    manifest_path = repo / REL / "FIRSTDOT_STABLE_MANIFEST.json"
    manifest = read(manifest_path)
    manifest_hash = sha(manifest_path)
    require(manifest["contract"] == CONTRACT and manifest["api_version"] == 2, "V2 manifest contract")
    pins = manifest["input_sha256"]
    require(set(pins) == REQUIRED_INPUTS, "complete V2/frozen input inventory")
    for path, digest in pins.items():
        actual = (repo / path).resolve()
        require(actual.is_relative_to(repo) and not (repo / path).is_symlink() and sha(actual) == digest,
                "source/evidence pin: " + path)
    hardware = hardware_identity(manifest, read(repo / IDENTITY))
    matrix, qualified, library_module = raw_qualification(repo, output)
    rows = selection(matrix)
    require(rows == manifest["selection"], "manifest choices differ from raw qualified comparison")
    (output / "qualified-gemv.o").write_bytes(qualified)
    tools = {name: shutil.which(args.cross_prefix + name) for name in ("gcc", "ar", "ld", "nm", "readelf")}
    tools["make"] = shutil.which("make")
    require(all(tools.values()), "GNU toolchain missing")

    def run(folder, name, argv, success=True):
        folder.mkdir(parents=True, exist_ok=True)
        before = now()
        result = subprocess.run(argv, cwd=repo, capture_output=True, timeout=180)
        (folder / (name + ".stdout.log")).write_bytes(result.stdout)
        (folder / (name + ".stderr.log")).write_bytes(result.stderr)
        save(folder / (name + ".command.json"), dict(argv=argv, cwd=str(repo), started=before, finished=now(),
            exit_code=result.returncode, stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(result.stderr).hexdigest()))
        require((result.returncode == 0) == success, "unexpected GNU exit: " + name)
        return result.stdout

    versions = {k: dict(path=v, sha256=sha(v), version=run(output / "tools", k, [v, "--version"]).decode().splitlines()[0])
                for k, v in tools.items()}
    package = output / "package"
    run(output, "make-package", [tools["make"], "-C", str(repo / REL / "public/firstdot"),
        "OUT=" + str(package), "CROSS_COMPILE=" + args.cross_prefix, "-j1", "all"])
    require((package / "gemv.o").read_bytes() == qualified, "whole package object differs from qualified firstdot")
    archive = package / "libxs_gemv_firstdot.a"
    def check_archive(path):
        require(library_module.archive_member(path.read_bytes()) == qualified, "package archive member inventory/bytes")

    check_archive(archive)
    require((package / "include/firstdot_gemv.h").read_bytes() == (repo / S1 / "firstdot/public/gemv.h").read_bytes() and
            (package / "include/selected_gemv.h").read_bytes() == (repo / REL / "public/firstdot/selected_gemv.h").read_bytes(),
            "packaged headers differ")
    expected = {"firstdot_gemv_%dx%d_%s_%s" % (*shape, s, m) for shape in SHAPES
                for s in ("basic", "reuse") for m in ("vdot", "rvv")}
    symbols = run(output, "package-symbols", [tools["nm"], "-g", "--defined-only", str(package / "gemv.o")])
    require({line.split()[-1].decode() for line in symbols.splitlines()} == expected, "16 public functions without wrappers")
    run(output, "elf-symbols", [tools["readelf"], "--wide", "--syms", str(package / "gemv.o")])
    flags = ["-std=c11", "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-ffreestanding", "-O2", "-g0",
             "-fno-pic", "-fno-pie", "-fno-asynchronous-unwind-tables", "-fno-tree-vectorize"]

    def mode(force):
        folder = output / ("force-" + ("default" if force is None else str(force)))
        for kind in ("alias", "explicit"):
            target = folder / kind
            target.mkdir(parents=True)
            (target / "caller.c").write_text(caller_source(rows, force, kind == "alias"), encoding="utf-8")
            options = [] if force is None else ["-DXS_GEMV_FORCE_RVV=" + str(force)]
            run(target, "compile", [tools["gcc"], *flags, *options, "-I" + str(package / "include"),
                "-c", str(target / "caller.c"), "-o", str(target / "caller.o")])
            run(target, "link", [tools["ld"], "-r", "--no-relax", str(target / "caller.o"), str(archive),
                "-o", str(target / "linked.o")])
            require(not run(target, "undefined", [tools["nm"], "-u", str(target / "linked.o")]).strip(), "unresolved package consumer")
        require(all((folder / "alias" / name).read_bytes() == (folder / "explicit" / name).read_bytes()
                    for name in ("caller.o", "linked.o")), "alias/explicit whole objects differ")
        wanted = {r["rvv_symbol"] for r in rows} | ({r["default_symbol"] for r in rows} if not force else set())
        actual = run(folder, "targets", [tools["nm"], "-u", str(folder / "alias/caller.o")])
        require({line.split()[-1].decode() for line in actual.splitlines()} == wanted, "actual alias target inventory")
        return dict(force_rvv=force, aliases=8, targets=sorted(wanted), caller_sha256=sha(folder / "alias/caller.o"),
            linked_sha256=sha(folder / "alias/linked.o"), whole_objects_identical=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        modes = list(pool.map(mode, (None, 0, 1)))
    require(all(modes[0][name] == modes[1][name] for name in ("caller_sha256", "linked_sha256")), "default/zero differ")
    tests = output / "configurations"
    tests.mkdir()
    source = tests / "caller.c"
    source.write_text('#include "selected_gemv.h"\n', encoding="utf-8")
    invalid = ["2", "-1", "true", "0+1", "true && true", "0||1", "00"]
    for index, value in enumerate(invalid):
        run(tests, "invalid-" + str(index), [tools["gcc"], *flags, "-I" + str(package / "include"),
            "-DXS_GEMV_FORCE_RVV=" + value, "-fsyntax-only", str(source)], success=False)
    header_cases = {
        "expanded-zero": ('#define CHOICE 0\n#define XS_GEMV_FORCE_RVV CHOICE\n#include "selected_gemv.h"\n', True),
        "expanded-one": ('#include <stdbool.h>\n#define XS_GEMV_FORCE_RVV true\n#include "selected_gemv.h"\n', True),
        "repeat-v2": ('#include "selected_gemv.h"\n#include "selected_gemv.h"\n', True),
        "v1-before-v2": ('#include "' + str(repo / REL / "public/selected_gemv.h") + '"\n#include "selected_gemv.h"\n', False),
        "v2-before-v1": ('#include "selected_gemv.h"\n#include "' + str(repo / REL / "public/selected_gemv.h") + '"\n', True),
    }
    for name, (body, accepted) in header_cases.items():
        # A rejection must come from the header itself, not from a test assertion.
        tail = ('_Static_assert(XS_GEMV_STABLE_API_VERSION == 2, "V2 required");\n' +
                'void call(const int8_t *a, void *b) { xs_gemv_4x8(a,b); }\n') if accepted else ''
        source.write_text(body + tail, encoding="utf-8")
        target = tests / (name + ".o")
        run(tests, name, [tools["gcc"], *flags, "-I" + str(package / "include"), "-c", str(source), "-o", str(target)], success=accepted)
        if accepted:
            wanted = "firstdot_gemv_4x8_reuse_" + ("rvv" if name == "expanded-one" else "vdot")
            refs = run(tests, name + "-targets", [tools["nm"], "-u", str(target)])
            require({line.split()[-1].decode() for line in refs.splitlines()} == {wanted}, "header ordering/expanded configuration target")
    # The frozen V1 verifier proves the rollback package and supplies its real library.
    rollback = output / "rollback-v1"
    run(output, "rollback-v1", [sys.executable, "-B", str(repo / REL / "verify_stable.py"), "--repo", str(repo),
        "--output", str(rollback), "--cross-prefix", args.cross_prefix])
    require(read(rollback / "result.json")["status"] == "R5_STABLE_SOURCE_ALIAS_BUILD_PASS", "V1 rollback qualification")
    wrong = tests / "wrong-library.o"
    run(tests, "wrong-library", [tools["ld"], "-r", "--no-relax", str(output / "force-default/alias/caller.o"),
        str(rollback / "library/libxs_gemv.a"), "-o", str(wrong)])
    unresolved = run(tests, "wrong-library-undefined", [tools["nm"], "-u", str(wrong)])
    require({line.split()[-1].decode() for line in unresolved.splitlines()} == set(modes[0]["targets"]),
            "wrong-library negative control must expose unresolved firstdot symbols")
    # Move only the distributable archive and headers; no repository-relative includes.
    moved = output / "relocated-sdk"
    shutil.copytree(package / "include", moved / "include")
    shutil.copyfile(archive, moved / archive.name)
    usage = repo / REL / "public/firstdot/example.c"
    (moved / "example.c").write_bytes(usage.read_bytes())
    for root in (package, moved):
        run(root, "example-compile", [tools["gcc"], *flags, "-I" + str(root / "include"), "-c",
            str(usage if root == package else moved / "example.c"), "-o", str(root / "example.o")])
        run(root, "example-link", [tools["ld"], "-r", "--no-relax", str(root / "example.o"),
            str(root / archive.name), "-o", str(root / "example-linked.o")])
        require(not run(root, "example-undefined", [tools["nm"], "-u", str(root / "example-linked.o")]).strip(), "relocated SDK unresolved")
    require(all((package / f).read_bytes() == (moved / f).read_bytes() for f in ("example.o", "example-linked.o")), "relocation changes consumer")
    # Targeted semantic controls bypass no production gate; hashes are recorded
    # again so these controls exercise the actual mapping/selection/object checks.
    negative = output / "semantic-negative"
    negative.mkdir()
    controls = []

    def rejects(name, action, artifacts):
        try:
            action()
        except ValueError as exc:
            controls.append(dict(name=name, error=str(exc), artifact_sha256={p.name: sha(p) for p in artifacts}))
        else:
            raise ValueError("semantic negative accepted: " + name)

    bad_selection = json.loads(json.dumps(manifest))
    bad_selection["selection"][0]["deployed_rvv_mean"] = 187.5
    bad_manifest = negative / "wrong-fallback-manifest.json"
    save(bad_manifest, bad_selection)
    rejects("rehash-wrong-fallback-mean", lambda: require(selection(matrix) == read(bad_manifest)["selection"],
            "manifest choices differ from raw qualified comparison"), [bad_manifest])
    altered = negative / "alias"
    shutil.copytree(package / "include", altered / "include")
    bad_header = altered / "include/selected_gemv.h"
    original = bad_header.read_text()
    old_target, new_target = "#define xs_gemv_8x32 firstdot_gemv_8x32_reuse_vdot", "#define xs_gemv_8x32 firstdot_gemv_8x32_basic_vdot"
    require(original.count(old_target) == 1, "negative alias mutation location")
    bad_header.write_text(original.replace(old_target, new_target))
    bad_caller = altered / "caller.c"
    bad_caller.write_text(caller_source(rows, None, True))
    run(altered, "compile", [tools["gcc"], *flags, "-I" + str(altered / "include"), "-c", str(bad_caller), "-o", str(altered / "caller.o")])
    rejects("rehash-wrong-alias-target", lambda: require((altered / "caller.o").read_bytes() ==
        (output / "force-default/explicit/caller.o").read_bytes(), "alias/explicit whole objects differ"), [bad_header, altered / "caller.o"])
    wrong_member = negative / "object"
    wrong_member.mkdir()
    shutil.copyfile(rollback / "library/gemv.o", wrong_member / "gemv.o")
    run(wrong_member, "archive", [tools["ar"], "rcsD", str(wrong_member / "wrong.a"), str(wrong_member / "gemv.o")])
    rejects("rehash-wrong-complete-object", lambda: check_archive(wrong_member / "wrong.a"), [wrong_member / "wrong.a"])
    missing = negative / "missing-header"
    missing.mkdir()
    shutil.copyfile(package / "include/selected_gemv.h", missing / "selected_gemv.h")
    run(missing, "compile", [tools["gcc"], *flags, "-I" + str(missing), "-fsyntax-only", str(usage)], success=False)
    save(negative / "result.json", dict(semantic_controls=controls, missing_header_compile_rejected=True))
    require(sha(manifest_path) == manifest_hash and all(sha(repo / p) == h for p, h in pins.items()), "inputs changed during qualification")
    result = dict(status="R5_FIRSTDOT_STABLE_SOURCE_PACKAGE_PASS", contract=CONTRACT, started=started, finished=now(),
        manifest_sha256=manifest_hash, verifier_sha256=sha(__file__), input_sha256=pins, selection=rows,
        hardware=hardware, manifest_hardware_bound_to_pinned_identity=True,
        qualified_object_sha256=OBJECT_SHA, library_object_sha256=sha(package / "gemv.o"), library_archive_sha256=sha(archive),
        whole_library_object_identical=True, public_functions=16, modes=modes, invalid_configurations_rejected=invalid,
        header_cases={name: accepted for name, (_, accepted) in header_cases.items()},
        semantic_negative_controls=controls, missing_header_compile_rejected=True,
        wrong_library_unresolved_symbols_detected=True, relocated_sdk_whole_consumer_identical=True,
        rollback_status=read(rollback / "result.json")["status"], tools=versions,
        cpu_affinity=sorted(os.sched_getaffinity(0)), parallel_workers=2, raw_matrix_audit_calls=1,
        new_emu_runs=0, new_nemu_runs=0, new_application_performance_qualified=False,
        scope="V2 source selection and library packaging equivalence; original firstdot runtime qualification only")
    save(output / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cross-prefix", default="riscv64-linux-gnu-")
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    require(os.name == "posix", "qualification requires Linux/WSL and GNU")
    require(not output.exists() and not output.is_relative_to(repo), "new output outside source required")
    require(not any(c.isspace() for c in str(output)) and re.fullmatch(r"[A-Za-z0-9_./-]+", args.cross_prefix), "output/toolchain path")
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    output.mkdir(parents=True)
    state = dict(status="R5_FIRSTDOT_STABLE_RUNNING", contract=CONTRACT, started=now(), new_emu_runs=0)
    save(output / "state.json", state)
    try:
        result = verify(args, output, state["started"])
        state["status"] = result["status"]
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = now()
        save(output / "state.json", state)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
