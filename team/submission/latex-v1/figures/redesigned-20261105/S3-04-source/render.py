#!/usr/bin/env python3
"""Render the S3-04 event illustration from adjacent data.json.

Run: python3 render.py
Outputs: S3-04-dual-window.svg, .png and .pdf in this directory.
The SVG is 160 mm wide; its viewBox uses points, so font-size is physical pt.
PNG is a 240 dpi preview. SVG construction uses only Python's standard library;
PNG/PDF rendering uses Inkscape and the installed Noto Sans CJK SC family.
No experiment or simulator is invoked. data.json links the archived figure
and the fixed raw-log source record beside the report figures.
"""
from pathlib import Path
import html
import json
import os
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
d = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
events = {event["id"]: event for event in d["csr_events"]}
style = d["style"]
width_pt = style["width_mm"] * 72.0 / 25.4
height_pt = style["height_pt"]
height_mm = height_pt * 25.4 / 72.0
start = events["I0"]["sample"]
end = events["I1"]["sample"]
cycle_delta = events["C1"]["sample"] - events["C0"]["sample"]
csr_count = sum(start <= event["retire"] < end for event in events.values())
fence_count = sum(start <= tick < end for tick in d["fence_retirement_ticks"])
body_count = d["body_instruction_count"]
instret_delta = csr_count + fence_count + body_count
assert cycle_delta == d["expected_cycle_delta"] == 71
assert instret_delta == d["expected_instret_delta"] == 12
assert csr_count == 3 and fence_count == 4 and body_count == 5
assert start <= events["I0"]["retire"] < end
assert not (start <= events["I1"]["retire"] < end)
assert all(start <= tick < end for tick in d["body_retirement_ticks"])
assert all(event["rob"] < event["sample"] < event["retire"] for event in events.values())

axis_left = 76.0
axis_right = width_pt - 16.0
axis_span = axis_right - axis_left
sample_y = 143.0
retire_y = 235.0
axis_y = 285.0
text_sizes = []
parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    f'<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="{height_mm:.6f}mm" viewBox="0 0 {width_pt:.6f} {height_pt}">',
    '<title>CSR采样与退休计数的双窗口</title>',
    '<desc>依据既有全核事件记录重绘。横轴为相对START的tick。instret采样点I0=31、I1=170，其退休计数差为12；cycle采样点C0=65、C1=136，差为71。主体5条含1条vdot，退休记录位于101与105，不分配每个记录的指令数。</desc>',
    f'<rect width="{width_pt:.6f}" height="{height_pt}" fill="{style["background"]}"/>',
    f'<g font-family="Noto Sans CJK SC" fill="{style["text"]}">',
]

def x(tick):
    return axis_left + axis_span * tick / d["stop_relative_tick"]

def text(px, py, value, size=12.0, color=None, anchor="middle", weight="normal"):
    assert size >= style["minimum_text_pt"]
    text_sizes.append(size)
    color = color or style["text"]
    parts.append(f'<text x="{px:.3f}" y="{py:.3f}" font-size="{size:.2f}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(str(value))}</text>')

def line(x1, y1, x2, y2, color=None, stroke_width=0.7, dash=None, opacity=1):
    color = color or style["structure"]
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{stroke_width}" opacity="{opacity}"{dash_attr}/>')

