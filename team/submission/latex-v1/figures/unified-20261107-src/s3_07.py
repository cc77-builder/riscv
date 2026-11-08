"""S3-07 Nangate45 模块面积与主档 STA 裕量（统一风格，160 x 90 mm）。
数值取自现用 figures/updated-20261106/S3-07.pdf：
VFEX4 父级 284,614.946 µm²（含 FU），VDot FU 17,298.246 µm²，约 6.1%；1 ns / 5 fF，14 类中 10 类为负。
柱条用浅色填充加细描边：负裕量浅红（取自早先 S1-07 的浅红 #F6E4E7 / #A63D4F 一系），正值与 FU 面积浅青。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 90, "Nangate45 模块面积与主档 STA 裕量")
B, T, G, INK = C["blue"], C["teal"], C["grey"], C["ink"]
RED, RED_F, RED_S = "#A63D4F", "#F3D3D8", "#C98A94"     # 负值：文字 / 填充 / 描边
POS_F, POS_S = "#D3EBE8", C["teal_s"]                   # 正值与 FU 面积：填充 / 描边

# ---------- 面积 ----------
s.text(2, 5.0, "面积", S_PANEL, INK, "start")
s.text(158, 5.0, "Nangate45 Typical · 1.10 V · 25 °C", S_NOTE, G, "end")
AX0, AX1 = 30, 156
s.text(2, 11.2, "VFEX4 父级", S_BODY, INK, "start")
s.rect(AX0, 7.6, AX1 - AX0, 5.2, fill=C["blue_f"], stroke=C["blue_s"], sw=0.22, rx=0.5)
fu = (AX1 - AX0) * 17298.246 / 284614.946
s.rect(AX0, 7.6, fu, 5.2, fill=POS_F, stroke=POS_S, sw=0.22, rx=0.5)
s.text(AX1 - 1.5, 11.3, "284,614.946 µm²（含 FU）", S_LABEL, B, "end")
s.line([(AX0 + fu / 2, 12.8), (AX0 + fu / 2, 15.3), (AX0 + fu + 2.5, 15.3)], T, sw=0.22, arrow=False)
s.rich(AX0 + fu + 3.3, 16.3, [("VDot FU 17,298.246 µm²", T), ("，约占父级 6.1%", INK)], S_LABEL, "start")
s.line([(2, 19.0), (158, 19.0)], C["rule"], sw=0.2, arrow=False)

# ---------- STA ----------
s.text(2, 24.2, "主档 STA setup 裕量", S_PANEL, INK, "start")
s.rich(158, 24.2, [("1 ns / 5 fF　", G), ("14 类中 10 类为负", RED)], S_LABEL, "end")
XZ, K = 121.5, 30.6          # 0 ns 位置，每 ns 宽度
def X(v):
    return XZ + K * v


for v, lab in [(-2, "−2"), (-1, "−1"), (0, "0"), (0.5, "+0.5")]:
    s.line([(X(v), 27.5), (X(v), 82.0)], INK if v == 0 else C["rule"], sw=0.24 if v == 0 else 0.18,
           dash=None if v == 0 else "0.8 0.8", arrow=False)
    s.text(X(v), 85.3, lab, S_LABEL, G)
s.text(158, 85.3, "ns", S_NOTE, G, "end")
s.text(XZ - 30, 89.2, "setup 裕量 / ns（负值表示未满足 1 ns 约束）", S_LABEL, G)

groups = [("VDot FU", 29.4, [("i2o", 0.213), ("i2r", -0.269), ("r2o", 0.239), ("r2r", -0.240), ("ready", 0.596)]),
          ("VFEX4 父级", 50.2, [("gate_enable", -1.011), ("i2o", -2.314), ("i2r", -2.394), ("r2o", -2.337), ("r2r", -2.341),
                              ("ready", 0.602), ("vdot_i2r", -0.549), ("vdot_r2o", -1.927), ("vdot_r2r", -0.434)])]
for gname, gy, items in groups:
    s.text(2, gy, gname, S_TITLE, INK, "start")
    for k, (name, v) in enumerate(items):
        y = gy + 3.3 + 3.35 * k
        s.text(39, y + 0.9, name, S_LABEL, INK, "end")
        x0, x1 = sorted((X(0), X(v)))
        s.rect(x0, y - 1.15, x1 - x0, 2.3, fill=POS_F if v > 0 else RED_F, stroke=POS_S if v > 0 else RED_S, sw=0.18, rx=0.2)
        s.text(158, y + 0.9, f"{v:+.3f}".replace("-", "−"), S_LABEL, T if v > 0 else RED, "end")

s.save("S3-07.svg")
