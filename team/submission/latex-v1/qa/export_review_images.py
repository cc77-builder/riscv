#!/usr/bin/env python3
"""Export the 31 report figures and shared cover for local review/editing.

Requires PyMuPDF. Reads generated sections/stageN.tex in display order and
the matching QA page-map.json. Output must not exist. Source files are read
only. All PNGs are rendered directly from the exported final PDFs at 220 dpi.

Example (run with Python's -X utf8 option on Windows):
  python -X utf8 export-review-images.py --source-root REPORT_ROOT \
    --page-map QA_DIR/page-map.json --output-dir NEW_REVIEW_DIRECTORY
"""

from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote
import argparse
import csv
import hashlib
import html
import json
import re
import shutil

import fitz

DPI = 220
SCHEMA = "xiangshan-report-image-export-v1"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def argument(text, offset):
    """Read a balanced TeX argument, including nested and escaped braces."""
    while offset < len(text) and text[offset].isspace():
        offset += 1
    if offset == len(text) or text[offset] != "{":
        raise ValueError("Malformed figure macro: expected a braced argument")
    start, depth, offset = offset + 1, 1, offset + 1
    while offset < len(text):
        char = text[offset]
        if char == "\\":
            offset += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if not depth:
                return text[start:offset], offset + 1
        offset += 1
    raise ValueError("Unclosed argument in a figure macro")


