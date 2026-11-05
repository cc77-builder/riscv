#!/usr/bin/env python3
"""Build S2-01 and S2-10 from pure JSON data; Python standard library only.

Only S2-01.svg, S2-10.svg and manifest.json beside this script are written.
No repository access, network, rasterization or engineering build is performed.
"""
from pathlib import Path
from html import escape
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
IDS = ("S2-01", "S2-10")


class Drawing:
    def __init__(self, data):
        self.data = data
        self.p = data["palette"]
        self.parts = []
        width, height = data["canvas"]["width_mm"], data["canvas"]["height_mm"]
        families = ", ".join('"' + f + '"' if f != "sans-serif" else f
                             for f in data["typography"]["font_stack"])
        self.parts.append('<?xml version="1.0" encoding="UTF-8"?>')
        self.parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">')
        self.parts.append(f'<title id="title">{data["figure_id"]}</title>')
        self.parts.append(f'<desc id="desc">{escape(data["caption"])}</desc>')
        self.parts.append(f'<metadata>Fixed source: {data["fixed_ref"]}; see {data["figure_id"]}.sources.json. Native width 160 mm; minimum text 4.0 mm = 11.33858 pt.</metadata>')
        self.parts.append('<defs>')
        for key, color in (("arrow", self.p["graphite"]), ("accentArrow", self.p["accent"])):
            self.parts.append(f'<marker id="{key}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="2.6" markerHeight="2.6" orient="auto" markerUnits="userSpaceOnUse"><path d="M 1 1 L 9 5 L 1 9 Z" fill="{color}"/></marker>')
        self.parts.append('<style>')
        self.parts.append(f'text {{font-family: {families}; fill: {self.p["graphite"]}; font-weight: 400;}}')
        self.parts.append('.aux {font-size: 4px;} .body {font-size: 4.5px;} .bold {font-weight: 600;} .sigma {font-size: 7.8px;}')
        self.parts.append('</style></defs>')
        self.parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{self.p["background"]}"/>')

    def text(self, x, y, content, cls="aux", anchor="start", accent=False, id=None):
        attrs = f' id="{escape(id)}"' if id else ""
        color = f' fill="{self.p["accent"]}" style="fill:{self.p["accent"]}"' if accent else ""
        self.parts.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{color}{attrs}>{escape(str(content))}</text>')

    def rect(self, x, y, w, h, fill=None, accent=False, dashed=False, id=None):
        fill = self.p["warm_gray"] if fill is None else fill
        color = self.p["accent"] if accent else self.p["graphite"]
        extra = ' stroke-dasharray="1.2 0.8"' if dashed else ""
        extra += f' id="{escape(id)}"' if id else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{color}" stroke-width="{0.42 if accent else 0.30}"{extra}/>')

    def line(self, x1, y1, x2, y2, accent=False, width=0.34):
        color = self.p["accent"] if accent else self.p["graphite"]
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    def arrow(self, d, accent=False):
        color = self.p["accent"] if accent else self.p["graphite"]
        marker = "accentArrow" if accent else "arrow"
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="0.35" stroke-linejoin="round" marker-end="url(#{marker})"/>')

    def slot(self, x, y, name, value, w=18, h=10, crossed=False):
        self.rect(x, y, w, h,
                  fill=self.p["warm_gray"] if value is not None else self.p["background"],
                  dashed=value is None)
        self.text(x+w/2, y+h/2+1.6, f'{name}: {value if value is not None else "空"}',
                  "body", "middle")
        if crossed:
            self.line(x+w-4.0, y+0.85, x+w-0.85, y+4.0, True, 0.44)
            self.line(x+w-4.0, y+4.0, x+w-0.85, y+0.85, True, 0.44)

    def finish(self):
        raw = ("\n".join(self.parts) + "\n</svg>\n").encode("utf-8")
        ET.fromstring(raw)
        return raw


