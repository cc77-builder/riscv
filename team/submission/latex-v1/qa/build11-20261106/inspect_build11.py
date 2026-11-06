#!/usr/bin/env python3
"""Inspect existing report PDFs; never invoke LaTeX or modify report sources.

Requires PyMuPDF and Pillow. Figures are discovered from the current TeX input
chain, including stage counter resets and direct captionof/label pairs. Findings
are review aids, not RTL/engineering acceptance gates. Contact sheets and detail
pages still need human visual inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


BASE = Path(__file__).resolve().parents[1]
NAMES = {
    "main": "三阶段技术文档_合订本.pdf",
    "stage1": "第一阶段_执行日志与过程文档.pdf",
    "stage2": "第二阶段_设计与基础测试文档.pdf",
    "stage3": "第三阶段_协同仿真与性能分析.pdf",
}
COMMAND = re.compile(r"\\([A-Za-z@]+|.)")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def masked_tex(text):
    """Hide verbatim material and comments, preserving offsets and line numbers."""
    blank = lambda match: re.sub(r"[^\n]", " ", match.group(0))
    text = re.sub(r"\\begin\{(Verbatim|verbatim|lstlisting)\}.*?"
                  r"\\end\{\1\}", blank, text, flags=re.S)
    text = re.sub(r"\\Verb\*?(?:\[[^\]]*\])?([^A-Za-z\s]).*?\1", blank, text)
    lines = []
    for line in text.splitlines(keepends=True):
        for index, char in enumerate(line):
            if char != "%":
                continue
            backslashes, cursor = 0, index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                line = line[:index] + re.sub(r"[^\n]", " ", line[index:])
                break
        lines.append(line)
    return "".join(lines)


def group(text, pos, opening="{", closing="}"):
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos >= len(text) or text[pos] != opening:
        raise ValueError("Expected " + opening + " near " + repr(text[pos:pos + 70]))
    start, depth, cursor = pos + 1, 1, pos + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\":
            cursor += 2
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if not depth:
                return text[start:cursor], cursor + 1
        cursor += 1
    raise ValueError("Unclosed group near " + repr(text[pos:pos + 70]))


def arguments(text, pos, count):
    values = []
    for _ in range(count):
        value, pos = group(text, pos)
        values.append(value)
    return values, pos


def plain_tex(text):
    text = re.sub(r"\\([%&#_{}])", r"\1", text)
    text = re.sub(r"\\(?:texttt|textbf|textit|textrm|seqsplit|emph)\b", "", text)
    text = text.replace(r"\times", "×").replace(r"\textbackslash", "\\")
    text = re.sub(r"\\[,;! ]", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?", "", text)
    text = re.sub(r"\\[()[\]]", "", text)
    return re.sub(r"[{}$]", "", text).strip()


def compact(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    return re.sub(r"\s+", "", text)


def discover_source(source, document):
    """Small parser for this report's real macros, not a general TeX engine."""
    concepts = {}
    concept_file = source / "report-concepts.tex"
    concept_text = masked_tex(concept_file.read_text(encoding="utf-8"))
    for match in re.finditer(r"\\DeclareReportConcept\s*\{", concept_text):
        values, _ = arguments(concept_text, match.end() - 1, 3)
        concepts[values[0]] = values[1]
    state = {"prefix": "1", "counter": 0}
    figures, files, notes = [], {}, []

    def walk(path, stack=(), entry=False):
        path = path.resolve()
        relative = path.relative_to(source).as_posix()
        if path in stack:
            raise ValueError("Recursive TeX input: " + relative)
        raw = path.read_text(encoding="utf-8")
        files[relative] = sha256(path)
        text = masked_tex(raw)
        pos = 0
        if entry:
            begin = re.search(r"\\begin\s*\{document\}", text)
            if not begin:
                raise ValueError("No document body in " + relative)
            pos = begin.end()  # Preamble macro definitions are not figure calls.
        pending_images = []
        while match := COMMAND.search(text, pos):
            command, pos = match.group(1), match.end()
            location = {"source": relative, "line": text.count("\n", 0, match.start()) + 1}
            if command == "input":
                values, pos = arguments(text, pos, 1)
                child = source / values[0]
                if not child.suffix:
                    child = child.with_suffix(".tex")
                walk(child, stack + (path,))
            elif command in ("renewcommand", "setcounter"):
                if pos < len(text) and text[pos] == "*":
                    pos += 1
                values, pos = arguments(text, pos, 2)
                if command == "renewcommand" and values[0] == r"\stagefigureprefix":
                    state["prefix"] = values[1]
                elif command == "setcounter" and values[0] == "figure":
                    state["counter"] = int(values[1])
            elif command == "includegraphics":
                while pos < len(text) and text[pos].isspace():
                    pos += 1
                if pos < len(text) and text[pos] == "[":
                    _, pos = group(text, pos, "[", "]")
                values, pos = arguments(text, pos, 1)
                pending_images.append(values[0])
            elif command in ("reportfigure", "evidencefigure", "captionof"):
                count = {"reportfigure": 5, "evidencefigure": 4, "captionof": 2}[command]
                values, pos = arguments(text, pos, count)
                if command == "captionof" and values[0] != "figure":
                    continue
                state["counter"] += 1
                number = state["prefix"] + "-" + str(state["counter"])
                images = []
                if command == "captionof":
                    label = re.match(r"\s*\\label\{([^}]+)\}", text[pos:])
                    fid = label.group(1).removeprefix("fig:") if label else "unlabeled-" + number
                    title, images = values[1], list(pending_images)
                    if not label:
                        notes.append({**location, "message": "Direct figure caption has no following label."})
                else:
                    fid, title = values[:2]
                    choices = ([f"figures/updated-20261106/{fid}.pdf",
                                f"figures/{fid}.pdf", f"figures/{fid}.png", f"figures/{fid}.jpg"]
                               if command == "reportfigure" else [f"figures/{fid}.pdf"])
                    selected = next((name for name in choices if (source / name).is_file()), None)
                    if selected:
                        images = [selected]
                    else:
                        notes.append({**location, "message": "No image found for " + fid, "candidates": choices})
                figures.append({**location, "id": fid, "stage": state["prefix"],
                                "number": number, "title_tex": title, "title": plain_tex(title),
                                "macro": command, "source_images": images,
                                "concept_image": concepts.get(fid)})
                pending_images.clear()

    walk(source / (document + ".tex"), entry=True)
    for name in ("preamble.tex", "report-concepts.tex"):
        files[name] = sha256(source / name)
    seen = set()
    for figure in figures:
        if figure["id"] in seen:
            notes.append({"message": "Duplicate source figure ID: " + figure["id"]})
        seen.add(figure["id"])
    return {"files_sha256": files, "figures": figures, "notes": notes}


