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

MAKE_ARGS = ["CONFIG=MinimalConfig", "NUM_CORES=1", "EMU_THREADS=1", "JVM_XMX=12G",
             "OPT_FAST=-O3", "OPT_SLOW=-O0", "EMU_TRACE=0", "WITH_CHISELDB=0",
             "WITH_CONSTANTIN=0", "WITH_ROLLINGDB=0", "-j2"]


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


def probe_tools():
    """Resolve compiler payloads, rejecting unbound launcher indirection."""
    result = {}
    for role, command, option in (("cxx", "g++", "--version"), ("cc", "gcc", "--version"),
        ("java", "java", "-version"), ("mill", "mill", "--version"),
        ("verilator", "verilator", "--version"),
        ("firtool", str(Path.home()/".cache/llvm-firtool/1.62.1/bin/firtool"), "--version")):
        path = shutil.which(command)
        if not path:
            raise ValueError("missing compiler " + command)
        path = Path(path).resolve()
        # The supported Mill 0.12 launcher is itself the executable JAR. A
        # shell wrapper's hash would leave its actual compiler payload unbound.
        if role == "mill" and not zipfile.is_zipfile(path):
            raise ValueError("mill must resolve directly to its executable JAR payload")
        result[role] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           version=subprocess.check_output([str(path), option], text=True, stderr=subprocess.STDOUT))
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


def capture(root):
    # Probe in precisely the environment used by the build; explicitly pass
    # these compiler paths to Make instead of merely recording clang --version.
    probe = ("import json,runpy; helper=runpy.run_path(" + repr(str(Path(__file__).resolve())) +
             "); print(json.dumps(helper['probe_tools']()))")
    command = "source team/scripts/activate.sh\npython3 -c " + shlex.quote(probe)
    clean = environment()
    captured = json.loads(subprocess.check_output(["bash", "-c", command], cwd=root, text=True, env=clean))
    metadata = Path(root) / ".mill-version"
    return dict(schema=2, make_args=list(MAKE_ARGS), compilers=captured,
                launch_metadata={".mill-version": dict(sha256=hashlib.sha256(metadata.read_bytes()).hexdigest(),
                                                       value=metadata.read_text(encoding="utf-8").strip())},
                environment_sha256=hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest(),
                recipe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def validate(contract):
    if not isinstance(contract, dict) or contract.get("schema") != 2 or contract.get("make_args") != MAKE_ARGS:
        raise ValueError("unsupported native build contract")
    if not all(re.fullmatch(r"[0-9a-f]{64}", contract.get(key, ""))
               for key in ("environment_sha256", "recipe_sha256")):
        raise ValueError("incomplete native build contract")
    metadata = contract.get("launch_metadata", {})
    if (set(metadata) != {".mill-version"} or not isinstance(metadata[".mill-version"], dict)
            or not metadata[".mill-version"].get("value")
            or not re.fullmatch(r"[0-9a-f]{64}", metadata[".mill-version"].get("sha256", ""))):
        raise ValueError("missing Mill launcher metadata identity")
    for role in ("cxx", "cc", "java", "mill", "verilator", "verilator_bin", "firtool"):
        tool = contract.get("compilers", {}).get(role, {})
        if (not PurePosixPath(tool.get("path", "")).is_absolute() or not tool.get("version")
                or not re.fullmatch(r"[0-9a-f]{64}", tool.get("sha256", ""))):
            raise ValueError("missing native tool identity: " + role)


def make_command(contract, products=None):
    validate(contract)
    args = ["make", "emu", *MAKE_ARGS,
            "CXX=" + contract["compilers"]["cxx"]["path"],
            "CC=" + contract["compilers"]["cc"]["path"]]
    if products is not None:
        args.append("BUILD_DIR=" + str(products))
    return shlex.join(args) + "\n"


def verify(root, expected):
    if capture(root) != expected:
        raise ValueError("native compiler/build contract changed")
