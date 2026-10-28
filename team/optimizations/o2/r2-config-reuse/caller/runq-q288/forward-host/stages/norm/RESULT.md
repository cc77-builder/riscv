# RMSNorm 输出 RVV 与 W2 组合：实际结果

日期：2026-10-27（UTC+08:00）。源码基点 `431938271dd3b9eda8595a45d2bcf4e429d25797`，本结果随新增叶级源码与证据提交；实际载体提交由 Git 历史定位。

**独立 norm 的固定域正确性、目标重放、完整归档恢复及冻结校验器复算通过。性能按原门槛 HOLD：四个 scalar 样本的跨度为 3.2205087%，超过 1%。** 新组合消费者已完成八例全状态参考与同对象双状态 API 验证，可作为有明确资格边界的可选工程对象；没有据此切换稳定默认或宣布应用加速。

## 1. 验证层级与采用决定

| 对象 | 实际结论 | 适用范围 |
| --- | --- | --- |
| 原 norm build-04 / reference-01 | PASS | 39 次真实输入＋9 个固定合成输入、384 组功能检查，真实末字节负控、正常、独立重放 |
| 原 norm target-01 | FAILED，保留 | 原 4M guest-cycle / 3600 秒合同未完成；两个正例进程因超时被终止，已有功能或计时前缀不算整批 PASS |
| 新 target-budget2 | 正确性、原 DiffTest、计数器及独立重放 PASS；性能 HOLD | 同原 ELF、同原输入及判据，仅采用事前独立的 6M guest-cycle / 7200 秒资源补充 |
| W2＋norm consumer-build-02 / reference-01 | PASS | 八个独立案例：七个正常／恢复／重放案例覆盖 p0..2，真实负控在 p0 的 byte152476 拒绝；完整状态和五模型检查 |
| api-build-01 / api-reference-01 | PASS | 同一完整 consumer 对象，双状态、初始化／失败调用原子性、guards、TLS、errno、flags 与模型只读 |
| 原字节恢复与离线复算 | PASS | 1,826 个普通文件、2,884,708,772 字节；五类 campaign 各在独立进程中导入自己的历史源码 |
| 同对象首 token 包装 | 四例完整目标、实际恢复及冻结raw复算PASS | [目标结果](target/RESULT.md)；资格限固定p0/token1，不把它补写到原300k probe、旧W2或公平性能实验 |

主审计入口为 [完整复算结果](evidence/norm/audit/result.json)，所有发布文件的摘要见 [证据索引](evidence/index.json)。原先失败的 build-01/02/03、原 target 超时、初始工具参数拒绝及对应原始记录均保留在归档；“失败证据复核通过”表示保存及判定一致，不表示原失败实验通过。

原 norm 合同提出在局部收益合格后再考虑消费者接入。本轮局部筛选的性能门槛未过，故没有授予采用资格；新 [消费者合同](consumer/CONTRACT.md)另行建立同对象完整正确性入口，目的是检验实际接入和支持后续完整目标验证。它保持可选身份，不把局部 HOLD 改成收益结论。

## 2. 数值与接口到底保持了什么

候选只将 RMSNorm 输出的两次独立乘法向量化。逐项平方、标量左折叠、除以 size、epsilon、sqrtf 和倒数保持原源码顺序；无 FMA、重关联或 fast-math。固定调用域为 size=288、有限 binary32 输入／权重、VLEN128、RNE、FS/VS enabled、vstart=0，输出与输入相同或完全不相交，权重与两者均分离。

384 组检查覆盖两种实现、独立／原地输出、清零／预置 sticky flags；读取完整输出、输入、权重、guards、fcsr、errno 和向量配置。实际负控翻转 case38 的最后一个输出字节，精确拒绝位置为 byte1151，代码92。该域没有扩展到任意 size、非有限输入、其他舍入模式或部分重叠。

组合消费者仅在四条优化 forward 路径中替换共12处静态 norm 调用，scalar 方法继续使用原上游路径。完整对象中的四个 K288/K768 FR/TA GEMV 函数字节不变；64字节 RVV norm 叶完整字节不变，192字节 norm C 函数只接受规定的四组链接重定位，并核对常量、两个调用目的地及全部其余指令位。

八例消费者参考比较每个位置全部 3,691,424 字节状态、五个完整模型和 flags，负控在最后 logit 的 byte152476 实际翻位。TA-cache、恢复、重放的完整验证结构一致。API 资格包括13次拒绝 forward、5次失败初始化、6次成功初始化、5次有效 forward 和6组双状态比较；两侧 guards 与 TLS errno=12345 均保持。旧 W2 对象的 S256 资格不迁移到本对象。

## 3. 原始计时与 HOLD

计时边界是 p2 的13次完整 norm C 调用，包含归约、sqrtf、倒数、向量配置保存／恢复和实际输出计算。每个样本先同方法预热13次，恢复输入和状态，再计时13次；检查、恢复和 UART 在窗口外。顺序固定为 `S,V,V,S,V,S,S,V`，每方法四个正式样本；重放不增加样本数。

