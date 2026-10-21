"""Source and native tool contracts for new O4 experiments (never backfill archives)."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment():
    # Do not inherit LD_PRELOAD/LD_LIBRARY_PATH, tool startup hooks or user Tcl files.
    return {**{k: os.environ[k] for k in ("HOME", "PATH") if k in os.environ},
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}


def load_lock():
    return json.loads(Path(__file__).with_name("toolchain-lock.json").read_text(encoding="utf-8"))


def expected_library():
    return {item["file"]:item["sha256"] for item in load_lock()["library"]["files"] if "url" in item}


def library_inventory(work):
    expected = expected_library()
    require(bool(expected), "missing pinned O4 library")
    for name, digest in expected.items():
        require(sha(Path(work)/"library"/name) == digest, "O4 reference library/source changed: " + name)
    return expected


def capture(work):
    work = Path(work).resolve()
    env = environment()
    library_files = library_inventory(work)
    tools = {}
    for name, options in (("yosys", ["-V"]), ("berkeley-abc", ["-c", "version"]),
                          ("sta", ["-version"])):
        path = (work / "tools/root/usr/bin" / name).resolve(strict=True)
        digest = sha(path)
        linked = subprocess.check_output(["ldd", str(path)], text=True, env=env)
        require("not found" not in linked, "unresolved O4 tool library")
        libraries = {}
        for line in linked.splitlines():
            match = re.search(r"(?:=>\s+)?(/\S+)\s+\(", line)
            if match:
                shared_library = Path(match[1]).resolve(strict=True)
                libraries[str(shared_library)] = sha(shared_library)
        require(bool(libraries), "missing O4 shared library inventory")
        version = subprocess.check_output([str(path), *options], text=True,
                                          stderr=subprocess.STDOUT, env=env)
        require(sha(path) == digest, "O4 tool changed during capture")
        tools[name] = dict(path=str(path), sha256=digest, version=version,
                           libraries=dict(sorted(libraries.items())))
    return dict(schema=1, tools=tools, environment=env, library=library_files,
                lock_sha256=sha(Path(__file__).with_name("toolchain-lock.json")))


def validate(contract):
    require(isinstance(contract, dict) and type(contract.get("schema")) is int
            and contract["schema"] == 1, "missing current O4 tool contract")
    require(set(contract.get("tools", {})) == {"yosys", "berkeley-abc", "sta"},
            "incomplete O4 tool inventory")
    require(isinstance(contract.get("environment"), dict) and contract["environment"],
            "missing O4 environment")
    require(re.fullmatch(r"[0-9a-f]{64}", contract.get("lock_sha256", "")), "invalid O4 lock digest")
    require(contract["lock_sha256"] == sha(Path(__file__).with_name("toolchain-lock.json"))
            and contract.get("library") == expected_library(), "O4 pinned library/lock differs")
    for tool in contract["tools"].values():
        require(isinstance(tool, dict) and isinstance(tool.get("path"), str)
                and tool["path"].startswith("/") and bool(tool.get("version"))
                and re.fullmatch(r"[0-9a-f]{64}", tool.get("sha256", "")), "invalid O4 tool identity")
        require(isinstance(tool.get("libraries"), dict) and tool["libraries"], "missing O4 library inventory")
        for path, digest in tool["libraries"].items():
            require(isinstance(path, str) and path.startswith("/")
                    and re.fullmatch(r"[0-9a-f]{64}", digest), "invalid O4 library identity")


def verify(work, expected=None):
    saved = json.loads((Path(work) / "tools/contract.json").read_text(encoding="utf-8"))
    validate(saved)
    if expected is not None:
        require(saved == expected, "O4 preparation contract changed")
    require(library_inventory(work) == saved["library"], "O4 library contract changed")
    for name, tool in saved["tools"].items():
        path = (Path(work) / "tools/root/usr/bin" / name).resolve(strict=True)
        require(str(path) == tool["path"] and sha(path) == tool["sha256"], "O4 executable changed")
        require(all(sha(path) == digest for path, digest in tool["libraries"].items()),
                "O4 shared library changed")
    require(capture(work) == saved, "O4 tool/environment changed since preparation")
    return saved


def paired_sources(generations):
    from elaborate import build_recipe
    require(len(generations) == 4, "four generation receipts required")
    reference = None
    for receipt in generations:
        inputs = receipt.get("source_inputs")
        require(isinstance(inputs, dict) and receipt.get("source_inputs_unchanged") is True
                and not receipt.get("verification_error"), "current generation source contract required")
        require(inputs.get("source_commit") == receipt.get("source_commit"), "generation commit mismatch")
        for group in ("files", "dependency_files"):
            require(isinstance(inputs.get(group), dict) and inputs[group], "missing generation input inventory")
            require(all(isinstance(path,str) and re.fullmatch(r"[0-9a-f]{64}",digest)
                        for path,digest in inputs[group].items()), "invalid generation input inventory")
        native = receipt.get("native_build_contract")
        build_recipe.validate(native)
        identity = (inputs, native)
        if reference is None:
            reference = identity
        require(identity == reference, "O4 paired generation inputs/tools differ")


def paired_tools(results):
    reference = None
    for row in results.values():
        for stage in ("mapping", "timing"):
            summary = row[stage]
            contract = summary.get("tool_contract")
            validate(contract)
            require(summary.get("tool_contract_unchanged") is True, "O4 tool contract was not verified after execution")
            if reference is None:
                reference = contract
            require(contract == reference, "O4 paired mapping/STA tools differ")


def stage_receipt(contract, receipt):
    validate(contract)
    require(receipt.get("tool_contract") == contract
            and receipt.get("tool_contract_unchanged") is True
            and type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0,
            "O4 stage tool receipt differs")
