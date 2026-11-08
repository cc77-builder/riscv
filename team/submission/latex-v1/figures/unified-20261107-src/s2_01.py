"""S2-01 八项点积指令字段与完整结果布局（统一风格，160 x 89 mm）。
内容取自现用 figures/tu/S2-01_vdot_instruction_and_result_layout.png。
调整：结果寄存器中“96 位全 0”改为中性底色，突出真正的结果 S；求和式重新排版。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 89, "八项点积指令字段与完整结果布局")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]
X0, X1 = 12, 158

# ---------- A ----------
s.text(2, 5.6, "A 32 位指令编码", S_PANEL, B, "start")
s.text(X1, 5.6, "custom-0 • 0x0b", S_LABEL, O, "end")
fields = [("funct6", "000000", "[31:26]", 24, "panel", INK), ("vm", "1", "[25]", 7, "panel", INK),
          ("vs2", "寄存器编号", "[24:20]", 22, "blue", B), ("vs1", "寄存器编号", "[19:15]", 22, "blue", B),
          ("funct3", "000", "[14:12]", 19, "panel", INK), ("vd", "寄存器编号", "[11:7]", 22, "teal", T),
          ("opcode", "0001011", "[6:0]", 30, "orange", O)]
x = X0
for name, val, bits, w, kind, col in fields:
    s.text(x + w / 2, 10.8, bits, S_NOTE, G)
    s.box(x, 12.2, w, 10, kind, sw=0.22)
    s.text(x + w / 2, 16.6, name, S_TITLE, col, within=(x, x + w))
    s.text(x + w / 2, 20.4, val, S_LABEL, INK if kind != "blue" and kind != "teal" else G, within=(x, x + w))
    x += w
s.text(X0, 26.8, "vdot.vv vd, vs2, vs1", S_BODY, B, "start")
s.text(X1, 26.8, "示例：vdot.vv v10, v8, v9 → 0x0284850b", S_LABEL, G, "end")
s.line([(2, 30), (158, 30)], C["rule"], sw=0.18, arrow=False)

# ---------- B ----------
s.text(2, 35.6, "B 源向量取位", S_PANEL, B, "start")
s.text(X1, 35.6, "VLEN128 • 两源各取低 8 字节", S_LABEL, G, "end")
HX1 = 80
cw = (X1 - HX1) / 8
s.text((X0 + HX1) / 2, 40.6, "[127:64]", S_NOTE, G)
for i in range(8):
    hi = 63 - 8 * i
    s.text(HX1 + cw * (i + 0.5), 40.6, f"[{hi}:{hi - 7}]", S_NOTE, G)
for r, (reg, sym) in enumerate([("vs1", "a"), ("vs2", "b")]):
    y = 42 + 8.3 * r
    s.text(6.5, y + 4.6, reg, S_BODY, B)
    s.rect(X0, y, HX1 - X0, 6.6, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=0)
    s.text((X0 + HX1) / 2, y + 4.4, "高 64 位不参与运算", S_LABEL, G)
    for i in range(8):
        s.rect(HX1 + cw * i, y, cw, 6.6, fill=C["blue_f"], stroke=C["blue_s"], sw=0.2, rx=0)
        s.text(HX1 + cw * (i + 0.5), y + 4.4, f"{sym}[{7 - i}]", S_BODY, B)
s.text((HX1 + X1) / 2, 61.6, "signed int8 • 同编号字节配对", S_LABEL, B)
s.line([(2, 64.2), (158, 64.2)], C["rule"], sw=0.18, arrow=False)

# ---------- C ----------
s.text(2, 69.8, "C 完整结果布局", S_PANEL, T, "start")
# 求和式：S = Σ_{i=0}^{7} a[i] × b[i]
FX, FY = 112, 69.8
s.text(FX, FY, "S =", S_BODY + 1, INK, "end")
s.text(FX + 1.2, FY + 0.6, "∑", 12, INK, "start")
s.text(FX + 4.6, FY - 2.7, "7", S_NOTE - 0.5, INK, "start")
s.text(FX + 4.6, FY + 1.6, "i = 0", S_NOTE - 0.5, INK, "start")
s.text(FX + 10.0, FY, "a[i] × b[i]", S_BODY + 1, INK, "start")

SX = 118
s.text((X0 + SX) / 2, 74.8, "[127:32]", S_NOTE, G)
s.text((SX + X1) / 2, 74.8, "[31:0]", S_NOTE, G)
s.text(6.5, 80.8, "vd", S_BODY, T)
s.rect(X0, 76.2, SX - X0, 7, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=0)
s.text((X0 + SX) / 2, 80.8, "96 位全 0", S_BODY, G)
s.rect(SX, 76.2, X1 - SX, 7, fill=C["teal_f"], stroke=C["teal_s"], sw=0.24, rx=0)
s.text((SX + X1) / 2, 80.8, "S 的 32 位补码", S_BODY, T)
s.text((X0 + X1) / 2, 87.8, "示例：S = −8 → 0x00000000_00000000_00000000_FFFFFFF8", S_LABEL, INK)

s.save("S2-01.svg")
