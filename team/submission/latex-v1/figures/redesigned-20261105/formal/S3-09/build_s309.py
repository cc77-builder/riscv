#!/usr/bin/env python3
"""Render S3-09 from existing report evidence; no engineering tests are run.

Usage: python build_s309.py [--source-root /path/to/latex-v1]
Without --source-root, finds the report root among this script's ancestors.
Requires Python 3, PyMuPDF, Inkscape, pdffonts and Noto Sans CJK SC.
Writes only alongside this script. SVG keeps editable text; PDF outlines it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

import fitz

HERE = Path(__file__).resolve().parent
STEM = "S3-09-evidence-coverage"
W, H = 160.0, 145.0
MM_PER_PT = 25.4 / 72
C = dict(navy="#24384A", teal="#287F84", gray="#637487", line="#CED9E2", pale="#F5F8FA")
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_source_root(requested=None):
    candidates = [requested.expanduser().resolve()] if requested is not None else [HERE, *HERE.parents]
    for candidate in candidates:
        if (candidate / "figures/placement.json").is_file() and (candidate / "content").is_dir():
            return candidate
    raise FileNotFoundError("Report root must contain figures/placement.json and content; use --source-root if it is not an ancestor of this script.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, help="Report root; by default search this script's ancestors")
    args = ap.parse_args()
    try:
        src = resolve_source_root(args.source_root)
    except FileNotFoundError as exc:
        ap.error(str(exc))
    names = ["sections/stage3.tex", "content/overview-stage2.tex", "content/overview-stage3.tex",
             "figures/placement.json", "figures/evidence-20261105/figure-data.json",
             "figures/redesigned-20261105/S3-09-provenance.json"]
    sources = {n: src / n for n in names}
    text3 = sources["sections/stage3.tex"].read_text(encoding="utf-8")
    data = json.loads(sources["figures/evidence-20261105/figure-data.json"].read_text(encoding="utf-8"))
    placement = json.loads(sources["figures/placement.json"].read_text(encoding="utf-8"))
    s309 = next(x for x in placement if x["id"] == "S3-09")
    # These are documentary consistency checks, not a transfer of historical PASS.
    for required in ("13项", "1项新", "80.119", "62.888356", "Fmax", "布线后时序", "功耗"):
        assert required in text3, required
    assert "墙钟稳定性未证实" in s309["content"]
    assert "FAIL" in s309["content"]
    nominal = [x for x in data["timing"] if x["profile"] == "nominal"]
    negative = sum(float(x["after_slack_ns"]) < 0 for x in nominal)
    assert len(nominal) == 14 and negative == 10
    assert round(data["area"]["fu"]["after"]["area"], 3) == 17298.246
    assert round(data["area"]["parent"]["after"]["area"], 3) == 284614.946

    svg = ET.Element(f"{{{NS}}}svg", width=f"{W:g}mm", height=f"{H:g}mm",
                     viewBox=f"0 0 {W:g} {H:g}", role="img", version="1.1",
                     attrib={"aria-labelledby": "title desc"})

    def add(tag, **attrs):
        return ET.SubElement(svg, f"{{{NS}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()})

    add("title", id="title").text = "S3-09 固定工程组合的证据覆盖与边界"
    add("desc", id="desc").text = (
        "Rows show VDot FU, full VFEX4 parent, whole-core programs, and fixed GEMV/C8 calls. "
        "Columns show functionality, cycle observations, standard-cell area, pre-layout STA, and power. "
        "A solid circle means an existing record, including a non-converged result; it does not mean PASS. "
        "An open circle means explicitly unmeasured. A dash means that this software-evidence row "
        "does not evaluate that physical metric. All evidence is scoped to the frozen 0f plus "
        "firstdot V2 plus original C8 combination. Historical UTC capacity FAIL and unproven "
        "wall-clock stability remain recorded. There are 10 negative slack categories among 14 "
        "reported nominal 1ns/5fF paths. Whole-core Fmax, post-route timing, and power are unmeasured."
    )
    add("rect", x=0, y=0, width=W, height=H, fill="white")
    text_items = []

    def label(x, y, value, pt=11.5, color=None, anchor="start", weight=400, ident=None):
        assert pt >= 11.5
        ident = ident or f"text-{len(text_items):02d}"
        node = add("text", id=ident, x=x, y=y, text_anchor=anchor,
                   font_family="Noto Sans CJK SC", font_size=f"{pt * MM_PER_PT:.6f}",
                   font_weight=weight, fill=color or C["navy"])
        node.text = value
        text_items.append(dict(id=ident, text=value, pt=pt, x_mm=x, baseline_mm=y))

    def line(x1, y1, x2, y2, color=None, sw=.23):
        return add("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=color or C["line"], stroke_width=sw)

    def mark(x, y, status, ident):
        if status == "record":
            add("circle", id=ident, cx=x, cy=y, r=1.65, fill=C["teal"])
        elif status == "unmeasured":
            add("circle", id=ident, cx=x, cy=y, r=1.65, fill="white", stroke=C["gray"], stroke_width=.38)
        elif status == "outside_row_scope":
            add("path", id=ident, d=f"M {x-1.65} {y} H {x+1.65}", stroke=C["gray"],
                stroke_width=.38, fill="none")
        else:
            raise ValueError(status)

    # Version identity is a scope label, not a repeated figure title.
    label(3, 7, "固定组合  0f + firstdot V2 + 原 C8", pt=12.2, weight=500)
    mark(4.8, 14.5, "record", "legend-record")
    label(8.2, 16.0, "有记录（含未达标）")
    mark(58.5, 14.5, "unmeasured", "legend-unmeasured")
    label(62, 16, "未测")
    mark(91, 14.5, "outside_row_scope", "legend-outside")
    label(95, 16, "本行不评价")

    x0, left, right = 3.0, 47.0, 157.0
    colw = (right-left)/5
    centers = [left + (i+.5)*colw for i in range(5)]
    line(x0, 20.5, right, 20.5, sw=.35)
    label((left+91)/2, 26, "逻辑与执行", anchor="middle", color=C["teal"])
    label((91+right)/2, 26, "物理实现", anchor="middle", color=C["gray"])
    line(left, 28, 90, 28, color=C["teal"], sw=.35)
    line(92, 28, right, 28, sw=.35)
    headers = [("功能", "正确性"), ("周期", "观察"), ("单元", "面积"), ("布局前", "STA"), ("功耗", "")]
    for x, (a,b) in zip(centers, headers):
        label(x, 33.4 if b else 36.0, a, anchor="middle")
        if b:
            label(x, 38.3, b, anchor="middle")
    label(x0, 36, "证据层级", color=C["gray"])

    top, rh = 42.0, 16.0
    rows = [
        {"key":"fu", "label":"局部 VDot FU", "sub":"算术与握手", "status":["record"]*4+["unmeasured"]},
        {"key":"parent", "label":"VFEX4 父级", "sub":"含 FU 与 DIV", "status":["record"]*4+["unmeasured"]},
        {"key":"wholecore", "label":"整核程序", "sub":"差分／微基准", "status":["record","record"]+["unmeasured"]*3},
        {"key":"software", "label":"固定 GEMV / C8", "sub":"原完整调用", "status":["record","record"]+["outside_row_scope"]*3},
    ]
    add("rect", x=91, y=top, width=66, height=3*rh, fill=C["pale"])
    line(x0, top, right, top, sw=.35)
    for i, row in enumerate(rows):
        y = top+i*rh
        label(x0, y+6.0, row["label"], pt=11.8, weight=500)
        label(x0, y+11.5, row["sub"], color=C["gray"])
        for j, status in enumerate(row["status"]):
            mark(centers[j], y+8, status, f"cell-{row['key']}-{j}")
        line(x0, y+rh, right, y+rh, sw=.35 if i in (1,3) else .2)
    line(91, top, 91, top+4*rh, sw=.35)

    # Compact scope annotations keep the matrix itself graphical, and preserve
    # failure/unknown outcomes without encoding unmeasured cells as failed tests.
    notes = [
        ("周期口径", "局部握手拍；整核与 C8 为 DUT 周期"),
        ("记录沿用", "全核组合：13 项既有 + 1 项新诊断；C8 接入为静态等价"),
        ("时序边界", f"1 ns／5 fF：{len(nominal)} 类中 {negative} 类负裕量"),
        ("未测项目", "整核 Fmax、布线后时序、功耗"),
        ("宿主审计", "旧 UTC 容量 FAIL；墙钟稳定性未证实"),
    ]
    for i, (head, body) in enumerate(notes):
        y=113.0+6.5*i
        label(3, y, head, color=C["gray"])
        label(23, y, body, weight=500 if i in (2,4) else 400)

    svg_path = HERE / f"{STEM}.svg"
    ET.indent(svg, space="  ")
    svg_path.write_bytes(ET.tostring(svg, encoding="utf-8", xml_declaration=True))
    pdf_path = HERE / f"{STEM}.pdf"
    subprocess.run(["inkscape", str(svg_path), "--export-area-page", "--export-text-to-path", "--export-type=pdf",
                    f"--export-filename={pdf_path}"], check=True, capture_output=True)
    # Preview comes from the saved PDF, not a separate SVG/bitmap rendering path.
    doc=fitz.open(pdf_path)
    page=doc[0]
    page.get_pixmap(dpi=240, alpha=False).save(HERE / f"{STEM}.png")
    fonts=page.get_fonts(full=True)
    font_check=subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True, check=True).stdout
    query=subprocess.run(["inkscape",str(svg_path),"--query-all"],capture_output=True,text=True,check=True).stdout
    boxes={}
    for q in query.splitlines():
        parts=q.split(',')
        if len(parts)==5: boxes[parts[0]]=[float(v) for v in parts[1:]]
    out_of_page=[]
    for t in text_items:
        x,y,w,h=boxes[t['id']]
        if x<0 or y<0 or x+w>W*96/25.4+.1 or y+h>H*96/25.4+.1:
            out_of_page.append({'text':t['text'],'bbox_px':[x,y,w,h]})
    source_records=[dict(path=str(path), relative=n, sha256=sha(path)) for n,path in sources.items()]
    report={
        "schema":"s309-evidence-matrix-review-v1", "figure_id":"S3-09", "created_utc":datetime.now(timezone.utc).isoformat(),
        "scope":"Read and redraw existing report evidence only; no new simulation, benchmark, synthesis, or source-code change.",
        "human_aesthetic_approval":False, "status":"candidate-awaiting-independent-and-visual-review",
        "figure_size_mm":[W,H], "minimum_svg_text_pt":min(t["pt"] for t in text_items),
        "font":{"requested":"Noto Sans CJK SC", "pdf_font_report":font_check, "pdf_font_rows":fonts,
                "outlined":True, "minimum_pdf_span_pt":None,
                "size_validation":"Editable SVG font-size at native 160mm width; actual PDF-derived preview visually checked separately"},
        "pdf_renderer":"Inkscape --export-text-to-path; SVG text editable, PDF glyphs vector outlines without erroneous ToUnicode mappings",
        "preview":{"method":"PyMuPDF rendering of saved PDF", "dpi":240},
        "automatic_checks":{"source_assertions_passed":True,
                            "pdf_contains_no_text_objects":not page.get_text().strip(),
                            "svg_text_outside_native_page":out_of_page,
                            "pdf_size_mm":[page.rect.width*25.4/72,page.rect.height*25.4/72]},
        "legend":{"record":"existing evidence, including non-converged measurement; never means unconditional PASS",
                  "unmeasured":"explicitly unmeasured physical metric in this report",
                  "outside_row_scope":"this software-evidence row does not evaluate physical metrics; no claim that a measurement is impossible"},
        "matrix":{"columns":["functionality","cycle_observations","standard_cell_area","pre_layout_STA","power"],"rows":rows},
        "evidence_mapping":{
            "fu_parent_function":"sections/stage3.tex: 功能、复现与性能检查汇总 / 功能单元与父级; overview-stage2.tex: 基础验证层级",
            "fu_parent_cycles":"overview-stage2.tex: 两槽在持续ready下最早2拍响应、连续接收间隔1拍; placement S2-05: 原父级逐拍握手记录",
            "wholecore_function":"sections/stage3.tex: 整核协同仿真、宿主运行记录与并发审计; 13 reused + 1 new control diagnostic",
            "wholecore_cycles":"sections/stage3.tex: 点积微基准 / 原周期记录复用; this is guest-DUT cycles, not host seconds",
            "software_function_cycles":"sections/stage3.tex: 通用GEMV入口, 8×32专用入口, 接入结果与功能记录复用; SDK link audit runs EMU/NEMU 0 times",
            "area_STA":"figure-data.json area.after and nominal timing.after_slack_ns; stage3 physical assessment",
            "physical_unmeasured":"overview-stage3.tex: 父级面积包含FU及DIV...整核Fmax、功耗和布线后时序为待测; placement S3-07 scope includes no whole-core PPA",
            "capacity_wallclock":"sections/stage3.tex: 宿主运行记录与并发审计; UTC apparent overlap 80.119ms; new UTC minus monotonic -62.888356s; historical FAIL retained"
        },
        "numerical_crosscheck":{"nominal_categories":len(nominal),"nominal_negative":negative,
                                "fu_area_um2":data["area"]["fu"]["after"]["area"],
                                "parent_area_um2":round(data["area"]["parent"]["after"]["area"],3)},
        "unknown_cells":[],
        "preserved_export_failures":[
            {"file":"first-inkscape-ToUnicode-error.pdf","reason":"Actual glyphs rendered correctly, but extraction mapped some digits and CJK characters incorrectly. Not selected."},
            {"file":"first-pymupdf-CFF-glyph-error.pdf","reason":"Text extraction passed but actual PDF rendering showed wrong/missing glyphs from the CFF subset. Not selected."}],
        "limits":["Only frozen 0f + firstdot V2 + original C8 evidence is summarized; no historical PASS is transferred to a new candidate.",
                  "The matrix reports coverage, not numerical scale or relative magnitude.",
                  "Functionality circles refer to the report's specified test coverage, not exhaustive correctness. In the parent, DIV is dynamically covered while SQRT has a static cancellation-path check only.",
                  "The two cycle notions are differentiated; no local-cycle-to-application-speedup inference is made.",
                  "Software row physical cells deliberately remain outside this figure's evaluation scope.",
                  "Capacity FAIL concerns the historical host UTC concurrency audit; it is not a vdot arithmetic failure.",
                  "Noto Sans CJK SC supplies the actual glyphs, not Microsoft YaHei. The editable SVG retains text; the selected PDF uses vector outlines and cannot be text-searched. This candidate has not received human aesthetic approval."],
        "sources":source_records,
        "visual_references":[
            {"historical_asset":"pro1-structural-svg-v1/S3-01-structural.png","build_input":False},
            {"historical_asset":"pro2-c8-layout-v1/S3-06-c8-layout.png","build_input":False}],
        "outputs":{p.name:{"sha256":sha(p),"bytes":p.stat().st_size} for p in [svg_path,pdf_path,HERE/f"{STEM}.png",Path(__file__).resolve()]},
        "text_inventory":text_items,
        "visual_review":{"actual_saved_pdf_preview_viewed":False,"overlap_or_clipping":None}
    }
    (HERE/"source-and-review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    assert not out_of_page, out_of_page
    assert not fonts and not page.get_text().strip()
    print(json.dumps({"pdf":str(pdf_path),"size_mm":[W,H],"min_svg_pt":report["minimum_svg_text_pt"],
                      "nominal_negative":negative,"fonts":font_check},ensure_ascii=False))


if __name__=="__main__":
    main()
