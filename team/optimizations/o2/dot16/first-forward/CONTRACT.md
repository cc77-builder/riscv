# dot16 四臂首个完整 forward 合同 v1

合同：`r3-dot16-first-forward-v1`。创建时状态为 **SOURCE_PREPARED / UNBUILT / UNVERIFIED**；原暂停阶段的源码准备记录保留在冻结快照中。当前实际运行与证据见[RESULT.md](RESULT.md)，不能用本合同的计划描述代替运行回执。

## 2026-11-07：N候选登记的有限扩展

已有whole2四臂使用外部冻结副本及profile运行，其输入、预算和结果归属保持独立。公共入口新增显式候选`narrow`，绑定已经通过[固定Q288](../whole2/NARROW_Q288_RESULT.md)的N=whole8+narrow完整函数。本次只更新候选表、符号白名单和说明，并在独立新输出进行一次source-only控制器准备；不执行GNU构建、参考或目标EMU，不修改原在途作业。

准备成功仅表示`FIRST_FORWARD_DOT16_CONTROLLER_BOUND_NOT_RUNTIME`：输入身份、派生控制器文本、逆向证明及Python语法检查通过；`reference_runs=0`、`target_emu_runs=0`、`target_cases=[]`、`performance_qualified=false`。prepare没有执行derive.core/main、构建阶段函数提取、GNU函数字节相等检查或新的完整forward，因此不能据此声称N完整forward已静态验收或运行通过。

现有准备模板仍列四个正常参考臂及一个DQ反例，并让D/DQ共用一个显式内核；该清单只是生成配置。此次登记既未选择新的目标清单，也不自动提供W与N同ELF双内核比较。下一轮先依据原四臂真实结果决定最小公平比较及独立预算；旧ELF的周期不能成为新ELF的分母。PARENT_PINS、硬件身份、方法字、MAGIC及既有plain/whole2表项保持原样，新输出如实记录更新后公共文件SHA。

## 目标与范围

在同一新 ELF、同一已冻结 dot16 EMU 和 reference 上比较 P、PQ、D、DQ，选择正确且较快的完整应用路径。P/PQ 是当前候选集合中的 RVV 对照，D/DQ 使用同一个最终选定的完整 dot16 函数。所有臂共用模型、准备过程、输入、独立 golden、状态布局、浮点计算次序和计时入口。

[范围登记6689984031](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6689984031)接续同账号 WORK6670578319/UPDATE6670959414 与既有 consumer 范围。新增写入仅本叶；原 P/PQ、plain D Q288、whole2、官方程序和所有冻结运行输入只读。不修改公共 API 的既有枚举，不改变默认运行入口，不改 RTL、官方验证器或赛事提交物。

## 规格与四臂关系

沿用固定 synthetic 模型 D288/H768/L6/HQ6/HKV6/V32000/S256、GS32、VLEN128、RV64/lp64d。按原规定准备后测首个 position0/token1 完整 forward；模型加载、生成、packing、初始化及验证打印仍在窗口外。这不是含准备开销的端到端生产应用测量。

| 臂 | 私有方法字 | 7处静态 K288 路由 | W2 矩阵乘 | 5处静态量化调用 |
| --- | --- | --- | --- | --- |
| P | 0x50313631 | 原完整 P | FR | 原 quantize |
| PQ | 0x50535131 | 与 P 同一函数 | FR | 原完整 Q helper |
| D | 0x44313631 | 显式选定 dot16 函数 | FR | 原 quantize |
| DQ | 0x44313651 | 与 D 同一函数 | FR | 与 PQ 同一 Q helper |

表中位点数是源码与最终 ELF 的静态范围，不声明动态调用或自定义指令退休次数。W2 的量化在 PQ/DQ 中使用 Q helper，但其矩阵乘仍明确走 FR。

选择参数不得默认：`prepare.py --kernel plain|whole2|narrow` 必填。原四臂已根据独立[whole2 Q288筛选](../whole2/q288-consumer/RESULT.md)选用whole2；新增narrow只登记N的冻结函数身份，不更改原选择。每个新实验另行固定候选、共同镜像与实际运行清单。三种候选的源码和函数身份分别保留，不能互相替代：

| 候选 | 完整函数 | 长度 | 函数 SHA-256 |
| --- | --- | ---: | --- |
| plain | q288_dot16_vdot | 484B | ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb |
| whole2 | q288_dot16_whole2 | 412B | b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6 |
| narrow | q288_dot16_whole8_narrow | 312B | 050bc3db3e2a70bd6e5409cbf9c139868008e8ccb18776b7e0e7104e6a554b75 |

plain 输入沿用已闭合 Q 镜像及其原 dot16.S；whole2 输入沿用已有 host ELF 和完整 whole2.S，包含 X+=32 后缀。它们仅提供候选函数身份；选择依据仍须来自适用的真实 Q 结果，旧 host 或 Q PASS 不授予新完整 forward 资格。

