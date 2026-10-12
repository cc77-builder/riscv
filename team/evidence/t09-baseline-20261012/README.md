# T08 复核与 T09 baseline 实际证据

2026-10-12（北京时间）；团队基准 `7cd588a8f`。本轮尚未提交源码以输入、源码、配置、镜像及补丁摘要识别。既有 T05/T08 归档不修改。

| 原始记录 | 验收结论 |
| --- | --- |
| [QEMU run.log](virt/run.log) / [检查](virt/check.json) | 最终脚本普通RVV，48定向+1000随机，1048/1048通过，退出0 |
| [香山目标构建](xs-build/build.txt) / [反汇编](xs-build/disassembly.txt) | 固定nexus-am构建通过；保存完整来源和elf/bin摘要 |
| [NEMU run.log](nemu/run.log) / [检查](nemu/check.json) | 同一输入，1048/1048通过，退出0，GOOD TRAP |
| [输入、镜像与源码校验](nemu/source-verification.txt) | 编译来源与当前运行来源匹配；data/source/image分别保存实际校验记录 |
| [Python tests](model-tests.txt) | 16个方法通过；含32768种scratch编号组合和缺失证据拒绝 |
| [旧镜像来源负控](stale-source/summary.json) | 真实main.c注释变更导致校验拒绝，退出1且未执行镜像；源码复原、镜像未变 |
| [T08来源注入负控](t08-guards/summary.json) | 普通NEMU、优化模式NEMU、依赖未知源码均拒绝；注入文件移除、补丁源码未变 |
| [T08干净构建](t08-build/build.txt) | 最终来源检查脚本构建通过，config/binary/provenance保留 |
| [静态序列校验](sequence-check.json) | 全部生成stub包含13条完整核心指令，算术区间3条；可执行text无custom-0 |

逐用例记录包括预先声明scratch、完整目的、六项CSR、VS、trap_count、哨兵及全部非scratch比较结果。高位/非scratch/CSR的判定负控与scratch允许变化记录在实际运行日志中。

QEMU与NEMU数据分别使用独立目录避免覆盖，cases.jsonl摘要相同。数值预期均由独立T05模型生成。基线配置及指令语义见 [measurement](../../spec/measurement.md)，复现命令见 [workload](../../workloads/rvv-baseline/README.md)。运行脚本/输入生成器/模型/汇编的摘要可对应仓库源码；NEMU沿用固定基线加T08补丁，CUSTOM_VDOT虽启用，baseline的执行text不包含该候选编码。

[summary.json](summary.json) 从真实check.json、退出码和负控记录提取，未合成任何模拟器通过日志。所有归档文件由 [archive.sha256](archive.sha256) 校验。部分SHA清单保留原运行机器的绝对路径。全量输入、elf/bin留在忽略的team/out，可按生成器/seed复现。

本轮没有运行香山RTL、全核DiffTest或硬件计时，未证明真实两种指令序列的T13配对与加速比；同一协助工具的子任务复核不替代成员签字或非作者环境验收。
