# R3 只读门控审查（2026-10-24）

源码：4669c487f3024ee5fce514c37270297f99066b2a；参考分支对象：James_Hotten 的 b806ce9c。
本轮只读源码、归档 RTL 和真实父级原始日志；未执行 RTL、全核、综合或功耗仿真，未修改仓库。
复算入口：audit_trace.py；机器结果：gate-trace-audit.json。

## 结论

优先候选是 **O2 共享 DIV 被取消后清除时钟保持位**。这不是 vdot 吞吐缺陷，也不是新的算术优化。现有 O2 vdot 占用门控已正确覆盖两槽、取消清理、反压和复位；不应为复用旧 O1 补丁改回单事务时钟保持逻辑。

此缺陷已在当前 H1 封存父级数据中实际观测到，James 的历史 O2 移植有失败→通过证据。适合下一轮做最小移植和局部重验；目前尚不能把历史 James PASS 当成“当前 O2＋H1＋门控修复”验收。

## 当前时钟与生命周期

以下行号对应上述当前源码。

- ExeUnit.scala:93–153：每 FU 的 uncer_en_reg 在 in.fire 置位、out.fire 清零（124–128），复位初始化为零（98）；没有取消清零路径。其组合使能在134–136，真实 ClockGate 接在149–150。
- ExeUnit.scala:85–91,138–143：O2 vdot 使用真实 pValid/rValid 占用，不用 uncer_en_reg 决定时钟；使能为 occupied || in.fire || reset。
- VDotElastic.scala:59–70,94–107：以 ROB needFlush 分别取消 P/R；liveP/liveR 屏蔽被取消或复位事务；输出在取消当拍撤销，下一有效边沿清掉实际 valid。P/R任一旧槽有效仍给该清理边沿；部分取消的幸存者继续时钟。反压时 R 保持，P 在 R 可接时移动；输入只在有空间且无任何 redirect/reset 时接受。
- ExeUnit.scala:158–176：DIV使用独立 divBusy/divRobIdx。取消先清divBusy，响应完成也清；此外还等待divOutValid消失且两个真实DIV都ready，才允许新FU接入。取消和完成都不允许跨FU同拍切换。
- ExeUnit.scala:290–323：仅选中FU接收，禁止redirect/reset当拍接收；vdot未排空不能切DIV，DIV未完全可用也不能接vdot。
- VIDiv.scala:25–47；VFDivSqrt.scala:51–87：DIV将已保存事务ROB的needFlush送到内部除法器，取消可能需要真实边沿；取消当拍的旧out.valid允许暂时存在，不能当作已经完成的新事务。父级取消清divBusy不等于可以省掉这个清理边沿。
- VDotElastic.scala:97–107：乘积/控制寄存器只在in.fire写入，R包只在move时写入，数据写使能已存在。138–146的复位/保持断言属于实际门控时钟域，改变停钟时机也会影响这些监测状态。
- 真实ClockGate为低电平透明锁存TE|E再与CK相与（H1归档parent-map-01/ClockGate.original.sv:9–13）；不能组合直接与时钟替代。
- 现有父级测试Generator:82–83、parent_test.cpp:358–363,458–476明确：VDot覆盖TE=0空槽/非空/取消重合复位，历史DIV bootstrap/reset仍用TE=1。不能声称当前已证明DIV在TE=0所有复位模式下可恢复。

## 从归档重新计算的证据

本次校验H1封存manifest的压缩与原文SHA256/长度、James files.json对应Git blob字节，并解析实际O2_PARENT_CYCLE记录。当前ExeUnit、VDotElastic、VIDiv、VFDivSqrt、parent_test.cpp、GenerateVDotElasticParent.scala六文件均与H1父级source.json哈希一致。

H1输入：
team/optimizations/o2/result-width/h1/evidence/20261021-local/files/parent-01/result.log.gz

