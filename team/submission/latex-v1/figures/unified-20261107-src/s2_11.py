"""S2-11 vdot 在昆明湖 V2 流水线中的位置（统一风格，160 x 66 mm）。
依据第二阶段 2.1、2.4.2、2.4.3 节：custom-0 精确译码为单个微操作，派发到 VFEX4，
与整数 DIV、浮点 DIV/SQRT 共享派发与写回，结果写入向量寄存器堆并由 ROB 按序提交。
蓝色表示新增或修改，白底表示复用原有机制。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 66, "vdot 在昆明湖 V2 流水线中的位置")
L, B, G, INK, F = C["line"], C["blue"], C["grey"], C["ink"], C["faint"]
DASH = "0.9 0.6"

# ---------- 七段流水 ----------
STAGES = [("取指", "复用", "plain"), ("译码", "+ vdot 识别", "blue"), ("重命名", "复用", "plain"),
          ("派发", "复用", "plain"), ("执行", "VFEX4", "blue"), ("写回", "共享写回", "plain"),
          ("提交", "ROB 按序", "plain")]
BW, STEP, X0, Y0, BH = 18.0, 23.0, 2.0, 6.0, 11.0
for i, (name, sub, kind) in enumerate(STAGES):
    x = X0 + STEP * i
    s.box(x, Y0, BW, BH, kind)
    s.text(x + BW / 2, Y0 + 4.6, name, S_TITLE, B if kind == "blue" else INK, within=(x, x + BW))
    s.text(x + BW / 2, Y0 + 8.8, sub, S_LABEL, G, within=(x, x + BW))
    if i:
        s.line([(x - STEP + BW, Y0 + BH / 2), (x, Y0 + BH / 2)], L)
s.text(2, 3.4, "昆明湖 V2 流水线", S_LABEL, G, "start")

# ---------- VFEX4 展开 ----------
EX = X0 + STEP * 4
PX0, PX1, PY0, PY1 = 40.0, 150.0, 25.0, 58.0
s.line([(EX, Y0 + BH), (PX0, PY0)], F, sw=0.18, dash=DASH, arrow=False)
s.line([(EX + BW, Y0 + BH), (PX1, PY0)], F, sw=0.18, dash=DASH, arrow=False)
s.rect(PX0, PY0, PX1 - PX0, PY1 - PY0, fill=C["panel"], stroke=C["panel_s"], sw=0.22, rx=1.0)
s.text(PX0 + 3, PY0 + 4.6, "VFEX4 执行单元", S_PANEL, B, "start")

DX0, DX1, DY0, DY1 = 44.0, 67.0, 33.5, 54.5
s.box(DX0, DY0, DX1 - DX0, DY1 - DY0, "blue")
s.text((DX0 + DX1) / 2, (DY0 + DY1) / 2 - 0.8, "派发选择", S_TITLE, B, within=(DX0, DX1))
s.text((DX0 + DX1) / 2, (DY0 + DY1) / 2 + 3.4, "按选中单元接收", S_LABEL, G, within=(DX0, DX1))

WX0, WX1 = 123.0, 146.0
s.box(WX0, DY0, WX1 - WX0, DY1 - DY0, "blue")
s.text((WX0 + WX1) / 2, (DY0 + DY1) / 2 - 0.8, "写回选择", S_TITLE, B, within=(WX0, WX1))
s.text((WX0 + WX1) / 2, (DY0 + DY1) / 2 + 3.4, "唯一有效来源", S_LABEL, G, within=(WX0, WX1))

FX0, FX1, FH = 75.0, 115.0, 5.6
FUS = [(36.0, "VDot 功能单元（新增）", "blue"), (44.0, "整数 DIV", "plain"), (52.0, "浮点 DIV / SQRT", "plain")]
for cy, name, kind in FUS:
    s.box(FX0, cy - FH / 2, FX1 - FX0, FH, kind, sw=0.3 if kind == "blue" else 0.24)
    s.text((FX0 + FX1) / 2, cy + 1.0, name, S_BODY, B if kind == "blue" else INK, within=(FX0, FX1))
    s.line([(DX1, cy), (FX0, cy)], L)
    s.line([(FX1, cy), (WX0, cy)], L)

# ---------- 图例 ----------
LY = 62.6
s.box(2, LY - 2.6, 5, 3.4, "blue")
s.text(8.6, LY, "新增或修改", S_LABEL, INK, "start")
s.box(30, LY - 2.6, 5, 3.4, "plain")
s.text(36.6, LY, "复用原有机制", S_LABEL, INK, "start")

s.save("S2-11.svg")
