"""tu 风格 1:1 画布工具：画布单位 mm，字号单位 pt，中文 Noto Serif SC，西文 Times New Roman。"""
import itertools
import os
from html import escape
from PIL import ImageFont

PT = 0.352778          # 1 pt in mm
CJK_FAMILY = "Noto Serif SC"
LAT_FAMILY = "Times New Roman"
CJK_WEIGHT = int(os.environ.get("TU_CJK_WEIGHT", "400"))   # 400 = Regular，与原 tu 图一致；正文 FandolSong 墨量约为其 0.87

# 字号规范（pt，未含全局调整）
S_PANEL = 10.0   # 分区标题
S_TITLE = 9.5    # 框标题
S_BODY = 8.5     # 框内正文、边标签
S_LABEL = 8.0    # 次要标签
S_NOTE = 7.5     # 最小说明字
# 全局字号调整：所有文字统一加减，默认整体缩小 1 pt
SIZE_DELTA = float(os.environ.get("TU_SIZE_DELTA", "-1.0"))

C = {
    "ink": "#22384A", "grey": "#526775", "faint": "#8194A3", "rule": "#DAE3EB",
    "panel": "#F7F9FB", "panel_s": "#D5DEE6", "line": "#46627A",
    "blue": "#2B6189", "blue_s": "#7CA1C4", "blue_f": "#F2F7FC",
    "teal": "#13827F", "teal_s": "#6CA8A4", "teal_f": "#EFF8F6",
    "orange": "#AD641F", "orange_s": "#BD8C4C", "orange_f": "#FFF7EF",
    "purple": "#6A4C93", "purple_s": "#9C86BC", "purple_f": "#F6F2FA",
    "white": "#FFFFFF",
    "plain_f": "#FFFFFF", "plain_s": "#BFCCD7",
}

_cjk_font = ImageFont.truetype("C:/Windows/Fonts/NotoSerifSC-VF.ttf", 100)
try:
    _cjk_font.set_variation_by_axes([CJK_WEIGHT])
except Exception:
    pass
_lat_font = ImageFont.truetype("C:/Windows/Fonts/times.ttf", 100)


def is_cjk(ch):
    o = ord(ch)
    return (0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF
            or 0x3000 <= o <= 0x303F)


def runs(s):
    return [(k, "".join(g)) for k, g in itertools.groupby(s, key=is_cjk)]


def width(s, pt):
    total = 0.0
    for cjk, part in runs(s):
        f = _cjk_font if cjk else _lat_font
        total += f.getlength(part) / 100.0
    return total * pt * PT


class SVG:
    def __init__(self, w, h, title="", arrow=1.55, sw=0.2):
        self.w, self.h, self.title = w, h, title
        self.arrow = arrow      # 箭头头部尺寸（mm）
        self.sw = sw            # 默认连线粗细（mm）
        self.items = []
        self.markers = set()
        self.boxes = []      # (name, x0, x1) for overflow checks
        self.warnings = []

    # ---------- shapes ----------
    def rect(self, x, y, w, h, fill="none", stroke=None, sw=0.22, rx=0.7, dash=None):
        a = f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{rx}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.items.append(a + "/>")

    def box(self, x, y, w, h, kind, dash=None, sw=0.24):
        fill = C.get(kind + "_f", C.get(kind, C["white"])) if kind != "white" else C["white"]
        self.rect(x, y, w, h, fill=fill, stroke=C[kind + "_s"] if kind != "white" else C["blue_s"], sw=sw, dash=dash)

    def line(self, pts, color, sw=None, dash=None, arrow=True, dot_start=False, start_arrow=False):
        sw = self.sw if sw is None else sw
        p = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        a = f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        mid = "m" + color.lstrip("#")
        if arrow:
            self.markers.add(color)
            a += f' marker-end="url(#{mid})"'
        if start_arrow:
            self.markers.add(color)
            a += f' marker-start="url(#{mid})"'
        self.items.append(a + "/>")
        if dot_start:
            self.circle(*pts[0], 0.45, color)

    def circle(self, x, y, r, fill, stroke=None, sw=0.22):
        a = f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        self.items.append(a + "/>")

    def poly(self, pts, fill="none", stroke=None, sw=0.22, dash=None):
        p = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        a = f'<polygon points="{p}" fill="{fill}" stroke-linejoin="round"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.items.append(a + "/>")

    def path(self, d, fill="none", stroke=None, sw=0.22):
        a = f'<path d="{d}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"'
        self.items.append(a + "/>")

    def rich(self, x, y, parts, pt, anchor="middle", within=None):
        """parts: [(text, color), ...]，同一行多色文字。"""
        pt = pt + SIZE_DELTA
        size = pt * PT
        spans = []
        total = ""
        for seg, color in parts:
            total += seg
            for cjk, part in runs(seg):
                fam = CJK_FAMILY if cjk else LAT_FAMILY
                wt = CJK_WEIGHT if cjk else 400
                if not cjk:
                    part = part.replace(" ", "\u00a0")
                spans.append(f'<tspan font-family="{fam}" font-weight="{wt}" fill="{color}">{escape(part)}</tspan>')
        self.items.append(
            f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size:.4f}" text-anchor="{anchor}" '
            f'style="font-variant-ligatures:none">{"".join(spans)}</text>')
        w = width(total, pt)
        if within:
            x0, x1 = within
            left = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
            if left < x0 - 0.01 or left + w > x1 + 0.01:
                self.warnings.append(f"overflow: {total!r} [{left:.1f},{left + w:.1f}] not in [{x0},{x1}]")
        return w

    # ---------- text ----------
    def text(self, x, y, s, pt, color, anchor="middle", within=None):
        pt = pt + SIZE_DELTA
        size = pt * PT
        spans = []
        for cjk, part in runs(s):
            if cjk:
                spans.append(f'<tspan font-family="{CJK_FAMILY}" font-weight="{CJK_WEIGHT}">{escape(part)}</tspan>')
            else:
                part = part.replace(" ", "\u00a0")
                spans.append(f'<tspan font-family="{LAT_FAMILY}" font-weight="400">{escape(part)}</tspan>')
        self.items.append(
            f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size:.4f}" text-anchor="{anchor}" '
            f'fill="{color}" style="font-variant-ligatures:none">{"".join(spans)}</text>')
        w = width(s, pt)
        if within:
            x0, x1 = within
            left = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
            if left < x0 - 0.01 or left + w > x1 + 0.01:
                self.warnings.append(f"overflow: {s!r} [{left:.1f},{left + w:.1f}] not in [{x0},{x1}]")
        return w

    def save(self, path):
        defs = []
        for col in sorted(self.markers):
            mid = "m" + col.lstrip("#")
            defs.append(
                f'<marker id="{mid}" markerUnits="userSpaceOnUse" markerWidth="{self.arrow}" markerHeight="{self.arrow}" '
                f'viewBox="0 0 6 6" refX="5.6" refY="3" orient="auto-start-reverse"><path d="M0,0.9 L6,3 L0,5.1 Z" fill="{col}"/></marker>')
        out = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}">',
            f"<title>{escape(self.title)}</title>",
            "<defs>" + "".join(defs) + "</defs>",
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#FFFFFF"/>',
        ] + self.items + ["</svg>"]
        path = os.path.join(os.environ.get("TU_OUT", "."), path)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out))
        for w in self.warnings:
            print("WARN", w)
