# SP1-C/D 新EMU与有界chain-d0探针结果

2026年11月4日，UTC+08:00；执行者@cc77-builder / Agent，工作跨11月3日至4日。记录ID SP1-CD-CHAIN-D0-20261104-01。

**SP1-C通过；SP1-D在第3角色后的跨硬件退休记录公平检查失败，整轮STOPPED/HOLD。** 实际仅3个目标，两个重放均未启动。候选观测均值1601.25 cycles、RVV/vdot=3.397658×，相对同批0f的1857 cycles观测减少13.772213%；这组数值尚未取得最终公平及重放资格。

## 1. 三项主指标与资格

| 版本/本轮资格 | RVV平均cycles | vdot平均cycles | 观测RVV/vdot | FU面积μm² | 含FU父级面积μm² | nominal setup FU/父级ns |
| --- | --- | --- | --- | --- | --- | --- |
| 0f，单次正常对照通过 | 5440.5 | 1857 | 2.929725× | 17298.246 | 284614.946 | −0.268520 / −2.393998 |
| SP1一拍候选，公平/重放未验收 | 5440.5 | 1601.25 | 3.397658×（未最终合格） | 18322.878 | 285241.642 | −0.790381 / −2.337809 |


表中cycles是本轮各自完整正常运行的真实窗口均值；跨硬件正式比较被门禁拒绝，不把观测差值冒充已验收收益。面积和时序是原G2 trace关闭功能硬件的历史复用，本轮没有新增综合/STA。候选C8加速比NOT_TESTED；稳定0f旧C8的299/273=1.095238×不能转借给候选。稳定选择仍为0f＋firstdot V2＋原C8，用户最终选型待定。

## 2. 已完成内容与身份

复用SP1-A/B的原P4 G1＋SP1观察器，本轮没有改RTL。新增显式候选根的构建入口，隔离cwd/NOOP_HOME/DESIGN_DIR/Mill及build输出，禁止PGO隐藏目标运行。预冻结25962项不可变构建输入，构建退出0并清空进程组；中断后核实已有成果，未重复构建。1688生成文件匹配，21项真实配置审计及24项独立准入通过。

MinimalConfig单核，VLEN128、ROB48、FTQ8；一拍算术、双槽。P4/O2/T14/SP1_TRACE/T13_TRACE启用，旧O2/O1/T12观察器关闭。运行器31项机制测试、checker43类宿主检查、真实supervisor→历史日志宿主播放→checker的12窗/6坏收据联调通过。它们只授宿主准入，不预授目标性能资格。

- 候选patch：e1842a5f52a27fda2bea30f791921d6acefd63c54b415912adb8a1e3438be682。
- 新EMU：e34b2eaa8deb99f83534478217aaf144e32262ba08b2c18c31c6ac7265525c1e。
- 固定0f EMU：2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。
- 共同BIN：f80c53390aa7c913cff5b2a219b71b147355c93e09494a67b017e8dbf26460da。
- 共同ELF：644ebdc61e4e0023cd49a010a3b35fbc4cc670e092847d3acd330682a4df1f4b。
- 正常NEMU：efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4。
- runtime附录：0323087c2d359083df00c8a48fdb03951897467bba40387c5ffa901b19437d2e；执行冻结：94c949ac9e5f992d572b48ccfbd04d5e351def7e195db9f31b793e056edfbf5e。

## 3. 五角色计划的实际终态

| 角色 | 结果 | guest cycles | 目标墙钟s | 峰值线程 | 峰值RSS MiB | 日志B |
| --- | --- | --- | --- | --- | --- | --- |
| candidate-bit100 | NEGATIVE_PASS | 11059 | 22.475 | 1 | 72.625 | 44325 |
| candidate-normal-recovery | NORMAL_PASS | 119199 | 251.884 | 1 | 73.500 | 8971909 |
| baseline-normal-calibration | NORMAL_PASS | 120824 | 273.787 | 1 | 73.250 | 9227564 |
| candidate-replay | NOT_RUN | — | — | — | — | — |
| baseline-replay | NOT_RUN | — | — | — | — | — |


第一角色在PC0x8000114c/word0x0295050b的v10唯一注入bit100；DiffTest正确报对应高位mismatch并退出1。正常恢复和0f对照均使用原正常reference，各自GOOD TRAP、live DiffTest、完整12窗、CSR、1536次custom架构提交及完整128位结果通过；跨核提交源/完整结果摘要也相等。

角色3之后的冻结增量门禁拒绝cross_control_sha256，随后没有启动角色4/5。目标累计548.146秒/6300秒，总监督562.672秒/7200秒，日志合计18243798B/2GiB。全部CPU4，观测峰值1线程；独立资源审计66项通过，已用PGID全部消失，没有超限、未知清理、重试或加时。资源峰值属于约50ms采样证据，不是瞬时内核硬限证明。

## 4. 失败归因与记录边界

原始失败：`ValueError: cross-hardware PC/word/count/data/CSR cross_control_sha256`。

