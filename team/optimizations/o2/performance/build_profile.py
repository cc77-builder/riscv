"""Verify current paired native contracts; frozen measurements use archived tools."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.append(str(Path(__file__).resolve().parents[2] / "o1"))
import build_recipe


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_verilator(log, products):
    rows = [line for line in log.splitlines() if "verilator --exe " in line]
    require(len(rows) == 1, "expected one real Verilator generation command")
    require("--threads 1 " in rows[0] and "-O3 --cc" in rows[0], "wrong simulator options")
    return rows[0].replace(str(products), "<BUILD>")


def build_profile(o1_build, o2_build):
    files, contracts, commands = {}, [], []
    for directory, status in ((Path(o1_build), "O1_MATCHED_BUILD_PASS"),
                              (Path(o2_build), "O2_FULLCORE_BUILD_PASS")):
        state = json.loads((directory / "build-state.json").read_text())
        pins = json.loads((directory / "hardware-inputs.json").read_text())
        require(state.get("status") == status and type(state.get("build_exit_code")) is int
                and state["build_exit_code"] == 0, "build not complete")
        require(state.get("source_commit") == pins.get("source_commit"), "build source identity differs")
        require(state.get("emu_sha256") == pins.get("emu_sha256") == sha(pins["emu_path"]),
                "build binary identity differs")
        contract = pins.get("native_build_contract")
        build_recipe.validate(contract)
        contracts.append(contract)
        for tool in contract["compilers"].values():
            require(sha(tool["path"]) == tool["sha256"], "native tool changed")
            files[tool["path"]] = tool["sha256"]
        for leaf in ("hardware-inputs.json", "build-state.json", "build-command.sh", "emu-build.log"):
            path = directory / leaf
            files[str(path)] = sha(path)
        command = (directory / "build-command.sh").read_text()
        expected = build_recipe.make_command(contract,
                    Path(state["build_products"]) if status == "O1_MATCHED_BUILD_PASS" else None)
        require(command.endswith(expected), "native invocation differs from contract")
        products = Path(pins["emu_path"]).parent
        commands.append(normalized_verilator((directory / "emu-build.log").read_text(), products))
        if status == "O1_MATCHED_BUILD_PASS":
            restoration = directory / "original-build-restoration.json"
            require(json.loads(restoration.read_text()).get("status") == "ORIGINAL_O2_GENERATION_RESTORED",
                    "original O2 build not restored")
            files[str(restoration)] = sha(restoration)
            auxiliary = directory / "generated-auxiliary.json"
            files[str(auxiliary)] = sha(auxiliary)
            for row in json.loads(auxiliary.read_text()):
                require(sha(row["destination"]) == row["sha256"], "staged auxiliary changed")
                files[row["destination"]] = row["sha256"]
    require(contracts[0] == contracts[1], "native build contracts differ")
    require(commands[0] == commands[1], "normalized Verilator commands differ")
    return files, dict(status="MATCHED_O1_O2_BUILD_PROFILE_PASS", native_build_contract=contracts[0],
                       normalized_verilator_command=commands[0], original_o2_generation_restored=True)
