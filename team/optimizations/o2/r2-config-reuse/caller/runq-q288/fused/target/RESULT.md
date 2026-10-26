# 完整 Q 融合：目标运行、公平比较与原文闭合

结果：**`FUSED_TARGET_DIFFTEST_AND_PLAN_PASS` / `VDOT_PREFERRED_IN_FIXED_PLAN`**。合同 [`r2-s3-runq-q288-fused-target-v1`](CONTRACT.md) 的真实负控、正常恢复、独立进程重放与隔离新源原文复算均已完成。

本固定计划中，建议显式使用 **`q288_fused_vdot`**；保留相同融合消费的 `q288_fused_rvv4` 作为强 RVV 对照和回退。fused-vdot 相对 acc8-vdot 保守减少 **23.797253%** 周期；fused-RVV4 相对 acc8-RVV4 保守减少 **23.852889%**；融合 vdot 对本次纳入的全部 RVV 最快观察仍少 **6.844186%** 周期。它们分别是共同软件融合的收益和同样融合消费下的整数实现差异，分母不同，不相加，不称为新的 RTL 收益。

范围仅为**固定 T17、同一 ELF、预量化且预打包的 288×288/GS32 Q、一次同方法完整 selfwarm 后、两个反序块**。不包括 pack、激活量化、冷启动、完整 forward/token、训练质量或 ASIC PPA；本集合没有穷尽所有 RVV。计时输入为冻结合成 fixture x0；x1/x2 仅用于功能验证。稳定 R5 默认与其他合同的 HOLD 均保持原适用范围。

## 1. 五路全部观察

每一行都是完整 Q，包含入口/出口、整数核、严格逐组 FP32 消费及全部输出写入。没有扣除估计开销。以下为正常恢复的原始观察；独立重放完整 validation JSON 相同，不增加统计样本。

| 方法 | 实际 cycle 观察 | 均值 cycle | 每窗实际 CSR instret |
|---|---|---:|---:|
| acc8-vdot | 82,314；82,270 | 82,292.00 | 72,865 |
| acc8-RVV3 | 90,567；90,629 | 90,598.00 | 56,341 |
| acc8-RVV4 | 88,453；88,456；88,420；88,396 | 88,431.25 | 56,017 |
| fused-vdot | 62,691；62,692 | **62,691.50** | 52,529 |
| fused-RVV4 | 67,298；67,311 | 67,304.50 | 35,681 |

全部四个 AR4 共同锚点同时属于其方法观察，包括更快的末尾点 88,396。最大/最小为 88,456/88,396，差 60 拍、**0.067876%**，通过事前 1% 门槛。两组顺序与共同 prepare/selfwarm 策略均在首次运行前冻结，全部 UART 后置。

| 对应比较 | 均值周期减少 | 最慢候选对最快基线的周期减少 | 事前 0.5% 分离门槛 |
|---|---:|---:|---|
| fused-vdot 对 acc8-vdot | 23.818233% | **23.797253%**（62,692 对 82,270） | PASS |
| fused-RVV4 对全部四个 acc8-RVV4 | 23.890593% | **23.852889%**（67,311 对 88,396） | PASS |
| fused-vdot 对全部三条 RVV 路径 | 6.853925%（对最快 RVV 均值） | **6.844186%**（62,692 对 67,298） | PASS |

每块的软件比较也分别通过。最后一项直接使用 AR3 两点、AR4 四点和 FR 两点中的最小值，没有先按均值挑对照而漏掉反证。符合条件的 vdot 只有 fused-vdot，因此固定选择器返回 wrapper `q288_fused_vdot`、leaf 身份 `split_gemv_8x32_vdot`。保守周期比为约 1.07347×；不能把“少 6.84% 周期”与“快 6.84%”混用。

1%/0.5% 是本研发合同的稳定性与采用门槛，不是赛事评分标准。两个固定顺序点及确定性重放不构成统计显著性或任意调用历史下的保证；锚点变化也不是所有方法误差的已证明上界。

## 2. 实际正确性与三进程闭合

| 进程 | PID | UTC+08 时间 | 结果 |
|---|---:|---|---|
| negative | 1303 | 07:41:44.886703～07:41:52.114169 | 预定高位拒错，退出 1 |
| recovery | 1311 | 07:41:52.115308～08:13:21.293467 | 完整 DiffTest / counter / path PASS，退出 0 |
| replay | 3469 | 08:13:21.414336～08:45:26.617222 | 独立进程完整重放 PASS，退出 0 |

