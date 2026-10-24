# R2-S1：向量累加与对等 RVV

当前新增的首块直接初始化子项已取得独立运行资格与可选C库，见 [Firstdot结果](FIRSTDOT_RESULT.md)、[普通C使用/复算/回退](FIRSTDOT_README.md)。原R5稳定默认入口保持不变。下文继续记录原S1与冻结v2批次，不将其旧PASS转移到新候选。

本模块检验一个独立假设：在输出向量寄存器中保留 INT32 部分和，可减少逐块向量到标量搬移及标量累加，并改善完整 GEMV 性能。候选以同一硬件上的新 S0 为对照；采用与否由真实整核结果决定。

## 边界与比较合同

- 形状为 4×8、8×32、16×64、4×13，每个形状保留 basic/reuse、core/endtoend、三组固定数据，以及原主机黄金值、全部 128 位输出、CSR、退休和 scratch 检查。
- S1 vdot 用临时向量接收 dot8 部分和，在 e32/VL4 下累加到对应输出寄存器。输出清零属于测量窗口。4×13 的剩余五项仍走原标量尾部，没有混入 S2。
- 对等 RVV 将宽归约的 scalar seed 和目的设为当前输出寄存器，使用 tu 保留已经清零的高 96 位；所有候选均遵守 v16..v31 scratch 预算，无 spill。
- v2 显式使用 `.option norelax`，S0/S1 都使用四个固定 8 KiB 函数槽，入口为 `0x80002000/4000/6000/8000`，`.text` 总长固定 40960 字节。所有加载段的类型、地址、大小、flags、对齐逐对相同，四槽以外的整个 BIN 逐字节相同。S0 指令主体与冻结 O3 完全相同，但由于布局不同，必须重新测量；不复用旧 S2 或已否决 v1 的周期。
- core 与 endtoend 延续 O3 定义。endtoend 保留原配置与输出存储；同一布局、同一输入、同一测量与退休检查。不能将 core 周期解释为应用性能。
- 硬件使用合并提交 6d2abe403b07c297b8830a7d4f06e370b0a8e070 的已有 minimal/VLEN128 EMU；实际源码、依赖、生成物及二进制由原 merged_screen 门禁核验。没有新 RTL、频率、面积或功耗结论。

## 证据层级

candidate.py 独立生成 S0/S1，不修改冻结 S2 candidate 或原黄金值。gate.py 在原 ELF 审核和有限指令模型上只增加严格的无掩码 e32 vadd；未知指令仍拒绝。重新生成逐字节核对 snapshot、manifest、汇编与头文件，实际链接 ELF 必须与独立 GNU 汇编相等。

experiment.py 使用私有模块实例把新生成门禁接入原 fullcore/merged 运行器。原 UART、CSR、精确退休、致命错误、reference 路径、O2 排空和提交数条件不变。所有镜像绑定相同源码、AM、库和工具链；结束前再次核验完整硬件来源及输入，最终计数通过后才写 PASS。

主机测试是实际 GNU 汇编指令的有限模型测试，不是 NEMU/RTL 协同仿真。test_candidate.py 包含三数据集、INT8 极值及漏清零、错误累加宽度、掩码、错误寄存器、错误归约种子、tail-agnostic、CSR 漏恢复、跨行读取和构建身份漂移负测。

### 寄存器和数值范围

| 对象 | vdot | RVV |
| --- | --- | --- |
| 当前组的输出／累加器 | 对应的 v0..v15，仅改本组 | 相同 |
| 当前组 A | v16..v19 | v16..v19 |
| 部分和／宽乘结果 | v20..v23 | v20:v21、v22:v23、v24:v25、v26:v27 |
| 预载 x | v24..v31，最多八个 dot8 块 | v28..v31，最多四个 16 项块 |

basic 一次处理一行，reuse 一次处理四行。已经完成的组不再写入，仍只使用原有 v16..v31 scratch。INT8 有符号乘积在 K≤64 时的精确总和范围为 [-1040384, 1048576]，INT32 不溢出。vdot 的高 96 位为零，因此四个 e32 lane 相加仍保持高位为零；RVV 的归约种子和目的各只占单个向量寄存器，允许同寄存器作种子与目的，tu 保留其已清零的高位。相关分配设计及指令规范依据见[原 S1 寄存器审查](../r2-safe-tail/S1_REGISTER_REVIEW.md)。

### 为什么只固定函数入口不够

首版 v1 的真实 GNU 对象仍含八条 `R_RISCV_ALIGN`。虽然链接后的四个内核入口对齐，`.text` 的剩余尾部却依赖内核长度；冻结链接脚本中的 orphan `.text.startup` 和 AM 代码因而移动。首对 16×64/endtoend 的 main 相差 4480 字节，不能据此作公平性能取舍。该批次在发现后停止，原源码和输出保留。

