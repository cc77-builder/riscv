"""Finalize a new Build10 publication from actual, mutually bound evidence.

Read-only preflight precedes output creation. No compilation, rendering, image
generation/processing, base changes, image manager calls or Git publication.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import io
import json
import re
import struct
import zipfile

import fitz


WORK = Path(__file__).resolve().parents[1]
QA = "qa/concept-figures-20261106"
INPUT_DOCS = QA + "/build10-input-documents"
BASELINE_SHA = "e3a913fd7374e9948202d51844f0c7f127fe920c554bdbd0cc7aeb9d2e781ecc"
OVERLAY_SHA = "610d5da11884bfd04aeccdb634f0c6d812b4f62cb1a6a3997efa8f66c359ea50"
DRIVER_SHA = "785e17aede0c48145300ff85a4a82c452c49649d3cd11e330766c6822f1237a7"
SELECTED_SHA = "a74521b7993d70919fb7e8a609055e90afb301b789b8ed974a5e5bff2d6dde26"
METADATA_ARCHIVE = {"bytes": 180087, "sha256": "d6298405e2aba716cf05ea0a041f08012dfca0172dcb12af2d298ae2a0fa7d41"}
FIRST_FAILURE = {
    "build-receipt.json": {"bytes": 2377, "sha256": "b7c1287fa21aa12a40a956bf138bf90ff95e9c82dc6bf0ae7bb906ae9b427c09"},
    "state.json": {"bytes": 2377, "sha256": "b7c1287fa21aa12a40a956bf138bf90ff95e9c82dc6bf0ae7bb906ae9b427c09"},
    "post-input-check.json": {"bytes": 247, "sha256": "746bb695d0ba581d93cdb4c2fc566a690159bea98dc45570e92f76c23f9b85d4"},
}
SUPPLEMENTARY_VISUAL = {
    "stage2-stage3-visual-review.json": {"bytes": 21690, "sha256": "29d5c1c1924f18b0c22823f4bd262e11fa8bd3c9713ba4f08ca4881e4267e133"},
    "stage2-stage3-visual-review.md": {"bytes": 1761, "sha256": "0010024e7fb582c79df23d911c16b1d29243829b42ef662759e5d04459390a36"},
}
NAMES = {
    "main": "三阶段技术文档_合订本.pdf",
    "stage1": "第一阶段_执行日志与过程文档.pdf",
    "stage2": "第二阶段_设计与基础测试文档.pdf",
    "stage3": "第三阶段_协同仿真与性能分析.pdf",
}
DESCRIPTIONS = {
    "README.md", "插图清单与替换说明.md", "figures/README.md",
    "figures/evidence-20261105/图形表达参考.md",
    "figures/ai-concepts/layout-map.json", "BUILD10_LAYOUT_README.md",
    "figures/page-map.json", "qa/pdf-inspection.json", "交付校验.json",
    "publication-manifest.json",
}
LIMITS = [
    "概念伴图用于帮助理解；原精确图、正文和冻结工程证据承担位宽、时序、数值及验证结论。",
    "S2-09仍是合法算术截图，非法配置异常码与目的寄存器不更新的专门截图未新增；SQRT不因静态路径图增加动态覆盖。",
    "历史UTC容量审计FAIL、负时序裕量和墙钟稳定性未证实继续保留；整核Fmax、布线后时序及功耗未新增验证。",
    "本次通过范围是文档身份、图像显示与记录的视觉检查，不产生新的RTL、EMU、NEMU、应用性能或EDA资格。",
]


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def pin(row):
    return {key: row[key] for key in ("bytes", "sha256")}


def readj(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)


def checked_copy(source, target, expected=None):
    data = source.read_bytes()
    actual = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    need(expected is None or actual == expected, f"Input changed: {source}")
    write(target, data)
    need(identity(target) == actual, f"Copied bytes differ: {target}")


def relative(name):
    path = PurePosixPath(name.replace("\\", "/"))
    need(not path.is_absolute() and ".." not in path.parts
         and ":" not in path.as_posix(), f"Unsafe relative path: {name}")
    return path.as_posix()


def pdf_binding(row, actual, context):
    need(row["pdf_sha256"] == actual["sha256"]
         and row["pdf_bytes"] == actual["bytes"]
         and row["pages"] == actual["pages"], f"PDF binding differs: {context}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path,
                        default=WORK / "source/team/submission/latex-v1")
    parser.add_argument("--overlay", type=Path,
                        default=WORK / "build10-layout-work/v3/v2/overlay")
    parser.add_argument("--selected", type=Path, default=WORK / (
        "image-redesign/root-four-revisions-20261106/selected-22-delivery/"
        "XiangShan_Selected_22_Manifest_20261106.json"))
    parser.add_argument("--fetch", type=Path, default=WORK / "build10-fetch")
    parser.add_argument("--visual-review", type=Path, required=True)
    parser.add_argument("--asset-audit", type=Path, required=True)
    parser.add_argument("--supplementary-visual-review", type=Path, nargs=2,
                        metavar=("JSON", "MARKDOWN"),
                        default=[WORK / "build10-visual-review" / name for name in SUPPLEMENTARY_VISUAL])
    parser.add_argument("--preflight-failure", type=Path,
                        help="Directory containing the three original first-failure JSON records",
                        default=WORK / "build10-fetch/first-preflight-failure")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name, value in vars(args).items():
        setattr(args, name, [item.resolve() for item in value]
                if name == "supplementary_visual_review" else value.resolve())
    supplementary_paths = dict(zip(SUPPLEMENTARY_VISUAL, args.supplementary_visual_review))
    base, overlay, fetch, out = args.base, args.overlay, args.fetch, args.output
    meta = fetch / "metadata"
    need(not out.exists(), f"Keep existing publication: {out}")
    for input_dir in (base, overlay, fetch, args.selected.parent, args.asset_audit.parent,
                      args.visual_review.parent, args.preflight_failure,
                      *(path.parent for path in supplementary_paths.values())):
        need(out != input_dir and input_dir not in out.parents,
             f"Output must be outside input tree: {input_dir}")

    evidence_pins = {}

    def capture(path):
        data = path.read_bytes()
        actual = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        need(path not in evidence_pins or actual == evidence_pins[path],
             f"Evidence changed while reading: {path}")
        evidence_pins[path] = actual
        return data

    def evidence_json(path):
        return json.loads(capture(path))

    capture(Path(__file__).resolve())

    # Bind the extracted native records to the original archive; copy only these.
    raw_files = []
    archive_bytes = capture(fetch / "metadata.zip")
    need(evidence_pins[fetch / "metadata.zip"] == METADATA_ARCHIVE,
         "Fetched native metadata archive differs from the actual Build10 record")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        need(len(names) == len(set(names)), "Duplicate metadata archive members")
        for name in names:
            rel = relative(name)
            need(rel == name, f"Noncanonical archive name: {name}")
            data = archive.read(name)
            expected = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            need(identity(meta / rel) == expected, f"Extracted metadata differs: {rel}")
            evidence_pins[meta / rel] = expected
            raw_files.append({"path": rel, **expected})
    baseline_path = meta / "controls/source-preservation.json"
    overlay_path = meta / "controls/overlay-manifest.json"
    driver_path = meta / "controls/build10_native_driver.py"
    for path, expected_sha in ((baseline_path, BASELINE_SHA), (overlay_path, OVERLAY_SHA),
                               (driver_path, DRIVER_SHA), (args.selected, SELECTED_SHA)):
        capture(path)
        need(evidence_pins[path]["sha256"] == expected_sha, f"Pinned input differs: {path}")
    baseline, overlay_manifest = evidence_json(baseline_path), evidence_json(overlay_path)
    receipt = evidence_json(meta / "build-receipt.json")
    frozen_doc = evidence_json(meta / "frozen-sources.json")
    frozen = frozen_doc["files"]
    inspection = evidence_json(meta / "qa/pdf-inspection.json")
    page_map = evidence_json(meta / "qa/page-map.json")
    post, build_assets = evidence_json(meta / "post-input-check.json"), evidence_json(meta / "asset-receipt.json")
    selected = evidence_json(args.selected)
    audit, visual = evidence_json(args.asset_audit), evidence_json(args.visual_review)
    for name, path in supplementary_paths.items():
        capture(path)
        need(evidence_pins[path] == SUPPLEMENTARY_VISUAL[name],
             f"Supplementary visual-review bytes differ: {name}")
    supplementary_visual = evidence_json(supplementary_paths["stage2-stage3-visual-review.json"])
    for name, expected_pin in FIRST_FAILURE.items():
        path = args.preflight_failure / name
        evidence_json(path)  # Preserve raw history; never treat the old failure as a PASS.
        need(evidence_pins[path] == expected_pin, f"First-failure bytes differ: {name}")
    need(receipt["exit_code"] == 0 and receipt["post_input_mismatch_count"] == 0,
         "Native build did not complete successfully")
    need(receipt["status"] == "AUTOMATED_INSPECTION_COMPLETE_VISUAL_REVIEW_PENDING",
         "Unexpected native build qualification")
    need(inspection["status"] == "AUTOMATED_INSPECTION_COMPLETE_VISUAL_REVIEW_PENDING",
         "Unexpected original automatic-inspection qualification")
    need([step["name"] for step in receipt["steps"]] == [*NAMES, "inspect"]
         and all(step["exit_code"] == 0 for step in receipt["steps"]),
         "All four fresh builds and the original inspector must complete")
    need(not post["mismatches"] and post["source_freeze_complete"]
         and post["base_verified_before_execution"], "Native input freeze did not close")
    need(receipt["driver_identity"] == identity(driver_path), "Executed driver identity differs")
    need(receipt["asset_manifest_identity"] == identity(meta / "controls/assets-manifest.json")
         == build_assets["manifest"], "Native asset input manifest binding differs")

    # Reconstruct exactly the 469 compiler inputs before descriptive publication edits.
    formal = {name: value for name, value in baseline["baseline_files"].items()
              if name not in baseline["excluded_existing_cache_paths"]}
    need(len(formal) == 448 and len(frozen) == 469, "Unexpected source input counts")
    for name, expected in formal.items():
        need(identity(base / relative(name)) == expected, f"Base identity differs: {name}")
    origins = {name: base / name for name in formal
               if name not in baseline["omitted_old_output_files"]}
    expected = {name: formal[name] for name in origins}
    for row in overlay_manifest["files"]:
        name = relative(row["path"])
        need(identity(overlay / name) == row["after"], f"Overlay identity differs: {name}")
        origins[name], expected[name] = overlay / name, row["after"]
        evidence_pins[overlay / name] = row["after"]
    layout = evidence_json(overlay / "figures/ai-concepts/layout-map.json")
    targets = [row["id"] for row in layout["illustrations"]]
    asset_rows = selected["assets"]
    need(selected["selected_count"] == len(asset_rows) == len(targets) == 22
         and {row["figure_id"] for row in asset_rows} == set(targets),
         "Selected asset IDs differ from the reviewed layout")
    by_id = {row["figure_id"]: row for row in asset_rows}
    native_assets = {row["id"]: row for row in build_assets["assets"]}
    need(len(native_assets) == 22 and set(native_assets) == set(targets),
         "Native asset receipt must contain the same 22 IDs")
    reviews = {}
    for fid in targets:
        row = by_id[fid]
        image = args.selected.parent / relative(row["package_path"])
        need(identity(image) == pin(row), f"Selected PNG identity differs: {fid}")
        header = image.read_bytes()[:24]
        need(header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR"
             and struct.unpack(">II", header[16:24]) == (row["width"], row["height"]),
             f"Selected PNG dimensions differ: {fid}")
        name = f"figures/ai-concepts/{fid}.png"
        native = native_assets[fid]
        need(pin(native) == pin(row) and native["copied_path"] == name
             and (native["width"], native["height"]) == (row["width"], row["height"]),
             f"Selected/native PNG binding differs: {fid}")
        origins[name], expected[name] = image, pin(row)
        review = row["review_source"]
        review_path = Path(review["report_path"])
        need(review_path.suffix.lower() == ".md" and review["verdict"] == "PASS",
             f"Missing selected review reference: {fid}")
        capture(review_path)
        need(evidence_pins[review_path]["sha256"] == review["report_sha256"],
             f"Selected review bytes differ: {fid}")
        reviews[review["report_sha256"]] = review_path
    need(expected == frozen and len(origins) == 469, "Cannot reconstruct all frozen build inputs")
    need(audit["result"] == "PASS" and audit["selected_manifest_sha256"] == SELECTED_SHA
         and audit["page_map_sha256"] == evidence_pins[meta / "qa/page-map.json"]["sha256"],
         "Actual asset audit is absent, unverified or bound to different inputs")
    need(visual["result"] == "PASS" and visual["performed"] is True
         and visual["reviewer_role"] == "root" and visual["reviewed_at_utc"]
         and visual["blocking_findings"] == [], "Actual root visual PASS is required")
    need(visual["automatic_qa_sha256"] == evidence_pins[meta / "qa/pdf-inspection.json"]["sha256"]
         and visual["asset_audit_sha256"] == evidence_pins[args.asset_audit]["sha256"],
         "Root visual review is bound to different automatic evidence")
    need(len(visual["supplementary_reviews"]) == 2
         and {row["path"]: pin(row) for row in visual["supplementary_reviews"]} == SUPPLEMENTARY_VISUAL,
         "Root visual review does not bind both archived supplementary records")
    need(supplementary_visual["result"] == "PASS" and supplementary_visual["blocking_findings"] == []
         and supplementary_visual["asset_audit_sha256"] == evidence_pins[args.asset_audit]["sha256"]
         and supplementary_visual["selected_manifest_sha256"] == SELECTED_SHA
         and supplementary_visual["page_map_sha256"] == evidence_pins[meta / "qa/page-map.json"]["sha256"],
         "Supplementary visual review is bound to different inputs or has blockers")
    for record, name in ((inspection["reports"], "automatic QA"), (audit["documents"], "asset audit"),
                         (visual["documents"], "root visual review"), (page_map, "page map")):
        need(set(record) == set(NAMES), f"Four document records are required: {name}")

    pdfs = {}
    native_pdfs = {row["document"]: row for row in receipt["files"]}
    need(set(native_pdfs) == set(NAMES), "Native PDF receipt is incomplete")
    for document in NAMES:
        pdf = fetch / (document + ".pdf")
        actual = identity(pdf)
        with fitz.open(pdf) as opened:
            actual["pages"] = len(opened)
        pdfs[document] = actual
        need(pin(native_pdfs[document]) == pin(actual)
             and native_pdfs[document]["build_origin"] == "build-10",
             f"Actual PDF differs from the fresh native build: {document}")
        for table, name in ((inspection["reports"], "QA"), (audit["documents"], "audit"),
                            (visual["documents"], "visual")):
            pdf_binding(table[document], actual, document + "/" + name)
        if document in ("stage2", "stage3"):
            pdf_binding(supplementary_visual["documents"][document], actual,
                        document + "/supplementary visual")
        automatic = inspection["reports"][document]
        need(automatic["a4_all_pages"] and automatic["figure_captions_unique"]
             and all(not automatic[field] for field in (
                 "outside_text", "footer_mismatches", "placeholder_pages")),
             f"Automatic document checks did not pass: {document}")
        observed = visual["documents"][document]
        need(observed["reviewed"] is True and observed["observed_scope"],
             f"Actual root viewing scope is missing: {document}")
        mapped = page_map[document]
        wanted = layout["expected_outputs"][document]
        need(mapped["pages"] == actual["pages"]
             and set(mapped["figures"]) == set(wanted["original_technical_ids"]),
             f"Original technical figure map differs: {document}")
        for fid, row in mapped["figures"].items():
            need(row["present"] and len(row["pdf_pages"]) == 1
                 and 1 <= row["pdf_pages"][0] <= actual["pages"]
                 and relative(row["source_path"]) == f"figures/{fid}.pdf",
                 f"Invalid original figure page: {document}/{fid}")
        concepts = audit["documents"][document]["concepts"]
        need(set(concepts) == set(wanted["ai_ids"]), f"Companion count differs: {document}")
        for fid, row in concepts.items():
            need(row["sha256"] == by_id[fid]["sha256"] and row["identity_match"] is True
                 and row["geometry_match"] is True and row["occurrence_count"] == 1
                 and len(row["pdf_pages"]) == 1 and row["match_method"]
                 and 1 <= row["pdf_pages"][0] <= actual["pages"],
                 f"Companion identity/occurrence/geometry did not close: {document}/{fid}")

    # No output exists until actual build, audit and root visual evidence all agree.
    now = datetime.now(timezone.utc).isoformat()
    source, delivery = out / "source", out / "delivery"
    out.mkdir(parents=True, exist_ok=False)
    source.mkdir()
    delivery.mkdir()
    for name, original in origins.items():
        checked_copy(original, source / name, frozen[name])
    for row in raw_files:
        checked_copy(meta / row["path"], source / QA / "build10-native" / row["path"], pin(row))
    checked_copy(fetch / "metadata.zip", source / QA / "build10-native-metadata.zip",
                 evidence_pins[fetch / "metadata.zip"])
    checked_copy(driver_path, source / QA / "drivers/build10_native_driver.py", evidence_pins[driver_path])
    checked_copy(Path(__file__).resolve(), source / QA / "drivers/finalize_build10_metadata.py",
                 evidence_pins[Path(__file__).resolve()])
    for original, name in (
        (args.selected, "selected-22-manifest.original.json"),
        (args.asset_audit, "asset-audit.json"), (args.visual_review, "root-visual-review.json")):
        checked_copy(original, source / QA / name, evidence_pins[original])
    for name, expected_pin in FIRST_FAILURE.items():
        checked_copy(args.preflight_failure / name, source / QA / "first-preflight-failure" / name,
                     expected_pin)
    for name, original in supplementary_paths.items():
        checked_copy(original, source / QA / name, SUPPLEMENTARY_VISUAL[name])
    review_locations = {}
    for index, (review_sha, original) in enumerate(sorted(reviews.items()), 1):
        name = f"{QA}/concept-reviews/review-{index:02d}.md"
        checked_copy(original, source / name, evidence_pins[original])
        review_locations[review_sha] = name
    for document, name in NAMES.items():
        checked_copy(fetch / (document + ".pdf"), source / "output" / name, pin(pdfs[document]))
        checked_copy(fetch / (document + ".pdf"), delivery / name, pin(pdfs[document]))

    # Archive every changed compiler input before its descriptive replacement.
    archived = {}

    def update(name, data):
        need(name in DESCRIPTIONS, f"Unreviewed descriptive change: {name}")
        if name not in archived:
            need(identity(source / name) == frozen[name], f"Input changed before archiving: {name}")
            checked_copy(source / name, source / INPUT_DOCS / name, frozen[name])
            archived[name] = frozen[name]
        write(source / name, data)

    portable_rows = []
    for fid in targets:
        row = by_id[fid]
        portable_rows.append({
            "id": fid, "path": f"figures/ai-concepts/{fid}.png", **pin(row),
            "width": row["width"], "height": row["height"],
            "review": review_locations[row["review_source"]["report_sha256"]],
            "review_sha256": row["review_source"]["report_sha256"],
            "review_scope": "Model review of this concept image; document viewing is recorded separately.",
        })
    portable = {
        "schema": "build10-portable-concept-assets-v1", "status": "INTEGRATED_DOCUMENT_QA_COMPLETE",
        "paths_relative_to": "publication source root",
        "selected_count": 22, "source_manifest": QA + "/selected-22-manifest.original.json",
        "source_manifest_sha256": SELECTED_SHA, "visual_review": QA + "/root-visual-review.json",
        "assets": portable_rows,
    }
    write(source / "figures/ai-concepts/selected-assets.json", encoded(portable))
    layout["status"] = "INTEGRATED_DOCUMENT_QA_COMPLETE"
    layout["source_plan"] = {
        "compiled_layout_map": INPUT_DOCS + "/figures/ai-concepts/layout-map.json",
        **frozen["figures/ai-concepts/layout-map.json"],
    }
    layout["selected_asset_count"] = 22
    layout["final_image_identity_enforcement"] = (
        "Selected PNG bytes match the 469-file native freeze, actual asset audit, and root visual record.")
    portable_by_id = {row["id"]: row for row in portable_rows}
    for row in layout["illustrations"]:
        row["selected_asset"] = portable_by_id[row["id"]]
        row["selection_status"] = "INTEGRATED_DOCUMENT_QA_COMPLETE"
    update("figures/ai-concepts/layout-map.json", encoded(layout))
    final_map = copy.deepcopy(page_map)
    for document in NAMES:
        for row in final_map[document]["figures"].values():
            row["source_path"] = relative(row["source_path"])
        final_map[document]["concept_figures"] = {
            fid: {"pdf_pages": row["pdf_pages"], "source_path": f"figures/ai-concepts/{fid}.png"}
            for fid, row in audit["documents"][document]["concepts"].items()}
    update("figures/page-map.json", encoded(final_map))

    pdf_table = ["| 文档 | 实际页数 | 原技术图位 | 概念伴图 |",
                 "| --- | ---: | ---: | ---: |"]
    for document, name in NAMES.items():
        wanted = layout["expected_outputs"][document]
        pdf_table.append(f"| {name} | {pdfs[document]['pages']} | "
                         f"{len(wanted['original_technical_ids'])} | {len(wanted['ai_ids'])} |")
    table = "\n".join(pdf_table)
    limits = "\n".join("- " + item for item in LIMITS)
    rebuild = (
        "常规重编使用原 `build.py` 与已记录的 XeLaTeX、SimSun、Times New Roman 环境，"
        "无需运行正文展开器、绘图器或生图工具。精确恢复本次构建输入时，在全新目录按 "
        f"`{QA}/build10-native/frozen-sources.json` 逐项复制：描述性更新的文件取 "
        f"`{INPUT_DOCS}/` 中的原字节，其余取当前 source。469 项全部核验后再编译。"
        "字体和系统库没有因编译器 exe 的 SHA 而自动冻结，不承诺跨环境重编 PDF 字节必然相同。")
    update("README.md", f"""# 三阶段技术报告 · Build10

