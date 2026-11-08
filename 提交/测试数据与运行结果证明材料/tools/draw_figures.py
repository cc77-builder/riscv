"""根据 data/ 中的窗口数据和事件记录绘制证明材料的三张数据图。

用法：python tools/draw_figures.py
依赖：matplotlib、numpy。字体：Times New Roman 与 Noto Sans SC。
输出：figures/fig01_microbench.png、fig02_c8.png、fig03_control_events.png（300 dpi）。
图题写在证明材料正文中，图内只保留坐标、数据标签和图例。
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"

plt.rcParams.update({
    "font.family": ["Times New Roman", "Noto Sans SC"],
    "font.size": 10,
    "axes.titlesize": 10.5,
    "axes.labelsize": 10,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.unicode_minus": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "path",
})
BLUE, ORANGE, GREEN, PURPLE, AMBER = "#1f5a99", "#c8552b", "#2b8a6e", "#7a5aa6", "#d39a1f"
GRID = "#e4e4e4"


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=300, facecolor="white")
    plt.close(fig)


# 图 1：四类微基准的全部正式窗口
bench = [r for r in read_csv(ROOT / "data" / "微基准全部窗口.csv") if r["phase"] == "measured"]
scenes = [("single", "单次点积"), ("chain", "依赖链（256次）"),
          ("batch", "四路独立批量（128次）"), ("stream", "加载、计算、存储流（64次）")]
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4))
fig.subplots_adjust(left=0.10, right=0.98, bottom=0.06, top=0.90, wspace=0.32, hspace=0.58)
for ax, (key, label) in zip(axes.flat, scenes):
    part = [r for r in bench if r["scenario"] == key]
    means = {}
    for pos, method, color, marker in [(0, "vdot", BLUE, "o"), (1, "rvv", ORANGE, "s")]:
        values = np.array([float(r["cycles"]) for r in part if r["method"] == method])
        means[method] = values.mean()
        ax.scatter(pos + np.linspace(-0.16, 0.16, len(values)), values, s=16, color=color,
                   marker=marker, zorder=3, linewidths=0.4, edgecolors="white")
        ax.plot([pos - 0.24, pos + 0.24], [values.mean()] * 2, color=color, lw=1.2, zorder=2)
        ax.annotate(f"{values.mean():g}", (pos, values.max()), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=9)
    top = max(float(r["cycles"]) for r in part) * 1.28
    ax.set_ylim(0, top)
    ax.set_xlim(-0.55, 1.55)
    ax.set_xticks([0, 1], ["VDot", "RVV"])
    ax.grid(axis="y", color=GRID, zorder=0)
    ax.set_title(f"{label}\n加速比 {means['rvv'] / means['vdot']:.4f}×", pad=8)
    ax.set_ylabel("DUT周期")
save(fig, "fig01_microbench")

# 图 2：8×32 GEMV 调用的全部正式窗口
c8 = read_csv(ROOT / "data" / "C8最终尺寸正式窗口.csv")
rows = [("firstdot V2", "首段初始化版本（VDot）", PURPLE, "^"),
        ("C8", "C8配置复用版本（VDot）", BLUE, "o"),
        ("最快 RVV", "较快的RVV实现", ORANGE, "s")]
fig, ax = plt.subplots(figsize=(7.2, 2.5))
fig.subplots_adjust(left=0.25, right=0.96, bottom=0.22, top=0.95)
for pos, (key, label, color, marker) in enumerate(rows):
    values = np.array([float(r["cycles"]) for r in c8 if r["implementation"] == key])
    ax.scatter(values, pos + np.linspace(-0.18, 0.18, len(values)), s=20, color=color, marker=marker,
               edgecolors="white", linewidths=0.4, zorder=3)
    ax.vlines(values.mean(), pos - 0.26, pos + 0.26, color=color, lw=1.2)
    ax.annotate(f"均值 {values.mean():g}", (values.max(), pos), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=9.5)
ax.set_xlim(240, 320)
ax.set_yticks(range(len(rows)), [r[1] for r in rows])
ax.set_ylim(len(rows) - 0.5, -0.5)
ax.set_xlabel("一次8×32调用的DUT周期")
ax.grid(axis="x", color=GRID, zorder=0)
save(fig, "fig02_c8")

# 图 3：控制诊断中的流水重叠与两槽取消
events = [dict(r, cycle=int(r["cycle"]), seq=int(r["seq"])) for r in read_csv(ROOT / "data" / "控制事件时间线.csv")]
styles = {"ACCEPT": (BLUE, "o", "接受"), "MOVE": (AMBER, "s", "P槽移入R槽"),
          "RESPONSE": (GREEN, "D", "响应"), "KILL": (ORANGE, "X", "取消")}
fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.9), gridspec_kw={"width_ratios": [1.25, 1]})
fig.subplots_adjust(left=0.09, right=0.98, bottom=0.30, top=0.88, wspace=0.32)
for ax, seqs, title in [(axes[0], [1, 2, 3], "连续三笔请求重叠执行"),
                        (axes[1], [182, 183], "P、R两槽同一周期取消")]:
    part = [e for e in events if e["seq"] in seqs]
    for row, seq in enumerate(seqs):
        own = sorted((e for e in part if e["seq"] == seq), key=lambda e: e["cycle"])
        ax.plot([e["cycle"] for e in own], [row] * len(own), color="#b8b8b8", lw=1.0, zorder=1)
        for e in own:
            color, marker, _ = styles[e["event"]]
            ax.scatter(e["cycle"], row, s=46, color=color, marker=marker, zorder=3,
                       edgecolors="white", linewidths=0.5)
    cycles = sorted({e["cycle"] for e in part})
    ax.set_xticks(cycles, [str(c) for c in cycles])
    ax.set_xlim(cycles[0] - 0.6, cycles[-1] + 0.6)
    ax.set_yticks(range(len(seqs)), [f"请求{s}" for s in seqs])
    ax.set_ylim(len(seqs) - 0.5, -0.5)
    ax.set_xlabel("全局周期")
    ax.set_title(title, pad=6)
    ax.grid(axis="x", color=GRID, zorder=0)
axes[0].axvspan(9172.7, 9173.3, color="#dbe7f3", zorder=0)
handles = [plt.Line2D([], [], color=c, marker=m, ls="", markersize=7, label=l) for c, m, l in styles.values()]
fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.0))
save(fig, "fig03_control_events")
print("figures written to", OUT)
