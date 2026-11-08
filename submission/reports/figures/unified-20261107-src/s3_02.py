"""S3-02 参考模型的译码、状态检查与完整写回（统一风格，160 x 80 mm）。
内容取自现用 figures/tu/S3-02_NEMU_vdot_decode_and_execute.png；判定菱形收小，整体更紧凑。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 81, "参考模型的译码、状态检查与完整写回")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]
MC = 80

s.box(MC - 17, 1.5, 34, 7, "plain")
s.text(MC, 6.1, "32 位指令字", S_TITLE, INK)
s.line([(MC, 8.5), (MC, 12)], L)

# 判定 1
D1, HW, HH = 19.5, 27, 7.5
s.poly([(MC, D1 - HH), (MC + HW, D1), (MC, D1 + HH), (MC - HW, D1)], fill=C["blue_f"], stroke=C["blue_s"], sw=0.24)
s.text(MC, D1 - 0.4, "custom-0", S_BODY, B)
s.text(MC, D1 + 3.2, "精确匹配？", S_BODY, B)
s.line([(MC - HW, D1), (38, D1)], L)
s.text((MC - HW + 38) / 2, D1 - 1.3, "否", S_LABEL, G)
s.box(4, D1 - 5.5, 34, 11, "plain")
s.text(21, D1 - 1.0, "继续其他译码", S_TITLE, INK)
s.text(21, D1 + 3.0, "未匹配则默认非法", S_LABEL, G)
s.line([(MC, D1 + HH), (MC, 33.5)], L)
s.text(MC + 1.5, D1 + HH + 3.0, "是", S_LABEL, G, "start")

# 判定 2
D2, HW2, HH2 = 44, 33, 10.5
s.poly([(MC, D2 - HH2), (MC + HW2, D2), (MC, D2 + HH2), (MC - HW2, D2)], fill=C["blue_f"], stroke=C["blue_s"], sw=0.24)
s.text(MC, D2 - 3.4, "向量状态合法？", S_TITLE, B)
s.text(MC, D2 + 0.6, "VS 启用 • 合法 vtype", S_LABEL, INK)
s.text(MC, D2 + 4.0, "vl=8 • vstart=0", S_LABEL, INK)
s.box(4, D2 - 8, 34, 16, "plain")
s.text(21, D2 - 3.4, "合法 vtype", S_TITLE, INK)
s.text(21, D2 + 0.4, "vill=0 • 保留位=0", S_LABEL, G)
s.text(21, D2 + 3.8, "e8 / m1", S_LABEL, INK)
s.text(21, D2 + 7.0, "vta / vma 任意", S_LABEL, G)
s.line([(38, D2), (MC - HW2, D2)], C["faint"], dash="0.8 0.6", arrow=False)
s.line([(MC + HW2, D2), (120, D2)], O)
s.text((MC + HW2 + 120) / 2, D2 - 1.3, "否", S_LABEL, O)
s.box(120, D2 - 8, 37, 16, "orange")
s.text(138.5, D2 - 3.0, "非法指令异常", S_TITLE, O)
s.text(138.5, D2 + 1.1, "cause=2；不写 vd", S_LABEL, INK)
s.text(138.5, D2 + 4.8, "xTVAL 按固定平台规则", S_LABEL, G)

s.line([(MC, D2 + HH2), (MC, 59), (26, 59), (26, 62)], L)
s.text(MC + 1.5, D2 + HH2 + 2.8, "是", S_LABEL, G, "start")

# 执行与写回
BY, BH = 62, 17.5
s.box(4, BY, 44, BH, "blue")
s.text(26, BY + 4.6, "先快照两源低 64 位", S_TITLE, B)
s.text(26, BY + 8.6, "vs1 → a；vs2 → b", S_BODY, INK)
s.text(26, BY + 12.8, "允许与 vd 别名（含 v0）", S_LABEL, G)
s.line([(48, BY + BH / 2), (56, BY + BH / 2)], L)
s.box(56, BY, 46, BH, "teal")
s.text(79, BY + 4.6, "signed int8 点积", S_TITLE, T)
s.text(79, BY + 8.6, "S = 0；i = 0…7", S_BODY, INK)
s.text(79, BY + 12.8, "S += int8(a[i]) × int8(b[i])", S_BODY, INK)
s.line([(102, BY + BH / 2), (110, BY + BH / 2)], L)
s.box(110, BY, 47, BH, "teal")
s.text(133.5, BY + 4.6, "完整 128 位写回 vd", S_TITLE, T)
s.text(124, BY + 7.6, "[127:32]", S_NOTE, G)
s.text(149, BY + 7.6, "[31:0]", S_NOTE, G)
s.rect(113, BY + 8.6, 22, 4.6, fill=C["white"], stroke=C["teal_s"], sw=0.2, rx=0)
s.text(124, BY + 11.9, "0", S_LABEL, T)
s.rect(135, BY + 8.6, 19, 4.6, fill=C["teal_f"], stroke=C["teal_s"], sw=0.2, rx=0)
s.text(144.5, BY + 11.9, "S[31:0]", S_LABEL, T)
s.text(133.5, BY + 16.2, "成功后 VS 置脏", S_NOTE, G)

s.save("S3-02.svg")
