"""S2-06 背压期间的数据与目的身份保持（统一风格，160 x 64 mm）。
内容取自现用 figures/updated-20261106/S2-06.pdf：A = #1321，B = #1322；+2～+8 下游阻塞 7 拍；
+9 时 A 响应一次，B 由 P 迁入 R，FU in.ready = 1，父级 in.ready = 0。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 64, "背压期间的数据与目的身份保持")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]

s.rich(2, 5.0, [("A", T), (" = #1321　　", INK), ("B", B), (" = #1322", INK)], S_LABEL, "start")
s.text(158, 5.0, "时钟沿前采样", S_NOTE, G, "end")

X0, CW = 26, 13.2          # +0 列左边界、每拍宽
def cx(k):
    return X0 + CW * (k + 0.5)


s.rect(X0 + CW * 2, 7.5, CW * 7, 41.5, fill=C["orange_f"], rx=0.8)
for k in range(10):
    s.text(cx(k), 11.4, f"+{k}", S_LABEL, G)
    if 0 < k < 10:
        s.line([(X0 + CW * k, 13.2), (X0 + CW * k, 49)], C["rule"], sw=0.16, arrow=False)
ROWS = [("P 槽", 18.5), ("R 槽", 27.5), ("out.valid", 36.5), ("out.ready", 45.5)]
H = 6.4


def seg(k0, k1, y, label, kind, col):
    x0, x1 = X0 + CW * k0 + 0.7, X0 + CW * (k1 + 1) - 0.7
    fill = C["white"] if kind == "plain" else C.get(kind + "_f", C["panel"])
    stroke = C["plain_s"] if kind == "plain" else C[kind + "_s"]
    s.rect(x0, y - H / 2, x1 - x0, H, fill=fill, stroke=stroke, sw=0.22, rx=0.7)
    s.text((x0 + x1) / 2, y + 1.15, label, S_BODY, col)


for name, y in ROWS:
    s.text(2, y + 1.1, name, S_BODY, INK, "start")
seg(0, 0, 18.5, "—", "plain", C["faint"]); seg(1, 1, 18.5, "A", "teal", T); seg(2, 9, 18.5, "B", "blue", B)
seg(0, 1, 27.5, "—", "plain", C["faint"]); seg(2, 9, 27.5, "A", "teal", T)
seg(0, 1, 36.5, "0", "plain", INK); seg(2, 9, 36.5, "1", "panel", INK)
seg(0, 1, 45.5, "1", "panel", INK); seg(2, 8, 45.5, "0", "orange", O); seg(9, 9, 45.5, "1", "panel", INK)

s.line([(X0 + CW * 2 + 0.4, 53.5), (X0 + CW * 9 - 0.4, 53.5)], O, start_arrow=True)
s.text(X0 + CW * 5.5, 57.4, "下游阻塞 7 拍：P、R 中的数据与目的身份保持不变", S_LABEL, O)
s.rich(2, 62.6, [("+9：", T), ("A 响应一次，B 由 P 迁入 R；此时 FU in.ready = 1，父级 in.ready = 0", INK)], S_LABEL, "start")

s.save("S2-06.svg")
