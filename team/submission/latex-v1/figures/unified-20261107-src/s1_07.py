"""S1-07 共同启动镜像与差分恢复（统一风格，160 x 86 mm）。
内容取自现用 figures/updated-20261106/S1-07.pdf（boot-flash.bin 12 B 三条指令及修正前后对照）。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 86, "共同启动镜像与差分恢复")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]

s.text(3, 5.8, "共同启动文件", S_PANEL, INK, "start")
s.text(28, 5.8, "boot-flash.bin · 12 B", S_BODY, B, "start")
s.text(157, 5.8, "两端显式加载同一文件", S_NOTE, G, "end")

# 表格
TX0, TX1 = 26, 157
cw = (TX1 - TX0) / 3
rows = [("偏移", ["0–3 B", "4–7 B", "8–11 B"], G, C["blue_f"]),
        ("机器码", ["0010029b", "01f29293", "00028067"], INK, C["white"]),
        ("指令", ["addiw t0, zero, 1", "slli t0, t0, 0x1f", "jr t0"], INK, C["white"]),
        ("效果", ["t0 = 1", "t0 = 0x80000000", "跳转至 0x80000000"], T, C["teal_f"])]
y = 9.5
RH = 6.2
for name, cells, col, fill in rows:
    s.rect(TX0, y, TX1 - TX0, RH, fill=fill, rx=0)
    s.text(3, y + 4.3, name, S_LABEL, G, "start")
    for i, c in enumerate(cells):
        size = S_TITLE if name == "机器码" else S_LABEL
        s.text(TX0 + cw * (i + 0.5), y + 4.3, c, size, col, within=(TX0 + cw * i, TX0 + cw * (i + 1)))
    y += RH
for i in range(1, 4):
    s.line([(TX0, 9.5 + RH * i), (TX1, 9.5 + RH * i)], C["panel_s"], sw=0.18, arrow=False)
for i in range(1, 3):
    s.line([(TX0 + cw * i, 9.5), (TX0 + cw * i, y)], C["panel_s"], sw=0.18, arrow=False)
s.rect(TX0, 9.5, TX1 - TX0, y - 9.5, stroke=C["blue_s"], sw=0.24, rx=0)

# 修正前 / 修正后
PY0, PY1 = 40, 85


def panel(x0, x1, kind, col, title, labels, result):
    s.rect(x0, PY0, x1 - x0, PY1 - PY0, fill=C[kind + "_f"], stroke=C[kind + "_s"], sw=0.22, rx=1.0)
    s.text(x0 + 3, PY0 + 5.8, title, S_TITLE, col, "start")
    cx = (x0 + x1) / 2
    bw = 28
    xs = [cx - 17.5, cx + 17.5]
    for xc, name, lab in zip(xs, ["RTL / DUT", "NEMU / REF"], labels):
        s.text(xc, PY0 + 12.0, lab, S_NOTE, G)
        s.box(xc - bw / 2, PY0 + 13.5, bw, 7.5, "plain")
        s.text(xc, PY0 + 18.4, name, S_TITLE, INK)
    s.line([(xs[0], PY0 + 21), (xs[0], PY0 + 24.5), (xs[1], PY0 + 24.5), (xs[1], PY0 + 21)], C["faint"], arrow=False)
    s.line([(cx, PY0 + 24.5), (cx, PY0 + 28)], C["faint"])
    s.rect(cx - 15, PY0 + 28, 30, 6.8, fill=C["white"], stroke=C[kind + "_s"], sw=0.26, rx=3.4)
    s.text(cx, PY0 + 32.6, "DiffTest 比较", S_TITLE, col)
    for i, txt in enumerate(result):
        s.text(cx, PY0 + 39.0 + 3.8 * i, txt, S_LABEL, col, within=(x0, x1))


panel(1, 78.5, "orange", O, "修正前：两端各用默认启动序列", ["默认启动序列", "默认启动序列"],
      ["首次差异：PC 0x10000004 · instrCnt = 2", "t0 不一致"])
panel(81.5, 159, "teal", T, "修正后：两端加载同一 12 B 文件", ["boot-flash.bin", "boot-flash.bin"],
      ["3 类 · 24 元素 · GOOD TRAP · exit 0", "hello 与 vadd 正常结束"])

s.save("S1-07.svg")
