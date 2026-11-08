"""重新生成技术图：python -X utf8 build_figs.py [ID ...] [--out DIR] [--png DIR]

每个 ID 对应本目录下的脚本（S2-03 -> s2_03.py）。不写 ID 时生成全部 23 张。
- 可编辑的 SVG 写到本目录的 svg/；
- 文字转曲线、无嵌入字体的 PDF 默认写到 ../unified-20261107/（报告实际引用的位置），
  用 --out 可改写到其他目录，便于先比对再替换；
- --png DIR 另存 220 dpi 预览图。
脚本会按 sections/ 中 \\reportfigure 的高度上限报告每张图印刷时的缩放比例。
依赖：Python 3、PyMuPDF（fitz）、Inkscape 1.4（在 PATH 中），以及字体 Noto Serif SC、Times New Roman。"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))          # latex-v1 工程根
SVG_DIR = os.path.join(HERE, "svg")
TEX = os.path.join(ROOT, "sections")
TEXT_W = 162.0                                                   # 版心宽度（mm）

ap = argparse.ArgumentParser()
ap.add_argument("ids", nargs="*")
ap.add_argument("--out", default=os.path.join(ROOT, "figures", "unified-20261107"))
ap.add_argument("--png", default=None)
args = ap.parse_args()

limits = {}
for f in os.listdir(TEX):
    if f.endswith(".tex"):
        for fid, h in re.findall(r"reportfigure\{([^}]*)\}\{[^}]*\}\{([\d.]+)cm\}",
                                 open(os.path.join(TEX, f), encoding="utf8").read()):
            limits[fid] = float(h) * 10

ids = args.ids or sorted(f[:-3].upper().replace("_", "-") for f in os.listdir(HERE)
                         if re.fullmatch(r"s\d_\d\d(_sup)?\.py", f))
os.makedirs(SVG_DIR, exist_ok=True)
os.makedirs(args.out, exist_ok=True)
if args.png:
    os.makedirs(args.png, exist_ok=True)
env = dict(os.environ, TU_OUT=SVG_DIR)
failed = 0
for fid in ids:
    script = fid.lower().replace("-", "_") + ".py"
    r = subprocess.run([sys.executable, "-X", "utf8", script], cwd=HERE, env=env,
                       capture_output=True, text=True, encoding="utf8")
    if r.returncode:
        print(fid, "SCRIPT FAILED\n", r.stderr)
        failed += 1
        continue
    warn = [l for l in r.stdout.splitlines() if l.startswith("WARN")]
    svg = os.path.join(SVG_DIR, fid + ".svg")
    pdf = os.path.join(args.out, fid + ".pdf")
    # 经临时 ASCII 目录调用 Inkscape，避免部分安装方式不接受非 ASCII 路径
    tmp = tempfile.mkdtemp(prefix="tufig-")
    shutil.copy(svg, os.path.join(tmp, "in.svg"))
    subprocess.run(["inkscape", os.path.join(tmp, "in.svg"), "--export-type=pdf", "--export-text-to-path",
                    "--export-filename=" + os.path.join(tmp, "out.pdf")], capture_output=True, check=True)
    shutil.move(os.path.join(tmp, "out.pdf"), pdf)
    shutil.rmtree(tmp, ignore_errors=True)
    page = fitz.open(pdf)[0]
    assert not page.get_fonts(), fid + " has embedded fonts"
    if args.png:
        page.get_pixmap(dpi=220).save(os.path.join(args.png, fid + ".png"))
    w, h = page.rect.width / 72 * 25.4, page.rect.height / 72 * 25.4
    lim = limits.get(fid)
    scale = min(TEXT_W / w, lim / h) if lim else TEXT_W / w
    lim_txt = f"{lim:.0f} mm" if lim else "未在正文中使用"
    print(f"{fid}: {w:.0f}x{h:.1f} mm, limit {lim_txt}, print scale {scale:.3f}"
          + ("" if not warn else "\n  " + "\n  ".join(warn)))
sys.exit(1 if failed else 0)
