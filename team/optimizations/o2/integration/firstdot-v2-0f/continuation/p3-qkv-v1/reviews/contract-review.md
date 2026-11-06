评审时间：2026-10-30T21:40:35+08:00

# P3 FP32→QKV 数值、ABI 与目标探针独立合同评审

状态：**GO_HOST_MIGRATION_WITH_GATES**。这是固定来源的只读合同审查；不是新迁入实现通过证明，不授予 EMU/NEMU、周期、面积或时序资格。供体固定为 `ffd668bf1bc80850d382f514d13bb00316c85582`；不得跟随活动分支漂移。

本评审只新增本文件。未运行 EMU/NEMU，未改 RTL，未构建全核，未操作 GitHub。当前迁入、构建、模型和负控的实际状态由本包最终结果与逐项证据决定。

## 1. 已经独立核对的源码事实

来源为 `../../deferred-reduction-c8-r1-review/p3-reference/`。7 个参考文件的字节数、SHA256 和 Git blob 均重新计算，与该目录 `manifest.json` 全部相符；这只证明这 7 个本地文件的身份，不能替代全部传递源闭包、fixture 或旧目标归档核验。

| 事实 | 直接依据 |
| --- | --- |
| 量化为 9 组 × 32 个 FP32，一组扫描 max(abs)，使用静态 RNE 的 FP32 除法及静态 RMM 的转换 | `boundary.S.txt:10-37`，`donor-qkv-contract.md:15-19` |
| boundary 只量化一次，然后依次调用三个 projection，三次加载同一个 kernel 表项 | `boundary.S.txt:45-66` |
| boundary 保存 ra/s0，分配并恢复 16 B 栈；量化器使用 ft0-ft3 等 caller-saved 状态 | `boundary.S.txt:10-37,45-66` |
| qkv_context 为 fp、x、xs、3 个 projection、kernel，共 7 个指针；原头文件只断言总大小 56 B | `boundary.h.txt:5-12` |
| TA 为 q288_tail_vdot，FR 为 q288_fused_rvv4；同量化器、数据地址和 Q/K/V 边界 | `donor-qkv-contract.md:7-11` |
| 供体选用 0.5% 收益门槛，不能作为本项目 3% 门槛的替代 | `donor-qkv-contract.md:27`；本地 `P3_REVIEW.md:51-54` |

固定供体的完整树在本次子审查的本地 Git 对象库中不可直接解析（`git ls-tree` 返回 `fatal: not a tree object`）；完整传递闭包的取得与核验由主工作单元负责。本评审不假设尚未取得的源已经通过。

## 2. 必须冻结的最小合同

- D=288、GS=32、VLEN=128、RV64/lp64d；FP32 输入 1152 B，一次量化产生 288 B q 和 36 B scale。每次 boundary 的全部 864 个 Q/K/V 输出都属于正确性范围。
- 权重、权重 scale、投影计算次序和每步 binary32 舍入沿用固定来源；量化等价不自动证明投影等价，禁止改用倒数乘法、FP 重关联或合并乘加后仍声称原合同。
- 必须在转换之前检查有限、非零 group max、有限正 scale、有限商以及 `-128.5 < z < 127.5`。避免先执行域外浮点到整数转换，再检查错误。
- 域外至少包括全零组、NaN、Inf、scale 舍入为零、正 scale 但商越界。特别保留 `max=128*2^-149`、scale=`2^-149`、商=128 的反例；正 scale 并不足以判为合法。
- 明确输入到返回的生命周期：fp/packed/weight scales 只读；三个 projection 共享同一 x/xs，量化完后按只读使用；x/xs、三个 y/slots、所有 context、只读输入彼此按原约束分离；并发调用必须有独立可写区。
- FRM 前置为 RNE 且返回保持；FS/VS 已启用；量化器本身不承诺投影返回向量状态。完整 boundary 返回 vl=8、vtype=0、vstart=0、vcsr=7。向量寄存器允许破坏。
- fflags 为 sticky 累积；允许正常 NX/UF，拒绝新产生的 NV/DZ/OF。若检查最终 NV/DZ/OF 必为零，应明写入口先清零或入口此三位为零；不能把入口已有 sticky 标志误判为算法新异常，也不能一概要求 fflags=0。

## 3. 宿主门禁的重点与易漏项

