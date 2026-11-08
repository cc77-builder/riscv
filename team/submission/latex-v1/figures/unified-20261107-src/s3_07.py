"""S3-07 Nangate45 模块面积与 4 ns STA 裕量（原统一风格，160 x 90 mm）。
数值读取本工程 evidence/nangate45-4ns-20261108/RESULT.json；来源为已完成的 4 ns 重新综合及 4 ns / 5 fF STA。
保留原字体、字号、画布、版式、线宽和配色；正负值沿用原青/红语义，坐标范围随新数值调整。"""
from pathlib import Path
import json

DATA = json.loads((Path(__file__).resolve().parents[2] / "evidence/nangate45-4ns-20261108/RESULT.json").read_text(encoding="utf-8"))
FU, PARENT = DATA["fu"], DATA["parent"]
assert DATA["status"] == "MAPPING_AND_SETUP_PASS"

from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 90, "Nangate45 模块面积与 4 ns STA 裕量")
B, T, G, INK = C["blue"], C["teal"], C["grey"], C["ink"]
RED, RED_F, RED_S = "#A63D4F", "#F3D3D8", "#C98A94"     # 负值：文字 / 填充 / 描边
POS_F, POS_S = "#D3EBE8", C["teal_s"]                   # 正值与 FU 面积：填充 / 描边

# ---------- 面积 ----------
s.text(2, 5.0, "面积", S_PANEL, INK, "start")
s.text(158, 5.0, "Nangate45 Typical · 1.10 V · 25 °C", S_NOTE, G, "end")
AX0, AX1 = 30, 156
s.text(2, 11.2, "VFEX4 父级", S_BODY, INK, "start")
s.rect(AX0, 7.6, AX1 - AX0, 5.2, fill=C["blue_f"], stroke=C["blue_s"], sw=0.22, rx=0.5)
fu = (AX1 - AX0) * FU["area_um2"] / PARENT["area_um2"]
s.rect(AX0, 7.6, fu, 5.2, fill=POS_F, stroke=POS_S, sw=0.22, rx=0.5)
s.text(AX1 - 1.5, 11.3, f'{PARENT["area_um2"]:,.3f} µm²（含 FU）', S_LABEL, B, "end")
s.line([(AX0 + fu / 2, 12.8), (AX0 + fu / 2, 15.3), (AX0 + fu + 2.5, 15.3)], T, sw=0.22, arrow=False)
s.rich(AX0 + fu + 3.3, 16.3, [(f'VDot FU {FU["area_um2"]:,.3f} µm²', T), (f'，约占父级 {100 * FU["area_um2"] / PARENT["area_um2"]:.1f}%', INK)], S_LABEL, "start")
s.line([(2, 19.0), (158, 19.0)], C["rule"], sw=0.2, arrow=False)

# ---------- STA ----------
s.text(2, 24.2, "各类路径的 setup 裕量", S_PANEL, INK, "start")
s.rich(158, 24.2, [("4 ns / 5 fF　", G), ("14 类全部为正", T)], S_LABEL, "end")
XZ, K = 44.0, 24.5          # 0 ns 位置，每 ns 宽度
def X(v):
    return XZ + K * v


for v, lab in [(0, "0"), (1, "+1"), (2, "+2"), (3, "+3"), (4, "+4")]:
    s.line([(X(v), 27.5), (X(v), 82.0)], INK if v == 0 else C["rule"], sw=0.24 if v == 0 else 0.18,
           dash=None if v == 0 else "0.8 0.8", arrow=False)
    s.text(X(v), 85.3, lab, S_LABEL, G)
s.text(158, 85.3, "ns", S_NOTE, G, "end")
s.text(91.5, 89.2, "setup 裕量 / ns（正值表示满足 4 ns 约束，越大越宽松）", S_LABEL, G)

groups = [("VDot FU", 29.4, [(name, FU["paths"][name]["slack_ns"]) for name in ("i2o", "i2r", "r2o", "r2r", "ready")]),
          ("VFEX4 父级", 50.2, [(name, PARENT["paths"][name]["slack_ns"]) for name in ("gate_enable", "i2o", "i2r", "r2o", "r2r", "ready", "vdot_i2r", "vdot_r2o", "vdot_r2r")])]
assert sum(len(items) for _, _, items in groups) == 14
assert all(0 < v < 4 for _, _, items in groups for _, v in items)
for gname, gy, items in groups:
    s.text(2, gy, gname, S_TITLE, INK, "start")
    for k, (name, v) in enumerate(items):
        y = gy + 3.3 + 3.35 * k
        s.text(39, y + 0.9, name, S_LABEL, INK, "end")
        x0, x1 = sorted((X(0), X(v)))
        s.rect(x0, y - 1.15, x1 - x0, 2.3, fill=POS_F if v > 0 else RED_F, stroke=POS_S if v > 0 else RED_S, sw=0.18, rx=0.2)
        s.text(158, y + 0.9, f"{v:+.3f}".replace("-", "−"), S_LABEL, T if v > 0 else RED, "end")

s.save("S3-07.svg")
