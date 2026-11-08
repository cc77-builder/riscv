"""S1-02 环境部署与验证执行流程（统一风格，160 x 109 mm）。
内容取自现用 figures/tu/S1-02_environment_setup_and_validation_flow.png。"""
from tukit import SVG, C, S_PANEL, S_TITLE, S_BODY, S_LABEL, S_NOTE

s = SVG(160, 109, "环境部署与验证执行流程")
L, B, T, O, G, INK = C["line"], C["blue"], C["teal"], C["orange"], C["grey"], C["ink"]
DASH = "0.9 0.6"
LX0, LX1 = 3, 92            # 左列
LC = (LX0 + LX1) / 2
RX0, RX1 = 107, 157         # 右列（定位与修正）
RC = (RX0 + RX1) / 2


def stage(y0, title, steps):
    s.rect(LX0, y0, LX1 - LX0, 22, fill=C["panel"], stroke=C["panel_s"], sw=0.2, rx=1.0)
    s.text(LC, y0 + 5.4, title, S_PANEL, B)
    w, gap = 25.0, 4.5
    x = LX0 + (LX1 - LX0 - 3 * w - 2 * gap) / 2
    for i, (t1, t2) in enumerate(steps):
        s.box(x, y0 + 8.5, w, 10.5, "blue")
        s.text(x + w / 2, y0 + 12.9, t1, S_TITLE, B, within=(x, x + w))
        s.text(x + w / 2, y0 + 16.8, t2, S_LABEL, G, within=(x, x + w))
        if i < 2:
            s.line([(x + w, y0 + 13.75), (x + w + gap, y0 + 13.75)], L)
        x += w + gap


def fix(y0, h, title, lines):
    s.box(RX0, y0, RX1 - RX0, h, "orange")
    s.text(RC, y0 + 4.6, title, S_TITLE, O, within=(RX0, RX1))
    for i, (txt, col) in enumerate(lines):
        s.text(RC, y0 + 8.6 + 3.9 * i, txt, S_LABEL, col, within=(RX0, RX1))


# 01 环境准备
stage(3, "01 环境准备", [("资源配置", "WSL2 • 原生目录"), ("仓库锁定", "提交 • 递归依赖"), ("工具检查", "版本 • 路径")])
fix(9, 12, "配置与依赖定位", [("资源 / 路径 / 固定版本", INK)])
s.line([(LX1, 16.5), (RX0, 16.5)], O, dash=DASH)
s.text((LX1 + RX0) / 2, 15.2, "检查未通过", S_NOTE, O)
s.line([(RC, 9), (RC, 6.2), (LX1, 6.2)], O, dash=DASH)
s.text((LX1 + RX0) / 2, 4.9, "修正后复查", S_NOTE, O)

s.line([(LC, 25), (LC, 31)], L)
s.text(LC + 1.6, 28.9, "通过", S_LABEL, INK, "start")

# 02 按序构建
stage(31, "02 按序构建", [("NEMU reference", "参考动态库"), ("香山 EMU", "MinimalConfig"), ("hello / vadd", "BIN + 共同 flash")])
fix(37, 12, "构建日志定位", [("依赖 / 工具链 / 资源配置", INK)])
s.line([(LX1, 44.5), (RX0, 44.5)], O, dash=DASH)
s.text((LX1 + RX0) / 2, 43.2, "构建失败", S_NOTE, O)
s.line([(RC, 37), (RC, 34.2), (LX1, 34.2)], O, dash=DASH)
s.text((LX1 + RX0) / 2, 32.9, "修正后重建", S_NOTE, O)

s.line([(LC, 53), (LC, 59)], L)
s.text(LC + 1.6, 56.9, "成功", S_LABEL, INK, "start")

# 03 DiffTest 运行
s.box(LX0, 59, LX1 - LX0, 11.5, "blue")
s.text(LC, 63.6, "03 DiffTest 运行", S_PANEL, B)
s.text(LC, 67.9, "同一 BIN / flash • 固定 reference • RAM 128 MB", S_LABEL, INK, within=(LX0, LX1))
s.line([(LC, 70.5), (LC, 74.5)], L)

# 判定菱形
DC, HW, HH = 83.5, 38, 9
s.poly([(LC, DC - HH), (LC + HW, DC), (LC, DC + HH), (LC - HW, DC)], fill=C["blue_f"], stroke=C["blue_s"], sw=0.24)
s.text(LC, DC - 2.4, "验证通过？", S_TITLE, B)
s.text(LC, DC + 1.4, "DiffTest 启用 • 3 类 vadd PASS", S_LABEL, INK)
s.text(LC, DC + 4.8, "GOOD TRAP • 真实 exit=0", S_LABEL, INK)

fix(76.5, 14, "运行与差分定位", [("核对 flash / RAM / reference", INK), ("历史修复：统一 12 B flash", G)])
s.line([(LC + HW, DC), (RX0, DC)], O, dash=DASH)
s.text((LC + HW + RX0) / 2, DC - 1.3, "未通过", S_NOTE, O)
s.line([(RC, 76.5), (RC, 64.75), (LX1, 64.75)], O, dash=DASH)
s.text((LX1 + RX0) / 2, 63.4, "修正输入后重跑", S_NOTE, O)

s.line([(LC, DC + HH), (LC, 97)], L)
s.text(LC + 1.6, 95.4, "通过", S_LABEL, INK, "start")

# 结果确认
s.box(LX0, 97, LX1 - LX0, 11, "teal")
s.text(LC, 101.5, "结果确认与证据归档", S_PANEL, T)
s.text(LC, 105.6, "摘要 / 版本 / 反汇编 / 波形定位", S_LABEL, INK)

# 各步留证（适用于所有步骤，用虚线框表示）
s.rect(RX0, 97, RX1 - RX0, 11, fill=C["panel"], stroke=C["panel_s"], sw=0.22, dash="1.0 0.7")
s.text(RC, 101.5, "各步留证（含失败）", S_TITLE, INK)
s.text(RC, 105.6, "命令 • 日志 • 退出码 • SHA256", S_LABEL, G)

s.save("S1-02.svg")
