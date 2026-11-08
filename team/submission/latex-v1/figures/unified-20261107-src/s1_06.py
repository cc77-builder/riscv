"""S1-06 vadd 输入、输出与提交事件时间线（统一风格，160 x 64 mm）。
周期取自现用 figures/updated-20261106/S1-06.pdf：正数 19625/19626/19631，负数 25460/25461/25466，
边界 33009/33010/33015；输出比输入晚 1 拍，ROB 提交再晚 5 拍。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 64, "vadd 输入、输出与提交事件时间线")
L, B, T, G, INK = C["line"], C["blue"], C["teal"], C["grey"], C["ink"]

X0, STEP = 34, 19.0          # 相对周期 0 的 x 与每拍宽度
def X(k):
    return X0 + STEP * k


def m_in(x, y):
    s.circle(x, y, 1.25, T)


def m_out(x, y):
    s.poly([(x, y - 1.55), (x + 1.55, y), (x, y + 1.55), (x - 1.55, y)], fill=B)


def m_commit(x, y):
    s.rect(x - 1.2, y - 1.2, 2.4, 2.4, fill=INK, rx=0.2)


# 图例
m_in(4.5, 4.6); s.text(7, 5.6, "执行输入", S_LABEL, INK, "start")
m_out(26, 4.6); s.text(28.5, 5.6, "结果输出", S_LABEL, INK, "start")
m_commit(47.5, 4.6); s.text(50, 5.6, "ROB 提交", S_LABEL, INK, "start")
s.text(157, 5.6, "坐标单位：cycle", S_NOTE, G, "end")

# 区间标注
s.line([(X(0) + 0.3, 12.5), (X(1) - 0.3, 12.5)], B, start_arrow=True)
s.text((X(0) + X(1)) / 2, 11.2, "+1", S_LABEL, B)
s.line([(X(1) + 0.3, 12.5), (X(6) - 0.3, 12.5)], INK, start_arrow=True)
s.text((X(1) + X(6)) / 2, 11.2, "+5 至 ROB 提交", S_LABEL, INK)

# 网格
for k in range(7):
    s.line([(X(k), 15.5), (X(k), 50.5)], C["rule"], sw=0.18, dash="0.8 0.8", arrow=False)

rows = [("正数", (19625, 19626, 19631)), ("负数", (25460, 25461, 25466)), ("边界", (33009, 33010, 33015))]
for i, (name, (a, b, c)) in enumerate(rows):
    y = 21.5 + 11.5 * i
    if i % 2 == 0:
        s.rect(2, y - 5.2, 156, 10.4, fill=C["blue_f"], rx=0.8)
    s.text(5, y + 1.1, name, S_TITLE, INK, "start")
    s.line([(X(0), y), (X(6), y)], C["blue_s"], sw=0.3, arrow=False)
    m_in(X(0), y); m_out(X(1), y); m_commit(X(6), y)
    for k, v in ((0, a), (1, b), (6, c)):
        s.text(X(k), y + 4.6, str(v), S_LABEL, INK)

for k in range(7):
    s.text(X(k), 55.6, "0" if k == 0 else f"+{k}", S_LABEL, G)
s.text((X(0) + X(6)) / 2, 61.0, "相对执行输入的周期", S_LABEL, G)

s.save("S1-06.svg")