def title_text(text):
    text = re.sub(r"\\([_&#%${}])", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?", "", text)
    return re.sub(r"\s+", " ", text.replace("{", "").replace("}", "").replace("~", " ")).strip()


def read_figures(source_root):
    entries, section_hashes = [], {}
    pattern = re.compile(r"(?m)^\s*\\(reportfigure|evidencefigure)\s*")
    for stage in (1, 2, 3):
        path = source_root / "sections" / f"stage{stage}.tex"
        text = path.read_text(encoding="utf-8-sig")
        section_hashes[str(path.relative_to(source_root))] = sha256(path)
        for index, match in enumerate(pattern.finditer(text), 1):
            args, offset = [], match.end()
            for _ in range(5 if match[1] == "reportfigure" else 4):
                value, offset = argument(text, offset)
                args.append(value)
            fid = args[0].strip()
            if not re.fullmatch(r"[A-Za-z0-9-]+", fid):
                raise ValueError(f"Invalid figure ID: {fid}")
            entries.append({"order": len(entries) + 1, "stage": stage,
                            "kind": match[1], "number": f"{stage}-{index}",
                            "id": fid, "title": title_text(args[1]), "title_tex": args[1]})
    if len(entries) != 31 or len({item["id"] for item in entries}) != 31:
        raise ValueError("Expected exactly 31 unique figure macros in generated stage1/2/3.tex")
    return entries, section_hashes


def page_number(page_map, document, item):
    record = page_map[document]["figures"][item["id"]]
    pages = record.get("pdf_pages", [])
    if record.get("number") != item["number"] or record.get("present") is not True:
        raise ValueError(f"Page-map/source mismatch: {document}, {item['id']}")
    if len(pages) != 1 or not isinstance(pages[0], int) or not 1 <= pages[0] <= page_map[document]["pages"]:
        raise ValueError(f"Expected one physical PDF page for {document}, {item['id']}: {pages}")
    return pages[0]


def write_indexes(output_dir, rows, manifest):
    columns = ["order", "number", "id", "title", "stage", "kind", "main_pdf_page",
               "booklet_pdf_page", "source_path", "source_sha256", "pdf_file",
               "pdf_sha256", "png_file", "png_sha256", "png_dpi"]
    with (output_dir / "images.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "export-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = ["# 香山报告图片总览", "",
          "31张正文图按实际出现顺序排列，另附共用封面。PDF保留源字节，正文PNG由同一PDF以220 dpi渲染。",
          "页码为从封面开始计数的PDF物理页；分册页对应本图所属阶段。原报告文件保持不变。", "",
          "| 图号 | 稳定ID | 标题 | 合订本页 | 分册页 | 文件 |",
          "| --- | --- | --- | ---: | --- | --- |"]
    cards = []
    for row in rows:
        links = []
        for key, label in (("pdf_file", "PDF"), ("png_file", "PNG")):
            if row.get(key):
                links.append(f"[{label}]({quote(row[key])})")
        safe_title = row["title"].replace("|", "\\|")
        md.append(f"| {row['number'] or '封面'} | {row['id']} | {safe_title} | "
                  f"{row['main_pdf_page']} | {row['booklet_pdf_page']} | {' · '.join(links)} |")
        h = html.escape
        html_links = " · ".join(f'<a href="{quote(row[key])}">{label}</a>'
                                for key, label in (("pdf_file", "PDF"), ("png_file", "PNG")) if row.get(key))
        hashes = f"源文件 SHA-256: {row['source_sha256']}\n"
        if row.get("pdf_file"):
            hashes += f"导出 PDF SHA-256: {row['pdf_sha256']}\n"
        hashes += f"导出 PNG SHA-256: {row['png_sha256']}"
        cards.append(f'<article><a href="{quote(row["png_file"])}"><img loading="lazy" '
                     f'src="{quote(row["png_file"])}" alt="{h(row["title"])}"></a>'
                     f'<h2>{h(row["number"] or "封面")} · {h(row["title"])}</h2>'
                     f'<p>{h(row["id"])}｜合订本第 {row["main_pdf_page"]} 页｜'
                     f'分册 {h(str(row["booklet_pdf_page"]))} 页</p><p>{html_links}</p>'
                     f'<details><summary>来源与文件摘要</summary><p>{h(row["source_path"])}</p>'
                     f'<pre>{h(hashes)}</pre></details></article>')
    md += ["", "## 文件摘要", "", f"页码索引 SHA-256：`{manifest['page_map_sha256']}`", ""]
    for row in rows:
        md += [f"### {row['number'] or '封面'} · {row['id']}", "",
               f"- 源文件：`{row['source_path']}`", f"- 源 SHA-256：`{row['source_sha256']}`"]
        if row.get("pdf_file"):
            md.append(f"- 导出 PDF SHA-256：`{row['pdf_sha256']}`")
        md += [f"- 导出 PNG SHA-256：`{row['png_sha256']}`", ""]
    (output_dir / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>香山报告图片总览</title>
<style>body{margin:0;padding:24px;background:#F6F3EE;color:#242424;font-family:"Microsoft YaHei",sans-serif}
main{max-width:1500px;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}
article{padding:16px;background:white;border:1px solid #DAD4CB;border-radius:8px}img{display:block;width:100%;height:320px;object-fit:contain}
h1{font-size:26px}h2{font-size:18px;line-height:1.5}p{line-height:1.6}a{color:#CE4B32}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px}details p{overflow-wrap:anywhere;font-size:12px}
@media(max-width:450px){body{padding:12px}.grid{grid-template-columns:1fr}}</style><main>
<h1>香山报告图片总览</h1><p>31张正文图与共用封面。PNG来自相同PDF的220 dpi渲染，PDF保留源字节。
页码为PDF物理页；点击图片查看全尺寸。<a href="images.csv">CSV清单</a> · <a href="README.md">Markdown清单</a></p>
<div class="grid">''' + "\n".join(cards) + "</div></main></html>"
    (output_dir / "index.html").write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--page-map", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preview-dir", type=Path, help="Optional compatibility argument; PNGs are always freshly rendered from the final PDFs.")
    args = parser.parse_args()
    root = args.source_root.resolve()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise FileExistsError(f"Output directory must not exist: {args.output_dir}")
    output = args.output_dir.resolve()
    page_map = json.loads(args.page_map.read_text(encoding="utf-8-sig"))
    figures, section_hashes = read_figures(root)
    if set(page_map.get("main", {}).get("figures", {})) != {item["id"] for item in figures}:
        raise ValueError("Use the latest 31-figure QA page-map.json matching these generated sections")
    for item in figures:
        item["main_pdf_page"] = page_number(page_map, "main", item)
        item["booklet_pdf_page"] = page_number(page_map, f"stage{item['stage']}", item)
        source = root / "figures" / f"{item['id']}.pdf"
        if not source.is_file():
            raise FileNotFoundError(f"The required preferred PDF asset is missing: {source}")
        with fitz.open(source) as doc:
            if len(doc) != 1:
                raise ValueError(f"Expected a single-page figure PDF: {source}")
        item.update(source_path=str(source), source_sha256=sha256(source))
        title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", item["title"]).strip(" .")[:64]
        stem = f"{item['order']:02d}_图{item['number']}_{item['id']}_{title}"
        item.update(pdf_file=stem + ".pdf", png_file=stem + ".png", png_dpi=DPI)
    cover_source = root / "figures" / "cover-concept.png"
    cover_hash = sha256(cover_source)
    output.mkdir(parents=True, exist_ok=False)
    for item in figures:
        pdf, png = output / item["pdf_file"], output / item["png_file"]
        shutil.copy2(item["source_path"], pdf)
        item["pdf_sha256"] = sha256(pdf)
        if item["pdf_sha256"] != item["source_sha256"]:
            raise RuntimeError(f"Source changed during export: {item['id']}")
        with fitz.open(pdf) as doc:
            doc[0].get_pixmap(dpi=DPI, colorspace=fitz.csRGB, alpha=False).save(png)
        item["png_sha256"] = sha256(png)
        print(f"{item['order']:02d}/31  {item['number']}  {item['id']}", flush=True)
    shutil.copy2(cover_source, output / "cover-concept.png")
    if sha256(output / "cover-concept.png") != cover_hash:
        raise RuntimeError("Cover changed during export")
    cover = {"order": 0, "number": "", "id": "cover-concept", "title": "共用封面概念图",
             "stage": "all", "kind": "cover", "main_pdf_page": 1,
             "booklet_pdf_page": "stage1:1; stage2:1; stage3:1", "source_path": str(cover_source),
             "source_sha256": cover_hash, "pdf_file": "", "pdf_sha256": "",
             "png_file": "cover-concept.png", "png_sha256": cover_hash,
             "png_dpi": "原图"}
    rows = [cover] + figures
    manifest = {"schema": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_root": str(root), "page_map_path": str(args.page_map.resolve()),
                "page_map_sha256": sha256(args.page_map), "section_sha256": section_hashes,
                "render_dpi": DPI, "figure_count": 31, "images": rows}
    write_indexes(output, rows, manifest)
    print(f"Exported 31 PDFs, 31 rendered PNGs and the shared cover: {output}", flush=True)


if __name__ == "__main__":
    main()
