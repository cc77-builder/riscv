> 2026-11-08 `zjhwork2` 发布说明：本分支集成已验收的原 SP1 四文件与显式构建配置，firstdot V2＋原 C8 不变。`zjhwork` 保持原位。以下各轮“默认未切换／未上传”为执行当时的历史状态，参见 [SP1_RELEASE.md](../../SP1_RELEASE.md)。

# 香山 vdot 工程开发路线：满足赛题技术要求，持续提高性能

## 当前执行计划 SP0～SP6

**记录120：SP1-E最后第19项通过，冻结矩阵20/20，GO可供用户选用。** S0/S1实际覆盖、中性、完整数值和原镜像精确重放完成，无待补第19项探针。默认仍0f＋firstdot V2＋原C8，未上传。

建议加速比优先选择原SP1一拍两槽版；四文件源码/补丁/配置已准备。主目录未采用P4-R1不能误当候选。用户选型后再集成默认及发布。chain3.397658×，FU面积+5.9233%、父级+0.2202%，FU局部时序退化保留；新SP0成本47/47通过，非全核时钟签核。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/RESULT.md) · [矩阵](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/MATRIX.md) · [三项指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/METRICS.md) · [候选包](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/release-candidate/README.md)

## 历史路线与完成记录

### 记录115当时执行状态（历史原文保留）

**记录115：第19项观察EMU诊断准入HOLD，目标0次，正式19/20。** 默认0f＋firstdot V2＋原C8不变；记录114新EMU构建PASS保持。新旧输入、8动态库及实际观察点身份核对通过，但完整日志/目标开销依据和流式适配尚缺；只读格式分析脚本类型假设错误FAIL已保留。

下一轮集中修静态格式估算、收紧整批完整日志界、完成流式投影/侧带检查器及必要负控和宿主成本。原两角色300/900秒、整批2GiB不变，全部准入才运行；依据不足HOLD，不自动把诊断预算改成校准。目标、RTL、镜像、构建、EDA、默认及GitHub均未动。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-20261108/RESULT.md) · [预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-20261108/BUDGET_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-20261108/NEXT_STEP.md)



### 记录114接续（构建PASS保持，诊断预算待收口）


**记录114：新观察EMU构建PASS，构建阻塞解除；第19项诊断待准入，正式19/20。** 默认0f＋firstdot V2＋原C8不变。15项宿主、8项冻结通过；单次851.429秒/7.481GiB完成后处理、Verilator与原生编译，新EMU `fc25f9e2a22cc1c51e4a4884c03c6d84e950fcbb1925eb55a448de104273f742` 已固定。目标运行0次，无新三项性能/成本测量。

下一轮集中两角色诊断准入：复用原M1镜像与旧证据，只补新身份/侧带/投影/bit100差异及预算；全部通过并新授权后300/900秒诊断。依据不足HOLD；未命中保留，不能据诊断授予正式PASS。不自动M2、重放、切默认或上传。旧FAIL保持；构建单调/UTC时间差异另存，不授UTC一致性资格。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-r1-20261108/RESULT.md) · [缺项说明](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-r1-20261108/WHY_ITEM19_IS_PENDING.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-r1-20261108/NEXT_STEP.md)



### 记录113接续（LF已修复，观察EMU已构建）


**记录113：R4-R3 Git目录修复PASS；安全接续宿主检查器LF语义FAIL，整体HOLD，正式19/20。** 默认0f＋firstdot V2＋原C8不变。629目录补齐、127Git仓库可识别、1687生成物已备份；实际完整构建0次，3600秒预算0秒。

下一轮R4-R3-R1仅修宿主检查器LF分行并保留裸CR，使用现有小样真实输出补齐正负控、完整冻结；全部通过后一次3600秒/16GiB剩余构建，不重复JVM/firtool。原Make与RTL不变，原FAIL和锁保留，不自动运行目标或切默认。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-20261108/RESULT.md) · [归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-20261108/LF_SEMANTICS_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-20261108/NEXT_STEP.md)



### 记录112接续（Git目录已修；接续检查器LF模型待修）


**记录112：R4-R2解析/冻结PASS，真实FIR/SV生成PASS；原Make Git目录闭包失败HOLD。正式19/20。** 默认0f＋firstdot V2＋原C8不变。一次构建490.888秒、峰值9.692GiB，未触发3600秒/16GiB上限；未产生新EMU，未进入原生编译。原FAIL、锁与生成物保留。

下一轮R4-R3只补副本遗漏Git空目录并验证原Make后处理的安全接续，复用已过10＋6证据、本轮解析检查及FIR/SV，不重复JVM/firtool。禁止直接用已有SV跳过未完成后处理。新准入与独立预算后才剩余构建；不自动运行目标、不改RTL或镜像、不切默认、不上传。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r2-20261108/RESULT.md) · [归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r2-20261108/GIT_DIRECTORY_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r2-20261108/NEXT_STEP.md)



### 记录111接续（解析已修复；生成完成但原Make后处理失败）


**记录111：R4-R1宿主闭包10项、适配器6项通过；冻结续行解析失败HOLD，正式19/20。** 默认0f＋firstdot V2＋原C8不变。重复侧文件已解决，独立build-03/source共24,596文件完备；Make干跑成功，完整输入冻结尚未完成，无全核构建或生成输出。

下一轮R4-R2只修复反斜杠续行的逻辑命令解析，复用现有干跑日志/10+6通过证据/源码副本，补齐冻结后一次3600秒/16GiB构建。旧FAIL和锁保留；不重编小样或重复已过门，不自动运行EMU/NEMU，不改RTL/镜像、切默认或上传。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r1-20261107/RESULT.md) · [归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r1-20261107/FREEZE_FAILURE.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r1-20261107/NEXT_STEP.md)



### 记录110接续（侧文件已修复，冻结尚未完成）

**记录110：R4默认FIR与原生成文件一致，重复注解侧文件导致闭包HOLD；正式19/20。** 默认0f＋firstdot V2＋原C8。独立导出解决R3-R1变换丢失，完整FIR、原10个RTL目录文件及6个尾部逐字节一致；额外ClosureTop.anno.json与FIR注解重复，已失败即停。disable-all未运行，完整构建0次/0秒。

下一轮R4-R1仅抑制导出完成后的隐式注解侧文件请求，保留FIR内注解和独立firtool原参数。复用通过证据，完成必要闭包/PrintControl检查；全部通过后完整冻结、一次3600秒/16GiB构建。原FAIL和锁保留，不自动目标运行，不改生产RTL/镜像、不切默认、不上传。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-20261107/RESULT.md) · [差异归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-20261107/SIDECAR_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-20261107/NEXT_STEP.md)



### 记录109接续（R4修复FIR内容，尚有侧文件差异）

**记录109：R3-R1确认真实序列化差异，构建HOLD，正式19/20。** 默认0f＋firstdot V2＋原C8不变。ArgParser小样参数修复，编译和两种生成均成功，但CHIRRTL保留JVM对象标识，未保留原PrintModuleName稳定模块路径；按合同停止，完整构建0次、3600秒使用0秒。

下一轮R4从实验目录的独立构建工具导出香山变换后的FIR及完整注解，复用原参数和尾部文件路径；小样闭包与参数等价通过才一次3600秒/16GiB完整构建。禁止只改target重跑、删除观察或弱化比较。原失败保留；不自动运行目标，不改RTL/镜像、切默认或上传。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-r1-20261107/RESULT.md) · [归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-r1-20261107/SERIALIZATION_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-r1-20261107/NEXT_STEP.md)



### 记录108接续（小样参数已修复，确认序列化差异）

**记录108：R3宿主夹具参数缺项HOLD，未启动全核；正式19/20。** 默认0f＋firstdot V2＋原C8不变。串行入口草稿、4项参数检查和小样编译完成；原小样展开漏掉ArgParser派生日志选项而失败，原锁与失败保留。3600秒构建预算使用0秒。

下一轮R3-R1修正小样参数路径，并集中验证FIR/注解与尾部文件闭包。静态发现CHIRRTL序列化可能不保留PrintModuleName/PrintControl，须验证而不能只改target强行启动。存在真实差异即HOLD；全部准入后完整冻结并执行一次3600秒/16GiB构建。仍不授权目标运行、RTL变更、切默认或上传。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-20261107/RESULT.md) · [设计评审](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-20261107/DESIGN_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-20261107/NEXT_STEP.md)



### 记录107接续（R3宿主HOLD，未进入全核）

**记录107：R2宿主与输入身份通过，实际构建RSS_LIMIT，诊断HOLD；正式19/20。** 默认0f＋firstdot V2＋原C8不变。一次构建已停止且全部回收，无新EMU，不能继续旧锁或借剩余预算。

R2消除了Mill父进程，剩余瓶颈是约10GiB生成JVM与firtool同时占用内存。下一轮R3评审并实现CHIRRTL生成→JVM退出→独立firtool→原Make后处理。先验证FIR及尾部附属文件闭包，准入通过后新的单次3600秒构建；保持16GiB。旧R1/R2失败保留，不改RTL，不自动进入目标。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r2-20261107/RESULT.md) · [资源归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r2-20261107/RESOURCE_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r2-20261107/NEXT_STEP.md)



### 记录106接续（R2已执行，仍RSS超限）



**记录106：R1宿主修复通过，实际构建因RSS_LIMIT停止，诊断HOLD。正式19/20。** 默认0f＋firstdot V2＋原C8不变。一次构建已使用，未生成可交付EMU，不得继续旧锁或借剩余预算重试。

峰值16.030GiB超过16GiB；Mill编译进程与展开JVM/firtool并存。下一步R2仅做分阶段宿主入口，复用已编译类以减少并存内存，保留原Make后处理和资源上限；新准入后才一次新的3600秒构建。索引stat缓存与源码冻结需区分，旧字节FAIL保留。三项指标本轮NOT_TESTED，原性能和PPA不变。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r1-20261107/RESULT.md) · [资源分析](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r1-20261107/RESOURCE_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r1-20261107/NEXT_STEP.md)



### 记录105接续（R1宿主已修复；构建资源HOLD）



**记录105：独立观察EMU构建准入HOLD；实际构建尚未开始。正式19/20。** 记录104观察实现资格保持，默认0f＋firstdot V2＋原C8及第20项PASS不变。

本轮独立源码物理副本已完成并核对，宿主监督器启动亲和竞态导致门禁FAIL后停止。实际构建0次，3600秒预算0秒；无目标、EDA、切换或上传。下一步仅修exec前亲和设置和夹具回执/failfast，补齐外部依赖冻结；通过后同轮一次有界构建。保留旧FAIL，不重复未变RTL验证。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-20261107/RESULT.md) · [下一轮指令](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-20261107/NEXT_STEP.md) · [两角色草案（未准入）](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-20261107/DIAGNOSTIC_CONTRACT_DRAFT.md)



### 记录104接续（构建入口宿主失败，未启动构建）



**记录104：最小观察器实现及宿主核查GO；新目标诊断和第19项HOLD。正式19/20。** 默认0f＋firstdot V2＋原C8不变，第20项PASS保持。

四文件仅位于独立overlay；完成编译、默认关闭、身份正负控及六模块开关两态结构中性，未做全核构建/EMU/NEMU/EDA。旧生产/候选/输入保持。没有新的命中或性能结果，不重复盲改M1或扫描phase。

下一步独立观察EMU构建和诊断准入：提议单次3600秒构建停止上限，先冻结完整树与资源；成功后核对新身份和日志成本。目标仍需新两角色合同及后续授权，本轮不启动。保留原覆盖和重放；最终默认选择由用户决定。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-impl-20261107/RESULT.md) · [预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-impl-20261107/BUDGET_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-impl-20261107/NEXT_STEP.md)



### 记录103接续（本轮已完成观察实现）



**最小观察方案设计GO；第19项定点修订/目标补测HOLD。** 现有证据不足以给出可信FEX0/VDOT碰撞窗口。正式仍19/20，默认0f＋firstdot V2＋原C8不变；第20项PASS保持。

记录103已完成当前设计：按实际FEX0/VFEX4仲裁、I2v/vialu拆分及前递路径，冻结四处最小观察方案。软件/镜像和所有源码保持；没有新目标、构建或EDA。不能继续盲改phase或用第20项保护代替第19项覆盖。

默认次序：先实现默认关闭观察器与必要宿主/局部中性，再据实际开销评审独立构建/一次诊断；获得可信碰撞窗口后才提出单一M2定点改法。任一环节依据不足HOLD，不自动扩围。正式覆盖与重放仍按原合同；最终默认选型由用户决定。

开始第19项最小观察器实现与宿主验证：按 DESIGN 和 OBSERVATION_SCHEMA，先说明四个 RTL 源文件的具体改法，在独立候选目录实现默认关闭的调度/写回侧带观察，保持原数据通路、仲裁、ready 和 SP1/T13 协议；完成微操作身份与时序解析正负控、默认关闭检查和必要局部观察中性验证，并评审构建及一次诊断的预算。保留 S0/S1 原覆盖和第19项 HOLD；先不构建全核、不运行 EMU/NEMU、不改软件镜像、不做 EDA、不切默认、不上传 GitHub。完成后给出 GO/HOLD 和下一轮指令。

[设计结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/RESULT.md) · [有界合同](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/BOUNDED_CONTRACT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/NEXT_STEP.md)。



### 记录102完成后接续（本次设计已完成，目标未启动）

第20项四角色 R1 已通过：候选正常、0f正常、候选重放和0f重放全部完成，九格配对及两次精确重放通过。正式验收由18/20推进到 **19/20**；第19项继续 HOLD。默认仍为 **0f＋firstdot V2＋原C8**，没有切换或上传。

本轮记录102：第20项四个新角色、九格2%门槛、两次精确重放全部PASS；每角色54窗/432算子覆盖完整，bit100复用。118项冻结/445生产与398候选源码未变，所有本轮目标已结束。

第19项继续按R5暂存，不重复M1、不扫描相位。建议下一轮仅做缺失时序观测与定点触发设计，先判断能否补齐冻结构建的FEX0向量写回请求、I2v/vialu释放与VDOT响应的相对时序证据；没有可信窗口仍HOLD。设计不等于允许改观察器或构建新核。

开始 SP1-E 第19项最小观测与定点补测设计评审：基于 R5 已冻结结论与现有候选构建，明确 FEX0 向量写回请求、I2v/vialu 释放及 VDOT 响应的相对时序缺口，先核对现有可见信号，再设计必要的最小观察补丁与有界触发合同。保留 S0/S1 原覆盖、完整结果、取消及精确重放要求；没有可信触发窗口就 HOLD。只做设计和成本评审，不改代码、不运行 EMU/NEMU、不构建新核、不做 EDA、不切默认、不上传 GitHub；完成后给出 GO/HOLD 和下一轮指令。

[记录102结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/RESULT.md) · [三项指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/METRICS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/NEXT_STEP.md)。


### 2026-11-07 记录101结束时的计划（已由记录102完成）

第20项四角色接入已实现，但宿主准入 FAIL，目标准入 HOLD。首6项方法通过，第7项负控错误选中首调用窗口，预期拒绝未发生；第8项未执行。遵守失败即停，本轮EMU/NEMU为0，正式进度仍18/20，默认0f＋firstdot V2＋原C8不变，第19项继续暂存。

本轮只改宿主接入；6项PASS，负控使用repeat0首调用而不是repeat2～5计分窗口导致第7项FAIL，第8项未运行。不是目标超时或RTL失败。81项冻结和生产445/候选398源码未变，当前没有目标进程。

下一轮第20项四角色R1：最小修复负控的语义窗口定位，复用6项证据，补受影响项与冷进程导入，再同轮四角色。新预算已接受，沿用每角色4800秒/200万guest、目标19200/宿主900/外层20100秒；不再重复预算设计。

开始第20项原镜像四角色 R1：按 NEXT_STEP 最小修复宿主负控的计分窗口定位，用 dataset/op/repeat 语义键唯一选择 measured 窗口并断言实际命中，保留原 FAIL 与锁，复用本轮6项通过证据及未变运行器。集中完成受影响测试、尚未执行的冷进程导入与授权拒绝检查、新执行冻结和宿主准入；全部通过后，同轮串行执行候选正常→0f正常，九格配对通过后执行候选重放→0f重放。沿用已接受的每角色4800秒/200万guest、目标19200秒、宿主900秒、外层20100秒预算及原资源、完整54窗/432算子、9格2%与精确重放门槛，复用bit100。失败即停、不重试、不加时、不扩围；不改RTL或镜像、不构建新核、不做EDA、不切默认、不上传GitHub，第19项继续暂存。完成后更新计分板并给出下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-20261107/NEXT_STEP.md)。


### 第20项原镜像四角色接入前的设计评审（历史）


**第20项原镜像四角色设计GO，宿主实现/目标准入HOLD。** 保留原ELF/BIN和0f/候选EMU，复用同身份真实bit100；不改输出格式。新批次拟为候选正常→0f正常→候选重放→0f重放；两次正常完整54窗及九格比较通过后才重放。

拟定各4800秒/200万guest，目标19200/执行宿主900/执行外层20100秒。新预算是有真实前缀依据的独立停止提案，不是保守完工上界，须下一轮明确接受后执行；旧1500秒FAIL与原6300/7200HOLD保留，不复用旧锁。

本轮完成静态与日志归因，目标/代码修改/构建/EDA0；正式18/20，默认0f＋firstdot V2＋原C8，第19项暂存。第20项四角色和原拒错资格全部闭合最多19/20。历史三指标保持，新测NOT_TESTED。

开始第20项原镜像四角色接入与有界验收，按 NEXT_STEP 复用原ELF/BIN、0f/候选EMU及已通过bit100，完成四角色差异接入、历史证据绑定、必要宿主检查和执行冻结。全部准入通过后，同轮执行候选正常→0f正常，九格比较通过后再执行候选重放→0f重放。我接受新的每角色4800秒/200万guest、目标累计19200秒、执行宿主900秒、执行外层20100秒预算。保持54窗、432算子、完整结果与CSR/退休绑定、逐窗控制相等、9格2%及精确重放。任一失败即停，不重试、不加时、不借用预算、不增加角色；第19项继续暂存。不改RTL、不改目标软件或重编镜像、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并给出结论和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/RESULT.md) · [设计合同](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/DESIGN_CONTRACT.json) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/NEXT_STEP.md)。



### 2026-11-07 第20项预算收口前的超时校准接续（历史）


**第20项完整调用校准HOLD：bit100通过，候选正常1500秒超时，0f未启动。** 外部监督1524.176042秒后清理完成；原FAIL/锁和batch中间态保留，不重试、不加时。26组标记/208退休、14完整UART行只是部分证据，54窗/432算子与CSR全量尚未闭合，9格2%及重放未测。

正式18/20，默认0f＋firstdot V2＋原C8；第19项继续暂存。本轮2个EMU，无RTL/镜像修改、构建、EDA、默认变更或上传。新三指标NOT_TESTED，历史18组性能/面积/五档STA保留。

窗口标记区间仅占观察前缀约1.43%，完整调用预算需重新收口；约3185秒/125.5万guest的线性情景不构成上界。下一轮集中核对窗口外成本，选择原镜像独立预算或最小输出方案并冻结一个合同，不重复同预算校准。