def circle(px, py, radius, color, hollow=False):
    fill = style["background"] if hollow else color
    parts.append(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="{radius}" fill="{fill}" stroke="{color}" stroke-width="1.0"/>')

def square(px, py, half_size, color):
    parts.append(f'<rect x="{px-half_size:.3f}" y="{py-half_size:.3f}" width="{2*half_size}" height="{2*half_size}" fill="{color}"/>')

def bracket(begin, finish, y, label, color, endpoint_circles=False):
    a, b = x(begin), x(finish)
    # Orange dashed/closed-open endpoints distinguish instret from the
    # graphite solid/capped cycle interval even without colour perception.
    line(a, y, b, y, color, 1.3, dash="4 2.6" if endpoint_circles else None)
    if endpoint_circles:
        circle(a, y, 2.5, color)
        circle(b, y, 2.5, color, hollow=True)
    else:
        line(a, y-4, a, y+4, color, 1.1)
        line(b, y-4, b, y+4, color, 1.1)
    text((a+b)/2, y-12, label, size=12.8, color=color, weight="bold")
    line(a, y+5, a, sample_y-5, color, 0.6, dash="2.4 2.4", opacity=0.45)
    line(b, y+5, b, sample_y-5, color, 0.6, dash="2.4 2.4", opacity=0.45)

# The report provides the figure number and overall title below the artwork.
bracket(start, end, 54, f"instret 差 = {instret_delta}", style["instret"], endpoint_circles=True)
bracket(events["C0"]["sample"], events["C1"]["sample"], 89,
        f"cycle 差 = {cycle_delta}", style["cycle"])

line(axis_left, sample_y, axis_right, sample_y, stroke_width=0.6, opacity=0.32)
line(axis_left, retire_y, axis_right, retire_y, stroke_width=0.6, opacity=0.32)
text(65, sample_y+4, "CSR采样", size=12.0, anchor="end")
text(65, retire_y+4, "退休", size=12.0, anchor="end")

for event in d["csr_events"]:
    color = style[event["kind"]]
    sx, rx = x(event["sample"]), x(event["retire"])
    line(sx, sample_y+3.4, rx, retire_y-3.2, color, 0.95,
         dash="3.2 2.2" if event["kind"] == "instret" else None)
    circle(sx, sample_y, 3.1, color)
    square(rx, retire_y, 2.9, color)
    text(sx, sample_y-14, event["id"], size=12.8, color=color, weight="bold")
    text(sx-7, sample_y+19, event["sample"], size=11.5, color=color, anchor="end")
    text(rx, retire_y+21, event["retire"], size=11.5, color=color)

for tick in d["fence_retirement_ticks"]:
    line(x(tick), retire_y-6, x(tick), retire_y+6, style["fence"], 1.5)

body_left, body_right = map(x, (min(d["body_retirement_ticks"]), max(d["body_retirement_ticks"])))
parts.append(f'<rect x="{body_left:.3f}" y="{retire_y-5:.3f}" width="{body_right-body_left:.3f}" height="10" fill="{style["subtle"]}" stroke="{style["structure"]}" stroke-width="0.9"/>')
body_mid = (body_left + body_right) / 2
text(body_mid, 196, "5 条主体", size=12.3, color=style["structure"], weight="bold")
text(body_mid, 213, "含 1 条 vdot", size=11.5, color=style["structure"])
line(body_mid, 217, body_mid, retire_y-7, style["structure"], 0.7)
text(body_mid, retire_y+21, "101–105", size=11.0, color=style["structure"])

line(axis_left, axis_y, axis_right, axis_y, stroke_width=0.8)
for tick in (0, 50, 100, 150, d["stop_relative_tick"]):
    line(x(tick), axis_y-3, x(tick), axis_y+3, stroke_width=0.8)
    text(x(tick), axis_y+18, tick, size=11.5)
text(axis_left, axis_y-12, "START", size=11.0)
text(axis_right, axis_y-12, "STOP", size=11.0, anchor="end")
text((axis_left+axis_right)/2, 324, "相对 START 的全核 tick", size=11.5)

line(26, 349, 51, 349, style["cycle"], 1.3)
circle(38.5, 349, 2.5, style["cycle"])
text(60, 353, "cycle", size=11.5, color=style["cycle"], anchor="start")
line(158, 349, 186, 349, style["instret"], 1.3, dash="4 2.6")
circle(172, 349, 2.5, style["instret"])
text(195, 353, "instret", size=11.5, color=style["instret"], anchor="start")
line(312, 343, 312, 355, style["fence"], 1.5)
text(325, 353, "fence 退休", size=11.5, color=style["fence"], anchor="start")
text(width_pt/2, 375,
     f"{instret_delta} = {csr_count} 条 CSR + {fence_count} 条 fence + {body_count} 条主体",
     size=11.5, color=style["instret"])
text(width_pt/2, 395, "计数窗口含 I0 退休，不含 I1 退休", size=11.5)
text(width_pt/2, 416, "依据既有记录重绘的事件示意", size=11.0)
parts.append("</g></svg>")
svg = "\n".join(parts) + "\n"
out_svg = HERE / "S3-04-dual-window.svg"
out_svg.write_text(svg, encoding="utf-8")

out_png = HERE / "S3-04-dual-window.png"
out_pdf = HERE / "S3-04-dual-window.pdf"
inkscape = shutil.which("inkscape")
if inkscape is None:
    raise SystemExit("SVG generated; PNG/PDF rendering needs Inkscape.")
font_records = []
for request in ("Noto Sans CJK SC", "Noto Sans CJK SC:style=Bold"):
    match = subprocess.run(
        ["fc-match", "-f", "%{family}\n%{style}\n%{file}\n", request],
        check=True, text=True, stdout=subprocess.PIPE,
    ).stdout.strip().splitlines()
    if not match or "Noto Sans CJK SC" not in match[0]:
        raise SystemExit(f"Requested Noto family not resolved: {request}: {match}")
    font_records.append({"request": request, "family": match[0],
                         "style": match[1], "file": match[2]})
with tempfile.TemporaryDirectory(prefix=".inkscape-profile-", dir=HERE) as profile:
    environment = dict(os.environ)
    environment["INKSCAPE_PROFILE_DIR"] = profile
    for kind, output in (("png", out_png), ("pdf", out_pdf)):
        subprocess.run([
            inkscape, str(out_svg), f"--export-type={kind}", "--export-dpi=240",
            f"--export-filename={output}",
        ], check=True, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
png_renderer = "Inkscape"
print(json.dumps({
    "svg": str(out_svg), "preview": str(out_png), "pdf": str(out_pdf),
    "width_mm": style["width_mm"],
    "height_mm": round(height_mm, 3), "minimum_text_pt": min(text_sizes),
    "cycle_delta": cycle_delta, "cycle_calculation": f"{events['C1']['sample']} - {events['C0']['sample']} = {cycle_delta}",
    "instret_delta": instret_delta, "count_components": {"csr": csr_count, "fence": fence_count, "body": body_count},
    "body_record_counts_assigned": False,
    "png_renderer": png_renderer,
    "font_resolution": font_records,
    "source_reference_status": "Fixed archived log, window-result and runtime identity independently verified; see data.json source_notes.",
}, ensure_ascii=False, indent=2))
