<!-- O2_H1_PUBLICATION_20261021 -->

> 2026-10-21 本批发布：按用户授权将 R0/R1、H1 实现、全核回归及 B0/H1 周期不退化证据交付 GitHub 的 zjhwork。H1 本机验证链完成，96 对正式窗口周期完全一致；R4 独立复现与最终采用待完成。实际发布结果以远端回读回执为准，下文旧发布状态按历史时点阅读。 [发布说明](../../../../../docs/o2-h1-publication-20261021.md)。

# B0/H1 同镜像周期不退化检查

2026-10-21：B0/H1 同镜像周期不退化检查完成。36 次新运行、478 个校验窗口、192 个正式窗口组成的 96 对样本逐项周期完全一致；严格原始日志重审和 Linux/Windows 便携复算通过。H1 本轮没有周期提速，保留此前局部面积收益及部分 STA 路径回退的取舍。H1 本机验证链已齐备，R4 独立复现与最终采用仍待完成。本轮未推送 GitHub，未切换默认模式，未自动开始 R2/R4，正式报告后置。

[工程结果](B0_H1_RESULT.md) · [预先固定的测量合同](CONTRACT.md)

原始工作根：/home/riscv/riscv-lab/o2-h1-performance-20261021。交付监督根：/home/riscv/riscv-lab/o2-h1-performance-delivery-20261021。两条流程均已结束，不要重新启动 launch.py 或 finish.py，不修改已封存载荷。

原始运行源码固定 f732d92d；受测硬件固定 B0 b218cbc6、H1 8b5024f。导出工具的实际字节由 archive-manifest.json 固定，与运行提交身份分开记录。

便携复算（无需 EMU）：

    python3 -B portable.py --archive evidence/20261021-performance --output /tmp/b0-h1-recheck.json

输出路径必须不存在。Windows 使用交付目录 tools/portable.py 和 archive/，以 Python -X utf8 -B 执行。该复算验证原始证据，不代替 Linux 构建依赖审计或另一名成员重构建。
