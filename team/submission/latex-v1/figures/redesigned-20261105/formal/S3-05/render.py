#!/usr/bin/env python3
"""One normalized-cycle chart of the frozen four-scenario after microbenchmark.

This only renders recorded documentation data. It does not run a benchmark.
The common linear 0--100% axis uses each scenario's RVV mean as denominator.
"""
from __future__ import annotations

from decimal import Decimal, getcontext
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch
from fontTools.ttLib import TTCollection

getcontext().prec = 40
ROOT = Path(__file__).resolve().parent
STEM = "S3-05-normalized-cycles"
WIDTH_MM, HEIGHT_MM = 160, 132
SOURCE_COMMIT = "e2c2e8d5fa9a92c5d99c3c3e3f5399d60a115c63"
SOURCE_BLOB = "5a30c92eacad99ab317f0f15825b8aa0a0d6e34e"
SOURCE_PATH = "team/optimizations/o2/r3-div-gate/performance/results/summary.csv"

# Exact decimal means and integer cycle sums from the four 'after' rows only.
DATA = [
    {"scenario": "single", "label": "单次点积\nsingle × 1", "dots": 1,
     "vdot": "71", "rvv": "85.25", "vdot_sum": 852, "rvv_sum": 1023},
    {"scenario": "chain", "label": "依赖链\nchain × 256", "dots": 256,
     "vdot": "1857", "rvv": "5440.5", "vdot_sum": 22284, "rvv_sum": 65286},
    {"scenario": "batch", "label": "独立批量\nbatch × 128", "dots": 128,
     "vdot": "221", "rvv": "678", "vdot_sum": 2652, "rvv_sum": 8136},
    {"scenario": "stream", "label": "访存流\nstream × 64", "dots": 64,
     "vdot": "1127.5", "rvv": "1133", "vdot_sum": 13530, "rvv_sum": 13596},
]
N = 12
ROWS = []
for d in DATA:
    v, r = Decimal(d["vdot"]), Decimal(d["rvv"])
    assert v == Decimal(d["vdot_sum"])/N
    assert r == Decimal(d["rvv_sum"])/N
    pct = 100*v/r
    speedup = r/v
    assert speedup == Decimal(d["rvv_sum"])/Decimal(d["vdot_sum"])
    ROWS.append({**d, "samples_per_method": N, "vdot_relative_cycles_percent": str(pct),
                 "vdot_percentage_label": f"{pct:.2f}%", "speedup_ratio_of_sums": str(speedup)})

