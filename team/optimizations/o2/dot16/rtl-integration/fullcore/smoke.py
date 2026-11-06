#!/usr/bin/env python3
"""Build one six-case AM image, or run it once with the fixed feature1 reference."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

HELPER_SHA = "db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3"
GATE_SHA = "172551fb537e93f33937819b1a7625e39986726c039266750adadb73e8ccc05c"
REF_SHA = "cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae"
AM_HEAD = "086a238062fdfb3281b745a537b361983d0154b5"
AM_LIBS = {"am/build/am-riscv64-xs.a": "57501f59d55d1b15116d9022ffc2d5efcc74bcde8c5674d7f31db0714e04b933",
           "libs/klib/build/klib-riscv64-xs.a": "f45d8c2049384123642b8c5d4a86f46be285d785ac5d16438eee510347eafda1"}
FLASH_SHA = "1771e3e0ef670084df491c7e5fddd1ae189cc8e2ccd4ee6d4a4af585ac98eeb3"
REF_HEADER_SHA = "6a2ce3ab51893908f74452522ab03c553cf7fa7e8aa25f74ea84d79aa45f044d"
REF_API_SHA = "23056586264f8aacff65ba7ab5ceca6f8e5fddf680da8dd3e731c2a5673a7012"
EXPECTED_WORDS = [0x0294050b, 0x0e94040b, 0x0e94000b, 0x0e94048b, 0x0e00000b, 0x0294050b]
EXPECTED_LOW = [0, 131072, 262144, 0xfffc0800, 65064, 0xfffe0400]
EXPECTED_VL = [8, 16, 16, 16, 16, 8]
EXPECTED_ABI = dict(bytes=1400, regs_int=0, regs_fp=256, csr=512, pc=656,
                    hcsr=664, regs_vec=800, vcsr=1312, fcsr=1368, triggercsr=1376)
ARCH_TYPES = ("DifftestArchIntRegState", "DifftestArchFpRegState", "DifftestCSRState",
              "DifftestHCSRState", "DifftestArchVecRegState", "DifftestVecCSRState",
              "DifftestFpCSRState", "DifftestTriggerCSRState")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True)


def am_identity(am):
    require(git(am, "rev-parse", "HEAD").strip() == AM_HEAD, "AM source pin differs")
    require(not git(am, "status", "--porcelain=v1", "--untracked-files=normal"), "AM tracked/source state differs")
    names = git(am, "ls-files", "-z").split("\0")
    files = {n: sha(am / n) for n in names if n and (am / n).is_file()}
    for name, digest in AM_LIBS.items():
        require(sha(am / name) == digest, "frozen AM library differs: " + name)
        files[name] = digest
    return dict(root=str(am), head=AM_HEAD, files=files)


def audit_elf(disassembly, symbols):
    addresses = {parts[2]: int(parts[0], 16) for line in symbols.splitlines()
                 if len(parts := line.split()) == 3}
    inst = [(int(m[1], 16), int(m[2], 16))
            for m in re.finditer(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s", disassembly, re.M)]
    result = []
    for i, expected in enumerate(EXPECTED_WORDS):
        name = "dot16_smoke_case" + str(i)
        start, end = addresses[name], addresses[name + "_end"]
        words = [(pc, word) for pc, word in inst if start <= pc < end and word & 0x7f == 0x0b]
        require(len(words) == 1 and words[0][1] == expected, "ELF custom instruction differs in " + name)
        result.append(dict(case=i, begin=start, end=end, pc=words[0][0], word=hex(expected)))
    return result


def architectural_blocks(header):
    blocks = {}
    for m in re.finditer(r"typedef struct\s*\{([^{}]*)\}\s*(\w+)\s*;", header):
        if m[2] in ARCH_TYPES:
            require(m[2] not in blocks, "duplicate architectural state type")
            blocks[m[2]] = re.sub(r"\s+", " ", m[1]).strip()
    require(set(blocks) == set(ARCH_TYPES), "missing architectural state type")
    return blocks


def runtime_gate(text, ref, gate):
    gate.validate_failure_markers(text)
    plain = gate.normalize_console(text)
    require(re.search(r"CRITICAL ERROR|double trap|PMA check failed|DOT16_CORE_SMOKE_FAIL", plain, re.I) is None,
            "additional smoke/runtime failure marker")
    require("The first instruction of core 0 has commited. Difftest enabled." in plain, "missing real DiffTest banner")
    loaded = [x.strip() for x in re.findall(r"The reference model is ([^\r\n]+)", plain)]
    require(loaded == [str(ref)], "loaded reference differs or is ambiguous")
    require("HIT GOOD TRAP" in plain, "missing good trap")
    markers = [line for line in plain.splitlines() if "DOT16_CORE_SMOKE_" in line]
    expected = ["DOT16_CORE_SMOKE_BEGIN schema=1 cases=6 vlenb=16"]
    expected += [f"DOT16_CORE_SMOKE_CASE case={i} vl={EXPECTED_VL[i]} low={EXPECTED_LOW[i]:08x} high96=zero PASS"
                 for i in range(6)]
    final = "DOT16_CORE_SMOKE_PASS cases=6 dot8=2 dot16=4 failures=0"
    expected.append(final)
    require(markers == expected, "exact BEGIN, six cases and PASS sequence differs")
    return dict(cases=6, dot8=2, dot16=4, failures=0, loaded_reference=str(ref))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("image", "run"))
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cpu", type=int, choices=range(4), default=1)
    p.add_argument("--am", type=Path)
    p.add_argument("--build-record", type=Path)
    p.add_argument("--image-build", type=Path)
    p.add_argument("--reference", type=Path)
    p.add_argument("--reference-inputs", type=Path)
    args = p.parse_args()
    sys.dont_write_bytecode = True
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"
    repo, out = args.repo.resolve(), args.output.resolve()
    here = Path(__file__).resolve().parent
    helper = here.parent / "run_fu.py"
    require(sha(helper) == HELPER_SHA, "process helper identity changed")
    util = module(helper, "dot16_smoke_process_helper")
    require(args.output.is_absolute() and not out.exists() and not out.is_relative_to(repo)
            and not repo.is_relative_to(out), "output must be new and outside checkout")
    os.sched_setaffinity(0, {args.cpu})
    out.mkdir(parents=True)
    state = dict(schema=1, contract="dot16-production-fullcore-smoke-v1", mode=args.mode,
                 status="CAPTURING", started=util.stamp(), cpu=args.cpu, output=str(out),
                 fullcore_difftest_qualified=False, performance_measured=False, asic_ppa_qualified=False)
    proc, records = None, []
    env = {k: os.environ[k] for k in ("HOME", "PATH", "JAVA_HOME", "TEAM_XS_ENV_ROOT") if k in os.environ}
    env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", TZ="UTC", PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0")
    activated = "set -euo pipefail\nsource " + shlex.quote(str(repo / "team/scripts/activate.sh")) + "\n"

    def step(name, argv, cwd, budget=300, separate=False):
        nonlocal proc
        row = dict(name=name, command=argv, cwd=str(cwd), started=util.stamp(), budget_seconds=budget)
        state["active_step"] = name
        util.save(out / "status.json", state)
        stderr = (out / (name + ".stderr")).open("wb") if separate else subprocess.STDOUT
        try:
            with (out / (name + ".log")).open("wb") as stdout:
                proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                state["active_process_group"] = proc.pid
                util.save(out / "status.json", state)
                try:
                    row["exit_code"] = proc.wait(timeout=budget)
                except subprocess.TimeoutExpired:
                    row["timed_out"] = True
                    row["cleanup_complete"] = util.stop_group(proc)
                    raise RuntimeError(name + " timed out")
            require(not util.group_exists(proc.pid), "command left a live process group")
            row["process_group_absent"] = True
            require(row["exit_code"] == 0, name + " failed")
        finally:
            if separate:
                stderr.close()
            row["finished"] = util.stamp()
            records.append(row)
            util.save(out / "commands.json", records)

    try:
        frozen = {str(p): sha(p) for p in [Path(__file__), here / "CONTRACT.md", helper,
                 here / "main.c", here / "kernels.S", here / "Makefile", here / "abi_probe.cpp"]}
        snap = out / "source-snapshot"
        snap.mkdir()
        for path in frozen:
            shutil.copyfile(path, snap / Path(path).name)
            require(sha(snap / Path(path).name) == frozen[path], "source snapshot differs")
        util.save(out / "source-inputs.json", frozen)
        if args.mode == "image":
            require(args.am is not None, "image mode needs --am")
            am = args.am.resolve()
            before = am_identity(am)
            util.save(out / "am-before.json", before)
            flash = repo / "team/workloads/hello-vadd/boot-flash.S"
            require(sha(flash) == FLASH_SHA, "boot flash source changed")
            shutil.copyfile(flash, snap / "boot-flash.S")
            probe = "import json,hashlib,pathlib,shutil,subprocess; names=['make','riscv64-linux-gnu-gcc','riscv64-linux-gnu-as','riscv64-linux-gnu-ld','riscv64-linux-gnu-nm','riscv64-linux-gnu-objdump','riscv64-linux-gnu-objcopy']; r={}; "
            probe += "exec(\"for name in names:\\n p=pathlib.Path(shutil.which(name)).resolve(); r[name]=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),version=subprocess.check_output([str(p),'--version'],text=True))\"); "
            probe += "print(json.dumps(r))"
            step("tool-probe", ["bash", "-c", activated + "python3 -B -c " + shlex.quote(probe)], repo)
            tools = json.loads((out / "tool-probe.log").read_text())
            util.save(out / "tools.json", tools)
            shell = activated + "export AM_HOME=" + shlex.quote(str(am)) + "\n"
            make = [tools["make"]["path"], "-C", str(snap), "ARCH=riscv64-xs", "MARCH=rv64gcv", "-o", "am", "-o", "klib",
                    "SMOKE_OBJ_ROOT=" + str(out / "objects"), "BINARY=" + str(out / "dot16-core-smoke"), "-j1"]
            shell += shlex.join(make) + "\n"
            shell += shlex.join(["riscv64-linux-gnu-gcc", "-c", "-march=rv64gc", "-mabi=lp64d", str(snap / "boot-flash.S"), "-o", str(out / "boot-flash.o")]) + "\n"
            shell += shlex.join(["riscv64-linux-gnu-objcopy", "-O", "binary", "-j", ".text", str(out / "boot-flash.o"), str(out / "boot-flash.bin")]) + "\n"
            shell += shlex.join(["riscv64-linux-gnu-nm", "--defined-only", str(out / "dot16-core-smoke.elf")]) + " > " + shlex.quote(str(out / "symbols.txt")) + "\n"
            shell += "riscv64-linux-gnu-gcc --version\n"
            (out / "build-command.sh").write_text(shell)
            step("image-build", ["bash", str(out / "build-command.sh")], repo)
            require(am_identity(am) == before, "frozen AM sources/libraries changed")
            require(all(sha(t["path"]) == t["sha256"] for t in tools.values()), "image tool payload changed")
            checked = audit_elf((out / "dot16-core-smoke.txt").read_text(), (out / "symbols.txt").read_text())
            files = ["dot16-core-smoke.elf", "dot16-core-smoke.bin", "dot16-core-smoke.txt", "symbols.txt", "boot-flash.bin"]
            state.update(status="DOT16_SMOKE_IMAGE_PASS", am=before, compiled_cases=checked,
                         files={name: sha(out / name) for name in files}, flash_source_sha256=FLASH_SHA)
        else:
            require(all(x is not None for x in (args.build_record, args.image_build, args.reference, args.reference_inputs)),
                    "run needs build record, image build, reference and fixed reference inputs")
            build, image_dir, ref = args.build_record.resolve(), args.image_build.resolve(), args.reference.resolve()
            build_status = json.loads((build / "status.json").read_text())
            build_inputs = json.loads((build / "build-inputs.json").read_text())
            image_status = json.loads((image_dir / "status.json").read_text())
            require(build_status["status"] == "DOT16_FULLCORE_BUILD_PASS", "new EMU build did not pass")
            require(image_status["status"] == "DOT16_SMOKE_IMAGE_PASS", "new image build did not pass")
            require(sha(ref) == REF_SHA, "reference library differs")
            binary = Path(build_inputs["emu"]["path"])
            require(sha(binary) == build_inputs["emu"]["sha256"], "new EMU binary changed")
            for name, digest in image_status["files"].items():
                require(sha(image_dir / name) == digest, "image artifact changed: " + name)
            for group in ("hardware_files", "dependency_files"):
                for name, digest in build_inputs[group].items():
                    require(sha(repo / name) == digest, "build source differs: " + name)
            require(build_inputs["flags"].get("VDOT_DOT16") == "1", "new feature was not enabled")
            gate_path = repo / "team/optimizations/o1/audit/runtime_gate.py"
            require(sha(gate_path) == GATE_SHA, "generic runtime gate changed")
            gate = module(gate_path, "dot16_smoke_generic_runtime_gate")
            tools = json.loads((build / "tools.json").read_text())
            cxx = tools["cxx"]["path"]
            require(sha(cxx) == tools["cxx"]["sha256"], "ABI compiler changed")
            reference_header = args.reference_inputs.resolve() / "diffstate.h"
            reference_api = args.reference_inputs.resolve() / "reference_api.cpp"
            generated_header = repo / "build/generated-src/diffstate.h"
            generated_manifest = build / "generated-artifacts.json"
            require(sha(generated_manifest) == build_inputs["generated_manifest_sha256"],
                    "generated artifact manifest differs from the successful EMU build")
            header_entries = [entry for entry in json.loads(generated_manifest.read_text())
                              if entry["path"] == "build/generated-src/diffstate.h"]
            require(len(header_entries) == 1, "build manifest lacks one unambiguous DiffTest header")
            header_entry = header_entries[0]
            require(generated_header.stat().st_size == header_entry["bytes"]
                    and sha(generated_header) == header_entry["sha256"],
                    "current DiffTest header differs from the successful EMU build")
            require(sha(reference_header) == REF_HEADER_SHA and sha(reference_api) == REF_API_SHA,
                    "fixed API ABI evidence changed")
            actual_types = architectural_blocks(generated_header.read_text())
            require(actual_types == architectural_blocks(reference_header.read_text()),
                    "architectural state field order/types differ from the fixed API header")
            util.save(out / "abi-type-blocks.json", actual_types)
            includes = [repo / "build/generated-src", repo / "difftest/config",
                        repo / "difftest/src/test/csrc/common", repo / "difftest/src/test/csrc/difftest",
                        repo / "difftest/src/test/csrc/plugin/include"]
            abi_cmd = [cxx, "-std=c++17", "-DNUM_CORES=1", "-Wno-invalid-offsetof", *["-I" + str(p) for p in includes],
                       str(snap / "abi_probe.cpp"), "-o", str(out / "abi-probe")]
            step("abi-build", abi_cmd, repo)
            step("abi-run", [str(out / "abi-probe")], repo, budget=30)
            abi = json.loads((out / "abi-run.log").read_text())
            require(abi == EXPECTED_ABI, "new EMU register-copy layout differs from the fixed reference")
            util.save(out / "abi-layout.json", abi)
            image, flash = image_dir / "dot16-core-smoke.bin", image_dir / "boot-flash.bin"
            runtime_inputs = {str(path): sha(path) for path in (binary, image, flash, ref, gate_path,
                              build / "status.json", build / "build-inputs.json", image_dir / "status.json",
                              generated_header, reference_header, reference_api, generated_manifest)}
            runtime_inputs[str(generated_header)] = header_entry["sha256"]
            runtime_inputs[str(generated_manifest)] = build_inputs["generated_manifest_sha256"]
            util.save(out / "runtime-inputs.json", runtime_inputs)
            argv = [str(binary), "-i", str(image), "--flash=" + str(flash), "--ram-size=128MB",
                    "--diff=" + str(ref), "--max-cycles=300000", "--seed=1"]
            step("emulator", argv, repo, budget=600, separate=True)
            raw = (out / "emulator.stderr").read_bytes() + (out / "emulator.log").read_bytes()
            (out / "run.log").write_bytes(raw)
            checked = runtime_gate(raw.decode("utf-8", errors="strict"), ref, gate)
            require(all(sha(p) == h for p, h in runtime_inputs.items()), "runtime input changed")
            for group in ("hardware_files", "dependency_files"):
                require(all(sha(repo / n) == h for n, h in build_inputs[group].items()), "source changed during run")
            state.update(status="DOT16_FULLCORE_SMOKE_PASS", fullcore_difftest_qualified=True,
                         qualification_scope="one fixed six-legal-case AM image; no G3/performance/illegal-trap transfer",
                         checks=checked, abi_layout=abi, runtime_inputs=runtime_inputs,
                         raw_logs_sha256={n: sha(out / n) for n in ("emulator.log", "emulator.stderr", "run.log")})
        require(all(sha(path) == digest for path, digest in frozen.items()), "smoke source changed during operation")
        state["finished"] = util.stamp()
        util.save(out / "status.json", state)
        print(json.dumps({k: v for k, v in state.items() if k not in ("am", "runtime_inputs")}), flush=True)
        return 0
    except BaseException as exc:
        if proc is not None and util.group_exists(proc.pid):
            state["cleanup_complete"] = util.stop_group(proc)
        state.update(status="FAILED", fullcore_difftest_qualified=False, error=repr(exc), finished=util.stamp())
        util.save(out / "status.json", state)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
