# prefix 真实父级有限功能验证合同 v1

状态：新入口准备阶段，尚未实际生成或验证父级。此合同不改写上游冻结记录。

## 目标、顺序与范围

只验证已完成局部算术、FU 和成本评估的同一个 prefix 候选放入真实 VFEX4 父级后的功能行为。其 matched feature1 FU 面积低于 20,000 library area units，是推进可采用性的依据；此次不测 EDA、频率、功耗或应用提速。原 K288 与完整 forward 的实际终态优先；K288 的原辅助进程真实回收后，才可使用唯一 CPU1 / absolute nice5 辅助 worker。若闭合软件结果支持更直接、可按预算完成的应用工作，先处理该主线。

不改 resident 源码、缓存、原父级、官方程序、原 checker、已运行输入或实验合同；不创建 checkout、不构建 EMU、不运行整核、不派生第三个硬件候选。新增源码只在独立控制器目录；生成、临时文件、harness classes、仿真二进制、日志和回执只写全新外部输出。

## 冻结输入

| 对象 | SHA256 |
| --- | --- |
| prefix local-01 完成结果，205865B | `a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0` |
| `VDotDatapath.scala` | `1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb` |
| `VDotElastic.scala` | `912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92` |
| prefix local inputs | `1afacb22c143705355ffed93b62824b2a02153e799b003bcc7f92dba1b10c219` |
| 完整 23 类 overlay 清单 | `f36dd44ef66c0058a73839bfeaacd321cc6ac7d41144c622c38371948375c4bf` |
| 原 generation recipe | `ec29dc8725cf3a1c04ea684e2753debc1a9b2a04d37b4adadcdfe96f85ec20d8` |
| 原完整基础 classpath 清单 | `d9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902` |

上游完整结果必须确实完成两个 feature 的 FU 检查和两个实际 prefix 模和 SAT，源、产物、classpath 与子进程回收记录均成功。原乘法 miter 的 `UNKNOWN_EXTERNAL_TIMEOUT` 原样引用，不转换成 SAT PASS，不在此次重跑。

完整 overlay（包括 wrapper、status 和匿名类）先于基础 classpath。只外部编译原 `GenerateVDotElasticParent.scala`，候选算术及 wrapper 不重编。旧父级两态的原状态、16 个 source-map 文件、完整生成清单、原 C++、vectors、工具、支持树和固定 helper 沿用旧 parent-v3 身份；运行前后核验。不得仅替换两个 class 或只依赖基底 HEAD。

## 时钟、接口与测试

沿原 harness 的时钟上升沿驱动和同步高有效 valid 状态复位，保留真实 ClockGate、DIV、dispatch 和三条写回路径。输入是已解码请求，不覆盖译码、Rename、RF 或 ROB 退休。VLEN=128、ROB=48，dot8/16 合法性、128 位结果的低32位符号扩展及高96位清零沿既有规格；没有新增 fflags/vxsat 写入。

仍为两弹性槽，最早 E2 响应、无停顿 II1。P 每半区保存两条19位 carry-save row；feature0 为一半区，feature1 为两半区，后者在接收 dot8 时将高半区两条 row 置零。R 保存19/20位精确有符号结果，再扩展到架构输出。控制、完整 perf 元数据、kill、reset、stall 和 DIV 切换语义不改变。

原 source snapshot、派生 C++、10022向量、14组刺激、dot16扩展，以及原 checker 自测保持原样。每态执行原真实父级正例、严格 trace 与独立事务回放、完整577-bit metadata audit、dot16 coverage、全部20项观察负控及其原判定器。20项是观察负控，不称为20种RTL故障注入。原 DIV 单行 WIDTHEXPAND waiver 原样沿用。不新增微架构或性能矩阵。

## 新生成边界

