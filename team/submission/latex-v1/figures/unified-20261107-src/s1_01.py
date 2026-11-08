"""S1-01 开发环境与软硬件协同验证框架（统一风格，160 x 100 mm）。
内容取自现用 figures/tu/S1-01_development_environment.png。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 100, "开发环境与软硬件协同验证框架")
L, B, T, P, O, G, INK = C["line"], C["blue"], C["teal"], C["purple"], C["orange"], C["grey"], C["ink"]
DASH = "0.9 0.6"

# 外层：Windows 宿主 / WSL2
s.rect(0.5, 0.5, 159, 99, stroke=C["blue_s"], sw=0.28, rx=1.2)
s.text(3.5, 5.6, "Windows 宿主", S_PANEL, B, "start")
s.text(156.5, 5.6, "阶段一历史环境 • 2026-10-09", S_NOTE, G, "end")
s.rect(3, 8, 154, 89.5, stroke=C["teal_s"], sw=0.26, rx=1.0)
s.text(6, 13.2, "WSL2 / Ubuntu 22.04.5", S_PANEL, T, "start")
s.text(154, 13.2, "xs-env • 固定依赖与工具链 • Linux 原生文件系统", S_NOTE, G, "end")

COLS = [32, 80, 128]
BW = 42


def node(cx, y0, h, lines, kind, colors):
    s.box(cx - BW / 2, y0, BW, h, kind)
    n = len(lines)
    step = 3.7
    first = y0 + h / 2 - step * (n - 1) / 2 + 1.1
    for i, (txt, size) in enumerate(lines):
        s.text(cx, first + i * step, txt, size, colors[i], within=(cx - BW / 2, cx + BW / 2))


# 编译期
s.rect(6, 16, 148, 39.5, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(9, 21, "编译期", S_LABEL, G, "start")
src = [("香山工程", "Scala / Chisel • 16ae9dd", B), ("AM 程序与启动代码", "hello / vadd • nexus-am", B),
       ("NEMU 源码", "a48a11f", T)]
tools = [["JDK / Mill / firtool", "RTL → Verilator / C++"], ["RISC-V GCC / binutils"], ["宿主编译器"]]
arts = [("香山 EMU", "MinimalConfig", "blue", B), ("AM BIN", "共同 boot-flash", "blue", B),
        ("NEMU reference", "动态库", "teal", T)]
for cx, (t1, t2, col), tl, (a1, a2, ak, acol) in zip(COLS, src, tools, arts):
    node(cx, 22.5, 8.6, [(t1, S_TITLE), (t2, S_LABEL)], "plain", [col, G])
    s.line([(cx, 31.1), (cx, 34.3)], C["faint"], dash=DASH)
    node(cx, 34.3, 8.0, [(x, S_BODY) for x in tl], "plain", [INK, INK])
    s.line([(cx, 42.3), (cx, 45.5)], C["faint"], dash=DASH)
    node(cx, 45.5, 8.6, [(a1, S_TITLE), (a2, S_LABEL)], ak, [acol, G])

# 运行期
s.rect(6, 58.5, 148, 37, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
s.text(9, 63.5, "运行期", S_LABEL, G, "start")
RY = 66.5
s.line([(COLS[0], 54.1), (COLS[0], RY)], C["faint"], dash=DASH)
s.line([(COLS[2], 54.1), (COLS[2], RY)], C["faint"], dash=DASH)
# 同一镜像
JY = 62.5
s.line([(COLS[1], 54.1), (COLS[1], JY)], L, arrow=False)
s.line([(COLS[1], JY), (45, JY), (45, RY)], L)
s.line([(COLS[1], JY), (115, JY), (115, RY)], L)
s.circle(COLS[1], JY, 0.45, L)
s.text(COLS[1] + 1.5, JY - 1.2, "同一镜像", S_LABEL, INK, "start")

node(COLS[0], RY, 8.6, [("EMU / DUT", S_TITLE), ("单核 • VLEN128 • 128MB", S_LABEL)], "blue", [B, G])
node(COLS[2], RY, 8.6, [("NEMU reference", S_TITLE), ("独立架构模型", S_LABEL)], "teal", [T, G])
s.line([(COLS[0] + BW / 2, RY + 4.3), (COLS[2] - BW / 2, RY + 4.3)], P, dash=DASH)
s.text(COLS[1], RY + 3.0, "按提交推进", S_LABEL, P)

DY = 77.5
node(COLS[1], DY, 8.6, [("DiffTest", S_TITLE), ("架构状态比较", S_LABEL)], "purple", [P, G])
HY = DY + 4.3
s.line([(COLS[0], RY + 8.6), (COLS[0], HY), (COLS[1] - BW / 2, HY)], L)
s.text((COLS[0] + COLS[1] - BW / 2) / 2 + 2, HY - 1.2, "提交状态", S_LABEL, B)
s.line([(COLS[2], RY + 8.6), (COLS[2], HY), (COLS[1] + BW / 2, HY)], L)
s.text((COLS[2] + COLS[1] + BW / 2) / 2 - 2, HY - 1.2, "对应状态", S_LABEL, T)

AY = 90.0
s.line([(COLS[1], DY + 8.6), (COLS[1], AY)], L)
s.text(COLS[1] + 1.5, DY + 10.8, "比较结果", S_NOTE, G, "start")
s.rect(52, AY, 56, 5.6, fill=C["white"], stroke=C["plain_s"], sw=0.22)
s.rich(80, AY + 3.9, [("运行证据归档：", INK), ("日志 • 波形 • 退出状态 • SHA256", G)], S_LABEL, within=(52, 108))
# 串口 / FST
s.line([(COLS[0] - BW / 2, RY + 6.0), (8.5, RY + 6.0), (8.5, AY + 2.8), (52, AY + 2.8)], L)
s.text(30, AY + 1.6, "串口 / FST", S_LABEL, INK)

s.save("S1-01.svg")
