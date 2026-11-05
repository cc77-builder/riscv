#!/usr/bin/env python3
"""Draw one precise static-equivalence figure from the frozen C8 relink record.

Coordinates use millimetres. The PT_LOAD bar alone is proportional to bytes.
Call/input grids preserve logical source order and do not assert memory spacing.
This renders documentation only; it does not rebuild or run the project.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
STEM = "S3-08-relink-structure"
W, H = 160.0, 178.0
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
COL_X = (31.0, 74.0, 117.0)
COL_W = 38.0
FILE_B, ZERO_B, MEM_B = 30024, 1416, 31440
FILE_W = COL_W * FILE_B / MEM_B
ZERO_W = COL_W * ZERO_B / MEM_B
ROW_SHAPES = ("8×32", "4×8", "16×64", "4×13")
INPUT_B = (288, 40, 1088, 65)
DATA_COLORS = ("#E5EFF8", "#E1F0ED", "#F0EDE5")
C = {"ink": "#24364A", "muted": "#52687B", "line": "#7790A4",
     "grid": "#B9CCD9", "rule": "#CCD8E1", "blue": "#315D85",
     "load": "#E5EFF8", "zero": "#F1F3F5", "debug": "#F3F4F5",
     "white": "#FFFFFF"}

def tag(name):
    return f"{{{NS}}}{name}"

svg = ET.Element(tag("svg"), {"width": f"{W:g}mm", "height": f"{H:g}mm",
    "viewBox": f"0 0 {W:g} {H:g}", "version": "1.1", "role": "img",
    "aria-labelledby": "title description"})
ET.SubElement(svg, tag("title"), {"id": "title"}).text = "C8三方静态装载内容与调用输入对照"
ET.SubElement(svg, tag("desc"), {"id": "description"}).text = (
    "Original qualified fixture, same-source rebuild, and actual SDK linkage are "
    "compared statically. Each PT_LOAD memory range consists of 30024 file-backed "
    "bytes and 1416 zero-filled bytes, in exact horizontal proportion. All three "
    "31440-byte BIN images are byte-identical. Forty-eight 64-byte call records "
    "are shown in original sequence, rows 8x32, 4x8, 16x64, 4x13, and dataset "
    "groups d0,d1,d2. Four records per dataset are not relabeled into a common "
    "method order: the first group retains its original special ordering. "
    "Twelve packed input arrays have sizes 288,40,1088,65 bytes in the same row "
    "order, three datasets each. Grid widths represent logical objects rather "
    "than physical byte sizes or addresses. Only the named debug sections differ "
    "outside allocated content; complete original ELF files are not identical. "
    "627 counts protected files. This historical static qualification introduced "
    "zero EMU, NEMU or full-core runs and permits reuse of the original fixture evidence."
)

def el(name, attrs):
    return ET.SubElement(svg, tag(name), {k: str(v) for k, v in attrs.items()})

def rect(x, y, width, height, fill, stroke=C["line"], sw=0.22, ident=None):
    a = {"x": x, "y": y, "width": width, "height": height, "fill": fill,
         "stroke": stroke, "stroke-width": sw}
    if ident:
        a["id"] = ident
    return el("rect", a)

def line(x1, y1, x2, y2, color=C["line"], sw=0.22, dash=None):
    a = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "stroke": color,
         "stroke-width": sw, "fill": "none"}
    if dash:
        a["stroke-dasharray"] = dash
    return el("line", a)

def text(x, y, value, pt=11.5, color=C["ink"], anchor="start", mono=False):
    e = el("text", {"x": x, "y": y, "font-family": "DejaVu Sans Mono" if mono else "Noto Sans CJK SC",
         "font-size": f"{pt * 25.4 / 72:.6f}", "font-weight": "400", "fill": color,
         "text-anchor": anchor})
    e.text = value
    return e

def compare_signs(y, value="="):
    for x in (71.5, 114.5):
        text(x, y, value, anchor="middle", color=C["muted"])

def dataset_heads(y):
    for x in COL_X:
        for d in range(3):
            text(x + (d + 0.5) * COL_W / 3, y, f"d{d}", anchor="middle", mono=True, color=C["muted"])

rect(0, 0, W, H, C["white"], stroke="none", sw=0)
for x, name in zip(COL_X, ("原夹具 ELF", "同源重建 ELF", "SDK 接入 ELF")):
    text(x + COL_W/2, 7.5, name, pt=12, anchor="middle")
    line(x, 11.5, x + COL_W, 11.5, color=C["rule"], sw=0.28)

# One PT_LOAD, with actual file-backed / zero-filled byte proportions.
text(4, 22.1, "PT_LOAD", mono=True)
text(4, 28.4, "装载内存", color=C["muted"])
for n, x in enumerate(COL_X):
    rect(x, 17, FILE_W, 12, C["load"], ident=f"load-{n}-file-30024")
    rect(x + FILE_W, 17, ZERO_W, 12, C["zero"], ident=f"load-{n}-zero-1416")
    for yy in (18.5, 21, 23.5, 26):
        line(x + FILE_W + 0.15, yy + 1.2, x + COL_W - 0.15, yy,
             color=C["line"], sw=0.14)
    text(x + FILE_W/2, 24.5, "30,024 B", anchor="middle", mono=True, color=C["blue"])
compare_signs(24.5)
text(80, 36.5, "蓝区为文件内容；末端为 1,416 B 零填充", anchor="middle", color=C["muted"])
text(80, 43.5, "入口 0x80000000；地址、权限、对齐一致", anchor="middle", color=C["muted"])

# BIN comparison is separately labeled; no whole-ELF equality is asserted.
text(4, 53, "BIN", mono=True)
text(4, 59, "全字节", color=C["muted"])
for n, x in enumerate(COL_X):
    rect(x, 48.5, COL_W, 10, "#FAFCFE", ident=f"bin-{n}-31440")
    text(x + COL_W/2, 55.3, "31,440 B", anchor="middle", mono=True)
compare_signs(55.3)
line(4, 64, 156, 64, color=C["rule"], sw=0.25)

# Exact logical sequence: four shape rows, three datasets, four records each.
# Cell position alone preserves order, including the deliberately reordered first
# 8x32-d0 group. No common method ordering is invented by labels or colors.
text(4, 72, "调用记录")
dataset_heads(72)
CALL_Y, CALL_H = 76.0, 5.0
for row, shape in enumerate(ROW_SHAPES):
    text(4, CALL_Y + row*CALL_H + 3.85, shape, color=C["muted"])
for n, x in enumerate(COL_X):
    for row in range(4):
        for col in range(12):
            seq = row*12 + col
            rect(x + col*COL_W/12, CALL_Y + row*CALL_H, COL_W/12, CALL_H,
                 DATA_COLORS[col//4], stroke=C["grid"], sw=0.15,
                 ident=f"call-{n}-seq-{seq:02d}")
    rect(x, CALL_Y, COL_W, 4*CALL_H, "none", sw=0.25)
    for d in (1, 2):
        line(x+d*COL_W/3, CALL_Y, x+d*COL_W/3, CALL_Y+4*CALL_H, sw=0.3)
compare_signs(87.5)
text(80, 103, "每格 64 B · 每份 48 条 · 按原 seq 逐项核对", anchor="middle", color=C["muted"])

# Input array identity has the same shape/dataset organization. Cell values are
# actual array byte lengths; equal cell widths are deliberately not a size scale.
text(4, 111, "输入数组")
dataset_heads(111)
INPUT_Y, INPUT_H = 115.0, 5.0
for row, shape in enumerate(ROW_SHAPES):
    text(4, INPUT_Y + row*INPUT_H + 3.85, shape, color=C["muted"])
for n, x in enumerate(COL_X):
    for row, size in enumerate(INPUT_B):
        for d in range(3):
            rect(x + d*COL_W/3, INPUT_Y + row*INPUT_H, COL_W/3, INPUT_H,
                 DATA_COLORS[d], stroke=C["grid"], sw=0.18,
                 ident=f"input-{n}-shape-{row}-dataset-{d}")
            text(x+(d+0.5)*COL_W/3, INPUT_Y+row*INPUT_H+3.85,
                 str(size), mono=True, anchor="middle")
    rect(x, INPUT_Y, COL_W, 4*INPUT_H, "none", sw=0.25)
compare_signs(126.5)
text(80, 142, "每份 12 个数组：地址与内容一致；格内为 B（非比例）", anchor="middle", color=C["muted"])

# Debug differences are visually isolated from the compared loaded content.
# The difference symbol is about the three original ELF files, not their BIN.
line(4, 146.5, 156, 146.5, color=C["rule"], dash="1.2 0.9", sw=0.25)
text(4, 155.5, "非装载", color=C["muted"])
for n, x in enumerate(COL_X):
    rect(x, 150, COL_W, 8, C["debug"], stroke=C["rule"], sw=0.22,
         ident=f"debug-{n}-outside-loaded-content")
    text(x+COL_W/2, 155.5, "调试信息", anchor="middle", color=C["muted"])
compare_signs(155.5, "≠")
text(80, 165, ".debug_info / .debug_line / .debug_line_str", anchor="middle", mono=True, color=C["muted"])
text(80, 173.2, "627 个受保护文件 · SDK 新增 EMU：0", anchor="middle", color=C["muted"])

svg_path = ROOT / f"{STEM}.svg"
ET.indent(svg, space="  ")
svg_path.write_bytes(ET.tostring(svg, encoding="utf-8", xml_declaration=True))
pdf_path = ROOT / f"{STEM}.pdf"
subprocess.run(["inkscape", str(svg_path), "--export-area-page", "--export-text-to-path",
    "--export-type=pdf", f"--export-filename={pdf_path}"], check=True, capture_output=True)
subprocess.run(["pdftoppm", "-r", "300", "-singlefile", "-png", str(pdf_path), str(ROOT/STEM)],
    check=True, capture_output=True)

assert FILE_B + ZERO_B == MEM_B
assert abs(FILE_W + ZERO_W - COL_W) < 1e-12
assert len([e for e in svg if e.get("id", "").startswith("call-")]) == 3*48
assert len([e for e in svg if e.get("id", "").startswith("input-")]) == 3*12
files = {}
for name in (f"{STEM}.svg", f"{STEM}.pdf", f"{STEM}.png", "render.py"):
    b = (ROOT/name).read_bytes()
    files[name] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
print(json.dumps({"geometry": {"canvas_mm": [W,H], "font_points": [11.5,12],
    "columns": 3, "load_file_bytes": FILE_B, "load_zero_fill_bytes": ZERO_B,
    "load_memory_bytes": MEM_B, "load_file_width_mm": FILE_W,
    "load_zero_width_mm": ZERO_W, "call_records_per_column": 48,
    "call_record_bytes": 64, "call_grid_rows_cols": [4,12],
    "shape_row_order": ROW_SHAPES, "input_arrays_per_column": 12,
    "input_grid_rows_cols": [4,3], "input_bytes_by_row": INPUT_B,
    "dataset_order": [0,1,2], "grid_order": "logical source order, not physical layout"},
    "files": files}, ensure_ascii=False, indent=2))