完整真实父级 SV/V 集合必须恰好将 `VDotProducts.sv`、`VDotReduce.sv` 替换为 `VDotCarrySaveRows.sv` 和该 feature 的 `VDotPrefixFinish19.sv` / `VDotPrefixFinish20.sv`。新黑盒 RTL 必须逐字节等于本候选已验证局部生成物；ClockGate 等既有资源仍完整保留，资源清单及完整 filelist 都须实际核对。

允许变化的既有模块仅有：

1. **VDotElastic。** 与同 feature 的旧父级比较，公开模块接口逐字节保持；剔除旧 P products、新 P rows、R data 和 stalled-response shadow 后，有序非数据寄存器更新右值表达式相同。数据 checker 核对实际低/高64位接线、P row 数量/19位宽度、P更新右值与dot8高半零条件、prefix行序及20位所需符号扩展、R19/R20位宽、非法零结果、架构高96位零和低32位符号扩展。feature1 的唯一 `isDot16` 定义必须为原 `fuOpType == 9'h1`；有限支持已见的模块级 `wire` 和块内 `automatic logic` 声明，不假设其位置。941位 stalled shadow 仅允许加入同一已绑定的 R 符号扩展线，其余完整表达式不变。实际节点名可由该唯一声明和输出接线绑定，不假设必须叫某个 `_GEN`。只在这些封闭表达式匹配中忽略空白，不做通用 HDL 归一化。右值比较不检查所有 if/clock guards；接收、时钟和控制协议仍由固定源码身份及原父级套件验证，不把静态比较称为完整顺序等价证明。
2. **extern_modules。** 仅允许各新增一个 CSA / prefix 外部模块注释，去掉这两个精确注释后须等于旧原件。
3. **LogPerfEndpoint。** 原 parent-v3 既有的三个完整独立日志块比较函数原样沿用：只允许固定三块的对象标签及3!排列；条件、完整格式、参数、区域外文本仍逐字节相同。没有新增日志例外。

其余保留的父级、ClockGate、DIV、顶层 SV/V 逐字节等于旧父级。新 wrapper 不与 FU/cost wrapper 全文硬比；不同边界本就有不同控制字段裁剪。真实生成物一律不改写，所有实际 SHA、比较与变化范围保存至 `generation-boundary.json`。

## 资源、失败与资格

复用原 process helper、单 worker、CPU1、absolute nice5、Java ActiveProcessorCount1/SerialGC、Verilator5.052、显式 Clang/make/ar/link、j1。这个 worker 与原 CPU1 作业共享资源，不能宣称零竞争。总预算上限1200秒，包含预检、编译、生成、检查和最终身份审计，外层另留60秒有限回收余量；各步骤沿旧 parent-v3 的较小子预算。1200秒是执行截止，不是开发工作总时长承诺。

每个子命令独立进程组并记录 argv、PID、退出码、时间和原始日志；取消/超时通过原 helper TERM/KILL/reap，最终须确认全部子进程回收。运行身份、完整 overlay、基础 classpath、工具和生成物前后核验成功后，才可写 `PREFIX_REAL_PARENT_PASS` / `parent_qualified=true`。

第一次真实生成若超出上述有限边界、预期成功项失败、负控不成立或超预算，保留全部输出并分类诊断；不自动加时、扩大文本忽略、替换旧 checker、换对象重跑或扩矩阵。是否修复自己的明确实现缺陷由主端根据实际证据重新判断，不将本测试变成无限追加工作。

即使通过，也仅新增该实际 prefix 源码在真实父级已解码请求边界内的功能资格。`fullcore_qualified`、`application_performance_qualified`、本次 `cost_qualified` / `core_cost_qualified` / `performance_measured` 仍为 false；不改变旧 f149 EMU、生产默认、现有1ns负slack或50%应用目标状态。原 CSA/prefix 的局部成本结果继续独立引用。

调用入口保留旧参数形状，`--local-root` 指向实际 prefix local-01，`--local-result-sha256` 必须为上表完整结果 SHA，`--output` 为全新隔离目录；资源与原作业状态须在执行前核实。
