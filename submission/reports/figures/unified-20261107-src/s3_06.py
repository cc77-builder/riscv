"""S3-06 C8 软件入口、结果布局与最终镜像等价核对（统一风格，160 x 100 mm）。
内容取自现用 figures/tu/S3-06_firstdot_C8_entry_and_image_equivalence.png。
调整：编译期开关改画成“xs_c8_gemv_8x32 默认走 vdot、FORCE_RVV = 1 时走 RVV；_rvv 入口始终走 RVV”，不再交叉。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 100, "C8 软件入口、结果布局与最终镜像等价核对")
L, B, T, P, G, INK = C["line"], C["blue"], C["teal"], C["purple"], C["grey"], C["ink"]

# ---------- A ----------
s.text(2, 5.4, "A 普通 C 调用", S_PANEL, B, "start")
s.text(158, 5.4, "固定 8×32 • VLEN128 • VS 启用", S_NOTE, G, "end")
# 输入
s.box(2, 9.5, 38, 29.5, "blue")
s.text(21, 14.8, "连续输入 A || x", S_TITLE, B)
s.rect(5, 17.5, 26, 6.2, fill=C["white"], stroke=C["blue_s"], sw=0.22, rx=0)
s.text(18, 21.6, "A[8][32]", S_BODY, B)
s.rect(31, 17.5, 6, 6.2, fill=C["blue_f"], stroke=C["blue_s"], sw=0.22, rx=0)
s.text(34, 21.6, "x", S_BODY, B)
s.text(18, 27.2, "256 B", S_NOTE, G)
s.text(34, 27.2, "32 B", S_NOTE, G)
s.text(21, 32.0, "signed INT8 • 行优先", S_LABEL, INK)
s.text(21, 36.2, "共 288 B", S_BODY, B)
s.line([(40, 24.25), (45, 24.25)], L)

# C8 显式入口
s.rect(45, 9.5, 69, 32.5, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(79.5, 14.4, "C8 显式入口 • 编译期选择", S_TITLE, INK)
s.box(48, 18, 31, 6.5, "blue")
s.text(63.5, 22.3, "xs_c8_gemv_8x32", S_LABEL, B, within=(48, 79))
s.box(48, 29.5, 31, 6.5, "purple")
s.text(63.5, 33.8, "xs_c8_gemv_8x32_rvv", S_LABEL, P, within=(48, 79))
s.box(95, 17.5, 16, 7.5, "teal")
s.text(103, 21.0, "vdot", S_BODY, T)
s.text(103, 24.0, "配置复用", S_NOTE, G)
s.box(95, 29, 16, 7.5, "purple")
s.text(103, 32.5, "RVV", S_BODY, P)
s.text(103, 35.5, "回退", S_NOTE, G)
s.line([(79, 21.25), (95, 21.25)], T)
s.text(87, 20.0, "缺省 / 0", S_NOTE, T)
s.line([(84, 21.25), (84, 30.8), (95, 30.8)], P)
s.circle(84, 21.25, 0.45, T)
s.text(85.3, 27.0, "= 1", S_NOTE, P, "start")
s.line([(79, 34.6), (95, 34.6)], P)
s.text(79.5, 40.0, "开关 XS_C8_GEMV_FORCE_RVV；更改后完整重编", S_NOTE, G)
# 汇入输出
s.line([(111, 21.25), (115.5, 21.25), (115.5, 32.75), (111, 32.75)], L, arrow=False)
s.line([(115.5, 24.25), (119, 24.25)], L)

# 输出
s.box(119, 9.5, 39, 29.5, "teal")
s.text(138.5, 14.8, "输出 8 × 16 B 槽", S_TITLE, T)
s.text(138.5, 18.2, "共 128 B", S_NOTE, G)
cw = 33 / 8
for i in range(8):
    s.rect(122 + cw * i, 20, cw, 5.2, fill=C["white"], stroke=C["teal_s"], sw=0.2, rx=0)
    s.text(122 + cw * (i + 0.5), 23.6, str(i), S_LABEL, T)
s.text(138.5, 30.6, "每槽：低 32 位结果", S_LABEL, INK)
s.text(138.5, 34.6, "高 96 位清零", S_LABEL, INK)

s.text(2, 46.4, "输入 / 输出：各自 16 B 对齐，互不重叠", S_NOTE, G, "start")
s.text(158, 46.4, "撤销 C8：恢复首段初始化版头文件与库，完整重编", S_NOTE, G, "end")
s.line([(2, 49.4), (158, 49.4)], C["rule"], sw=0.2, arrow=False)

# ---------- B ----------
s.text(2, 54.6, "B 封装前后的最终镜像一致性", S_PANEL, B, "start")
srcs = [(28, "原测试镜像", "已完成全核功能验证", "blue", B), (80, "原源码复制对照", "原源码重新构建", "plain", INK),
        (132, "SDK 接入版", "libxs_gemv_c8.a(gemv.o)", "teal", T)]
for cx, t1, t2, kind, col in srcs:
    s.box(cx - 22, 57, 44, 9, kind)
    s.text(cx, 60.9, t1, S_TITLE, col)
    s.text(cx, 64.4, t2, S_LABEL, G)
    s.line([(cx, 66), (cx, 69)], L, arrow=False)
s.line([(28, 69), (132, 69)], L, arrow=False)
s.circle(80, 69, 0.45, L)
s.line([(80, 69), (80, 72)], L)
s.rect(6, 72, 148, 13.5, fill=C["panel"], stroke=C["panel_s"], sw=0.22)
cells = [("完整 BIN", ["31,440 B • 全字节一致", "SHA256 相同"]), ("PT_LOAD 一致", ["地址 / 权限 / 对齐 / 内容"]),
         ("48 条调用记录", ["逐项一致"]), ("12 组输入", ["地址与内容一致"])]
cw = 148 / 4
for i, (t, lines) in enumerate(cells):
    cx = 6 + cw * (i + 0.5)
    s.text(cx, 76.2, t, S_TITLE, B)
    for k, ln in enumerate(lines):
        s.text(cx, 79.8 + 3.3 * k, ln, S_LABEL, INK, within=(6 + cw * i, 6 + cw * (i + 1)))
    if i:
        s.line([(6 + cw * i, 74), (6 + cw * i, 83.5)], C["panel_s"], sw=0.18, arrow=False)
s.line([(80, 85.5), (80, 88.5)], L)
s.box(42, 88.5, 76, 6.6, "teal")
s.text(80, 92.8, "原测试的功能结果同样适用", S_TITLE, T)
s.text(80, 98.8, "完整 ELF 差异仅在调试节", S_NOTE, G)

s.save("S3-06.svg")
