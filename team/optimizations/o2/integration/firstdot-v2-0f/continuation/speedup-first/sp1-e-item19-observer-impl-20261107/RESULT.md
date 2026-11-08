# 第19项最小观察器实现与宿主验证（记录104）

**结论：实现与宿主核查GO；目标诊断及正式第19项HOLD。** 正式进度仍19/20；第20项已有PASS保持；默认0f＋firstdot V2＋原C8不变。本轮只在独立四文件overlay增加默认关闭观察器，没有改生产或旧SP1候选。

|核查|结果|证据|
|---|---|---|
|四文件Scala/Chisel编译|PASS|COMPILE.json|
|默认关闭/依赖旗标拒绝|6项PASS|FLAG_TESTS.json|
|真实模块开关两态局部elaboration|6模块×2态=12次PASS|LOCAL_ELAB/EXU_ELAB_R2/ROB_ELAB.json|
|功能投影与旧消息格式|6对PASS，结构层级|NEUTRALITY.json|
|微操作身份及握手正负控|7组PASS|host-tests-final.log|
|生产445/旧候选398源码与历史443输入|全部未变|PRESERVATION.json|
|全核构建/EMU/NEMU/EDA|本轮均未执行|权限边界保持|
|新的加速比/面积/时序|NOT_TESTED|METRICS.json仅沿用历史|

代码、解析器、局部harness与失败留档均在本目录。中性检查不是RTL事件仿真或形式证明，LogPerfEndpoint只比较旧消息格式多重集；新EMU全核中性仍需后续验证。初版空日志漏洞、负控夹具未命中及两次harness配置失败均保留，修复后的当前检查通过。

## 历史三项指标（不是新观察器实测）

|指标/合同|0f基线|SP1一拍候选|
|---|---:|---:|
|chain-256 d0/d1/d2，RVV/VDOT窗口平均cycles|2.929725×|3.397658×|
|batch d0/d1/d2，同镜像窗口|3.067873×|3.067873×|
|原C8 reuse d0/d1/d2，同镜像窗口|1.095238×|1.099265×|
|FU映射面积，μm²|17298.246|18322.878|
|含DIV真实父级映射面积，μm²|284614.946|285241.642|
|nominal FU Q，ns|1.268520|1.790381|
|nominal父级Q，ns|3.393998|3.337809|

面积/时序为历史Nangate45同约束边界结果；Q沿用T−最差setup slack的定义，不能当全核实际周期。完整18格历史窗口和五档STA保存在METRICS.json，包括退化和负slack；本轮未新增或改善这些数值。

## 为什么仍HOLD

观察器已经能在源码和局部结构层取得所需时序信息，但尚无新EMU真实日志，不能证明FEX0竞争、P入队或P-only取消已命中。打印开销也尚未测，旧M1的583.11秒不能给出新观察版900秒完成保证。全日志/解析资源和运行闭包需在独立构建后评审。不能把本轮实现通过写成20/20，也不能切换默认。

下一步建议一次独立观察EMU构建及诊断准入；本轮只提出3600秒构建停止上限，未启动。目标仍待独立合同和后续授权，不改M1、不扫描phase。详见[NEXT_STEP](NEXT_STEP.md)、[具体改法](IMPLEMENTATION.md)、[预算评审](BUDGET_REVIEW.md)、[命令及失败留档](LOCAL_COMMANDS.md)。
