"""S2-10 两槽同拍推进与取消、复位处理 —— 160 x 105 mm，1:1 字号试画（v3：放宽间距）。
内容与现用 figures/tu/S2-10_PR_elastic_state_and_cancel_priority.png 相同。
v3：状态框与 B 区框体按缩小后的字号收小，状态之间、B 区各框之间、边标签与连线之间留出更多空白。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 105, "两槽同拍推进与取消、复位处理")
L, B, T, O, P, G = C["line"], C["blue"], C["teal"], C["orange"], C["purple"], C["grey"]
TOP_BOTTOM = 76.0

# ---------------- A 正常弹性转移 ----------------
s.rect(0.5, 0.5, 100, TOP_BOTTOM - 0.5, stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(4, 6.6, "A 正常弹性转移", S_PANEL, B, "start")
s.text(4, 11.0, "状态 = (P.valid, R.valid)", S_LABEL, G, "start")
s.text(97.5, 6.4, "无 flush / reset", S_NOTE, G, "end")
s.text(97.5, 10.0, "标注为同拍全部事件", S_NOTE, G, "end")

HW, HH = 10, 5.5        # 状态框半宽、半高


def state(cx, cy, code, sub, kind, color):
    s.box(cx - HW, cy - HH, 2 * HW, 2 * HH, kind)
    s.text(cx, cy - 0.5, code, 12, color)
    s.text(cx, cy + 3.9, sub, S_BODY, color, within=(cx - HW, cx + HW))


X00, X10, X11 = 16, 50, 84
Y10, YMID, Y01 = 22, 39.5, 57
state(X10, Y10, "10", "仅 P / 1 笔", "blue", B)
state(X00, YMID, "00", "空闲 / 0 笔", "panel", C["ink"])
state(X11, YMID, "11", "P + R / 2 笔", "purple", P)
state(X10, Y01, "01", "仅 R / 1 笔", "teal", T)

# 00 -> 10 入
s.line([(X00, YMID - HH), (X00, Y10), (X10 - HW, Y10)], L)
s.text((X00 + X10 - HW) / 2, Y10 - 1.5, "入", S_BODY, L)
# 10 -> 01 仅移 ; 01 -> 10 入+出
s.line([(X10 - 3, Y10 + HH), (X10 - 3, Y01 - HH)], L)
s.text(X10 - 4.8, YMID + 0.9, "仅移", S_BODY, L, "end")
s.line([(X10 + 3, Y01 - HH), (X10 + 3, Y10 + HH)], L)
s.text(X10 + 4.8, YMID + 0.9, "入+出", S_BODY, L, "start")
# 10 -> 11 入+移
s.line([(X10 + HW, Y10), (X11 - 3, Y10), (X11 - 3, YMID - HH)], L)
s.text(70.5, Y10 - 1.5, "入+移", S_BODY, L)
# 11 自环
s.line([(X11 + HW, YMID - 2.5), (97.5, YMID - 2.5), (97.5, 29.5), (X11 + 5, 29.5), (X11 + 5, YMID - HH)], L)
s.text(98.5, 15.4, "无事件：保持", S_NOTE, G, "end")
s.text(98.5, 19.2, "入+移+出：更新", S_NOTE, G, "end")
# 01 -> 11 仅入（R 阻塞）
Y_IN, Y_OUT = Y01 - 3.5, Y01 + 4.0
s.line([(X10 + HW, Y_IN), (X11 - 6, Y_IN), (X11 - 6, YMID + HH)], L)
s.text(X10 + HW + 1.0, (Y_IN + Y_OUT) / 2 + 1.1, "仅入（R 阻塞）", S_BODY, L, "start")
# 11 -> 01 移+出
s.line([(X11 + 4, YMID + HH), (X11 + 4, Y_OUT), (X10 + HW, Y_OUT)], L)
s.text(74, Y_OUT + 3.9, "移+出", S_BODY, L)
# 01 -> 00 仅出
s.line([(X10 - HW, Y01 + 2), (X00, Y01 + 2), (X00, YMID + HH)], L)
s.text((X00 + X10 - HW) / 2, Y01 + 0.5, "仅出", S_BODY, L)

s.text(19, 69.8, "入 = in.fire", S_LABEL, B)
s.text(50, 69.8, "移 = move", S_LABEL, B)
s.text(81, 69.8, "出 = out.fire", S_LABEL, B)
s.text(50, 73.6, "00 / 01 无事件时保持；满槽反压时停止接收", S_NOTE, G)

# ---------------- B 取消与复位 ----------------
s.rect(103, 0.5, 56.5, TOP_BOTTOM - 0.5, stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(106.5, 6.6, "B 取消与复位", S_PANEL, O, "start")
X0, X1, CX = 106.5, 156, 131.25

s.box(X0, 9.8, X1 - X0, 8.6, "orange")
s.text(CX, 13.4, "reset 最高", S_TITLE, O, within=(X0, X1))
s.text(CX, 16.8, "两 valid 清零；本拍无入 / 移 / 出", S_LABEL, C["ink"], within=(X0, X1))
s.line([(CX, 18.4), (CX, 23.8)], O)
s.text(CX + 1.6, 21.9, "未复位", S_NOTE, G, "start")

s.box(X0, 23.8, X1 - X0, 12.0, "orange")
s.text(CX, 27.7, "按各自 ROB 匹配 kill", S_TITLE, O, within=(X0, X1))
s.text(CX, 31.2, "得到 liveP / liveR", S_LABEL, C["ink"], within=(X0, X1))
s.text(CX, 34.3, "取消优先于同一事务的响应", S_NOTE, G, within=(X0, X1))
s.line([(CX, 35.8), (CX, 40.6)], O)

s.box(X0, 40.6, X1 - X0, 8.6, "teal")
s.text(CX, 44.2, "幸存事务可移动 / 输出", S_TITLE, T, within=(X0, X1))
s.text(CX, 47.6, "flush.valid = 1：禁止新入", S_LABEL, C["ink"], within=(X0, X1))

EY = 52.4
s.rect(X0, EY, X1 - X0, 22.2, fill=C["panel"], stroke=C["panel_s"], sw=0.2)
s.text(CX, EY + 4.0, "示例：旧状态 11，flush = 1，reset = 0", S_NOTE, C["ink"], within=(X0, X1))
s.line([(X0 + 2, EY + 5.5), (X1 - 2, EY + 5.5)], C["rule"], sw=0.18, arrow=False)
ex = [("仅 killP，R 阻塞", "01"), ("仅 killR，P 幸存", "01（移）"), ("killP + killR", "00")]
for i, (k, r) in enumerate(ex):
    y = EY + 8.8 + 3.5 * i
    s.text(X0 + 2.2, y, k, S_LABEL, C["ink"], "start")
    s.line([(136.5, y - 0.9), (141.5, y - 0.9)], G)
    s.text(X1 - 2.2, y, r, S_LABEL, B, "end")
s.text(CX, EY + 20.4, "仅 killR 时，out.ready = 0 也可移动", S_NOTE, O, within=(X0, X1))

# ---------------- C 同一边沿重叠 ----------------
CY0 = 79.0
s.rect(0.5, CY0, 159, 104.5 - CY0, stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(4, CY0 + 6.0, "C 三件事可在同一边沿重叠", S_PANEL, P, "start")
s.text(156, CY0 + 6.0, "move 读取旧 P；身份随数据移动", S_NOTE, G, "end")
BY = CY0 + 12.4
s.text(28, BY - 1.6, "边沿前", S_LABEL, G)
s.text(132, BY - 1.6, "边沿后", S_LABEL, G)
for x0, lab, kind, col in [(10, "P：B", "blue", B), (28, "R：A", "teal", T),
                           (114, "P：C", "blue", B), (132, "R：B", "teal", T)]:
    s.box(x0, BY, 18, 7.2, kind)
    s.text(x0 + 9, BY + 4.8, lab, S_TITLE + 0.5, col)
s.line([(46, BY + 3.6), (114, BY + 3.6)], P, sw=0.22)
s.text(80, BY + 2.0, "入 C + 移 B + 出 A", S_TITLE + 0.5, P)
s.text(80, 102.6, "A / B / C 表示事务；数据与 ROB / pdest / ctrl / perf 同步移动", S_NOTE, G)

s.save("S2-10.svg")