开始第20项 timed DIV/SQRT 预算收口与最小开销方案评审：基于本轮1500秒超时日志，核查窗口外校验、格式化输出与UART成本，比较保留原镜像的新独立预算和最小窗口外输出调整，选出一个有依据的方案并冻结下一批合同。保留54窗、432算子、完整结果、CSR/退休绑定、逐窗控制相等、9格2%及精确重放要求，复用已通过bit100与未变证据；依据不足就HOLD，不重复同预算校准、不缩减覆盖。先不改代码、不运行EMU/NEMU、不构建新核、不做EDA、不切默认、不上传GitHub；第19项继续暂存，完成后给出GO/HOLD和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/RESULT.md) · [预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/BUDGET_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/NEXT_STEP.md)。



### 2026-11-07 第20项三角色校准前的宿主准备接续（历史）


**第20项timed DIV/SQRT宿主准备GO；正式五角色预算HOLD。** 原54窗/432算子/9格各2%/完整128位与CSR/精确重放合同保持，137份旧材料身份复核并复用。独立三角色入口、两核观察器及bit100实际e64/e8/e64 guard分组适配已完成，11项方法闭合；两次原宿主FAIL保留，不把合成通过算目标通过。

正式18/20，默认0f＋firstdot V2＋原C8；第19项F2v反压补测继续暂存。本轮目标0、RTL/镜像不改、构建/EDA0、未上传GitHub，历史三项指标原样保留。

下一批建议一次完整调用校准：bit100→候选→0f，300/1500/1500秒、10万/100万/100万guest，目标3300＋宿主900＝外层4200秒、最多3串行目标。必须获得当前执行授权并复核35项冻结及资源后开始；这是停止限额，不是保守完成保证。保持54窗/432算子和9格2%，失败/超限即停，不加时/重试/跳过/自动重放。

原6300/7200正式预算因无本镜像完整目标样本继续HOLD；校准三角色不增加验收计数。收齐完整证据后，身份和合同不变可保留前三角色，只提出必要两次重放的新预算；第20项即使最终通过最多19/20，不能替代第19项。

开始 SP1-E 第20项 timed DIV/SQRT 三角色完整调用有界校准，按 NEXT_STEP 先核查进程、冻结输入和宿主准入，接受本轮独立预算后串行执行 bit100拒错→候选正常→0f正常。分别300秒/10万guest、1500秒/100万guest、1500秒/100万guest；目标累计3300秒、宿主900秒、外层4200秒。保持完整54窗、432条DIV/SQRT、完整128位和CSR/退休绑定、逐窗控制相等及9格各自最多2%退化，沿用CPU4/整组4线程/RSS12GiB/日志2GiB。失败、未拒错、超限或退化即停，不重试、不加时、不跳过继续、不自动重放；第19项继续暂存。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并判断正式预算和必要重放。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/RESULT.md) · [完整预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/BUDGET_REVIEW.md) · [下一批](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/NEXT_STEP.md)。



### 2026-11-07 第20项宿主准备前的R5接续（历史）


O2补测R5只读归因完成：**一次最小软件修订HOLD，暂存当前F2v压力触发方向**。保持18/20及默认0f＋firstdot V2＋原C8；第19项S0/S1全核见证与必要重放仍未完成。没有生成M2、重跑同镜像、扫描相位或切默认。

实际生成RTL证实VFEX4与FEX0共享写回仲裁且ready非绑高；M1的77个有效输出周期没有竞争，37对A/B均A出R同拍B直入R。vadd.vx存在I2v和向量ALU的RAW链，8条F2v压力不等于8拍连续请求。phase0/1/2的B未进入FU，phase4杀R中B时A已响应，因此不能补记P取消。现有日志无F2v/I2v动态时刻，不能以最小重排保证冲突。

M1完整功能、bit100及资源PASS复用，原NOT_HIT/GUARD_FAIL和锁保留。新三项指标NOT_TESTED；历史18组性能、面积和五档时序继续完整留档，不拼成新测或默认采用证明。

**下一轮建议：第20项timed DIV/SQRT宿主准备与预算评审。** 复用现有保护与公共机制，只补计时负载/公平窗口/差异和完整预算；无依据HOLD。第20项若通过最多19/20，不能替代仍HOLD的第19项。获得可绑定真实构建的冲突窗口新依据后再考虑第19项，不反复对相同日志开同类归因。

开始 SP1-E 第20项 timed DIV/SQRT 宿主准备与预算评审，按 NEXT_STEP 暂存第19项F2v反压补测，复用已有DIV/SQRT功能、身份和运行器证据，集中明确计时负载、同镜像公平窗口、必要差异检查、最少角色及完整预算。已有部分直接复用，只补真正缺项；依据不足就HOLD，不以第20项替代第19项覆盖。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后给出GO/HOLD、可执行批次和下一轮指令。

[R5结论](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/RESULT.md) · [接续](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/NEXT_STEP.md) · [历史三指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/METRICS.md)。



### 2026-11-07 R5收口前的M1校准接续（历史，已被上方当前路线替代）


O2第19项M1两角色已实际完成：**正常功能与bit100拒错PASS；S0/S1必需覆盖NOT_HIT，HOLD。** 原两角色分别25.727555秒/11653guest及583.112479秒/267282guest，外部610.835181秒。41调用、84UART、77退休和完整128位/CSR/ABI通过；资源合格且全部清理。

78次接受均DIRECT_R，77响应、1次R取消，没有P入队、反压或部分取消。phase4的A在262039响应，B同拍进入R，262040杀R中B；phase0/1/2的probe B未进入FU。这是新的取消时刻证据，仍不满足“杀P留R”。按未命中即停保留NOT_HIT及GUARD_FAIL/CHILD_EXIT_1，没有重试或自动重放。

下一轮R5只读定位FEX0释放/F2v压力/vset/vadd/VDOT接受关系，先判断为何944条STATE观察均outready1且P为空，再考虑取消时刻。依据实际源码/构建和日志给最小软件修订GO/HOLD；没有可信窗口就暂存，不盲扫phase或重复同镜像。下一轮没有新的目标预算或代码修改授权。

正式18/20，默认0f＋firstdot V2＋原C8。新的第19项真实校准已经执行，但真实S0/S1见证和必要重放仍缺。新公平加速比、面积及STA均未测；原历史指标、失败、退化和锁完整保留。

开始 O2 补测 R5，按 NEXT_STEP 只读分析 M1 两角色真实日志，先解释为何944条STATE观察中outready均为1、没有反压和P入队，再核对phase4的A响应、B进入R及取消顺序。复用本轮功能、bit100、资源与宿主证据，不重跑同镜像、不扫描相位、不新增无关门禁。结合现有源码和实际构建给出一次最小软件修订的GO/HOLD及验证合同；没有可信触发窗口就暂存补测方向。先不改代码、不运行EMU/NEMU、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并给出下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-calibration-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-calibration-20261107/NEXT_STEP.md) · [指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-calibration-20261107/METRICS.md)。



### O2第19项M1目标校准前入口（历史保留）


O2第19项R4-R1：**GO_HOST_ADMITTED_FOR_BOUNDED_CALIBRATION**。原始夹具出处漏项已在新冻结中补齐；13方法/94序列负控/6绑定负控/3冻结负控全部通过，旧完整日志和独立方法二进制复核通过。单次外部监督12.056357秒，有限宿主成本估计381.265913秒<900秒。原R4 FAIL/锁、R2未命中与全部旧证据保留。

下一轮直接进入M1两角色目标校准，不另开重复宿主准备：复用382项冻结、M1 ELF/BIN/bit100和本轮PASS，在明确目标授权后执行bit100300秒/10万guest→正常900秒/30万guest，目标1200/宿主900/外层2100秒。失败或S0/S1未命中即停；不重试、不加时、不扩围、不自动重放。

正式18/20，默认0f＋firstdot V2＋原C8。下一轮实际覆盖命中后仍需原合同的必要同硬件/跨硬件及精确重放才能记19/20；本轮只是宿主准入，不授予目标执行权限或默认切换。新目标、构建、EDA、三指标测量均0。

开始 O2 第19项 M1 两角色有界校准，按 NEXT_STEP 复用 R4-R1 已通过的宿主准入和382项冻结，先核查进程与输入并完成新目标授权绑定，不重编译、不重跑宿主整套。随后串行执行 bit100拒错→候选正常，分别300秒/10万guest、900秒/30万guest；最多2个目标进程，目标累计1200秒、宿主900秒、外层2100秒。保持CPU4、整组最多4线程、RSS12GiB、日志2GiB，以及41调用、77退休、完整128位、CSR/ABI和S0/S1覆盖合同。失败或未命中即停，不重试、不加时、不扩围、不自动重放；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板，给出第19项剩余重放安排和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-r1-host-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-r1-host-20261107/NEXT_STEP.md) · [指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-r1-host-20261107/METRICS.md)。



### O2补测R4-R1前入口（历史保留）


O2第19项R4：**M1软件及GNU/对象/bit100准备PASS；宿主准入HOLD**。首次宿主闭包检查发现冻结器漏收BASE_REUSE已声明的原夹具出处，0.432922秒退出并清理，已按失败即停停止。279项hash一致但闭包不完整；13个计划差异测试、旧日志复核、分开复核和预算测量未运行。

下一步R4-R1仅修正清单生成/校验不一致，保留R4原FAIL与旧锁。复用已通过M1源码、ELF/BIN、对象审计和bit100组件，不重新生成或编译、不增加条件；以新身份完成剩余宿主门及一次900秒成本门。当前目标执行HOLD，不自动进入两角色校准。

正式18/20，默认0f＋firstdot V2＋原C8。41调用/77退休/320架构F2v与原C数据合同保留；M1实际覆盖仍NOT_TESTED。本轮没有目标、RTL修改、新核构建、EDA、默认变更或GitHub写入，三指标没有新测，历史数据完整保留。

开始 O2 补测 R4-R1，按 NEXT_STEP 最小修复冻结器与必需文件清单的不一致，将 BASE_REUSE 已声明的原始 fixtures.py 作为出处输入纳入新冻结。复用 R4 已通过的 M1 源码、GNU ELF/BIN、对象审计和 bit100 组件，不重新生成或编译；保留 R4 原 FAIL、279 项旧冻结及锁。以新身份完成尚未运行的差异正负控、旧完整日志离线复核、独立方法复核和一次900秒宿主预算准入，不新增无关条件。失败即停、不重试、不加时；先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。全部通过后给出原两角色校准的GO/HOLD与下一轮指令，更新计分板。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-host-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-host-20261107/NEXT_STEP.md) · [指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-host-20261107/METRICS.md)。



### O2补测R4前入口（历史保留）


O2第19项R3只读归因与最小设计完成：**GO仅限M1软件宿主实现，目标与覆盖资格HOLD**。R2原正常41调用/77退休/81完整结果的功能PASS及S0/S1 NOT_HIT保留。全部40对B在A响应同拍DIRECT_R，4次probe取消晚于B响应39/7/7/7拍；冻结源码/实际构建支持FEX0释放器排在压力后及地址与加载依赖分叉的归因，缺动态F2v grant/branch PC，未证明新重叠窗口。

下一步只实施单一M1：提前FMV、零增量vector RAW替代v8重载、S1原商前置且真实门控FP生产者、phase留在分支链。集中GNU/对象/PC与bit100绑定、必要差异门和执行冻结/预算；复用未变证据，不增加调用/phase/压力。原两角色1200目标/900宿主/2100外层预算只为后续提案，当前不运行目标，不重放、不进入第20项。

正式18/20，默认0f＋firstdot V2＋原C8。本轮没有代码修改、目标、构建、EDA、默认变更或GitHub写入；三指标没有新测，历史表保留。

开始 O2 补测 R4，按 NEXT_STEP 在独立目录实现 R3 的单一 M1 软件修订：将 FMV 移到 F2v 压力之前，用 e8 零增量 vadd 替代 v8 重载；将 S1 原除法前置并真实门控 FP 生产者，原 phase 只调整分支依赖。保留41调用、77退休、320条F2v、原数据、完整128位及CSR/ABI合同。集中完成 GNU 构建、对象/链接审计、新PC和bit100绑定、必要差异正负控、执行冻结及原两角色预算评审；复用未变证据，失败即停，不扩相位、不增加调用。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；全部通过后给出一次两角色有界校准的GO/HOLD及执行指令，更新计分板。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/RESULT.md) · [设计](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/DESIGN_CONTRACT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/NEXT_STEP.md)。



### O2补测R3前入口（历史保留）


O2第19项接入R2已完成授权两角色并按NOT_HIT停止：合法历史标签修复、R1完整日志离线复核、9方法/4复用及184输入准入全部通过；新bit100拒错正式PASS，正常607.969222秒/268036guest，GOOD TRAP、41调用/77退休/81次完整128位与CSR功能通过。但81次全部DIRECT_R，P入队/反压保持/部分取消为0，S0/S1均未命中。外层645.963262秒，目标2个、资源/清理PASS，无重试或重放。原FAIL/锁与当前NOT_HIT完整保留。

正式18/20，默认0f＋firstdot V2＋原C8。R2获得了新功能证据，未测新加速比、面积或STA；局部历史数据保持原范围。第19项仍需真实覆盖及约定重放，第20项独立保留，不切默认。

下一轮R3一次集中只读归因S0/S1：先解释S0为何没有R阻塞/P入队，再对照F2v、e32/e8切换、RAW操作数加载及S1分支路径，列出有证据支持的最小软件修订、覆盖合同、可复用门禁和预算。观测不到的F2vgrant/分支PC不能写成实测；缺可信重叠窗口就HOLD。先不改软件/RTL、不运行目标或EDA，不重复同镜像。

开始 O2 补测 R3：基于 R2 完整真实日志，集中完成 S0/S1 未命中的只读时序归因与最小软件修订设计。先解释为何81次均DIRECT_R、没有STALL或ENQUEUE_P，再核对F2v压力、e32/e8切换、操作数重载及S1重定向的先后关系，区分实测与推断。给出有依据的最小改动清单、完整覆盖合同、可复用门禁和下一批预算；没有可信重叠窗口就HOLD，不重复同镜像探针。本轮先不改软件或RTL、不运行EMU/NEMU、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并给出下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r2-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r2-20261107/NEXT_STEP.md)。



### O2补测接入R2前入口（历史保留）


O2第19项接入R1已停止：最小负控修复、3宿主方法/13子例、新路径冻结及预算通过，旧7方法复用（冷导入重叠），同一外层已实际启动bit100。目标1个，25.976018秒/11668guest，原始bit100注入与差异可见，但合法历史(S)标签未被检查器支持，collector FAIL后停止，正常角色未启动。清理完成，原FAIL和锁全部保留。正式18/20，默认0f＋firstdot V2＋原C8；不切换默认。

下一轮R2：补生产者明确支持的历史tag格式，用R1完整真实日志一次核全链并做必要差异控制，复用未变机制；新冻结/宿主预算通过后在同一任务执行原两角色。预算仍300/900秒、10万/30万guest、target1200/host900/outer2100；失败或未命中即停，不自动重放或进入第20项。第19项完成仍需S0/S1真实覆盖及约定重放。

后续按用户偏好集中“修复→真实日志离线完整核对→必要准入→已授权执行→入账”，减少重复准备；不额外扩围或降低门槛。

开始 SP1-E O2 补测接入 R2，按 NEXT_STEP 最小补齐合法历史环 S/D/W 标签解析，明确当前拒错提交组不能用 skip/delayed 指令作证；用 R1 完整真实日志一次性核查整个拒错检查链，补针对性正负控，保留原FAIL与锁，复用未变宿主证据。全部宿主、冻结、独立方法复核和预算门通过后，以新身份同轮串行原 bit100拒错→候选正常两角色，保持300秒/10万guest、900秒/30万guest、目标1200秒、宿主900秒、外层2100秒及原资源和41调用/77退休、S0/S1完整覆盖。失败或未命中即停，不重试、不加时、不扩围、不自动重放；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板并给出下一批指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r1-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r1-20261107/NEXT_STEP.md)。



### O2补测接入R1前入口（历史保留）


O2第19项接入轮已停止：118项完整执行冻结完成，宿主8方法7通过1失败，尚未进入成本准入和目标；外层0.954496469秒、清理完成。负控把默认dst32输入按dst255替换，产生无效变异，与assertRaises失败一致；原FAIL/锁保留，未重试。当前正式18/20，默认0f＋firstdot V2＋原C8；0EMU/NEMU、0RTL/新核/EDA/切默认/GitHub写入。

下一轮O2补测接入R1，仅修历史环负控的精确命中与子例标注，复用7项未变证据，补剩余冻结、独立方法复核和成本准入；用户新指令下可同轮执行原两角色。保持300/900秒、10万/30万guest、目标1200/宿主900/外层2100。失败或未命中即停，不自动进入重放或第20项。

开始 SP1-E O2 补测接入 R1，按 NEXT_STEP 最小修复负控夹具的无效替换：使用实际存在的历史环dst字段，并检查替换命中及字节确实变化，给各子例明确标签。保留本轮FAIL与锁，复用7项通过证据，只补受影响负控、冷导入、执行冻结、独立方法复核和宿主预算准入。全部通过后，以新独立身份同轮串行bit100拒错→候选正常，接受原300秒/10万guest、900秒/30万guest、目标累计1200秒、宿主900秒、外层2100秒及原资源/完整覆盖要求。失败或未命中即停，不重试、不加时、不扩围、不自动重放；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-20261107/NEXT_STEP.md)。



### 第19项有界校准前入口（历史保留）


第19项O2最小补测准备已完成：**软件/宿主GO，目标与正式资格HOLD**。固定attempt-02、41调用/77退休，GNU、对象、完整128位/CSR/ABI宿主门、bit100编译及独立审查通过；首次宿主FAIL留档。当前18/20，默认0f＋firstdot V2＋原C8，未运行目标、未改RTL/新核/EDA/默认或上传。

下一轮只补运行器差异、新guard严格拒错、完整执行冻结和900秒宿主准入，全部通过及用户新授权后可同轮执行最多两个有界校准角色。预算target1200/host900/outer2100，不保证命中，失败/未命中即停、不自动进入重放。原O2重放和第20项仍待。

开始 SP1-E O2（第19项）补测运行器接入与有界校准，按 NEXT_STEP 复用本轮 attempt-02 镜像和已通过宿主证据，完成新 guard 的严格拒错检查、运行器差异接入、完整执行冻结、独立复核及900秒宿主预算准入。全部通过后，接受新独立预算，同轮串行执行 bit100拒错→候选正常校准，最多2个目标：分别300秒/10万guest、900秒/30万guest，目标累计1200秒、宿主900秒、外层2100秒，原CPU4、4线程、RSS12GiB、日志2GiB限制不变。保留41调用/77退休、完整128位、CSR/ABI及S0/S1真实观察链；失败或未命中即停，不重试、不加时、不扩相位、不自动进入重放或第20项。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板，给出结论和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-host-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-host-20261107/NEXT_STEP.md)。



### 第19项补测准备前入口（历史保留）


B4-R7已完成：fixtures冷导入修复、原9项宿主门、成本和独立审查通过，按新预算执行candidate-replay→baseline-replay，两次完整功能/同核精确重放及跨核比较全部PASS。新合同C48功能项认定，进度 **18/20**。默认保持 **0f＋firstdot V2＋原C8**；旧FAIL、锁和原1500秒HOLD保留，未上传。

