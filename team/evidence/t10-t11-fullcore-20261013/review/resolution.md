# 独立审查问题处理与验收边界

原REVIEW只审固定1bd6和当时不完整review-inputs，结论保留不改。下面是主审基于当前实际完整矩阵和代码修复作出的逐项处理，不伪称Codex已独立审过后来每行修改。

| 问题 | 本轮处理 | 证据/仍有边界 |
| --- | --- | --- |
| R01 来源只求片间一致 | 外部source/parent-source/EMU/ref/flash/corpus固定；consume build/runtime source/config/provenance，按被测Git blob核对源码及两阶段生成器 | 真实归档重算和统一错来源/错运行产物反例拒绝；二进制按实际执行时字节验证回执绑定，不把hash当重新构建 |
| R02 缺自检与异常先行 | 七条H记录逐项校验并要求正确顺序；所有实际extension顺序等于分片计划 | 删除七条H、异常移到D00之前均拒绝；实际56自检/24负控逐条读取 |
| R03 负控和恢复未闭合 | 同image/EMU/ref/flash与实际build/runtime回执对应；raw injection与mismatch/result PC/vd/word一致、目的字段与编码一致 | 最终负控是vdot指令bit100，shard0同镜像正常完成；无关PC和改summary反例拒绝 |
| R04 完成时序/矛盾exit | 只接受单一driver exit/带时区完成时间；driver verifier→action→完成标记有序；单run的DiffTest→begin→summary→GOOD TRAP有序 | GOOD TRAP前移、缺summary但exit0、矛盾exit124/0均拒绝；旧中断任务明确排除 |
| R05 current摘要过时 | original source_commit/blob/hash/size不变，Current字段重算；增加modified/current_size与本地适配说明 | 41个导入路径逐文件真实SHA复核，全部当前值对应 |
| R06 外置/硬编码验收材料 | checker入team/scripts，parent/runs/repo/pins参数化；完整8片与API runner/config/provenance/日志入库 | 源母用例plan同旧，8片124记录不是旧4片120记录；API仍非程序状态可达证明 |
| R07 虚拟化/陷阱竞争未证明 | 当前交付明确M模式固定程序；不宣称S/HS/VS与乱序陷阱竞争完成 | 转入T12控制/扩展验收；无生产BUG证据时不凭猜测改硬件 |
| R08 当前入口过时 | 新验收报告、根AGENTS/README、teamREADME、patch1.1说明同步；旧WIP/旧patch原文保留 | 最终发布SHA与远端结果只在实际回执记录，不预填成功 |

主审新增/强化验收器后，以真实归档进行正向重放，并在临时副本做拒错测试；既有数学golden、117项原始输入/期望、实际日志及运行源码未为通过而修改。最新全部测试数量和退出码以`final-host-tests.log.gz`为准。