首条不一致位于全流index2743、RVV warmup窗：相同PC0x80002160、word0x001f0f13、data8，候选退休记录count=1，0f count=2。原摘要直接比较ROB压缩退休分组，后续事件索引因此错位；这不能直接等同于架构程序执行了不同工作量。详细逐窗展开、数据语义和源码依据见[只读归因](review/cross-control-failure-attribution.md)及同名JSON。

1328条按原记录索引比较的差异全部位于seq2 RVV warmup。按固定ELF和count展开后，12窗PC/word序列全部相等，按原合同排除计时计数器动态返回值后，各正式measured窗分组与其余data也相等。预热窗两边各1894个ROB记录、167个count2组；166次循环的压缩/拆分位置互换产生332处分组边界差异。展开包含窗口边界时为2061条逻辑指令，性能区间仍为2056条，二者口径不同。

对齐相同逻辑组后仅剩两处data：9/247、12/244，分别对应压缩ADDI对的t5递增值和t6剩余值，和均为256。Rob.scala的debug_exuData按ROB索引接收写回覆盖，压缩组共享索引，单个调试值不能固定解释为第一条PC的唯一架构写回。因此原跨核比较错误地把合法ROB分组和非唯一调试值当作跨硬件不变量。完整1536次点积提交的源和128位结果摘要相等，未见该差异对应架构结果错误。

只读归因用于确定下一轮修订范围，未修改冻结checker、旧合同、原始日志或STOPPED结果，也没有补跑两个重放。即使可解释分组差异，当前正式性能仍HOLD；下一轮应先补宿主正负控并冻结新口径。

## 5. 本轮24窗观测

| seq | 阶段/重复 | 方法 | 0f cycles | SP1 cycles | 退休指令数 |
| --- | --- | --- | --- | --- | --- |
| 0 | first/0 | vdot | 1889 | 1636 | 1032 |
| 1 | first/0 | rvv | 5448 | 5448 | 2056 |
| 2 | warmup/1 | rvv | 5440 | 5443 | 2056 |
| 3 | warmup/1 | vdot | 1858 | 1602 | 1032 |
| 4 | measured/2 | vdot | 1857 | 1601 | 1032 |
| 5 | measured/2 | rvv | 5440 | 5440 | 2056 |
| 6 | measured/3 | rvv | 5441 | 5441 | 2056 |
| 7 | measured/3 | vdot | 1857 | 1601 | 1032 |
| 8 | measured/4 | vdot | 1857 | 1601 | 1032 |
| 9 | measured/4 | rvv | 5441 | 5441 | 2056 |
| 10 | measured/5 | rvv | 5440 | 5440 | 2056 |
| 11 | measured/5 | vdot | 1857 | 1602 | 1032 |


正式观察均值只用repeat2～5，每方法4窗；first/warmup单列。vdot每窗1032条退休指令/256条custom，RVV2056条/0条custom。本核各自正确性已验证。观测RVV均值两边均5440.5，观测退化0%；AB/BA数值减少分别13.785676%/13.758751%。由于公平门禁失败且重放未执行，本节只是数值留档，不能标注PERFORMANCE_PASS。原始数据另存observed-24-windows.csv、OBSERVED_METRICS.json。

候选1536次实际响应均为接受后1拍，主接受间隔6拍；0f的直方图见RESULT.json。这说明一拍候选的局部机制确实在全核执行，但最终可采用的收益仍需后续合同验证。

## 6. 面积、五档时序与原失败

FU面积18322.878μm²，较0f 17298.246增加5.923329%；完整父级285241.642μm²，较284614.946增加0.220191%。原G2 trace-off实现与SP1-A/B关闭生成物核对后复用。新SP0成本预算47/47通过，旧G0六项FAIL及NO-GO保持。

| 档位 | 参考周期ns | 负载fF | FU Q/ns | FU setup/ns | 父级 Q/ns | 父级 setup/ns |
| --- | --- | --- | --- | --- | --- | --- |
| nominal | 1.0 | 5.0 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5.0 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5.0 | 1.790381 | +0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1.0 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20.0 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |


Nangate45 Typical、1.10V、25°C，五档与原工具/边界一致。全部arrival/required/slack、关键路径起终点、ready与gate_enable数据保留在METRICS.json，五档CSV亦保留。1ns负裕量未隐藏；这些是布局前局部代理，不能当作全核Fmax。SP1_TRACE=1诊断电路面积/STA及本轮实际芯片频率均NOT_TESTED。

## 7. 归档与下一步

保留构建入口初审漏项、宿主接口/门禁修订与测试初期FAIL、生成物审计正则漏数字4的误报。正式目标本轮保留1项跨硬件公平门禁FAIL，两个NOT_RUN；不因之后的离线解释回填PASS。原48条版本档案不覆盖。

下一步为SP1-C/D-R1宿主修订及新合同，见[NEXT_STEP.md](NEXT_STEP.md)。本轮无RTL修改、无默认切换、无GitHub写入。原始命令、资源采样、日志、退出码、哈希及分析源由[evidence-manifest.json](evidence-manifest.json)索引。
