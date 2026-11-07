# signed8 真实父级 overlay v3 有限验证合同

状态：控制器尚未执行构建、仿真或授予父级资格。

## 输入与范围

只验证 local-03 已实际生成、SAT 证明并通过两个 feature FU 的 signed8 候选，固定其 candidate 源 SHA `50522c0cd2700f7f852872049533bc31f79ce811ad2ed53da2c1d333cece45e2`。调用时必须提供 local-03 原 `result.json` 的完整原件 SHA；同时固定其 `inputs.json`、完整 `overlay-classes.json` 和原 generation-01 recipe/classpath 身份。

复用原 `parent-flag0-01`、`parent-flag1-01` 的实际 source-snapshot 和生成物。父级 source map 的 16 个文件逐一固定 SHA，两态必须相同；每个原完成回执及 `campaign/generated-files.json` 也固定 SHA。已核实际生成清单为 57 项 list，每项包含相对 campaign 的 `path`、`sha256`、`bytes`，覆盖 56 个 SV/V 和原黑盒资源表。原源码、缓存、类目录、合同、检查器、失败证据及在途 EMU 均只读。

候选的完整 overlay 目录在编译和运行 classpath 中优先，包含匿名 Bundle 类。只将未改的 `GenerateVDotElasticParent.scala` 编译到新外部 harness classes，不重编算术、不调用 Mill、不建立新 checkout、不构建或运行整核。

## 真实父级及判定器

原 harness 保留真实 VFEX4 ExeUnit、原 dispatch、ClockGate、VDotElastic、VIDiv、VFDiv 和三条写回路径。时钟、复位、两槽协议、最早 E2 响应与无停顿 II1 沿原合同；这里验证直接送入的已解码请求，不包含译码、Rename、RF 或 ROB 提交。

每态新生成全部真实 SV/V，检查旧父级完整文件集合只增加 `VDotSignedByteProduct.sv`。inline 必须与 local-03 已验证字节相同；Products 按下述精确公共头部规则比较，其完整模块正文必须与 local-03 相同。除 Products、新增 external-module 注释与下述三个完整错误日志块的对象标签和排列外，其余 SV/V（包括父级、ClockGate、DIV、VDotElastic）逐字节等于对应原 feature。资源清单保持旧 ClockGate 等资源并增加 signed8；检查真实 filelist，不假设父级只有五个文件。

## v3 的有限生成文本比较边界

v1 的 parent-01 在 feature0 真实生成后、lint/构建/仿真前因 `LogPerfEndpoint.sv` 字节差异停止。v2 的 parent-02 同样在原 checker 测试、harness 编译和 feature0 生成后，因三个完整日志块的排列变化在静态比较处停止；两个失败输出和 v2 均保留。两次实物的 Products、SignedByteProduct、external-module 注释 SHA 完全相同。v3 沿用 v2 的 Products 比较，只对 `compare_log_object_labels` 增加下述三个已知独立块的排列比较；绝不重写实际 RTL、日志或原 checker，其他运行和资格门槛不变。

1. **Products 公共宏头。** parent-01 实发 `VDotProducts.sv` 为 2335 字节、SHA `67b6c822ef838cf5a26ff05c71798cd858475bb01131672abcb7aae6aed4c3de`。相比 local-03 的 2080 字节、SHA `408856505a97565531f567d25840ed4d02ec54b5d53b8b2bbb01e00dab9406a5`，唯一变化是添加完整 255 字节 `PRINTF_COND` 宏定义头部。控制器固定该块的每个字节，要求恰好出现一次且位于模块声明前，模块正文不得含 `PRINTF_COND`；只在内存中去除该块，再同时要求整体 SHA 及字节与已固定 local-03 原件相等。不存在通用去头部、去宏、空白或语法归一化。
2. **LogPerfEndpoint 的三个完整独立日志块。** 仅识别实物中精确的四行 `if`/`$fwrite` 块，每类在新旧文件中各一次：`xiangshan.backend.fu.wrapper.VFDivSqrt` 对应 `x1_bore` 和参数 `64'h0`；`xiangshan.backend.exu.ExeUnitImp` 对应 `x1_bore_2` 和 `64'h0, x2_bore`；`xiangshan.backend.fu.wrapper.VIDiv` 对应 `x1_bore_1` 和 `64'h0`。三者都必须保持原 `PRINTF_COND_`/`~reset` 条件、`32'h80000002` 文件描述符、完整原格式字符串和每个空白/换行字节。每块只允许类名后 `@` 加 1～8 个小写十六进制字符的对象标签变化；仅替换标签后，新旧同类完整块必须逐字节一致。三个块在新旧文件中必须各自形成无间隙的连续区域，该区域外的 prefix/suffix 必须逐字节相等。只允许这三个块的 3! 种排列，不接受额外块、重复/缺失块、插入语句或其他文本归一化。parent-02 实际顺序由 VFDivSqrt/ExeUnitImp/VIDiv 变为 VFDivSqrt/VIDiv/ExeUnitImp。对象标签文字及同时触发多个错误时的日志先后顺序可能不同，不声称全部可见文本或日志顺序相同。

