# 第19项构建入口 R3：HOLD（记录108）

本轮完成串行入口草稿和必要宿主检查，未获全核构建准入。正式验收仍为19/20，默认0f＋firstdot V2＋原C8。没有新EMU；用户授权的3600秒全核构建预算使用0秒。

## 实际完成与停止点

|内容|结果|证据边界|
|---|---|---|
|冻结编译缓存复核|PASS|10,326文件一致，未重编全核|
|Java参数一致、firtool参数一致、错参数/错目录拒绝|4项PASS|仅宿主命令映射|
|独立闭包小样编译|PASS|4.044秒；不是RTL功能验证|
|原SystemVerilog小样展开|FAIL|2.034秒，返回1，进程组已回收|
|CHIRRTL小样与FIR/附属文件/SV等价|NOT_TESTED|前一步失败即停|
|完整源码副本、全核冻结及构建|NOT_STARTED|未创建build-03，未接入实际Make|
|EMU/NEMU、EDA、默认切换、上传|未执行|保持用户边界|

直接错误为 `Key LogUtilsOptionsKey is not defined in Parameters`。我编写的小样直接实例化MinimalConfig，遗漏原ArgParser补入日志/性能配置，这是宿主夹具问题，不是硬件回归失败。没有修复后重跑。失败源码、HOST.lock和回执全部保留。

## 串行方案与尚未解决的风险

入口草稿先等待JVM退出，再核对FIR与附属文件，然后独立firtool；最终返回原Make后处理。四项参数检查证明命令映射没有改动其他选项，但实际闭包仍未验证。旧监督器只复用于本轮宿主监督，尚未成为完整R3构建入口。

静态读取本地Chisel字节码发现：常规CIRCT序列化变换后的FirrtlCircuitAnnotation，而CHIRRTL早返回所保留的CircuitSerializationAnnotation来自更早的Chisel内部Circuit。因此必须证明香山PrintModuleName/PrintControl和注解仍保留，不能直接以换target参数作为构建准入。当前只确认存在风险，未测出动态不等价；详见[设计评审](DESIGN_REVIEW.md)。

## 版本及保护

基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；分支 `local/zjhwork-integration-20261024`。源码24,595项、外部依赖18,061项、保护输入456项复核无变化；逻辑Git index一致；当前宿主源码冻结和10,326项缓存均无漂移。R1/R2的RSS失败、锁和部分生成物保留，不复用其不完整闭包冒充新成功。

本轮记录时间：2026-11-07T22:20:37.015103+08:00 ～ 2026-11-07T22:25:54.013149+08:00；不是人工工时统计。@cc77-builder / Agent（会话身份）。没有源码提交或远端更新。

## 三项指标

本轮加速比、面积、时序均为NOT_TESTED。历史18个工作负载及五档STA完整保留在[指标表](METRICS.md)和[JSON](METRICS.json)，不能用于宣称新观察EMU通过。代表历史值：chain候选3.397658×，默认2.929725×；FU面积候选18322.878μm²，默认17298.246μm²；nominal FU Q候选1.790381ns，默认1.268520ns。Q不是整核时钟，历史负slack保留。

## 下一轮

开始第19项构建入口R3-R1：修复闭包小样的参数初始化，使用原ArgParser路径，复用已通过的参数和缓存证据，集中核查FIR、注解、尾部附属文件及小样生成结果。存在真实序列化差异就HOLD，不绕过变换或弱化比较；全部准入后接入完整冻结与原Make后处理，同轮执行一次独立3600秒总预算构建，保持16GiB上限。保留原FAIL与锁，失败即停、不重试、不加时；不运行EMU/NEMU、不改RTL或镜像、不做EDA、不切默认、不上传GitHub。

[完整接续说明](NEXT_STEP.md)。本轮停止后只做只读归因、输入核查和文档收口，没有再执行生成或构建。
