"""S2-07 部分取消、全部取消与复位恢复（统一风格，160 x 62 mm）。
场景内容采用 figures/tu/S2-07_blue_candidate_v3.svg（2026-11-07 的风格统一候选稿）：
共同示例 out.ready = 0，重定向当拍无新接收；幸存 R 保持，幸存 P 在被取消 R 释放后推进。
配色按事务区分，与图 S2-06 一致：A 青、B 蓝；橙色只表示被取消或清空；P/R 槽名与场景标题用中性色。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 62, "部分取消、全部取消与复位恢复")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]

COLW = 37.5
X0 = 8.0
s.text(3.4, 23.2, "前", S_BODY, G)
s.text(3.4, 39.1, "后", S_BODY, G)
BW, BH = 11.5, 7.6


def slot(x, y, label, state):
    if state == "empty":
        s.rect(x - BW / 2, y - BH / 2, BW, BH, fill=C["white"], stroke=C["plain_s"], sw=0.2, dash="1.0 0.8")
        s.text(x, y + 1.1, "—", S_BODY, C["faint"])
        return
    kind, col = ("orange", O) if state == "kill" else {"A": ("teal", T), "B": ("blue", B)}[label]
    s.rect(x - BW / 2, y - BH / 2, BW, BH, fill=C[kind + "_f"], stroke=C[kind + "_s"], sw=0.22)
    s.text(x, y + 1.2, label, S_TITLE, col)
    if state == "kill":
        s.line([(x - 3.4, y), (x + 3.4, y)], O, sw=0.3, arrow=False)


scenes = [
    ("仅取消 P", INK, [("A", "kill"), ("B", "R")], [("", "empty"), ("B", "R")], "B 留在 R 等待就绪", B, "down"),
    ("仅取消 R", INK, [("A", "P"), ("B", "kill")], [("", "empty"), ("A", "R")], "A 从 P 推进至 R", T, "diag"),
    ("两槽同时取消", INK, [("A", "kill"), ("B", "kill")], [("", "empty"), ("", "empty")], "两槽均失效", O, "clear"),
    ("reset 与 redirect 同拍", INK, [("A", "P"), ("B", "R")], [("", "empty"), ("", "empty")], "reset 优先，清空两槽", O, "clear"),
]
for i, (title, tcol, before, after, note, ncol, kind) in enumerate(scenes):
    x0 = X0 + COLW * i
    s.rect(x0 + 0.8, 2.0, COLW - 1.6, 48.5, fill=C["panel"], stroke=C["panel_s"], sw=0.18, rx=1.0)
    c = x0 + COLW / 2
    xp, xr = c - 8.5, c + 8.5
    s.text(c, 7.4, title, S_TITLE, tcol, within=(x0 + 0.8, x0 + COLW - 0.8))
    s.text(xp, 13.6, "P", S_LABEL, G)
    s.text(xr, 13.6, "R", S_LABEL, G)
    if kind == "down":
        s.line([(xr, 22.1 + BH / 2), (xr, 38.0 - BH / 2 - 0.2)], B)
    elif kind == "diag":
        s.line([(xp + 2, 22.1 + BH / 2), (xr - 2, 38.0 - BH / 2 - 0.2)], T)
    else:
        for x in (xp, xr):
            s.line([(x, 22.1 + BH / 2), (x, 38.0 - BH / 2 - 0.2)], O)
        s.text(c, 31.2, "清空", S_LABEL, O)
    for x, (lab, st) in zip((xp, xr), before):
        slot(x, 22.1, lab, st)
    for x, (lab, st) in zip((xp, xr), after):
        slot(x, 38.0, lab, st)
    s.text(c, 47.4, note, S_LABEL, ncol, within=(x0 + 0.8, x0 + COLW - 0.8))

s.text(2, 55.4, "四个独立场景；前 / 后分别为同一时钟边沿之前 / 之后。", S_NOTE, G, "start")
s.text(2, 59.6, "示例 out.ready = 0；重定向当拍无新接收。删除线：取消；虚线框：无效槽。", S_NOTE, G, "start")

s.save("S2-07.svg")