每态保存 `generation-boundary.json`，记录 Products 实际/参考/比较 SHA、精确宏块 SHA/长度、三个对象标签的旧值/新值、逐块实际/参考/比较 SHA、LogPerfEndpoint 新旧及比较 SHA、两个区域的边界、外部 prefix/suffix SHA，以及新旧块顺序和同时报错顺序可能变化的标志。比较 SHA 仅在内存中将新块按原顺序排列并替换标签得到。该回执纳入最终产物稳定性检查。真实 SV/V 原件仍参与后续构建及前后 SHA 检查，其他原合同条件不变。

本次纯函数自测的旧 LogPerf 参考由 parent-01 实发文件的三个已记录标签逆向恢复，未写回任何 RTL；恢复后 1891 字节，SHA 精确等于原件 `6117e093dc353242609fccbde1dac8b4fd477bcb9f1416768db08ea4471dc857`。运行控制器仍直接读取已固定的原父级 RTL，不使用重构字节替换原件。纯函数自测不授予生成、父级、整核或性能资格。

原 `derive_test.py` 用固定原 C++ 和 extra fragment 重现两态已运行的 `dot16_parent_test.cpp`，与旧派生原件逐字节比较。保留原 10022 向量、14 组、完整随机/时钟/元数据/复位/DIV 切换刺激与 dot16 扩展。原 checker 不作代码或阈值变更。

快照保留 `team/optimizations/o2/parent` 与 `team/optimizations/o4/perf` 的相对目录，让未修改 `audit.py` 的 ROOT 解析加载快照内原 `check_trace.py`。共享原 `test_negative.py`、`test_trace.py` 单元门槛先运行一次。每态执行：原真实父级正例；原 `check_negative.py --positive`（内部严格 trace 和独立事务回放）；原完整 577-bit metadata audit；原 dot16 coverage；原全部 20 项观察负控及原类别判定器。它们不是 20 项 RTL 故障注入。原 DIV 的单行 WIDTHEXPAND waiver 原样沿用。

## 资源、失败与资格

CPU1、绝对 nice 5、单 worker；Java 沿已验证 recipe 的 ActiveProcessorCount1/SerialGC，Verilator 使用已核 5.052 安装的真实 bin/share，Clang 及 make/link/ar 明确绑定，构建 j1。总预算默认及上限 1200 秒，包含预检和最终审计；单次 harness 编译/父级构建最多300秒、生成180秒、lint/原 checker 测试120秒、正例90秒、回放及单项负控60秒、负控判定30秒，均受剩余总预算限制。

每个外部命令有独立进程组、argv/PID/退出码/时间/原始日志。信号只置标志，0.25秒有界等待点处理；失败和超时沿原 helper 执行 TERM/KILL/reap。新输出必须全新、绝对且与全部输入树分离，所有临时文件、编译产物、日志和快照只写新输出。所有已创建失败产物保留，不能覆盖重试。

1200 秒是工程操作截止时间；超时后的进程回收沿原 helper 的有限等待执行，外层调用另留 60 秒回收余量。

只有两个 feature 的原检查全部完成、源/快照/产物前后 SHA、完整 base classpath、完整原 overlay、Verilator 支持树、总预算与全部子进程回收审计均成功后，才写 `INLINE_SIGNED8_REAL_PARENT_PASS` 和 `parent_qualified=true`。本轮 `fullcore_qualified`、`application_performance_qualified`、`cost_qualified`、`core_cost_qualified`、`performance_measured` 始终为 false。local-03 的 FU/算术/成本结果只作为上游引用，不重授资格；生产采用仍按项目后续整核要求处理。

## 调用

```text
python3 -B inline_parent.py --repo <resident-source>
  --cost-root <dot16-production-cost-20261107-main>
  --parent-root <dot16-production-20261106-0014-pro2>
  --local-root <dot16-inline-signed8-20261107-main/local-03>
  --local-result-sha256 <已核原件的完整64位SHA256>
  --output <全新外部目录> --cpu 1 --budget-seconds 1200
```

尚未实测：父级 harness 单源外部编译与候选 overlay 的实际加载、完整父级生成物的严格字节边界、真实黑盒清单及 parser 细节、两个 feature 的父级构建/仿真/全部检查、当前四路 EMU 资源共享下的预算适用性。任何失败应保留实际原因，不能降低原 checker 判据或扩大本轮资格。
