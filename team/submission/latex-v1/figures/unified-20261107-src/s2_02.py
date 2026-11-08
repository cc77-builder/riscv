"""S2-02 八项点积的乘积槽、归约网络和结果槽（统一风格，160 x 80 mm）。
内容取自现用 figures/tu/S2-02_core_datapath.png。
为保证 1:1 字号，各乘法器的“8+8”输入标注合并到列标题“signed 8 × 8”中，其余信息保留。"""
import math
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 80, "八项点积的乘积槽、归约网络和结果槽", arrow=1.2, sw=0.16)   # 本图连线密集，线和箭头更细
L, B, T, O, P, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["purple"], C["grey"], C["ink"]
DASH = "0.9 0.6"

AX0, AX1 = 1, 20.5
BUS = 23
MX0, MX1 = 25.5, 31
PX0, PX1 = 34, 52
TX0, TX1 = 55, 92
LV = [62, 73.5, 84.5]
SX0, SX1 = 95, 106.5
MUX0, MUX1 = 109.5, 113.5
RX0, RX1 = 116.5, 134.5
OX0, OX1 = 137, 157
PANEL_TOP = 11.5
YS = [16 + 5.2 * i for i in range(8)]
R_ADD = 2.1

# 列标题
for x, t, col in [((AX0 + AX1) / 2, "输入与提取", INK), ((MX0 + MX1) / 2 + 0.5, "并行乘法", INK),
                  ((PX0 + PX1) / 2, "P 乘积槽", B), ((TX0 + TX1) / 2, "足宽归约树（组合逻辑）", INK),
                  ((RX0 + RX1) / 2, "R 结果槽", T), (147.5, "完整向量输出", INK)]:
    s.text(x, 4.8, t, S_TITLE, col)
for x, t in [((MX0 + MX1) / 2 + 0.5, "signed 8 × 8"), ((PX0 + PX1) / 2, "8 × 16 bit"), (LV[0], "4 × 17 bit"),
             (LV[1], "2 × 18 bit"), (LV[2], "1 × 19 bit"), ((RX0 + RX1) / 2, "rPacket.res.data")]:
    s.text(x, 9.4, t, S_NOTE, G)