下一步为O2（第19项）最小软件补测准备，复用既有两核数值证据，只补候选P槽与部分取消。第20项timed DIV/SQRT独立待验。本轮没有新性能窗口或EDA，历史三指标已续档。

开始 SP1-E O2（第19项）最小软件补测准备，按 NEXT_STEP 复用现有 bit100、两核完整数值和 R4 配对证据，在独立目录实现 R3 设计的最小 F2v 写回竞争软件，补候选 P 槽及部分取消覆盖的触发方案，完成 GNU 构建、对象审计、完整128位和CSR/ABI宿主正负控，冻结有限相位与新校准/重放合同及预算。复用未变机制，不新增反方向硬门；先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后给出GO/HOLD及下一批执行指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r7-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r7-20261106/NEXT_STEP.md)。



### B4-R7执行前入口（历史保留）


B4-R6停止：两角色运行器与执行冻结已完成，但唯一正式host在加载test_delta时因fixtures同名导入选中旧G0模块而FAIL。9方法0执行、成本0、目标0，外层1.395338548秒exit1且清理完成；源/旧证据全部MATCH。原独立静态PASS保持其有限范围并记录漏项，不替代真实FAIL。

当前仍17/20，默认0f＋firstdot V2＋原C8。下一轮B4-R7仅修宿主测试及成本脚本的helper装载，补冷进程完整导入门；保留原FAIL/锁，在新独立身份下复用未变运行器与三历史角色。全部门通过可在用户一次授权下同轮仅两次重放；当前禁止重启已失败的R6。

开始 B4-R7，按 NEXT_STEP 保留 B4-R6 原FAIL与消费锁，在新独立身份和目录中仅修复宿主测试、成本脚本的 fixtures 同名导入，使用绝对路径和唯一模块名并核对来源。按真实加载顺序补冷进程完整导入正控及必要错路径负控，复用未变运行器和历史证据；完成原差异门、执行冻结、独立审查和预算准入后，同轮串行 candidate-replay→baseline-replay。接受最多2目标、各2400秒/150万guest、目标累计4800秒、宿主900秒、外层5700秒及原资源/完整覆盖/精确重放要求。失败即停、不重试、不加时、不扩围，不重跑三历史角色、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r6-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r6-20261106/NEXT_STEP.md)。



### B4-R6执行前入口（历史保留）


B4-R5完成：C48有效低64跨硬件摘要、完整128结果及同核raw128合同明确；宿主27项与独立2016完整结果/3负控PASS。首次独立包装失败保留，R1全量复核通过。原R4 FAIL不翻转，默认0f＋firstdot V2＋原C8、正式17/20不变。

下一轮B4-R6：接入仅两个重放角色、完整执行冻结和必要宿主预算门，用户一次授权后可同轮执行。提案预算各2400秒/150万guest、target4800/host900/outer5700；实际执行准入目前HOLD。不重跑四历史目标，不加无关门，不自动进入O2或timed DIV/SQRT。

开始 B4-R6，按 NEXT_STEP 完成 C48 两次重放运行器、三份历史角色绑定、完整执行冻结及必要宿主差异、独立审查和预算准入；复用未变证据，不重做旧宿主全套。全部通过后接受新独立预算，同轮串行执行 candidate-replay→baseline-replay，最多2个新目标，每角色2400秒/150万guest、目标累计4800秒、宿主900秒、整批外层5700秒。保持CPU4、整组最多4线程、RSS12GiB、日志2GiB、完整48调用/1008custom/128位结果、同硬件raw128/observer/guest精确重放及跨硬件active64。保留旧FAIL和锁，失败即停、不重试、不加时、不扩围，不重跑既有三角色、不自动进入其他用例。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板并给出结论和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r5-20261106/RESULT.md) · [下一步](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r5-20261106/NEXT_STEP.md)。



### B4-R5执行前入口（历史保留）


B4-R4宿主15＋8项、独立审查和预算门通过；剩余四个真实角色各自通过，O2数值配对完成。C48最终跨硬件accepted_sources_sha256比较失败，整批STOPPED且清理正常。只读逐条归因确认1008条有效低64输入、非数据字段、完整128结果及48调用UART均相同，96条仅未消费高64不同；原FAIL保留，最小宿主口径修订设计GO，当前C48整case/正式验收HOLD。未改RTL/新核/EDA/默认或上传，进度17/20。

当前下一轮为最小宿主比较修订与原日志离线复核，不重启目标。

开始 B4-R5 最小比较合同修订与离线复核：保留 B4-R4 原FAIL、原始日志、授权和消费锁，在独立目录为 C48 增加按退休链绑定的有效低64位输入摘要，仅用于跨硬件比较；完整128位结果、PC/编码/配置/控制字段及同硬件raw128精确重放要求保持。复用四个已完成角色和未变宿主机制，使用两份真实完整日志补齐高64差异正控、低64/结果/身份及同硬件高64漂移负控，做独立复核。通过后同轮准备复用既有三角色＋两次新重放的明确合同和实测预算提案，不自动授正式资格。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板，给出GO/HOLD和下一批指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r4-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r4-20261106/NEXT_STEP.md)。



### B4-R4执行前入口（历史保留）


B4-R3宿主准备完成：同源码组件证据和R2真实数值/拒错证据可复用；原全核P槽及部分取消覆盖仍HOLD。已形成FEX0/F2v写回竞争的最小补测设计，实际命中NOT_TESTED。剩余四角色新独立校准预算设计GO（7500秒目标/9300秒外层），但数值专用adapter和显式角色运行器尚未接入，执行准入HOLD。未运行任何EMU/NEMU或新测试，未改RTL/构建/EDA，17/20及默认0f＋firstdot V2＋原C8保持。

优先下一轮补齐四个未运行角色的数值/预算校准：先完成最小宿主接入和准入，再在同一授权任务内有界执行；新取消覆盖补测设计独立保留，不借这批预算。原全核coverage FAIL与正式进度不改。

开始 B4-R4，按NEXT_STEP实现校准专用数值摘要和剩余四角色运行器，复用未变公共机制，只补角色/参考库/退出码/历史身份/冻结差异正负控及宿主预算准入。保留R2原FAIL和旧锁，不重跑已完成的o2-control bit100与候选正常。全部准入后，以新冻结身份和独立授权，仅串行运行0f O2正常→C48 bit100→C48候选正常→C48 0f正常；接受新独立预算：最多4目标、目标累计7500秒、整批外层9300秒，O2目标2400/宿主900/外层3300秒，C48目标5100/宿主900/外层6000秒；各角色和资源按本轮草案。失败即停、不重试、不加时、不借旧余量、不自动进入正式验收。新取消覆盖补测镜像不在该批执行，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板和三项指标，给出下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r3-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r3-20261106/NEXT_STEP.md)。



### B4-R3评审前入口（历史保留）

B4-R2最小raw dst范围修复与宿主准入通过；新独立批次bit100拒错通过，候选o2-control完整程序GOOD_TRAP、256次试验零错误、1208次退休完整128位重算一致，但原覆盖门KILL_P/PARTIAL_KILL未触发，整批按合同STOPPED。仅启动2/6目标，其余4个NOT_RUN，清理正常、旧FAIL和锁保留。候选1562.610640秒超过原正式1500秒，低于本轮2400秒；不授完整校准或正式验收资格，进度仍17/20，默认保持0f＋firstdot V2＋原C8。

下一步为B4-R3覆盖合同与剩余校准方案收口，不是原批次重试；未经新的目标运行授权不启动后续角色。

开始 B4-R3 取消覆盖合同与剩余校准方案收口：保留 B4/R2 原FAIL、原始日志和消费锁，复用本轮bit100、1208次完整128位结果、程序完整结束及资源证据。先针对SP1直接入R、P槽未占用的真实路径，核对已有FU/真实父级反压和两槽取消证据能否组成完整分层覆盖；不能替代的全核覆盖，给出能实际触发的最小补测设计，不直接删掉KILL_P/PARTIAL_KILL要求。同步依据1562.61秒实测修订正式预算提案，明确0f O2和原C8普通C48尚缺的校准角色、证据复用边界、下一批进程和独立预算。只做必要宿主差异验证与合同准备，不重跑已完成目标、不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后给出GO/HOLD及可整批执行的下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r2-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r2-20261106/NEXT_STEP.md)。


### B4-R2执行前入口（历史保留）

B4按最终runtime-r1和新授权实际启动唯一首例o2-control bit100进程，9243 guest/19.937916秒后冻结检查器报instruction ring slots/destination；整批STOPPED，guardian CHILD_EXIT_1且清理完成，后5目标未启动，未重试。确切触发是非当前提交组历史slot06的dst32被整环dst<32检查拒绝，当前组为slots10–13；数值部分观察一致但不翻转FAIL。实际身份/349份资源采样/原始日志/清理独立通过。完整正常调用0，原正式预算仍HOLD，验收17/20不变，三项新指标NOT_TESTED，稳定默认不变。

当前B4实际执行已失败即停，旧授权/消费锁永久保留，不能直接重启。此前宿主GO为历史准备资格，不覆盖此次目标日志解析FAIL；仍17/20、默认稳定组合不变。下一步建议以新身份只修历史环raw字段与当前提交组语义范围，采用本次真实日志验证；通过并取得新批次授权后同轮执行相同预算校准。

开始 SP1-E B4-R2 宿主修订与两例完整调用校准：保留本轮真实FAIL、原始日志、授权和消费锁，在独立修订目录仅修正历史指令环raw dst解析与当前提交组架构目的地检查的作用范围，按冻结输出端uint8字段定义处理历史槽，不把32改写成28，不放宽当前组/ELF/最后写入者/完整128位/CSR/bit100判据。使用本轮真实日志做离线正控，补齐历史dst32、当前组非法目的地、槽序/尾指针/组计数及数值身份负控，复用未变通过证据；完成最小差异审查、实际输入冻结写读及宿主预算影响核对。全部GO后，在新源码/合同/授权和独立输出下同轮执行o2-control→原C8普通C48，每例bit100300秒/10万guest、候选完整2400秒/150万guest、0f完整2400秒/150万guest；每例目标5100/宿主900/外层6000秒，整批最多6目标、目标10200/外层12000秒。CPU4、整组4线程、RSS12GiB、每例日志2GiB、原完整覆盖与seed/RAM/reset保持。新批次任一失败即停，不重试、不加时、不借旧剩余预算、不跳过继续、不自动进入正式验收；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板和三项指标状态，给出结论和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/execution-01/RESULT.md) · [失败归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/execution-01/independent-review/FAILURE_ATTRIBUTION.md) · [下一轮指令](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/execution-01/NEXT_STEP.md)。


### B3-R6原入口与B3-R7执行前路线（历史保留）


B3-R6已修正历史出处检查：准备与正式验证使用同一原路径/字节数/SHA逻辑，304项冻结内容及4份历史别名通过；运行器和checker保持R5原字节，27＋10项证据明确复用、未重跑。独立审查唯一正式尝试在首个CSR正控API调用时报explicit scope/run id：审查脚本误传HOST_FIXTURE_NOT_TARGET，生产既有合法值为HOST_FIXTURE。首个正控调用1次、完成0/41；这是Agent编写的审查脚本参数错误，不是RTL、CSR结果或预算超限。按失败即停，预算0次、EMU目标0，保留原FAIL，整体HOLD，SP1-E仍15/20。

开始 B3-R7：在独立目录仅将CSR独立审查共享调用点的scope改为生产已有合法值HOST_FIXTURE；沿用非空host run_id和既有全部41项覆盖，不新增条件、不为测试放宽生产API。复用R5已通过且字节未变的27项checker、10项外部监督及现有身份/溯源证据，复用R6历史路径检查修复。先逐项静态核对本次改动调用的签名、合法scope和返回字段，再冻结并完成剩余独立审查及一次原夹具900秒外部监督预算测量；保留R1至R6全部FAIL和旧锁，不缩样、不重复无关测试。两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色，每例300＋4×1500秒，目标6300/外层7200/宿主900秒；整批最多10目标，目标12600/外层14400秒，不借时，负控100000guest、正常800000/300000guest，CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式审查、预算或目标任一失败即停，不重试、不加时、不跳过继续、不扩围；三个暂缓项继续HOLD。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板、三项指标和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r6-20261106/RESULT.md)。



### B3-R5原入口与B3-R6执行前路线（历史保留）


B3-R5完成两条CSR正则的同行空白修复，checker27/27一次PASS；新增进程外超时监督，runtime10/10及12次宿主进程夹具清理一次通过。独立审计错误地把历史出处符号链接也要求为直接canonical路径，在执行0/41项对抗控前FAIL；240项冻结内容及4份别名的字节/SHA均一致。这是本轮审计新增条件导致的假阻断。按失败即停，预算0次、EMU目标0，保留全部记录，整体HOLD、SP1-E仍15/20。

开始 B3-R6：在独立目录仅修独立审计的路径校验适用范围，历史出处与宿主冻结文件按原路径、字节数和SHA校验，允许已有符号链接；记录解析目标作为审计信息，不新增别名白名单或额外准入条件。真实执行路径的canonical、boot/PID/start_ticks、完整结果和重放检查保持。冻结准备与正式校验采用一致逻辑；未运行的终态审计只在授予功能PASS时要求GUARD_PASS，FAIL收据仍可如实审计。保留R1至R5全部FAIL和旧锁，复用身份匹配且未变的27项checker、10项外部监督及旧身份/溯源证据，不重复无关测试。集中完成剩余独立审查、执行冻结和一次外部900秒监督预算测量；原两份24,558,348字节成本夹具不缩样。全部通过且两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色，每例300＋4×1500秒、目标6300/外层7200/宿主900秒，整批最多10目标、目标12600/外层14400秒；负控100000guest、正常800000/300000guest，CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式门或目标任一失败即停，不重试、不加时、不借时、不跳过继续、不扩围；三个暂缓项保持HOLD。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板、三项指标和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r5-20261106/RESULT.md)。



### B3-R4原入口与B3-R5执行前路线（历史保留）


B3-R4已修正准备期启动身份范围：旧boot只作历史，真实批次仍绑定boot/PID/start_ticks/单调时钟；4项新差异与65项独立检查一次通过，原6项运行器和23项checker按身份复用。唯一宿主预算进程超过900秒仍未返回，核实身份后在观测1012.62秒时发送SIGTERM，超限112.62秒已如实留档；两例预算均HOLD/null，EMU目标0，不重试，SP1-E仍15/20。

开始 B3-R5：在独立目录仅修订宿主拒错检查器两条CSR行的空白匹配，将同行空白限制为[ \t]，并补齐预算测量的独立进程外墙钟监督；核查实际批次宿主解析也受原900/7200/14400秒限制可靠约束，必要时作最小外部监督接入。保留R1至R4全部失败、原24,558,348字节成本夹具、完整数值/CSR/身份/重放合同及原预算，不缩样、不加时。复用未变的运行器、身份、溯源证据，集中完成受影响正负控、外部超时小夹具、独立复核和一次预算准入；全部通过且两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色。每例300＋4×1500秒、目标6300/外层7200/宿主900秒；整批最多10目标、目标12600/外层14400秒，不借时；负控100000guest，正常800000/300000guest，CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式门或目标任一失败立即停止，不重试、不跳过继续、不扩围；三个暂缓项保持HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板、三项指标及下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r4-20261105/RESULT.md)。



### B3-R3原入口与B3-R4执行前路线（历史保留）


R3完成test18精确行定位，checker23/23、runtime6/6及源码二进制溯源PASS；独立门新增的准备快照boot相等条件遇WSL启动代际变化而FAIL，对抗控制0项。该前提比原执行身份协议过严，不是RTL或guest功能失败。按单轮失败即停，预算0次、目标0个；整体HOLD，SP1-E仍15/20。

后续仍按用户要求合并必要宿主修订与准入后的两例执行，复用已验证未变机制；不得再将与目标执行无关的准备期不变条件作为新的强制门。真正目标boot/PID/monotonic身份、资源、覆盖和失败即停保持。

开始 B3-R4，按 NEXT_STEP 在独立目录仅修订宿主准入的启动身份绑定：BEFORE.boot_id保留为历史快照，正式准入/执行前记录实时boot并绑定后续目标PID/start_ticks/单调时钟，不允许跨boot拼接运行。保留R1/R2/R3全部FAIL及旧锁；复用未变且身份匹配的23项checker、6项运行器和溯源证据，补齐该合同变更的正负控及尚未完成的独立对抗门、执行冻结和900秒预算门。全部通过且两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色。每例300＋4×1500秒、目标6300/外层7200/宿主900秒；整批最多10目标、目标累计12600秒/外层14400秒，不借时；负控100000guest、正常800000/300000guest、CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式门或目标任一失败即停，不重试、不加时、不跳过继续；三个暂缓项保持HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板、三项指标和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r3-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r3-20261105/NEXT_STEP.md)。



### B3-R2夹具失败及B3-R3原入口（R3现有独立boot门FAIL）


严格提交组与组末最后写入者检查器已实现，真实R1日志和多写入者正控所在的前17方法通过；第18方法的错误dst变异因同时匹配历史slot15与当前slot31而断言失败，未调用该变异的生产checker，正式宿主门HOLD。方法19–23及后续运行器/独立正式门/预算门均NOT_RUN；目标0。三个暂缓项无当前组合完整预算新证据，继续HOLD；SP1-E仍15/20。

用户偏好：后续按已准入精确白名单合并批次，复用未变公共机制；本次建议把最小夹具修订、宿主准入和通过后的两例执行放在同一下一轮，但当前未运行目标。

开始 SP1-E B3-R3 夹具修订与两例批量验收：保留 R1/R2 原 FAIL、日志及旧锁，在独立目录仅修正错误目的寄存器负控的定位，精确锚定当前环尾 slot31、PC0x80000370 和完整行，先检查所有变异目标的唯一性。保持严格当前提交组、组末最后写入者完整128位、CSR/身份/重放及原完整覆盖，完成新源码冻结、全部宿主正负控、运行器接入、独立审查和900秒宿主预算准入；未变公共机制复用。全部门禁通过且两例均GO后，在同一轮仅按 legacy-control→o2-all-pairs 串行运行五角色。每例300＋4×1500秒，目标6300/外层7200/宿主900秒；整批最多10目标、目标累计12600秒、外层14400秒，不借预算。负控100000guest，正常分别800000/300000guest；CPU4、整组4线程、RSS12GiB、每例日志2GiB及原seed/RAM/reset不变。任一正式宿主门或目标失败立即停止，不重试、不加时、不跳过继续；三个暂缓项保持HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后一次更新计分板、三项指标及下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r2-host-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r2-host-20261105/NEXT_STEP.md)。



### SP1-E B3-R1目标停止与B3-R2原宿主入口（现R2另有夹具FAIL，见当前）


B3-R1整批在legacy首个bit100角色停止：注入PC0x80000298，DiffTest诊断PC为同提交组首0x80000294，冻结检查器要求二者相等而拒绝。真实运行1目标/8339guest/20.819646708秒；正常角色0、allpairs未启动。资源与清理通过，独立fail-stop审计通过但功能资格0；不重试，SP1-E仍15/20。

