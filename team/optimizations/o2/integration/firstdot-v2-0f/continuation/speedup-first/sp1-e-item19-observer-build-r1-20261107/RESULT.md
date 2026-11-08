# 第19项构建入口R1（记录106）

**宿主修复GO；实际构建HOLD（RSS_LIMIT），诊断继续HOLD。** 已执行一次构建，没有重试。正式进度仍19/20，默认0f＋firstdot V2＋原C8不变。

|阶段|结果|
|---|---|
|exec前CPU4–5亲和设置及/proc生命周期读取|已修复宿主入口，RTL未改|
|正常退出、退出码7、精确超时整组回收|3项PASS，启用failfast，每例回执永久保留|
|完整源码/外部依赖/旧保护输入|启动前24596＋7820＋449项核对通过|
|香山Scala主体及测试入口编译|通过|
|Chisel展开|完成，保留约1.038GB FIR|
|firtool lowering及后续native EMU|未完成；整组RSS超限停止|
|停止/回收|378.804秒触发，380.636秒回收完毕，remaining=[]|
|EMU/NEMU运行、EDA、GitHub写入|全部0|
|新加速比、面积、时序|NOT_TESTED，历史指标沿用|

峰值RSS为17211658240字节，约16.030GiB，超过冻结16GiB上限约30.32MiB。现场保留约4.555GiB的Mill进程、约9.997GiB的展开JVM及约1.360GiB的firtool；不是3600秒超时。没有可交付的新build/emu，也没有仿真正确性或新覆盖结果。

## 身份与失败保留

旧R0失败未改。失败后7820外部输入、449保护输入全部未变；24596项独立源码快照仅.git/index字节变化。INDEX_REVIEW证明新旧HEAD一致、暂存path/mode/blob/stage条目完全一致，原候选index仍匹配冻结起点；RTL和源码内容没有漂移。原不可变字节合同的POST_INPUT_CHECK=FAIL如实保留，不抹成通过。下一轮应把索引stat缓存与不可变内容分开管理，而非放宽源码核验。

保留本轮RUN.lock、STATE/LIMIT/telemetry、stdout/stderr、未完成生成物和编译缓存，未清理重跑。没有EMU/NEMU、EDA或默认切换。当前已无本轮构建进程。

## 接续

建议R2采用编译与展开分阶段入口，复用冻结编译类，先退出Mill编译进程再运行同配置top.SimTop，保留原Make全部后处理。这有减少并存内存的依据，但并不保证全流程峰值；保持原16GiB和新的单次3600秒有界构建，失败即停。只有用户发起下一轮才实施。

[下一轮完整指令](NEXT_STEP.md) · [资源归因](RESOURCE_ANALYSIS.md) · [历史三指标](METRICS.md) · [原始失败回执](build-run-01/STATE.json)。两角色诊断草案沿用上轮，当前未获运行准入，不把观察构建或诊断完成算成第19项PASS。
