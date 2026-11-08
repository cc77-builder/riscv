"""S3-09 八项点积受测组合的验证与评估范围（统一风格，160 x 96 mm）。
内容取自现用 figures/updated-20261106/S3-09.pdf；字体改为与其余图一致的宋体 + Times。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 96, "八项点积受测组合的验证与评估范围")
B, T, G, INK = C["blue"], C["teal"], C["grey"], C["ink"]

s.text(2, 5.6, "最终交付组合：两槽硬件 + 首段初始化 + C8", S_PANEL, INK, "start")


def done(x, y):
    s.circle(x, y, 1.45, T)


def todo(x, y):
    s.circle(x, y, 1.35, C["white"], stroke=G, sw=0.28)


def na(x, y):
    s.line([(x - 1.6, y), (x + 1.6, y)], G, sw=0.3, arrow=False)


done(83, 4.6); s.text(85.6, 5.6, "已有记录", S_LABEL, INK, "start")
todo(108, 4.6); s.text(110.6, 5.6, "待评估", S_LABEL, INK, "start")
na(130, 4.6); s.text(132.6, 5.6, "随硬件评估", S_LABEL, INK, "start")

COLX = [58, 79, 103, 124, 145]
s.line([(2, 9.5), (158, 9.5)], C["rule"], sw=0.22, arrow=False)
s.text((COLX[0] + COLX[1]) / 2, 14.0, "逻辑与执行", S_BODY, T)
s.line([(COLX[0] - 9, 15.6), (COLX[1] + 9, 15.6)], T, sw=0.3, arrow=False)
s.text((COLX[2] + COLX[4]) / 2, 14.0, "物理实现", S_BODY, G)
s.line([(COLX[2] - 9, 15.6), (COLX[4] + 9, 15.6)], C["plain_s"], sw=0.3, arrow=False)
s.text(2, 22.0, "评估对象", S_LABEL, G, "start")
for x, (a, b) in zip(COLX, [("功能", "正确性"), ("周期", "测量"), ("单元", "面积"), ("布局前", "STA"), ("功耗", "")]):
    if b:
        s.text(x, 20.2, a, S_LABEL, INK)
        s.text(x, 23.8, b, S_LABEL, INK)
    else:
        s.text(x, 22.0, a, S_LABEL, INK)
s.line([(2, 26.5), (158, 26.5)], C["rule"], sw=0.22, arrow=False)
s.rect(92.5, 26.5, 65.5, 27, fill=C["panel"], rx=0)

rows = [("局部 VDot FU", "算术与握手", "DDDDT"), ("VFEX4 父级", "含 FU 与 DIV", "DDDDT"),
        ("整核程序", "差分／微基准", "DDTTT"), ("固定 GEMV / C8", "完整调用", "DDNNN")]
for i, (a, b, marks) in enumerate(rows):
    y = 26.5 + 9 * i
    s.text(2, y + 4.0, a, S_BODY, INK, "start")
    s.text(2, y + 7.4, b, S_LABEL, G, "start")
    for x, m in zip(COLX, marks):
        {"D": done, "T": todo, "N": na}[m](x, y + 4.6)
    s.line([(2, y + 9), (158, y + 9)], C["rule"], sw=0.18, arrow=False)
s.line([(92.5, 26.5), (92.5, 62.5)], C["rule"], sw=0.18, arrow=False)

notes = [("周期单位", "FU 按握手拍计；整核与 C8 按 DUT 周期计"), ("功能验证", "全核 117 个用例共运行 124 次；C8 最终镜像与测试版一致"),
         ("时序结果", "4 ns／5 fF 约束下，14 类路径 setup 全部满足"), ("后续评估", "整核最高频率、布线后时序与功耗"),
         ("复现方式", "源码、镜像、输入和原始记录均已归档")]
for k, (key, val) in enumerate(notes):
    y = 68.0 + 6.0 * k
    s.text(2, y, key, S_LABEL, G, "start")
    s.text(22, y, val, S_LABEL, INK, "start")

s.save("S3-09.svg")
