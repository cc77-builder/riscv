#!/usr/bin/env python3
"""Draw the frozen C8 buffer contract as one precise, original vector figure.

This script renders documentation only. It does not compile or run project code.
All SVG coordinates are millimetres. Font sizes are converted from points.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
STEM = "S3-06-c8-layout"
W, H = 160.0, 145.0
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

C = {
    "ink": "#24364A", "muted": "#52687B", "line": "#7790A4",
    "grid": "#B9CCD9", "rule": "#CCD8E1", "blue": "#315D85",
    "teal": "#237D82", "matrix": "#EBF3FA", "vector": "#DEF1EF",
    "zero": "#F3F6F8", "result": "#DCEAF7", "white": "#FFFFFF",
}

def tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"

svg = ET.Element(tag("svg"), {
    "width": f"{W:g}mm", "height": f"{H:g}mm", "viewBox": f"0 0 {W:g} {H:g}",
    "version": "1.1", "role": "img", "aria-labelledby": "title description",
})
ET.SubElement(svg, tag("title"), {"id": "title"}).text = "C8 公共调用、编译选择与输入输出布局"
ET.SubElement(svg, tag("desc"), {"id": "description"}).text = (
    "xs_c8_gemv_8x32 is a compile-time alias. XS_C8_GEMV_FORCE_RVV=0 or absent selects "
    "the VDot implementation; 1 selects RVV. packed_ax contains row-major signed INT8 "
    "A[8][32], 256 bytes, immediately followed by x[32], 32 bytes. output_slots contains "
    "eight 16-byte slots. Each complete 128-bit slot contains zero in bits 127:32 and "
    "the signed dot product in bits 31:0. Bit fields are drawn high-to-low, not as an "
    "endianness diagram. Both buffers are 16-byte aligned and non-overlapping. VLEN=128."
)
defs = ET.SubElement(svg, tag("defs"))
marker = ET.SubElement(defs, tag("marker"), {
    "id": "arrow", "viewBox": "0 0 8 8", "refX": "6.8", "refY": "4",
    "markerWidth": "2.1", "markerHeight": "2.1", "orient": "auto", "markerUnits": "userSpaceOnUse",
})
ET.SubElement(marker, tag("path"), {"d": "M 0 0 L 8 4 L 0 8 Z", "fill": C["muted"]})

def el(name: str, attrs: dict[str, object], parent=svg):
    return ET.SubElement(parent, tag(name), {k: str(v) for k, v in attrs.items()})

def rect(x, y, width, height, fill, stroke=C["line"], sw=0.22, ident=None):
    attrs = {"x": x, "y": y, "width": width, "height": height,
             "fill": fill, "stroke": stroke, "stroke-width": sw}
    if ident:
        attrs["id"] = ident
    return el("rect", attrs)

def line(x1, y1, x2, y2, color=C["line"], sw=0.22, dash=None, arrow=False):
    attrs = {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
             "stroke": color, "stroke-width": sw, "fill": "none"}
    if dash:
        attrs["stroke-dasharray"] = dash
    if arrow:
        attrs["marker-end"] = "url(#arrow)"
    return el("line", attrs)

def path(d, color=C["line"], sw=0.22, dash=None, arrow=False):
    attrs = {"d": d, "stroke": color, "stroke-width": sw, "fill": "none"}
    if dash:
        attrs["stroke-dasharray"] = dash
    if arrow:
        attrs["marker-end"] = "url(#arrow)"
    return el("path", attrs)

def text(x, y, content, pt=11.5, color=C["ink"], anchor="start", mono=False, ident=None):
    attrs = {"x": x, "y": y, "font-family": "DejaVu Sans Mono" if mono else "Noto Sans CJK SC",
             "font-size": f"{pt * 25.4 / 72:.6f}", "font-weight": "400",
             "fill": color, "text-anchor": anchor}
    if ident:
        attrs["id"] = ident
    t = el("text", attrs)
    t.text = content
    return t

rect(0, 0, W, H, C["white"], stroke="none", sw=0)

# A public source-level call alias, with build-time alternatives only.
text(80, 7, "xs_c8_gemv_8x32(packed_ax, output_slots)", pt=11.5, anchor="middle", mono=True)
text(80, 15, "XS_C8_GEMV_FORCE_RVV", pt=11.5, anchor="middle", mono=True, color=C["muted"])
path("M 80 17.5 V 20 H 39 V 27", color=C["muted"], dash="1.1 0.85", arrow=True)
path("M 80 20 H 121 V 27", color=C["muted"], dash="1.1 0.85", arrow=True)
text(19, 24.4, "0（缺省）", color=C["muted"])
text(130, 24.4, "1", color=C["muted"])
text(80, 25.5, "编译时绑定", anchor="middle", color=C["muted"])
text(39, 33, "VDot 实现", pt=12, anchor="middle", color=C["blue"])
text(121, 33, "RVV 实现", pt=12, anchor="middle", color=C["teal"])
line(22, 35.5, 56, 35.5, color=C["blue"], sw=0.45)
line(104, 35.5, 138, 35.5, color=C["teal"], sw=0.45)
line(4, 40, 156, 40, color=C["rule"], sw=0.25)

# Buffer names and true total sizes; the lower graphics apply to either build.
text(46.5, 47.3, "packed_ax · 288 B", pt=12, anchor="middle", mono=True)
text(124.5, 47.3, "output_slots · 128 B", pt=12, anchor="middle", mono=True)
text(47, 55.5, "A[8][32] · 256 B", anchor="middle", mono=True, color=C["blue"])
text(125, 55.5, "8 槽 × 16 B", anchor="middle", color=C["muted"])

IX, IY, CELL_W, ROW_H = 15.0, 72.0, 2.0, 6.0
IW, IH = 32 * CELL_W, 9 * ROW_H
text(4, 62.3, "偏移", color=C["muted"])
text(4, 68.4, "/B", color=C["muted"], mono=True)
for j in (0, 7, 15, 23, 31):
    text(IX + (j + 0.5) * CELL_W, 68.4, str(j), anchor="middle", color=C["muted"])

# Every byte cell is represented exactly once: 8x32 A cells, then 32 x cells.
for i in range(9):
    fill = C["matrix"] if i < 8 else C["vector"]
    for j in range(32):
        rect(IX + j * CELL_W, IY + i * ROW_H, CELL_W, ROW_H,
             fill, stroke=C["grid"], sw=0.12, ident=f"input-byte-{i*32+j}")
    text(11.3, IY + (i + 0.5) * ROW_H + 1.45, str(i * 32),
         anchor="end", mono=True, color=C["muted"] if i < 8 else C["teal"])
rect(IX, IY, IW, 8 * ROW_H, "none", stroke=C["blue"], sw=0.28, ident="input-A-256B")
rect(IX, IY + 8 * ROW_H, IW, ROW_H, "none", stroke=C["teal"], sw=0.28, ident="input-x-32B")
for j in (8, 16, 24):
    line(IX + j * CELL_W, IY, IX + j * CELL_W, IY + IH, color=C["line"], sw=0.20)
line(47, 126.5, 47, 129.3, color=C["teal"], sw=0.25)
text(47, 134.4, "x[32] · 32 B", anchor="middle", mono=True, color=C["teal"])

# Output slot rows increase in byte offset. Within each row, bit numbers decrease
# left-to-right (standard bit-field notation), without asserting byte endianness.
OX, OY, OW, OH = 97.0, 72.0, 56.0, 54.0
ZERO_W, RESULT_W, SLOT_H = OW * 96 / 128, OW * 32 / 128, OH / 8
text(84, 62.3, "偏移", color=C["muted"])
text(84, 68.4, "/B", color=C["muted"], mono=True)
text(OX + ZERO_W/2, 62.3, "高96位清零", anchor="middle", color=C["muted"])
text(OX + ZERO_W + RESULT_W/2, 62.3, "低32位", anchor="middle", color=C["blue"])
text(OX + ZERO_W/2, 68.4, "127:32", anchor="middle", color=C["muted"])
text(OX + ZERO_W + RESULT_W/2, 68.4, "31:0", anchor="middle", color=C["muted"])
for i in range(8):
    y = OY + i * SLOT_H
    rect(OX, y, ZERO_W, SLOT_H, C["zero"], stroke=C["grid"], sw=0.16,
         ident=f"slot-{i}-bits127-32-zero")
    rect(OX + ZERO_W, y, RESULT_W, SLOT_H, C["result"], stroke=C["grid"], sw=0.16,
         ident=f"slot-{i}-bits31-0-result")
    text(93.3, y + SLOT_H/2 + 1.45, str(i * 16), anchor="end", mono=True, color=C["muted"])
    text(OX + ZERO_W/2, y + SLOT_H/2 + 1.45, "0", anchor="middle", color=C["muted"], mono=True)
    text(OX + ZERO_W + RESULT_W/2, y + SLOT_H/2 + 1.45, f"S[{i}]", anchor="middle", mono=True, color=C["blue"])
rect(OX, OY, OW, OH, "none", stroke=C["line"], sw=0.28, ident="output-8x16B")
line(OX + ZERO_W, OY, OX + ZERO_W, OY + OH, color=C["line"], sw=0.28)
text(125, 134.4, "S[i]：第 i 行点积补码", anchor="middle", color=C["muted"])

text(80, 142.2, "两缓冲区各自 16 B 对齐、互不重叠；VLEN = 128", anchor="middle", color=C["muted"])

svg_path = ROOT / f"{STEM}.svg"
ET.indent(svg, space="  ")
svg_path.write_bytes(ET.tostring(svg, encoding="utf-8", xml_declaration=True))

# Inkscape is the mature SVG renderer; Poppler rasterizes that same PDF once.
pdf_path = ROOT / f"{STEM}.pdf"
subprocess.run(["inkscape", str(svg_path), "--export-area-page", "--export-text-to-path", "--export-type=pdf",
                f"--export-filename={pdf_path}"], check=True, capture_output=True)
subprocess.run(["pdftoppm", "-r", "300", "-singlefile", "-png", str(pdf_path), str(ROOT / STEM)],
               check=True, capture_output=True)

geometry = {
    "canvas_mm": [W, H], "font_points": [11.5, 12.0],
    "input_A_shape": [8, 32], "input_A_bytes": 256, "input_x_bytes": 32,
    "input_bytes": 288, "input_x_offset_bytes": 256,
    "input_byte_cells_drawn": 9*32,
    "input_row_offsets_bytes": [i*32 for i in range(9)],
    "output_slots": 8, "slot_bytes": 16, "output_bytes": 128,
    "output_slot_offsets_bytes": [i*16 for i in range(8)],
    "output_high_zero_bits": 96, "output_low_result_bits": 32,
    "output_drawn_high_width_mm": ZERO_W, "output_drawn_low_width_mm": RESULT_W,
    "output_drawn_width_ratio": ZERO_W/RESULT_W,
    "output_bit_orientation": "127 on left to 0 on right; not a byte-endianness drawing",
    "input_A_row_order": "row-major", "buffers_align_bytes": 16,
    "buffers_nonoverlap": True, "VLEN_bits": 128,
}
assert geometry["output_drawn_width_ratio"] == 3
assert len(svg.findall(f".//{tag('rect')}[@id]")) == 288 + 2 + 16 + 1
files = {}
for name in (f"{STEM}.svg", f"{STEM}.pdf", f"{STEM}.png", "render.py"):
    raw = (ROOT/name).read_bytes()
    files[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
print(json.dumps({"geometry": geometry, "files": files}, ensure_ascii=False, indent=2))
