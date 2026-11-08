"""S2-09 正数、负数与边界测试的输入和结果（统一风格，160 x 100 mm）。
数值取自现用 figures/updated-20261106/S2-09.pdf：
正数 functional-2 seq 1 ROB 0:39，和 204；负数 functional-0 seq 4 ROB 0:12，和 −8；
正端点 functional-0 seq 5 ROB 0:43，和 131072；算术 RTL 定向 22 + 随机 10000 = 10022 项全部通过。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 100, "正数、负数与边界测试的输入和结果")
L, B, T, G, INK = C["line"], C["blue"], C["teal"], C["grey"], C["ink"]

HX0, HX1 = 37, 49            # 高 64 位
BX0, CW = 51, 6.0            # 低 8 字节
BX1 = BX0 + 8 * CW
VX0, VS, VX1 = 107, 143.5, 158

s.text(2, 4.8, "测试", S_LABEL, G, "start")
s.text((HX0 + HX1) / 2, 4.8, "高 64 位", S_LABEL, G)
s.text((HX0 + HX1) / 2, 8.6, "不参与", S_NOTE, G)
s.text((BX0 + BX1) / 2, 4.8, "低 64 位：八个有符号 INT8", S_LABEL, G)
for i in range(8):
    s.text(BX0 + CW * (i + 0.5), 8.6, str(7 - i), S_NOTE, G)
s.text((VX0 + VX1) / 2, 4.8, "vd 完整 128 位写回", S_LABEL, G)
s.text((VX0 + VS) / 2, 8.6, "[127:32]", S_NOTE, G)
s.text((VS + VX1) / 2, 8.6, "[31:0]", S_NOTE, G)
s.line([(2, 10.4), (158, 10.4)], C["rule"], sw=0.2, arrow=False)

tests = [("正数", "Σ i²，i = 1…8", "functional-2", "seq 1 · ROB 0:39",
          ["08", "07", "06", "05", "04", "03", "02", "01"], ["08", "07", "06", "05", "04", "03", "02", "01"], "204", "000000cc"),
         ("负数", "8 × (−1 × 1)", "functional-0", "seq 4 · ROB 0:12",
          ["ff"] * 8, ["01"] * 8, "−8", "fffffff8"),
         ("正端点", "8 × (−128)²", "functional-0", "seq 5 · ROB 0:43",
          ["80"] * 8, ["80"] * 8, "131072", "00020000")]


def check(x, y):
    s.path(f"M{x:.2f},{y:.2f} l1.0,1.1 l2.0,-2.6", stroke=T, sw=0.4)


for k, (name, formula, case, seq, v1, v2, total, low) in enumerate(tests):
    y0 = 12.5 + 26.5 * k
    s.rect(1, y0, 158, 24, fill=C["panel"], stroke=C["panel_s"], sw=0.18, rx=1.0)
    s.text(4, y0 + 6.0, name, S_PANEL, INK, "start")
    s.text(4, y0 + 10.6, formula, S_LABEL, INK, "start")
    s.text(4, y0 + 15.4, case, S_NOTE, G, "start")
    s.text(4, y0 + 19.0, seq, S_NOTE, G, "start")
    for r, (reg, vals) in enumerate([("vs1", v1), ("vs2", v2)]):
        yc = y0 + 8.0 + 8.0 * r
        s.text(34.5, yc + 1.1, reg, S_BODY, B, "end")
        s.rect(HX0, yc - 2.9, HX1 - HX0, 5.8, fill=C["white"], stroke=C["teal_s"], sw=0.18, dash="0.8 0.6")
        s.text((HX0 + HX1) / 2, yc + 1.0, "a5 × 8", S_NOTE, G)
        for i, v in enumerate(vals):
            s.rect(BX0 + CW * i, yc - 2.9, CW, 5.8, fill=C["white"], stroke=C["blue_s"], sw=0.2, rx=0)
            s.text(BX0 + CW * (i + 0.5), yc + 1.1, v, S_LABEL, INK)
    # 求和箭头
    ym = y0 + 12.0
    s.line([(BX1 + 0.3, y0 + 8.0), (BX1 + 2.6, y0 + 8.0), (BX1 + 2.6, y0 + 16.0), (BX1 + 0.3, y0 + 16.0)], C["faint"], arrow=False)
    s.line([(BX1 + 2.6, ym + 2.4), (VX0, ym + 2.4)], T)
    s.text(BX1 + 4.6, ym + 1.4, "Σ", S_LABEL, T)
    s.rich(VX0, y0 + 7.4, [("和 = ", INK), (total, T)], S_TITLE, "start")
    check(140.0, y0 + 6.0)
    s.text(VX1, y0 + 7.4, "期望 = 实际", S_LABEL, T, "end")
    s.rect(VX0, ym - 0.6, VS - VX0, 6.0, fill=C["white"], stroke=C["plain_s"], sw=0.2, rx=0)
    s.text((VX0 + VS) / 2, ym + 3.5, "全 0", S_LABEL, G)
    s.rect(VS, ym - 0.6, VX1 - VS, 6.0, fill=C["teal_f"], stroke=C["teal_s"], sw=0.24, rx=0)
    s.text((VS + VX1) / 2, ym + 3.5, low, S_LABEL, T)

s.line([(2, 92.5), (158, 92.5)], C["rule"], sw=0.2, arrow=False)
s.text(2, 97.4, "算术 RTL", S_TITLE, INK, "start")
s.rich(22, 97.4, [("定向 22 项 + 随机 10000 项 = ", INK), ("10022 项全部通过", T)], S_LABEL, "start")
s.text(158, 97.4, "历史组合 RTL 套件，2026-10-12", S_NOTE, G, "end")

s.save("S2-09.svg")
