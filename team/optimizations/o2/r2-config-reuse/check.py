"""Build and check config-reuse host evidence. Never launches an EMU.

Uses LLVM's actual assembler, the frozen GNU firstdot object as a byte anchor,
and the unchanged S1 architectural interpreter. ET_REL is not runtime evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import struct
import subprocess
import sys
import traceback

import candidate as c

MODEL_PINS = {
    str(c.S1 / "gate.py"): "ab07b578f5fe2dc7782ef9af64e722e051363d1dfddfcd0f1939efb209346b6d",
    "team/optimizations/o2/r2-safe-tail/machine_model.py": "8fb2ac208d8db9083464fb839c06b46ec365234d72b819822563830dad90171e",
    "team/optimizations/o2/r2-safe-tail/linked_gate.py": "96807465bfd97a483f31ce100e552e2b83c4d0edd59f9bf4d817c66abd80ec1f",
}
GNU_OBJECT = c.S1 / "evidence/firstdot-v1/library/gemv.o"
GNU_SHA = "b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af"
INIT_STATES = ((8, 8, 1, 0, 0, 0, 7), (1, 32, 2, 1, 1, 7, 0), (0, 16, 1, 1, 0, 15, 3))
CSR_NAMES = ("vl", "sew", "lmul", "ta", "ma", "vstart", "vcsr")


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def words(code):
    c.require(code and len(code) % 4 == 0, "nonempty fixed-width instructions required")
    result = [w for w, in struct.iter_unpack("<I", code)]
    c.require(all(w & 3 == 3 for w in result), "compressed instruction")
    return result


def erasure(before, after, proof):
    left, right = words(before), words(after)
    removed = {r["index"] for r in proof["removed"]}
    c.require(len(removed) == len(proof["removed"]) and len(left) == proof["original_instructions"],
              "removal cardinality")
    c.require(len(right) == proof["candidate_instructions"], "candidate body length")
    for i in removed:
        c.require(type(i) is int and 0 <= i < len(left), "removal index")
        w = left[i]
        c.require(w & 127 == 0x57 and (w >> 12) & 7 == 7 and w >> 30 == 3 and (w >> 7) & 31 == 0,
                  "removed word is not vsetivli x0")
    c.require([w for i, w in enumerate(left) if i not in removed] == right,
              "candidate changed a retained machine word")
    c.require(proof["retained_indices"] == [i for i in range(len(left)) if i not in removed],
              "retained index certificate")
    return removed


def execute_with_witness(machine, code, removed):
    for i, word in enumerate(words(code)):
        if i in removed:
            vt = (word >> 20) & 1023
            c.require(vt & ~0xff == 0 and (vt & 7) in (0, 1), "removed unsupported vtype")
            expected = ((word >> 15) & 31, 8 << ((vt >> 3) & 7), 1 << (vt & 7),
                        (vt >> 6) & 1, (vt >> 7) & 1, 0)
            actual = tuple(getattr(machine, key) for key in CSR_NAMES[:-1])
            c.require(actual == expected, "compiled deletion does not have identity state")
        machine.execute(struct.pack("<I", word))
    return machine


def state_equal(left, right, removals):
    for key in (*CSR_NAMES, "x", "v", "memory", "before", "output", "reads", "stores", "tail_dot_operands"):
        c.require(getattr(left, key) == getattr(right, key), "machine state mismatch: " + key)
    counts = Counter(left.counts)
    counts["vsetivli"] -= removals
    c.require(counts == right.counts, "non-configuration instruction counts changed")


def model_inputs(base, m, k):
    result = [dict(kind=f"dataset-{d}", matrix=a, vector=x)
              for d in range(3) for a, x in [base.inputs(m, k, d)]]
    for name, av, xv in (("min-min", -128, -128), ("max-min", 127, -128), ("zero", 0, 127)):
        result.append(dict(kind=name, matrix=[[av] * k for _ in range(m)], vector=[xv] * k))
    result.append(dict(kind="alternating", matrix=[[127 if j % 2 else -128 for j in range(k)] for _ in range(m)],
                       vector=[1 if j % 2 else -1 for j in range(k)]))
    rng = random.Random(0x5333 + 1009 * m + k)
    for trial in range(32):
        result.append(dict(kind=f"random-{trial}", matrix=[[rng.randrange(-128, 128) for _ in range(k)] for _ in range(m)],
                           vector=[rng.randrange(-128, 128) for _ in range(k)]))
    return result


def check_object(g, path):
    obj = g.ELF(path.read_bytes())
    c.require(obj.kind == 1 and not any(s[1] in (4, 9) and s[5] for s in obj.sections),
              "object must be ET_REL without relocations")
    return obj


def run_command(command, output, timeout=90):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    output.with_suffix(".stdout").write_text(result.stdout, encoding="utf-8")
    output.with_suffix(".stderr").write_text(result.stderr, encoding="utf-8")
    save(output.with_suffix(".command.json"), dict(argv=command, exit_code=result.returncode))
    c.require(result.returncode == 0, "command failed; see " + str(output))
    return result.stdout


def check(repo, output, library, jobs):
    repo, output, library = c.bind(repo), Path(output).resolve(), Path(library).resolve()
    c.require(type(jobs) is int and 1 <= jobs <= 4, "jobs must fit four-core budget")
    c.require(not output.exists() and output != repo and repo not in output.parents and output not in repo.parents,
              "fresh output outside source tree required")
    c.require(library.is_file(), "selected LLVM shared library missing")
    output.mkdir(parents=True)
    try:
        return run_owned(repo, output, library, jobs)
    except Exception:
        # Only this invocation's newly created, validated output is writable.
        # A preflight rejection must not leave a failure file in old evidence
        # or in the source tree. Never overwrite an existing failure record.
        with (output / "failure.txt").open("x", encoding="utf-8") as stream:
            stream.write(traceback.format_exc())
        raise


def run_owned(repo, output, library, jobs):
    if hasattr(os, "sched_setaffinity"):
        allowed = sorted(os.sched_getaffinity(0))
        os.sched_setaffinity(0, allowed[:min(jobs, 4)])
    started = datetime.now(timezone.utc).isoformat()
    sources = {rel: c.sha(repo / rel) for rel in c.PINS}
    sources.update(MODEL_PINS)
    for rel, digest in MODEL_PINS.items():
        c.require(c.sha(repo / rel) == digest, "frozen model drift: " + rel)
    for name in ("candidate.py", "check.py", "test_candidate.py", "llvm_assemble.py"):
        sources[str(c.REL / name)] = c.sha(repo / c.REL / name)
    c.require(c.sha(repo / GNU_OBJECT) == GNU_SHA, "frozen GNU reference object drift")
    save(output / "source-identity.json", dict(parent_commit=c.BASE, files=sources, gnu_object=str(GNU_OBJECT), gnu_sha256=GNU_SHA))
    run_command([sys.executable, str(repo / c.REL / "test_candidate.py")], output / "state-tests")
    g = c.module("config_frozen_s1_gate", repo / c.S1 / "gate.py")
    parent = c.module("config_frozen_firstdot", repo / c.S1 / "firstdot_candidate.py")
    base = c.module("config_frozen_s1", repo / c.S1 / "candidate.py").load_base(repo)
    gnu = check_object(g, repo / GNU_OBJECT)
    inventory = [(s, d, v) for s in (1, 3, 5, 7) for d in range(3) for v in ("firstdot", "config-reuse")]

    def name(item):
        s, d, v = item
        return f"s{s}-d{d}-{v}"

    def generate(item, prefix):
        s, d, v = item
        directory = output / prefix / name(item)
        manifest = c.generate(repo, directory, v, d, s)
        return manifest, {p: c.sha(directory / p) for p in c.FILES}

    serial = {item: generate(item, "serial") for item in inventory}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        parallel = list(pool.map(lambda item: (item, generate(item, "parallel")), inventory))
    c.require(all(value == serial[item] for item, value in parallel), "parallel generation differs")
    parent_matches = []
    for s in (1, 3, 5, 7):
        for d in range(3):
            path = output / "parent" / f"s{s}-d{d}"
            parent.generate(repo, path, "firstdot", d, s)
            c.require(all(c.sha(path / p) == serial[(s, d, "firstdot")][1][p] for p in c.FILES),
                      "firstdot baseline byte identity")
            parent_matches.append(dict(shard=s, dataset=d))

    def compile_item(item):
        directory = output / "serial" / name(item)
        results = []
        for stem in ("gemv", "kernels"):
            text = run_command([sys.executable, str(repo / c.REL / "llvm_assemble.py"),
                                str(directory / (stem + ".S")), str(directory / (stem + ".o")),
                                "--library", str(library)], directory / (stem + "-assembly"))
            results.append(json.loads(text))
        return dict(name=name(item), results=results)

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        builds = list(pool.map(compile_item, inventory))
    save(output / "builds.json", builds)
    inputs = {f"{m}x{k}": model_inputs(base, m, k) for m, k in base.SHAPES}
    save(output / "model-inputs.json", dict(initial_states=INIT_STATES, csr_names=CSR_NAMES, shapes=inputs))
    pairs, unique = [], []
    for s in (1, 3, 5, 7):
        for d in range(3):
            dirs = [output / "serial" / name((s, d, v)) for v in ("firstdot", "config-reuse")]
            manifests = [serial[(s, d, v)][0] for v in ("firstdot", "config-reuse")]
            c.require(manifests[0]["plan"] == manifests[1]["plan"], "measurement plan changed")
            for filename in ("cases.h", "gemv.h"):
                c.require((dirs[0] / filename).read_bytes() == (dirs[1] / filename).read_bytes(), "input/header mismatch")
            objects = [[check_object(g, path / filename) for filename in ("gemv.o", "kernels.o")] for path in dirs]
            for public, wrapper in objects:
                c.require(wrapper.named[".text"][5] == 4 * 8192 and
                          [wrapper.symbols[f"t13_kernel_{i}"][0] for i in range(4)] == [8192 * i for i in range(4)],
                          "four fixed wrapper slots")
            allowed = bytearray(4 * 8192)
            for row in manifests[1]["rows"]:
                symbol = row["api_symbol"]
                start0, size0 = objects[0][1].symbols[symbol][:2]
                start1, size1 = objects[1][1].symbols[symbol][:2]
                c.require(start0 == start1 and size1 <= size0, "paired public entry addresses changed")
                allowed[start0:start0 + size0] = b"\1" * size0
            texts = [obj[1].section(obj[1].named[".text"]) for obj in objects]
            c.require(all(a == b for a, b, selected in zip(*texts, allowed) if not selected),
                      "paired wrapper changed bytes outside the old leaf extents")
            for i, row in enumerate(manifests[1]["rows"]):
                symbol = row["api_symbol"]
                leaves = [obj[0].symbol_data(symbol) for obj in objects]
                for leaf, (_, wrapper) in zip(leaves, objects):
                    c.require(leaf == wrapper.symbol_data(symbol), "public and wrapper leaf differ")
                    c.require(leaf[:8] == struct.pack("<II", 0x00050613, 0x00058693) and leaf[-4:] == struct.pack("<I", 0x00008067),
                              "leaf ABI prologue/return changed")
                c.require(leaves[0] == gnu.symbol_data(symbol.replace("r4_", "firstdot_", 1)), "LLVM baseline differs from GNU anchor")
                codes = [leaf[8:-4] for leaf in leaves]
                removed = erasure(*codes, row["config_reuse_proof"])
                c.require(len(codes[1]) == 4 * len(row["body"]), "assembler expansion changed body length")
                pairs.append(dict(shard=s, dataset=d, symbol=symbol, removed_configs=len(removed),
                                  baseline_bytes=len(leaves[0]), candidate_bytes=len(leaves[1]),
                                  baseline_sha256=hashlib.sha256(leaves[0]).hexdigest(),
                                  candidate_sha256=hashlib.sha256(leaves[1]).hexdigest()))
                if d == 0:
                    unique.append((row, codes, removed))
    save(output / "compiled-pairs.json", pairs)
    reports, total = [], 0
    for row, codes, removed in unique:
        data = inputs[f"{row['m']}x{row['k']}"]
        for trial, item in enumerate(data):
            matrix, vector = item["matrix"], item["vector"]
            for init in INIT_STATES:
                machines = [g.Machine(matrix, vector, poison_seed=0x5333 + trial) for _ in range(2)]
                for machine in machines:
                    for key, value in zip(CSR_NAMES, init):
                        setattr(machine, key, value)
                execute_with_witness(machines[0], codes[0], removed)
                machines[1].execute(codes[1])
                for machine in machines:
                    machine.check(matrix, vector, stored=True)
                state_equal(*machines, len(removed))
                total += 2
        reports.append(dict(symbol=row["api_symbol"], input_cases=len(data), initial_states=len(INIT_STATES),
                            executions=2 * len(data) * len(INIT_STATES), removals=len(removed),
                            full128=True, all_registers_equal=True, csr_equal=True, exact_accesses_equal=True,
                            compiled_deletion_state_witness=True))
    # These are deliberately wrong compiled candidates, not string-parser tests.
    row, codes, removed = next(item for item in unique if item[0]["m"] == 8 and item[0]["k"] == 32 and
                               item[0]["software"] == "reuse" and item[0]["method"] == "vdot")
    wrong = [codes[1][4:], struct.pack("<I", words(codes[1])[0] ^ (1 << 15)) + codes[1][4:]]
    rejected = 0
    for broken in wrong:
        try:
            erasure(codes[0], broken, row["config_reuse_proof"])
        except ValueError:
            rejected += 1
    c.require(rejected == len(wrong), "compiled mutation was accepted")
    for rel, digest in sources.items():
        c.require(c.sha(repo / rel) == digest, "source changed during verification: " + rel)
    result = dict(status="CONFIG_REUSE_HOST_COMPILED_MODEL_PASS_NOT_RUNTIME", contract=c.CONTRACT,
                  started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                  source_parent=c.BASE, python=platform.python_version(), platform=platform.platform(),
                  assembler="LLVM C API", llvm_library=str(library), llvm_library_sha256=c.sha(library),
                  cpu_budget=jobs, cpu_affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
                  serial_generations=24, parallel_generations=24, original_firstdot_byte_matches=12,
                  assembled_objects=len(builds) * 2, compiled_pairs=len(pairs), unique_functions=len(unique),
                  relocatable_wrapper_outside_leaf_bytes_equal=True,
                  model_executions=total, compiled_mutations_rejected=rejected, reports=reports,
                  source_identity_sha256=c.sha(output / "source-identity.json"),
                  model_inputs_sha256=c.sha(output / "model-inputs.json"), gnu_anchor_sha256=GNU_SHA,
                  live_difftest=False, new_emu_runs=0, new_nemu_runs=0,
                  executable_link_test=False, performance_measured=False, stable_default_changed=False)
    save(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--llvm-library", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    value = check(args.repo, args.output, args.llvm_library, args.jobs)
    print(json.dumps({k: v for k, v in value.items() if k != "reports"}, indent=2))
