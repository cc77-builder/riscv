"""T14-only F2v burst sweep; preserve the original T12 generator and goldens."""
import argparse
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path

BASE = Path(__file__).with_name("generate.py")


def emit(output):
    spec = importlib.util.spec_from_file_location("t14_original_t12", BASE)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    with redirect_stdout(io.StringIO()):
        original.emit(output)
    path = output / "sequences.S"
    lines = path.read_text().splitlines()
    expanded = []
    bursts = []
    for line in lines:
        if line == "vfmv.v.f v28,ft1":
            burst = 1 + (len(bursts) // 4) % 16
            bursts.append(burst)
            expanded.extend([line] * burst)
        else:
            expanded.append(line)
    if len(bursts) != 128 or set(bursts) != set(range(1, 17)):
        raise ValueError("original F2v layout changed")
    path.write_text("\n".join(expanded) + "\n")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["wb_sweep"] = dict(version="t14-f2v-burst-1-to-16-v1", bursts=bursts,
        semantics="Repeat the exact 3.5f broadcast to v28; unchanged golden registers and vdot retirement count.")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in output.iterdir() if p.name in ("sequences.S", "sequences.h", "manifest.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    emit(parser.parse_args().output)
