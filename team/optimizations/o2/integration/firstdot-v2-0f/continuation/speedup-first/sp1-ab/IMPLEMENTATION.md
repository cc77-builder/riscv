# SP1-A/B 原P4恢复与观察器适配合同

执行日期为2026年11月3日，UTC+08:00。用户已授权SP1-A/B，本轮范围为观察器实现、宿主负控、默认关闭及FU/真实VFEX4局部观察中性。SP0的成本和五角色目标准入合同保持，SP1-C及其后目标另行执行。

## 源码身份与改动

独立构建源位于 `/home/riscv/riscv-lab/speedup-first-20261103/sp1-ab/candidate`。398项生产src从固定0f恢复，加原G1补丁，其Elastic与O2的SHA与SP0相同。原工作树R1不覆盖，原G1恢复收据见evidence/restoration.json。

修改前已向用户说明以下四文件。

| 文件 | 改动与不变的功能边界 |
| --- | --- |
| VDotO2.scala | 严格0/1的新SP1_TRACE，默认关闭。要求O2/P4/T14，拒绝旧O2观察器与新SP1混用，T13要求匹配观察协议 |
| VDotElastic.scala | 原G1算术和状态转移保持。子模块中先形成directR、enqueueP、incomingData、pData、acceptedCtrl只读句柄，再由父模块tap |
| ExeUnit.scala | 保留旧O2分支，增加独立SP1分支。PSeq只在入P更新，RSeq依旧P搬移或新请求直入更新，当前R响应使用沿前序号。DIV接受/取消/物理残留输出依据真实接口记录 |
| Rob.scala | 保留旧O2/T13，增加SP1分配、提交、redirect记录 |

新观察寄存器位于未门控父时钟域。观察量不反馈到ready、slot状态、结果、门控和DIV协议。该性质由生成物功能锥审计和实际局部trace on/off相同刺激共同检查。主机模型与仿真不作为形式等价证明。

## 局部验证合同

原G1全部数值向量、协议oracle、负控和真实DIV/SQRT夹具继续复用。仅为观察中性在独立夹具增加逐拍完整接口记录，数据/刺激/断言不改。FU检查完整128位与其已暴露控制字段，真实父级补齐完整VPU/perf及DIV共享协议。

固定候选P4=1、O2=1、T14=1，SP1_TRACE为0/1配对。旧O2/T12/O1/T13 trace均关闭。第一层独立FU不会实例化ExeUnit观察器，第二层真实VFEX4实际展开并执行生产SP1观察分支。局部多次复位使用显式local检查模式，无法授予ROB/退休/全核资格。Rob由实际Scala编译及可行的独立展开检查，完整退休与CSR运行资格留待SP1-C后全核验证。

局部编译与仿真串行，CPU4–5、构建2工人、JVM10GiB。所有输出独立，失败保留。读到Issue #2最后有效UPDATE为6511950608，队友CPU0/1/2及冻结输入保护继续尊重。本轮不向Issue发消息，不做共享分支集成。

## 通过条件与记账

- 全部完整128位与原局部控制测试通过，trace on/off逐周期功能记录相同。
- SP1 parser识别真实directR/enqueueP/MOVE、身份、取消/复位和DIV，宿主负控全部拒绝错误。
- 所有新开关默认关闭，合法配置可生成，非法配置生成期拒绝。
- 原G1 trace-off与候选trace-off功能生成物一致，新增观察锥与功能锥分离，源码/工具/依赖清单固定。
- 完成后更新计分板与统一版本数据档案，标明加速比NOT_TESTED、成本历史复用条件及五档时序。最终选择为PENDING_USER_SELECTION。

每个事实以实际收据为准，未完成项保持HOLD或NOT_TESTED。实际EMU、NEMU、综合、STA均不属于本轮。
