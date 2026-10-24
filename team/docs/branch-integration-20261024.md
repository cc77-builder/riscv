# 2026-10-24 分支进度核查与 zjhwork 整合

用户要求查看 zjhwork2、zufan、James_Hotten 的进度，将领先且可直接复用的成果合入 zjhwork。第三个分支名称经用户确认；本轮连接器核实登录为 cc77-builder。

结论：以 zufan/c9132b8d 为整体快进候选，它已完整包含 zjhwork2；James_Hotten 的独立改进保留为后续移植项。本次仅更新 zjhwork，实际发布结果以远端回读回执为准。

## 分支快照与实际进度

| 分支 | 核查完整 SHA | 相对原 zjhwork | 实际完成范围 |
| --- | --- | --- | --- |
| zjhwork（整合前） | 17bab1d6e51692ccf1cc007e1ec73054ceda168e | 基点 | O2＋H1、局部成本、全核回归及B0/H1周期检查 |
| zjhwork2 | 79ce5643e225437000c3b5a3f2c97e888c47596c | 后代，新增3提交 | R2内核审计、S2安全尾部候选、主机模型和严格ELF/全核入口；此分支自己的阶段记录没有新EMU或周期成绩 |
| zufan | c9132b8d7f284ad7e76550315214b5b2ca431f79 | 后代，新增28提交，包含上行3提交 | 新S1、固定布局S2、镜像选择、普通C调用入口及MERGE-REG封存闭合 |
| James_Hotten | b806ce9c9c5228f6512474c7f2c3ab917349d7a6 | 后代，新增79提交；与zufan各有57/6独有提交 | 门控/观察器及严格验证改进；当前来源全核功能通过，但G3缺PARTIAL_KILL；无当前组合版新性能/PPA结论 |

提交数不是性能或完整度排名。James与zufan共同基点为bca14d45b07ff07a86a7f54bce2b25870e60e2f3，已分叉。

## 本次吸收的成果

- [S1](../optimizations/o2/r2-vector-accum/VALIDATION.md)：57次主批、768正式窗口，另4次小尺寸重放。4×8、8×32、16×64的reuse/endtoend相对同布局S0少5.7751%、12.5%、17.1589%周期；K13退化，保留回退。这里不是对RVV的加速比。
- [S2固定布局](../optimizations/o2/r2-safe-tail/FIXED_RESULT.md)：K13 reuse为210→187周期，但有界强RVV探针为175.25周期，S2仍慢6.705%，不扩大采用；保留退化结果。
- [R2选择工具](../optimizations/o2/r2-select/RESULT.md)：按形状查询、精确导出合格镜像，包含最快RVV及S0回退。
- [R4普通C入口](../optimizations/o2/r2-select/ENTRY_RESULT.md)：33次性能进程、384正式窗口、192重放比较；另3次普通C进程验证16公共函数。新调用窗下4×8、8×32、16×64获选vdot较最快同入口RVV少9.4667%、2.7431%、7.9859%周期，K13选择RVV。
- [MERGE-REG](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)：12核心＋2补充任务，13完整正常轨迹、1预期拒错，六项O2覆盖，完整原文及来源链可复算。

相对17bab1d，生产src、build.sc、子模块指针均相同，VDotElastic仍为O2＋H1低32位结果保存；未切换默认硬件或调用入口。ISA正文、NEMU补丁未改变语义。H1等旧封存载荷未改写，旧构建身份不冒充当前文档提交。

## 本机整合验证

干净工作区新建local/zjhwork-integration-20261024，从17bab1d执行git merge --ff-only team/zufan；无冲突，不改写历史。

| 验证 | 本次结果与边界 |
| --- | --- |
| 主机 | 16内核审计＋88安全尾部/门禁＋38 S1＋21选择器＋6可移植调用/恢复＋15合并回归＋75 T12，共259项运行通过；安全尾部另有4个依赖外置配置/夹具的组跳过 |
| C judge | 原生gcc构建并运行通过，T12_JUDGE_PASS checks=98321 |
| 原文复算 | S1主批、小尺寸补充、S2固定布局、强RVV探针、R4调用窗、普通C、MERGE-REG，7项PASS |
| Git索引 | MERGE-REG 560文件完整库存及blob检查PASS |
| 新硬件执行 | 本轮0次EMU、0次NEMU、0次RTL重构建；复用相同硬件源码与已提交原始证据，不宣称本机重跑队友全核实验 |

