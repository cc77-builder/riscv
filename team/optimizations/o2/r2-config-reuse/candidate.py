"""Conservative repeated-vsetivli candidate for the frozen firstdot C ABI.

Generation/host proof only. This module cannot qualify a runtime or change the
stable library. Every invocation owns its parent renderer modules.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
REL = Path("team/optimizations/o2/r2-config-reuse")
S1 = Path("team/optimizations/o2/r2-vector-accum")
ENTRY = Path("team/optimizations/o2/r2-select")
CONTRACT = "r2-s3-config-reuse-c-abi-v1"
HARNESS = "r4-gemv-c-abi-entry-v1"
BASE = "c362ca74194f238afe7a84247ccd3e1cb7da36d2"
FILES = ("kernels.S", "cases.h", "gemv.S", "gemv.h")
PINS = {
    str(S1 / "firstdot_candidate.py"): "c6d759f1225832ba23e4d06301d5c8b54dd095e8",
    str(S1 / "candidate.py"): "fc9f03491e7b25ddef2028d8244d1b7d30889916",
    str(ENTRY / "entry_candidate.py"): "f855f8f9722d75214846bd2908e008d538f335a6",
    "team/workloads/o3-gemv/generate.py": "9cb0c6b755daa9b05d346b4b48cb80246852d4a8",
    "team/workloads/o3-gemv/model.py": "0be812d0fc112af863fe5adf3be3794e16c7bdf4",
    "team/workloads/unified-vdot/generate.py": "90cc41079c27ebfe146321d4bf01e2ee0426dae9",
}

# Restrict the transformation to this project's VLEN128, legal immediate AVL
# subset. No dataflow is inferred through unknown assembler text or labels.
CONFIG = re.compile(r"vsetivli zero, (\d+), e(8|16|32), m(1|2), (tu|ta), (mu|ma)")
GPR = r"(?:zero|t[0-6]|a[0-7])"
VREG = r"v(?:[0-9]|[12][0-9]|3[01])"
IMM = r"-?\d+"
SCALAR = tuple(re.compile(p) for p in (
    rf"(?:addi) {GPR}, {GPR}, {IMM}",
    rf"(?:addw|mulw) {GPR}, {GPR}, {GPR}",
    rf"li {GPR}, {IMM}", rf"mv {GPR}, {GPR}",
    rf"lb {GPR}, {IMM}\({GPR}\)",
))
VECTOR = tuple(re.compile(p) for p in (
    rf"vle8\.v {VREG}, \({GPR}\)",
    rf"vs1r\.v {VREG}, \({GPR}\)",
    rf"(?:vadd\.vv|vwmul\.vv|vwredsum\.vs) {VREG}, {VREG}, {VREG}",
    rf"vmv\.v\.i {VREG}, {IMM}",
    rf"vmv\.x\.s {GPR}, {VREG}",
    rf"vmv\.s\.x {VREG}, {GPR}",
))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def bind(repo):
    repo = Path(repo).resolve()
    require(repo == ROOT, "candidate must execute in its selected source snapshot")
    for path, digest in PINS.items():
        require(blob((repo / path).read_bytes()) == digest, "frozen source drift: " + path)
    return repo


def configuration(line):
    match = CONFIG.fullmatch(line)
    if not match:
        return None
    avl, sew, lmul = map(int, match.group(1, 2, 3))
    # VLEN=128; AVL <= VLMAX makes actual VL exactly known. Retain unsupported
    # or out-of-range forms instead of assuming a particular stripmine result.
    if not (0 <= avl <= 31 and avl <= 128 * lmul // sew):
        return None
    return (avl, sew, lmul, int(match[4] == "ta"), int(match[5] == "ma"))


def prune(body):
    """Return a fresh body plus witnesses for removed identity transitions.

    Unknown instructions invalidate both facts. A known ordinary vector op
    only preserves an already-proven zero vstart; we do not infer a legal
    nonzero-vstart execution. Custom words require the exact dot8 legal state.
    This is not a general assembler optimizer or an exception-path proof.
    """
    require(isinstance(body, (list, tuple)) and all(isinstance(x, str) for x in body),
            "body must be a sequence of instruction strings")
    known, zero, origin = None, False, None
    retained, removed, barriers = [], [], []
    for index, line in enumerate(body):
        cfg = configuration(line)
        if cfg is not None:
            if cfg == known and zero:
                removed.append(dict(index=index, line=line, dominated_by=origin,
                                    state=list(cfg), vstart=0))
                continue
            known, zero, origin = cfg, True, index
        elif (match := re.fullmatch(r"csrwi vstart, (\d+)", line)) and 0 <= int(match[1]) <= 31:
            zero = int(match[1]) == 0
        elif (match := re.fullmatch(r"csrwi vcsr, (\d+)", line)) and 0 <= int(match[1]) <= 31:
            pass  # vcsr does not alias vl/vtype/vstart; retain the write.
        elif any(p.fullmatch(line) for p in SCALAR):
            pass
        elif any(p.fullmatch(line) for p in VECTOR):
            pass  # Normal completion preserves cfg and an already-zero start.
        elif (match := re.fullmatch(r"\.word (0x[0-9a-fA-F]{8})", line)) and \
                int(match[1], 16) & 0xfe00707f == 0x0200000b and \
                known == (8, 8, 1, 0, 0) and zero:
            pass
        else:
            known, zero, origin = None, False, None
            barriers.append(dict(index=index, line=line))
        retained.append(index)
    return [body[i] for i in retained], dict(
        retained_indices=retained, removed=removed, barriers=barriers,
        original_instructions=len(body), candidate_instructions=len(retained),
        proof_scope="VLEN128 straight-line normal completion; CONTRACT.md")


def generate(repo, output, variant, dataset, shard, suite="performance"):
    repo, output = bind(repo), Path(output).resolve()
    require(variant in ("firstdot", "config-reuse"), "candidate variant")
    require(type(dataset) is int and dataset in range(3), "dataset")
    require(type(shard) is int and shard in (1, 3, 5, 7) and suite == "performance", "cohort")
    require(not output.exists() and output != repo and repo not in output.parents and output not in repo.parents,
            "new output directory outside the source snapshot required")
    first = module("config_private_firstdot", repo / S1 / "firstdot_candidate.py")
    entry = module("config_private_entry", repo / ENTRY / "entry_candidate.py")
    original_source = entry.source
    witnesses = []

    def source(root):
        s1 = original_source(root)
        original_kernel = s1.kernel

        def kernel(base, m, k, method, software, scope, selected):
            require(selected == "s1" and scope == "endtoend", "frozen parent selection")
            body = first.first_dot(original_kernel(base, m, k, method, software, scope, selected),
                                   m, k, method, software)
            new, proof = prune(body)
            require(not proof["barriers"], "unsupported instruction in pinned parent")
            witnesses.append(dict(m=m, k=k, method=method, software=software,
                                  before=body, proof=proof))
            return new if variant == "config-reuse" else body

        s1.kernel = kernel
        return s1

    entry.source = source
    manifest = entry.generate(repo, output, "s1", dataset, shard, suite)
    require(manifest["contract"] == HARNESS and len(witnesses) == len(manifest["rows"]) == 4,
            "frozen harness or row cardinality changed")
    for row, witness in zip(manifest["rows"], witnesses):
        require(all(row[key] == witness[key] for key in ("m", "k", "method", "software")), "row order")
        row["r2_variant"] = variant
        row["config_reuse_proof"] = witness["proof"]
        row["config_reuse_parent_body"] = witness["before"]
    manifest.update(config_reuse_contract=CONTRACT, r2_variant=variant,
                    parent_variant="firstdot", parent_source_commit=BASE,
                    config_reuse_source_sha256=sha(Path(__file__)),
                    config_reuse_dependency_blobs=PINS, runtime_qualified=False,
                    stable_default_changed=False, acceptance="GENERATION_ONLY_NOT_RUNTIME")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("firstdot", "config-reuse"), required=True)
    parser.add_argument("--dataset", type=int, choices=range(3), default=0)
    parser.add_argument("--shard", type=int, choices=(1, 3, 5, 7), default=3)
    args = parser.parse_args()
    result = generate(args.repo, args.output, args.variant, args.dataset, args.shard)
    print(json.dumps(dict(status="GENERATED_NOT_EXECUTED", variant=args.variant,
                          candidate_removals=[len(r["config_reuse_proof"]["removed"]) for r in result["rows"]])))
