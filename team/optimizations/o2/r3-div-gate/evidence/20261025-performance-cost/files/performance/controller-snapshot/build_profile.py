"""Audit the preserved H1 and fixed DIV-gate builds without changing either."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
BEFORE_PRODUCTS = Path("/home/riscv/riscv-lab/o2-h1-build-before-r3-div-gate-20261024")
AFTER_PRODUCTS = ROOT / "build"
DEFAULT_ACCEPTANCE = {
    "before": Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021/final-validation.json"),
    "after": Path("/home/riscv/riscv-lab/o2-r3-div-gate-fullcore-20261024/final-validation.json"),
}
VDOT = "src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala"
SOURCE_COMMITS = {
    "before": "8b5024fcbd96986871cc40ce8c9fb71a67c495eb",
    "after": "0f12df675378556670afd0dd2153f47fcb330610",
}
PIN_SHA = {
    "before": "39f525c9a9e2a068aee04ef1e08878af3f4056da24115a1236ddacf09b893666",
    "after": "388e286327006c7a58494d434370aaaf7c36815f1abeaa517c40754c4e620bc5",
}
EMU_SHA = {
    "before": "e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747",
    "after": "2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8",
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


def verify_accepted_receipts(accepted):
    """Keep before/after provenance checks even when their storage locations change."""
    require(set(accepted) == {"before", "after"}, "two acceptance receipt paths required")
    paths = {name: Path(path) for name, path in accepted.items()}
    require(all(path.is_absolute() for path in paths.values()), "acceptance receipt paths must be absolute")
    before = json.loads(paths["before"].read_text())
    after = json.loads(paths["after"].read_text())
    require(before["status"] == "H1_FULLCORE_VALIDATION_PASS"
            and before["input_receipts"]["build-01/hardware-inputs.json"] == PIN_SHA["before"]
            and before["emu_sha256"] == EMU_SHA["before"], "before acceptance mismatch")
    recheck = paths["after"].parent / "recheck-01/result.json"
    checked = json.loads(recheck.read_text())
    require(after["status"] == "R3_DIV_GATE_FULLCORE_PASS"
            and checked["status"] == "O2_G3_OFFLINE_RECHECK_PASS" and checked["g3_complete"]
            and checked["hardware_pins_sha256"] == PIN_SHA["after"]
            and after["emu_sha256"] == EMU_SHA["after"], "after acceptance mismatch")
    paths["after_recheck"] = recheck
    return paths

def validate_pair(a, b):
    for key in ("dependency_files", "config", "NUM_CORES", "EMU_THREADS", "JVM_XMX",
                "BUILD_JOBS", "VDOT_T14_FUSED_INPUT", "VDOT_T12_TRACE",
                "VDOT_T13_TRACE", "VDOT_O2_ELASTIC", "VDOT_O1_HANDOFF",
                "VDOT_O1_TRACE", "VDOT_O2_TRACE"):
        require(a[key] == b[key], "non-H1 build difference: " + key)
    require(a["files"].keys() == b["files"].keys(), "source inventory differs")
    changed = {k for k in a["files"] if a["files"][k] != b["files"][k]}
    require(changed == {"src/main/scala/xiangshan/backend/exu/ExeUnit.scala"}, "unexpected source difference")
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
    return rows[0].replace(str(products), "<BUILD>")

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

def build_profile(before_build, after_build, *, acceptance_paths=None):
    dirs = {"before": Path(before_build), "after": Path(after_build)}
    products = {"before": BEFORE_PRODUCTS, "after": AFTER_PRODUCTS}
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
    validate_pair(pins["before"], pins["after"])
    require(sources["before"]["build.sc"] == sources["after"]["build.sc"], "build.sc differs")
    require(commands["before"] == commands["after"], "actual compiler/Verilator command differs")
    versions = {}
    for tool in ("java", "mill", "verilator", "clang", "make", "python", "firtool"):
        paths = [folder / (tool + "-version.log") for folder in dirs.values()]
        require(paths[0].read_bytes() == paths[1].read_bytes(), "tool version differs: " + tool)
        versions[tool] = sha(paths[0])
        for p in paths:
            bind(p)
    changed = {k for k in manifests["before"].keys() | manifests["after"].keys()
               if manifests["before"].get(k) != manifests["after"].get(k)}
    require(changed == {"build/emu", "build/rtl/ExeUnit_9.sv", "build/rtl/ExeUnit_17.sv", "build/rtl/SimTop.sv",
                        "build/rtl/NewCSR.sv", "build/rtl/LogPerfEndpoint.sv"},
            "unexpected generated change")
    rtl = {m: products[m] / "rtl" for m in products}
    texts = lambda name: [(rtl[m] / name).read_text() for m in ("before", "after")]
    a, b = texts("SimTop.sv")
    require(re.sub(r"(?m)^\s*//.*\n", "", a) == re.sub(r"(?m)^\s*//.*\n", "", b),
            "top-level functional RTL differs")
    a, b = texts("NewCSR.sv")
    normalize = lambda t: re.sub(r"gitCommitSHA = 40'h[0-9A-F]+", "gitCommitSHA = <BUILD_ID>", t)
    require(normalize(a) == normalize(b), "CSR difference beyond embedded Git identity")
    for t in texts("LogPerfEndpoint.sv"):
        monitor_effect_check(t)
    a, b = texts("VDotElastic.sv")
    require(a == b and "reg  [31:0]  rPacket_res_data;" in b, "H1 arithmetic/storage changed")
    require("assign io_out_bits_res_data = {96'h0, rPacket_res_data};" in b, "public128 output missing")
    a, b = texts("ExeUnit_9.sv")
    a = re.sub(r"  wire\s+_GEN_0 = io_out_ready & _Fdiv_io_out_valid;\n", "", a)
    a = a.replace("_GEN_0", "(io_out_ready & _Fdiv_io_out_valid)")
    # The only extra parent change is expression inlining. Prove its Boolean
    # statement equivalence for the shared subexpression, then normalize parentheses.
    compact = lambda t: re.sub(r"\s+", "", t).replace("(io_out_ready&_Fdiv_io_out_valid)", "io_out_ready&_Fdiv_io_out_valid")
    require(compact(a) == compact(b), "unexpected scalar FDiv generation difference")
    a, b = texts("ExeUnit_17.sv")
    require("wire         elasticDivCancelled =" not in a and "wire         elasticDivCancelled =" in b,
            "DIV gate candidate not generated")
    require(b.count("| elasticDivCancelled)") == 2, "both DIV holds must clear on matching cancel")
    for leaf in ("constantin.txt", "plusArgs"):
        a, b = BEFORE_PRODUCTS / leaf, AFTER_PRODUCTS / leaf
        require(a.read_bytes() == b.read_bytes(), "runtime auxiliary differs: " + leaf)
        bind(a); bind(b)
    accepted = verify_accepted_receipts(DEFAULT_ACCEPTANCE if acceptance_paths is None else acceptance_paths)
    for p in accepted.values():
        bind(p)
    return files, dict(status="BEFORE_AFTER_BUILD_PROFILE_PASS",
        source_commits=SOURCE_COMMITS, emu_sha256=EMU_SHA,
        emulator_paths={m: str(products[m] / "emu") for m in products},
        hardware_source_files_per_build=429, common_dependency_files=21236,
        source_differences=["src/main/scala/xiangshan/backend/exu/ExeUnit.scala"], generated_differences=sorted(changed),
        source_review="Only DIV cancel clock-hold source change; all Git blobs verified",
        generated_review="DIV gate, reviewed scalar FDiv expression inlining, top comments, Git ID, and input-only log monitor differ; no whole-design formal equivalence claim",
        diagnostic_monitor_external_ports="input-only; no DPI/force or external writes except diagnostic fwrite",
        randomized_initialization="seed=1 and explicit reset; random register layout can differ; deterministic replays checked",
        tool_version_sha256=versions, normalized_verilator_command=commands["before"],
        common_optimization="OPT_FAST=-O3 OPT_SLOW=-O0", observer_flags_differ_by_mode=False,
        original_pins_unchanged=True, before_binary_relocated=True)