def find_metadata(directory, document, suffix):
    candidates = [directory / (document + suffix), directory / document / (document + suffix),
                  directory / "output" / (document + suffix)]
    return next((path for path in candidates if path.is_file()), None)


def inspect_log(path):
    result = {"file": str(path) if path else None, "missing": path is None,
              "missing_characters": [], "undefined_references": [], "overfull": [],
              "errors": [], "other_warnings": []}
    if path is None:
        return result
    result["sha256"] = sha256(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        kind = None
        if "Missing character:" in line:
            kind = "missing_characters"
        elif (re.search(r"(?:Reference|Citation)", line)
              and "undefined" in " ".join(lines[index:index + 4])) or re.search(
                  r"There were undefined (?:references|citations)", line):
            kind = "undefined_references"
        elif line.startswith("Overfull "):
            kind = "overfull"
        elif (line.startswith("!") or "Undefined control sequence" in line or "Emergency stop" in line
              or re.search(r"(?:LaTeX|Package [^ ]+) Error:", line)):
            kind = "errors"
        elif re.search(r"LaTeX Warning:|Package .+ Warning:|Font Warning:", line):
            kind = "other_warnings"
        if kind:
            record = {"line": index + 1, "text": line,
                      "context": "\n".join(lines[index:min(index + 4, len(lines))])[:1600]}
            amount = re.search(r"\(([0-9.]+)pt too (wide|high)\)", line)
            if amount:
                record.update(points=float(amount.group(1)), direction=amount.group(2))
            result[kind].append(record)
    return result


def inspect_recorder(path, source, figures):
    expected = {"figures/cover-concept.png"}
    for figure in figures:
        expected.update(figure["source_images"])
        if figure["concept_image"]:
            expected.add(figure["concept_image"])
    result = {"file": str(path) if path else None, "missing": path is None,
              "expected_images": sorted(expected), "source_images_missing": sorted(
                  name for name in expected if not (source / name).is_file())}
    if path is None:
        result["images_not_recorded"] = None
        return result
    result["sha256"] = sha256(path)
    inputs = sorted({line[6:].strip().strip('"').replace("\\", "/")
                     for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                     if line.startswith("INPUT ")})
    result["recorded_input_count"] = len(inputs)
    result["images_not_recorded"] = sorted(
        name for name in expected if not any(value == name or value.endswith("/" + name) for value in inputs))
    project = set()
    for value in inputs:
        candidates = [value.removeprefix("./")]
        marker = "/" + source.name + "/"
        if marker in value:
            candidates.append(value.rsplit(marker, 1)[1])
        for candidate in candidates:
            if ":" not in candidate and not candidate.startswith("/") and (source / candidate).is_file():
                project.add(candidate)
    result["recorded_project_inputs"] = sorted(project)
    return result


def read_aux_labels(path):
    if path is None:
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {fid: {"number": number, "printed_page": page}
            for fid, number, page in re.findall(
                r"\\newlabel\{fig:([^}]+)\}\{\{([^{}]+)\}\{([^{}]+)\}", text)}


def render_pages(document, name, destination, details, dpi):
    contact_dir, detail_dir = destination / "contacts" / name, destination / "details" / name
    contact_dir.mkdir(parents=True, exist_ok=True)
    sheets = []
    columns, per_sheet, cell_width, cell_height = 3, 12, 350, 500
    for first in range(0, len(document), per_sheet):
        last = min(first + per_sheet, len(document))
        rows = math.ceil((last - first) / columns)
        sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#e5e9ed")
        draw = ImageDraw.Draw(sheet)
        for offset, index in enumerate(range(first, last)):
            page = document[index]
            scale = min(326 / page.rect.width, 458 / page.rect.height)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
            thumbnail = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            left, top = (offset % columns) * cell_width, (offset // columns) * cell_height
            sheet.paste(thumbnail, (left + (cell_width - thumbnail.width) // 2,
                                    top + 30 + (458 - thumbnail.height) // 2))
            orientation = "landscape" if page.rect.width > page.rect.height else "portrait"
            draw.text((left + 10, top + 9), f"{name} / PDF p. {index + 1} / {orientation}", fill="#17324d")
        output = contact_dir / f"contact-{first + 1:03d}-{last:03d}.png"
        sheet.save(output)
        sheets.append(str(output))
    full_pages = []
    if details:
        detail_dir.mkdir(parents=True, exist_ok=True)
        for number in sorted(details):
            if not 1 <= number <= len(document):
                raise ValueError(f"Requested page outside {name}: {number}")
            output = detail_dir / f"page-{number:03d}.png"
            document[number - 1].get_pixmap(dpi=dpi, colorspace=fitz.csRGB, alpha=False).save(output)
            full_pages.append({"pdf_page": number, "file": str(output)})
    return {"contact_sheets": sheets, "detail_pages": full_pages, "detail_dpi": dpi}


def inspect_document(args, name, source_info):
    pdf = args.compiled_dir / (name + ".pdf")
    if not pdf.is_file():
        raise FileNotFoundError(f"Missing {name}.pdf in {args.compiled_dir}; historical named PDFs are not used as a fallback")
    with fitz.open(pdf) as document:
        texts = [page.get_text() for page in document]
        normal_texts = [compact(text) for text in texts]
        aux = read_aux_labels(find_metadata(args.logs_dir, name, ".aux"))
        figures = []
        for original in source_info["figures"]:
            figure = dict(original)
            title = compact(figure["title"])
            caption = compact("图" + figure["number"] + figure["title"])
            pages = [index + 1 for index, text in enumerate(normal_texts) if caption in text]
            method = "number_and_title"
            if not pages:
                pages = [index + 1 for index, text in enumerate(normal_texts) if title and title in text]
                method = "title_only" if pages else "not_found"
            figure.update(pdf_pages=pages, match_method=method, unique=len(pages) == 1,
                          aux_label=aux.get(figure["id"]))
            figures.append(figure)
        bounds, page_info = [], []
        for index, page in enumerate(document, 1):
            width, height = page.rect.width, page.rect.height
            page_info.append({"pdf_page": index, "pdf_label": page.get_label(),
                              "width_pt": round(width, 3), "height_pt": round(height, 3),
                              "rotation": page.rotation,
                              "orientation": "landscape" if width > height else "portrait"})
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        box = fitz.Rect(span["bbox"]) * page.rotation_matrix
                        if (box.x0 < -1.5 or box.y0 < -1.5 or box.x1 > width + 1.5 or box.y1 > height + 1.5):
                            bounds.append({"pdf_page": index, "bbox_display": list(box), "text": span["text"]})
        log = inspect_log(find_metadata(args.logs_dir, name, ".log"))
        recorder = inspect_recorder(find_metadata(args.logs_dir, name, ".fls"), args.source_dir, figures)
        record = {
            "file": str(pdf), "bytes": pdf.stat().st_size, "sha256": sha256(pdf),
            "pages": len(document), "page_geometry": page_info, "bookmarks": document.get_toc(),
            "fonts": sorted({font[3] for page in document for font in page.get_fonts(full=True)}),
            "a4_pages_in_either_orientation": all(
                abs(min(p.rect.width, p.rect.height) - 595.276) < 1 and
                abs(max(p.rect.width, p.rect.height) - 841.890) < 1 for p in document),
            "outside_text": bounds, "log": log, "recorder": recorder,
            "replacement_character_pages": [i + 1 for i, text in enumerate(texts) if "\ufffd" in text],
            "question_mark_pair_pages": [i + 1 for i, text in enumerate(texts) if "??" in text],
            "placeholder_pages": [i + 1 for i, text in enumerate(texts)
                                  if re.search(r"待插入图片|图片待补|图待补", text)],
            "source": source_info, "figures": figures,
            "figure_captions_unique": all(figure["unique"] for figure in figures),
            "aux_number_mismatches": [figure["id"] for figure in figures if figure["aux_label"]
                                      and figure["aux_label"]["number"] != figure["number"]],
        }
        text_dir = args.result_dir / "text"
        text_dir.mkdir(parents=True, exist_ok=True)
        (text_dir / (name + ".txt")).write_text("\n\n".join(
            f"=== PDF page {i + 1} ===\n{text}" for i, text in enumerate(texts)), encoding="utf-8")
        if not args.no_render:
            details = set(args.extra_pages.get(name, []))
            if name in args.detail_documents and "none" not in args.detail_figures:
                for figure in figures:
                    if "all" in args.detail_figures or figure["id"] in args.detail_figures:
                        details.update(figure["pdf_pages"])
            record["rendered"] = render_pages(document, name, args.render_dir, details, args.detail_dpi)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-dir", type=Path, default=BASE / "source")
    parser.add_argument("--compiled-dir", type=Path)
    parser.add_argument("--logs-dir", type=Path, default=BASE / "compile-v2-metadata" / "output")
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--documents", nargs="+", choices=tuple(NAMES), default=list(NAMES))
    parser.add_argument("--render-dir", type=Path, help="Default: RESULT_DIR/rendered")
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--detail-documents", nargs="+", choices=tuple(NAMES), default=["main"])
    parser.add_argument("--detail-figures", nargs="+", default=["all"], help="Figure IDs, all, or none")
    parser.add_argument("--detail-dpi", type=int, default=144)
    parser.add_argument("--page", action="append", default=[], metavar="DOCUMENT:PAGE",
                        help="Additional full page, e.g. --page main:1; repeat as needed")
    args = parser.parse_args()
    args.source_dir = args.source_dir.resolve()
    args.compiled_dir = (args.compiled_dir or args.source_dir / "output").resolve()
    args.logs_dir = args.logs_dir.resolve()
    args.result_dir = args.result_dir.resolve()
    args.render_dir = (args.render_dir or args.result_dir / "rendered").resolve()
    if args.detail_dpi < 72:
        parser.error("--detail-dpi must be at least 72")
    # This tool must never mix review output into the authoritative source tree.
    for destination in (args.result_dir, args.render_dir):
        if destination == args.source_dir or args.source_dir in destination.parents:
            parser.error("Review output must be outside --source-dir")
    args.extra_pages = {}
    for item in args.page:
        try:
            name, value = item.split(":", 1)
            number = int(value)
            if name not in args.documents or number < 1:
                raise ValueError()
        except ValueError:
            parser.error("Invalid --page value: " + item)
        args.extra_pages.setdefault(name, set()).add(number)
    args.result_dir.mkdir(parents=True, exist_ok=True)
    result = {"schema": "xiangshan-build11-pdf-inspection-v1",
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "status": "AUTOMATED_INSPECTION_COMPLETE_VISUAL_REVIEW_PENDING",
              "scope": "Existing PDF/source/log inspection only. No LaTeX, RTL, simulation or EDA is executed. Findings require interpretation and are not engineering acceptance gates.",
              "reports": {}, "input_errors": {}}
    maps = {}
    for name in args.documents:
        try:
            source_info = discover_source(args.source_dir, name)
            report = inspect_document(args, name, source_info)
            result["reports"][name] = report
            maps[name] = {"pages": report["pages"], "pdf_sha256": report["sha256"],
                          "figures": {figure["id"]: figure for figure in report["figures"]}}
            print(json.dumps({"document": name, "pages": report["pages"],
                              "figures": len(report["figures"]), "captions_unique": report["figure_captions_unique"],
                              "missing_characters": len(report["log"]["missing_characters"]),
                              "undefined_references": len(report["log"]["undefined_references"]),
                              "overfull": len(report["log"]["overfull"]),
                              "recorder_images_missing": report["recorder"]["images_not_recorded"]}, ensure_ascii=False), flush=True)
        except Exception as error:
            result["input_errors"][name] = f"{type(error).__name__}: {error}"
            print(json.dumps({"document": name, "input_error": result["input_errors"][name]}, ensure_ascii=False), flush=True)
    if result["input_errors"]:
        result["status"] = "INSPECTION_INCOMPLETE_INPUT_ERROR"
    for filename, data in (("pdf-inspection.json", result), ("page-map.json", maps)):
        (args.result_dir / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Visual review remains pending. Review directory: " + str(args.result_dir), flush=True)
    # Missing/unreadable input is a tool error. Layout/log findings never set this exit code.
    return 2 if result["input_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