v2 不改冻结的链接脚本：只在新模块生成汇编中显式禁用 relaxation，再用真实 AM 构建和加载映像检查证明效果。独立汇编对象必须恰好 32768 字节且无重定位；双版本非内核加载字节必须完全一致。GNU 对 `.option norelax` 的定义见[官方汇编器文档](https://sourceware.org/binutils/docs/as/RISC_002dV_002dDirectives.html)。测试还直接拒绝原 v1 的实际 ELF，避免仅凭新输出看似正常就关闭问题。

## 整核计划与决策

构建 52 个真实 AM 镜像：4 个 smoke，加上 2 variants ×8 shards ×3 datasets 的 48 个正式镜像。运行 57 次单进程 EMU：1 次新建负控、4 次正常 smoke（包括负控后的新进程恢复）、48 次正式运行、4 次重放。768 个正式测量窗口来自每镜像的 2 software ×2 methods ×4 measured repeats；warmup 和重放不混入正式样本。

同一 shard/dataset 内交替 S0/S1 顺序。57次主批次的专门重放覆盖 dataset0 的16×64和4×13 endtoend、S0/S1各一次，要求每个窗口的 cycles/instret 精确一致。4×8和8×32的同输入新进程重放由下述独立补充入口完成，不修改主批次计划或样本。结果同时报告 S0/S1 各方法，并从 S0/S1 × basic/reuse 中选最快合格 RVV 分母，保留退化组合。正确性失败即不采用；只有可重复的完整窗口收益才支持对应形状的选择。此筛选不替代 MERGE-REG、历史 B0/H1、完整 T17 或 PPA 验收。

## 运行

配置 JSON 仅包含 am_home、cross_prefix、hardware_source、build_record、build_driver、reference、flash；本机路径写 runtime.local.json，不进入共享配置。AM 固定提交与库来源由构建收据记录。构建只使用已准备的私有 AM 库。

下面的 shell 示例使用 Linux／WSL。`REPO` 是本次实际执行的完整 Git 根，其他输入／输出变量均使用绝对路径；`REPLAY_REPO` 是另一个完整 Linux 检出，`ARCHIVE_COPY` 是复制到该环境的完整封存目录。入口脚本与 `--repo` 必须属于同一检出。

```sh
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/test_candidate.py"
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/experiment.py" --action build --repo "$REPO" --config "$CONFIG" --output "$BUILD"
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/experiment.py" --action run --repo "$REPO" --config "$CONFIG" --build "$BUILD" --output "$RUN" --operation-id "$OPERATION_ID"
```

输出目录必须不存在。本脚本不支持断点续跑；run 可以消费已完成且身份仍一致的 BUILD，不能把重新构建或新建运行描述成恢复。state.json 保存真实进程与结果位置，build.json 保存源码快照、命令、依赖及产物。运行期间保护其实际输入，结束后按 Issue 规则释放。

实际执行状态、结果、失败定位及接续条件见 [VALIDATION.md](VALIDATION.md)。没有运行证据的层级记为 NOT_TESTED。

### 小形状的独立进程重放

`complete_replay.py` 只接受已经完成57次验收的主批次，且 run 必须从原 source_root 执行。它对 dataset0 的4×8、8×32 endtoend、S0/S1各启动一次相同镜像的新进程，继续使用原数学／CSR／精确退休／O2门禁，并逐项比较原过程的全部24个窗口 `(seq, cycles, instret)`；共96个匹配窗口，新增正式样本为零。运行前后核验原批次哈希、硬件及所用镜像；输出独立，不支持断点续跑。

```sh
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/complete_replay.py" --action run --repo "$REPO" --parent "$RUN" --output "$SMALL_REPLAY" --operation-id "$OPERATION_ID"
```

封存时须同时传入该输出目录和实际执行的 `complete_replay.py`，不能用另一检出的同字节副本代替其原路径：

```sh
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/evidence.py" --action pack --repo "$REPO" --run "$RUN" --archive "$ARCHIVE" --support "$SMALL_REPLAY" --support "$REPO/team/optimizations/o2/r2-vector-accum/complete_replay.py"
python3 -B "$REPLAY_REPO/team/optimizations/o2/r2-vector-accum/complete_replay.py" --action audit --repo "$REPLAY_REPO" --archive "$ARCHIVE_COPY" --supplement "$(basename "$SMALL_REPLAY")" --output "$SMALL_AUDIT"
```

补充 audit 从归档重算这四份原始日志、严格运行身份和精确签名，允许另一个完整 Linux 检出；它不代替下述主57次完整 audit，也不重新启动 EMU。两个审计必须绑定同一 archive manifest SHA。`$SMALL_REPLAY` 的 basename 应保持唯一；本轮实际为 `replay-small-01`。

### 首块直接写输出的静态探针

`first_dot_probe.py` 是已验证可编译的 S1 后续子项，尚未具备运行采用结论。它为四形状的 core/endtoend 各构建 S1 与 firstdot 两个版本，要求 S1 对照 BIN 与已有规范 BUILD 完全一致，再检查配对布局、RVV 完整槽、实际指令差额和有限模型。它保留 K13 标量尾项；当前冻结候选文件与运行合同不变。

```sh
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/first_dot_probe.py" --repo "$REPO" --config "$CONFIG" --canonical "$BUILD" --output "$FIRST_DOT_PROBE"
```

该命令产生16份 AM ELF，输出必须是新目录，不启动模拟器。探针 manifest 明确标记 `runtime_qualified=false`；其二进制 harness 标识仍与 S1 对照一致，以保持加载字节可比。若继续测周期，须先补独立的精确再生和运行合同，重新核对首条 custom 目的寄存器的负控／恢复，不可直接把探针收据当作 experiment.py 的规范构建。

## 归档与离线重算

evidence.py 在完成运行后保存版本 1 归档，压缩 ELF/BIN 中的填充及大日志，并同时保留原始字节与存储字节的大小和 SHA-256。audit 从归档逐项重算生成物、链接 ELF、数学/CSR/精确退休、O2 事务、负控与恢复、57份进程收据及统计。它不启动 EMU，也不声称重新验证未携带的硬件、参考模型、AM 或工具链实体。

此处的主架构重算覆盖归档中的规范 `canonical` 与 `campaign` 输入；`support` 保存失败定位、主机测试、独立探针及补充重放的原始收据和产物。主 audit 对附件执行完整字节检查；补充四次重放另由 `complete_replay.py --action audit` 做架构重算，不并入本批57次 PASS，其余附件不声称离线再次执行所有模型检查。

```sh
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/evidence.py" --action pack --repo "$REPO" --run "$RUN" --archive "$ARCHIVE"
python3 -B "$REPLAY_REPO/team/optimizations/o2/r2-vector-accum/evidence.py" --action audit --repo "$REPLAY_REPO" --archive "$ARCHIVE_COPY" --output "$AUDIT"
```

严格架构重算目前要求 Linux/WSL：冻结生成器的路径键和精确文本输出尚未适配原生 Windows。原生 Windows 可用相同入口的 --action bytes 校验全部原始/压缩字节与 manifest，但该结果明确标注 architecture_recomputed=false，不替代架构重算。不要为移机放宽固定哈希或改变已执行源码。

本轮部分支持附件路径超过260字符。在未启用普通长路径读取的Windows环境中，使用 `\\?\` 扩展路径调用同一入口；repo、archive和output保持同一前缀。以下PowerShell示例中，`$PythonExe` 指向原生Windows Python，`$RepoPath` 为已确认的绝对仓库根，输出文件必须尚不存在：

```powershell
$LongRepo = '\\?\' + $RepoPath
$S1 = "$LongRepo\team\optimizations\o2\r2-vector-accum"
& $PythonExe -B "$S1\evidence.py" --action bytes --repo $LongRepo --archive "$S1\evidence\merged-v2" --output "$S1\evidence\new-bytes-check.json"
```

这只改变操作系统的路径表示，归档路径、字节和检查器不改。实际普通路径失败、同文件扩展路径通过及完整字节核验的收据见VALIDATION；不需要修改系统注册表。Git暂存深层文件时可仅为该命令传 `-c core.longpaths=true`，index检查仍使用同一实际仓库和完整普通stage-0 blob门禁。

架构重算需要完整 Git 检出，包含冻结源码对象 `24cb8b2e0fa0b17cad65c82246c572347a351d43`，因为复用检查器通过 `git show` 校验原模型；单独解压 tools 目录不足。必须从所选仓库的本模块执行入口，不能从另一份草稿执行后用 `--repo` 指向不同源码。物理 EMU/NEMU/flash、硬件树、AM 库和 GNU 工具实体不随归档分发；归档记录其固定哈希，新的硬件复现仍须准备并验证这些输入。

### 发布字节检查

全部审计结果均写到归档目录外。封存目录严格只包含 manifest 声明的载荷及 `archive-manifest.json`、`archive-manifest.sha256`、`archive-check.json` 三份根元数据；把报告写到归档根也会破坏该库存。

仓库既有忽略规则会忽略部分 ELF/BIN/log。审阅归档后仅对目标归档使用 `git add -f -- "$ARCHIVE_RELATIVE"`，不要全局取消忽略规则。随后运行以下只读检查，它会逐项确认 Git index 内的普通 stage-0 文件、库存和实际 blob 字节，不仅检查磁盘文件：

```sh
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/evidence.py" --action index --repo "$REPO" --archive "$ARCHIVE" --output "$INDEX_AUDIT"
```

index action 固定复用旧 `merged_index.py` 的通用解析函数，独立检查 S1 合同与缓存状态；不修改旧 S2 检查器或借用旧 S2 的 PASS。模块内 `.gitattributes` 仅对 `evidence/**` 禁用文本转换，保留归档原字节。`test_evidence.py` 用实际临时 Git 仓库验证忽略漏项、缺元数据、额外暂存项、旧压缩 blob 和错误合同／缓存等失败方式。

归档外的审计报告和实际命令收据也须单独暂存。若其中原始日志命中既有忽略规则，只对已经审阅的具体验证收据目录显式 `git add -f`，不要扩大为强制添加整个工作树；发布检查应另确认这些外置报告与日志的blob字节。归档index检查的2797文件范围不能代替外置报告交付检查。
