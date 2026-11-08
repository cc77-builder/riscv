"""把含英文子标题的截图组图改为中文子标题（2026-11-08）。
原图中的位图从原 PDF 无损提取到 shots/，此处只重排版式并换成中文子标题；截图内容不变。
子标题字体与正文一致（TeX Gyre Termes + FandolSong），按图在正文中的实际缩放反算字号，使印刷后约为 10 pt。
用法：python -X utf8 screenshot_figs.py [ID ...] [--out DIR] [--png DIR]
默认把 PDF 写到 ../unified-20261107/（报告实际引用的位置）；--out 可改写到其他目录先比对。
依赖：Python 3、PyMuPDF（fitz），以及 TeX Live 的 xelatex（含 TeX Gyre、Fandol 字体）。"""
import argparse
import os
import shutil
import subprocess
import tempfile
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "shots")
W = 460.0                 # 版心宽（pt），与原组图一致
TEXT_W_MM = 162.0
TARGET_PT = 10.0          # 子标题印刷字号

# ID: (正文中的高度上限 cm, 行列表)；每行为 [(图片文件, 子标题, 宽度占比), ...]
FIGS = {
    "S1-03": (8.5, [[("S1-03-1.png", "2026年10月9日原始运行的终端输出", 1.0)]]),
    "S1-04": (16.0, [[("S1-04-1.png", "（a）输出握手：游标19626 ps，三个事件位置均可见", 1.0)],
                     [("S1-04-2.png", "（b）输入游标19625 ps", 0.489), ("S1-04-3.png", "（c）提交游标19631 ps", 0.489)]]),
    "S1-05": (10.0, [[("S1-05-1.png", "（a）负数用例：输出游标25461 ps", 1.0)],
                     [("S1-05-2.png", "（b）边界用例：输出游标33010 ps", 1.0)]]),
    "SUP-S2-ARITH": (12.0, [[("SUP-S2-ARITH-1.png", "（a）受测版本的VDotProducts源码", 1.0)],
                            [("SUP-S2-ARITH-2.png", "（b）受测版本的VDotReduce源码", 1.0)]]),
    "SUP-S2-STATE": (13.0, [[("SUP-S2-STATE-1.png", "（a）槽寄存器与32位结果状态", 1.0)],
                            [("SUP-S2-STATE-2.png", "（b）握手与取消条件", 1.0)],
                            [("SUP-S2-STATE-3.png", "（c）状态更新与原P内容转入R", 1.0)]]),
    "SUP-S2-MODEL": (11.0, [[("SUP-S2-MODEL-1.png", "主机参考模型的单元测试输出", 1.0)]]),
    "SUP-S2-OVERLAP": (11.0, [[("SUP-S2-OVERLAP-1.png", "全核运行中两槽观察器的日志摘录", 1.0)]]),
    "SUP-S3-SUMMARY": (9.0, [[("SUP-S3-SUMMARY-1.png", "（a）FU、父级与全核范围：R5验收矩阵的证据列", 1.0)],
                             [("SUP-S3-SUMMARY-2.png", "（b）成本范围：R5验收矩阵的证据列", 1.0)]]),
}

PRE = r"""\documentclass[border=0pt]{standalone}
\usepackage{fontspec,xeCJK,graphicx}
\setmainfont{texgyretermes-regular.otf}
\setCJKmainfont{FandolSong-Regular.otf}
\begin{document}
"""


def tex_for(rows, size):
    lead = size * 1.25
    body = [r"\begin{minipage}{%.2fpt}\centering\fontsize{%.2f}{%.2f}\selectfont" % (W, size, lead)]
    for r, row in enumerate(rows):
        if r:
            body.append(r"\par\vspace{%.2fpt}" % (size * 1.1))
        cells = []
        for img, cap, frac in row:
            w = W * frac
            cells.append(r"\begin{minipage}[t]{%.2fpt}\centering %s\par\vspace{%.2fpt}"
                         r"\includegraphics[width=%.2fpt]{%s}\end{minipage}" % (w, cap, size * 0.45, w, img))
        body.append(r"\hfill".join(cells) if len(cells) > 1 else cells[0])
    body.append(r"\end{minipage}")
    return PRE + "\n".join(body) + "\n\\end{document}\n"


def build(fid, size):
    tmp = tempfile.mkdtemp(prefix="shotfig-")
    for row in FIGS[fid][1]:
        for img, _, _ in row:
            shutil.copy(os.path.join(SRC, img), tmp)
    open(os.path.join(tmp, "f.tex"), "w", encoding="utf-8").write(tex_for(FIGS[fid][1], size))
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "f.tex"], cwd=tmp,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(fid + " failed:\n" + r.stdout[-1500:])
    pdf = os.path.join(tmp, "f.pdf")
    rect = fitz.open(pdf)[0].rect
    return tmp, pdf, rect


ap = argparse.ArgumentParser()
ap.add_argument("ids", nargs="*")
ap.add_argument("--out", default=os.path.join(HERE, "..", "unified-20261107"))
ap.add_argument("--png", default=None)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
if args.png:
    os.makedirs(args.png, exist_ok=True)

for fid, (limit_cm, _) in FIGS.items():
    if args.ids and fid not in args.ids:
        continue
    size = TARGET_PT
    for _ in range(3):           # 字号影响组图高度，迭代到印刷字号稳定
        tmp, pdf, rect = build(fid, size)
        w_mm, h_mm = rect.width / 72 * 25.4, rect.height / 72 * 25.4
        scale = min(TEXT_W_MM / w_mm, limit_cm * 10 / h_mm)
        new = TARGET_PT / scale
        if abs(new - size) < 0.05:
            break
        shutil.rmtree(tmp, ignore_errors=True)
        size = new
    else:
        tmp, pdf, rect = build(fid, size)
        w_mm, h_mm = rect.width / 72 * 25.4, rect.height / 72 * 25.4
        scale = min(TEXT_W_MM / w_mm, limit_cm * 10 / h_mm)
    shutil.copy(pdf, os.path.join(args.out, fid + ".pdf"))
    if args.png:
        fitz.open(pdf)[0].get_pixmap(dpi=150).save(os.path.join(args.png, fid + ".png"))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{fid}: {w_mm:.0f}x{h_mm:.0f} mm, print scale {scale:.3f}, subtitle {size:.1f}pt -> {size * scale:.1f}pt printed")