narrow输入为固定Q288实际GNU构建的完整`fused.S`（SHA `4df1d70ddc5efadc202f20817d43cbc70c1601a2261549820308ed3fe02a315e`）和ELF（SHA `82281d6fab843190321cdb21189f2feae848e2c1220e6a1ad0ec8bd883011b91`）。函数仍须满足唯一`.global`—`.size`完整段且位于来源文件末尾的既有提取条件；不放松提取器或构建时整段机器码相等检查。N的固定Q资格不继承为新的forward资格。

## 最小实现

复用固定 [P/PQ preparer](../../r2-config-reuse/caller/runq-q288/fused/gs32-rvv/quantize/paired-consumer/prepare.py)及其原基座，不修改冻结文件。新 `prepare.py` 在新输出中保留完整父控制器快照、派生记录和正反向字节证明：

1. 先得到原 P/PQ 源码，再从最后的 PQ clone 逆向恢复已存在的完整 P 模板；追加 D/DQ 与各自薄入口，不改变原 clone 顺序。使用独立的函数别名，避免覆盖父扩展的 BASE_CORE/BASE_MAIN。
2. D/DQ 的七处 K288 调用共用一个 route_dot16；保留原 W2 行。仅 DQ 的五处 STAGE_QUANTIZE 换成既有 Q helper。原 C、include、初始化与模型全局保持可逆。
3. 新选择器的读取、合法性判断和分派全部位于同一个原计时调用内；四个 CSR 读取及 fence、完整比较器、guard 和 FCSR==1 检查保持。
4. 在最终 ELF 中检查各 clone 的八处矩阵路由、七处指定 K288/一处 FR W2、公开入口到自身 clone、一次共同 measured dispatch、四臂各五处正确量化调用。新增选择器到入口的实际分支关系须结合最终反汇编核对；只检查目标集合不能证明这层映射。
5. 原7个 consumer 加 D/DQ 后应有9个 consumer、27处原 norm 调用。保留兼容方法表中的 FR/G，但实际正常参考和目标清单仅 P/PQ/D/DQ，不因遍历兼容表额外启动 FR/G。
6. 仅编译新增一个选定 dot16 对象，与原 P、Q、norm 等对象组合；最终函数整段 SHA、与固定来源 ELF 的逐字节比较、原 P 的完整 guard/fallback 身份都须通过。

新构建继续使用原 GNU/AM 命令和原静态库，串行、一个协调 CPU；不构建官方依赖。输出必须在常驻开发区 runs 的新独立目录，不能位于任何源码、模型、候选、硬件记录或冻结输出内部。每个新源、派生控制器、GNU 工具、链接输入、ELF/BIN 和输出清单均冻结身份，原始与失败证据保留。

## 新硬件身份

复用已真实完成六个合法用例 DiffTest 的 dot16 硬件，不重建 EMU 或增加 ABI 探针：

- 硬件结果 SHA：`e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f`。
- EMU：`f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d`。
- feature1 reference：`cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae`。
- Flash：`a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994`。

保持 D16/O2/T14=1，O1 handoff、O1/O2/T12/T13 trace=0；既有 ABI 1400B，int0/fp256/csr512/pc656/hcsr664/vec800/vcsr1312/fcsr1368/trigger1376。新身份入口逐项复核同一硬件结果的 runtime_inputs、flags、ABI、EMU/reference/flash。旧 T17 支持快照只承担原软件、fixture 与历史证据来源；不得冒充新实际执行硬件或关闭原校验后替换路径。

## 参考模型与真实验收

新参考队列明确为四个正常臂，加一个 DQ 的既有末 logit byte152476 单比特破坏负例。沿用原 runner 和原完整比较器，保留每个实际子进程的正常退出、回收、进程组消失、输入身份前后相等及原始 dump。

每个正常臂须独立验证全部 **3,691,424B** state、模型与独立 golden 未变、前后 guards、完整 dump inventory、TLS/errno12345、原控制字段、RNE 和精确 FCSR==1、实际 GOOD trap 与 PC。负例须由相同完整比较器在精确字节处拒绝，并保留真实 BAD trap；不以构造日志代替执行。既有每例100M API calls、600s内部/630s外部参考预算不自动扩大，整段构建与参考任务预算在恢复后另行冻结。

最终 ELF/BIN 一致性、入口/RAM/TLS/链接范围、四次 CSR 0xc00/0xc02/0xc02/0xc00 与前后 IORW fence、成功/拒绝 trap 的0x0005006b机器字继续采用原检查。四个目标 image 除同一4B方法字外必须逐字相同，UART=1且negative=0。

## 目标运行与证据边界

参考端 `prepare.py` 仍只生成参考控制器。新增 `prepare_target.py` 准备独立目标控制器：逐字保留新参考端的构建、派生、镜像检查和比较器，复用原 P/PQ 目标运行器的进程 owner、调度和清理流程，并将案例清单、新硬件身份与 TRACE0 审计做有限可逆派生。合同创建时尚无生成的run.py/audit.py或目标profile；后续whole2实际生成、参考与在途目标记录见RESULT.md。新增narrow的source-only准备不生成目标控制器或profile。