James历史O2输入（在b806ce9c读取）：
team/evidence/o2-o3-integration-20261020/parent-green-01/result.log.gz
team/evidence/o2-o3-integration-20261020/parent-red-01/result.log.gz

| 指标 | 当前H1封存运行 | James历史O2 green |
| --- | ---: | ---: |
| 总父级周期 | 34356 | 34356 |
| 接受/响应/取消/复位丢弃 | 13515/13037/418/60 | 相同 |
| 36组DIV取消后的108拍采样中仍有被取消DIV时钟 | 72 | 0 |
| 其中整数DIV / 浮点DIV | 36 / 36 | 0 / 0 |
| VDot真实时钟边沿 | 14851 | 14851 |
| VIDiv真实时钟边沿 | 12875 | 11094 |
| VFDiv真实时钟边沿 | 9078 | 7535 |

34356帧的所有非clocks事件字段逐帧一致；DIV边沿总计少3324。它们不是新版本的同机功耗实验；James green仍是H1前的128位R存储，其硬件、工具、其他源码身份须保留。上述比较说明已归档控制刺激与架构事务事件一致，不能代替完整数据/元数据重新验收。

当前parent_test.cpp:445–453在36组DIV取消后各观察3拍，但仅增加cancelIdleClockOn；没有要求其必须为零。封存PASS因此可以同时带cancel_idle_clock_on=72。这是已知检查缺口，而非功能PASS伪造。现有最终clock-recovery用正常完成再关钟，不证明取消后立即关钟。

James严格red运行在cycle=13330观测VIDiv已空闲、busy=0、ready=1但clocks=2，随后tick=13331报“canceled DIV retained idle clock hold”；green对应强约束通过。b0c8a54a最初修的是单事务VFEX4模式；769b3b4b移植后，当前James源码使用DIV专属cancel信号，才适合O2。

## 修复为什么可行，不能怎样直接搬

James b806ce9c ExeUnit.scala:88定义cancelVFEX4Clock；128–136清不定时延保持位；174绑定divBusy && divRobIdx.needFlush(io.flush)。146–151保留原O2占用门控。旧单事务模式另在198–199绑定busy/robIdx。

建议第一轮只移植 **O2 DIV对应小块** 和相应测试要求：
1. 父级独立DIV取消条件复用已有divBusy/divRobIdx，不添加第二套ROB身份。
2. 取消发生时，旧uncer_en_reg仍为1，让真实DIV获得清理边沿；边沿后清零，下拍空闲关闭。
3. 下一次真实in.fire仍能唤醒。非取消redirect不可清正在执行DIV的时钟。
4. O2的VDot两槽门控及legacy默认/T14/O1路径保持原实现。若选择同时改legacy路径，应另外验证这三个模式，不能把O2证据外推。
5. 不直接cherry-pick完整b0c8a54a：它还加入O1观察器、ROB与构建改动，且原始取消条件基于一个busy/ROB；单事务条件不能替代O2两槽身份。
6. 不用“io.flush.valid就关钟”；必须匹配正在执行DIV的ROB，并保留清理边沿。

## 后续最小验证

第一阶段局部验证即可决定是否保留候选，不必立刻启动新的全核长跑：

- 当前H1旧版＋严格cancel-idle门禁先产生预期失败；候选用同一生成器、同一10022向量、同一刺激通过。
- 36组DIV取消覆盖计算中、可见响应、响应背压，out.ready两值及下一FU三种；取消后空闲至少3拍并继续新请求，逐FU计数都为零。
- 加入非取消redirect、ROB flag环绕、取消与reset重合、取消后DIV→VDot/另一DIV恢复；既有原始取消当拍out.valid规则保留。
- 保持当前两槽部分取消、满队列背压、R完成而P幸存、II=1、初响应2拍、完整128位数据/身份和16类读回负控。
- 当前测试requiredClocks假设占用期间必须有时钟，这与本DIV取消修复不冲突；如果做下面的VDot停钟探索，则必须另立监测合同，不能简单放松旧检查。
- 局部通过后，以候选新硬件身份做受影响全核正常/异常/控制/NEMU差分与周期不退化；不能挪用H1旧EMU冒充修复候选。
- 要宣称PPA，另做同工具同约束的结构/时序；要宣称功耗，需要同负载活动数据和电容/库功耗模型。边沿计数只能叫门控活动改善。