本版已将 22 张实际选定的 AI 概念伴图加入四份完整报告，并保留原 22 张精确技术图、9 个截图组、三份正文和四个入口的字节身份。伴图为无编号的独立说明块，通过原图标签引用技术依据；原图编号、caption 和技术说明保持不变。封面另计。

{table}

四份 PDF 均由本次原生构建重新生成。实际文件身份、自动结构检查、伴图像素身份／次数／几何核对和主端实际视觉审查已相互绑定，原始记录位于 `{QA}/`。审查主体和观察范围按原记录保留，文档通过不扩展为新的工程资格。

## 阅读与复现

`output/` 保存四份 PDF；`插图清单与替换说明.md` 给出本次实际物理页码；`figures/ai-concepts/selected-assets.json` 是可移植的 22 图路径、SHA、尺寸和审查索引。逐图模型审查 Markdown 原文已收录，其中涉及旧候选的 REVISE 和限定没有删改。`figures/page-map.json` 同时记录原技术图与伴图页面。

{rebuild}

## 工程范围和历史

{limits}

原 Build09 及更早 QA、失败记录继续保留。首次 Build10 缓存预检失败的三份原始回执在 `{QA}/first-preflight-failure/`；后续只增加两个明确 Python 3.13 缓存的排除，448 项正式基线身份要求未放宽。文件清单与复原闭合记录分别见 `publication-manifest.json` 和 `{QA}/package-source-closure.json`。
""")
    figures = []
    for stage in (1, 2, 3):
        body = (source / f"sections/stage{stage}.tex").read_text(encoding="utf-8")
        for fid, caption in re.findall(r"\\(?:reportfigure|evidencefigure)\{([^}]+)\}\{([^}]+)\}", body):
            main_row = page_map["main"]["figures"][fid]
            booklet_row = page_map[f"stage{stage}"]["figures"][fid]
            figures.append((fid, caption, main_row["number"],
                            main_row["pdf_pages"][0], booklet_row["pdf_pages"][0]))
    need(len(figures) == 31, "Original caption inventory changed")
    index = ["# Build10 插图清单", "", table, "",
             "页码均为从封面第 1 页起的 PDF 物理页码；稳定 ID 与正文图号分别记录。", "",
             "## 原技术图与截图", "",
             "| ID | 原图号 | 原图题 | 合订本页 | 对应分册页 |",
             "| --- | --- | --- | ---: | ---: |"]
    for fid, caption, number, main_page, booklet_page in figures:
        index.append(f"| {fid} | 图{number} | {caption} | {main_page} | {booklet_page} |")
    index += ["", "## 无编号概念伴图", "",
              "| ID | 主题 | 合订本页 | 对应分册页 |",
              "| --- | --- | ---: | ---: |"]
    for row in layout["illustrations"]:
        fid, document = row["id"], f"stage{row['stage']}"
        main_page = audit["documents"]["main"]["concepts"][fid]["pdf_pages"][0]
        booklet_page = audit["documents"][document]["concepts"][fid]["pdf_pages"][0]
        index.append(f"| {fid} | {row['concept_topic']} | {main_page} | {booklet_page} |")
    index += ["", "精确图、截图和概念 PNG 原字节均保留；逐图来源与审查引用见 "
              "`figures/ai-concepts/selected-assets.json`。", "", limits, ""]
    index_text = "\n".join(index)
    update("插图清单与替换说明.md", index_text)
    write(delivery / "01_插图索引.md", index_text)
    update("figures/README.md", f"""# Build10 报告图片

