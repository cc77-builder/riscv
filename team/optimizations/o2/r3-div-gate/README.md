# R3：O2 DIV取消关钟修复候选

最小修复、严格FU／真实父级、新全核/NEMU、同镜像周期及同约束综合STA均已完成。
本地硬件源码为0f12df675378556670afd0dd2153f47fcb330610，未推送GitHub。

96对正式窗口周期相同；完整FU成本不变，父级面积约降0.093%，但部分父级时序路径变差。
保留为关钟正确性修复候选，定向时序复核及一次 C1 筛选已完成；C1 因其他路径退化不采用。只读归因及 C2-G0 控制证明已完成；固定实现/有效复位条件下空闲必 ready 成立，建议进入有界 C2 候选设计。尚未实施 C2，未自动切换团队默认。

- [最新总结果与取舍](PERFORMANCE_COST_RESULT.md)
- [同镜像周期](performance/README.md)
- [同约束综合STA](cost/README.md)
- [全核结果与证据](fullcore/RESULT.md)
- [全核执行合同](fullcore/CONTRACT.md)
- [局部合同](CONTRACT.md)
- [局部结果、证据与边界](RESULT.md)
- [局部归档清单](evidence/20261024-local/manifest.json)
- [局部离线复算器](audit_evidence.py)
- [前置只读分析](../r3-readonly/README.md)

- [周期/成本封存清单](evidence/20261025-performance-cost/manifest.json)
- [归档字节检查](reviews/archive-linux.json)

后续记录：[C2-G0 控制证明与候选接续](c2-g0/RESULT.md)；[DIV 门控只读归因与 C2-G0 建议](c2-attribution/RESULT.md)；[时序代价复核与C1有界候选决定](timing-review/RESULT.md)；[C1 实现与筛选结果](c1/RESULT.md)。C1 局部功能通过、综合STA筛选不通过，保留 0f12df6 原修复版，不进入 C1 全核。