用户新增偏好：后续验收优先把多个已准入用例合并为明确白名单的串行批次，公共机制复用，只补差异；不降低原覆盖、预算、失败即停条件，不自动扩围或越过HOLD。

开始 SP1-E B3-R2 拒错归属修订与剩余项集中宿主评审：保留B3-R1原FAIL、日志和已消费锁，在独立目录修订保护负控的PC归属检查，严格绑定冻结注入PC/指令字/目的寄存器、当前提交组及唯一bit100差异，不得忽略PC或仅凭exit1放行。用本轮真实日志做离线复核，补齐错误组、历史同PC、错误指令/寄存器/bit、重复注入和非预期退出等正负控，冻结新检查器依赖与执行闭包，独立审查预算影响。同轮集中核对o2-control、原C8普通C48、timed DIV/SQRT的真正宿主缺项与完整预算依据，复用未变公共证据，不重复无收益的短探针；无实质新依据就保留HOLD。保持原完整覆盖、五角色、6300/7200秒及900秒宿主门、原资源和失败即停，不重试、不加时。本轮先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；一次交付各项GO/HOLD、更新计分板，并仅为全部准入的精确白名单给出下一批串行执行指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/execution-01/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/execution-01/NEXT_STEP.md)。



### SP1-E B3-R1宿主GO与原两例执行指令（目标批次已消费，见当前停止记录）


四项cwd配套输入已从真实B2原冻结精确迁入，17方法及独立29项门通过；CPU4完整宿主预算两例468.345019776/331.801223876秒均低于900秒，正式执行冻结及最终增量复核通过。只完成宿主准入，目标进程0、两例未运行，旧FAIL保留，SP1-E仍15/20。

开始 SP1-E B3-R1 两例五角色有界执行，按 NEXT_STEP 先核查已有进程、冻结输入、独立最终增量复核及未消费锁，再为本轮明确创建目标授权，按 legacy-control→o2-all-pairs 串行执行。每例保留300/1500×4秒、目标6300秒/外层7200秒/宿主900秒；整批最多10个目标进程、目标12600秒/外层14400秒，不借预算。负控guest各100000，正常guest分别800000/300000，CPU4、整组4线程、RSS12GiB、每例日志2GiB以及原seed/RAM/reset不变。保持完整覆盖、128位、退休身份、CSR、bit100拒错与正常恢复、八维功能精确重放；这些功能程序没有性能计时窗。任何失败立即停止整批，不重试、不加时、不跳过继续、不扩围；o2-control继续HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板的三项指标及资格状态，给出结论和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/NEXT_STEP.md)。



### SP1-E B3首轮执行接入停止及R1宿主修订入口历史


两例运行器和宿主机制完成；正式CPU4执行闭包核验因遗漏四个cwd配套文件失败，900秒宿主门未建立，按失败即停终止整批。两例均未运行，原o2-control继续HOLD。 SP1-E仍15/20，默认0f＋firstdot V2＋原C8不变。

开始 SP1-E B3-R1 宿主闭包修订：保留本轮 FAIL 和旧 HOST_FREEZE，在独立目录从已验证的真实 B2 执行冻结中提取候选及0f的 constantin.txt、plusArgs 四项精确路径、大小和SHA，建立可追溯输入 annex，并修订新执行闭包；补齐缺失、错路径、内容漂移负控，冻结新运行器源码，再做独立复核和CPU4实际调用图的完整900秒宿主开销门。保持两例完整功能及每例6300/7200秒、整批12600/14400秒和原资源/guest上限，失败即停、不重试、不加时；o2-control继续HOLD。本轮仅做宿主修订与准入，不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后逐例给出GO/HOLD、更新计分板，并仅在全部GO时给出两例串行执行指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-execution-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-execution-20261105/NEXT_STEP.md)。



### SP1-E B3原宿主合同与预算准备历史（不等于执行准入）


三例宿主合同与检查器完成；legacy-control/o2-all-pairs有条件预算GO进入执行接入，o2-control预算HOLD。当前三例均非TARGET_READY，专用运行器/执行冻结/CPU4完整宿主900秒门尚待下一轮。

开始 SP1-E B3 两例执行接入与有界验证：仅 legacy-control→o2-all-pairs，先接入专用五角色外层，核验真实进程/参考映射及资源回执，完成执行源码冻结、宿主正负控和CPU4下完整核验/解析开销审计；实际调用图的宿主开销须通过900秒门，全部准入后再串行执行两例。每例保持300/1500×4秒、目标6300/外层7200秒；整批最多10个目标进程、目标12600秒/外层14400秒，不借时。负控guest各100000，正常guest分别800000/300000，CPU4/整组4线程/RSS12GiB/日志2GiB不变。保留原完整功能、128位、CSR、bit100、八维功能精确重放；不把无计时窗程序当性能测试。任何准入或执行失败立即停止整批，不重试、不加时、不跳过继续；o2-control保持HOLD，不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-protection-host-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-protection-host-20261105/NEXT_STEP.md)。



### SP1-E B2 stream执行历史


B2 stream d0/d1/d2五角色全部通过；完整SP1-E必验进度从12/20推进到15/20。默认仍为0f＋firstdot V2＋原C8，SP1候选未切默认；其余保护及普通C调用缺项未冒充通过。

开始 SP1-E B3 原功能保护的专用宿主合同与预算准入：集中核查 legacy-control、o2-all-pairs、o2-control，复用未变公共机制，明确当前候选的完整功能、取消/反压、DIV混合、CSR/全向量结果、负控及重放合同，补齐专用收集器和宿主正负控。按原每例6300/7200秒及资源约束逐例审查预算，guest上限按各自冻结工作量论证，不套用micro的300000上限；o2-control证据不足继续HOLD，不借时、不加时、不重复短校准。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后逐例给出GO/HOLD、必要缺项和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B2-stream/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B2-stream/NEXT_STEP.md)。



### SP1-E B1 batch有界执行历史


B1 batch d0/d1/d2五角色全部通过；完整SP1-E必验进度从9/20推进到12/20。默认仍为0f＋firstdot V2＋原C8，SP1候选未切默认；stream及其余保护缺项未冒充通过。

开始 SP1-E B2 stream 三数据集五角色有界执行：按 NEXT_STEP 先核查进程和冻结输入，确认B1全通过，再按 d0→d1→d2 串行执行 performance-d0-s03、performance-d1-s03、performance-d2-s03。每例保持6300/7200秒及原CPU4、整组4线程、RSS12GiB、日志2GiB与guest上限；整批最多15个目标进程、18900秒目标累计、21600秒外层预算，不借用预算。保留完整12窗、384次custom、递增地址/三条退休融合及专用bit100、VDOT/RVV各自最多2%退化、完整128位、退休/CSR、逐窗控制及精确重放。任一失败立即停止整批，不重试、不加时、不跳过继续、不自动扩围。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新三项指标和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B1-batch/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B1-batch/NEXT_STEP.md)。



### SP1-E B0宿主准入历史


2026-11-05，GO：batch/stream六例共享宿主入口、差异正负控、实际执行冻结和有界预算准入完成；batch三例可在下一轮明确授权后整批执行。本轮没有EMU/NEMU或新性能资格，完整SP1-E仍9/20已验，默认0f＋firstdot V2＋原C8不变。

开始 SP1-E B1 batch 三数据集五角色有界执行：按 NEXT_STEP，先核查已有进程及冻结输入，明确仅 performance-d0-s02、performance-d1-s02、performance-d2-s02，按 d0→d1→d2 串行执行，每例最多5个角色进程。每例保持6300/7200秒、原guest及CPU4/整组4线程/RSS12GiB/日志2GiB上限；整批最多15个目标进程、目标累计18900秒、外层21600秒，预算互不借用。每个正常角色完整12窗、768次custom，VDOT与RVV各自最多2%退化，完整128位、源操作数、退休/CSR、逐窗控制相等及双方八项精确重放全部保留。任一用例任一门禁失败立即停止整批，不重试、不加时、不跳过继续、不自动进入stream。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新三项指标，给出结论和下一轮指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/RESULT.md) · [下一轮合同入口](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/NEXT_STEP.md)。



### SP1-E剩余验收收口与共享运行器复用评审历史


2026-11-05，GO：六个batch/stream用例集中做共享宿主迁入与差异准入；HOLD：剩余目标执行及完整SP1-E。20项必验中9项已通过、11项待完成；未变公共机制复用，逐case完整覆盖和原门槛保留。默认0f＋firstdot V2＋原C8不变。

下一轮为B0：一次共享micro宿主迁入，分别完成batch/stream各三数据集差异准入；只准备，不运行目标。之后按B1 batch、B2 stream、B3原功能保护分批执行，预算缺证项留HOLD，有限统一收口。每case6300/7200秒不变；全批失败即停；具体未来执行须明确case名单与累计硬上限。

[本轮计划](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-closeout-review-20261105/PLAN.md) · [下一轮完整指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-closeout-review-20261105/NEXT_STEP.md)。



### single-d2五角色验收历史


2026-11-05，**GO（single-d2）：五角色有界探针、独立指标与功能审计通过。** VDOT平均周期71→70，下降1.408451%；RVV保持85.25cycles，加速比1.200704225×→1.217857143×。四个正常角色各12窗/6custom，共48窗/24次；专用bit100拒错、完整128位全零、接受源、退休/CSR、逐窗控制及双方精确重放通过。结合第62/64条，single三个数据集已分别完成目标验收，收益一致；本轮补齐数据覆盖，未新增RTL优化。完整SP1-E尚未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

默认0f＋firstdot V2＋原C8不变；加速比优先，面积与时序继续据实留档。完整SP1-E及默认采用尚未闭合。

开始 SP1-E 剩余验收收口与共享运行器复用评审：结合已通过的chain、single和原C8性能三数据集，固定剩余必验清单、暂缓项、验收终点和执行批次；复用已验证的公共宿主机制，只补用例/镜像差异检查。保留各case完整覆盖、原性能门槛、6300/7200秒预算及失败即停要求，不用代表性抽样替代未验证项。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出必要缺项、GO/HOLD及下一批执行指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d2-g0/target-20261105-01/RESULT.md)。



### single-d2宿主准入与冻结历史

2026-11-05，**GO（宿主准入）：single-d2合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d2的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

第65条仅single-d2宿主准入。第51/58/60条chain三数据集、第53～55条C8及第62/64条single-d0/d1成绩按原范围保留，C48 HOLD不变。完整SP1-E和默认采用尚未闭合。

开始 SP1-E micro single-d2 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d2-g0/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d2-g0/CONTRACT.md)。



### single-d1五角色验收历史

2026-11-05，**GO（single-d1）：五角色有界探针、独立指标及功能审计通过。** VDOT平均周期71→70，下降1.408451%；RVV维持85.25cycles，加速比1.200704225×→1.217857143×。四个正常角色各12窗/6custom，共48窗/24次；专用bit100拒错、完整128位结果、退休/CSR、逐窗控制及双方精确重放通过。仅新增single-d1资格，本轮未改RTL。完整SP1-E尚未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

默认0f＋firstdot V2＋原C8不变；加速比优先，面积与时序继续据实留档。完整SP1-E及默认采用尚未闭合。

开始 SP1-E micro single-d2 的合同与宿主准入准备：复用 single-d1 机制，核查 G0 冻结镜像、12窗和6次custom、专用bit100、完整128位结果、退休/CSR及精确重放，完成运行器适配和6300/7200秒预算评审。按G0保持VDOT与RVV各自最多2%退化、逐窗控制相等和平衡执行顺序，预算不足就HOLD。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出结论和下一轮指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d1-g0/target-20261105-01/RESULT.md)。



### single-d1宿主准入与冻结历史

2026-11-05，**GO（宿主准入）：single-d1合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d1的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

第63条仅single-d1宿主准入。第51/58/60条chain三数据集、第53～55条C8及第62条single-d0成绩按原范围保留，C48 HOLD不变。完整SP1-E和默认采用尚未闭合。

开始 SP1-E micro single-d1 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d1-g0/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d1-g0/CONTRACT.md)。



### single-d0五角色验收历史

2026-11-05，**GO（single-d0）：五角色有界探针和独立复核全部通过。** VDOT平均周期71→70，下降1.408451%；RVV维持85.25cycles，加速比1.200704225×→1.217857143×。四个正常角色各12窗/6custom，共48窗/24次；专用bit100拒错、完整128位结果、退休/CSR、逐窗控制及双方精确重放通过。只增加single-d0资格，未新增RTL优化；完整SP1-E仍未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

默认0f＋firstdot V2＋原C8不变；加速比优先，面积与时序继续据实留档。完整SP1-E及默认采用尚未闭合。

开始 SP1-E micro single-d1 的合同与宿主准入准备：复用 single-d0 机制，核查 G0 冻结镜像、12窗和6次custom、专用bit100、完整128位结果、退休/CSR及精确重放，完成运行器适配和6300/7200秒预算评审。按G0保持VDOT与RVV各自最多2%退化、逐窗控制相等和平衡执行顺序，预算不足就HOLD。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出结论和下一轮指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d0-g0/target-20261105-01/RESULT.md)。



### single-d0宿主准入与冻结历史

2026-11-05，**GO（宿主准入）：single-d0合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d0的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

第61条仅single-d0宿主准入。第51/58/60条chain三数据集与第53～55条C8成绩按原范围保留，C48 HOLD不变。完整SP1-E和默认采用尚未闭合。

开始 SP1-E micro single-d0 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d0-g0/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d0-g0/CONTRACT.md)。



### chain-d2五角色验收历史

2026-11-05，**GO（chain-d2）：五角色有界探针与独立复核全部通过。** VDOT均值1857→1601.25 cycles，降低13.772213%；RVV均值5440.5 cycles不变，加速比2.929725×→3.397658×。四个正常角色各完成12窗/1536次custom，共48窗/6144次；bit100实际拒错、完整128位、退休/CSR、AB/BA和双方精确重放通过。结合第51/58条，chain三数据集已闭合；本轮新增dataset2覆盖，收益与d0/d1一致。完整SP1-E仍未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

默认0f＋firstdot V2＋原C8不变；加速比优先，面积与时序继续据实留档。完整SP1-E及默认采用尚未闭合。

开始 SP1-E micro single-d0 的合同与宿主准入准备：沿用 G0 冻结矩阵，核查同镜像12窗、6次custom、bit100、完整128位结果、退休/CSR、平衡执行顺序及精确重放，完成最小运行器适配和6300/7200秒预算评审。按G0固定single的vdot与RVV各自最多2%退化门槛；预算依据不足就HOLD。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出GO/HOLD和下一轮指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d2-g0/target-20261105-01/RESULT.md)。



### chain-d2宿主准入与冻结历史

2026-11-05，**GO：chain-d2 的合同、宿主准入及执行输入冻结完成，可进入下一轮单独授权的五角色有界探针。** 本轮未运行 EMU/NEMU，SP1 chain-d2 目标正确性及加速比仍为 NOT_TESTED，默认保持0f＋firstdot V2＋原C8。

第59条仅宿主准入；第51/58条chain-d0/d1及第53～55条C8资格各自保持，C48 HOLD不变。SP1-E尚未完整验收；默认选型仍由用户决定。

开始 SP1-E micro chain-d2 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和1536次custom、10%收益、2% RVV退化、AB/BA及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d2-g0/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d2-g0/CONTRACT.md)。



### chain-d1五角色验收历史

2026-11-05，**GO（仅 chain-d1 用例）：五角色探针与独立复核通过；VDOT 周期下降 13.772213%，同机 RVV/VDOT 加速比由 2.929725× 提高至 3.397658×，RVV 退化 0%。** 四个正常角色各完成 12 窗和 1536 次 custom，共 48 窗/6144 次；bit100 实际拒错、完整 128 位结果、退休/CSR、AB/BA 和双方精确重放通过。此次增加 dataset1 覆盖，未改 RTL，不能作为一次新的硬件优化或整个 SP1-E 完成。默认仍为 0f＋firstdot V2＋原 C8，候选最终采用等待用户决定。

默认0f＋firstdot V2＋原C8不变；加速比优先，面积与时序继续据实留档。完整SP1-E及默认采用尚未闭合。

开始 SP1-E micro chain-d2 的合同与宿主准入准备：复用已验收 chain-d1 机制，核查 G0 冻结镜像、12 窗、1536 次 custom、bit100、完整 128 位结果、退休/CSR 及精确重放，完成最小运行器适配和 6300/7200 秒预算评审。保持 10% 收益、2% RVV 退化及 AB/BA 门槛，预算不足就 HOLD。先不运行 EMU/NEMU、不改 RTL、不构建新核、不做 EDA、不切默认、不上传 GitHub；完成后给出 GO/HOLD 和下一轮指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d1-g0/target-20261105-01/RESULT.md)。



### chain-d1宿主准入与冻结历史

2026-11-05，**GO：chain-d1 合同、宿主准入和执行输入冻结完成，可进入下一轮独立授权的五角色有界探针。** 本轮未运行目标；chain-d1 在 SP1 上的功能与性能仍 NOT_TESTED。

默认0f＋firstdot V2＋原C8。第57条仅宿主准入，第51条chain-d0和第53～55条C8成绩保持各自范围；原C48第56条预算HOLD保留。按用户要求加速比优先，当前候选不新增PPA限制。

开始 SP1-E micro chain-d1 五角色有界探针：先核查已有进程、冻结输入和本轮 NEXT_STEP，使用已冻结运行器与同镜像、0f/SP1 EMU及NEMU；准入全部通过后，依次运行bit100拒错、候选恢复、0f校准、候选重放和0f重放。保持6300/7200秒、CPU4/4线程、原guest/RSS/日志上限，完整12窗和1536custom，10%收益、2%RVV退化、AB/BA均正及精确重放。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序并给下一轮指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d1-g0/RESULT.md) · [冻结合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d1-g0/CONTRACT.md)。



### SP1-E C48 宿主评审历史

2026-11-04，**静态合同 GO；C48 目标执行准入 HOLD。** 未发现冻结调用表/数值/镜像不一致；当前组合完整运行墙钟上界没有证据，专用执行闭包也未完成。暂存此项，保留全部验收覆盖，不等于放弃最终SP1验收。

默认0f＋firstdot V2＋原C8保持。第56条是宿主评审，没有新目标成绩；第51条chain-d0和第53～55条C8性能资格保持各自范围。

暂存 SP1-E 原 C8 普通 C48 的预算HOLD，保留48调用及1008custom，不重试或缩减。开始 SP1-E micro chain-d1 的合同与宿主准入准备：复用固定0f/SP1 EMU、NEMU及G0冻结镜像，核查12窗、1536custom、bit100、退休/CSR/完整128位及精确重放，审查专用运行器适配、正负控和6300/7200秒预算依据。保持10%收益、2% RVV退化及AB/BA门槛；预算不足就HOLD。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出GO/HOLD和下一轮指令。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-c8-c48-g0/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-c8-c48-g0/CONTRACT.md)。



### SP1-E 原C8 dataset2五角色收口历史

2026-11-04，**C8 dataset2 完整五角色合格。** 全部五角色和独立审计/指标复算通过，仅授原C8 dataset2资格；其他dataset、普通C48调用、DIV/SQRT和默认采用均未转授。

稳定0f＋firstdot V2＋原C8不变；第55条保存本轮完整数据/资格，前54和失败不覆盖。面积与五档STA仍为原G2 trace-off复用，没有新RTL/新核/EDA/默认切换/GitHub写入。

