# 第19项观察EMU构建 R4-R3-R1 结果（记录114）

**结论：GO——新观察EMU构建PASS，构建阻塞解除；诊断执行仍待准入，正式验收仍19/20。默认0f＋firstdot V2＋原C8不变。**

开始：2026-11-08T01:06:22.126707+08:00；归档：2026-11-08T01:26:24.784778+08:00。本地分支`local/zjhwork-integration-20261024`，未提交，基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。

## 实际结果

|项目|结果|
|---|---|
|唯一检查器行为修订|header只按LF分行；裸CR、CRLF及末尾换行均按原sed字节语义保留|
|必要宿主验证|15项PASS；复用旧小样，不重跑小样Make/JVM/firtool|
|完整冻结|8项PASS；24595源文件、18360外部文件、2151受保护文件、1411目录|
|原Make后处理|PASS；1608个SV精确结果一致，其他79件生成物保持|
|Verilator及原生编译/链接|PASS；单次退出0，未重试、未加时|
|有界构建用时|监督器单调计时851.429秒，约14分11秒；上限3600秒|
|资源|峰值RSS 7.480949GiB／16GiB，峰值10线程，输出日志7380字节|
|构建后复核|冻结输入、旧失败证据、Git逻辑身份均保持；所有构建进程退出|
|目标运行|EMU/NEMU均0次；无第19项新覆盖命中或性能窗口|

新的EMU为71,379,320字节，SHA-256：

`fc25f9e2a22cc1c51e4a4884c03c6d84e950fcbb1925eb55a448de104273f742`

生成路径：`/home/riscv/riscv-lab/item19-observer-20261107/build-03/source/build/emu`。

固定副本：`/home/riscv/riscv-lab/item19-observer-20261107/artifacts-r4-r3-r1/emu`，逐字节摘要与生成文件相同。仅使用readelf做静态ELF检查，未执行二进制。完整身份见`EMU_IDENTITY.json`、`FROZEN_EMU.json`和`FINAL_ARTIFACT_PINS.json`。

## 为什么这次通过，为什么还不是20/20

上轮FAIL来自新增宿主检查器将147处裸CR视为行界，多插294字节。本轮只修LF语义；7类行尾样例以GNU sed作为字节参考，旧小样真实结果精确通过；缺失版本头、双重版本头、未转换断言和多插CR前缀仍被拒绝。原Make行为、生产RTL和软件镜像没有变化。

这次确实完成了原Make后处理、Verilator、C++编译及链接；采样未见JVM/firtool重跑或EMU/NEMU执行。它使下一轮能够观察真实全核时序，但不证明S0反压入P、S1杀P留R已命中。第19项缺项及收口顺序见[说明](WHY_ITEM19_IS_PENDING.md)。前几轮宿主工具/检查器问题确实拖慢了进度，不能把它们说成RTL功能不通过。

## 计时证据边界

本轮停止合同由单调时钟和外部timeout监督。单调耗时851.429秒；UTC起止时间戳差807.711738秒，两者相差43.717535秒，原记录完整保留。未归因系统时钟差异，不宣称UTC墙钟一致性审计通过。两种观测均在3600秒内；这里的构建PASS不扩大为新时钟审计或性能资格。

## 三项指标与采用

加速比、面积、时序本轮均NOT_TESTED，历史数据见[指标表](METRICS.md)。构建资源不能当作处理器性能。默认未切换，旧EMU与原M1镜像保持，旧FAIL和锁不变；无EDA、GitHub上传或生产RTL修改。

## 下一步

建议同一轮集中做新EMU两角色诊断准入；合同、必要差异检查及预算全部通过后，按新授权运行bit100拒错及原M1正常诊断。预算依据不足HOLD，诊断允许保留未命中事实但不能授予第19项PASS；不自动修改M2或重放。详见[NEXT_STEP](NEXT_STEP.md)。

## 证据入口

- `checker.patch`、`HOST_RESULT.json`：最小修订与15项宿主验证。
- `FREEZE_CHECKS.json`、`INPUTS.json`、`EXECUTION_FREEZE.json`、`BUILD_CONTRACT.json`：完整冻结与唯一执行预算。
- `build-run-01/STATE.json`、日志和telemetry、`BUILD_RESULT.json`：真实构建全过程。
- `POSTPROCESS_RESULT.json`、`BUILD_PHASE_SUMMARY.json`、`POST_INPUT_CHECK.json`：阶段与输入复核。
- `TIME_ACCOUNTING.json`：单调/UTC两种时间原始差异。
