"""S2-05 连续请求在两槽中的逐拍流动（统一风格，160 x 64 mm）。
内容取自现用 figures/updated-20261106/S2-05.pdf：持续供给且 out.ready = 1，
cycle 12 同拍接收 #3、#2 由 P 迁入 R、#1 从 R 响应；发起间隔 1 拍，最早接收后 2 拍响应。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 64, "连续请求在两槽中的逐拍流动")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]

s.text(2, 5.0, "持续供给，out.ready = 1", S_LABEL, INK, "start")
s.text(158, 5.0, "P、R 两行为时钟沿前状态", S_NOTE, G, "end")

CX = {10: 49, 11: 82, 12: 115, 13: 147}
ROWS = {"接收": 17.5, "P 槽": 28.5, "R 槽": 39.5, "响应": 50.5}
TX = {1: ("teal", T), 2: ("blue", B), 3: ("orange", O), 4: ("panel", G)}
PW, PH = 15, 6.2

s.rect(CX[12] - 13, 7.0, 26, 48.5, fill=C["orange_f"], rx=1.0)
s.text(2, 11.2, "cycle", S_NOTE, G, "start")
for c, x in CX.items():
    s.text(x, 11.2, str(c), S_TITLE if c == 12 else S_BODY, O if c == 12 else INK)
s.line([(2, 12.8), (158, 12.8)], C["rule"], sw=0.2, arrow=False)
s.line([(2, 45.0), (158, 45.0)], C["rule"], sw=0.18, dash="0.8 0.8", arrow=False)
for name, y in ROWS.items():
    s.text(2, y + 1.1, name, S_BODY, INK, "start")

cells = {("接收", 10): 1, ("接收", 11): 2, ("接收", 12): 3, ("接收", 13): 4,
         ("P 槽", 11): 1, ("P 槽", 12): 2, ("P 槽", 13): 3,
         ("R 槽", 12): 1, ("R 槽", 13): 2, ("响应", 12): 1, ("响应", 13): 2}
for row, y in ROWS.items():
    for c, x in CX.items():
        if (row, c) not in cells:
            s.text(x, y + 1.1, "—", S_BODY, C["faint"])


def pill(x, y, n):
    kind, col = TX[n]
    s.rect(x - PW / 2, y - PH / 2, PW, PH, fill=C[kind + "_f"] if kind != "panel" else C["panel"],
           stroke=C[kind + "_s"], sw=0.24, rx=PH / 2)
    s.text(x, y + 1.15, f"#{n}", S_BODY, col)


# 流动箭头（先画线再画胶囊）
for n, c0 in [(1, 10), (2, 11), (3, 12)]:
    col = TX[n][1]
    s.line([(CX[c0] + PW / 2, ROWS["接收"] + 1.2), (CX[c0 + 1] - PW / 2 - 0.3, ROWS["P 槽"] - 1.4)], col)
    if c0 + 2 in CX:
        s.line([(CX[c0 + 1] + PW / 2, ROWS["P 槽"] + 1.2), (CX[c0 + 2] - PW / 2 - 0.3, ROWS["R 槽"] - 1.4)], col)
for n, c in [(1, 12), (2, 13)]:
    s.line([(CX[c], ROWS["R 槽"] + PH / 2), (CX[c], ROWS["响应"] - PH / 2 - 0.2)], TX[n][1])
for (row, c), n in cells.items():
    pill(CX[c], ROWS[row], n)

s.rich(2, 59.0, [("cycle 12 同拍完成：", O), ("接收 #3，#2 由 P 迁入 R，#1 从 R 响应", INK)], S_LABEL, "start")
s.rich(2, 63.0, [("发起间隔 1 拍；最早在接收后 2 拍响应", G)], S_LABEL, "start")

s.save("S2-05.svg")