| 方法 | 按该方法出现顺序的四个目标 cycle 差值 | 每窗 instret |
| --- | --- | --- |
| Scalar | 51,538 / 50,008 / 49,930 / 49,937 | 53,188 |
| RVV 输出 | 23,774 / 23,662 / 23,607 / 23,619 | 20,989 |

所有窗口的 flags 为1、FNV 为 `e8d94ebe570b175c`；32次 CSR 读完成实际 ELF、入队、采样和退休链核对，八组 cycle/instret 差值与 UART 一致。该镜像没有 vdot，实际 custom COMMIT 为0，不能借用其他实验的事务计数。

原取舍需同时满足 scalar `max/min−1 ≤ 1%`、最慢 RVV 比最快 scalar 至少少0.5%，并且两个顺序组均有利 RVV。实际 scalar 跨度 `51538/49930−1 = 0.03220508712197079`，首项失败，因此 `comparison_qualified=false`、`candidate_performance_qualified=false`、`selected=HOLD`。虽然其他原始条件有利 RVV，仍保留全部样本，不删首样本、不追加成功样本、不更换分母或调整预热。

这组数据只说明该固定局部调用计划的观测值。它不提供合格的应用加速倍数，也不改变原 W2 的性能 HOLD、较强 FR 对照或 R5 默认。

## 4. 消费者参考指令数观察

归档 `analysis/reference-instruction-comparison.json` 对原 W2 与本组合的原始完整参考结果作逐项核对；九份 report/state/flags/model 原始结果相等后，得到以下整段三位置验证程序的 NEMU 退休数。

| 方法 | 原 W2 对象 | 本组合对象 | 差值 |
| --- | ---: | ---: | ---: |
| Scalar | 364,544,120 | 364,544,120 | 0 |
| FR | 26,932,097 | 26,835,494 | −96,603 |
| TA | 34,789,781 | 34,693,178 | −96,603 |
| FR-cache | 26,503,298 | 26,406,695 | −96,603 |
| TA-cache | 34,360,982 | 34,264,379 | −96,603 |

这些值包含验证程序开销，不是纯 forward 计时窗口或香山周期。四个优化方法均少96,603条，FR-cache 与 TA-cache 的差仍为7,857,684条；它只能作为选择后续诊断问题的工程观察，不能据此推导 token/s 或模型质量。

## 5. 身份、恢复与回退

| 实物 | SHA256 |
| --- | --- |
| 原 norm ELF | `10b54abbc074b99bcc66c90fada9678447bf80f341790dbda3086797153ef5fe` |
| 原 norm BIN | `7e89b12cd1f2c07a8b3ec5d35e8c8ae8d5cb398b210dd62530911b6513582cfc` |
| 组合 consumer 完整对象 | `68ece1e0b8d7fbce6e3ea7167818058b2c74b19691f8e06ef15e917be396e037` |
| 组合验证 ELF | `93296b046b4cd8b814c65297dab74351389226a5cb004aa0fec700ba0d856198` |
| API ELF | `69e4689d6492ad4362d0d377fcf47c9839e906626b649e2ad3709d98a8f34499` |
| norm 归档 ZIP | `c10b8332590abeb7c2597e6cd051b81ba86b1de5b9b3070bbebeec3ca0b588c2` |
| norm 归档 manifest | `a72b1088cd52787fcba5cae1295fff2bace87c0f3a0f68fe897a60f08a7a9641` |

ZIP 为320,342,190字节，以16个至多20MiB的原字节分片发布。已用仓库既有 `restore.py` 从这些实际分片重组，并验证整体 SHA、所有对象与清单；原包已实际还原全部普通文件并由冻结验证器重新读取完整 raw。重组收据见 [transport-receipt.json](evidence/norm/transport-receipt.json)。

恢复命令和调用方式见 [README](README.md)。恢复后 `consumer-build/consumer-w2-norm.o` 是可链接对象，原 `consumer-w2.o` 是完整回退，两者二选一；公共 API、模型布局、ABI、旧实现和稳定 firstdot 入口均保留。这里没有通过全局宏或 linker wrap 偷换同编译单元内的调用。

原构建与运行根为 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/norm-resume-20261027-2000`；前序 norm 的构建／参考／原失败目标位于相邻 `forward-norm-20261027-1536`。这些是本批历史来源定位，不是换机器后可直接继承的环境资格。离线复算不启动 NEMU/EMU，不重新认证物理 RTL 或外部工具；新运行仍需实际匹配依赖。

## 6. 路线影响

独立norm已完成这次有界筛选，保留HOLD。2026-10-28已收束同对象首token的四例完整目标、全状态比较、原DiffTest、custom协议、四CSR链、独立重放及实际恢复后的原文复算，详见[首token结果](target/RESULT.md)。该固定p0/token1正确性资格不等于公平性能；旧失败保留。后续优先评估实际矩阵尾部填充计算，不自动重复已闭合长跑。

进一步性能比较需要独立、事前明确且包含强 FR 的公平计划。新的 norm、量化或非线性优化应由实际消费者成本证据驱动，不因本批局部 RVV 原始值较低而继续枚举。连续 token、真实 checkpoint/tokenizer 与模型质量、完整应用公平性能、ASIC 面积／功耗／时序仍分别缺少本候选的新资格。