## 暂缓的方向

### VDot反压期间进一步停钟

当前占用门控在P/R有数据时持续开钟，即使整拍不接受、不移动、不完成也不取消。本次封存迹线可筛出872拍这类“功能事务状态未前进但VDot有时钟”的记录，其中双槽559、仅R313。这只是诊断性可省边沿上界，不是候选实现收益；其中存在redirect或断言监测状态，不能直接删掉所有边沿。

这条路线要把ready、kill和reset等事件纳入门控使能，增加门控时序路径和验证负担；现有数据寄存器已经有写使能，收益主要是时钟网络活动。建议排在DIV取消修复后，待代表性应用证明确有大量长期背压再立项。不要宣称能提高II或缩短CPU周期。

### 乘法器输入隔离

VDotElastic.scala:78–79将父级源操作数直接接到组合VDotProducts。关FU时钟不会阻止前端组合乘法器因输入变化而翻转；加入有效请求隔离可能降低无效翻转，但需新增门逻辑并评估输入到乘积寄存器的延迟。当前没有门级/RTL活动分布或功耗证据，不宜先写“节能比例”。优先只做有效/无效输入切换统计；若总动态活动主要来自不相关DIV、无效周期输入变化，再试一个候选。

## 适用边界

本轮不是R3 RTL实现，不改变T17固定输入或现有EMU。最有把握的下一步是小范围DIV取消门控与严格门禁，其价值是工程完整性、验证严谨性和减少无效活动；没有证据说它直接提升赛题cycle加速比。

## 可移植复算入口与本轮复算记录

audit_trace.py现在要求显式--repo和--output；输出路径必须不存在，不会覆盖已封存证据。依赖Python标准库、Git，以及本地可读的两个固定提交：

- 当前基线：4669c487f3024ee5fce514c37270297f99066b2a
- James参考：b806ce9c9c5228f6512474c7f2c3ab917349d7a6
- H1 manifest SHA256：73fe5f79d3209937a3278a16f8bfc70f90333fc46657de161810bcf9c2d8974a

脚本不会联网fetch；若本地缺少James对象，先由维护者明确取得该提交后再执行。脚本校验当前六项输入仍与固定基线和H1归档一致；仓库HEAD可包含后续纯文档提交，但硬件/检查器漂移会拒绝。脚本拒绝-O、-OO和等价PYTHONOPTIMIZE，避免绕过断言；PASS要求两条迹线长度相等且所有非clocks字段无差异。

本轮实际命令（输出目录执行前不存在）：

~~~bash
python3 -B /home/riscv/riscv-lab/o2-r3-readonly-20261024/gating/audit_trace.py --repo /home/riscv/riscv-lab/zjhwork2-review-20261018/repo --output /home/riscv/riscv-lab/o2-r3-readonly-20261024/gating/recheck
~~~

退出码0，状态R3_READONLY_GATE_TRACE_AUDIT_PASS。命令、脚本SHA和退出码在recheck-command.json，stdout/stderr各自归档；重新计算结果在recheck/gate-trace-audit.json。后续复现应给新的输出目录，不可重复使用recheck。James差异只导出为patch供阅读，从未应用。

另以-O和已存在输出目录分别检查拒绝路径，均非零退出，原recheck文件哈希未变，-O未创建输出目录；见recheck-guards.json。这些是主机脚本检查，没有新的RTL/全核/综合运行。

附带的 james-exeunit.patch 是两个固定历史提交的源码差异，供阅读核查，未应用，也不是建议直接合入的最小修复补丁。
