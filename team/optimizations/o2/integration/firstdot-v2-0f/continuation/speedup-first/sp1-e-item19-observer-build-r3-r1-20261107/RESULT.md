# 第19项构建入口 R3-R1：HOLD（记录109）

已修复小样参数初始化，确认“只把target改为chirrtl”存在真实序列化差异；按合同停止。正式19/20，默认0f＋firstdot V2＋原C8不变。全核构建0次，3600秒预算使用0秒。

|检查|结果|实际证据|
|---|---|---|
|冻结输入、旧失败与复用脚本|PASS|源码24,595、外部18,061、保护456项；前后无漂移|
|原ArgParser配置初始化|修复生效|两条生成路径都越过上轮LogUtilsOptionsKey错误|
|参数一致、错误参数/路径拒绝|4项PASS|原检查器和适配器未改|
|小样Scala编译|PASS|3.593秒，返回0|
|原SystemVerilog小样生成|PASS|2.046秒，返回0|
|CHIRRTL小样生成|PASS|2.053秒，返回0|
|FIR打印模块身份等价|FAIL|ClosureTop变为r3host.ClosureTop@63da207f|
|已有输出的注解与尾部文件离线检查|部分一致|5条内嵌注解、6个尾部文件一致；不能覆盖FIR失败|
|独立firtool/完整闭包/全核构建|未执行|前置失败即停，不重试|

本次不是夹具再次无法启动，也不是内存超限。两个JVM都正常完成，原入口输出稳定模块路径，而CHIRRTL输出仍含JVM对象标识。除了语句名和空行，printf字符串本身确实不同。故不能把它作为原入口等价替代；这也不证明VDOT算术错误或性能下降。

根因：CHIRRTL的序列化来源没有保留香山PrintModuleName对FirrtlCircuitAnnotation的修改。详见[差异分析](SERIALIZATION_ANALYSIS.md)和[原始diff](FIR_SERIALIZATION.diff)。PrintControl其他行为尚未动态验证，不夸大证据。

本轮宿主门总耗时7.705秒，各子进程已回收。未运行EMU/NEMU，未做综合/STA，未改生产RTL或软件镜像，未切默认，未上传GitHub。旧R3及R1/R2失败不覆盖。

## 版本与指标留档

基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；本地分支`local/zjhwork-integration-20261024`。工作记录2026-11-07T23:08:59.173824+08:00～2026-11-07T23:13:07.536751+08:00，@cc77-builder / Agent（会话身份；非人工验收或工时统计）。

本轮加速比、面积、时序均NOT_TESTED；历史三项指标完整保存于[指标表](METRICS.md)和[JSON](METRICS.json)。例如chain候选3.397658×、默认2.929725×；FU面积18322.878/17298.246μm²；nominal FU Q为1.790381/1.268520ns，均为既有同口径数据，不能作为本轮新观察EMU成绩。

## 下一轮

开始第19项构建入口R4：在独立宿主工具中导出香山变换后的FIR及完整注解，复用原ArgParser、FileRegisters和Make后处理，不修改生产RTL。先完成小样闭包、参数和输出等价验证；全部准入后执行一次3600秒总预算、16GiB有界构建。保留原FAIL，失败即停、不重试、不加时；不运行EMU/NEMU、不改软件镜像、不做EDA、不切默认、不上传GitHub。

[完整接续合同](NEXT_STEP.md)。下一步重点是导出变换后的电路及注解，不再重复只改target的方案。
