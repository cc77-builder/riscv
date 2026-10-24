# R2-S2 固定完整布局重测与强 RVV 对照

本记录对应操作 `20261024-LiZufan001-r2s2-fixed-0001`。运行输入和协作状态以 [Issue #2](https://github.com/cc77-builder/riscv/issues/2) 的原事件为准；本文件记录工程结果与接续，不另建认领表。

## 结论

固定完整加载布局后，S2 的 K13 reuse 尾部收益仍然成立：endtoend 从 210 降至 187 周期，减少 **10.952%**；core 从 165 降至 143，减少 **13.333%**。basic 则分别退化 21.117% 和 25.587%，不能用 reuse 的收益覆盖 basic 退化。16×64 的整 BIN 与逐窗结果均保持一致，是本次布局与运行的控制项。

**同镜像强 RVV 探针否定了继续扩大 S2 采用的价值。** K13 reuse/endtoend 的 S2 为 187 周期，较快 RVV 为 175.25，S2 慢 **6.705%**（RVV/S2=0.937166×）。按事先停止条件，不再扩大 S2 采用矩阵；保留已合格 S1 RVV 和 S0 vdot 回退。探针只覆盖 dataset0/endtoend、四窗口单元格，不能写成完整三数据集/两 scope 资格。

这里只评价固定合并硬件上 O3 内核计时窗口。endtoend 包含配置、读取、计算、存储，仍不是完整应用或系统时间。没有 RTL 更改；本次没有面积、时序、功耗或新整核构建收益，不能由 FU 周期外推这些指标。

## 为什么必须重新测量

[旧合并结果](MERGED_RESULT.md)保留了真实架构正确性证据，但其 K13 S0/S2 的 caller 和后续加载字节未固定，历史性能差不能单独归因于 safe-tail。不能用旧 209.5→187.25 的差值恢复采用，也不能用 S1 另一 UART 合同的 175 周期直接拼接新的 S2 加速比。

本次新增适配器，保留冻结 S0/S2 候选、黄金数据和原 checker。四个内核固定为完整 8 KiB 槽；生成汇编显式加入 `.option norelax`，独立对象无有效重定位，并比较独立 GNU 对象与 AM 链接后的全部槽。S0/S2 必须具有相同入口、program headers、全部 ALLOC 节、main 和其它加载字节。K13 仅允许两个 vdot 槽及两个精确 dots 元数据字段由 4 改为 8；两个 RVV 槽完整不变。详细规则见 [FIXED_LAYOUT.md](FIXED_LAYOUT.md)。

## 固定布局主批

实际内部运行时间：**2026-10-23 16:23:40.757984–17:23:19.672103 UTC+00:00**；原始 controller 16:23:40.593522–17:23:19.696161。外层自然 exit 0、cleanup_complete；未重启、未续跑。运行状态为 `R2_S2_FIXED_LAYOUT_SOFTWARE_SCREEN_PASS`。

- **31 次实际 EMU**：1 次预期 bit100 负控、30 次正常；正常中有 2 次 smoke、24 次正式和 4 次确定性重放。
- **384 个正式窗口**：2 variants × 2 shapes × 2 scopes × 2 software × 2 methods × 3 datasets × 4 repeats。每单元格 12 个窗口；first、warmup 和重放均不增加正式样本。
- 全宽结果、高 96 位、CSR、精确 custom 退休、正常 NEMU 载入身份、O2 排空和提交对应关系均由原文检查。负控按真实指令建立高半部拒错链，并以新进程正常恢复。
- 最终源码下 20 项主机/GNU/布局测试通过，使用 8 份真实 AM 测试 ELF 和 288 个机器码输入试验；canonical 另为 26 ELF、13 对。这些是软件静态与模型层，不替代整核运行。

下表为正式周期均值；变化率为 `S2/S0−1`。本表 RVV 是原 O3 RVV，不能据此忽略更快的合格 RVV。

| 形状 | scope | software | S0 vdot | S2 vdot | vdot 变化 | S0 镜像 RVV | S2 镜像 RVV |
|---|---|---|---:|---:|---:|---:|---:|
| 16×64 | core | basic | 2145.25 | 2145.25 | 0.000% | 1381.75 | 1381.75 |
| 16×64 | core | reuse | 772 | 772 | 0.000% | 826.75 | 826.75 |
| 16×64 | endtoend | basic | 2214.5 | 2214.5 | 0.000% | 1452.75 | 1452.75 |
| 16×64 | endtoend | reuse | 845.25 | 845.25 | 0.000% | 893.75 | 893.75 |
| 4×13 | core | basic | 202.25 | 254 | 25.587% | 274.25 | 274 |
| 4×13 | core | reuse | 165 | 143 | -13.333% | 148 | 148.25 |
| 4×13 | endtoend | basic | 246.25 | 298.25 | 21.117% | 320 | 320 |
| 4×13 | endtoend | reuse | 210 | 187 | -10.952% | 190 | 190.25 |

原 RVV 下 K13 endtoend 的最快 RVV 为 190 周期，S2 reuse 为 187；这个约 1.016× 的比值只是旧 RVV 对照。完整总周期、样本、极值、离散度及全部逐窗记录在主批封存中，不仅保存表中有利格。

### 实际周期与 FU 诊断

[诊断派生数据](evidence/fixed-screen-v1-diagnostics.json)绑定完整 Linux 审计 SHA-256 `110072fd0e1117757558fcfdbc445345e44e4a7863a6fe337c261fb47852ed60`。192 个正式 vdot 窗口中，已观测响应延迟均为 2 周期，未观测到写回阻塞。K13 endtoend 的分段如下；这是观测区间，不是逐指令因果分解。

| software / variant | 窗口退休指令 | 到首次接收 | 接收跨度 | 响应延迟 | 最后观测响应到窗口结束 | 总周期 |
|---|---:|---:|---:|---:|---:|---:|
| basic S0 | 153 | 78 | 81 | 2 | 85.25 | 246.25 |
| basic S2 | 125 | 80 | 139 | 2 | 77.25 | 298.25 |
| reuse S0 | 124 | 80 | 5 | 2 | 123 | 210 |
| reuse S2 | 90 | 83 | 25 | 2 | 77 | 187 |

reuse 收益伴随最后一次观测响应后的区间减少 46 周期，同时首次接收晚 3 周期、接收跨度增加 20，净减少 23。不能把 46 周期全部归于一条指令或某类依赖。basic 虽少退休 28 条指令，接收跨度却增加 58 周期，完整窗口退化 52 周期。它们说明少指令和固定的 FU 响应时间都不能代替端到端取舍。

这些数据没有提供优先扩大 R3 硬件修改的依据，也不能证明不存在发射侧阻塞或硬件已最优。静态完整函数 words 含计时外初始化/CSR，与这里的窗口内退休数不同；原始派生数据明确区分两者。

## 强 RVV 有界探针

合同见 [RVV_PROBE.md](RVV_PROBE.md)。两份新真实 AM 镜像仅允许两个 RVV 槽变化；S2 vdot 两槽、main、全部其它加载字节及元数据完全一致，**零元数据例外**。rvv0 使用原 RVV，rvv1 使用已发布 S1 RVV；没有将 S1 vdot 与 S2 尾部组合，也未修改任何冻结候选。

主批的实际 S2/dataset0/shard7 BIN 与 rvv0 的 1,250,336 字节 BIN 完全一致，SHA-256 均为 `d196c0ab19b2f6581b0246a84f57653197a270e267032b349ad07f410d14738c`。这比仅检查 8 KiB 槽更严格；实际新镜像仍按新运行合同验收。

实际内部运行时间 **2026-10-23 17:26:02.623205–17:32:59.074281 UTC+00:00**。5 次实际 EMU：rvv1 预期 bit100 负控 → 同镜像正常恢复 → rvv0 正常 → rvv0 重放 → rvv1 重放。4 次正常、1 次预期拒错，0 失败/未完；完整输出、CSR、退休、来源、O2 轨迹和精确重放通过。总计 32 正式窗口，每格 4 个，不把两个重放加入样本。

| variant | software | S2 vdot 总周期 / 均值 | RVV 总周期 / 均值 |
|---|---|---:|---:|
| rvv0：原 RVV | basic | 1193 / 298.25 | 1280 / 320 |
| rvv0：原 RVV | reuse | 748 / 187 | 761 / 190.25 |
| rvv1：较快 RVV | basic | 1193 / 298.25 | 864 / 216 |
| rvv1：较快 RVV | reuse | 748 / 187 | 701 / 175.25 |

本次两个镜像的 vdot 数值恰好相同，这是实际结果；合同不预设它们必须相同，也不能把相邻 RVV 改动引起的执行历史差别说成新的 vdot 优化。采用判断以 rvv1 同镜像比较为主，不能拿 S1 旧合同的 175 替换本次实测 175.25。

最终 probe 源码下 9 项 GNU/模型/完整布局测试通过，含 56 个机器码输入试验；两份 canonical ELF 独立构建、完整布局成对通过。全批结束前再次核验完整 canonical 及五份实际进程收据。


## 来源与复算

### 固定外部输入

| 对象 | 身份 |
|---|---|
| 合并硬件源码 | `6d2abe403b07c297b8830a7d4f06e370b0a8e070` |
| EMU SHA-256 | `1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63` |
| 硬件 pins SHA-256 | `2c580afa6095cda5e9d1680b7e91939b6f182b21c47357c77402c2d6b09d0a2c` |
| 正常 NEMU SHA-256 | `efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4` |
| flash SHA-256 | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994` |
| AM 提交 | `086a238062fdfb3281b745a537b361983d0154b5` |
| AM 两个库 SHA-256 | `50443c3abb089f8d8e586d03cabb7770e5ac75738bbc1b44dc8b730ae3e67505`；`eec19a2a8e55ac89331ad63fba29095f2f76e2fa207ef31c3baa41105eb4bc76` |

使用 MinimalConfig、单核/单线程、128 MiB RAM、seed 1、每进程 max-cycles 2,000,000。硬件来源清单为 429 源文件、21,236 依赖文件和 1,672 生成文件。硬件、参考模型及库的实体不放入软件归档；离线复算保留其来源/哈希，不能声称重新取得或执行这些实体。

### 源码身份与持久化

主批原运行检出基点 `bca14d45b07ff07a86a7f54bce2b25870e60e2f3`，最终交付在包含 S1 的 `ec221262ae29522dd9d1a2be7240b405cc23a549` 上准备；新增源码以实际 SHA-256 和源快照绑定，没有把未提交源码冒写成基点提交内容。

| 新入口 | SHA-256 |
|---|---|
| `fixed_layout.py` | `92e025d334c71c3720a92beb4f92314fbe8fabc3c5722b8a733f1cb6c0f7bc29` |
| `fixed_screen.py` | `958dcb5303f09ddcf9ebf2f3a8e1225b5541d76f3f86a4aabf9c540ed9757e1d` |
| `fixed_evidence.py` | `fca140bb69b079eccb97e112da96435a05ab91f408d8096466ddaa95e9cbf6de` |
| `rvv_probe.py` | `035a0020733e00a6bded6921e7ee78afe2522f0ccb78c3680d89ac13bc38db6a` |
| `rvv_probe_evidence.py` | `dc75a716b7188c5270737334a510317a46e7289e682272fe542a09c7fd59762d` |

两份归档均保存真实 ELF/BIN、源码快照、命令、输入哈希、原始 stdout/stderr、全宽结果/CSR/退休/O2 轨迹与拒错链。它们在另一完整原生 Linux 检出中通过原文复算；该检出为 `ec221262` 加精确源码副本，**不是干净环境重新构建 T17，也不是成员人工验收**。复算命令见两个合同页；都没有新增 EMU/NEMU。

| 验证层级 | 实际状态与定位 |
|---|---|
| 最终主批静态/机器码 | **PASS**：20 测试、8 AM 测试 ELF、288 机器码试验；另 26 canonical ELF/13 完整布局对。实际命令在主归档 `support/tests-02-command`、`build-02-command` |
| 历史兼容 | **PASS**：88 项既有门禁；退出新 binding 后旧合同恢复。旧归档完整原文复算 PASS，未恢复旧 K13 的公平性能资格；回执在主归档支持目录 |
| 最终强 RVV 静态/模型 | **PASS**：9 测试、56 机器码试验、2 canonical ELF/1 对；见探针归档 `support/tests-03-command` 与 `build-02-command` |
| 主批真实 EMU/DiffTest | **PASS**：31 进程、384 正式窗口、4 replay；[终态](evidence/fixed-screen-v1/files/campaign/state.json)、[完整原始结果](evidence/fixed-screen-v1/files/campaign/results.json.gz) |
| 探针真实 EMU/DiffTest | **PASS**：5 进程、32 正式窗口、2 replay；[终态](evidence/rvv-probe-v1/files/campaign/state.json)、[原始结果](evidence/rvv-probe-v1/files/campaign/results.json.gz) |
| 主批独立 Linux 完整复算 | **PASS**：[报告](evidence/fixed-screen-v1-audit-linux.json)，SHA-256 `110072fd0e1117757558fcfdbc445345e44e4a7863a6fe337c261fb47852ed60`；[10 项归档拒错测试](evidence/fixed-screen-v1-tests/stderr.log)均通过，无 skip |
| 探针独立 Linux 完整复算 | **PASS**：[报告](evidence/rvv-probe-v1-audit-linux.json)，SHA-256 `1e087a69992673692d53c8c25f1ce0dd34ce35db1880c900d4e99e0cdb2c67dc`；[5 项针对性归档负测](evidence/rvv-probe-v1-tests/stderr.log)均通过，无 skip |
| 主批/探针直接控制关系 | **PASS**：[实际 BIN 哈希关系](evidence/rvv-probe-v1/files/support/main-image-relationship.json)与[跨批全部 24 窗口签名](evidence/rvv-probe-v1-main-window-relationship.json)一致。含 first/warmup/measured，不增加正式样本 |
| 原生 Windows 封存字节/完整布局与实际 Git 索引 | **PASS**：[主批 994 文件](evidence/fixed-screen-v1-index-windows.json)、[探针 204 文件](evidence/rvv-probe-v1-index-windows.json)，均为唯一 stage 0、100644、清单无缺失/额外项，Git blob 与封存字节相同；Python 3.13.13。完整架构复算在 Linux 执行，Windows 该层 **NOT_TESTED** |
| 原固定 B0/H1 两硬件合同 | **BLOCKED**：旧固定实物未恢复；没有改变旧哈希或借合并 EMU 冒充 |
| 强 RVV 全矩阵、S1+S2 组合、生产默认、R4/T17、PPA | **NOT_TESTED**：当前有界否决无需扩大无收益候选；不转移旧 PASS |

主归档 [manifest](evidence/fixed-screen-v1/archive-manifest.json) SHA-256为 `ffbab60af26f77854d3d5847a11ed992e4599e1d9e21edcb3eca2a6e35b32df0`，991 个 payload，原始 277,369,094 字节，封存 56,153,666 字节。探针 [manifest](evidence/rvv-probe-v1/archive-manifest.json)为 `f4a26857a5dffd98f3a187f82eb71e08b3e9d134b74713af223094ffbfb4d3f9`，201 个 payload，原始 28,716,972 字节，封存 3,596,406 字节。每份归档另有 3 个元数据文件。外置复算报告和原始命令按[复制清单](evidence/fixed-rvv-report-copy.json)逐字节保留。


## 失败、未测边界与接续

探针第一次 9 项静态测试中有 1 项 **FAIL**：测试把 RVV 的逻辑 dots 数误当作 custom 退休数。只修正该测试的语义预期，未改候选、黄金数据或退休检查器；原失败日志、原测试/生成器源码保存在探针归档 `support/tests-01-command` 和 `support/tests-01-source`，最终源码的通过回执是 `tests-03-command`。早期主批 build-01/test-01 属于另一适配器身份，原输出保留，未转算成最终源码 PASS。

准备源码后的 WSL Git 状态扫描曾超时；独立检查确认文件 SHA 完整且没有遗留 Git 进程。事后观察命令还曾将 Path 误传给要求 state 对象的辅助函数，在写结果前失败；正确解析 JSON 后完成检查，没有重启 EMU或更改运行数据。两项原失败收据及诊断均在探针归档支持目录，不能将工具命令失败隐去或误报成硬件失败。

**当前决定：**关闭本候选的扩大采用方向，保留可复现实现、回退和真实收益；按预定停止条件不再扩大强 RVV 全矩阵。否决范围限于本次采用方向，不推断未执行范围的周期结果。下一项是按 Issue 认领 `R2-SELECT`，从已发布 S1 v2 归档内的 S0/S1 完整 12 窗口矩阵构造可检查的四尺寸选择入口：4×8、8×32、16×64 选 S1 reuse vdot；K13 选较快 S1 reuse RVV，保留 S0 vdot 回退。来源入口为 [S1 最终验证](../r2-vector-accum/VALIDATION.md)及 `team/optimizations/o2/r2-vector-accum/evidence/merged-v2`，不能混入旧 O3/S2 的同名 S0。

该映射只描述各自原镜像中已验证的窗口。若增加统一调度、合并链接、缩槽、删除其它 case 或改变 caller，必须验证新 ELF/调用路径；可先用正收益余量最小的 **8×32、dataset0、endtoend** 比较实际新入口和强 RVV，正确性与重放通过且保留收益后才扩大受影响范围。新首 custom 位置或目的寄存器变化时，负控也按实际新指令绑定。若新入口吃掉优势，保留 RVV 或原合格入口，不沿用旧均值背书。

MERGE-REG 的现有他人认领和输入保护仍须依 Issue 核实，本次不接管或代签。两个本操作 EMU campaign 均已自然结束、无遗留活动 PID；具体源根、配置和运行/审计命令已在两份归档与外置回执中保存。实时认领释放、停止写入及发布状态仅由本操作的 Issue 收尾事件确定。