原 P/PQ 目标源以实际运行 profile 中的 binding `abab046e22508c6287b1ea9a9e91ece6d994ca6dd3c5d596d8d99e6ae3032972`、run `b8ab0c2bafaa7f329fec72537541fa621e1b428436ce587eb893e57d636e69a8` 和 audit `ffc32d13a5fc1d8483f3050d286fc80c26e970e585ec33255fd590a67a63694f` 固定。复用其93件 target-support 源闭包，保留新参考端56件来源及其输入 pin；沿用原7件替换、3件排除、40件添加的明确来源关系。此关系仅用于选择既有团队 helper，不授予新工作负载运行资格。

新目标源移除旧 T17 的 ExeUnit_17/trace 辅助文件假设，由已冻结 dot16 硬件记录及全部 runtime_inputs 验证实际 EMU/reference/flash。原 Q288 的实际 TRACE0 运行已使用空 cwd 和显式 flash/reference；新完整 forward 仍须独立验收。`prepare_target.py --max-cycles --timeout --raw-limit` 三项必填，不能默用原 P/PQ 的8小时合同。生成过程不启动任何进程，不生成外层任务 owner，不冻结CPU或运行profile。实际启动前仍须核准新镜像、五个闭合参考用例、实际CPU与内存、外层任务时限及清理余量；人工暂停未解除时不能执行。

外层入口 `launch_target.py` 直接导入固定原 owner（完整源码 SHA `25758520f36b83d3ca5feb25ece444b963d1e673f7a375096ffe3f60a5f3eafd`）的 `owned_campaign()` 与 `case_closure()`，不调用其带旧路径和两案例配置的 main。启动前显式提供入口源码SHA、已审核profile的SHA、原owner源路径以及work/TERM/hard/external四层预算；先认证完整冻结输入，再导入运行器。从profile读取实际新identity及全部运行根目录，不沿用旧CFG identity。原有目录级隔离检查保护仓库、build/reference/adapter、硬件、AM、owner和入口所在目录；phase/export/campaign三者也不能重叠。

外层入口要求实际CPU集合恰等于profile声明的1至4槽，不隐式改槽；工作预算须覆盖按案例数与槽数计算的完整波次数和清理余量。外层工具的超时必须与external声明一致，脚本不能代替工具施加此上限。最终资源释放仍依赖原真实Popen/launcher/EMU回执、实际回收与进程组消失，缺失或未知记录不自动释放。whole2原作业已按RESULT.md绑定独立profile并启动；narrow候选登记不绑定新的目标profile、资源值或运行。

TRACE0 审计覆盖完整原 stdout/stderr 的故障标记、实际 DiffTest banner/reference、唯一且正确的 GOOD trap PC/word、正常 exit、无超时、输入未漂移和真实进程清理。 完整文本复用原 stream.Reader.lines() 的跨流顺序与读取语义，保留原64 KiB单行和16 MiB文本边界；完整读到EOF，超限或解码失败拒绝，不截断、不按白名单丢行。不调用要求SCHEMA的 events()/analyze_reader()。应用协议仅匹配行首 CONSUMER_ 并核对完整三行，四个16位十六进制 CSR 原值须完整保存，周期取c1−c0，指令取i1−i0，不能用整 guest 或参考模型计数替代窗口。

旧 trace 的 ENQUEUE/COMMIT、PC-word动态计数、CSR sample/retire 链及 ordered-PC digest 不采集。静态函数身份不等于动态退休证明，未采集字段不得输出伪造 PASS 或“零 custom 已证实”。新目标成功最多支持固定首个完整 forward 的全状态/DiffTest正确性及静态 ELF、UART CSR 窗口观察；正式 performance、完整退休窗口和 ASIC PPA 资格保持未授予。

目标正常臂计划各一次、独立输出和单核实例，最多四核总预算。启动前按实际空闲 CPU、内存、I/O、剩余工作窗口冻结 max_cycles、主机预算、日志边界和清理余量；不自动延长，不额外启动校准 guest。只比较模拟的架构周期，主机耗时用于成本和资源记录。

## 比较、取舍与回退

只在通过本次完整正确性与目标检查的臂间比较。RVV 基线取 P/PQ 中较快者，dot16 候选取 D/DQ 中较快者；不把旧硬件或旧 ELF 的样本当作新分母。保留全部原始观察，不删除不利样本。

同实验可分别报告 P→PQ、D→DQ 的量化作用，以及 P→D、PQ→DQ 的条件路径差值。组合 P→DQ 的周期差可分解为 P−PQ 加 PQ−DQ，或 P−D 加 D−DQ；不同分母的百分比不得相加。dot16 路径差值包含软件与执行路径改变，不能称为纯硬件收益。此候选集合不代表穷尽所有 RVV 实现。

若 Q 路径不满足新的完整正确性合同，应按真实结果缩减到 P/D；若 dot16 完整应用无优势，保留较快合格 RVV，并报告局部 Q 与完整应用差异。回退是保留原完整工程、冻结证据和默认入口，放弃采用新候选；无部署。