def fields_and_result(data):
    d = Drawing(data)
    d.text(6, 7, "32 位指令", "body bold")
    d.text(154, 7, data["instruction"]["assembly"], "aux", "end")
    x, mm_per_bit = 6.0, 148.0 / data["instruction"]["width"]
    for field in data["fields_msb_first"]:
        width = field["width"] * mm_per_bit
        center = x + width/2
        d.text(center, 15, field["name"], "aux", "middle")
        fill = d.p["warm_gray"] if field["kind"] == "fixed" else d.p["background"]
        d.rect(x, 19, width, 11, fill, accent=field["name"] == "vd",
               id="field-"+field["name"])
        d.text(center, 26.2, field["value"], "body", "middle")
        label = f'[{field["high"]}]' if field["high"] == field["low"] else f'[{field["high"]}:{field["low"]}]'
        d.text(center, 36, label, "aux", "middle")
        x += width

    d.text(6, 46, "两源 [127:64] 不参与；每格为 signed int8")
    for src, label_y, y in zip(data["inputs"], (54, 75), (58, 79)):
        d.text(6, label_y, f'{src["register"]}[{src["active_high"]}:{src["active_low"]}]', "body")
        for index, lane in enumerate(src["lanes_left_to_right"]):
            cell_x = 6 + index * 10
            d.rect(cell_x, y, 10, 11)
            d.text(cell_x+5, y+7.15, f'{src["prefix"]}{lane}', "body", "middle")

    d.arrow("M 86 63.5 H 95 L 105.4 70.7")
    d.arrow("M 86 84.5 H 95 L 105.4 77.3")
    d.parts.append(f'<circle cx="111" cy="74" r="6.5" fill="{d.p["background"]}" stroke="{d.p["accent"]}" stroke-width="0.42"/>')
    d.text(111, 76.65, "Σ", "sigma", "middle", True)
    d.arrow("M 117.5 74 H 148 V 118")
    d.text(111, 94, "S = Σ a[i]b[i]", "aux", "middle")
    d.text(111, 100, "i = 0…7", "aux", "middle")
    d.text(6, 100, "8 对乘积精确求和")
    d.text(6, 108, "完整 128 位写回 · vd", "body bold")

    high, low = data["result"]["fields_msb_first"]
    high_width = 148 * high["width"] / data["result"]["total_bits"]
    low_width = 148 - high_width
    d.text(6+high_width/2, 115, f'[{high["high"]}:{high["low"]}]', "aux", "middle")
    d.text(6+high_width+low_width/2, 115, f'[{low["high"]}:{low["low"]}]', "aux", "middle")
    d.rect(6, 118, high_width, 12, id="result-high96")
    d.rect(6+high_width, 118, low_width, 12, accent=True, id="result-low32")
    d.text(6+high_width/2, 125.8, "高 96 位清零", "body", "middle")
    d.text(6+high_width+low_width/2, 125.8, "32 位补码", "body", "middle")
    return d.finish()


def states_and_cancel(data):
    d = Drawing(data)
    normal = data["same_edge"]
    d.text(6, 7, "同拍推进", "body bold")
    d.text(154, 7, "reset=0，flush.valid=0，out.ready=1", "aux", "end")
    d.text(6, 14, "输入 C 有效且父级准入")
    d.text(53, 21, "P 乘积槽", "aux", "middle")
    d.text(101, 21, "R 结果槽", "aux", "middle")
    d.text(6, 32.2, "沿前", "body")
    d.text(6, 62.2, "沿后", "body")
    for slot, x in (("P", 38), ("R", 86)):
        d.slot(x, 25, slot, normal["before"][slot], 30, 11)
        d.slot(x, 55, slot, normal["after"][slot], 30, 11)
    d.text(6, 46, "输入 "+normal["input"], "body")
    d.arrow("M 22 46 L 53 55")
    d.arrow("M 53 36 L 101 55", True)
    d.text(77, 40, "迁移 "+normal["move"], "aux", "middle", True)
    d.arrow("M 101 36 L 143 55")
    d.text(143, 63, "输出 "+normal["output"], "body", "middle")
    d.text(6, 74, "移动读取沿前 P；数据与身份同步。")

    d.text(6, 84, "同一事务：reset ＞ 匹配取消 ＞ 响应", "body bold")
    d.text(6, 92, "flush.valid=1，out.ready=0；后三行 reset=0")
    d.text(6, 100, "情形")
    d.text(61, 100, "沿前", "aux", "middle")
    d.text(125, 100, "沿后", "aux", "middle")
    for row, y in zip(data["cancellation_table"]["rows"], (104, 118, 132, 146)):
        d.text(6, y+6.6, row["label"], accent=row["id"] == "reset")
        for name, x in (("P", 43), ("R", 61)):
            d.slot(x, y, name, row["before"][name],
                   crossed=name in row["crossed_slots"])
        for name, x in (("P", 107), ("R", 125)):
            d.slot(x, y, name, row["after"][name])
        d.arrow(f'M 84 {y+5} H 103', accent=row["id"] == "killR")
        if row["id"] == "killR":
            d.text(93.5, y+1, "移 B", "aux", "middle", True)
    d.text(6, 163, "flush 禁止新入；幸存 R 仍可按 ready 响应。")
    return d.finish()


def main():
    renderers = {"S2-01": fields_and_result, "S2-10": states_and_cancel}
    output_manifest = {"schema": "riscv-figure-output-manifest-v1", "direction": "B",
                       "minimum_font_pt_at_native_width": 4 * 72 / 25.4,
                       "rendered_pdf_png": False, "outputs": []}
    for figure_id in IDS:
        source = ROOT / f"{figure_id}.sources.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        if data["figure_id"] != figure_id or data["canvas"]["width_mm"] != 160:
            raise ValueError("Unexpected figure identity or width")
        raw = renderers[figure_id](data)
        name = figure_id + ".svg"
        (ROOT / name).write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        output_manifest["outputs"].append({
            "file": name, "sha256": sha, "bytes": len(raw),
            "canvas": data["canvas"], "data_file": source.name,
            "data_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "fixed_ref": data["fixed_ref"]
        })
        print(f"{name} sha256={sha}")
    (ROOT / "manifest.json").write_text(json.dumps(output_manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()

