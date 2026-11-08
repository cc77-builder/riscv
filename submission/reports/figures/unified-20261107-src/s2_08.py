"""S2-08 共享资源切换、取消与时钟保持（统一风格，160 x 80 mm）。
内容取自现用 figures/updated-20261106/S2-08.pdf：
整数 DIV 11447/11448/11449/11459（接收至响应 10 拍），浮点 DIV 11504/11505/11506/11514（8 拍）；
取消清理后关钟，子时钟掩码 1 = VDot，2 = VIDiv，4 = VFDiv。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 80, "共享资源切换、取消与时钟保持")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]

# ---------- 上：排空 VDot 后接收 DIV ----------
s.text(2, 5.8, "排空 VDot 后接收 DIV", S_PANEL, INK, "start")
X0, STEP = 34, 9.4
def X(k):
    return X0 + STEP * k


def m_old(x, y):
    s.circle(x, y, 1.2, INK)


def m_drain(x, y):
    s.circle(x, y, 1.05, C["white"], stroke=INK, sw=0.3)


def m_acc(x, y):
    s.rect(x - 1.1, y - 1.1, 2.2, 2.2, fill=T, rx=0.2)


def m_resp(x, y):
    s.poly([(x, y - 1.45), (x + 1.45, y), (x, y + 1.45), (x - 1.45, y)], fill=B)


lx = 66
for f, lab in [(m_old, "旧 R 输出"), (m_drain, "VDot 排空"), (m_acc, "DIV 接收"), (m_resp, "DIV 响应")]:
    f(lx, 4.9)
    s.text(lx + 2.2, 5.9, lab, S_LABEL, INK, "start")
    lx += 23.5
for k in range(13):
    s.line([(X(k), 9.5), (X(k), 31.5)], C["rule"], sw=0.16, dash="0.8 0.8", arrow=False)
for i, (name, vals, resp, n) in enumerate([("整数 DIV", (11447, 11448, 11449, 11459), 12, 10),
                                           ("浮点 DIV", (11504, 11505, 11506, 11514), 10, 8)]):
    y = 15 + 10.5 * i
    s.text(2, y + 1.1, name, S_BODY, INK, "start")
    s.line([(X(0), y), (X(resp), y)], C["blue_s"], sw=0.3, arrow=False)
    s.text((X(2) + X(resp)) / 2, y - 1.6, f"接收至响应 {n} 拍", S_NOTE, B)
    m_old(X(0), y); m_drain(X(1), y); m_acc(X(2), y); m_resp(X(resp), y)
    for k, v in zip((0, 1, 2, resp), vals):
        s.text(X(k), y + 4.4, str(v), S_NOTE, INK)
for k in range(13):
    s.text(X(k), 35.0, "0" if k == 0 else f"+{k}", S_NOTE, G)
s.text(158, 35.0, "cycle", S_NOTE, G, "end")
s.line([(2, 38.2), (158, 38.2)], C["rule"], sw=0.2, arrow=False)

# ---------- 下：取消清理后关钟，再接收 VDot ----------
s.text(2, 44.2, "取消清理后关钟，再接收 VDot", S_PANEL, INK, "start")
s.text(158, 44.2, "格内为沿后开启的子时钟", S_NOTE, G, "end")
cols = [("入 DIV", "+0"), ("取消清理", "+1"), ("空闲", "+2～+4"), ("入 VDot", "+5"), ("响应", "+7")]
CX0, CW = 42, 25.5
for j, (t, c) in enumerate(cols):
    x = CX0 + CW * j
    s.text(x, 49.4, t, S_LABEL, INK)
    s.text(x, 52.6, c, S_NOTE, G)
rows = [("整数 DIV", [("VIDiv", "2", "blue"), ("VIDiv", "2", "blue"), ("全部关钟", "0", "off"),
                     ("VDot", "1", "teal"), ("VDot", "1", "teal")]),
        ("浮点 DIV", [("VFDiv", "4", "orange"), ("VFDiv", "4", "orange"), ("全部关钟", "0", "off"),
                     ("VDot", "1", "teal"), ("VDot", "1", "teal")])]
for i, (name, cells) in enumerate(rows):
    y = 58.8 + 8.8 * i
    if i == 0:
        s.rect(1, y - 4.0, 158, 8.0, fill=C["blue_f"], rx=0.8)
    s.text(3, y + 1.1, name, S_BODY, INK, "start")
    for j, (lab, mask, kind) in enumerate(cells):
        x = CX0 + CW * j
        if kind == "off":
            s.rect(x - 10, y - 3.0, 20, 6.0, fill=C["white"], stroke=C["faint"], sw=0.22, rx=3.0, dash="0.9 0.7")
            s.rich(x, y + 1.1, [("全部关钟 ", G), ("(0)", C["faint"])], S_LABEL)
        else:
            col = {"blue": B, "teal": T, "orange": O}[kind]
            s.rect(x - 10, y - 3.0, 20, 6.0, fill=C[kind + "_f"], stroke=C[kind + "_s"], sw=0.24, rx=3.0)
            s.rich(x, y + 1.1, [(lab + " ", col), (f"({mask})", G)], S_LABEL)
s.text(2, 77.8, "括号内为子时钟掩码：1 = VDot，2 = VIDiv，4 = VFDiv。取消清理后释放 DIV 的时钟保持，父级进入空闲后再接收 VDot。",
       S_NOTE, G, "start")

s.save("S2-08.svg")
