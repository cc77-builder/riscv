from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parent
compiler = shutil.which("xelatex")
if compiler is None:
    raise SystemExit("Install XeLaTeX and the licensed SimSun / Times New Roman fonts.")
(root / "output").mkdir(exist_ok=True)
for name in ("main", "stage1", "stage2", "stage3"):
    for iteration in (1, 2):
        subprocess.run(
            [compiler, "-interaction=nonstopmode", "-halt-on-error",
             "-output-directory=output", name + ".tex"],
            cwd=root, check=True,
        )
