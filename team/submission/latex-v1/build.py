"""Compile the current report sources without regenerating their content."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
NAMES = {
    "main": "三阶段技术文档_合订本.pdf",
    "stage1": "第一阶段_执行日志与过程文档.pdf",
    "stage2": "第二阶段_设计与基础测试文档.pdf",
    "stage3": "第三阶段_协同仿真与性能分析.pdf",
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default=shutil.which("xelatex"))
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--documents", nargs="+", choices=tuple(NAMES),
                        default=list(NAMES))
    args = parser.parse_args()
    if not args.compiler:
        parser.error("Install XeLaTeX (TeX Live with ctex, fandol and tex-gyre), "
                     "then add it to PATH or pass --compiler PATH.")
    compiler = str(Path(args.compiler).resolve())
    output = (ROOT / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for name in ("OMP_NUM_THREADS", "OMP_THREAD_LIMIT", "OPENBLAS_NUM_THREADS"):
        env[name] = "1"
    version = subprocess.run([compiler, "--version"], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True).stdout.splitlines()
    receipt = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "compiler": version[0] if version else Path(compiler).name,
        "source_directory": ".",
        "font_profile": "TeX Gyre + Fandol (TeX Live open fonts)",
        "passes_per_document": 3, "documents": [],
    }
    for name in args.documents:
        print("Compiling " + name + " ...", flush=True)
        for iteration in (1, 2, 3):
            command = [compiler, *(["-no-pdf"] if iteration < 3 else []),
                       "-interaction=nonstopmode", "-halt-on-error",
                       "-file-line-error", "-recorder",
                       "-output-directory=" + str(output), name + ".tex"]
            result = subprocess.run(command, cwd=ROOT, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log = output / (name + "-pass" + str(iteration) + ".txt")
            log.write_bytes(result.stdout)
            if result.returncode:
                raise SystemExit("Compilation failed; inspect " + str(log))
        pdf = output / (name + ".pdf")
        destination = output / NAMES[name]
        shutil.copy2(pdf, destination)
        data = destination.read_bytes()
        receipt["documents"].append({
            "name": name, "file": destination.name, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
        print("Created " + destination.name, flush=True)
    receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "build-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Compilation complete. See output/build-receipt.json.", flush=True)

if __name__ == "__main__":
    main()
