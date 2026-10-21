"""Complete input inventory for live O2 builds; archives retain frozen tools."""
import hashlib
from pathlib import Path
import subprocess
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "o1"))
from build_inputs import HARDWARE, hardware_files, verify_dependencies, verify_hardware_files
import build_recipe


def dependency_snapshot(root):
    root = Path(root)
    pins = verify_dependencies(root)
    files = {}
    modules = []
    for name, revision in sorted(pins.items()):
        child = root / name
        modules.append(dict(path=name, head=revision, pin=revision))
        tracked = subprocess.check_output(["git", "-C", str(child), "ls-files", "-z"]).split(b"\0")
        for raw in tracked:
            if raw:
                path = child / raw.decode()
                if path.is_file():
                    files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return modules, dict(sorted(files.items()))


def verify(root, pins):
    verify_hardware_files(root, pins["files"])
    _, dependencies = dependency_snapshot(root)
    if dependencies != pins["dependency_files"]:
        raise ValueError("dependency compiler inventory differs")
    build_recipe.validate(pins.get("native_build_contract"))
