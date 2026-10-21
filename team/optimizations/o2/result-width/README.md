<!-- O2_H1_PUBLICATION_20261021 -->

> 2026-10-21 本批发布：按用户授权将 R0/R1、H1 实现、全核回归及 B0/H1 周期不退化证据交付 GitHub 的 zjhwork。H1 本机验证链完成，96 对正式窗口周期完全一致；R4 独立复现与最终采用待完成。实际发布结果以远端回读回执为准，下文旧发布状态按历史时点阅读。 [发布说明](../../../docs/o2-h1-publication-20261021.md)。

<!-- B0_H1_PERFORMANCE_COMPLETED_20261021 -->

> 2026-10-21：B0/H1 同镜像周期不退化检查完成。36 次新运行、478 个校验窗口、192 个正式窗口组成的 96 对样本逐项周期完全一致；严格原始日志重审和 Linux/Windows 便携复算通过。H1 本轮没有周期提速，保留此前局部面积收益及部分 STA 路径回退的取舍。H1 本机验证链已齐备，R4 独立复现与最终采用仍待完成。本轮未推送 GitHub，未切换默认模式，未自动开始 R2/R4，正式报告后置。 [结果记录](h1/performance/B0_H1_RESULT.md)。下文旧状态按历史时点阅读。

# R1 结果寄存器审查与 H1 实现

2026-10-21更新：**H1局部验证、参考成本评估和全核NEMU差分回归均已通过**。见[局部结果](h1/H1_RESULT.md)与[全核结果](h1/fullcore/H1_FULLCORE_RESULT.md)。下一项B0/H1同镜像周期不退化检查；整项R1及最终采用仍待后续验收。以下保留首次映射审查的复现入口与历史结论。

# 首次映射审查（历史记录）

2026-10-21：**审查通过，建议进入低 32 位 H1 候选；候选尚未实施。**

先读 [审查结论与后续条件](R1_MAPPING_REVIEW.md)。这是工程审查记录，正式比赛报告继续后置。

在已包含 O4 封存材料的完整香山仓库中，用 Python 3.10+ 执行：

```bash
python3 -B -m unittest discover -s team/optimizations/o2/result-width -v
python3 -B team/optimizations/o2/result-width/audit.py \
  --evidence team/optimizations/o4/evidence/20261020-cost \
  --output /tmp/o2-r1-new-audit.json
```

输出路径必须尚不存在，避免覆盖旧结果。程序只读封存 JSON、参考库和原 summary，不调用综合器、仿真器或网络。输入 manifest 身份固定，实际读取载荷的压缩前后 SHA256 均校验。四份网表顺序处理；父级 JSON 较大，需要约 GB 量级空闲内存。

预期输出 `O2_R1_MAPPING_AUDIT_PASS`。新的输出保留实际命令与 Python 版本，比较时应比较 `profiles` 和输入身份，而不是要求整个运行记录字节相同。

本轮工作目录：`/home/riscv/riscv-lab/o2-r1-result-width-20261021`。交付证据在 [evidence/20261021](evidence/20261021/manifest.json)。`audit-attempt-01.py` 是失败尝试快照，实际入口是本目录 `audit.py`。

成本数字是旧网表局部归因；只有 H1 新映射和验证通过后才能报告净节省。没有生产 RTL 改动，因此本轮没有重跑数学模型、FU、全核或性能测试，也没有改变 R0 基线锁。
