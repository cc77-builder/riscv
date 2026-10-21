"""Versioned fresh G3 inputs; the historical frozen route remains independent.

This contract changes input provenance, never the ISA, corpus, runtime gates or
coverage obligations. All paths refer to immutable files retained for replay.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

NAME = "o2-g3-current-inputs-v1"
ROLES = ("reference", "negative", "hello", "flash")
FIXTURE = "team/evidence/t12-regression-20261014/negative-fixture.c"
HELLO_SOURCES = tuple("team/workloads/hello-vadd/" + name for name in
                      ("main.c", "vadd.S", "Makefile", "boot-flash.S"))
MATRIX_HELPERS = ("team/scripts/vdot-tests.sh", "team/scripts/check-vdot-run.py",
                  "team/scripts/artifact_guard.py", "team/tests/generate_vdot_cases.py",
                  "team/tests/vdot_model.py")
MATRIX_DATA = ("cases.h", "cases.jsonl", "exceptions.json", "manifest.json", "stubs.h", "word-sites.S")
AM_LIBRARIES = ("am/build/am-riscv64-xs.a", "libs/klib/build/klib-riscv64-xs.a")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value),
            "invalid input contract digest")
    return value


def absolute(value, follow=True):
    require(isinstance(value, str) and Path(value).is_absolute(), "input contract path must be absolute")
    path = Path(value)
    require(".." not in path.parts and (str(path.resolve()) if follow else str(path)) == value,
            "input contract path must be canonical: " + value)
    return path


def inventory(value, label):
    require(isinstance(value, dict) and value, "missing " + label + " inventory")
    for name, expected in value.items():
        # AM has tracked, internal symlinks. Its complete strict Git audit
        # validates link targets; preserve those original inventory names.
        path = absolute(name, follow=False)
        require(sha(path) == digest(expected), label + " drift: " + name)
    return dict(value)


def git_source(root, revision, relative, files):
    path = root / relative
    require(str(path) in files, "missing committed build source: " + relative)
    body = subprocess.check_output(["git", "-C", str(root), "show", revision + ":" + relative])
    require(hashlib.sha256(body).hexdigest() == files[str(path)] == sha(path),
            "build source differs from recorded Git revision: " + relative)


def receipt(path, root, revision, contract_files):
    path = absolute(path)
    require(str(path) in contract_files, "build receipt is not bound by input contract")
    row = json.loads(path.read_text(encoding="utf-8"))
    require(row.get("status") == "BUILD_PASS" and row.get("source_commit") == revision,
            "wrong fresh input build status/source")
    files = inventory(row.get("files"), "build files")
    tools = inventory(row.get("tools"), "build tools")
    for name, expected in {**files, **tools}.items():
        require(contract_files.get(name) == expected, "build input not bound by contract: " + name)
    return row, files, tools


def bound_tool(command, tools, role=None):
    """Preserve the real recorded argv while binding PATH-resolved executable bytes."""
    selected = shutil.which(command)
    expected = shutil.which(role) if role else selected
    return (selected is not None and expected is not None and
            Path(selected).resolve() == Path(expected).resolve() and str(Path(selected).resolve()) in tools)


def hello_commands(paths, root):
    source = root / "team/workloads/hello-vadd"
    obj = paths["flash"].with_suffix(".o")
    return [
        ["-C", str(source), "ARCH=riscv64-xs", "MARCH=rv64gcv", "BINARY=" + str(paths["hello"].with_suffix("")), "-j1"],
        ["-c", "-march=rv64gc", "-mabi=lp64d", str(source / "boot-flash.S"), "-o", str(obj)],
        ["-O", "binary", "-j", ".text", str(obj), str(paths["flash"])],
    ]


def validate(path, paths, matrix, root):
    """Check fresh build provenance before the unchanged semantic input gates."""
    root = Path(root).resolve()
    path = absolute(str(path))
    require(not path.is_relative_to(root), "fresh input contract must be outside checkout")
    before = sha(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value.get("schema_version") == 1 and value.get("contract") == NAME,
            "unknown fresh input contract")
    revision = value.get("source_commit", "")
    require(isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision),
            "fresh input contract requires full source revision")
    require(subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", revision, "HEAD"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
            "fresh inputs source is not an ancestor of current checkout")
    selected = value.get("paths", {})
    sums = value.get("sha256", {})
    require(set(selected) == set(ROLES) and set(sums) == {*ROLES, "matrix"},
            "fresh input role inventory mismatch")
    files = inventory(value.get("files"), "contract files")
    for role in ROLES:
        require(absolute(selected[role]) == paths[role].resolve(), "selected input path mismatch: " + role)
        require(sha(paths[role]) == digest(sums[role]) == files.get(str(paths[role])),
                "fresh input image mismatch: " + role)
    matrix_sums = sums["matrix"]
    require(isinstance(matrix_sums, list) and len(matrix_sums) == 8, "fresh matrix requires eight shards")
    for index, expected in enumerate(matrix_sums):
        image = matrix / f"build-{index}/vdot-exceptions.bin"
        require(sha(image) == digest(expected) == files.get(str(image)), "fresh matrix image mismatch")
    for p in (paths["reference"].parents[1] / ".config", paths["reference"].parent / "vdot-provenance.json"):
        require(str(p) in files, "missing reference build provenance: " + str(p))
    receipts = value.get("receipts", {})
    require(set(receipts) == {"negative", "hello"}, "fresh input build receipts missing")
    negative, negative_files, negative_tools = receipt(receipts["negative"], root, revision, files)
    git_source(root, revision, FIXTURE, negative_files)
    fixture = str(root / FIXTURE)
    command = negative.get("command")
    require(isinstance(command, list) and all(isinstance(word, str) for word in command),
            "missing negative compiler command")
    required = ["-shared", "-fPIC", "-O2", "-Wall", "-Wextra", "-Werror",
                '-DREF_SO="' + str(paths["reference"]) + '"', fixture, "-ldl", "-Wl,--no-as-needed",
                str(paths["reference"]), "-o", str(paths["negative"])]
    require(len(command) == len(required) + 1 and command[1:] == required and bound_tool(command[0], negative_tools, "gcc"),
            "negative command must bind the exact trusted fixture and linked reference")
    require(negative.get("reference_sha256") == sums["reference"] and
            all(negative_files.get(str(paths[role])) == sums[role] for role in ("reference", "negative")),
            "negative reference identity mismatch")
    hello, hello_files, hello_tools = receipt(receipts["hello"], root, revision, files)
    for name in HELLO_SOURCES:
        git_source(root, revision, name, hello_files)
    require(str(root / "team/workloads/hello-vadd/identity.h") in hello_files,
            "hello generated identity is not captured")
    commands = hello.get("commands")
    require(isinstance(commands, list) and len(commands) == 3 and all(
        isinstance(cmd, list) and cmd and all(isinstance(word, str) for word in cmd)
        and cmd[1:] == expected and bound_tool(cmd[0], hello_tools, role)
        for cmd, expected, role in zip(commands, hello_commands(paths, root),
                                      ("make", "riscv64-linux-gnu-gcc", "riscv64-linux-gnu-objcopy"))),
        "hello commands must build the selected images with bound executable tools")
    require(all(hello_files.get(str(paths[role])) == sums[role] for role in ("hello", "flash")),
            "hello/flash output not bound by build receipt")
    require(str(paths["hello"].with_suffix(".elf")) in hello_files and
            str(paths["flash"].with_suffix(".o")) in hello_files and
            all(str(Path(hello.get("am_home", "")) / name) in hello_files for name in AM_LIBRARIES),
            "hello build must capture ELF and AM libraries")
    am = hello.get("am_home")
    require(am is not None and hello.get("am_revision") == "086a238062fdfb3281b745a537b361983d0154b5"
            and isinstance(hello.get("am_source_sha256"), dict) and hello["am_source_sha256"],
            "hello AM source provenance missing")
    # The caller runs the established strict AM source auditor, not just hashes
    # of whatever files an untrusted manifest happened to enumerate.
    absolute(am)
    for name, expected in hello["am_source_sha256"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts, "invalid AM source path")
        require(files.get(str(Path(am) / relative)) == digest(expected),
                "AM source is not retained in runtime contract: " + name)
    supplements = value.get("supplements", {})
    require(isinstance(supplements, dict) and set(supplements) <= {"diagnostic", "control"},
            "unknown fresh supplement role")
    for kind, spec in supplements.items():
        require(isinstance(spec, dict) and set(spec) == {"build", "sha256"}, "invalid supplement binding")
        build = absolute(spec["build"])
        image = build / ("o2-diag.bin" if kind == "diagnostic" else "o2-control.bin")
        require(sha(image) == digest(spec["sha256"]) == files.get(str(image)), "fresh supplement image mismatch")
        require(str(build / "build.json") in files, "fresh supplement receipt not bound")
    require(sha(path) == before, "input contract changed while being checked")
    inventory(files, "contract files after validation")
    return value, {**files, str(path): before}


def verify_am(value, guard):
    hello = json.loads(Path(value["receipts"]["hello"]).read_text(encoding="utf-8"))
    actual = guard.audit_repo(hello["am_home"], hello["am_revision"],
                             source_roots=("am/src", "am/include", "libs/klib/src", "libs/klib/include"))
    require(actual == hello["am_source_sha256"], "hello AM source changed after build")


def bind_reference(value, reference, provenance):
    """Retain every source/config/system header already authenticated by NEMU's guard."""
    files = value["files"]
    source_root = reference.parents[1]
    require(isinstance(provenance.get("source_sha256"), dict) and provenance["source_sha256"],
            "missing NEMU compiler input inventory")
    for name, expected in provenance["source_sha256"].items():
        path = Path(name[len("@system/"):]) if name.startswith("@system/") else source_root / name
        require(files.get(str(path)) == digest(expected), "NEMU source absent from runtime contract: " + name)