# 面板
s.rect(PX0, PANEL_TOP, PX1 - PX0, 79 - PANEL_TOP, fill=C["blue_f"], stroke=C["blue_s"], sw=0.22, rx=1.0)
s.rect(TX0, PANEL_TOP, TX1 - TX0, 57.5 - PANEL_TOP, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.rect(RX0, PANEL_TOP, RX1 - RX0, 79 - PANEL_TOP, fill=C["teal_f"], stroke=C["teal_s"], sw=0.22, rx=1.0)

# 输入与提取
s.box(AX0, 13, AX1 - AX0, 43.5, "panel")
AC = (AX0 + AX1) / 2
for y, t, size, col in [(18, "vs1[127:0]", S_BODY, INK), (21.3, "128 bit", S_NOTE, G), (26.2, "vs2[127:0]", S_BODY, INK),
                        (29.5, "128 bit", S_NOTE, G), (35.6, "各取低 64 位", S_NOTE, INK), (38.9, "分为 8 对字节", S_NOTE, INK),
                        (43.6, "a[i], b[i]", S_BODY, INK), (46.9, "signed INT8", S_NOTE, INK),
                        (51.2, "源 [127:64]", S_NOTE, G), (54.4, "不参与计算", S_NOTE, G)]:
    s.text(AC, y, t, size, col, within=(AX0, AX1))
s.line([(AX0 + 2, 32.2), (AX1 - 2, 32.2)], C["panel_s"], sw=0.18, arrow=False)

# 总线与乘法器
s.line([(AX1, 34.2), (BUS, 34.2)], L, arrow=False)
s.line([(BUS, YS[0]), (BUS, YS[-1])], L, arrow=False)
s.circle(BUS, 34.2, 0.45, L)
for i, y in enumerate(YS):
    s.line([(BUS, y), (MX0, y)], L)
    s.box(MX0, y - 1.9, MX1 - MX0, 3.8, "plain")
    s.text((MX0 + MX1) / 2, y + 1.0, "×", S_BODY, B)
    s.line([(MX1, y), (PX0 + 2, y)], L)
    s.box(PX0 + 2, y - 2.0, PX1 - PX0 - 4, 4.0, "white", sw=0.2)
    s.text((PX0 + PX1) / 2, y + 0.95, f"p{i} [15:0]", S_LABEL, B)


def to_circle(x0, y0, cx, cy, r=R_ADD):
    d = math.hypot(cx - x0, cy - y0)
    return (cx - (cx - x0) * r / d, cy - (cy - y0) * r / d)


def adder(cx, cy):
    s.circle(cx, cy, R_ADD, C["white"], stroke=B, sw=0.2)
    s.text(cx, cy + 1.2, "+", S_BODY + 0.5, B)


# 归约树
L1 = [(YS[2 * k] + YS[2 * k + 1]) / 2 for k in range(4)]
L2 = [(L1[0] + L1[1]) / 2, (L1[2] + L1[3]) / 2]
L3 = (L2[0] + L2[1]) / 2
for k, y in enumerate(YS):
    yt = L1[k // 2]
    s.line([(PX1 - 2, y), (TX0 + 1.5, y), to_circle(TX0 + 1.5, y, LV[0], yt)], L)
for k, y in enumerate(L1):
    s.line([(LV[0] + R_ADD, y), to_circle(LV[0] + R_ADD, y, LV[1], L2[k // 2])], L)
for y in L2:
    s.line([(LV[1] + R_ADD, y), to_circle(LV[1] + R_ADD, y, LV[2], L3)], L)
for y in L1:
    adder(LV[0], y)
for y in L2:
    adder(LV[1], y)
adder(LV[2], L3)
s.text(90.6, L3 + 3.7, "精确和 S", S_NOTE, T)
s.text((TX0 + TX1) / 2, 55.9, "每级保留符号与进位", S_NOTE, G)

# 符号扩展、异常选零
s.line([(LV[2] + R_ADD, L3), (SX0, L3)], L)
s.text((LV[2] + R_ADD + SX0) / 2, L3 - 1.0, "19", S_NOTE, G)
s.box(SX0, L3 - 4.5, SX1 - SX0, 9, "plain")
s.text((SX0 + SX1) / 2, L3 - 0.8, "符号扩展", S_LABEL, INK, within=(SX0, SX1))
s.text((SX0 + SX1) / 2, L3 + 2.8, "19 → 32", S_NOTE, G)
MY = 36.5
s.poly([(MUX0, MY - 6), (MUX1, MY - 4), (MUX1, MY + 4), (MUX0, MY + 6)], fill=C["orange_f"], stroke=C["orange_s"], sw=0.24)
s.line([(SX1, L3), (MUX0, L3)], L)
s.text(MUX0 + 1.2, L3 + 0.9, "0", S_NOTE, O, "start")
s.text(MUX0 + 1.2, MY + 4.0, "1", S_NOTE, O, "start")
s.box(97, 42.5, 9.5, 5, "orange")
s.text(101.75, 46.0, "32'b0", S_LABEL, O)
s.line([(106.5, 45), (108, 45), (108, MY + 3.1), (MUX0, MY + 3.1)], O)
s.text((MUX0 + MUX1) / 2, MY - 7.6, "异常选零", S_NOTE, O)

# R 结果槽
s.line([(MUX1, MY), (RX0 + 2, MY)], L)
s.box(RX0 + 2, MY - 5.5, RX1 - RX0 - 4, 11, "teal")
s.text((RX0 + RX1) / 2, MY - 0.9, "R.data", S_TITLE, T)
s.text((RX0 + RX1) / 2, MY + 3.2, "32 bit", S_LABEL, G)
RC = (RX0 + RX1) / 2
s.text(RC, 47.4, "只锁存 32 位", S_LABEL, T, within=(RX0, RX1))
s.text(RC, 50.9, "高 96 位", S_NOTE, G)
s.text(RC, 54.2, "在输出补零", S_NOTE, G)

# 输出拼接
OC = (OX0 + OX1) / 2
s.box(OX0 + 5, 14.5, 10, 5, "plain")
s.text(OC, 18.1, "96'b0", S_LABEL, INK)
s.line([(OC, 19.5), (OC, 26.8)], L)
s.text(OC + 1.2, 23.9, "96", S_NOTE, G, "start")
s.box(OX0, 26.8, OX1 - OX0, 18.4, "teal")
s.text(OC, 30.6, "输出拼接", S_LABEL, T)
s.rect(OX0 + 1.5, 32.2, OX1 - OX0 - 3, 5.2, fill=C["panel"], stroke=C["panel_s"], sw=0.18, rx=0.4)
s.text(OC, 35.7, "高 96 位 = 0", S_NOTE, G, within=(OX0 + 1.5, OX1 - 1.5))
s.rect(OX0 + 1.5, 38.2, OX1 - OX0 - 3, 5.2, fill=C["white"], stroke=C["teal_s"], sw=0.18, rx=0.4)
s.text(OC, 41.7, "R.data [31:0]", S_NOTE, T, within=(OX0 + 1.5, OX1 - 1.5))
s.line([(RX1 - 2, MY), (135.6, MY), (135.6, 40.8), (OX0 + 1.5, 40.8)], L)
s.line([(OX1, 36), (159.7, 36)], L)
for y, t, size, col in [(49.4, "128 位完整结果", S_LABEL, T), (52.8, "io.out.bits.res.data", S_NOTE, INK),
                        (56.2, "io.out.valid = liveR", S_NOTE, INK), (59.8, "异常：关闭目的写使能", S_NOTE, O)]:
    s.text(147.5, y, t, size, col, within=(OX0 - 1, 160))

# 事务身份通路
s.text(AX0, 62.4, "事务身份通路", S_LABEL, P, "start")
s.box(AX0, 64.5, 31, 14.5, "purple")
for i, (t, col) in enumerate([("ROB / pdest / vpu ctrl", INK), ("vecWen / v0Wen / exceptionVec", INK),
                              ("perfDebugInfo + 合法性检查", INK), ("与数据同步推进", G)]):
    s.text(AX0 + 15.5, 67.9 + 3.3 * i, t, S_NOTE, col, within=(AX0, AX0 + 31))
s.line([(AX0 + 31, 68.2), (PX0 + 2, 68.2)], P, dash=DASH)
s.box(PX0 + 2, 64, PX1 - PX0 - 4, 8.5, "purple")
s.text((PX0 + PX1) / 2, 67.6, "pCtrl", S_LABEL, P)
s.text((PX0 + PX1) / 2, 71.0, "pPerf", S_LABEL, P)
s.text((PX0 + PX1) / 2, 76.6, "pValid", S_LABEL, B)
# illegalInstr -> 选零
s.line([(47, 64), (47, 61.6), (111.5, 61.6), (111.5, MY + 5.1)], O, dash=DASH)
s.text(80, 60.4, "P 中已锁存的 illegalInstr 标记", S_NOTE, O)
# move
s.line([(PX1 - 2, 68.2), (RX0 + 2, 68.2)], P, dash=DASH)
s.text(85, 66.9, "move：旧 P 的整包身份进入 R", S_LABEL, P)
s.box(RX0 + 2, 64, RX1 - RX0 - 4, 8.5, "purple")
s.text(RC, 67.5, "rPacket.ctrl", S_NOTE, P, within=(RX0 + 2, RX1 - 2))
s.text(RC, 70.9, "perfDebugInfo", S_NOTE, P, within=(RX0 + 2, RX1 - 2))
s.text(RC, 76.6, "rValid", S_LABEL, T)
s.line([(RX1 - 2, 68.2), (OX0, 68.2)], P, dash=DASH)
s.box(OX0, 63.5, 159.5 - OX0, 15.5, "purple")
for i, t in enumerate(["ROB / pdest / 写使能", "exceptionVec / perf", "与 R.data 属于", "同一事务"]):
    s.text((OX0 + 159.5) / 2, 66.9 + 3.3 * i, t, S_NOTE, INK if i < 2 else P, within=(OX0, 159.5))

s.save("S2-02.svg")