# Matplotlib reads the SC face from the installed collection. The temporary OTF
# is only for metrics; SVG retains the actual family name and editable text.
with tempfile.TemporaryDirectory(prefix="xiangshan-microbench-font-") as td:
    collection = TTCollection("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    face = next(f for f in collection.fonts if f["name"].getDebugName(1) == "Noto Sans CJK SC")
    font_path = Path(td)/"NotoSansCJKSC-Regular.otf"
    face.save(font_path)
    font_manager.fontManager.addfont(str(font_path))
    plt.rcParams.update({
        "font.family": "Noto Sans CJK SC", "font.size": 11.5, "font.weight": "normal",
        "axes.labelsize": 11.5, "xtick.labelsize": 11.5, "ytick.labelsize": 11.5,
        "text.color": "#24364A", "axes.labelcolor": "#52687B", "xtick.color": "#52687B",
        "ytick.color": "#24364A", "svg.fonttype": "none", "svg.hashsalt": "xs-s3-05-normalized-v1",
        "axes.unicode_minus": False,
    })
    fig = plt.figure(figsize=(WIDTH_MM/25.4, HEIGHT_MM/25.4), facecolor="white")
    ax = fig.add_axes([0.28, 0.22, 0.59, 0.65])
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, 3.6)
    ax.set_xscale("linear")
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_yticks([3, 2, 1, 0], [d["label"] for d in DATA])
    ax.tick_params(axis="y", length=0, pad=10)
    ax.tick_params(axis="x", length=3, width=0.6, pad=5)
    for name in ("left", "right", "top"):
        ax.spines[name].set_visible(False)
    ax.spines["bottom"].set_color("#8CA1B3")
    ax.spines["bottom"].set_linewidth(0.6)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#D7E1E9", linewidth=0.55)
    ax.axvline(100, color="#8CA1B3", linewidth=0.7, linestyle=(0,(3,3)), zorder=1)

    RVV_FILL, RVV_EDGE = "#B8CFE2", "#6C94B4"
    VDOT_FILL = "#287E86"
    for y, d in zip((3,2,1,0), ROWS):
        pct = float(Decimal(d["vdot_relative_cycles_percent"]))
        y_rvv, y_vdot = y + 0.16, y - 0.16
        ax.barh(y_rvv, 100, height=0.28, color=RVV_FILL, edgecolor=RVV_EDGE,
                linewidth=0.5, zorder=3)
        ax.barh(y_vdot, pct, height=0.28, color=VDOT_FILL, edgecolor=VDOT_FILL,
                linewidth=0.5, zorder=3)
        r_text = f"{Decimal(d['rvv']):,f}"
        v_text = f"{Decimal(d['vdot']):,f}"
        ax.text(3, y_rvv, r_text, ha="left", va="center", fontsize=11.5,
                color="#24364A", zorder=4)
        ax.text(3, y_vdot, v_text, ha="left", va="center", fontsize=11.5,
                color="white", zorder=4)
        ax.text(pct + 1.5, y_vdot, d["vdot_percentage_label"], ha="left", va="center",
                fontsize=11.5, color=VDOT_FILL, clip_on=False, zorder=4)

    legend = fig.legend(handles=[Patch(facecolor=RVV_FILL, edgecolor=RVV_EDGE, linewidth=0.5,
                                      label="RVV = 100%"),
                                Patch(facecolor=VDOT_FILL, edgecolor=VDOT_FILL, linewidth=0.5,
                                      label="VDot")],
                        loc="upper center", bbox_to_anchor=(0.595,0.965), ncol=2,
                        frameon=False, fontsize=12, handlelength=1.4, handleheight=0.65,
                        handletextpad=0.6, columnspacing=1.6, borderaxespad=0)
    ax.set_xlabel("相对本场景 RVV 周期（越短越好）", labelpad=9)
    fig.text(0.5, 0.035, "每场景每方法 n = 12；条内为平均窗口 cycles", ha="center",
             va="center", fontsize=11.5, color="#52687B")

    svg_path = ROOT/f"{STEM}.svg"
    fig.savefig(svg_path, format="svg", facecolor="white", transparent=False,
                metadata={"Date": None, "Creator": "Matplotlib; frozen XiangShan microbenchmark documentation"})
    plt.close(fig)

pdf_path = ROOT/f"{STEM}.pdf"
subprocess.run(["inkscape", str(svg_path), "--export-area-page", "--export-text-to-path",
    "--export-type=pdf", f"--export-filename={pdf_path}"], check=True, capture_output=True)
subprocess.run(["pdftoppm", "-r", "300", "-singlefile", "-png", str(pdf_path), str(ROOT/STEM)],
    check=True, capture_output=True)
files = {}
for name in (f"{STEM}.svg", f"{STEM}.pdf", f"{STEM}.png", "render.py"):
    b=(ROOT/name).read_bytes()
    files[name]={"bytes":len(b), "sha256":hashlib.sha256(b).hexdigest()}
print(json.dumps({"source_commit":SOURCE_COMMIT, "source_git_blob":SOURCE_BLOB,
    "source_path":SOURCE_PATH, "selected_mode":"after", "canvas_mm":[WIDTH_MM,HEIGHT_MM],
    "normal_font_points":[11.5,12], "linear_axis_range_percent":[0,100],
    "rows":ROWS, "files":files}, ensure_ascii=False, indent=2))
