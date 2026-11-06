# Dot16 生产 FU 接入验证

本合同只验证已审查的 `dot16-elastic-integration-v0.1` 候选在真实生产 FU 中的行为。独立算术原型、软件模型或 NEMU helper 的旧结果不能代替本合同的新运行。结果写入新的运行目录，本文件不预先宣称编译或仿真通过。

## 1. 输入、规格和边界

硬件检出基点为 `c981529dc6e493fb7deee8429b9ce05fd197497b`。候选只应用 `source-manifest.json` 所列六个生产路径；另两项未改依赖也须逐字匹配。补丁 SHA-256 为 `5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416`。更换源码后须新建运行身份；不能改写已有成功记录中的来源。

| 项目 | 本次约定 |
| --- | --- |
| 时钟与复位 | 使用原 `GenerateVDotElasticFu` 暴露的生产 FuncUnit 时钟、复位和 harness；保持原复位类型及连接，不从独立原型推断生产复位类型 |
| 数据接口 | 两个 128 位源操作数、128 位结果；保留生产输入/输出握手、ROB 身份、重定向、异常和写使能 |
| dot8 | `op=0`、`VL=8`，仅低八组有符号 8 位元素参与；高八组不得影响结果 |
| dot16 | 仅在 `VDOT_DOT16=1` 时允许 `op=1`、`VL=16`；16 对有符号 8 位数乘积求和，范围为 −260096 到 262144，先用 20 位有符号和表示，再符号扩展到结果低 32 位；结果高 96 位为零 |
| 其他合法条件 | e8、m1、vstart=0、vill=0、vm=1；保留既有 ta/ma 与 v0 处理条件 |
| 非法请求 | 不属于所启用 op/VL 组合，或违反上述向量配置时，沿用原 FU 异常、结果及写使能处理，不产生合法向量写回 |
| 延迟与吞吐率 | 无反压和取消时，沿用原测试的 E0 接收、E1 结果寄存、E2 可观察响应；每拍可接收一条，II=1。这里是 FU 握手时序，不是整核指令或应用周期 |
| 架构译码 | 候选的 dot16 编码为 MATCH `0x0e00000b`、MASK `0xfe00707f`；本 FU harness 直接驱动已译码 op，故本合同本身不证明整条指令的 decode、rename、提交或精确陷阱行为 |

开关关态和开态均使用同一套六路径候选源码。关态测试验证旧 FU 行为及新 op 拒绝；开态增加 dot8/dot16 混合数据与控制。`VDOT_O2_ELASTIC=1`、`VDOT_T14_FUSED_INPUT=1`，原互斥开关和 trace 约束继续生效。

## 2. 保留原验收，追加独立刺激

原始 `team/optimizations/o2/fu/fu_test.cpp` 固定 SHA-256 为 `d4dc81c7c206f1d395856023b01a32e76bf1dbef957b9023f8debc0a549bc01d`。`derive_fu_test.py` 在运行快照中派生新 C++；原文件及其冻结向量、scoreboard 和 observation fault 均不改。派生记录必须能将完整输出逆向恢复为原始全部字节。

关态仅插入新辅助函数和追加测试，原合法性谓词不变。开态仅额外改变 op/VL 合法谓词，再插入辅助函数和追加测试。开态不能把旧 dot8 的期望值改成 16 项；新请求才通过独立标量循环计算 16 项期望值。

| 追加测试 | 关态 `VDOT_DOT16=0` | 开态 `VDOT_DOT16=1` |
| --- | --- | --- |
| 原冻结 FU 测试 | 完整执行 | 完整执行，原 dot8 数据不变 |
| 新 op 拒绝 | ta/ma/v0 八组合 × op1/VL16，共八条 | 不适用，转为合法算术与配置拒绝测试 |
| 未知 op 拒绝 | ta/ma/v0 八组合 × op2/VL8，共八条 | 包含在 40 条非法组合中 |
| 混合连续流 | 不追加 | 10022 个冻结输入，各执行 dot8/dot16 一次；20044 个结果、20043 个连续接收间隔、首响应延迟 2 |
| 极值和上下半区 | 不追加 | 40 个定向输入，各执行两种 op，共 80 个结果；覆盖最大正和、最小负和、上半区独有贡献和逐元素正负贡献 |
| 合法算术计数 | 原测试计数 | 新增共 20124 个被比较结果；每种 op 10062 个，不把控制测试的恢复请求混入该计数 |
| 非法配置 | 原测试加上述 16 条 | 新增 40 条：VL/SEW/LMUL/vstart/vill/vm/未知 op/不匹配 op-VL |
| 混合 ROB 取消 | 原测试 | 12 组 ROB 关系 × 4 个 op 组合 × 2 个响应 ready 状态，共 96 对；比较实际取消数量和幸存队列 |
| 复位与取消同拍 | 原测试的八例 | 4 个占用状态 × 4 个 op 组合，共追加 16 例；复位清空及恢复，最终 reset_cases=24 |