日期均为 2026-10-26。campaign 闭合于 **2026-10-26T08:45:29.091571+08:00**。两个正常进程各执行 2,410,050 guest cycles、1,682,220 retired instructions；这是整批功能/预热/计时/判定/输出的运行量，不能当作单 Q 或完整模型时间。宿主运行时间单独保留在原日志，不用它比较处理器性能。

负控在本 ELF 实际首条 probe PC `0x80001a04`、word `0x0388000b` 向 vd0 注入 bit100，原 DiffTest 的 mismatch PC 与注入 PC 相等；`ABORT` 事件字段 `0x800020cc` 单独记录，不误写成同一个 PC。正常 NEMU 和官方判定没有修改。其后才运行正常恢复与重放。

每个正常进程实际完成：

- 28 次完整 Q：12 计时、12 同方法 selfwarm、4 个 x1/x2 功能调用；每次检查全部 288 输出位模式，共 8,064 输出及 224 个末组完整 128 位槽观察。
- 5 个真实判定破坏控制全部拒错并恢复；guard、context、vl/vtype/vstart/vcsr/frm 检查通过。RNE、逐行 g0→g8、两次独立乘法再加 sum 的语义保持。
- 16 个 acc8 Q 的 5,184 次普通整数叶调用，加 12 个融合 Q 内部的 3,888 个整数核，共 9,072 个核心；函数体 FP 逻辑元素 convert/add 各 72,576，mul 145,152。
- 全阶段 **103,681 个 vdot COMMIT**，其中计时内 41,472；probe、功能、selfwarm、计时的完整 custom PC 序列与实际 ELF 路径逐项匹配。48 个 COUNTER_ENQUEUE 和 48 个 CSR_SAMPLE 闭合。
- 12 个计时窗的完整实际退休 PC/word、压缩 ROB 边界、4 CSR 与模型路径一致；不把非计时 RVV 调用冒称为具有完整 T13 退休 trace。它们由固定执行计划、实际 DiffTest 和逐调用完整结果判定共同见证。

两份正常 validation JSON 的 SHA256 均为 `357fe838e7bcccbfcaaab4340cbff48f39dee731142d300ee1c21a831564e4cb`。stderr 每份 288,416,760 字节、SHA `ae64e3e4c85af646beb977e9f78a8116a6c3d7a918cec899cb5c9588aeb7030a`，两份原字节相同。 stdout 含不同宿主耗时，未声称 stdout 全字节相同。

实际 CSR instret 比固定 marker 到 marker 模型路径少 5 条，来自同一冻结计数器协议的端点定义；AV/AR3/AR4/FV/FR 的模型路径分别 72,870/56,346/56,022/52,534/35,686，真实 CSR 分别 72,865/56,341/56,017/52,529/35,681。不是漏执行五条或任意扣除开销。

## 3. 源码与镜像身份

目标实现冻结于 `151481e916bfed0fc23b0223ee04b2085d18e25e`；build-02 保留构建前 HEAD `d3338c0ea507dd03558405f24fccdce1363750b3` 和 98 份逐文件 SHA，不能把构建前 HEAD 当成目标适配器提交身份。所有冻结文件在前后检查及后续交付中保持相同字节。

| 对象 | SHA256 |
|---|---|
| 目标合同 | `87564096ebe5e5846e8150fc97c7f973c33d1bfe4a1c187b7d0eff5888b0870b` |
| 实际目标 ELF | `e45105a5cd57289cfc5e031fc34ab86d799b02ba575438376e3df55662fbc801` |
| 实际目标 BIN | `c9783f1f64461cfb76906bf70948ab1e79c416d235d63d254c7a2e7c9af3ffb0` |
| 固定 T17 EMU | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 正常 NEMU | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` |
| flash | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994` |

目标 ELF 中完整 acc8 包装、共同 timer、六个整数叶分别与已冻结对象逐字节相同；两条融合函数与 [静态筛选 ELF](../RESULT.md) 的完整函数体相同，后者完整 ELF 的 SHA 为 `6975d57aecd77f9ec6337cbf3aa5b031033e8a7b86dcad4bcd7e78b33b2dc97d`。两种 ELF 身份分开记录，新的链接与调用计划有本次独立验证，未自动继承旧性能。

真实 GNU build-02、9 个方法/dataset 完整数值/地址路径、全部常量数组/指针表和 7 个实际 ELF 破坏负例通过。选择器另以更快末尾锚点、上下文失败、另一 vdot 候选三组反证检查全部观察保留及 HOLD 行为。build-01 的已有 ELF 元数据元组适配失败与初始原文保留；修复只在团队新适配器，不修改冻结解析器/官方代码。

## 4. 原始证据与隔离新源审计