开始 SP1-E 原 C8 普通 C 48 调用的宿主合同与预算准入评审。复用固定 0f/SP1 EMU、NEMU 和最终 SDK 镜像，保留全部 48 调用、其中 12 个 C8 调用及 1008 次 custom；核对完整128位结果、数值/CSR/ABI、首条 bit100 绑定、身份和独立重放。按功能验收明确必要角色，分解完整运行与宿主检查开销，单独冻结 guest/墙钟上限及失败即停条件；不得套用性能镜像30万guest上限、删调用、把功能整程序周期当性能加速比，或把历史墙钟线性外推成完成保证。预算依据不足就 HOLD。先不运行 EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，也不自动改跑micro或DIV。完成后给出GO/HOLD和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d2/RESULT.md) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d2/evidence-manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d2/NEXT_STEP.md)。



### SP1-E-G1 原C8 dataset1 五角色历史

2026-11-04，**C8 dataset1 完整五角色合格。** 全部五角色和独立审计/指标复算通过，仅授原C8 dataset1资格；其他dataset、普通C48调用、DIV/SQRT和默认采用均未转授。

稳定0f＋firstdot V2＋原C8不变；第54条保存本轮完整数据/资格，前53和失败不覆盖。面积与五档STA仍为原G2 trace-off复用，没有新RTL/新核/EDA/默认切换/GitHub写入。

开始 SP1-E 原C8 dataset2：复用G1五角色机制，先按冻结case适配镜像与bit100绑定，冻结执行合同、全源码及公平对照并通过宿主检查；全部通过后仅运行该case五角色，保持300/1500×4秒、总6300/7200秒及原资源/guest上限、四格2%和精确重放门槛。失败即停、不重试、不加时、不扩围、不改RTL、不构建新核、不切默认、不上传GitHub，完成后更新三指标、给出GO/HOLD和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d1/RESULT.md) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d1/evidence-manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d1/NEXT_STEP.md)。



### SP1-E-G1 原C8 dataset0 五角色历史

2026-11-04，**C8 dataset0 完整五角色合格。** 全部五角色和独立审计/指标复算通过，仅授原C8 dataset0资格；其他dataset、普通C48调用、DIV/SQRT和默认采用均未转授。

稳定0f＋firstdot V2＋原C8不变；第53条保存本轮完整数据/资格，前52和失败不覆盖。面积与五档STA仍为原G2 trace-off复用，没有新RTL/新核/EDA/默认切换/GitHub写入。

开始 SP1-E 原C8 dataset1：复用G1五角色机制，先按冻结case适配镜像与bit100绑定，冻结执行合同、全源码及公平对照并通过宿主检查；全部通过后仅运行该case五角色，保持300/1500×4秒、总6300/7200秒及原资源/guest上限、四格2%和精确重放门槛。失败即停、不重试、不加时、不扩围、不改RTL、不构建新核、不切默认、不上传GitHub，完成后更新三指标、给出GO/HOLD和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d0/RESULT.md) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d0/evidence-manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d0/NEXT_STEP.md)。



### SP1-E-G0 扩围宿主准入历史

2026-11-04，**SP1-E-G0 宿主准入 GO，目标执行 HOLD。** 已固定20用例、退休/CSR/完整128位/bit100与公平比较合同，完成micro/C8/DIV-SQRT软件宿主门禁和预算审查。本轮0目标、0RTL、0新核、0EDA、0默认切换、0GitHub写入。

下一步仅原C8 dataset0：先完成专用运行器/采集器、真实接口正负控及完整执行冻结，下一轮明确授权且门禁通过后再进行有界五角色。推荐300/1500×4秒、10万/30万×4guest、6300/7200秒，CPU4/整组4线程/RSS12GiB/日志2GiB；不自动运行其他case。完整48调用普通C和新54窗DIV/SQRT另立合同，不删覆盖。已合格chain-d0复用第51条，不重跑。

第52条和计分板记录本轮宿主结论；没有新加速比/面积/时序。第51条候选chain-d0为3.397658×、vdot1601.25cycles，较同批0f减少13.772213%；只具该工作负载资格。成本继续原G2 trace-off复用。稳定选择0f＋firstdot V2＋原C8，最终选型由用户决定。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g0/RESULT.md) · [预算](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g0/BUDGET_REVIEW.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g0/NEXT_STEP.md)。完整主线仍按[速度优先计划](speedup-first-optimization-plan-20261102.md)。



### SP1-D 五角色通过历史

2026-11-04，**GO：SP1-D 的 dataset0/chain256 五角色公平周期探针通过。** 可以进入SP1-E扩围合同与宿主准入评审，尚未取得全部数据集、C8或默认采用资格。

本轮候选相对同批0f的vdot周期减少 13.772213%，RVV均值退化 0.000000%；AB/BA分别减少 13.785676% / 13.758751%。这些数值只描述本轮chain256。


新五角色活动 `SP1-CD-R1-CHAIN-D0-20261104-01`，运行器PERFORMANCE_PASS、独立审计PASS、指标复算PASS；原FAIL保留，未切默认。计分板及档案第51条列出三指标；周期为本轮新测，成本仍为原G2 trace-off复用。稳定选择0f＋firstdot V2＋原C8，最终选型由用户决定。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/run-20261104-01/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/run-20261104-01/NEXT_STEP.md)。当前不自动扩围或改RTL；完整后续按[速度优先计划](speedup-first-optimization-plan-20261102.md)。


### SP1-C/D-R1 宿主准备历史

2026-11-04，**SP1-C/D-R1 宿主修订 GO，正式性能 HOLD 待新合同五角色**。默认保持0f＋firstdot V2＋原C8，最终选用由用户决定。

退休比较改为冻结ELF完整展开＋白名单双ADDI有效值验证；同核raw重放、完整128位/CSR/身份、10%链收益/2%RVV退化/ABBA和6300/7200秒不变。检查器72、运行器45、独立审验60项通过，旧三日志离线跨核控制通过。旧活动仍STOPPED/FAIL，两个真实重放仍NOT_RUN；不能授旧成绩最终PASS。

新运行合同已冻结验证：2604pin、43源，本轮0目标/RTL/全核/EDA/GitHub写入。下一步另获用户指令后，从新目录串行完成五角色；不恢复旧campaign，不自动进入SP1-E。原单对3.397658×、1601.25 cycles继续为未最终合格观察，原G2面积/五档STA复用，计分板和档案第50条区分宿主GO与性能HOLD。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/NEXT_STEP.md)。RTL下一主改动预计为SP2 dot16/累加，先设计合同再提前告知；本轮不实施。完整后续见[速度优先计划](speedup-first-optimization-plan-20261102.md)。

### SP1-C/D 原失败记录（R1前）

2026年11月4日，**SP1-C通过，SP1-D跨硬件公平门禁FAIL/HOLD**。稳定选择保持0f＋firstdot V2＋原C8，最终采用由用户决定。

**SP1-C通过；SP1-D在第3角色后的跨硬件退休记录公平检查失败，整轮STOPPED/HOLD。** 实际仅3个目标，两个重放均未启动。候选观测均值1601.25 cycles、RVV/vdot=3.397658×，相对同批0f的1857 cycles观测减少13.772213%；这组数值尚未取得最终公平及重放资格。

下一步为SP1-C/D-R1宿主修订与新合同：依据只读归因处理ROB融合退休分组与架构指令的比较，补强正负控，保留原10%/2%/ABBA及重放规则。先不运行目标，不接着补跑旧campaign，不改RTL或切换默认。

面积/时序仍复用原G2 trace-off FU18322.878μm²、完整父级285241.642μm²，nominal setup −0.790381/−2.337809ns；新SP0预算47/47，旧G0失败保留。计分板和数据档案第49条更新三指标资格及五档数据。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd/NEXT_STEP.md)。未授SP1-E扩围资格，完整主线仍按[速度优先计划](speedup-first-optimization-plan-20261102.md)。

以下保留前期材料编写、P5收口以及P0～P5阶段决定，当前后续任务以本页上方SP路线为准。

> 2026-11-02 用户确认进入提交材料阶段。参赛工程V1.0选用0f＋firstdot V2＋原C8，成本采用Nangate45。Agent已按本轮授权编写[三阶段报告、材料清单及录屏脚本初稿](../submission/2026-cie-vdot-v1-draft/00_先读我.md)，接续为团队信息、补图、录制和排版。

> 2026-10-31 更新：**P5稳定版只读收口完成：继续0f＋firstdot V2＋原C8，既有R5/G5资格可复用；没有必须新增实现或目标运行的缺项。** P1保持HOLD、P4/分段归约关闭、P3暂存HOLD；下一步可按发布需求整理提交范围，不继续自动试验。[P5结论与必要缺项](../optimizations/o2/integration/firstdot-v2-0f/continuation/p5-stable-closeout-v1/RESULT.md)。
>
> 研究基点：zjhwork `10b71ad4bff25cd2070e775c74a4717b01602f75`；生产硬件 `0f12df675378556670afd0dd2153f47fcb330610`，`src` 树 `78a0c93852dced038f645205e33d36a520fedfcd`。参考[公开项目与分支研究](public-vdot-review-and-plan-20261028.md)、[评分要求](../../赛题要求与评分总览.md)、[最终验收](../optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md)和[历版三指标](version-comparison-r5-g5-20261027.md)。研究文件中的供体成绩是选题依据，不是当前版本的新成绩。

> P0～P5本轮分析与失败证据按[资料发布范围](p0-p5-publication-20261031.md)归档；不合入候选源码，历史记录的本地/未上传状态不回写。稳定0f＋firstdot V2＋原C8保持。

## 0. P0～P5原路线与阶段记录（历史）


### 2026-10-31历史决定 P5收口通过

P5的12组只读核查全部通过：稳定clean-02的398项生产src、429项构建源、627项C8保护输入、实际EMU/NEMU/SDK/最终镜像和R5/G5证据匹配。原13＋补1组合验收与C8最终镜像等价可复用，旧clean-02 UTC失败和系统时钟限制仍保留，不再次补跑。

生产0f＋firstdot V2＋原显式C8保持。研究HEAD的src提交树等于0f，但工作树另有两份默认关闭P4修改；不能将整个脏树冒充R5原始源码。稳定O2由clean构建入口显式启用O2/T14，空环境通用构建并不等于已验收O2；公共firstdot默认及C8独立入口不变。

**必补实现/仿真/构建/EDA项为0。** 两处过期导航已收口。P1/P1-R1维持HOLD、P4及唯一修订NO-GO关闭、C8分段归约NO-GO关闭、P3预算HOLD暂存，不重开。实测档案47条原字节保持，没有新成绩或新采用版本。

若准备发布，下一步只整理zjhwork待提交范围，区分稳定交付、研究记录与P4补丁，核对必要文件/证据和恢复说明；不自动提交/上传。若暂不发布，可以停在当前稳定版。成员标识、人工复核、官方答疑和赛事材料保持各自边界。[P5完整结论](../optimizations/o2/integration/firstdot-v2-0f/continuation/p5-stable-closeout-v1/RESULT.md) · [下一轮可复制指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/p5-stable-closeout-v1/NEXT_STEP.md)。

### P3完整调用预算只读归因历史决定（2026-10-31）


原14次调用分解为功能2（TA1/FR1）、预热6（TA2/FR4）、计时6（TA2/FR4）；另3次独立量化。已知GNU主体合计1767568条指令，尚不含main/prepare/judge等开销。已有校准首窗仅完成量化及RVV的Q投影、K部分：量化退休跨度3532周期，Q为78408周期；0完整窗。TA的Q/K/V custom提交跨度77201/87464/91310，不能按单段复制授上界。

有利情景约3567041周期/5704.91秒，未覆盖后续检查、边界间隙、缓存/数据差异及日志/主机降速；26.2071%额外成本就超过7200。完整周期上界、后续吞吐下界、启动/收尾上界均未知，**HOLD_STAGE_P3：保留候选与全部证据，不进入正式探针、不重跑同样短校准、不删覆盖或放宽门槛**。本轮0目标/构建/RTL改动/GitHub写入，六组离线检查通过；实测档案仍47条、原字节不变。

依据原路线0.8进入P5的只读收口核查：继续0f＋firstdot V2＋原C8，确认默认开关/入口/身份/证据和真实缺项，复用未变R5/G5成果。没有获选优化就不虚构新性能版本、不无故整核重验。[本轮结论](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-budget-attribution-v1/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-budget-attribution-v1/NEXT_STEP.md)。



### P3单核有界校准历史记录（2026-10-31）

严格2个串行目标，bit100拒错23.401695秒通过；正常1599.320037秒到999988 guest原生上限停止，625.258周期/秒。只有首RVV窗口开始、0窗完成、2次CSR起始采样；首窗67782/110580条动态指令核对通过，仅进度证据。没有完整14调用/6窗/GOOD TRAP/候选配对，不能授正常全程或性能PASS。

**不重复同样短校准，不自动正式探针。** 按前缀速度7200秒约容纳450万周期，但剩余TA/FR、预热、检查和日志成本尚无可信上界。下一轮只读分解完整调用预算；有保守上界才建议正式合同，否则暂存P3，继续保持稳定版。[完整指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/NEXT_STEP.md)。

4502项目标前冻结、10组宿主门禁、4487旧保护文件及src不变；两组回收，线程观测峰值1≤4，未改镜像/RTL/核或上传。详见[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/RESULT.md)与版本档案47；旧失败全部保留。


### P3 R1宿主修订历史决定（2026-10-31）

显式CAL_HERE/必需源集合修复V1漏冻结，测试前4324项清单通过。触发快照含进程树、PID/TID、出生标识与亲和；14组宿主测试、13宿主进程通过。固定原运行时对象在四核亲和建立4宿主线程，诊断子sh使整组达到5；CPU4两次诊断峰值3，均正常退出。旧第45条目标失败及缺失身份仍保留。

**HOST_GO，不授目标资格。** 下一轮按[指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/NEXT_STEP.md)建立新执行合同/目录，实际wrapper也须预冻结，再用CPU4做300秒拒错→2400秒正常；各100万guest、最多2串行、总2700秒、4线程整组口径不变。不得把宿主占位助手带入目标PATH，不自动执行正式探针或加时。新目标、加速比/面积/时序未测，7200秒准入仍HOLD。

### P3短校准历史停止记录（2026-10-30）


正式7200秒准入仍HOLD。首个负控24.422秒出现全组线程5>4，按限额回收，exit−9；有首条提交和bit100注入，没有完整mismatch/ABORT/exit1，不能授拒错PASS。正常校准未启动，不使用启动前缀猜QKV吞吐。

收尾发现context通配导入覆盖HERE，漏预冻结新源码/合同6项；另缺线程超限当次PID/TID明细。两项均原样留档，不回填资格。下一轮仅先修显式命名空间、必需文件集合门禁与触发快照，用宿主夹具核查4线程总口径和诊断辅助进程；不默认放宽上限或启动目标。详见[下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/NEXT_STEP.md)，数据档案45。

### P3-0f适配历史决定（2026-10-30）


**不启动正式探针，不切换默认版本。** 22组宿主门禁、155521笔合成O2提交、62208笔计时精确绑定通过；旧0f C8真实32窗解析兼容。0f实际EMU_THREADS=1，完整硬件生成物、429源文件及P3冻结镜像有身份绑定。新目标功能/差分/周期、面积和STA仍NOT_TESTED。

完整14边界计划含42投影、17量化、5049浮点除法及校验；旧C8吞吐仅作情景参考，不能证明新P3在7200秒内完成。合成解析本身实测183.474秒/6.206GiB，真实日志/吞吐上界未闭合。预算门禁false，下一角色为空；原1%/3%规则、失败和未测全部保留。

下一步可由用户另行授权一份独立短校准合同：最多2串行，先bit100拒错≤300秒/1M，再正常校准≤2400秒/1M，总≤2700秒；只收集进度/吞吐/日志与资源，不凭不完整样本判性能，不自动续开正式探针。若不做校准则暂存P3、保持稳定版。当前不试跑、不加时、不删验证。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/RESULT.md) · [输入与阻断计划](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/READY_PLAN.json) · [下一轮完整指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/NEXT_STEP.md)。档案第44条HOST_ADAPTER_ONLY，不新增加速比成绩。

### C8 R1只读归因与P3宿主门禁历史决定（2026-10-30）


**NO-GO关闭当前8×32分段归约候选，不再重复探针；P3最小迁入与宿主门禁已完成，GO进入0f适配和预算准入。** 原R1 HOLD及全部32窗保持；P3没有新目标性能资格。

末尾OV锚点274→268可精确拆为首条退休前−5、叶内首条→ret +1、ret→结束采样−2；32笔vdot ACCEPT/MOVE/RESPONSE均整体提前5拍，首末接收跨度仍117拍。64个计时区间重定向都绑定既有fence，没有观测到JAL/RET误预测；底层取指/缓存/预测状态未记录，根因止于可证明区间。

正式OV/NV首条接受93、末条210、末响应212、末提交214、最后配置退休220均相同；少8配置没有缩短当前算术完成进度。NV入队→接收平均等待23.59375→25.40625拍；只是混合等待坐标，不能直接归因加载或寄存器压力。更快RVV也必须保留，B校准/重放未测；即使解释了锚点，正反3%收益仍失败。无新硬件改法、目标重跑或门槛调整的依据。

**P3固定源闭包及最小软件包已完成；本段记录当时进入0f适配的决定，最新状态见上节。** 143源＋2 API＋19历史对象已核验，最小包8文件；两位置两方法完整QKV、每笔128位、CSR/ABI宿主门禁通过。供体3.473%与0.5%阈值不转授；1%/3%规则不变。禁止直接使用旧T17 runner；预算不足HOLD。

[C8关闭依据](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-r1-review/RESULT.md) · [P3宿主结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/RESULT.md) · [0f有界合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/PROBE_CONTRACT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/NEXT_STEP.md)。版本档案追加第43条HOST_ONLY，三项指标新测量仍NOT_TESTED。

### C8 dataset0探针R1历史结果（2026-10-30；只读归因已接续完成）


**HOLD_ANCHOR_AND_GAIN_SCREEN，不采用候选、不扩围。** 仅修目标重复自检后，正常A图84功能＋32窗、完整128位/CSR/寄存器/范围检查、NEMU与O2通过。OV锚点273/274/274/268的跨度2.238806%超1%；正反NV相对OV仅少0.183%/0.365%，不达3%。A图正式均值OV/NV/OR/NR为273.75/273/301/278，最快RVV/NV原始比1.018315×只可作诊断，不能宣布新合格加速比。

2/5个串行目标进程：bit100拒错、A正常完成；后三项因前级门槛失败NOT_TESTED，逐窗跨镜像控制与重放资格未取得。四算术叶、窗口、门槛保持。重复validate1460→116，宿主177408扰动及1260自检保留；硬件/原C8包不变，旧失败不覆盖。统一数据档案追加第42条。

**下一轮建议：仅对本轮已封存日志作只读归因，解释末OV锚点少6拍、NV少8指令却无明显周期收益，以及NR/OR变化；判断是否值得继续分段归约。** 原1%/精确控制/3%门槛不变，无本轮后续自动修订或运行。若证据不足明确缺口，不猜测根因。面积/STA无新测，保持0f＋firstdot V2＋C8；P1/P4既有HOLD/NO-GO不变。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0-r1/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0-r1/NEXT_STEP.md)。

