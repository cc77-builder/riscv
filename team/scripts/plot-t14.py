"""Plot all paired hardware effects once, alongside the RVV control."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def require(ok, message):
    if not ok:
        raise ValueError(message)


def plot(args):
    sys.path.insert(0, str(args.qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    result = json.loads((args.ablation / "result.json").read_text())
    require(result["status"] == "T14_IDENTICAL_IMAGE_ABLATION_PASS", "ablation not accepted")
    path = args.ablation / "paired-windows.json"
    all_rows = json.loads(path.read_text())
    require(len(all_rows) == 1404, "wrong complete input size")
    rows = [row for row in all_rows if row["replay"] == 0]
    require(len(rows) == 468, "wrong replay selection")
    for row in all_rows:
        require(row["baseline_cycles"] > 0 and row["candidate_cycles"] > 0, "nonpositive cycles")
        ratio = row["baseline_cycles"] / row["candidate_cycles"]
        require(math.isfinite(ratio) and ratio == row["hardware_speedup"], "ratio drift")
    order = [("single", 1), ("chain", 16), ("chain", 64), ("chain", 256),
             ("batch", 1), ("batch", 8), ("batch", 32),
             ("stream", 1), ("stream", 16), ("stream", 64),
             ("generic", 1), ("generic", 16), ("generic", 64)]
    display = dict(single="Single", chain="Chain", batch="Independent batch",
                   stream="Load / dot / store", generic="CSR wrapper")
    labels = []
    for key in order:
        group = [row for row in rows if (row["scenario"], row["n"]) == key]
        counts = {row["dots"] for row in group}
        require(len(counts) == 1, "dot count drift")
        count = counts.pop()
        labels.append(f"{display[key[0]]}  |  {count} " + ("dot" if count == 1 else "dots"))
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "svg.fonttype": "none", "pdf.fonttype": 42, "axes.linewidth": 0.7,
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    })
    fig, axes = plt.subplots(1, 2, sharex=True, sharey=True,
                             figsize=(7.2047244094, 5.7086614173))
    fig.subplots_adjust(left=0.29, right=0.98, bottom=0.15, top=0.88, wspace=0.17)
    phases = [("first", "First", "#8b9095", "o", 0.22),
              ("warmup", "Warm-up", "#b77c32", "x", 0),
              ("measured", "Measured", "#27658a", "D", -0.22)]
    drawing = []
    for ax, method, title, panel in zip(axes, ("vdot", "rvv"), ("VDOT", "RVV control"), ("a", "b")):
        for phase, label, color, marker, offset in phases:
            xs, ys = [], []
            for index, key in enumerate(order):
                group = [row for row in rows if row["method"] == method and row["phase"] == phase
                         and (row["scenario"], row["n"]) == key]
                require(len(group) == (12 if phase == "measured" else 3), "missing phase/dataset/round")
                group.sort(key=lambda row: (row["dataset"], row["repeat"]))
                for rank, row in enumerate(group):
                    y = index + offset + (rank - (len(group) - 1) / 2) * 0.009
                    xs.append(row["hardware_speedup"])
                    ys.append(y)
                    drawing.append(dict(row, display_y=y))
            ax.scatter(xs, ys, s=13 if phase == "measured" else 16,
                       color=color, marker=marker, linewidths=0.65, label=label, zorder=3)
        ax.axvline(1, color="#555555", lw=0.8, ls="--", zorder=1)
        ax.grid(axis="x", color="#e6e8ea", lw=0.5, zorder=0)
        ax.set_title(title, pad=8)
        ax.annotate(panel, xy=(0, 1), xycoords="axes fraction", xytext=(-9, 8),
                    textcoords="offset points", fontsize=9, fontweight="bold",
                    ha="left", va="bottom", annotation_clip=False)
        ax.set_xlabel("Baseline cycles / candidate cycles")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    axes[0].set_yticks(range(len(order)), labels)
    axes[0].set_ylim(len(order) - 0.5, -0.5)
    values = [row["hardware_speedup"] for row in rows]
    low, high = min(min(values), 1), max(max(values), 1)
    margin = max((high - low) * 0.07, 0.02)
    axes[0].set_xlim(low - margin, high + margin)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.64, 0.98),
               ncol=3, columnspacing=1.5, handletextpad=0.4)
    fig.text(0.29, 0.065, ">1: candidate faster; <1: slower. Identical program images.",
             ha="left", va="bottom", fontsize=7)
    fig.text(0.29, 0.035, "3 inputs; first, warm-up and 4 measured rounds. All fresh replays agree; replay 0 drawn.",
             ha="left", va="bottom", fontsize=7)
    args.output.mkdir(parents=True, exist_ok=False)
    stem = args.output / "t14-hardware-ablation"
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig, json_out=str(stem) + ".alignment.json",
        overlay_svg=str(stem) + ".alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5,
        require_panel_labels=True, strict=True)
    fig.savefig(str(stem) + ".svg")
    fig.savefig(str(stem) + ".pdf")
    fig.savefig(str(stem) + ".png", dpi=600)
    fig.savefig(str(stem) + ".tiff", dpi=600)
    with (args.output / "source-data.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, list(drawing[0]))
        writer.writeheader()
        writer.writerows(drawing)
    (args.output / "source-receipt.json").write_text(json.dumps(dict(
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        input_rows=len(all_rows), drawn_rows=len(drawing),
        predicate="replay == 0; all methods, configurations, input datasets and phases retained",
        exclusion_reason="The other two fresh replays are identical, retained in the full archive, and not independent observations.",
        center="raw paired ratio", uncertainty="none: all selected observations are drawn",
        vertical_offsets="phase offsets plus deterministic within-phase separation; horizontal values never jittered",
        export_mm=[183, 145], backend="Python/Matplotlib"), indent=2) + "\n")
    plt.close(fig)
    print("T14_FIGURE_RENDERED rows=" + str(len(drawing)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("ablation", "qa-scripts", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    plot(parser.parse_args())