本版保留 31 个原技术图位：13 张精确 SVG 结构图、9 张精确数据／事件图、9 个原截图组；新增 22 张无编号概念伴图，三阶段分别为 4／9／9 张，封面另计。

原图继续优先读取 `figures/<ID>.pdf`。伴图由 `report-concepts.tex` 读取 `figures/ai-concepts/<ID>.png`，完整画布按原比例显示，伴图块与精确图块可自然分页。新增伴图的内容与版面审查各自记账，原数据、位宽、时序和结果仍以原图与正文为依据。

`ai-concepts/selected-assets.json` 保存相对路径、原 PNG SHA、尺寸和逐图审查引用；`page-map.json` 使用本次实际 PDF 页码。原始选图 manifest、完整审查 Markdown、像素身份／次数／几何核验和主端视觉记录保存在 `../{QA}/`，未复制图片管理器、claim 或私有请求。

风格参考与表达决策见 `evidence-20261105/图形表达参考.md`。原图、旧候选、历史截图和失败证据继续保留。{LIMITS[1]} {LIMITS[2]}

{rebuild}
""")
    old_style = (base / "figures/evidence-20261105/图形表达参考.md").read_text(encoding="utf-8")
    start = old_style.index("## 官方参考")
    end = old_style.index("## 本版的工程表达", start)
    style = f"""# Build10 图形表达与既有厂商参考