### C8 dataset0首轮历史决定（2026-10-30；R1已接续完成）


**HOLD_TEST_HARNESS_BUDGET_REVIEW**。本轮未完成正常恢复，32性能窗口为0；不得报加速比或“全通过”。1%／逐窗精确控制／3%门槛保持，尚未实际检验。稳定版本不改，候选不采用。

实际执行2个串行进程：NV首条bit100拒错PASS；正常图534.868秒后由Agent主动停止，未触发超时或guest上限。原因是测试框架把已在宿主完成的15项校验器负控重复到每次目标功能调用，增加1,260次自检，预算预检不足。原日志及退出失败保留，不能判作候选性能失败。后3进程未运行；统一档案第41条。

**下一轮：只移出重复的目标校验器自检，保留所有宿主负控、84次功能调用及每次完整结果／CSR／寄存器／范围检查。四个算术叶、原窗口、门槛不变；先审计前序开销并完善实际CPU记录，再冻结新A/B与新的最多5进程预算。** 不自动重跑、不扩围、不改RTL、不重建核、不上传。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0/NEXT_STEP.md)。

### C8分段归约宿主阶段历史决定（2026-10-30；探针已接续但HOLD）


**C8_DEFERRED_HOST_PASS_GO_D0_PROBE**：独立实现8×32 packed reuse的vdot/RVV延后归约，现有包和硬件不变。GNU实际叶配置13→5 / 13→9，指令164→156 / 112→108，字节656→624 / 448→432；无spill/额外move。310输入×3入口状态×4实现＝3720次机器码模型执行、29760完整128位槽、59520逐dot独立oracle，4原语/39负控、9产物重建相等通过。三次宿主记录保留，最后attempt03为采用的宿主证据。

只授予宿主/静态链接资格，不是NEMU/RTL/周期PASS。新AM性能镜像、observer适配尚未实现；程序加速比/面积/STA均NOT_TESTED，默认0f＋firstdot V2＋C8不变。数据档案第40条，旧39条保持。

**下一轮：按冻结合同构建真正AM A/B图并适配退休/寄存器门禁，先静态/负控通过，再复用0f EMU做dataset0受限探针。最多5串行目标进程，1%锚点、未改控制逐窗相等、同BIN重放相等及3%收益不变。** 不重建核、不修改RTL、不自动扩大或上传。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/RESULT.md) · [宿主合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/CONTRACT.md) · [dataset0公平探针合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/PROBE_CONTRACT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/NEXT_STEP.md)。

### P4收口后的只读评审历史（2026-10-30；宿主试验已接续完成）


**GO仅指下一轮最小软件实现/宿主验证，不指采用或立即运行。** R2-S3新增一个8×32 packed reuse叶：保留每组各段中间结果、延后归约，vdot与RVV同等评估；不修改现有C8包、输入接口或硬件。源计数两个函数各13次vsetivli；设计上vdot可到5、RVV可到9，分别使用28/30个架构寄存器。配置/指令减少只是静态推导，周期、物理寄存器压力和新的三指标未测。

下一步先独立生成候选，冻结寄存器/完整128位/CSR/固定布局/强RVV对照，完成GNU对象、宿主数学/指令模型及负控；通过后另轮用冻结0f EMU做dataset0最小探针，再按门槛扩三数据集与普通C接入。该宿主试验已由后续授权完成，结果见上方当前决定；目标EMU尚未启动。

P4/R1原47项37通过、10失败，停止进一步试改；P1/P1-R1保持HOLD。4×8漂移归因和有限QKV仅保留为条件项，当前不启动，不接管队友tailrows/forward。实测档案仍39条，设计不冒充第40条成绩。

[完整路线评审](../optimizations/o2/integration/firstdot-v2-0f/continuation/post-p4-route-review/RESULT.md) · [静态源计数与拟寄存器安排](../optimizations/o2/integration/firstdot-v2-0f/continuation/post-p4-route-review/source-analysis.json) · [可复制的下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/post-p4-route-review/NEXT_STEP.md)。

### P4-G2R1成本筛选历史决定（2026-10-30）


**P4_G2R1_COST_NO_GO**，47项37 PASS/10 FAIL；FU21通过后父级26筛选完成。局部功能PASS保持，本轮新映射/STA；程序加速比NOT_TESTED。

FU面积18086.936μm²，含FU父级285473.062μm²；nominal FU/父级最差setup裕量-0.776319/-2.235609ns。常量元数据实际映射已核查，全部纳入成本与路径；原47项门槛保持。默认0f＋firstdot V2＋C8不变，未采用；原G2六项FAIL保持为历史失败。

当时建议的P4收口只读路线评审已完成；下一动作以本节顶部的新评审为准，成本原记录与原下一轮指令作为历史保留。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1-cost/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1-cost/NEXT_STEP.md)。统一档案第39条，旧38条不变，本轮没有RTL修改、全核/NEMU/性能运行或commit/push。

### P4-G2R1局部验证历史（成本筛选已接续完成）

局部验证PASS记录见[原结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1/RESULT.md)。完整128位、FU/真实父级DIV/SQRT/反压/取消/身份/异常和默认关闭证据保持。生成夹具常量保留位数不是最终映射面积；实际成本以本轮独立记录为准。

### P4-G2R0历史评审（2026-10-30，R1已按其范围完成局部验证）

**P4_G2R0_GO_ONE_BOUNDED_REVISION**。只读分析完成，值得下一轮做一次R槽宽元数据选择试验；不代表现有P4已通过成本门槛。原G2六项失败完整保留。

FU 784位R元数据与真实父级593位各映射两级MUX。建议只把一拍分支的ctrl/perf写入改为包含旧值保持的三路互斥表达；数据32、P/R状态、ready、DIV/SQRT和默认关不改。手工库构型有面积空间，但新增保持控制可能增加负载，父级ready改善未证明。新修订三指标均NOT_TESTED。

当时建议的 **P4-G2R1局部实现与验证现已完成**：先说明具体RTL改法，完成完整128位、FU、真实父级DIV/SQRT/反压/取消/身份/异常和默认关闭验证；通过后另轮做原同约束FU/父级综合与五档STA。原47项数值/完整性门槛不变；只尝试该候选，任何原成本项仍失败就停止该次修订，不自动进入全核或搜索其他结构。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r0/RESULT.md) · [修订合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r0/REVISION_CONTRACT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r0/NEXT_STEP.md)。统一档案第37条，旧36条保持；本轮0 RTL改动/EDA/全核运行，无commit/push。

### P4-G2历史成本结论（2026-10-30，仍有效）

**P4_G2_NO_GO**。G1功能/协议PASS保留，当时的原P4候选未过G0成本门槛，禁止该旧版直接进入G3；R1状态以上方当前决定为准。FU面积18322.878μm²（+5.923329%），含FU父级285241.642μm²（+0.220191%）；全部五档时序、控制保护和失败见[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2/RESULT.md)。程序加速比NOT_TESTED，不把局部1拍当整体2倍。

当时建议的 **P4-G2R0只读成本复核现已完成**：审查R槽宽元数据写入选择与本轮全部超限路径，判断是否值得一次最小修订；不放宽G0门槛、不自动改RTL/构建全核。若没有可信收益路线则关闭P4，保留稳定版。[下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2/NEXT_STEP.md)。

统一档案第36条，旧35条与失败完整保留；本轮RTL修改0、全核/NEMU运行0、未commit/push。默认0f行为＋firstdot V2＋显式C8、P1-R1 HOLD保持。候选补丁默认关闭并保留供研究，不代表已采用。前置P2的1857拍/2.929725×仍是0f历史实测，1601只是条件模型。

### P1-R1历史结果：准备调用位置隔离（接续以上节为准）

**P1_R1_PROBE_HOLD**；新候选正确性 PASS_STEADY_D0_ONLY；性能探针 HOLD。实际EMU 4 个，后处理新增目标0。 candidate S-V 310.00、最快观测RVV S-R4，同场RVV/S-V 1.099193548×；1%锚点=False，正反3%收益=True。

保留0f＋firstdot V2＋显式C8稳定版；停止该候选扩大，先复核本轮完整失败/未过门槛原因，不自动重试。 本轮固定4进程预算，不因探针过线自动扩围或采用；P1旧HOLD保留，P2其他方向未执行，P4硬件方向不会自动启动。统一档案第32条附两镜像/工具/运行/归档身份，生产RTL和默认保持。

### P2调用路径叶收口（前轮历史记录，当前接续以上节为准）

**本次P2只读归因完成；下一步P1-R1静态实现与布局对照。** 正式慢窗在split_full→leaf间接JALR发生额外预测纠正，快/慢leaf首退休45–47/55拍；其后首vdot入队/接受区间一致。20个split RVV正式普通窗也纠正，故全部对照重测。机制归因未深入到特定预测表，也未证明conditioning是唯一原因。

选择一次窗外conditioning调用位置隔离，保留被测12实现、完整窗口及原1%/3%门槛；先固定最终ELF/数据布局和新身份，后运行有界同布局控制/候选。候选尚未实现/运行，P1 HOLD和0f＋firstdot V2＋C8默认保持。P2依赖链/Jade方向没有开展，不据此启动P4。

[P2结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/callpath-p2/RESULT.md) · [单次修订设计](../optimizations/o2/integration/firstdot-v2-0f/continuation/callpath-p2/REVISION_PLAN.md)；统一档案已追加第31条，只读派生而无新三指标实测。


### 0.0 P1收口状态（2026-10-28）

最小软件迁入与9镜像静态证书通过；steady-d0正常/独立重放各7组功能数据、312调用、8控制、84窗、2432退休vdot。全部84窗及完整validation相等，统计只用正常48正式普通窗。收益两顺序通过3%，锚点两窗和605/605/626/606、跨度3.471074%超过1%，结论 **P1_PROBE_HOLD**。

同新窗口观测S-V308.5、最快RVV S-R4 340.5、P-V408.75 cycles，观测RVV/S-V 1.103727715×，不能作已采用升级，不能与旧273/299比较。PPA沿用0f无新测。其余8镜像runtime NOT_TESTED；RTL/默认不变。一次只读分段已留档，不改变门槛。


### 0.1 当前基线与最主要的优化空间

**当前建议：使用已验收0f＋firstdot V2＋原显式C8；P5只读收口完成，没有必须补跑的工程缺项。** P1/P1-R1保持HOLD，P4和C8分段归约NO-GO关闭，P3完整预算HOLD并暂存。可按发布需求整理文件范围，不重复校准、不正式探针、不自动重开优化。

| 三项主指标 | 当前已验证值 | 后续比较时必须保留的边界 |
| --- | --- | --- |
| 批量微基准加速比 | batch128：vdot 221 / RVV 678 cycles，**3.067873×** | 用来观察吞吐；不能当作 GEMV 或完整应用加速比 |
| 8×32 普通 C 调用加速比 | C8 273 / 最快合格 RVV 299 cycles，**1.095238×**；相对原 firstdot 282.25 少 **3.2772%** | 固定当前完整调用窗口；已连续的 288B 输入、完整 128 位结果槽；包和最终链接没有新增计时成绩 |
| 依赖链与流式窗口 | chain256：1857 / RVV 5440.5 cycles，**2.929725×**；stream64：1127.5 / RVV 1133，**1.004878×** | 说明不同负载瓶颈不同；不能平均成一个总加速比 |
| 综合面积 | FU **17,298.246 μm²**；VFEX4 父级 **284,614.946 μm²** | 父级含 FU 与 DIV，二者不能相加；软件变化沿用相同 0f 数据，注明无新测量 |
| 参考时序 | nominal：FU i2r **1.190323 ns**、r2r **1.163404 ns**、最差 slack **−0.268520 ns**；父级全局 r2r **3.261218 ns**；父级 VDot r2r **1.356106 ns**；父级已报告最差 slack **−2.393998 ns** | Nangate45、typical/25°C/1.1V、1ns/5fF 的布局前参考 STA；不是整核 Fmax，也不代表 1ns 已收敛 |

从这些数据能提出三个问题，不能直接给出答案：

1. 普通 C 入口中，准备输入、设置向量状态、调用、存储与提取结果各占多少？微基准 3.0679× 与 C8 1.0952× 的窗口不同，不能用二者相减计算“调用损耗”。
2. Jade 历史 chain256 为 1601.25，本项目为 1857，差约 255.75 cycles/256 条，值得调查是否存在每次依赖约一拍的机会。但历史批次、执行路径不同，不能据此断定应删一个算术流水级。
3. 当前全局时序瓶颈有 VFDiv 迭代路径，VDot 的输出路径也可能来自共享控制。应识别实际起点/终点，再决定改算术、共享输出还是不改；不把 vdot 任务扩大成整个 DIV 重构。

### 0.2 面向评分的投入顺序

以下是工程证据与评分项的对应关系，**不是预估得分或保证加分**。官方评分转录中没有加速比换分公式、面积硬上限或必须达到 1ns 的规定。

| 评分项 | 分值 | 已有基础 | 下一轮最值得补强的内容 |
| --- | --- | --- | --- |
| 三阶段完整性 | 15＋20＋25＝60 | 环境/hello/vadd、规格与 RTL、正负/边界、NEMU/DiffTest、基线与周期证据 | 保持新入口的证据与当前版本绑定；不能把供体 PASS 借给新组合。正式设计/分析材料仍需成员完成，不能因工程通过就称已拿 60 分 |
| 技术路径与功能验证 | 10＋10＝20 | 复用香山向量体系；完整 128 位、异常、取消、反压、身份、DIV/SQRT 切换 | 实际消费者的 C ABI、输入输出边界和强 RVV 对照；新硬件保持原协议 |
| 微架构分析与软硬件协同 | 5＋5＝10 | O1/O2、H1、0f 的取舍及失败留档；模型—NEMU—RTL 链 | 定量解释一个瓶颈，说明真实软件收益为何不同于吞吐收益 |
| 设计独特性与扩展潜力 | 5＋5＝10 | 两槽弹性结构、低 32 位保存、T15 INT16 独立单元扩展 | 一个可直接使用的新接口/有界消费者；若证据充分，再增加一项成本可接受的硬件优化 |

报告、PPT、录屏和答辩按原分工在工程结束后由成员准备。本计划只维护必要的合同、程序、运行记录和证据；完整 LLM、模型质量或新增指令模式不因“看起来更大”自动获得独立分数。

### 0.3 对参考计划的调整

| 参考方向 | 本次判断 | 调整理由 |
| --- | --- | --- |
| 先恢复/核查基线 | 保留为一次小范围身份与接口核查，不重跑整套 R5 | 当前工程验收已完成；准备新实验不撤销旧资格 |
| split-input 8×32 | 已完成P0/P1/P1-R1，**HOLD，不再优先重试** | 生命周期已核查；两轮锚点未过原门槛，旧复制288B收益不等于当前C8可省成本 |
| 全面重跑三个公开项目 | 降为条件项，优先只研究 Jade 的依赖路径 | 已有固定历史比较；解释本项目瓶颈比反复争跨项目排名更有价值 |
| FP32→QKV | P3宿主/适配/有界校准完成，完整预算只读归因HOLD并暂存 | bit100 PASS，正常仅首FR窗口前缀；无完整上界，不重复校准，不继承供体性能 |
| 新 RTL | **当前NO-GO** | P4及唯一R1修订均未过完整成本门槛；不以其他写法继续试P4，不开启共享后端优化 |
| 多尺寸配置复用 | 4×8 允许一次有界归因，16×64更低优先 | 未改对照仍有逐窗漂移；不能只看均值或把失败改写成噪声 |
| 全核/复现/总验收 | 只对最终获选变化补必要检查 | 软件不变硬件无需重做综合；相同最终装载内容、调用计划及运行条件才可复用旧运行资格 |

### 0.4 后续工作包与顺序

下列 P0～P5 是本节的阅读顺序，实际认领继续使用表中的既有父包及明确叶级范围。P0完成；P1完成最小迁入及steady-d0并以HOLD停止，其他8镜像runtime未测。P2调用路径与本次依赖链叶已完成，P1-R1已实测HOLD；P4-G0/G1完成、G2成本NO-GO；G2R0/G2R1局部与成本已完成，R1成本37/47通过、10失败，P4收口。R2-S3/C8宿主及R1功能/差分通过，锚点与收益HOLD；只读归因已完成，关闭当前分段归约候选。P3最小迁入/宿主验证、0f观察器适配及单核有界校准完成；完整预算只读归因HOLD并暂存。P5只读稳定版收口已完成，未发现新增实现/目标验证缺项；其他可选包未启动。

**当前顺序：C8分段归约NO-GO关闭 → P3完整预算HOLD并暂存 → P5稳定版只读收口已完成 → 按发布需求整理待提交范围。** 不再重复P3短校准，不正式探针；P0/P1/P2/P4及旧失败保持，没有必须继续的优化。

| 顺序 / 工作包 | 具体动作 | 交付与进入下一步的条件 | 投入等级 |
| --- | --- | --- | --- |
| **P0：已完成，R0 / R2-SELECT** | 当前0f+C8、供体ffd668四源/六算法及工具实物已固定；真实消费者支持固定A/独立x，C8可缓存A、每次只更新32B x | [P0合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-p0/CONTRACT.md)及来源锁完成；准入可选接口验证，不预告74.5%收益；steady/first/native分别测 | 完成静态核查，0新构建/目标运行 |
| **P1：R2-S3，已完成探针，HOLD停止扩大** | 先迁入最小 leaf/完整 C 包装及对称 RVV；先 8×32、dataset0、正反顺序的功能与配对性能探针；通过后才扩到三数据集；每实现/窗口每数据集四正式样本，正反序各二 | 当前硬件上全 128 位、C ABI/向量状态合同/护栏、NEMU、负控恢复及公平比较合格；明确采用、仅保留接口能力或否决。首个可看的新增结果来自这一包 | 中：软件编译与受限 EMU，不先重建硬件 |
| **P2：R3 / R4，调用路径与依赖链叶已完成** | 复用已有汇编/轨迹，对实际接受→响应→写回/旁路→依赖消费者分段；普通 C 同时分析准备/调用/结果消费。证据不足时只补必要观察，必要外部对照限 Jade＋当前版 | 给出一个定量瓶颈及“值得改/不值得改”的判断。不能用静态指令减少替代周期证据；不同窗口不能靠相减推导成本 | 低到中；新增观察器需要匹配构建时再升级预算 |
| **P3：R2-S3，预算HOLD并暂存** | 固定ffd668b源闭包、宿主/0f适配和单核有界校准已完成；bit100 PASS，正常999988 guest限额，0完整窗 | 原14调用/6窗/1%锚点/3%收益保持；有利约5705秒情景不是上界。完整预算无法准入，不重复短校准，不替换默认 | 本轮只读收口；0新目标运行 |
| **P4：R3，已收口NO-GO** | 原G2的6失败、R1的10失败均保留；一拍候选继续默认关闭 | 不进入全核或周期后级，不继续改P4；当前采用0f | 结束本轮硬件探索 |
| **R2-S3/C8分段归约：只读归因后NO-GO关闭当前候选** | 6周期坐标差已分解，少8配置未缩短32笔dot完成进度；原R1的HOLD保持 | 不删锚点、不弱化RVV、不续跑后三项；新证据和不同机制才可另立候选 | 已结束；本轮只读，0新目标运行 |
| **P5：稳定版只读收口已完成** | 原0f源/配置、firstdot与C8入口、SDK和最终镜像/R5证据匹配；研究P4补丁与生产源明确分开 | 既有验收可复用；必补实现/目标运行/EDA为0；档案47条保持。发布前再明确提交范围，成员人工事务不冒充完成 | 无新目标/构建；可按需进入发布整理 |

