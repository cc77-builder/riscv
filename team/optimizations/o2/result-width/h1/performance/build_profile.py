"""Audit the preserved B0 and accepted H1 builds without changing either."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[6]
B0_PRODUCTS = Path("/home/riscv/riscv-lab/o2-b0-build-before-h1-20261021")
H1_PRODUCTS = ROOT / "build"
VDOT = "src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"
SOURCE_COMMITS = {
    "b0": "b218cbc6e6b135e4ff219a902a9284a59d3c82c9",
    "h1": "8b5024fcbd96986871cc40ce8c9fb71a67c495eb",
}
PIN_SHA = {
    "b0": "3752438404f544b9006c52b4234f5f05906b2de0fe4fbfa63c2006a30884dbf9",
    "h1": "39f525c9a9e2a068aee04ef1e08878af3f4056da24115a1236ddacf09b893666",
}
EMU_SHA = {
    "b0": "ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57",
    "h1": "e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747",
}
O4_ENTRY = '''// O4 common production interfaces only: no scoreboard, taps or trace state.
object vdotCost extends HasChisel {
  override def sources = T.sources { Seq(PathRef(pwd / "team/optimizations/o4/GenerateVDotCost.scala")) }
  override def moduleDeps = Seq(xiangshan)
  override def forkArgs = Seq("-Xmx8G", "-Xss16m")
}

'''

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_pair(a, b):
    for key in ("dependency_files", "config", "NUM_CORES", "EMU_THREADS", "JVM_XMX",
                "BUILD_JOBS", "VDOT_T14_FUSED_INPUT", "VDOT_T12_TRACE",
                "VDOT_T13_TRACE", "VDOT_O2_ELASTIC", "VDOT_O1_HANDOFF",
                "VDOT_O1_TRACE", "VDOT_O2_TRACE"):
        require(a[key] == b[key], "non-H1 build difference: " + key)
    require(a["files"].keys() == b["files"].keys(), "source inventory differs")
    changed = {k for k in a["files"] if a["files"][k] != b["files"][k]}
    require(changed == {"build.sc", VDOT}, "unexpected source difference")
    require(a["config"] == "MinimalConfig" and a["NUM_CORES"] == a["EMU_THREADS"] == 1,
            "unexpected core configuration")
    require(a["JVM_XMX"] == "12G" and a["BUILD_JOBS"] == 2, "build resources differ")
    expected = dict(VDOT_T14_FUSED_INPUT="1", VDOT_T12_TRACE="0", VDOT_T13_TRACE="1",
                    VDOT_O2_ELASTIC="1", VDOT_O1_HANDOFF="0",
                    VDOT_O1_TRACE="0", VDOT_O2_TRACE="1")
    require(all(a[k] == v for k, v in expected.items()), "illegal O2 observation profile")
    return True

def normalized_verilator(log, products):
    rows = [line for line in log.splitlines() if "verilator --exe " in line]
    require(len(rows) == 1, "expected one actual Verilator command")
    require("--threads 1 " in rows[0] and "-O3 --cc" in rows[0], "wrong simulator options")
    # Build logs carry POSIX paths even when reviewed on Windows.
    return rows[0].replace(Path(products).as_posix(), "<BUILD>")

def verified_git_sources(pins):
    names = list(pins["files"])
    request = "".join(pins["source_commit"] + ":" + n + "\n" for n in names)
    data = subprocess.check_output(["git", "cat-file", "--batch"], input=request.encode(), cwd=ROOT)
    offset = 0
    selected = {}
    for name in names:
        end = data.index(b"\n", offset)
        header = data[offset:end].split()
        require(len(header) == 3 and header[1] == b"blob", "missing source Git blob: " + name)
        size = int(header[2])
        body = data[end + 1:end + 1 + size]
        require(hashlib.sha256(body).hexdigest() == pins["files"][name], "Git source mismatch: " + name)
        offset = end + size + 2
        if name in ("build.sc", VDOT):
            selected[name] = body.decode()
    require(offset == len(data), "unparsed Git batch")
    return selected

def validate_build_sc(a, b):
    require(b.count(O4_ENTRY) == 1 and b.replace(O4_ENTRY, "", 1) == a,
            "build.sc change is not solely the independent O4 test entry")

def code_without_comments_strings(text):
    return re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/', "", text)

def monitor_effect_check(text):
    clean = code_without_comments_strings(text)
    require(re.search(r"\b(output|inout|import|export|force|release|bind|alias)\b", clean) is None,
            "monitor has output or external effect")
    require(set(re.findall(r"\$\w+", clean)) <= {"$fwrite", "$random"}, "unexpected monitor system task")

def build_profile(b0_build, h1_build):
    dirs = {"b0": Path(b0_build), "h1": Path(h1_build)}
    products = {"b0": B0_PRODUCTS, "h1": H1_PRODUCTS}
    files, pins, sources, manifests, commands = {}, {}, {}, {}, {}
    def bind(p):
        files[str(p)] = sha(p)
    for mode, folder in dirs.items():
        pin_path = folder / "hardware-inputs.json"
        require(sha(pin_path) == PIN_SHA[mode], "unaccepted hardware pins: " + mode)
        pins[mode] = json.loads(pin_path.read_text())
        p = pins[mode]
        require(p["source_commit"] == SOURCE_COMMITS[mode] and p["emu_sha256"] == EMU_SHA[mode],
                "unaccepted source/binary identity")
        state = json.loads((folder / "build-state.json").read_text())
        require(state["status"] == "O2_FULLCORE_BUILD_PASS" and state["build_exit_code"] == 0,
                "build did not pass")
        require(state["source_commit"] == p["source_commit"] and state["emu_sha256"] == p["emu_sha256"],
                "build state identity mismatch")
        require(len(p["files"]) == 429 and len(p["dependency_files"]) == 21236, "hardware inventory changed")
        sources[mode] = verified_git_sources(p)
        for leaf in ("hardware-inputs.json", "build-state.json", "generated-artifacts.json",
                     "build-command.sh", "dependencies.json", "emu-build.log"):
            bind(folder / leaf)
        log = (folder / "emu-build.log").read_text()
        require('OPT_SLOW="-O0"' in log and "OPT_FAST=-O3" in log, "wrong C++ optimization")
        commands[mode] = normalized_verilator(log, ROOT / "build")
        generated = json.loads((folder / "generated-artifacts.json").read_text())
        manifests[mode] = {row["path"]: row["sha256"] for row in generated}
        require(len(manifests[mode]) == len(generated) == 1672, "generated inventory mismatch")
        for row in generated:
            rel = Path(row["path"])
            require(rel.parts[0] == "build" and ".." not in rel.parts, "invalid generated path")
            actual = products[mode] / Path(*rel.parts[1:])
            require(actual.stat().st_size == row["bytes"] and sha(actual) == row["sha256"],
                    "generated product drift: " + str(actual))
            files[str(actual)] = row["sha256"]
        require(sha(products[mode] / "emu") == EMU_SHA[mode], "relocated EMU mismatch")
    validate_pair(pins["b0"], pins["h1"])
    validate_build_sc(sources["b0"]["build.sc"], sources["h1"]["build.sc"])
    require(commands["b0"] == commands["h1"], "actual compiler/Verilator command differs")
    versions = {}
    for tool in ("java", "mill", "verilator", "clang", "make", "python", "firtool"):
        paths = [folder / (tool + "-version.log") for folder in dirs.values()]
        require(paths[0].read_bytes() == paths[1].read_bytes(), "tool version differs: " + tool)
        versions[tool] = sha(paths[0])
        for p in paths:
            bind(p)
    changed = {k for k in manifests["b0"].keys() | manifests["h1"].keys()
               if manifests["b0"].get(k) != manifests["h1"].get(k)}
    require(changed == {"build/emu", "build/rtl/VDotElastic.sv", "build/rtl/SimTop.sv",
                        "build/rtl/NewCSR.sv", "build/rtl/LogPerfEndpoint.sv"},
            "unexpected generated change")
    rtl = {m: products[m] / "rtl" for m in products}
    texts = lambda name: [(rtl[m] / name).read_text() for m in ("b0", "h1")]
    a, b = texts("SimTop.sv")
    require(re.sub(r"(?m)^\s*//.*\n", "", a) == re.sub(r"(?m)^\s*//.*\n", "", b),
            "top-level functional RTL differs")
    a, b = texts("NewCSR.sv")
    normalize = lambda t: re.sub(r"gitCommitSHA = 40'h[0-9A-F]+", "gitCommitSHA = <BUILD_ID>", t)
    require(normalize(a) == normalize(b), "CSR difference beyond embedded Git identity")
    for t in texts("LogPerfEndpoint.sv"):
        monitor_effect_check(t)
    a, b = texts("VDotElastic.sv")
    require("reg  [127:0] rPacket_res_data;" in a and "reg  [31:0]  rPacket_res_data;" in b,
            "result storage candidate not generated")
    require("assign io_out_bits_res_data = {96'h0, rPacket_res_data};" in b, "public 128-bit result missing")
    for leaf in ("constantin.txt", "plusArgs"):
        a, b = B0_PRODUCTS / leaf, H1_PRODUCTS / leaf
        require(a.read_bytes() == b.read_bytes(), "runtime auxiliary differs: " + leaf)
        bind(a); bind(b)
    accepted = {
        "b0": Path("/home/riscv/riscv-lab/o2-fullcore-20261019/recheck-02/result.json"),
        "h1": Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021/final-validation.json"),
    }
    b0 = json.loads(accepted["b0"].read_text())
    h1 = json.loads(accepted["h1"].read_text())
    require(b0["status"] == "O2_G3_OFFLINE_RECHECK_PASS" and b0["g3_complete"]
            and b0["hardware_pins_sha256"] == PIN_SHA["b0"] and b0["emu_sha256"] == EMU_SHA["b0"],
            "B0 acceptance mismatch")
    require(h1["status"] == "H1_FULLCORE_VALIDATION_PASS"
            and h1["input_receipts"]["build-01/hardware-inputs.json"] == PIN_SHA["h1"]
            and h1["emu_sha256"] == EMU_SHA["h1"], "H1 acceptance mismatch")
    for p in accepted.values():
        bind(p)
    return files, dict(status="B0_H1_BUILD_PROFILE_PASS",
        source_commits=SOURCE_COMMITS, emu_sha256=EMU_SHA,
        emulator_paths={m: str(products[m] / "emu") for m in products},
        hardware_source_files_per_build=429, common_dependency_files=21236,
        source_differences=["build.sc", VDOT], generated_differences=sorted(changed),
        source_review="Only H1 production RTL plus independent O4 build target; full Git blobs verified",
        generated_review="Top comments, embedded Git ID, and input-only diagnostic monitor differ; no claim of whole-design formal equivalence",
        diagnostic_monitor_external_ports="input-only; no DPI/force or external writes except diagnostic fwrite",
        randomized_initialization="seed=1 and explicit reset; random register layout can differ; deterministic replays checked",
        tool_version_sha256=versions, normalized_verilator_command=commands["b0"],
        common_optimization="OPT_FAST=-O3 OPT_SLOW=-O0", observer_flags_differ_by_mode=False,
        original_pins_unchanged=True, b0_binary_relocated=True)