本版以“概念伴图＋精确技术图”组织阅读：22 张概念 PNG 讲解关系与过程，31 个原技术图位保留精确数据、实现约束和历史截图。新增概念说明通过既有图号引向技术依据，图块保留完整画布和比例；没有用概念图替换测量值、逐拍记录、位域或验证证据。

本次逐图审查按选定 PNG 的实际 SHA 关联，审查原文及最终 PDF 观察范围见 `{QA}/`。色彩、字号与构图的判断以这些实际记录为准；生成提示词不构成字体 point 元数据，像素匹配不等于遮挡或可读性检查。原 31 个技术图的字体、矢量和来源记录保持原身份。

下列官方参考沿用已经归档的来源与组织方法说明，本收尾未重新抓取或改写厂商图片；它们不决定本项目的数值、接口或技术资格。

{old_style[start:end].rstrip()}

## 当前证据与范围

{limits}

历史制图、Build09 及失败记录仍在原目录。被本次更新的说明文件原字节保存在 `{INPUT_DOCS}/`，可恢复完整 469 项编译输入。
"""
    update("figures/evidence-20261105/图形表达参考.md", style)
    write(delivery / "03_图形表达与参考.md", style)
    update("BUILD10_LAYOUT_README.md", f"""# Build10 伴图整合与构建记录