def bind_matrix(value, root, build, provenance):
    """New binaries must originate from the entire committed matrix program."""
    root, build = Path(root).resolve(), Path(build).resolve()
    revision, files = value["source_commit"], value["files"]
    directory = "team/workloads/vdot-exceptions"
    names = subprocess.check_output(["git", "-C", str(root), "ls-tree", "-r", "--name-only",
                                     revision, "--", directory], text=True).splitlines()
    required = [name for name in names if Path(name).parent.as_posix() == directory and
                (Path(name).suffix in (".c", ".S", ".h") or Path(name).name in ("Makefile", "virt.ld"))]
    require(required, "missing committed matrix program")
    required += list(MATRIX_HELPERS)
    sources = provenance.get("source_sha256", {})
    require(set(sources) == {str(root / name) for name in required}, "matrix source inventory must be complete")
    for name in required:
        git_source(root, revision, name, sources)
    require(files.get(str(build / "workload-provenance.json")) == sha(build / "workload-provenance.json"),
            "matrix build receipt absent from runtime contract")
    require(re.fullmatch(r"build-[0-7]", build.name), "unexpected fresh matrix build path")
    data = build.parent / ("data-" + build.name.split("-")[1])
    require(provenance.get("data_dir") == str(data), "matrix data path differs from selected shard")
    am = absolute(provenance["am_home"])
    expected_inventories = {
        "inputs_sha256": {str(data / name) for name in MATRIX_DATA},
        "images_sha256": {str(build / ("vdot-exceptions" + suffix)) for suffix in (".bin", ".elf")},
        "am_libraries_sha256": {str(am / name) for name in AM_LIBRARIES},
    }
    for group, expected in expected_inventories.items():
        require(set(provenance.get(group, {})) == expected, "incomplete matrix " + group + " inventory")
    for group in ("source_sha256", "inputs_sha256", "images_sha256", "am_libraries_sha256"):
        entries = provenance.get(group)
        require(isinstance(entries, dict) and entries, "missing matrix " + group)
        for name, expected in entries.items():
            require(files.get(name) == digest(expected), "matrix input absent from runtime contract: " + name)
    require(provenance.get("am_rev") == "086a238062fdfb3281b745a537b361983d0154b5" and
            isinstance(provenance.get("am_source_sha256"), dict) and provenance["am_source_sha256"],
            "matrix AM source inventory missing")
    for name, expected in provenance["am_source_sha256"].items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts, "invalid matrix AM source path")
        require(files.get(str(am / name)) == digest(expected), "matrix AM source absent from runtime contract: " + name)
