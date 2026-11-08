"""S3-01 RTL 与独立参考模型的协同仿真（统一风格，160 x 84 mm）。
内容取自现用 figures/tu/S3-01_DiffTest_framework.png。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 84, "RTL 与独立参考模型的协同仿真")
L, B, T, P, G, INK = C["line"], C["blue"], C["teal"], C["purple"], C["grey"], C["ink"]
DASH = "0.9 0.6"
LC, MC, RC = 28, 80, 132
W = 50

# 顶部输入
s.box(LC - W / 2, 2, W, 9.5, "plain")
s.text(LC, 6.2, "RTL 源码", S_TITLE, INK)
s.text(LC, 9.6, "受测版本", S_LABEL, G)
s.box(MC - 19, 2, 38, 9.5, "blue")
s.text(MC, 6.2, "同一 AM 镜像", S_TITLE, B)
s.text(MC, 9.6, "共同 boot-flash", S_LABEL, G)
s.box(RC - W / 2, 2, W, 9.5, "plain")
s.text(RC, 6.2, "NEMU 源码 + 补丁", S_TITLE, INK)
s.text(RC, 9.6, "a48a11f • vdot 1.1.0", S_LABEL, G)

# DUT / REF
Y0, H = 22, 20
s.line([(LC, 11.5), (LC, Y0)], C["faint"], dash=DASH)
s.line([(RC, 11.5), (RC, Y0)], C["faint"], dash=DASH)
s.line([(MC, 11.5), (MC, 16.5)], L, arrow=False)
s.circle(MC, 16.5, 0.45, L)
s.line([(MC, 16.5), (LC + 15, 16.5), (LC + 15, Y0)], L)
s.line([(MC, 16.5), (RC - 15, 16.5), (RC - 15, Y0)], L)

s.box(LC - W / 2, Y0, W, H, "blue")
s.text(LC, Y0 + 4.6, "香山 DUT", S_PANEL, B)
s.text(LC, Y0 + 8.4, "EMU / Verilator", S_BODY, INK)
s.text(LC, Y0 + 11.7, "MinimalConfig", S_LABEL, G)
s.line([(LC - W / 2 + 3, Y0 + 13.6), (LC + W / 2 - 3, Y0 + 13.6)], C["blue_s"], sw=0.18, arrow=False)
s.text(LC, Y0 + 17.6, "架构提交", S_BODY, B)

s.box(RC - W / 2, Y0, W, H, "teal")
s.text(RC, Y0 + 4.6, "固定 NEMU reference", S_PANEL, T)
s.text(RC, Y0 + 8.4, "独立语义模型", S_BODY, INK)
s.text(RC, Y0 + 11.7, "固定平台适配", S_LABEL, G)
s.line([(RC - W / 2 + 3, Y0 + 13.6), (RC + W / 2 - 3, Y0 + 13.6)], C["teal_s"], sw=0.18, arrow=False)
s.text(RC, Y0 + 17.6, "参考动态库", S_BODY, T)

s.line([(LC + W / 2, Y0 + 5), (RC - W / 2, Y0 + 5)], P, dash=DASH)
s.text(MC, Y0 + 3.7, "按架构提交步进", S_LABEL, P)
s.rect(MC - 18, Y0 + 9.5, 36, 9.0, fill=C["panel"], stroke=C["panel_s"], sw=0.2)
s.text(MC, Y0 + 13.1, "冻结运行配置", S_LABEL, G)
s.text(MC, Y0 + 16.6, "单核 • VLEN128 • 128MB", S_LABEL, INK)

# DiffTest
DY0, DH = 50, 13
s.box(MC - 24, DY0, 48, DH, "purple")
s.text(MC, DY0 + 4.6, "DiffTest", S_PANEL, P)
s.text(MC, DY0 + 8.2, "完整 128 位向量", S_BODY, INK)
s.text(MC, DY0 + 11.6, "向量 CSR / 异常状态", S_BODY, INK)
s.line([(LC, Y0 + H), (LC, DY0 + 6.5), (MC - 24, DY0 + 6.5)], L)
s.text((LC + MC - 24) / 2 + 3, DY0 + 5.2, "DUT 提交状态", S_LABEL, B)
s.line([(RC, Y0 + H), (RC, DY0 + 6.5), (MC + 24, DY0 + 6.5)], L)
s.text((RC + MC + 24) / 2 - 3, DY0 + 5.2, "NEMU 对应状态", S_LABEL, T)

# 归档
AY = 70.5
s.line([(MC, DY0 + DH), (MC, AY)], L)
s.text(MC + 1.5, DY0 + DH + 2.8, "通过 / 差异", S_NOTE, G, "start")
s.rect(MC - 42, AY, 84, 12.5, fill=C["panel"], stroke=C["panel_s"], sw=0.22)
s.text(MC, AY + 4.4, "版本与证据归档", S_TITLE, INK)
s.text(MC, AY + 7.8, "源码 • 二进制 • 配置 • SHA256", S_LABEL, G)
s.text(MC, AY + 11.0, "原始日志 • 摘要 • 真实退出码", S_LABEL, G)

s.save("S3-01.svg")
