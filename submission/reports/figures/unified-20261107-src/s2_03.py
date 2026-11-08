"""S2-03 VFEX4 中的派发、资源互斥与共享写回 —— 160 x 80 mm，1:1 字号试画（v3：放宽间距）。
内容与现用 figures/tu/S2-03_VFEX4_simplified.png 相同；右上 ready 线按 stage2.tex
“输出ready向各FU广播”改为来自下游的 out.ready，不再悬空。
v3：框体按缩小后的字号收窄、降高，省出的空间用于框与框、组与控制框之间的间距。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 80, "VFEX4 中的派发、资源互斥与共享写回")
L, P, O, T = C["line"], C["purple"], C["orange"], C["teal"]
DASH = "0.9 0.6"

# 外框
FX0, FX1, FY0, FY1 = 16, 145, 1.5, 78.5
s.rect(FX0, FY0, FX1 - FX0, FY1 - FY0, stroke=C["blue_s"], sw=0.3, rx=1.0)
s.text(19.5, 6.4, "VFEX4 / ExeUnit", S_PANEL, C["blue"], "start")

# 几何
ROWS = [(14.5, "VDot", "P / R 两槽", "blue"), (31.5, "VIDiv", "整数除法", "white"),
        (48.5, "VFDivSqrt", "浮点 DIV / SQRT", "white")]
FU_H, CG_H, OFF = 11.5, 5.4, 2.7           # FU 高、ClockGate 高、时钟/数据相对行中心偏移
DX0, DX1 = 20, 43                           # 派发
TRUNK = 48
GX0, GX1 = 53, 110.5                        # FU 组
CGX0, CGX1 = 60, 73.5                       # ClockGate
FUX0, FUX1 = 80.5, 105.5                    # FU
BEND = 115.5
WX0, WX1 = 121, 141                         # 共享写回
DATA_MID = ROWS[1][0] + OFF                 # 派发出口 = 第二行数据线
WB_C = ROWS[1][0]

# 上游请求 / ready
DY0, DY1 = DATA_MID - 8.5, DATA_MID + 8.5
s.line([(0.3, DATA_MID - 3), (DX0, DATA_MID - 3)], L)
s.text(8, DATA_MID - 4.6, "上游请求", S_BODY, C["ink"], within=(0, FX0))
s.line([(DX0, DATA_MID + 3.5), (0.4, DATA_MID + 3.5)], P, dash=DASH)
s.text(8, DATA_MID + 1.9, "ready", S_LABEL, P, within=(0, FX0))

# 派发与互斥
s.box(DX0, DY0, DX1 - DX0, DY1 - DY0, "blue")
s.text((DX0 + DX1) / 2, DATA_MID - 1.0, "派发与互斥", S_TITLE + 0.5, C["blue"], within=(DX0, DX1))
s.text((DX0 + DX1) / 2, DATA_MID + 4.0, "按选中 FU 接收", S_BODY, C["grey"], within=(DX0, DX1))

# FU 组
GY0 = ROWS[0][0] - OFF - CG_H / 2 - 4.6
GY1 = ROWS[-1][0] + FU_H / 2 + 2.6
s.rect(GX0, GY0, GX1 - GX0, GY1 - GY0, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.line([(DX1, DATA_MID), (TRUNK, DATA_MID)], L, arrow=False)
s.line([(TRUNK, ROWS[0][0] + OFF), (TRUNK, ROWS[-1][0] + OFF)], L, arrow=False)
s.circle(TRUNK, DATA_MID, 0.45, L)
CGC = (CGX0 + CGX1) / 2
FUC = (FUX0 + FUX1) / 2
for c, name, sub, kind in ROWS:
    ck = c - OFF
    s.box(CGX0, ck - CG_H / 2, CGX1 - CGX0, CG_H, "teal")
    s.text(CGC, ck + 0.85, "ClockGate", S_LABEL, T, within=(CGX0, CGX1))
    s.line([(GX0 + 1.0, ck), (CGX0, ck)], T)
    s.text(GX0 + 3.2, ck - 1.0, "clk", S_NOTE, T)
    s.line([(CGC, ck - CG_H / 2 - 3.6), (CGC, ck - CG_H / 2)], O, sw=0.18)
    s.text(CGC + 1.2, ck - CG_H / 2 - 1.3, "en", S_NOTE, O, "start")
    s.line([(CGX1, ck), (FUX0, ck)], T)
    s.box(FUX0, c - FU_H / 2, FUX1 - FUX0, FU_H, kind)
    s.text(FUC, c - 0.6, name, S_TITLE + 0.5, C["blue"], within=(FUX0, FUX1))
    s.text(FUC, c + 3.9, sub, S_BODY, C["grey"], within=(FUX0, FUX1))
    s.line([(TRUNK, c + OFF), (FUX0, c + OFF)], L)

# 共享写回
WY0, WY1 = WB_C - 9.5, WB_C + 9.5
s.line([(FUX1, ROWS[0][0]), (BEND, ROWS[0][0]), (BEND, WB_C - 5), (WX0, WB_C - 5)], L)
s.line([(FUX1, WB_C), (WX0, WB_C)], L)
s.line([(FUX1, ROWS[2][0]), (BEND, ROWS[2][0]), (BEND, WB_C + 5), (WX0, WB_C + 5)], L)
s.box(WX0, WY0, WX1 - WX0, WY1 - WY0, "teal")
s.text((WX0 + WX1) / 2, WB_C - 1.0, "共享写回", S_TITLE + 0.5, T, within=(WX0, WX1))
s.text((WX0 + WX1) / 2, WB_C + 4.0, "单一有效来源", S_BODY, C["grey"], within=(WX0, WX1))
s.line([(WX1, WB_C), (159.7, WB_C)], L)
s.text(152.5, WB_C - 1.8, "写回", S_BODY, C["ink"], within=(FX1, 160))

# 下游 out.ready 广播
s.line([(159.7, 7.2), (GX1 + 0.2, 7.2)], P, dash=DASH)
s.text(135, 5.6, "out.ready 广播至各 FU", S_LABEL, P)

# 占用与控制
KY0 = GY1 + 7.0
KY1 = KY0 + 12.4
s.box(GX0, KY0, GX1 - GX0, KY1 - KY0, "purple")
KC = (GX0 + GX1) / 2
s.text(KC, KY0 + 4.2, "占用与控制", S_TITLE + 0.5, P, within=(GX0, GX1))
s.text(KC, KY0 + 7.8, "P / R 占用 • DIV 占用与 ROB 身份", S_BODY - 0.5, C["ink"], within=(GX0, GX1))
s.text(KC, KY0 + 10.8, "父级未门控时钟；DIV 按 ROB 匹配取消", S_NOTE, C["grey"], within=(GX0, GX1))
s.line([(66, GY1), (66, KY0)], P, dash=DASH)
s.text(67.4, (GY1 + KY0) / 2 + 0.9, "状态 / ready", S_NOTE, P, "start")
s.line([(97, KY0), (97, GY1)], O, dash=DASH)
s.text(98.4, (GY1 + KY0) / 2 + 0.9, "取消 / en", S_NOTE, O, "start")
OCC_X = (DX0 + DX1) / 2
s.line([(GX0, KY0 + 4.5), (OCC_X, KY0 + 4.5), (OCC_X, DY1)], P, dash=DASH)
s.text((GX0 + OCC_X) / 2, KY0 + 3.2, "占用约束", S_LABEL, P)
s.line([(0.4, KY0 + 9.5), (GX0, KY0 + 9.5)], O, dash=DASH)
s.text(24, KY0 + 8.2, "flush / reset", S_LABEL, O)

s.save("S2-03.svg")
