# P0～P5 分析与失败证据归档范围

本次仅发布分析、文档、结构化结果和失败/运行日志到 zjhwork，稳定方案保持 **0f＋firstdot V2＋原 C8**。不合入未采用候选的实现代码、源码补丁或构建产物。

- 发布基点：10b71ad4bff25cd2070e775c74a4717b01602f75。
- 生产硬件：0f12df675378556670afd0dd2153f47fcb330610；src树：78a0c93852dced038f645205e33d36a520fedfcd。
- 稳定EMU/C8最终镜像与[P5收口](../optimizations/o2/integration/firstdot-v2-0f/continuation/p5-stable-closeout-v1/RESULT.md)绑定；本轮不运行或重建。
- [逐文件发布与本地保留清单](p0-p5-publication-20261031.json)：新增研究资料2753项；本地保留3886项；另更新既有导航/计分板/47条数据档案。

## 阅读入口

| 内容 | 入口 |
| --- | --- |
| 当前方案、完整优化取舍 | [当前路线](development-route-current.md) |
| 稳定版结论与必要缺项 | [P5](../optimizations/o2/integration/firstdot-v2-0f/continuation/p5-stable-closeout-v1/RESULT.md) |
| P1/P1-R1：HOLD | [原P1](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/RESULT.md)、[R1](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-r1/RESULT.md) |
| P2调用与依赖归因 | [调用路径](../optimizations/o2/integration/firstdot-v2-0f/continuation/callpath-p2/RESULT.md)、[依赖链](../optimizations/o2/integration/firstdot-v2-0f/continuation/dependency-p2/RESULT.md) |
| P4与R1：成本NO-GO | [G2](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2/RESULT.md)、[R1成本](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1-cost/RESULT.md) |
| C8分段归约：NO-GO | [归因](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-r1-review/RESULT.md) |
| P3：预算HOLD暂存 | [完整预算归因](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-budget-attribution-v1/RESULT.md) |
| 完整历史实测/失败边界 | [47条数据档案](version-data-ledger.md) |

## 这不是完整候选源码包

历史结果、manifest和记录保持原字节，不回写当时的本地状态/时间/身份。文中的“未上传”“下一步”按其原记录日期理解，当前取舍以当前路线及P5为准。

部分历史manifest引用的候选源码、Python检查器、生成器、C/汇编、RTL、patch、对象、ELF/BIN、源码压缩包和映射网表**本次刻意不上传**；包含源码的打包归档也排除。相关源码链接在GitHub上可能不可访问，或检查器命令不能仅凭此资料归档执行。它们仍留在原本地路径，排除清单保存SHA和大小；不将删减后的GitHub资料宣传成完整可运行/完整离线复现包。保留的旧manifest说明原实验身份，本次发布清单单独说明实际上传范围，两者不能混用。

这不影响已在仓库中的稳定0f、firstdot和原C8代码及其既有证据；本次提交必须保持全部既有非文档文件不变。开发工作树里的VDotElastic.scala和VDotO2.scala仍是本地默认关闭P4研究差异，未暂存、未提交。当前本地目录同时包含稳定基线和未采用研究文件，不是干净交付树。

不产生新性能成绩；失败、退化、HOLD和NOT_TESTED均保留。准备时间：2026-10-31T14:40:19.087660+08:00，@cc77-builder / Agent。