22 张最终概念 PNG 已按显式映射整合，原 31 个技术图位、三份正文和四入口原字节保留。S2-03 的伴图说明为“VFEX4 父级派发与共享输出管理”；S3-08 为“三种制品分别核对装载内容、有序调用表和输入身份”。原精确图注未改变。

{table}

本次四份全部重编，构建和前后输入身份见 `{QA}/build10-native/`；新增图像的实际包含、次数和几何见 asset-audit.json，主端实际观看范围见 root-visual-review.json。结论仅覆盖记录的文档检查范围。

{rebuild}
""")

    final_qa = copy.deepcopy(inspection)
    final_qa.update({
        "date": now[:10], "status": "DOCUMENT_QA_PASS", "edition": "Build10",
        "finalized_utc": now, "scope": "Document integration and recorded review only; no new engineering qualification.",
        "review_authority": "root consolidated document review with separately archived native-agent visual review and model concept-image reviews",
        "user_whole_set_aesthetic_approval_claimed": False,
        "native_build_receipt": QA + "/build10-native/build-receipt.json",
        "raw_automatic_qa": QA + "/build10-native/qa/pdf-inspection.json",
        "asset_audit": QA + "/asset-audit.json", "asset_audit_sha256": evidence_pins[args.asset_audit]["sha256"],
        "root_visual_review": QA + "/root-visual-review.json", "root_visual_review_sha256": evidence_pins[args.visual_review]["sha256"],
        "post_input_check_sha256": evidence_pins[meta / "post-input-check.json"]["sha256"],
        "visual_reviewed_at_utc": visual["reviewed_at_utc"], "disclosed_limits": LIMITS,
        "supplementary_visual_reviews": [
            {"path": QA + "/" + name, **row} for name, row in SUPPLEMENTARY_VISUAL.items()],
        "figures": {"original_technical_slots": 31, "precise_structural": 13,
                    "precise_data_event": 9, "original_screenshot_groups": 9,
                    "concept_companions": 22, "cover_separate": True},
    })
    update("qa/pdf-inspection.json", encoded(final_qa))
    update("交付校验.json", encoded(final_qa))
    write(delivery / "04_交付校验.json", encoded(final_qa))
    write(source / QA / "README.md", f"""# Build10 文档证据

