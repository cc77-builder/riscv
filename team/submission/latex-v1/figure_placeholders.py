"""Add stable, version-qualified image slots to the generated reports."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent


def tex_text(value):
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
               "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
               "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    pieces = re.split(r"([A-Za-z0-9_./:=+-]{16,})", value)
    result = []
    for piece in pieces:
        escaped = "".join(mapping.get(c, c) for c in piece)
        result.append(r"\seqsplit{" + escaped + "}" if re.fullmatch(r"[A-Za-z0-9_./:=+-]{16,}", piece) else escaped)
    return "".join(result)


def apply_figure_slots(body, stage):
    # Preserve the previous drawn figures in qa/before-figures-20261102.
    # Their replacement slots explicitly distinguish drawings from raw waveforms.
    marker = "__STAGE1_TIMELINE__" if stage == 1 else "__STAGE2_DATAPATH__"
    if stage in (1, 2):
        pattern = r"\\begin\{center\}\s*\\begin\{tikzpicture\}.*?\\end\{center\}"
        body, count = re.subn(pattern, marker, body, flags=re.S)
        if count != 1:
            raise ValueError(f"Stage {stage}: expected one original drawn figure, got {count}")
    slots = json.loads((ROOT / "figures/placement.json").read_text(encoding="utf-8"))
    for slot in (s for s in slots if s["stage"] == stage):
        anchor = slot["anchor"]
        if body.count(anchor) != 1:
            raise ValueError(f"Non-unique or absent anchor for {slot['id']}: {anchor}")
        title = tex_text(slot["title"])
        content = tex_text(slot["content"])
        source = tex_text(slot["source"] + "。版本范围：" + slot["scope"] + "。")
        command = ("\n\\reportfigure{" + slot["id"] + "}{" + title + "}{"
                   + str(slot["height_cm"]) + "cm}{" + content + "}{" + source + "}\n")
        body = body.replace(anchor, command if anchor.startswith("__STAGE") else command + anchor, 1)
    first, rest = body.split("\n", 1)
    return (r"\renewcommand{\stagefigureprefix}{" + str(stage) + "}"
            + r"\setcounter{figure}{0}" + "\n" + first + "\n" + rest)
