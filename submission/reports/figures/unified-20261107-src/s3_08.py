"""S3-08 C8 接口、静态库与最终镜像的核对流程（统一风格，160 x 103 mm）。
内容取自现用 figures/tu/S3-08_C_call_link_and_result_audit.png。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 103, "C8 接口、静态库与最终镜像的核对流程")
L, B, T, O, P, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["purple"], C["grey"], C["ink"]
LC, RC = 48, 127.5

s.box(6, 1.5, 148, 8.5, "plain")
s.text(80, 5.4, "固定全部输入文件", S_TITLE, INK)
s.text(80, 8.7, "固定输入与封存证据 • 受测版本 EMU / NEMU / GNU 工具 • SHA256 核对", S_NOTE, G)
s.line([(80, 10), (80, 12.3)], L, arrow=False)
s.line([(LC, 12.3), (RC, 12.3)], L, arrow=False)
s.circle(80, 12.3, 0.45, L)
s.line([(LC, 12.3), (LC, 14.5)], L)
s.line([(RC, 12.3), (RC, 14.5)], L)

# 01
s.rect(4, 14.5, 88, 18.5, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(LC, 19.2, "01 完整对象与 SDK 链接", S_TITLE, B)
s.box(7, 21.5, 27, 9, "blue")
s.text(20.5, 25.4, "gemv.o", S_TITLE, B)
s.text(20.5, 28.9, "27,160 B • 16 个函数", S_NOTE, G, within=(7, 34))
s.line([(34, 26), (39, 26)], L)
s.box(39, 21.5, 50, 9, "blue")
s.text(64, 25.4, "libxs_gemv_c8.a(gemv.o)", S_BODY, B)
s.text(64, 28.9, "实际抽取 • GNU 依赖文件 + link map", S_NOTE, G, within=(39, 89))

# 三方镜像
row = [(17, 4, 30, "原测试镜像", "blue", B), (48, 33, 63, "原源码复制对照", "plain", INK), (79, 66, 92, "SDK 接入版", "teal", T)]
for cx, x0, x1, t, kind, col in row:
    s.box(x0, 37, x1 - x0, 7, kind)
    s.text(cx, 41.6, t, S_TITLE, col)
s.line([(64, 30.5), (64, 35), (79, 35), (79, 37)], L)
for cx, *_ in row:
    s.line([(cx, 44), (cx, 46.5)], L, arrow=False)
s.line([(17, 46.5), (79, 46.5)], L, arrow=False)
s.circle(LC, 46.5, 0.45, L)
s.line([(LC, 46.5), (LC, 49)], L)

# 02
s.box(4, 49, 88, 25.5, "blue")
s.text(LC, 53.6, "02 三方最终镜像核查", S_TITLE, B)
s.line([(7, 55.4), (89, 55.4)], C["blue_s"], sw=0.18, arrow=False)
for k, (key, val) in enumerate([("完整 BIN", "31,440 B • 全字节一致 • SHA256 相同"), ("PT_LOAD / 装载节", "地址 / 权限 / 对齐 / 内容一致"),
                                ("调用计划", "48 条调用记录 • 12 组输入一致")]):
    y = 59.4 + 4.1 * k
    s.text(7, y, key, S_LABEL, B, "start")
    s.text(35, y, val, S_LABEL, INK, "start")
s.line([(7, 69.4), (89, 69.4)], C["blue_s"], sw=0.18, arrow=False)
s.text(LC, 72.9, "入口 / ISA / BSS / 函数机器码：一致", S_NOTE, G)
s.line([(LC, 74.5), (LC, 77.5)], L)

s.box(4, 77.5, 88, 9.5, "purple")
s.text(LC, 81.5, "完整 ELF 仅调试节不同", S_TITLE, P)
s.text(LC, 85.2, "独立补充：strip-debug 后三方一致；原 ELF 保留", S_LABEL, INK)

# 03
s.rect(98, 14.5, 59, 73, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(RC, 19.2, "03 拒错与正控", S_TITLE, INK)
s.box(101, 22, 53, 19, "orange")
s.text(RC, 26.6, "6 项结构与输入负控", S_TITLE, O)
s.text(RC, 30.6, "代码 / 调用表 / 入口", S_LABEL, INK)
s.text(RC, 34.4, "BSS / ISA / 输入计划", S_LABEL, INK)
s.text(RC, 38.6, "检查器全部拒绝", S_BODY, O)
s.box(101, 45, 53, 10, "orange")
s.text(RC, 49.4, "1 项错误空库", S_TITLE, O)
s.text(RC, 53.2, "GNU 链接失败（符合预期）", S_LABEL, INK)
s.box(101, 59, 53, 16.5, "teal")
s.text(RC, 63.6, "1 项调试正控", S_TITLE, T)
s.text(RC, 67.6, "仅修改调试字节", S_LABEL, INK)
s.text(RC, 71.8, "等价检查通过", S_BODY, T)
s.text(RC, 82.0, "7 项负控 + 1 项正控均符合预期", S_NOTE, G)

# 汇入最终结论
s.line([(LC, 87), (LC, 89.6), (77.5, 89.6), (77.5, 92)], L)
s.line([(RC, 87.5), (RC, 89.6), (82.5, 89.6), (82.5, 92)], P, dash="0.9 0.6")
s.box(30, 92, 100, 9.5, "teal")
s.text(80, 96.0, "原测试的运行结果同样适用", S_TITLE, T)
s.text(80, 99.6, "功能 / DiffTest / bit100 拒错 / 恢复", S_LABEL, INK)

s.save("S3-08.svg")