`build10-native-metadata.zip` 与 `build10-native/` 保留本次原生构建的原记录和驱动，未把原自动检查状态改成视觉结论。`root-visual-review.json` 是主端整合的实际观看记录；`stage2-stage3-visual-review.json` 与同名 Markdown 原样保存独立子智能体对第二、三册的实际观察、范围和非阻塞项，不将它们归为主端亲自观看。`asset-audit.json` 仅核像素身份、次数与几何。`concept-reviews/` 保存选图 manifest 引用的 Markdown 原文，包含其中对旧候选的 REVISE。

`selected-22-manifest.original.json` 保留原选图记录；可移植索引在源码根目录的 `figures/ai-concepts/selected-assets.json`。没有复制图片管理器、claim 或私有请求文件。`first-preflight-failure/` 完整保留首次预检失败的 build-receipt.json、state.json 和 post-input-check.json；原 Build09 和更早 QA 仍在原目录。

`build10-input-documents/` 保存所有发生描述性更新的原编译输入。恢复规则与逐文件闭合见 `package-source-closure.json`。{LIMITS[-1]}
""")
    # The manifest is also a frozen input: archive its old bytes before replacement.
    update("publication-manifest.json", (source / "publication-manifest.json").read_bytes())
    need(set(archived) == DESCRIPTIONS, "A changed description was not archived")
    for name, expected_pin in frozen.items():
        original = source / INPUT_DOCS / name if name in archived else source / name
        need(identity(original) == expected_pin, f"469-file reconstruction failed: {name}")
        if name not in DESCRIPTIONS:
            need(identity(source / name) == expected_pin, f"Protected input changed: {name}")
    closure = {
        "schema": "build10-package-source-closure-v1", "verified_utc": now,
        "frozen_input_count": len(frozen), "all_469_exactly_reconstructable": True,
        "post_build_descriptive_updates": sorted(archived),
        "original_description_overlay": INPUT_DOCS + "/",
        "all_original_31_display_pdfs_unchanged": True,
        "three_body_and_four_entry_files_unchanged": True,
        "concept_png_bytes_unchanged": True, "rendering_tex_unchanged_after_build": True,
        "original_input_files": archived,
        "raw_frozen_sources": QA + "/build10-native/frozen-sources.json",
        "scope": "Descriptive publication updates only; original technical evidence and build inputs preserved.",
    }
    write(source / QA / "package-source-closure.json", encoded(closure))
    base_manifest = readj(base / "publication-manifest.json")
    files = [{"path": p.relative_to(source).as_posix(), **identity(p)}
             for p in sorted(source.rglob("*")) if p.is_file()
             and p.relative_to(source).as_posix() != "publication-manifest.json"]
    publication = {
        "schema": "report-build10-publication-manifest-v1", "created_utc": now, "build": "Build10",
        "source_report_commit": base_manifest.get("source_report_commit"),
        "base_publication_manifest_sha256": identity(base / "publication-manifest.json")["sha256"],
        "scope": final_qa["scope"], "self_excluded": True, "file_count": len(files), "files": files,
        "frozen_input_count": 469, "source_closure": QA + "/package-source-closure.json",
        "qa": "qa/pdf-inspection.json",
    }
    update("publication-manifest.json", encoded(publication))
    need(all(identity(source / row["path"]) == pin(row) for row in files),
         "Final publication file inventory differs")
    need(all(identity(base / name) == expected_pin for name, expected_pin in formal.items()),
         "Original base changed during finalization")
    need(all(identity(origins[name]) == expected_pin for name, expected_pin in frozen.items()),
         "An original overlay/PNG/source input changed during finalization")
    need(all(identity(path) == expected_pin for path, expected_pin in evidence_pins.items()),
         "An original build/review/history record changed during finalization")
    result = {
        "schema": "build10-finalization-receipt-v1", "status": "DOCUMENT_QA_PASS",
        "completed_utc": datetime.now(timezone.utc).isoformat(), "output": str(out),
        "publication_manifest": identity(source / "publication-manifest.json"),
        "source_file_count_including_manifest": len(files) + 1,
        "compiled_input_count": 469, "archived_descriptive_inputs": sorted(archived),
        "metadata_zip": evidence_pins[fetch / "metadata.zip"], "selected_manifest": evidence_pins[args.selected],
        "visual_review": evidence_pins[args.visual_review], "asset_audit": evidence_pins[args.asset_audit],
        "first_preflight_failure": FIRST_FAILURE,
        "supplementary_visual_reviews": SUPPLEMENTARY_VISUAL,
        "finalizer_identity": evidence_pins[Path(__file__).resolve()],
        "pdfs": {name: {"file": NAMES[name], **row} for name, row in pdfs.items()},
        "new_compilation_or_image_processing": False, "user_aesthetic_approval_claimed": False,
    }
    result_bytes = encoded(result)
    write(delivery / "README.md", f"""# Build10 文档交付

