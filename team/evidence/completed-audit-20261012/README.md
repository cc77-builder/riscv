# 已交付任务综合审查证据

2026-10-12（北京时间）。审查HEAD `7cd588a8f`及未提交T09/来源检查修复，不修改原五份证据归档。本目录是验证门槛的审查实验，不是新增功能验收或性能实验。

| 记录 | 实际观察 |
| --- | --- |
| [Python回归](python-tests.log) / [原C检查](judge-original-tests.log) | 原16个Python/18个C检查仍通过 |
| [VS判定探针源码](judge-vs-probe.c) / [输出](judge-vs-probe.log) | 生产judge对异常Dirty→Initial记录仍返回PASS；是判定缺口，不是NEMU实际发生该错误 |
| [ignored-source探针](probe-ignored-source.py) / [观察](ignored-source.json) | 新增C文件被Git忽略，却被实际find规则收集并通过来源条件；未编译此文件，已移除 |
| [运行来源探针](probe-runner-mismatch.py) / [观察](runner-mismatch-summary.json) | 原编译镜像配追加注释后的源码摘要，以及reference记录目录/standalone解释器错配，仍获退出0和115项通过 |
| [该次真实运行](runner-mismatch/run.log) / [驱动输出](runner-mismatch-driver.log) | 仅用于证明错误来源会被接受，不能把115个PASS当成来源门禁通过 |
| [覆盖/原归档核对](coverage-and-archives.json) | 五份原归档共189个摘要匹配；T08合法前VS全Dirty；T09随机寄存器组合单一且全部scratch布局相同 |
| [只读checkout过滤核对](checkout-filters.json) | 核对的已提交历史归档在Git过滤读出时摘要匹配 |

VS探针是人工记录fixture调用实际C判定器，明确不充当模拟器日志。来源探针使用已归档镜像的复制品：当前源码追加注释与原编译来源不同，运行后恢复原字节；运行记录source.sha256因此按设计不能对应恢复后的源码。该不匹配是被审查漏洞的证据，不能伪装为一个有效来源的新功能通过记录。

探针脚本、原运行输入/镜像/源码摘要保留供复现；完整数据和elf/bin仍在team/out。未写入NEMU功能源码、未编译注入文件、未改原镜像、未跑RTL或硬件计时。审查报告见 [completed-tasks-audit.md](../../docs/completed-tasks-audit.md)。本目录文件由archive.sha256校验，旧归档原SHA清单保持。
