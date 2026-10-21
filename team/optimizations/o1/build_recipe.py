"""Explicit, comparable native compiler settings for new O1/T14 builds.

Legacy receipts remain valid only for their frozen workflow. This contract is
required when selecting a new O1 reference build instead of the historical EMU.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import zipfile
import copy

MAKE_ARGS = ["CONFIG=MinimalConfig", "NUM_CORES=1", "EMU_THREADS=1", "JVM_XMX=12G",
             "OPT_FAST=-O3", "OPT_SLOW=-O0", "EMU_TRACE=0", "WITH_CHISELDB=0",
             "WITH_CONSTANTIN=0", "WITH_ROLLINGDB=0", "-j2"]
SPLIT_MAKE_ARGS = [arg if arg != "JVM_XMX=12G" else "JVM_XMX=6G" for arg in MAKE_ARGS]
SPLIT_MAKE_ARGS.insert(4, "JVM_XSS=16m")
SPLIT_PHASES = [
    dict(name="scala-compile", mill_args=["-i", "-Djvm-xmx=6G", "-Djvm-xss=16m", "xiangshan.test.compile"],
         environment=dict(JAVA_OPTS="-Xmx3g -XX:ActiveProcessorCount=2", JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=2")),
    dict(name="fir-elaborate", make_args=["sim-verilog", "CONFIG=MinimalConfig", "NUM_CORES=1", "JVM_XMX=6G",
         "JVM_XSS=16m", "CHISEL_TARGET=chirrtl", "-j1"],
         environment=dict(JAVA_OPTS="-Xmx1g -XX:ActiveProcessorCount=2", JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=2")),
    dict(name="fir-lower", firtool_args=["build/rtl/SimTop.fir", "--format=fir", "--split-verilog", "-o", "build/rtl",
         "--mlir-disable-threading", "--repl-seq-mem", "--repl-seq-mem-file=SimTop.sv.conf", "-O=release",
         "--disable-annotation-unknown", "--lowering-options=explicitBitcast,disallowLocalVariables,disallowPortDeclSharing,locationInfoStyle=none"]),
    dict(name="memory-generate", script="scripts/gen_sep_mem.sh",
         arguments=["scripts/vlsi_mem_gen", "build/rtl/SimTop.sv.conf", "build/rtl"]),
    dict(name="rtl-postprocess", implementation="root-Makefile-default-assertions-and-git-comment-v1"),
    dict(name="native-compile", make_args=["emu", *SPLIT_MAKE_ARGS],
         environment=dict(JAVA_OPTS="-Xmx1g -XX:ActiveProcessorCount=2", JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=2")),
]


def environment():
    """Only tool bootstrap settings may enter a new native build.

    In particular, do not inherit Make variables, BASH_ENV, preload/include
    paths or PGO flags. activate.sh reconstructs project paths inside this
    environment; its bytes belong to the hardware input inventory.
    """
    names = ("HOME", "PATH", "JAVA_HOME", "JAVA_OPTS", "JAVA_TOOL_OPTIONS",
             "COURSIER_REPOSITORIES", "TEAM_XS_ENV_ROOT")
    result = {key: os.environ[key] for key in names if key in os.environ}
    result.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", TZ="UTC")
    return result


def probe_tools(profile="direct"):
    """Resolve compiler payloads, rejecting unbound launcher indirection."""
    result = {}
    selected = [("cxx", "g++", "--version"), ("cc", "gcc", "--version"),
        ("java", "java", "-version"), ("bash", "bash", "--version"),
        ("sh", "/bin/sh", "-c"), ("time", "/usr/bin/time", "--version"), ("mill", "mill", "--version"),
        ("verilator", "verilator", "--version"),
        ("firtool", str(Path.home()/".cache/llvm-firtool/1.62.1/bin/firtool"), "--version")]
    if profile == "split-v1":
        selected += [("python", "python3", "--version"), ("make", "make", "--version")]
    for role, command, option in selected:
        path = shutil.which(command)
        if not path:
            raise ValueError("missing compiler " + command)
        path = Path(path).resolve()
        # The supported Mill 0.12 launcher is itself the executable JAR. A
        # shell wrapper's hash would leave its actual compiler payload unbound.
        if role == "mill" and not zipfile.is_zipfile(path):
            raise ValueError("mill must resolve directly to its executable JAR payload")
        command = ([result["sh"]["path"], str(path), option] if role == "mill" else [str(path), option])
        if role == "sh":
            # GNU time uses execvp, whose ENOEXEC fallback is /bin/sh for
            # Mill's executable JAR. Dash has no --version option; record a
            # successful shell probe together with its executable digest.
            command.append("printf '%s\\n' 'POSIX shell ENOEXEC fallback'")
        result[role] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           version=subprocess.check_output(command, text=True, stderr=subprocess.STDOUT))
    # Ubuntu's verilator executable is a Perl launcher; normal (non-debug)
    # operation dispatches to its sibling binary. The restricted environment
    # excludes VERILATOR_ROOT/VERILATOR_BIN, so there is no inherited override.
    payload = Path(result["verilator"]["path"]).with_name("verilator_bin")
    if not payload.is_file():
        raise ValueError("missing sibling Verilator compiler payload: " + str(payload))
    payload = payload.resolve()
    result["verilator_bin"] = dict(path=str(payload), sha256=hashlib.sha256(payload.read_bytes()).hexdigest(),
        version=subprocess.check_output([str(payload), "--version"], text=True, stderr=subprocess.STDOUT))
    return result


def capture(root, profile="direct"):
    # Probe in precisely the environment used by the build; explicitly pass
    # these compiler paths to Make instead of merely recording clang --version.
    if profile not in ("direct", "split-v1"):
        raise ValueError("unsupported native recipe profile")
    probe = ("import json,runpy; helper=runpy.run_path(" + repr(str(Path(__file__).resolve())) +
             "); print(json.dumps(helper['probe_tools'](" + repr(profile) + ")))")
    command = "source team/scripts/activate.sh\npython3 -c " + shlex.quote(probe)
    clean = environment()
    captured = json.loads(subprocess.check_output(["bash", "-c", command], cwd=root, text=True, env=clean))
    metadata = Path(root) / ".mill-version"
    result = dict(schema=2, make_args=list(MAKE_ARGS), compilers=captured,
                mill_launch=[captured["sh"]["path"], captured["mill"]["path"]],
                launch_metadata={".mill-version": dict(sha256=hashlib.sha256(metadata.read_bytes()).hexdigest(),
                                                       value=metadata.read_text(encoding="utf-8").strip())},
                environment_sha256=hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest(),
                recipe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if profile == "split-v1":
        result.update(schema=3, profile=profile, make_args=list(SPLIT_MAKE_ARGS), phases=copy.deepcopy(SPLIT_PHASES),
                      split_script_sha256=hashlib.sha256(Path(__file__).with_name("split_recipe.py").read_bytes()).hexdigest())
    return result


def validate(contract):
    if not isinstance(contract, dict):
        raise ValueError("unsupported native build contract")
    if contract.get("schema") == 2:
        if contract.get("make_args") != MAKE_ARGS or any(name in contract for name in ("profile", "phases", "split_script_sha256")):
            raise ValueError("unsupported native build contract")
    elif contract.get("schema") == 3:
        if (contract.get("profile") != "split-v1" or contract.get("make_args") != SPLIT_MAKE_ARGS or
                contract.get("phases") != SPLIT_PHASES or
                not re.fullmatch(r"[0-9a-f]{64}", contract.get("split_script_sha256", ""))):
            raise ValueError("unsupported split native build contract")
    else:
        raise ValueError("unsupported native build contract")
    if not all(re.fullmatch(r"[0-9a-f]{64}", contract.get(key, ""))
               for key in ("environment_sha256", "recipe_sha256")):
        raise ValueError("incomplete native build contract")
    metadata = contract.get("launch_metadata", {})
    if (set(metadata) != {".mill-version"} or not isinstance(metadata[".mill-version"], dict)
            or not metadata[".mill-version"].get("value")
            or not re.fullmatch(r"[0-9a-f]{64}", metadata[".mill-version"].get("sha256", ""))):
        raise ValueError("missing Mill launcher metadata identity")
    roles = ("cxx", "cc", "java", "bash", "sh", "time", "mill", "verilator", "verilator_bin", "firtool")
    if contract["schema"] == 3:
        roles += ("python", "make")
    for role in roles:
        tool = contract.get("compilers", {}).get(role, {})
        if (not PurePosixPath(tool.get("path", "")).is_absolute() or not tool.get("version")
                or not re.fullmatch(r"[0-9a-f]{64}", tool.get("sha256", ""))):
            raise ValueError("missing native tool identity: " + role)
    if contract.get("mill_launch") != [contract["compilers"]["sh"]["path"], contract["compilers"]["mill"]["path"]]:
        raise ValueError("missing bound Mill shell launch command")


def make_overrides(contract):
    validate(contract)
    return ["SHELL=" + contract["compilers"]["bash"]["path"],
            # Make expands TIMELOG in its own scope. Shell quoting preserves
            # the expression until then, including output paths with spaces.
            "TIME_CMD=" + shlex.join([contract["compilers"]["time"]["path"], "-avp", "-o", "$(TIMELOG)"]),
            "CXX=" + contract["compilers"]["cxx"]["path"],
            "CC=" + contract["compilers"]["cc"]["path"]]


def make_command(contract, products=None):
    validate(contract)
    executable = contract["compilers"]["make"]["path"] if contract["schema"] == 3 else "make"
    args = [executable, "emu", *contract["make_args"], *make_overrides(contract)]
    if products is not None:
        args.append("BUILD_DIR=" + str(products))
    return shlex.join(args) + "\n"


def execution_command(contract, pins_path, output):
    """Select an explicit fresh recipe; split never resumes a direct build."""
    validate(contract)
    if contract["schema"] == 2:
        return make_command(contract)
    return shlex.join([contract["compilers"]["python"]["path"], str(Path(__file__).with_name("split_recipe.py").resolve()),
                       "--pins", str(pins_path), "--output", str(Path(output) / "split")]) + "\n"


def verify(root, expected):
    validate(expected)
    if capture(root, expected.get("profile", "direct")) != expected:
        raise ValueError("native compiler/build contract changed")