四份正式 PDF 已完成本次原生编译、自动检查、伴图资产核验及主端记录的实际视觉审查。完整源码位于同级 `source/`，图像原件、审查 Markdown、构建原始记录和469项输入复原资料均随源码保存。

{table}

`01_插图索引.md` 使用本次实际物理页码；`03_图形表达与参考.md` 保存表达方法和既有厂商参考；`04_交付校验.json` 记录本次文档范围。{LIMITS[-1]}
""")
    write(out / "delivery-manifest.json", encoded({
        "schema": "build10-delivery-manifest-v1", "created_utc": now,
        "files": [{"path": p.relative_to(out).as_posix(), **identity(p)}
                  for p in sorted(delivery.rglob("*")) if p.is_file()],
        "finalization_receipt": {"bytes": len(result_bytes), "sha256": hashlib.sha256(result_bytes).hexdigest()},
        "publication_manifest": identity(source / "publication-manifest.json"),
    }))
    # This completion receipt is deliberately written last. A partial output is
    # evidence of a failed/interrupted finalization, not a completed publication.
    write(out / "finalization-receipt.json", result_bytes)
    print(json.dumps({"status": result["status"], "output": str(out),
                      "pages": {name: row["pages"] for name, row in pdfs.items()},
                      "publication_files": len(files)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