| 门禁 | 可接受证明 | 常见漏项/拒绝条件 |
| --- | --- | --- |
| 来源闭包 | 运行源、生成器、fixture、独立参考和审计器分层清单；固定 Git blob/SHA；所有传递 import/读取的文件可解析 | 只核验顶层 export.py，运行时又读取活动树或另一个生成器 |
| 数值 oracle 独立 | 原样上游量化参考与实际活动 q/scale 相互验证；投影独立 golden；目标机器码模型与这些 oracle 对照 | 两边调用同一新实现后把相等当成独立证明 |
| binary32 精确性 | 核对全部 q 字节和 scale 位型；保留半整数两侧、±0、subnormal、商下溢和大有限边界 | 仅比较容差、只验证 checksum、宿主 double/fast-math 掩盖单精度舍入 |
| 完整投影 | 两位置 × 两方法全部 864 输出、完整路径读写范围/顺序、每组 dot 累加及浮点尺度次序 | 只验位置 0、只验 Q、只验最终摘要或混用旧 ELF 的 golden |
| 完整 128 位 | 每个 slot 下 32 位有符号 dot 和上 96 位全零，覆盖负数与边界，保留高位故障检测负控 | 只比较 int32 低位或者最后输出正确就忽略 slot |
| ABI 布局 | 实际 RV64 编译产物，qkv/q288 context 的 sizeof、offsetof、对齐与实际加载偏移一致 | 只有 qkv_context sizeof=56，无字段偏移或 q288 结构证明 |
| ABI 状态 | sp 16 B 对齐并恢复，整数 callee-saved 及 lp64d FP callee-saved 保持；实际函数叶与调用链审计 | 只验 s0 或只审 boundary 而未检查投影叶及测量 wrapper；将单精度 NaN-boxing 默认为模型已支持 |
| CSR | 指令解码/执行模型验证静态 rm、FRM 不写、fflags 与 vl/vtype/vstart/vcsr；污染反例能拒绝 | 只比最终 C 输出、模型忽略 CSR 指令却标记 CSR PASS |
| GNU/链接 | 指令编码、无未解符号/重复导出、最终函数指针、路径目标及重定位、RO 数据和数组大小逐项核对 | 同时链接去重 kernels 与旧 fused.o；源文本正确但最终 route 指向旧函数 |
| 负控 | 对 q、scale、K 输出、slot 高位、边界/guard、context、route、FP 输入、rm/CSR/ABI 分别注入实际变异并被对应 gate 拒绝 | 仅手工设置 status=FAIL，或检测失败来自无关编译错误；负控从未经过真实检测器 |
| 失败保存 | 每个变异的变更、退出码、检测原因、源/对象身份保存 | 删除失败日志，或校验器异常退出被当成成功拒错 |

若源码/对象模型暂不支持某一 CSR、FP 或 ABI 行为，应明确 NOT_TESTED/BLOCKED 并阻止目标准入，不能凭参考文档升级为 PASS。参数/链接合同的独立静态证明可与数值模型组合，但须写清各自范围。

## 4. 0f 有界目标探针应如何冻结

只有本包实际宿主门禁全部通过，才可交付下一轮目标合同；本轮不执行。建议保留固定来源的两块顺序 `FR,TA,FR | FR,TA,FR`，每窗一次 same-method selfwarm、对称 prepare；位置 1 仅功能，不根据结果临时增加窗口或选择有利数据。

1. 固定本地 0f EMU、normal NEMU、真正高位故障 NEMU、AM/flash/toolchain、生成源与最终 ELF/BIN 的完整 SHA。现有二进制身份须实际重新读取得到，不能从供体标记继承。需要的 dot 编码/CSR 先静态核对。
2. 计时窗包含普通 C 边界调用、一次量化、Q/K/V、返回；pack、RMSNorm/attention/FFN 等不计入。只比较同一输入与同一窗口的 FR/TA，不能与 C8 的 273 周期或供体旧 ELF 横向拼接。
3. 锚点保持 `100*max(FR) <= 101*min(FR)`；保守减少率 `1-max(TA)/min(FR)` 至少 3%，即 `100*max(TA) <= 97*min(FR)`。若采用 speedup 表示，则为 `min(FR)/max(TA)`；不要将 3% 减少率误写为同值 speedup。
4. 完整 correctness、DiffTest、每窗控制/计数、锚点全部先通过，才判断收益。所有窗口都保留；replay 只检复现，不作为新增统计样本。不同方法的实际 instret/VDOT 数不应被错误要求相同，固定控制窗口的相等与方法自己的预期值必须区分。
5. 目标保留必要功能/完整结果与真正第一条 custom 高位拒错→normal recovery→same BIN replay。大量检测器变异留在宿主，避免目标重复自检吞掉周期与墙钟预算。
6. 从新 ELF 的实际循环/调用/机器码导出所有预期计数。若完全保留供体计划，应交叉得到 14 boundary、42 projection、12096 输出、17 次量化、153 group、4896 element；若新方案有变化，先另列新合同与派生过程，不能硬拷旧常数。
7. 冻结最多进程数、串行执行、每进程 guest cycle/墙钟/CPU/内存/日志上限及总预算。供体 18M guest cycles、7200 秒与约 53 分钟历史运行不代表本机预算或 ETA；先计算运行开销再定数值。
8. 任一拒错未命中预期、恢复失败、DiffTest/功能/计数/锚点失败、超预算或收益不足立即停止，保留状态；不得自动扩围或新增样本寻求通过。没有合格性能收益仍可保留 FR 回退与软件功能成果，不替换当前 0f+firstdot V2+C8 默认。

## 5. 结论与未核验边界

**合同方向 GO；目标运行仍 NOT_READY，直到本包真实宿主结果和新预算合同完成。** 本次直接核验范围只有 7 个固定参考的身份、边界汇编/头文件和供体声明之间的一致性；完整生成器、q288 叶实际机器码、fixture、独立 numerical 模型、迁入后的 GNU/链接/负控及 0f 执行均未由本子审查独立运行。主工作单元不能把本评审文件本身当成上述项目的 PASS。
