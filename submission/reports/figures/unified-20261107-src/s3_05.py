"""S3-05 四类微基准周期与 RVV 归一化结果（统一风格，160 x 64 mm）。
数值取自现用 figures/updated-20261106/S3-05.pdf：
single × 1：VDot 71 / RVV 85.25 = 83.28%；chain × 256：1,857 / 5,440.5 = 34.13%；
batch × 128：221 / 678 = 32.60%；stream × 64：1,127.5 / 1,133 = 99.51%；n = 12。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 64, "四类微基准周期与 RVV 归一化结果")
B, T, G, INK = C["blue"], C["teal"], C["grey"], C["ink"]
POS_F, POS_S = "#D3EBE8", C["teal_s"]     # VDot 柱：浅青填充 + 细描边，与 S3-07 一致
X0, X1 = 36, 134          # 0% 与 100%
def X(p):
    return X0 + (X1 - X0) * p / 100


s.rect(2, 2.6, 7, 3.4, fill=POS_F, stroke=POS_S, sw=0.2, rx=0.4)
s.text(10.5, 5.4, "VDot 平均周期", S_LABEL, INK, "start")
s.rect(38, 2.6, 7, 3.4, fill=C["blue_f"], stroke=C["blue_s"], sw=0.2, rx=0.4)
s.text(46.5, 5.4, "同场景 RVV 平均周期 = 100%", S_LABEL, INK, "start")
s.text(158, 5.4, "VDot / RVV", S_LABEL, G, "end")

for p in (0, 25, 50, 75, 100):
    s.line([(X(p), 9), (X(p), 48)], C["rule"], sw=0.18, dash="0.8 0.8" if p not in (0, 100) else None, arrow=False)
    s.text(X(p), 52.0, f"{p}%", S_LABEL, G)
rows = [("单次点积", "single × 1", 71, "71", "85.25", 83.28),
        ("依赖链", "chain × 256", 1857, "1,857", "5,440.5", 34.13),
        ("独立批量", "batch × 128", 221, "221", "678", 32.60),
        ("访存流", "stream × 64", 1127.5, "1,127.5", "1,133", 99.51)]
for i, (name, sub, v, vs, rvv, pct) in enumerate(rows):
    y = 15.5 + 9.6 * i
    s.text(2, y + 0.2, name, S_TITLE, INK, "start")
    s.text(2, y + 3.8, sub, S_NOTE, G, "start")
    s.rect(X(0), y - 1.6, X(100) - X(0), 5.2, fill=C["blue_f"], stroke=C["blue_s"], sw=0.18, rx=0.3)
    s.rect(X(0), y - 1.6, X(pct) - X(0), 5.2, fill=POS_F, stroke=POS_S, sw=0.2, rx=0.3)
    s.text(X(0) + 1.5, y + 2.1, vs, S_LABEL, T, "start")
    s.text(X(100) - 0.5, y - 2.7, f"RVV {rvv}", S_NOTE, G, "end")
    s.text(158, y + 2.4, f"{pct:.2f}%", S_PANEL, T, "end")
s.text((X0 + X1) / 2, 57.0, "相对本场景 RVV 周期（越短越好）", S_LABEL, G)
s.text(2, 62.6, "每场景每种方法 n = 12；条内为正式窗口的平均 DUT 周期", S_NOTE, G, "start")

s.save("S3-05.svg")
