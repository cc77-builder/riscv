<!-- O2_H1_PUBLICATION_20261021 -->

> 2026-10-21 本批发布：按用户授权将 R0/R1、H1 实现、全核回归及 B0/H1 周期不退化证据交付 GitHub 的 zjhwork。H1 本机验证链完成，96 对正式窗口周期完全一致；R4 独立复现与最终采用待完成。实际发布结果以远端回读回执为准，下文旧发布状态按历史时点阅读。 [发布说明](../../../../../docs/o2-h1-publication-20261021.md)。

# H1 全核构建与 NEMU 差分回归

2026-10-21：**本轮已完成。** 先读 [H1 全核结果](H1_FULLCORE_RESULT.md) 和 [执行合同](CONTRACT.md)。

13 项正常作业与 1 项 bit100 预期拒错全部满足要求，同镜像正常库恢复通过。117 个唯一功能/异常用例、5,378 条正常 vdot 提交、95 项主机检查及六项 O2 两槽覆盖通过；严格离线重审核对了 429 份硬件源码与 21,236 份依赖。完整 128 位结果、身份、反压和取消仍沿用原门禁。

硬件提交为 8b5024fcbd96986871cc40ce8c9fb71a67c495eb；新 EMU SHA256 为 e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747。当前 repo/build/emu 是 H1，原 B0 构建完整保留在 /home/riscv/riscv-lab/o2-b0-build-before-h1-20261021，R0 锁仍绑定 B0。

[封存清单](evidence/20261021-fullcore/archive-manifest.json) 收录 300 份载荷，原始 230,185,700 字节、存储 18,431,410 字节。Linux 与 Windows 原生便携复算均通过，核对 13 条完整轨迹和 1 条预期故障截断轨迹。便携复算只做归档字节和轨迹审计，不重新执行 EMU/NEMU；完整来源与架构检查以本轮 Linux 严格重审为准。

## 复核与定位

原始工作根 /home/riscv/riscv-lab/o2-h1-fullcore-20261021；交付根 /home/riscv/riscv-lab/o2-h1-fullcore-delivery-20261021。主流程 campaign-state.json 和交付 finish-state.json 均已完成，不要重复启动 launch.py/finish.py 或覆盖已封存证据。命令、日志、真实退出码、输入散列及生成 RTL 快照保留在归档中。

在完整仓库中只读复算已封存轨迹：

    python3 -B team/optimizations/o2/fullcore/portable.py \
      --archive team/optimizations/o2/result-width/h1/fullcore/evidence/20261021-fullcore \
      --core-campaign core-01 --supplement-campaign supplements-01 \
      --output /tmp/h1-portable-new-review.json

输出使用新的文件名。[Linux 复核回执](reviews/20261021/portable-linux.json)、[Windows 原生复核回执](reviews/20261021/portable-windows.json)及[双平台命令记录](reviews/20261021/review.json)保留实际结果；Windows 交付目录另有逐文件清单。便携复核回执在归档之外保存，原封存字节保持不变。

下一项是 B0/H1 同镜像周期不退化检查。本轮未运行新性能 A/B，未改变默认开关，未推送 GitHub；整项 R1、独立成员复现和最终采用仍待后续验收。原有面积/参考时序结论保持不变，正式报告继续后置。