首次安全尾部测试缺ld.lld；从发行源下载lld-19包并解压到独立工具目录后重跑通过，未改系统工具或检查器。首次广泛R4测试缺原构建/探针路径R4_ENTRY_BUILD、R4_C_API_BUILD、R4_ENTRY_ARCHIVE；这三组没有在本机重跑，随后明确运行可移植检查及完整封存复算。未把跳过或历史PASS写成新的物理夹具执行。失败和命令原样保留。

证据：[摘要](../evidence/branch-integration-20261024/validation-summary.json)、[首次命令](../evidence/branch-integration-20261024/checks.json)、[补充命令](../evidence/branch-integration-20261024/checks-followup.json)、[载荷清单](../evidence/branch-integration-20261024/manifest.json)。本机原始输出：/home/riscv/riscv-lab/branch-review-integration-20261024。

## James_Hotten：有用但暂不直接合入

1. b0c8a54a03036aa9991f1aace5671c103a9b5324：ExeUnit取消后清除时钟保持位，避免已取消FU等不到out.fire而持续开钟。有对方真实父级旧版失败/修复通过证据；改变RTL行为，移植后需当前组合版父级、全核和周期验证。
2. 658ab8bdf567d3ba96f88aebdb0cea9cfc8daeb7：严格构建/归档门禁、避免python -OO删除assert式验证。这是混有H1及构建合同修改的合并提交，应逐块提取为版本化新入口。
3. 95e2cf05d836642ea8723c3a701449b31d31301b：冻结来源复算、环境和输出路径保护，同为合并提交，不是单一独立补丁。

相对zufan涉及6个Scala文件和build.sc。ExeUnit有实际门控变化，其余主要为CSR/ROB/FU可选观察器；VDotElastic数值实现相同。只读三方merge-tree发现当前路线、开发计分板两处实际内容冲突；代码可文本合并不等于来源合同及组合验证相容。

James全核绑定bc9e5ae469137a64b82744231acae9f9e3fe0359、EMU e66a8900eb09dc7f35acfe944c38386046fc8ef481e91792b2501f5cbd9679f5，14进程/5378正常vdot提交，但PARTIAL_KILL=0，明确INCOMPLETE。不能借zufan另一硬件身份的覆盖补成该版G3通过。本次记录为后续移植候选，未实施这些改动。

### 旧H1重放的合同边界补注

James指出的旧重放调度问题经原始result.json核实：2026-10-21 UTC 05:38:25至05:42:01的H1 r1/B0 r2、05:42:01至05:45:39的H1 r2/B0 r1分别重叠，偏离同镜像两版顺序交替的合同。不得把这四次历史重放描述成严格串行。

原证据：team/optimizations/o2/result-width/h1/performance/evidence/20261021-performance/files/runs/campaign-01/<mode>/performance/performance-d0-s02-r<编号>/result.json。compare.py的paired_deltas及results.py正式汇总均限定phase=measured、replay=0；96对正式统计不包含4次重放，正式周期逐对相等仍有原始数据支持。本次保留旧封存，未补跑；后续若关闭此合同缺项，须新建串行重放证据。

## 接续与分支目标

硬件继续O2＋H1；S1/R2-SELECT及R4普通调用有上述资格，K13选择更快RVV。T17、R5/G5默认采用分别验收。

[Issue #2评论6378912183](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6378912183)报告T17新干净构建已完成正确性、正在启动33进程串行性能复现。这是队友进行中报告，尚不在c9132b8d快照中；本轮不接管其工作、不宣称T17完成。下一步先读取最终已提交结果，避免重复构建。

导入文档保留团队zufan协作安排；本用户当前及后续本地目标为zjhwork，不能据此自动向zufan发布。旧“只写zjhwork2”“本轮不push”按原时点理解。本次不代签人工ACK，不代替T17和最终参赛冻结。