四种原 observation fault 为 identity、wen、high、cancel。各负测须由原 `check_negative_fu.py` 按真实退出码和完整日志确认拒错。它们验证原 scoreboard 的敏感性；不能称为新增 dot16 RTL 变异覆盖，也不能称 DiffTest。

## 3. 运行器与可复现输入

复用的原 `team/optimizations/o2/run_rtl.py` 固定 SHA-256 为 `125cd5a308fa0253c7bd0dbc6d9ea7593afea6e7a118e3b544bfd1dab0fd7922`。`run_fu.py` 仅在新的运行快照中机械派生五处：实际 ROOT、新开关与 Mill 输出目录、环境记录、显式 Bash/Mill 无服务器启动、派生 C++ 路径。五处必须能够逆向恢复完整原运行器；原工具版本检查、全部硬件输入清单、子模块固定版本检查、lint、仿真、四项负测及源前后验证保留。

运行输出须在检出目录外，与 Mill 缓存彼此不嵌套。Mill 缓存通常置于仓外；本次允许唯一仓内例外 `out/dot16-fu-20261106-pro2`，要求实际路径及父目录均无符号链接、已被仓库现有规则忽略，并在启动前确认无其他任务占用。原因是首轮 `flag0-01` 在全部相关 Scala 编译完成后，因 Mill 0.12.3 将进程置于仓外 sandbox，现有 build.sc 和固定 VcsVersion 0.4.0 中未指定 cwd 的 Git 调用失败。仓内真实目录恢复正常 Git 父路径发现；不修改 build.sc、插件、官方源码或 Git 元数据。首轮失败输出及旧仓外缓存保持原样，新缓存不复制旧绝对路径元数据。

每个 flag 使用新的运行输出，允许复用上述独立 Mill 编译缓存；每次 `runMain` 均重新执行并以自己的开关环境 elaboration。复用 Scala 编译缓存不能代替新 RTL 和新仿真。`run_fu.py` 在运行快照中生成并记录 `mill-jvm-opts`，通过 Mill 正式 `MILL_JVM_OPTS_PATH` 机制把实际 Mill 主 JVM 限为 `-Xmx4G -Xss8m -XX:ActiveProcessorCount=1`；客户端同为 4G 上限，原 FU fork 的 4G 配置不变。堆上限不是实际常驻内存，资源协调依据进程实际用量。

运行器记录完整 HEAD、补丁后六路径/未改两依赖 SHA、运行控制源码及快照 SHA、派生关系、工具命令、实际返回码和开始结束时间。源副本须在复制后立即匹配此前记录，执行后再次一致。底层生成的 RTL、测试向量、编译后二进制及依赖清单仍按原运行器留存。

以下为调用形式；路径须换为本次已核实的绝对路径，不能把已有失败或成功输出覆盖重跑：

```bash
python3 -B team/optimizations/o2/dot16/rtl-integration/run_fu.py \
  --repo /absolute/current/source \
  --expected-head c981529dc6e493fb7deee8429b9ce05fd197497b \
  --output /absolute/new/flag0-run \
  --mill-output /absolute/current/source/out/dot16-fu-20261106-pro2 \
  --feature 0 --cpu 1 --budget-seconds 900
```

关态完成后，以新的 `flag1-run` 输出和 `--feature 1` 运行开态。预算先限制为 15 分钟，CPU1 单核，Mill/Verilator jobs=1；启动前仍应核对团队总体四核资源分配。编译超过预算属于有界尝试未完成，须检查进展与原回执后决定下一次执行，不能据此判定硬件功能错误。超时只停止本次创建的进程组；发现其他运行或未知来源进程时不结束它们。

## 4. 验收与报告

一个 flag 的 FU 资格需要同时满足：

1. 实际底层运行器退出码为 0，`runner.status.json` 的 stage=fu 且 passed=true。
2. 正测日志恰有一个对应 flag 的追加覆盖标记，字段及数量与本合同完全一致；随后恰有一个最终 `O2_FU_PASS`。日志不能含 FAIL、INJECT 或 FAULT_ESCAPED 标记。
3. 原 10022 输入、最终复位计数、四项原负测、所有底层生成与身份验证完整通过；不存在只打印追加 PASS 后失败的接受路径。
4. 输入与快照前后不变，HEAD 和候选源码仍匹配，底层 `SOURCE_AND_DEPENDENCIES_UNCHANGED` 存在；本次进程已退出且无遗留进程组。

两种 flag 分别报告，不以一个 flag 推断另一个。验证失败或未完成时保留实际日志、退出原因和输入身份；只能在新的输出身份下继续。整个结果不授予父执行单元、译码、架构别名、整核 DiffTest、软件 ABI、应用性能或 ASIC PPA 资格；这些结论须由各自真实验证取得。
