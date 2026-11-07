#!/usr/bin/env python3
"""Derive one fixed P/whole2/plain-D/FR complete-Q288 image. No EMU."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import zipfile

CONTRACT = "r3-dot16-whole2-q288-v1"
BASE_ZIP_SHA = "9056f62f93718b2afbe1dcea103b15b64f70292ae27546b78f544bb2249915f9"
BASE_ELF_SHA = "216ed0418829bed5be00732670aed8d09532ca6f9615a68f9ea720fd05649fe5"
WHOLE2_ZIP_SHA = "4e1167fc4b1c635c56ef104201489c9f24e85af624ff0f0c73461e4b8fcbe05b"
WHOLE2_SOURCE_SHA = "df2983a21ab85d982b51e7faa0710d536d2bd4afe5bc9c2b91577dd3450972c8"
HELPER_SHA = "db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3"
MODEL_SHA = "703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82"
FULLMIN_SHA = "66c4c3af41f5c15c3228ce31c1bfc1be67e438e566d1def9499e6daa6b96e525"
WRAPPERS = ("q288_paired16_rvv", "q288_dot16_whole2", "q288_dot16_vdot", "q288_fused_rvv4")
FUNCTION_SHA = (
    "a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c",
    "b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6",
    "ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb",
    "66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab")
ORDER = (3, 0, 1, 2, 3, 3, 2, 1, 0, 3)
METHODS = (5, 0, 0, 5)
SOURCE_PINS = {
    "caller.h": "8f8ebbdfc64f506549b8fcb91700fc80dd91b1fd0a5be64aaed504ebcfa0c38e",
    "data.h": "65dd7fe726ebf49dd7d9cfb90e73e4e4d2c66775743e8ffd3af86571778051c5",
    "fused.S": "65f3f2b310a6f9c3e9a8b613e8dcafe41e9d2532ea5879ba6b3820492c7a2038",
    "gemv.S": "9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2",
    "kernels.S": "fd7c4278949db1b7a9d439f665bf67cf66cbdc7cbcd779800e4cdc8f792fc70f",
    "main.c": "d4df1b76da77b4b288e2cf9309d4dce075d6acc0d2b01fca654f5548b00c7346",
    "oracle.c": "6e72ed5b4e6b4ea804d34212e9e84d9001207eea076a26a8a835f2a1c29f9dec",
    "q288.c": "f0c557cb837ac05ff713b0eaadb7949b3ba623ae54fe1c02aedcd4220f5bf8d1",
    "q288.h": "f8e4df00dba860487c168f6990edbf2dc8814291b825d30762c7ecad61821cc2",
    "split.h": "94ccdc8e6212c0c0d7ef0e8795c8edcdc9a02e173802bea18965bbce5e01e222",
    "timers.S": "6f3d434048e270f99a5158e1890dfc8f8595c78d34eea5718f1f4749a0e7fa22"
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def change(raw, edits):
    text = raw.decode()
    for before, after in edits:
        need(text.count(before) == 1, "nonunique original source anchor: " + before)
        text = text.replace(before, after, 1)
    inverse = text
    for before, after in reversed(edits):
        need(inverse.count(after) == 1, "nonunique inverse source anchor: " + after)
        inverse = inverse.replace(after, before, 1)
    need(inverse.encode() == raw, "whole-source inverse differs")
    return text.encode(), dict(original_sha256=sha(raw), derived_sha256=sha(text.encode()),
                               edits=edits, original_reconstructed_byte_exact=True)


def call_plan():
    rows = [dict(stage=0, arm=i % 4, dataset=1 + i // 4) for i in range(8)]
    rows.append(dict(stage=0, arm=1, dataset=3))
    for arm in ORDER:
        rows.extend(dict(stage=stage, arm=arm, dataset=0) for stage in (1, 2))
    return rows


def inspect(elf_raw, base_raw, model):
    need(sha(base_raw) == BASE_ELF_SHA, "base ELF identity")
    elf, old = model.ELF(elf_raw), model.ELF(base_raw)
    rows = []
    for index, (name, pin) in enumerate(zip(WRAPPERS, FUNCTION_SHA)):
        data = elf.symbol_data(name)
        need(sha(data) == pin and len(data) > 0, "full machine function: " + name)
        if index != 1:
            need(data == old.symbol_data(name), "retained base machine function: " + name)
        else:
            need(len(data) == 412, "whole2 function length including unchanged +32 footer")
        rows.append(dict(name=name, address=hex(elf.symbols[name][0]),
                         bytes=len(data), sha256=sha(data)))
    table = struct.unpack("<4Q", elf.symbol_data("q_wrappers"))
    need(table == tuple(elf.symbols[n][0] for n in WRAPPERS), "actual wrapper addresses")
    arrays = {"q_order": ORDER, "q_methods": METHODS,
              "q_functional_order": (0, 1, 2, 3, 0, 1, 2, 3),
              "q_functional_datasets": (1, 1, 1, 1, 2, 2, 2, 2)}
    for name, expected in arrays.items():
        need(elf.symbol_data(name) == struct.pack("<" + "I" * len(expected), *expected),
             "actual control array: " + name)
    fixtures = {}
    for name in ("q_weights", "q_packed", "q_inputs", "q_weight_scale", "q_input_scale",
                 "q_golden", "q_min_packed", "q_min_x", "q_min_golden"):
        data = elf.symbol_data(name)
        need(len(data) > 0 and data == old.symbol_data(name), "unchanged data: " + name)
        fixtures[name] = dict(bytes=len(data), sha256=sha(data))
    need(fixtures["q_min_golden"]["sha256"] == FULLMIN_SHA, "independent fullmin golden")
    need(elf.symbol_data("q_min_packed")[16:-16] == bytes([128]) * 82944
         and elf.symbol_data("q_min_x")[16:-16] == bytes([128]) * 288, "fullmin signed inputs")
    retained = {}
    for name in ("split_measure", "q_fault_probe"):
        data = elf.symbol_data(name)
        need(data and data == old.symbol_data(name), "unchanged timer/probe machine bytes: " + name)
        retained[name] = dict(bytes=len(data), sha256=sha(data))
    words = [v[0] for v in struct.iter_unpack("<I", elf.symbol_data(WRAPPERS[2]))]
    sites = [i * 4 for i, word in enumerate(words) if word & 0xfe00707f == 0x0e00000b]
    need(len(sites) == 16 and not any(w & 0xfe00707f == 0x0200000b for w in words),
         "D contains exactly sixteen static dot16 sites and no dot8")
    return dict(functions=rows, wrapper_addresses=[hex(v) for v in table],
                arrays=arrays, unchanged_fixtures=fixtures, retained_machine_bytes=retained,
                d_static_sites=sites, d_function_bytes=484,
                expected_dot16_from_plan=67392, expected_probe_dot8_from_plan=1,
                retired_custom_count_verified=False, full_retirement_window_audited=False)


def build(args):
    sys.dont_write_bytecode = True
    os.sched_setaffinity(0, {args.cpu})
    out = args.output.resolve()
    need(args.output.is_absolute() and not out.exists(), "fresh absolute output required")
    paths = [args.base_archive.resolve(), args.whole2_archive.resolve(), args.helper.resolve(),
             Path(__file__).resolve(), Path(__file__).with_name("CONTRACT.md").resolve()]
    need(not any(p.is_relative_to(out) for p in paths), "output cannot contain inputs")
    for path, pin in zip(paths[:3], (BASE_ZIP_SHA, WHOLE2_ZIP_SHA, HELPER_SHA)):
        need(digest(path) == pin, "fixed input identity: " + str(path))
    before = {str(p): digest(p) for p in paths}
    out.mkdir(parents=True)
    inputs, source, objects = (out / n for n in ("inputs", "source", "objects"))
    for path in (inputs, source, objects):
        path.mkdir()
    status = dict(schema=1, contract=CONTRACT, status="BUILDING", cpu=args.cpu,
                  compile_workers=1, target_runtime_qualified=False, performance_qualified=False)
    save(out / "status.json", status)
    for p, name in zip(paths, ("base.zip", "whole2.zip", "process_helper.py", "image.py", "CONTRACT.md")):
        shutil.copyfile(p, inputs / name)
        need(digest(inputs / name) == before[str(p)], "snapshot differs: " + name)
    util = module(inputs / "process_helper.py", "dot16_q288_process_helper")
    status["started"] = util.stamp()
    commands = []
    proc = None
    try:
        with zipfile.ZipFile(inputs / "base.zip") as z:
            need(len(z.namelist()) == len(set(z.namelist())), "duplicate base ZIP entries")
            base_sources = {}
            for name, pin in SOURCE_PINS.items():
                raw = z.read("files/image-01/source/" + name)
                need(sha(raw) == pin, "frozen generated source: " + name)
                base_sources[name] = raw
                (source / name).write_bytes(raw)
            base_raw = z.read("files/image-01/paired16-target.elf")
            need(sha(base_raw) == BASE_ELF_SHA, "base actual ELF")
            (inputs / "base.elf").write_bytes(base_raw)
            old_build_raw = z.read("files/image-01/inputs/base-build.json")
            (inputs / "base-build.json").write_bytes(old_build_raw)
            old_build = json.loads(old_build_raw)
            model_raw = z.read("files/image-01/inputs/model.py")
            need(sha(model_raw) == MODEL_SHA, "frozen ELF reader")
            (inputs / "model.py").write_bytes(model_raw)
            base_manifest = json.loads(z.read("files/image-01/manifest.json"))
        with zipfile.ZipFile(inputs / "whole2.zip") as z:
            need(len(z.namelist()) == len(set(z.namelist())), "duplicate whole2 ZIP entries")
            whole2_raw = z.read("files/host-01/generated/whole2.S")
            need(sha(whole2_raw) == WHOLE2_SOURCE_SHA, "existing complete whole2 source identity")
            (inputs / "whole2.S").write_bytes(whole2_raw)
        whole2_text = whole2_raw.decode()
        matches = re.findall(r"(?ms)^\.global q288_dot16_whole2\n.*?^\.size q288_dot16_whole2, \.-q288_dot16_whole2\n", whole2_text)
        need(len(matches) == 1 and whole2_text.endswith(matches[0]),
             "unique complete existing whole2 function")
        append = "\n.option norvc\n.option norelax\n.text\n.balign 64\n" + matches[0]
        (source / "fused.S").write_bytes(base_sources["fused.S"] + append.encode())
        edits_main = [
            ("    q_wrappers[2](&q_context);", "    q_wrappers[1](&q_context);"),
            ("    record(0,2,3);", "    record(0,1,3);")]
        edits_data = [
            ('#define Q_CONTRACT "r3-dot16-q288-consumer-v1"',
             '#define Q_CONTRACT "' + CONTRACT + '"'),
            ("extern void q288_dot16_vdot(struct q288_context *);",
             "extern void q288_dot16_vdot(struct q288_context *);\nextern void q288_dot16_whole2(struct q288_context *);"),
            ("q_wrapper const q_wrappers[4] = {q288_paired16_rvv,q288_gs32_rvv,q288_dot16_vdot,q288_fused_rvv4};",
             "q_wrapper const q_wrappers[4] = {q288_paired16_rvv,q288_dot16_whole2,q288_dot16_vdot,q288_fused_rvv4};"),
            ("static const unsigned q_methods[4] __attribute__((aligned(16),used)) = {5,5,0,5};",
             "static const unsigned q_methods[4] __attribute__((aligned(16),used)) = {5,0,0,5};")]
        proofs = {}
        for name, edits in (("main.c", edits_main), ("data.h", edits_data)):
            changed, proof = change(base_sources[name], edits)
            (source / name).write_bytes(changed)
            proofs[name] = proof
        need((source / "fused.S").read_bytes()[:-len(append.encode())] == base_sources["fused.S"],
             "entire base assembly retained")
        proofs["fused.S"] = dict(original_sha256=sha(base_sources["fused.S"]),
            derived_sha256=digest(source / "fused.S"), appended_function_sha256=sha(matches[0].encode()),
            original_reconstructed_byte_exact=True, only_existing_whole2_appended=True)
        save(out / "derivation.json", proofs)
        plan = call_plan()
        manifest = dict(contract=CONTRACT, wrappers=WRAPPERS, methods=METHODS, order=ORDER,
            call_plan=plan, full_q_calls=29, windows=10, controls=5, checked_outputs=8352,
            calls_by_arm={name: sum(r["arm"] == i for r in plan) for i, name in enumerate(("P", "W", "D", "FR"))},
            fullmin=dict(dataset=3, arm=1, kind=0, output_sha256=FULLMIN_SHA),
            ordinary_fixture_sha256=base_manifest["ordinary_fixture_sha256"],
            expected_dot16_from_plan=67392, expected_dot8_probe_from_plan=1,
            retired_custom_count_verified=False, includes_quantization=False,
            actual_model_checkpoint=False, performance_qualified=False,
            target_runtime_qualified=False, full_retirement_window_audited=False,
            source_sha256={name: digest(source / name) for name in SOURCE_PINS})
        save(out / "manifest.json", manifest)
        for group in ("tools", "immutable_am_inputs"):
            for name, pin in old_build[group].items():
                need(digest(name) == pin, "original GNU/AM input: " + name)
                before[name] = pin
        save(out / "inputs.json", before)
        frozen_generated = {str(p): digest(p) for directory in (inputs, source)
                            for p in directory.iterdir() if p.is_file()}
        save(out / "generated-inputs.json", frozen_generated)
        first = old_build["commands"][0]["argv"]
        old_root = str(Path(next(a for a in first if a.endswith("/source/main.c"))).parent.parent)
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE="1", LANG="C.UTF-8", LC_ALL="C.UTF-8", TZ="UTC",
                   GIT_OPTIONAL_LOCKS="0", OMP_NUM_THREADS="1")
        need(len(old_build["commands"]) == 8, "original six units/link/objcopy command count")
        for index, row in enumerate(old_build["commands"]):
            argv = [a.replace(old_root, str(out)) for a in row["argv"]]
            need([a.replace(str(out), old_root) for a in argv] == row["argv"], "command inverse")
            need(str(Path(argv[0]).resolve()) in old_build["tools"], "bound GNU executable")
            started = time.monotonic()
            record = dict(argv=argv, cwd=str(out), started=util.stamp(), budget_seconds=120)
            commands.append(record)
            with (out / f"{index:02}-stdout.log").open("wb") as stdout, (out / f"{index:02}-stderr.log").open("wb") as stderr:
                proc = subprocess.Popen(argv, cwd=out, env=env, stdout=stdout, stderr=stderr,
                                        start_new_session=True)
                record["pid"] = proc.pid
                try:
                    record["exit_code"] = proc.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
                    record["timeout_cleanup_complete"] = util.stop_group(proc)
                    raise
            record["process_group_absent"] = not util.group_exists(proc.pid)
            record["elapsed_seconds"] = time.monotonic() - started
            record["finished"] = util.stamp()
            save(out / "commands.json", commands)
            need(record["exit_code"] == 0 and record["process_group_absent"], "GNU command failed")
        model = module(inputs / "model.py", "dot16_q288_frozen_elf")
        elf_path, binary = out / "paired16-target.elf", out / "paired16-target.bin"
        checked = inspect(elf_path.read_bytes(), base_raw, model)
        save(out / "elf-check.json", checked)
        need(all(digest(p) == h for p, h in before.items()), "original input changed")
        need(all(digest(p) == h for p, h in frozen_generated.items()), "frozen generated input changed")
        status.update(status="DOT16_WHOLE2_Q288_IMAGE_STATIC_PASS", elf=str(elf_path),
            elf_sha256=digest(elf_path), binary=str(binary), binary_sha256=digest(binary),
            inputs_unchanged=True, generated_inputs_unchanged=True,
            qualification="source derivation and real GNU ELF; no new guest executed")
    except BaseException as exc:
        status.update(status="FAILED", error=repr(exc))
        raise
    finally:
        if proc is not None:
            if util.group_exists(proc.pid):
                status["cleanup_complete"] = util.stop_group(proc)
            status["last_process_reaped"] = proc.poll() is not None
            status["last_process_group_absent"] = not util.group_exists(proc.pid)
        status["finished"] = util.stamp()
        save(out / "commands.json", commands)
        save(out / "status.json", status)
    print(json.dumps(status))
    return status


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-archive", required=True, type=Path)
    p.add_argument("--whole2-archive", required=True, type=Path)
    p.add_argument("--helper", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--cpu", required=True, type=int, choices=range(4))
    build(p.parse_args())