**P1当前收口：** [结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/RESULT.md)已保留9镜像静态检查、steady-d0负控/正常/重放及全部原文。收益两顺序过3%，锚点3.4711%未过1%，因此HOLD；其余8镜像NOT_TESTED，不改默认、不自动扩大或推进新软件包采用。后续P2已进一步归因到同代间接调用预测纠正所在的leaf到达区间；P1-R1已完成并HOLD；依赖链及P4全部授权关卡已完成，G2/R1均成本NO-GO，现已收口。旧结果不重写，稳定0f+C8/firstdot继续使用，本轮没有新增目标试验。

### 0.5 P1 必须解决的公平比较问题

供体固定为 `zufan@ffd668bf1bc80850d382f514d13bb00316c85582`，先选择性迁入，不整分支合并。该提交的 split 结果为 **308.5 cycles**，匹配的最快 split RVV 为 **334.25 cycles**；旧 packed 完整窗口为 **1209.583333 cycles**，其中包含每次复制 288B 等工作。供体声称的 74.495350% 降幅来自这种特定边界，**不是当前 C8 273 cycles 的可直接提升空间，也不是 RTL 提速**。

| 消费者实际情况 | 公平对照应如何设置 | 不允许的比较 |
| --- | --- | --- |
| A/x 本来连续，直接满足 C8 | 现有 C8 与 split 从同样已准备数据开始，计入各自必须的参数/结果处理；同步比较最快 RVV | 为 C8 人为增加不需要的 memcpy |
| A/x 分离、每次都变化 | C8 适配需要的复制/准备 vs split直接读；两者及 RVV从同样分离输入开始，以同样输出形式结束 | vdot只测计算、RVV计入准备或多一次输出转换 |
| A 固定、x 每次变化 | 明确权重准备一次与每次更新部分；分别报首次、稳态及指定复用次数的摊销成本 | 每次给 packed 重打包固定 A，或只给 vdot 免费缓存 |
| 下游只需要 INT32 | 所有实现均包含必要结果提取；同时在功能测试检查完整 128 位指令结果 | 靠不验证高 96 位、缩短接口合同取得“加速” |
| QKV融合消费者 | 共同的量化语义、权重状态、输出和准备边界；记录 core 与消费者两个窗口，采用结论以完整消费者为准 | 把 GEMV、量化、首 token或完整模型的成绩混为一项 |

最小迁入只改当前组合必需的适配层，冻结供体源码/工具。若供体工具默认绑定另一版硬件或 caller，建立新合同和输出目录，不改旧 pins 让旧门禁“通过”。性能 ELF 与诊断 ELF分开标识；需要新观测时，不拿增加 instrumentation 后的周期冒充原性能镜像。

当前 C8/firstdot 和 RVV 放入新的配对 ELF 后，均须在新窗口重新计时；旧273/299只作历史参照，不能充当P1新比较的分母。最终软件包若再次改变装载地址、布局或调用计划，按影响补验。向量状态按具体C ABI合同建立并允许覆盖，不擅自加入供体未承诺的全量保存/恢复。

### 0.6 统一的采用门槛与停止条件

以下是**新试验建议预先采用的内部筛选规则，不是比赛官方标准**。开跑前将准确输入、比较格、路径、统计式和预算冻结；不得为已得到的结果追改门槛。旧合同要求的逐窗相等仍按旧合同执行。

| 维度 | 新试验采用原则 | 不满足时 |
| --- | --- | --- |
| 正确性与协议 | 完整 128 位、标量参考/NEMU、边界/非法配置、C ABI保存义务、向量状态建立及允许覆盖范围；硬件保持取消、反压、独立身份、DIV/SQRT和无停顿 II=1 | 优先定位/修复；不以性能收益抵销错误 |
| 软件性能 | 同硬件，在同一配对 ELF 内安排候选/合格对照；同输入、同输出、同计时范围；P1正反序与首尾锚点，P3独立冻结对称锚点计划；使用最快合格 RVV及当前合格入口 | 不能只选慢 RVV 或仅报告最好的一次 |
| 收益目标 | 对新完整消费者，建议以**相对当前最佳合格实现至少降低 3% 周期**作为性能升级筛选线；逐数据集/顺序判定，不用总体平均掩盖退化 | 未达标但有接口价值可单独记录为能力扩展，不宣布性能升级，不替换默认 |
| 稳定性 | 新应用建议锚点跨度≤1%；P1每实现/窗口为3数据集×4正式样本＝12，正反序各二，另做独立重放。P3真实输入/重复/锚点计划独立冻结，不冒称三数据集覆盖；保留全部样本 | 超限 HOLD，先解释原因；不得挑样本。既有控制逐窗必须相等的门禁不因1%规则放宽 |
| 硬件公平性 | 同最终 ELF/BIN、NEMU、配置与软件；分别报告微基准和真实消费者；至少保住当前 batch 吞吐及原合格场景 | 只有链微基准改善、真实消费者无价值时，不为追一个数字替换稳定版 |
| 面积与时序 | 仅修改当前VDot时，默认新RTL筛选目标是FU及VFEX4父级面积均不增加；若换承载单元/执行端口，必须按原父级＋新承载父级或受影响EXU集合的同功能联合边界比较，不漏算移出的硬件。沿现有保守口径，五档对应关键路径至多+1%、原非负slack不得新增负值，同时报告全部退化 | 若确需面积换延迟，先另立明确预算再试。局部控制变好不能覆盖其他路径失败；不修改旧门槛 |
| 试验预算 | 一项假设先做一次最小筛选，最多再做一次有证据支持的修订；扩大数据和全核运行必须由前级通过触发 | 仍无可复现价值即关闭，保留结果和回退；不无限搜索布尔写法或重复全量回归 |

加速比统一为 `最快合格RVV周期 / 候选周期`；软件优化收益为 `1 - 新周期 / 同条件原周期`。多尺寸、多数据集分别报，不给没有定义的“项目总加速比”。微基准和应用同时列；面积至少区分 FU/父级；时序至少区分全局路径、VDot相关路径和slack。没有实测功耗、P&R/CTS/SPEF及整核频率资格时，仍写 NOT_TESTED。

### 0.7 条件项与暂缓项

| 方向 | 实际空间与限制 | 处理 |
| --- | --- | --- |
| 4×8配置复用 | 原候选157.75→153 cycles（约3.01%），但未改 basic RVV均值225.25相同而逐窗±1；完整8KiB控制槽相同也不能解释调用历史状态 | 一次只读归因预算，必要时一个固定布局/固定调用计划的干预；未解释则保持 firstdot，当前不阻塞8×32分段归约宿主试验 |
| 16×64配置复用 | 707→702.75（0.6011%）；未改 RVV990→991，六窗变化 | 价值较低，消费者确实需要且有新归因才重开 |
| 4×13 | 配置复用未胜强 RVV；当前应保留 RVV选择 | 不扩大点积尾部优化矩阵 |
| H1b，32位保存缩至19位 | INT8 dot8 总和范围 −130048～131072，19位足够；理论13个DFF约58.786 μm²，仅约FU 0.340%/父级0.0206%，**不是净综合收益预测** | 低优先小试；先确认实际映射与参数边界，输出仍符号扩展低32位/高96位清零。只有净面积下降且相关五档路径不退化才考虑后级 |
| Jade式短延迟 | 历史依赖链有信号；其VIAluFix路径不同于当前含DIV的不定延迟VFEX4 | 必须先做P2。不能只改latency字段或把全部乘加硬塞一拍；算术/唤醒/端口路径只选一个有依据的候选 |
| 元数据裁剪 | 父级已消除VPU等未消费控制；perf在公共父级仍保留，实际全核净节省尚未证实；必要控制/身份需保留 | 不靠删除接口能力制造面积收益；配置化诊断若有新需求另立合同 |
| CSA、C1/C2/C3门控 | 已有成本/时序否决；C3-HF控制路径改善仍有25/45路径未过 | 没有新的瓶颈、库/约束或架构假设就不重开 |
| 生产INT16/更高VLEN | T15已有独立参数扩展验证，尚非生产全核支持 | 暂不为扩展规模引入新ISA/NEMU/全核复杂度；如未来开展必须独立定宽和语义 |
| 完整LLM、首token、大K/RMSNorm | 供体部分方向仍HOLD/正在由成员处理，当前QKV仅有界信号 | 不接管或重复长跑；只读取正式固定结论。完整模型质量、tokens/s不作为这轮验收目标 |

P3供体约 **3.4732%** 保守改善仅作来源线索，不能加入本项目成绩。当前已完成143源＋2 API和19历史对象、最小迁入、宿主门禁、0f适配及独立单核校准；正式最多3串行的[原有界合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/PROBE_CONTRACT.md)未执行。完整预算只读归因HOLD并暂存，不用前缀性能或供体成绩授予准入。共同量化＋QKV窗口不含pack、norm、attention、KV、FFN或完整token；两个真实位置中仅pos0计时，不冒称三个真实数据集。

### 0.8 三人协作、运行成本和收尾

这是建议分工，不代表已向成员派单。共享活动仍以[协作规则](collaboration-current.md)和有效认领为准；本轮没有发GitHub消息。

| 角色 | 建议负责 | 独立复核重点 |
| --- | --- | --- |
| A：软件接口 | P0/P1最小迁入、输入生命周期、C8/split/RVV调用及输出消费 | 不自证所有对照公平；交给B核查 |
| B：验证与测量 | 版本pins、标量/NEMU检查、顺序/锚点、原文复算、结果档案、最终干净复现 | 确认真实输入输出边界、完整128位、负控恢复和所有样本 |
| C：硬件与性能归因 | P2只读路径/周期分析；必要时P4单候选及成本筛选；协助参数扩展说明 | 核查共享接口、时序起终点及不同负载的解释，不先改RTL |

个人电脑上先小样本、后扩大，沿用现有资源上限；编译、EMU和综合分别安排可写输出，不并发争用冻结生成器。第一次探针先单进程，估计本机实际成本后再定批次；超时、磁盘/内存和单调时钟记录写入新合同。不能把宿主墙钟耗时当作目标芯片周期，也不能把供体机器耗时当作本机工期保证。

原路线允许没有新候选获选时进入P5；现P3已暂存、P4已否决，P5只读收口完成。稳定版及保留证据已明确回答：新版本在哪个真实负载、相对哪一版/哪个RVV、快多少；是否改变面积和时序；有哪些失败/未测边界；如何退回当前0f+C8。软件单独变化且硬件身份不变，注明沿用0f成本即可，不做无必要EDA。

已有R5/G5的原13＋新1组合验收及clean-02旧墙钟FAIL均保留；后续新运行继续记录单调时钟。团队标识仍待确定、Q01～Q07仍为内部合同待官方答复、同机Agent复现不等于独立成员验收；这些边界不因本计划消失，也不作为无限扩大优化的理由。未来修改生产RTL前仍须提前说明；提交/上传按当轮用户授权。

### 0.9 核查入口

- [2026-10-28公开工程/分支研究](public-vdot-review-and-plan-20261028.md)：公开项目历史口径、供体提交与候选来源。
- [R5/G5最终结果](../optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md)、[验收矩阵](../optimizations/o2/integration/firstdot-v2-0f/acceptance/acceptance-matrix.json)：当前已闭合范围与限制。
- [版本三指标对照](version-comparison-r5-g5-20261027.md)、[结构化来源](version-comparison-r5-g5-20261027.json)、[实测数据档案](version-data-ledger.md)：当前绝对值及旧取舍；当前实测档案47条；P5只读收口不追加新测量，全部旧失败/未测资格保留。
- [多尺寸配置复用结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-expanded-v1/RESULT.md)：8×32资格及其他尺寸未决证据。
- [C8最小包](../optimizations/o2/integration/firstdot-v2-0f/package/c8/RESULT.md)、[最终接入等价](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/RESULT.md)：稳定入口及新应用不能直接继承的边界。
- [H1实际映射审查](../optimizations/o2/result-width/R1_MAPPING_REVIEW.md)、[元数据审查](../optimizations/o2/r3-readonly/metadata/R3_METADATA_REVIEW.md)、[0f成本与周期](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md)、[C3-HF否决](../optimizations/o2/r3-div-gate/c3-hf/RESULT.md)：条件性硬件方向的依据。
- [T15扩展验证](t15-parameter-extension.md)、[官方评分转录](../../赛题要求与评分总览.md)：已有扩展证据、评分与内部筛选标准的区别。

## 历史规划与工程包定义

以下2026-10-25正文保留当时的任务定义、证据和默认顺序。**若与上面第0节冲突，以本页最新当前顺序及0f/R5状态为准。** 历史“未上传”“下一步T17”等措辞不描述本轮状态，不据此重跑已完成工程。

更新：2026-10-25（UTC+08:00；R3本地候选接续）。共享硬件源码基点：6d2abe403b07c297b8830a7d4f06e370b0a8e070；当前获选软件及普通调用入口见下表与[R4结果](../optimizations/o2/r2-select/ENTRY_RESULT.md)。团队集成分支 cc77-builder/riscv:zufan。实时活动见[协作入口](collaboration-current.md)，每轮成果及路线变化见[开发计分板](../../开发计分板.md)。

本路线只安排工程实现、验证、复现和性能优化。比赛报告、PPT、视频、答辩、平台提交及赛事事务由成员另行安排，不属于 Agent 的工程任务，也不作为工程推进的前置条件。开发只维护必要的运行说明、结果证据和简短计分板记录。

赛题技术目标、完整评分表及官方／内部合同边界统一见根目录[赛题要求与评分总览](../../赛题要求与评分总览.md)。每轮先读计分板的近期“路线影响／接续”，结合 Issue 和真实运行恢复工作，再使用本路线选包；上轮聊天不是接续依据。

## SP1最后第19项自主接续（记录116）

观察EMU两角色诊断及原M1有效字段中性完成；原批次FAIL保留并有离线纠正，正式19/20。下一动作M2仅延迟F2v竞争源，保持原覆盖，准入后新身份有界补测；用户已授权包内连续推进，无需逐轮请求指令。不切默认、不上传。[完整结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-r1-20261108/RESULT.md)。

## 1. 当前从哪里出发

沿 O2 两槽弹性 FU＋H1 低 32 位结果保存继续开发，O1、原 O2 B0 保留为固定对照与回退。已有实现先复用，缺什么补什么，不从头重做全部阶段。

| 对象 | 已知事实 | 当前边界 |
| --- | --- | --- |
| 合并 6d2abe403 | [MERGE-REG 新夹具回归](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)完成12 core＋2 supplement，13完整正常轨迹、1预期拒错及六项O2覆盖；原实物与封存原文复算均PASS | 绑定6d2/1a23和新6e8b夹具；旧9b3、B0/H1合同缺项保留，不转移到新构建 |
| O2 吞吐 | 历史 batch128 相对 O1 周期少 39.03%，相对当轮 RVV 为 3.068×；无停顿 II=1、首响应 2 拍 | 不能推广为应用或 LLM 端到端收益 |
| GEMV | 历史 O2 相对 O1 端到端少 0.62%～1.50%；4×13 对较快 RVV 为 0.907× | 当前先解决尾部、搬运和配置开销，比较完整应用周期 |
| H1 | 历史 96 对正式窗口周期相同；FU 面积少 2.33386%、父级少 0.137349%，部分 STA 路径回退 | 32 位保存已完成，不重做；没有整核频率／功耗改善结论 |
| S2 | [固定完整布局重测](../optimizations/o2/r2-safe-tail/FIXED_RESULT.md)完成31次整核进程/384正式窗口；K13 reuse/endtoend 210→187周期（−10.952%），basic退化21.117%，16×64整BIN及窗口不变。另5次强RVV探针/32窗口正确性和重放PASS | 同镜像dataset0/endtoend下S2 reuse187对较快RVV175.25，慢6.705%；按停止条件不扩大S2采用矩阵，不冒称强RVV完整12样本资格。保留S1 RVV与S0 vdot回退，旧B0/H1仍BLOCKED |
| S1 | [独立实现及固定布局主批](../optimizations/o2/r2-vector-accum/VALIDATION.md)完成57次整核进程、768正式窗口，另4次小尺寸进程重放及两项原文重算均PASS；4×8／8×32／16×64的reuse vdot端到端周期下降5.7751%／12.5%／17.1589%，保留同步优化后的更快RVV | K13的S1 vdot退化1.3095%，不采用；保留S0 vdot回退和更快的S1 RVV。单项资格及原镜像选择/导出已闭合；不代表新caller、默认入口、T17或完整应用收益 |
| R4 调用入口 | [普通RV64 C ABI GEMV入口](../optimizations/o2/r2-select/ENTRY_RESULT.md)完成33次性能进程／384正式窗口／192全窗口重放比较；另3次普通C进程覆盖16公共函数、48个不同case和96正常调用 | 新调用窗中4×8／8×32／16×64选S1 reuse vdot，较最快同入口RVV少9.4667%／2.7431%／7.9859%周期；K13选S1 reuse RVV。只闭合调用入口影响，完整MERGE-REG、T17和默认切换分别验收 |
| R3 | [DIV取消关钟修复0f](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md)已通过全核/NEMU及96对窗口周期不变；batch保持3.067873×RVV，父级部分STA退化已留档 | [C3-HF最小试验](../optimizations/o2/r3-div-gate/c3-hf/RESULT.md)完成：只改FP DIV/SQRT hold置位，原门控/接收/双hold保留；局部功能通过，父级面积+0.184115%，三控制D最差1.930584→1.609770ns，五档20/45路径通过、25/45未通过。成本拒绝，关闭本轮门控优化；保留0f，转回稳定集成和T17干净复现。无新全核、周期、功耗或整核Fmax；未上传。旧C1/C2否决保持；今后改RTL仍提前告知，数据追加[版本档案](version-data-ledger.md) |

依据：[历史项目状态](project-status-20261020.md)、[H1 成本与时序](../optimizations/o2/result-width/h1/H1_RESULT.md)、[H1 周期](../optimizations/o2/result-width/h1/performance/B0_H1_RESULT.md)、[R2 入口](../../R2_STATUS.md)。结果绑定各自源码、配置和输入；运行是否结束须读实际 state、日志和进程。

## 2. Agent 按当前任务包执行与证据调整

在当前用户已授权的工程范围内，**沿当前规划的 14 个工程包及默认次序推进，Agent 无需每一轮重新搜索和规划全部可能方向**。工作包界定做什么、完成条件；Agent 在包内自主决定实现方法、试验和验证顺序。数量不是约束：新证据优先形成现有包的子项，确有独立目标或验收边界时按第 6 节调整工作包。

