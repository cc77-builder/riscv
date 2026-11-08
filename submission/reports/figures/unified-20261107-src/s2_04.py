"""S2-04 从数学结果到整核执行的验证层次（统一风格，160 x 85 mm）。
内容取自现用 figures/tu/S2-04_validation_layers_and_dataflow.png。
调整：输入列统一用中性色，五层验证用蓝色，期望与检查列统一用青色，颜色只表示所在列的角色。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 85, "从数学结果到整核执行的验证层次")
L, B, T, G, INK = C["line"], C["blue"], C["teal"], C["grey"], C["ink"]
DASH = "0.9 0.6"

IX0, IX1 = 2, 40
VX0, VX1 = 54, 103
CX0, CX1 = 117, 153
for x, t, col in [((IX0 + IX1) / 2, "测试输入", INK), ((VX0 + VX1) / 2, "五层验证", B), ((CX0 + CX1) / 2, "期望与检查", T)]:
    s.text(x, 5.2, t, S_TITLE, col)

LAYER = [("01 独立数学模型", "signed int8 精确求和"), ("02 算术 RTL", "8 路乘法 • 归约"),
         ("03 VDot FU", "P/R 两槽 • ready/valid"), ("04 真实 VFEX4 父级", "DIV/SQRT • ClockGate"),
         ("05 全核 EMU / NEMU", "同一镜像 • 按提交对齐")]
CHECK = [("完整 128 位期望", "低 32 位补码 • 高 96 位零"), ("完整 128 位比较", "实际值 / 期望值"),
         ("128 位 / 协议检查", "反压 • 取消 • 复位 • 身份"), ("128 位 / 父级协议", "互斥 • 切换 • 空闲关钟"),
         ("DiffTest + 程序自检", "128 位 / CSR / 异常")]
EDGE = [None, "实际值", "结果 / 轨迹", "结果 / 轨迹", "架构状态"]
YS = [9 + 13.2 * i for i in range(5)]
H = 9.4
for i, y in enumerate(YS):
    s.box(VX0, y, VX1 - VX0, H, "blue")
    s.text((VX0 + VX1) / 2, y + 4.1, LAYER[i][0], S_TITLE, B, within=(VX0, VX1))
    s.text((VX0 + VX1) / 2, y + 7.6, LAYER[i][1], S_LABEL, INK, within=(VX0, VX1))
    s.box(CX0, y, CX1 - CX0, H, "teal")
    s.text((CX0 + CX1) / 2, y + 4.1, CHECK[i][0], S_TITLE, T, within=(CX0, CX1))
    s.text((CX0 + CX1) / 2, y + 7.6, CHECK[i][1], S_LABEL, INK, within=(CX0, CX1))
    s.line([(VX1, y + H / 2), (CX0, y + H / 2)], L)
    if EDGE[i]:
        s.text((VX1 + CX0) / 2, y + H / 2 - 1.2, EDGE[i], S_NOTE, G)
    # 汇入归档
    s.line([(CX1, y + H / 2), (156.5, y + H / 2)], C["faint"], dash=DASH, arrow=False)
s.line([((CX0 + CX1) / 2, YS[0] + H), ((CX0 + CX1) / 2, YS[1])], T)
s.text((CX0 + CX1) / 2 + 1.4, YS[0] + H + 2.6, "期望", S_NOTE, T, "start")


def inbox(y0, h, lines, kind):
    s.box(IX0, y0, IX1 - IX0, h, kind)
    n = len(lines)
    first = y0 + h / 2 - 3.6 * (n - 1) / 2 + 1.1
    for k, (t, size, col) in enumerate(lines):
        s.text((IX0 + IX1) / 2, first + 3.6 * k, t, size, col, within=(IX0, IX1))


def fan(src_y, targets, label_x=None):
    jx = 47
    s.line([(IX1, src_y), (jx, src_y)], L, arrow=False)
    s.circle(jx, src_y, 0.45, L)
    ys = [t + H / 2 for t in targets]
    s.line([(jx, min(ys)), (jx, max(ys))], L, arrow=False)
    for y in ys:
        s.line([(jx, y), (VX0, y)], L)


inbox(9, 22.6, [("算术测试输入", S_TITLE, INK), ("22 组定向 + 10000 组随机", S_LABEL, INK),
                ("输入记录 / manifest", S_LABEL, G)], "panel")
fan(9 + 11.3, [YS[0], YS[1]])
s.text(50.5, YS[0] + H / 2 - 1.2, "输入", S_NOTE, G)
s.text(50.5, YS[1] + H / 2 - 1.2, "输入", S_NOTE, G)
inbox(YS[2], YS[3] + H - YS[2], [("分层事务用例", S_TITLE, INK), ("数据 • 期望 • 控制条件", S_LABEL, INK),
                                ("FU / 父级分别驱动", S_LABEL, G)], "panel")
fan((YS[2] + YS[3] + H) / 2, [YS[2], YS[3]])
s.text(50.5, YS[2] + H / 2 - 1.2, "输入", S_NOTE, G)
s.text(50.5, YS[3] + H / 2 - 1.2, "输入", S_NOTE, G)
inbox(YS[4], H, [("AM 功能矩阵", S_TITLE, INK), ("117 独立用例 / 124 次执行", S_LABEL, INK)], "panel")
s.line([(IX1, YS[4] + H / 2), (VX0, YS[4] + H / 2)], L)
s.text((IX1 + VX0) / 2, YS[4] + H / 2 - 1.2, "镜像", S_NOTE, G)

# 分层证据归档
AY = 74.5
s.line([(156.5, YS[0] + H / 2), (156.5, AY + 4.5), (110, AY + 4.5)], C["faint"], dash=DASH)
s.rect(48, AY, 62, 9.4, fill=C["panel"], stroke=C["panel_s"], sw=0.22)
s.text(79, AY + 4.1, "分层证据归档", S_TITLE, INK)
s.text(79, AY + 7.6, "用例 ID • 原始日志 • SHA256", S_LABEL, G)

s.save("S2-04.svg")
