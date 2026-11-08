"""S3-09-SUP R5 组合验收与 P5 候选路线取舍（补充）（统一风格，160 x 98 mm）。
内容取自现用 figures/tu/S3-09_R5_acceptance_and_P5_selection_closeout.png。
调整：HOLD 改用蓝灰、NO-GO 用橙色；底部两项加“保留项”标题，说明其与上方流程的关系。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 98, "R5 组合验收与 P5 候选路线取舍（补充）")
L, B, T, O, P, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["purple"], C["grey"], C["ink"]
LX0, LX1, RX0, RX1 = 4, 92, 104, 157
LC, RC = (LX0 + LX1) / 2, (RX0 + RX1) / 2

s.box(6, 1.5, 148, 8.5, "plain")
s.text(80, 5.4, "固定身份核查", S_TITLE, INK)
s.text(80, 8.7, "源码 / EMU / NEMU / 镜像 / 输入 / 工具 • SHA256", S_NOTE, G)
s.line([(80, 10), (80, 12.3)], L, arrow=False)
s.line([(LC, 12.3), (RC, 12.3)], L, arrow=False)
s.circle(80, 12.3, 0.45, L)
s.line([(LC, 12.3), (LC, 14.5)], L)
s.line([(RC, 12.3), (RC, 14.5)], L)

# 全核组合证据
s.rect(LX0, 14.5, LX1 - LX0, 33, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(LC, 19.2, "全核组合证据", S_TITLE, B)
s.box(7, 21.5, 38, 11.5, "blue")
s.text(26, 26.0, "13 项原记录", S_TITLE, B)
s.text(26, 29.8, "复用 • 原始日志重解析", S_NOTE, G)
s.box(51, 21.5, 38, 11.5, "teal")
s.text(70, 25.3, "1 项新执行", S_TITLE, T)
s.text(70, 28.6, "o2-control-diagnostic", S_LABEL, INK)
s.text(70, 31.7, "同 boot 单调时钟补证", S_NOTE, G)
s.line([(26, 33), (26, 35), (70, 35), (70, 33)], L, arrow=False)
s.circle(LC, 35, 0.45, L)
s.line([(LC, 35), (LC, 37)], L)
s.box(14, 37, 68, 8, "blue")
s.text(LC, 40.6, "14 项全核组合", S_TITLE, B)
s.text(LC, 43.9, "功能 / DiffTest / O2 覆盖 / 拒错恢复", S_NOTE, G)

# 右列
s.box(RX0, 14.5, RX1 - RX0, 13, "blue")
s.text(RC, 18.8, "其他验收证据", S_TITLE, B)
s.text(RC, 22.4, "模型 / FU 与父级 / 软件调用", S_LABEL, INK)
s.text(RC, 25.6, "性能 / 成本 / 复现等", S_NOTE, G)
s.line([(RC, 27.5), (RC, 36)], L)
s.box(RX0, 36, RX1 - RX0, 10, "blue")
s.text(RC, 40.3, "R5 验收矩阵", S_PANEL, B)
s.text(RC, 44.0, "选定范围内工程验收完成", S_LABEL, INK)
s.line([(82, 41), (RX0, 41)], L)
s.line([(RC, 46), (RC, 52)], L)
s.box(RX0, 52, RX1 - RX0, 10, "purple")
s.text(RC, 56.3, "P5 选型收口", S_PANEL, P)
s.text(RC, 60.0, "只读复核 • 复用 R5 资格", S_LABEL, INK)
s.line([(RC, 62), (RC, 68)], L)
s.box(RX0, 68, RX1 - RX0, 12, "teal")
s.text(RC, 72.0, "最终稳定组合", S_LABEL, T)
s.text(RC, 77.4, "0f + firstdot V2 + 原 C8", S_PANEL + 1, T)

# 候选路线取舍
s.rect(LX0, 51, LX1 - LX0, 29, fill=C["white"], stroke=C["panel_s"], sw=0.22, rx=1.0)
s.text(LC, 55.6, "候选路线取舍（未采用）", S_TITLE, INK)
s.line([(7, 57.4), (89, 57.4)], C["rule"], sw=0.18, arrow=False)
for k, (name, st, why) in enumerate([("P1 / P1-R1 输入分离", "HOLD", "锚点门槛未过"), ("P3 FP32→QKV", "HOLD", "预算未闭合"),
                                     ("P4 一拍 / P4-R1", "NO-GO", "成本门槛未过"), ("C8 分段归约 R1", "NO-GO", "锚点 / 收益未过")]):
    y = 61.6 + 4.1 * k
    s.text(7, y, name, S_LABEL, INK, "start")
    s.text(58, y, st, S_LABEL, B if st == "HOLD" else O)
    s.text(68, y, why, S_NOTE, G, "start")
    if k < 3:
        s.line([(7, y + 1.5), (89, y + 1.5)], C["rule"], sw=0.15, arrow=False)
s.text(LC, 78.2, "分段归约原运行 HOLD 保留", S_NOTE, G)
s.line([(LX1, 57), (RX0, 57)], P, dash="0.9 0.6")
s.text((LX1 + RX0) / 2, 55.7, "取舍依据", S_NOTE, P)

# 保留项
s.box(LX0, 84, RX1 - LX0, 12.5, "orange")
s.text(LX0 + 3, 91.2, "保留项", S_TITLE, O, "start")
s.line([(LX0 + 17, 86.5), (LX0 + 17, 94)], C["orange_s"], sw=0.18, arrow=False)
s.text(60, 88.9, "旧 UTC 容量 FAIL 保留", S_BODY, O)
s.text(60, 92.9, "墙钟稳定性未证实", S_LABEL, G)
s.line([(RX0 - 6, 86.5), (RX0 - 6, 94)], C["orange_s"], sw=0.18, arrow=False)
s.text(RC - 3, 88.9, "1 ns 时序未收敛", S_BODY, O)
s.text(RC - 3, 92.9, "负 slack 保留", S_LABEL, G)

s.save("S3-09-SUP.svg")
