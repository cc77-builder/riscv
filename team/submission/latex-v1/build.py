from pathlib import Path
import argparse
import shutil
import subprocess

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description="Compile the three-stage reports using XeLaTeX.")
parser.add_argument("--compiler", default=shutil.which("xelatex"))
parser.add_argument("--output-dir", default="output")
parser.add_argument("--documents", nargs="+", choices=("main", "stage1", "stage2", "stage3"), default=["main", "stage1", "stage2", "stage3"])
args = parser.parse_args()
if not args.compiler:
    raise SystemExit("Install XeLaTeX and licensed SimSun / Times New Roman fonts, or pass --compiler.")
out = (root / args.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
names = {"main": "三阶段技术文档_合订本.pdf", "stage1": "第一阶段_执行日志与过程文档.pdf", "stage2": "第二阶段_设计与基础测试文档.pdf", "stage3": "第三阶段_协同仿真与性能分析.pdf"}
for name in args.documents:
    for iteration in (1, 2, 3):
        result = subprocess.run([args.compiler, "-interaction=nonstopmode", "-halt-on-error", "-output-directory=" + str(out), name + ".tex"], cwd=root, capture_output=True)
        (out / (name + "-pass" + str(iteration) + ".txt")).write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise SystemExit("Compilation failed; see " + str(out / (name + "-pass" + str(iteration) + ".txt")))
    shutil.copy2(out / (name + ".pdf"), out / names[name])
    print(name + " PDF compiled", flush=True)