1. **先接续。** 核实当前 SHA、工作树、真实运行、最新结论和 Issue 有效认领；合格历史结果复用，仍在运行的任务继续观察，不重复启动。进程已结束时先读对应入口的恢复能力；S2 当前不能断点续跑，处理方式见[筛选合同的中断与重复构建限制](../optimizations/o2/r2-safe-tail/FULLCORE_VALIDATION.md#中断与重复构建限制)。
2. **按序选空闲包并 WORK。** `MERGE-REG` 的[新夹具拒错／正常恢复及相容旧日志复核](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)已闭合，绑定与R4相同的6d2/1a23硬件。`R2-S2` 已完成固定布局主批和强 RVV 有界取舍：reuse 相对 S0 的收益真实，但未胜过同镜像较快 RVV，当前停止扩大采用。`R2-SELECT` 的[原镜像选择/查询/导出](../optimizations/o2/r2-select/RESULT.md)已完成，`R4/O5` 的[普通调用入口子项](../optimizations/o2/r2-select/ENTRY_RESULT.md)已闭合新路径的性能及普通C使用验证。下一步以已闭合的MERGE-REG及R4固定身份为比较基线，完成T17干净依赖、实际构建与新身份运行复算；不等待firstdot。未来若再改caller/调度或链接布局，仍先在8×32/dataset0/endtoend与最快同入口RVV配对验证，不转借旧窗口PASS。原 B0/H1 固定实物未变化时不重复预检；这不是固定人员分工。若本包已有认领或冲突，按现有表选择下一输入就绪、未占用的**准确叶级包**。按[协作约定](collaboration-current.md)发布 WORK 后回读；不允许同包重复开发，也要检查公共生成器、接口和重型资源。
3. **包内连续自主工作。** 实现、主机检查、真实验证、定位问题、修订与提交不逐步征求确认。正确性失败优先修复受影响层级；无收益和退化依据第 4 节明确采用、再试一次有依据的修订或关闭。
4. **仅有理由才换包。** 被认领、依赖缺失、实际资源冲突或技术证据要求调整时，用 PAUSE/UPDATE 记录原因、是否释放及残留保护，改选已规划的独立包。缺什么补 `R0` 的对应子项，不为了填表反复预检，也不转去制作比赛材料。
5. **区分 R0 / S2 / 新硬件候选。** S2 的 `preflight` 分别报告 `build_ready` 和 `runtime_ready`。仅前者满足，可先 `--action build` 构建并静态检查 26 份 ELF，仍不得声称 EMU 或 DiffTest PASS；只有运行来源和所有固定回执齐备才能 `--action all`。历史 B0 使用其 `repro.py` 与旧版本锁；当前 H1／新 RTL 使用匹配的源码、硬件 pins 与新构建身份，不能拿 B0 锁拒绝新合法构建。
6. **阶段交付。** 候选进入 READY 等待按短窗口集成；完成采用/否决和相应验证后 DONE 并记一条计分板成果。获选组合走 `R4/O5 → T17 → R5/G5`，留下可用稳定版本及回退。条件探索不是必须逐项做完。

S1/S2 是不同叶级包，但 `candidate.py` 被 S2 的完整 Git blob 合同冻结：**S1 默认以独立候选模块实现**，只读引用原 O3 生成器/模型。确需修改相同文件时先协调版本和输出边界；旧 S2 在冻结提交复现，新候选明确新源码身份与检查条件，不静默放宽旧验证。

## 3. 工程工作包全表


沿用现有编号，以下为**当前规划的 14 个工程包**；默认次序见第 2 节，条件探索可以不开展，同一父包不构成对所有子项的排他认领。表格维护当前入口和决定，执行者及运行中／暂停等实时状态只放协调 Issue。

### A. 只补实际缺失的工程能力

| 工作包 | 当前从哪里开始／前置 | 完成条件与入口 |
| --- | --- | --- |
| MERGE-REG 合并基线回归 | [新夹具合同与原始证据交付](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)完成；12旧正常任务复用来源逐字节复核，新matrix0负控→新正常恢复2次实际执行；本轮接续新增EMU为0 | 原实物审计与558载荷归档的完整架构／异常／控制／dense／O2离线复算PASS。与R4固定6d2/1a23相容；旧9b3缺项、B0/H1旧合同与新构建身份分别保留 |
| R0 运行输入与复现缺项 | 只对当前实验缺的工具、依赖、正常／故障 NEMU、AM、flash、镜像和构建身份做预检与恢复 | 输入有来源或构建命令及校验方式；新机器能取得所需输入，配置不依赖个人目录，见[复现入口](../optimizations/o2/repro/README.md)。环境已满足时直接跳过 |
| T03 技术要求与语义缺项 | 对照[规格](../spec/vdot.md)及已有实现／验收，定位真正未覆盖的技术要求；Q01～Q07 区分现行内部合同、已获答复与未答复项 | 缺项补实现或对应测试；语义变化同步 RTL/NEMU/封装/测试。沿现行合同可继续工程开发，未答复不伪写官方认可，也不无条件阻塞所有优化 |
| T04 hello/vadd 与调试链路 | 复用[阶段一记录](stage1.md)；仅在实际缺失、源码变化或需要当前版本证明时补跑 hello、vadd 与短窗口波形 | 工程可运行、结果可校验、源码／执行路径及必要波形可定位；团队输出按已知信息配置。不包括报告、录屏或演示材料制作 |

negative-reference.so 是故障注入夹具，不是正常黄金 NEMU；不能把新哈希填进旧锁冒充原文件。无法恢复旧二进制时保留旧验收缺项，以新身份重建夹具并验证预期拒错和同镜像正常恢复。不得修改任何仍在运行的物理输入。

### B. 持续优化：先测现有候选，再按瓶颈扩展

| 工作包 | 当前从哪里开始／前置 | 完成条件与入口 |
| --- | --- | --- |
| R2-S2 安全尾部筛选 | [新固定布局合同与结果](../optimizations/o2/r2-safe-tail/FIXED_RESULT.md)闭合S0→S2单项因果比较；两形状/三数据集/basic-reuse/core-endtoend、负控恢复及重放PASS。另以仅RVV两槽改变的同镜像K13/endtoend探针比较已合格S1 RVV | 当前reuse相对S0少10.952%，却在dataset0探针比强RVV慢6.705%；basic退化，不扩大采用矩阵。该探针为4窗口单元格，不是强RVV全矩阵资格。保留完整原始数据、旧合同/哈希/归档；只有新可检验假设才重开。原[固定B0/H1合同](../optimizations/o2/r2-safe-tail/FULLCORE_VALIDATION.md)仍BLOCKED，不重跑未变缺项，也不以合并EMU替代旧对照或MERGE-REG |
| R2-S1 向量累加与对等 RVV | [独立S1模块](../optimizations/o2/r2-vector-accum/README.md)、完整主批、小尺寸补充及归档验收均完成；前三个整块形状的reuse进入R2-SELECT，K13不采用S1 vdot但保留更快S1 RVV | 后续子项为[首块直接初始化](../optimizations/o2/r2-vector-accum/VALIDATION.md#首块直接初始化的后续子项)：16 AM ELF／8对布局／576模型试验已通过，尚无运行资格。增加独立精确再生／运行合同，验证实际目的变更的负控及恢复，再与原S1和最快合格RVV配对测量。不得把静态少指令当收益，不能覆盖原批次 |
| R2-S3 后续应用瓶颈优化 | S1/S2 结果或汇编／周期诊断证明仍有可改善开销时启用；一次只检验一个假设，如调度、搬运、配置切换或混合尾部 | 不重复已有输入复用、四行交错和展开；把处理成本与寄存器压力计入公平窗口。有效候选进入 R2-SELECT，无效则关闭；新发现的软件候选优先作为本包子项 |
| R3 硬件成本／关键路径优化 | [C3-HF最小试验](../optimizations/o2/r3-div-gate/c3-hf/RESULT.md)完成：只改FP DIV/SQRT hold置位，原门控/接收/双hold保留；局部功能通过，父级面积+0.184115%，三控制D最差1.930584→1.609770ns，五档20/45路径通过、25/45未通过。成本拒绝，关闭本轮门控优化；保留0f，转回稳定集成和T17干净复现。无新全核、周期、功耗或整核Fmax；未上传。旧C1/C2否决保持；今后改RTL仍提前告知，数据追加[版本档案](version-data-ledger.md) | 不自动扩大改法、不放宽阈值，不将局部PASS转授T17；稳定工程接续按R4/O5、T17、R5/G5各自合同执行。发布仍按用户授权 |
| R1-H1b 19 位保存备选 | 默认不开展；32 位 H1 已完成，只有新增映射证据表明继续收窄值得才开启 | 19→32 符号扩展、高 96 位清零及边界正确，并有实际收益；否则关闭，见[H1 合同](../optimizations/o2/result-width/h1/CONTRACT.md) |
| T15-REPRO 参数扩展复核 | 已有[参数合同](../spec/t15-parameters.md)及[结果](t15-parameter-extension.md)先复用；只在相关实现变化、扩展验收缺项或有优化依据时重开 | 独立 INT16×8／64 位结果扩展在其范围内可复现；不扩大为生产整核支持，不作为默认 INT8 优化的前置 |
| R2-SELECT 应用与组合取舍 | [原镜像选择、查询与导出](../optimizations/o2/r2-select/RESULT.md)已完成：复算S1 v2完整768窗口/64候选格，每格12窗口；三个整块形状选S1 reuse vdot，K13选较快S1 reuse RVV并保留S0 vdot回退。48份完整原镜像精确导出，Linux/Windows各21项测试通过 | 本次只闭合原镜像数据层，未新增运行时或默认入口；实际export/verify/resolve见[入口](../optimizations/o2/r2-select/README.md)。新caller/dispatcher/合并ELF由R4/O5验证实际新增影响，先测8×32/dataset0/endtoend且强RVV走相同新调用路径；原10.75周期余量只作筛选依据。T17及R5/G5仍须独立闭合，不拼接不相容PASS |

S2 保持 dot8 合法域，安全读取剩余 5 项、显式补零、恢复 VL=8，全部成本计入窗口；16×64 是不应变化的控制形状。新合并 EMU 不能冒充合同中的 B0/H1。S1 先独立验证，组合收益不能代替单项归因。R3 保留 ROB、pdest、异常、写使能、两槽独立身份、必要观测、II=1、首响应 2 拍、反压／取消与 DIV 互斥；577 位额外信息不是可以直接删除的数量。

### C. 将获选方案闭合为稳定、可复现的工程

| 工作包 | 当前从哪里开始／前置 | 完成条件与入口 |
| --- | --- | --- |
| R4/O5 获选组合回归 | [新普通调用入口](../optimizations/o2/r2-select/ENTRY_RESULT.md)已完成24个性能ELF和1个普通C ELF的影响验证、原始证据复算及公共源码交付；硬件仍为固定6d2/1a23身份 | 调用入口与[MERGE-REG](../optimizations/o2/fullcore/MERGED_REGRESSION_RESULT.md)的功能／异常／控制证据均绑定相同6d2/1a23身份，进入T17；完整全宽结果、差分拒错／恢复、性能及必要成本证据一致，无未解释失败。只复测变化影响，不拼接不相容PASS |
| T17 干净环境复现 | 获选组合明确后，另一 Agent 或成员在干净目录取得完整依赖，实际构建、运行和复算；输入准备可提前并行 | 源码／依赖／镜像／命令可追溯，结果和差异可解释。注明真实执行者；Agent 复现不冒充成员人工验收，不等待人工签名才继续工程优化 |
| R5/G5 稳定版本与默认入口 | R4 和 T17 通过，所选范围内必要技术缺项已闭合；按已有授权使默认构建与运行入口指向选中配置，未授权切换时先保留明确候选入口 | 源码、子库／补丁、工具配置、输入和结果身份齐全，入口可运行，回退可取得；形成可供成员使用的稳定工程版本。有新证据可继续下一轮优化，不按旧日期强制终止开发 |

## 4. 每轮实验怎样决定下一步

开始前在已有结果文件或实验记录写清：假设、固定输入／修改范围、主要指标与可接受代价、最小实验和资源预算。已有合同足够时直接引用，不重复建文件。默认先用主机／静态检查和冒烟排除无效候选，再扩大验证。

| 结果 | 下一动作 |
| --- | --- |
| 正确性、身份、异常或边界安全失败 | 停止该候选的性能判断，修复最小失败并重测受影响层级；其他独立工作继续 |
| 环境／固定输入缺失 | 补 R0 的具体缺项，保留 BLOCKED 与已尝试动作；另一条线做独立原型／分析，不换不明二进制或改旧锁凑通过 |
| S2 或 S1 有可重放端到端收益，控制样本无未解释变化 | 进入 R2-SELECT 和组合回归；保持单项归因，再决定是否组合 |
| 无收益、退化，或更强 RVV 消除了优势 | 保留较好基线；依据完整数据选择一次有针对性的修订、转下一个瓶颈或关闭。只有 core 改善不能写成端到端收益 |
| R3 字段必要、路径不属于 VDot、收益不足或破坏观测 | 关闭该假设，记录依据，不为完成工作包强改 RTL |
| 面积更小但时序变差，或一个形状改善而其他形状退化 | 按事先指标衡量整体取舍，可保留分场景候选；不只取最佳样本、不事后换约束或降低门槛 |
| 新数据推翻当前瓶颈判断 | 更新相应工作包的下一动作，将新假设放入 R2-S3／R3 子项，先做最小实验；ISA 或公平合同变化单独定义身份和验证 |
| 当前候选均无采用价值，或达到用户预算／本轮停止条件 | 完成已获选组合的工程闭环，报告稳定版本、排除的方向和尚未验证的假设；不声称已达理论最优，不为保持忙碌无限开题 |

每个最小实验必须有能作决定的终点。达到约定预算或重复得到同类失败而无新证据时，先作取舍，不自动续开相同尝试；新证据才能重开已否决候选。软件以选定场景的 endtoend 周期和较快合格 RVV 为主，同时保留 core 与其余尺寸；硬件同时检查功能、接口、周期、面积和相关 STA，不把宿主耗时当处理器周期。

## 5. 工程完成与继续优化的边界

工程达标要有以下可定位的实现和验证；适用的历史证据可复用，有变化才按影响补测：

- 环境与 hello/vadd 可运行，必要调试和波形链路可用；vdot 的算术、编码、接入和向量状态符合当前明确标识的技术合同。
- 正数、负数、边界、全 128 位结果、别名、异常和流水控制有对应测试；NEMU 扩展与真实 DiffTest 有正常通过、故障捕获及同镜像恢复证据。
- 有正确且公平的 RVV 等价实现，以及延迟、吞吐和应用端到端的可重放比较；性能结论明确实现、尺寸、数据、配置和覆盖边界。
- 选中源码、依赖／补丁、构建与运行入口可在干净目录复现；未解决项如实记录，必要技术缺项未闭合就不能宣称全部达标。

达标后以稳定版本为保底持续优化；一个候选失败不影响已有成果，一个候选成功也不意味着不再优化。条件探索不要求全部做完，停止依据是用户目标／预算和当前证据，而非把工作包逐行打勾。比赛材料和人工事务不纳入上述工程闭环。

## 6. 只维护当前决定

普通工作更新相关结果并追加一条计分板记录；只有当前选择、前置或下一动作改变才更新本路线。结论及理由写计分板，详细数据留原处，本文件不累积逐日进度。已关闭工作包只留一行采用／不采用／完成结论和证据。

新增工作优先作为已有包的子项；只有新目标、独立验收或明确依赖边界才增包。旧计划、旧排期和 T16／T18 等材料事务只供历史追溯，不驱动当前 Agent 队列；已完成的 H1、T05～T15 等工作不因路线整理重新启动。技术要求来源和未确认项沿[vdot 规格](../spec/vdot.md)读取；获得新的真实要求时更新受影响的工程包，不把未确认内容写成事实。


## 2026-11-08 记录117：M2未命中，保留19/20

结论：NOT_HIT，19/20。bit100、41次功能调用、77次custom、完整128位与CSR/ABI、NEMU差分通过；P入队和真实父级反压均未命中，不计为第19项通过。

两个进程合计605.237秒，正常267234 guest cycles/579.294秒，均在预算内。完整时序：S1全部36次F2v结束早于A响应5拍；S0原四相位差4/7/9/15拍。M2确实后移压力，但不足以重叠，原FAIL和锁保留。

下一步仅在scratch ft3链再加两条依赖FMUL；数据、分支、原相位与完整覆盖不变。此前考虑一条，完整S1证据显示不足，故选择两条；不扫描相位。

本轮未测性能、面积、时序，均NOT_TESTED。历史SP1 chain加速比3.397658×（0f 2.929725×）；FU面积18322.878 μm²、父级285241.642 μm²；标称Q分别1.790381/3.337809 ns（Q=T−slack，不是全核Fmax）。未切默认，未上传。

证据：`team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-m2-fp-pressure-20261108/RESULT.json`。


## 2026-11-08 记录118：M3 完整未命中

NOT_HIT，19/20。bit100与完整41调用、77custom、全128位、CSR/ABI、NEMU差分通过，正常267397 guest/580.931秒。两个目标累计606.085秒；未重试、未加时。

40个A中39个在F2v末写后3拍响应，另一项5拍；P/反压仍0。FEX0与VFEX4共享写口且OG0也仲裁，VFEX3与VFEX4共享读口，不能将压力延迟视为独立旋钮。完整时序及源码支持一次M4：多一条依赖FMUL把F2v首写后移约4拍，使A/B有机会先经过OG0/OG2。保留旧FAIL、原相位和覆盖。

M3最初PC清单仍引用M2的宿主准入已撤销（零目标），runtime-r1绑定新manifest并通过负控后才启动。三个指标本轮NOT_TESTED；历史chain3.397658×、FU18322.878 μm²/标称Q1.790381ns、父级285241.642 μm²/Q3.337809ns均未重测。默认0f未切换，未上传。

证据：`team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-m3-runtime-r1-20261108/RESULT.json`。


## 2026-11-08 记录119：M4 全核命中 S0/S1，重放待完成

结论：GO 进入最终重放；仍为19/20，尚未把校准等同最终验收。bit100拒错25.346秒/11668guest通过；正常586.634秒/267845guest通过；目标总611.980秒。

|覆盖|真实证据|
|---|---|
|S0|phase0，R=A seq1，B seq2在17988进入P，17989双槽占用；双方完整响应/提交|
|S1|phase4第九次指定probe，R=A seq76/ROB1:30，B seq77/ROB1:36在262616进入P；262617来自ROB1:35的取消杀P保R；A在262624响应；B无响应/提交|
|完整检查|41调用、77提交、78接受，完整128位及实际C端CSR/ABI检查、NEMU差分；725侧带响应闭合|
|累计事件|ENQUEUE_P34、STALL296、KILL_P1、PARTIAL_KILL1|

M1/M2/M3原未命中记录保留。M4仅软件scratch依赖链，无RTL/EMU重构或默认切换。

本轮加速比、面积、时序均NOT_TESTED；历史SP1chain3.397658×（0f2.929725×）；FU18322.878 μm²、Q1.790381ns；父级285241.642 μm²、Q3.337809ns。Q为T−slack，非全核时钟。

下一步集中完成原SP1功能EMU观察中性、补测同核精确重放、0f补测数值对照及原o2-control双核重放。保留原覆盖、每角色预算和失败即停；不切默认、不上传。

证据：`team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-m4-fp-pressure-20261108/RESULT.json`。
