# R5/G5 工程总验收结果

完成时间：2026-10-27T22:58:45.908838+08:00；执行者：@cc77-builder / Agent。**选定范围内的工程验收完成，候选已冻结；未上传 GitHub。**

本次没有改生产RTL，也没有新做性能优化。硬件保持0f（O2两槽＋H1低32位结果保存＋DIV取消保持修复）；软件保留已合格firstdot V2四尺寸入口和独立显式C8 8×32入口，公共默认未切换。

## clean-02 墙钟问题的处理

原14项全核的UTC容量检查出现80.119ms表观四路重叠，原FAIL/WALL_CLOCK_LIMITED记录永久保留，未修改时间戳或门槛。按事前合同仅重新执行o2-control-diagnostic，其余13项全部从原始日志重新解析。

最终组合14项通过功能、NEMU差分、O2覆盖和负控后同镜像恢复。**13项复用＋1项新执行，不是重跑14项**。选定记录的严格UTC并发峰值为3（上限3）；新单进程以同boot/PID的单调时钟包络验证，峰值1，包络1497.000秒。该耗时是宿主审计数据，不用于DUT加速比。

新控制诊断检查131072字节寄存器结果，退出0；独立离线审计再次通过。原13项没有单调时钟记录，不能追溯宣称原批次的实际OS并发已测量。

本次UTC间隔与单调包络仍相差-62.888356秒（UTC更短）。因此墙钟稳定性仍未证实；新占用审计依赖同boot的单调包络，而非容差修正UTC。该现象如实留档，不把旧批次或系统时钟标为已修复。

## 验收矩阵

| 项目 | 状态 | 依据及范围 |
| --- | --- | --- |
| identity | PASS | 0f生产源码398项与clean副本、选定Git版本一致；完整工作树冻结24157项；冻结不等于提交；HEAD不能代表未提交软件材料 |
| stage1 | PASS_REUSED | 当前hello/vadd原文重验；原阶段一12文件SHA及220295598B波形定位；波形为2026-10-09 vadd；团队标识仍是占位符，正式材料需成员确定 |
| spec | IMPLEMENTED_INTERNAL_CONTRACT | SEW8/VLEN128，8对signed int8低32结果、高96清零；编码与异常合同有设计说明；Q01–Q07待官方澄清；不声称官方确认全部内部语义 |
| model | PASS_NEW_HOST_CHECK | 原模型及确定性向量一致性重新检查；22定向+10000随机未变；主机模型不代替RTL |
| fu-parent | PASS_REUSED_RAW_REPARSED | 0f真实FU与VFEX4父级；完整128位、反压/取消/身份/异常、严格DIV关钟及4+16负控；复用0f原167载荷；未新执行RTL仿真，不转授C1/C2/C3 |
| fullcore | PASS_COMPOSITE_13_REUSED_PLUS_1_NEW | 固定原13项重新解析+新o2-control-diagnostic；117不同/124次功能例，O2覆盖及负控恢复；组合验收不是fresh14；原14项UTC容量FAIL保留；本次UTC间隔比单调时钟短62.888356秒，系统墙钟稳定性未证实，新占用审计采用单调包络 |
| microbench | PASS_REUSED | 0f相对修复前96对正式窗完全一致；独立batch128为221 vs RVV678 cycles，3.067873×；历史0f构建的固定微基准；不是当前GEMV或LLM端到端加速 |
| firstdot | PASS_REUSED_INPUTS_REVALIDATED | 干净firstdot四尺寸：768窗口/96普通C输出复现一致；前三选vdot、4×13选RVV；33矩阵+3普通C为既有运行，本轮没有新性能 |
| c8 | PASS_REUSED_FINAL_IMAGE_RECHECKED | 627项输入闭合、C8包与旧合格普通C最终BIN/PT_LOAD/入口/48表项/12数据组一致；273 vs最快RVV299 cycles/1.095238×来自既有性能矩阵，不是本次新计时 |
| parameter | PASS_REUSED_IN_ORIGINAL_SOURCE_ENVIRONMENT | 独立s16x8/r64扩展归档复算；独立实验算术和包装；生产指令及NEMU仍INT8，未新增全核INT16 |
| cost | EVIDENCE_PASS_TIMING_NOT_CLOSED | 0f同约束面积/五档STA资料1008文件回读；FU17298.246、父级284614.946微米平方；不是新综合；1ns负slack保留，整核Fmax/布线后时序/功耗NOT_TESTED |
| reproduction | PASS_REUSED_SAME_HOST | 独立源/依赖、EMU/NEMU/AM/klib及25应用实际重建已完成，身份再次核验；同机Agent复现，工具与下载缓存复用；不是另一成员/另一机器复现 |
| entry-rollback | PASS_EXPLICIT_ENTRY | C8独立静态库入口及RVV回退、firstdot原入口与O1/B0历史对照保留；不新增混合dispatcher、不变公共默认；改链接/数据/工具链需按影响再验 |

## 当前可使用的性能结论

C8 8×32完整调用窗口为273 cycles，最快同场RVV为299，**1.095238×**；较firstdot 282.25少3.2772%。这些来自既有4尺寸×3数据集矩阵，本次只是验收和身份复核，没有新增跑分。四路batch128的3.067873×来自另一固定微基准合同，不代表应用端到端收益，不能与1.095238×混为一个总分。

## 已知边界与下一步

1ns STA尚未收敛，功耗、整核Fmax和布线后时序未测；保留真实成本取舍。独立INT16参数扩展不等于生产全核INT16支持。4×8/16×64配置复用控制漂移仍未归因，未纳入新采用项；4×13保留RVV。规格Q01–Q07待官方澄清，团队名称仍待确定；正式报告/PPT/视频和成员复核由团队另行安排。

工程可以以此冻结候选为保底版本，不再为了收尾新增应用或强行优化。后续可由用户安排发布zjhwork、成员复核与比赛材料，或另选一个有明确收益假设的优化。未授权的发布本轮不执行。

冻结文件24157项，生产源码398项与0f及clean副本一致。快照在 /home/riscv/riscv-lab/software-import-20261026/r5-g5-acceptance-01/frozen-workspace.tar.gz，已逐项回读，含工作树文件但不含Git历史和外部依赖。使用/回退见[README](README.md)，逐项身份见[数据记录](record.json)，原始新增证据见[manifest](evidence/manifest.json)。各失败尝试也已封存，没有覆盖旧28条数据档案。
