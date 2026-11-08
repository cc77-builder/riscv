"""S3-04 CSR 采样、退休与计时窗口的对应关系（统一风格，160 x 68 mm）。
数值取自现用 figures/tu/S3-04_CSR_timing_window_and_retirement_events.png：
t0 = 36679；I0/C0/C1/I1 入 ROB +28/+62/+133/+167、CSR 采样 +31/+65/+136/+170、退休 +34/+68/+139/+173；
F1–F6 = +17/+51/+85/+122/+156/+190；主体退休 +101/+105（5 条指令，含 1 条 vdot）；STOP +206；
instret 差 = 12（按退休 count 求和），cycle 差 = tick 差 = 71。
按原图加回外框；各类标点缩小约 30%。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 68, "CSR 采样、退休与计时窗口的对应关系")
L, B, T, O, P, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["purple"], C["grey"], C["ink"]
X0, X1 = 28.5, 152.5
def X(t):
    return X0 + (X1 - X0) * t / 206


Y_ROB, Y_CSR, Y_RET = 26, 36.5, 47
s.rect(0.4, 0.4, 159.2, 67.2, stroke=C["panel_s"], sw=0.24, rx=1.2)
s.text(3.5, 5.8, "全核事件", S_TITLE, INK, "start")
s.text(3.5, 9.8, "t0 = 36679", S_NOTE, G, "start")
for name, y in [("入 ROB", Y_ROB), ("CSR 采样", Y_CSR), ("退休", Y_RET)]:
    s.text(3.5, y + 1.1, name, S_BODY, INK, "start")
    s.line([(X0 - 3, y), (156, y)], C["rule"], sw=0.18, arrow=False)
for t, lab in [(0, "START"), (206, "STOP")]:
    s.text(X(t), 19.6, lab, S_NOTE, G)
    s.line([(X(t), 21), (X(t), 54)], C["rule"], sw=0.18, dash="0.8 0.8", arrow=False)
    s.poly([(X(t), Y_RET - 0.95), (X(t) + 0.95, Y_RET), (X(t), Y_RET + 0.95), (X(t) - 0.95, Y_RET)], fill=C["line"])
    s.text(X(t), Y_RET + 5.0, "0" if t == 0 else "+206", S_NOTE, INK)

events = [("I0 • instret_begin", 28, P), ("C0 • cycle_begin", 62, T), ("C1 • cycle_end", 133, T), ("I1 • instret_end", 167, P)]
for name, t, col in events:
    xr, xc, xt = X(t), X(t + 3), X(t + 6)
    s.line([(xt, Y_RET), (xc, Y_CSR), (xr, Y_ROB + 1.1)], col, sw=0.22)
    s.poly([(xr, Y_ROB - 0.7), (xr + 0.8, Y_ROB + 0.7), (xr - 0.8, Y_ROB + 0.7)], fill=col)
    s.circle(xc, Y_CSR, 0.65, col)
    s.rect(xt - 0.65, Y_RET - 0.65, 1.3, 1.3, fill=col, rx=0.15)
    s.line([(xc, 19.6 + 1.2), (xc, Y_CSR)], col, sw=0.18, dash="0.7 0.6", arrow=False)
    s.text(xc, 19.6, name, S_NOTE, col)
    s.text(xr - 1.6, Y_ROB + 4.4, f"+{t}", S_NOTE, col, "end")
    s.text(xc - 1.6, Y_CSR + 4.2, f"+{t + 3}", S_NOTE, col, "end")
    s.text(xt, Y_RET + 5.0, f"+{t + 6}", S_NOTE, col)

# 计时差
s.line([(X(31), 7.0), (X(170), 7.0)], P, sw=0.3, arrow=False)
s.circle(X(31), 7.0, 0.5, P)
s.circle(X(170), 7.0, 0.48, C["white"], stroke=P, sw=0.22)
s.text((X(31) + X(170)) / 2, 5.7, "instret 差 = 12（按退休 count 求和）", S_LABEL, P)
s.line([(X(65), 12.6), (X(136), 12.6)], T, sw=0.3, arrow=False)
for t in (65, 136):
    s.line([(X(t), 11.4), (X(t), 13.8)], T, sw=0.3, arrow=False)
s.text((X(65) + X(136)) / 2, 11.3, "cycle 差 = tick 差 = 71", S_LABEL, T)

# fence 与主体退休
for k, t in enumerate([17, 51, 85, 122, 156, 190]):
    s.rect(X(t) - 0.45, Y_RET - 1.1, 0.9, 2.2, fill=C["white"], stroke=O, sw=0.22, rx=0.15)
    s.text(X(t), Y_RET + 5.0, f"F{k + 1}", S_NOTE, O)
    s.text(X(t), Y_RET + 8.4, f"+{t}", S_NOTE, G)
s.rect(X(101) - 0.65, Y_RET - 0.65, 1.3, 1.3, fill=B, rx=0.15)
s.rect(X(105) - 0.6, Y_RET - 1.15, 1.2, 2.3, fill=C["white"], stroke=B, sw=0.22, rx=0.15)
s.line([(X(105) - 0.6, Y_RET), (X(105) + 0.6, Y_RET)], B, sw=0.2, arrow=False)
s.text(X(103), Y_RET - 4.0, "主体退休：5 条指令", S_NOTE, B)
s.text(X(103), Y_RET + 5.0, "+101 / +105", S_NOTE, B)
s.text(X(103), Y_RET + 8.4, "含 1 条 vdot", S_NOTE, G)

s.line([(X0 - 3, 59.5), (156.5, 59.5)], L)
s.text((X0 + X1) / 2, 65.4, "时间：相对 START 的全核 tick；F = fence rw,rw（退休事件）", S_LABEL, G)

s.save("S3-04.svg")