[`evidence/target-v1/archive`](evidence/target-v1/archive) 保存原始归档和历史对象来源；主 [`payload.zip`](evidence/target-v1/archive/payload.zip) 包含 **163 成员、583,743,922 原始字节**，ZIP **44,193,367 字节**、SHA256 `de3afffda86d1db7981d793d17f180b6af879582530d0979fe313bea00170b6c`。完整 build/campaign 的命令、输入、原始 stdout/stderr、实际 ELF/BIN、负控和结果记录均可定位。

原文审计重新计算完整构建/路径身份、三进程回执、全部日志和选择结果。之后仅从封存的 98 源、固定补充审计器和 19 个原始 Git 对象建立临时小型源码闭包，在新 Python 进程中再次复算。原源码、原 build/run、硬件、AM/NEMU/flash 路径被固定 probe 拒绝访问；guard 自检、无被拒绝依赖访问、报告 SHA 与原结果严格相等均通过。它不是完整仓库克隆，也不是 OS 级 sandbox；离线审计不冒称再次核验了外部物理文件或再次执行 EMU。

本次预检发现团队旧 helper 的 180 秒宿主上限有规模风险，且超时路径可能在保存回执前清理临时目录。因此使用独立 [`host_audit.py`](host_audit.py) / [资源合同](HOST_AUDIT_CONTRACT.md)：原 98 源及全部判定保持，唯一的审计子进程上限为 900 秒，本次归档 driver 的外层上限为 1800 秒，日志从进程开始直接落盘。成功、退出7、超时三种实际小进程控制通过；正常、错误和缺失诊断均记录原事实。未执行或声称一次不存在的“旧180秒超时”。

最终原审计状态为 `FUSED_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS`，资源包装状态为 `FROZEN_FUSED_AUDIT_WITH_DURABLE_HOST_BUDGET_PASS`，实际完成于 **2026-10-26T08:51:31.029034+08:00**。原 child-audit、guard、完整命令及流见 [`audit-host`](evidence/target-v1/audit-host)。支持包 [`support.zip`](evidence/target-v1/support.zip) 保留失败 build-01、实际负例及驱动原文；成员清单与摘要见同目录。

所有 ZIP 与 `history/objects.pack` 在首次加入索引前使用模块 binary 属性；交付文件逐项与原件和 Git blob 比较。`all-blob-check.json` 记录原字节证明，外层 manifest→history manifest→原 pack/commands 的长度/SHA 关系保持，没有改清单迎合换行规范化。

## 5. 使用、复现与下一步

普通 C ABI、内存布局、两个显式入口和回退方式见 [融合 API](../README.md)。文档的 vdot/RVV4 两种 C 调用已分别经真实 GNU 编译/链接，实际调用目标及完整函数体核对一致；其原文在 `../evidence/c-api-v1`。当前固定性能资格不自动迁移到任意最终链接布局或应用调用历史。

在依赖已就绪的原生 Linux 中，从仓库根执行。`OUT` 是仓库外的绝对路径新父目录，`OPERATION_ID` 是本次唯一运行 ID；先按实际环境设置这两个变量：

```sh
Q=team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target
python3 "$Q/run.py" --repo "$PWD" --action build --output "$OUT/build"
python3 "$Q/run.py" --repo "$PWD" --action elf --build "$OUT/build" --output "$OUT/elf-controls"
python3 "$Q/run.py" --repo "$PWD" --action run --build "$OUT/build" \
  --output "$OUT/campaign" --operation-id "$OPERATION_ID"
python3 "$Q/archive.py" --action pack --build "$OUT/build" \
  --run "$OUT/campaign" --output "$OUT/archive"
python3 "$Q/host_audit.py" --action audit --repo "$PWD" \
  --archive "$OUT/archive" --output "$OUT/fresh-audit"
```

对已提交证据可直接使用最后一条命令，把 `--archive` 指向本页归档目录，无需重跑 EMU。原 `archive.py --action audit-snapshot` 仍保留原 180 秒入口。所有新目标运行仍先核对协调 Issue、固定输入和总四核预算。

[完整上游 forward 观察](../../forward-host/RESULT.md) 已取得真实消费者产生的 72 个位置/矩阵案例及两融合 ELF 模型数值接续；没有替换整模型，也没有 token 加速。后续优先按实际消费者周期占比选择投入方向，不能由 INT8 乘项份额替代时间份额。

[phased](../phased/RESULT.md) 只保留单版静态候选：少 5.5524% 指令并改变 dot/add 重叠，当前总周期尚未证明配置指令是剩余瓶颈，因此本轮不自动追加另一完整 EMU 批。保留现已取得的融合收益、较快 RVV 和全部回退；有具体剩余成本证据再建立新目标合同。
