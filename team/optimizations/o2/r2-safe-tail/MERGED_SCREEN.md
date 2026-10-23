# R2-S2：合并版单硬件软件筛选

## 目的与边界

`merged_screen.py` 实现独立合同 `r2-s2-merged-software-screen-v1`。它消除的是：现有 S2 安全尾部在**当前已构建的合并版 O2/H1 硬件**上是否正确、是否相对 S0 降低固定 O3 GEMV 内核窗口周期的不确定性。

本合同不替换 [FULLCORE_VALIDATION.md](FULLCORE_VALIDATION.md) 中的固定 B0/H1 对照。原 26 ELF、60 次 B0/H1 运行及 768 正式窗口仍按原入口和原固定哈希复现。缺失的旧实物仍是 BLOCKED；新合并 EMU、重新编译的负控参考库均不冒充旧身份。本结果也不是 MERGE-REG 整套功能／异常验收、整核频率、功耗或面积结论。

源候选 `candidate.py`、O3 模型、完整黄金值、严格链接 ELF 门禁、CSR/退休窗口和 O2 事务检查均保持原身份。新增入口消费已成功的 canonical build-only 输出，不重复构建 26 份 ELF，也不声称原 `fullcore_screen.py --action all` 支持恢复。

## 实验假设和决定规则

假设：对 4×13 的剩余五项，S2 的安全向量读取、显式补零、恢复 VL=8 和第二次 dot8，能够抵消原标量乘加尾部的开销。

主要判断使用 **4×13 / reuse / endtoend 的 S2 对 S0 周期**，同时报告 basic、core、全部三个数据集及较快的合格 RVV。只在真实正确性、确定性重放和控制不变成立时评价性能。若端到端无收益，保留 S0；若只在部分软件布局有效，明确适用布局，不能把局部收益写成统一默认采用。采用还需按路线进入 R2-SELECT 的四尺寸完整比较及相应组合回归。

endtoend 沿用 [O3 固定内核窗口](../../../workloads/o3-gemv/CONTRACT.md)：包含内核配置、输入加载、计算与输出存储；框架的 VS 启用及寄存器哨兵初始化在窗外。core/endtoend 分别比较，不用二者相减推导可加成本，也不用于完整系统或 LLM 延迟结论。

16×64 是不变控制：S0/S2 的完整加载镜像必须逐字节一致，同硬件逐窗口的周期、退休数与序号必须一致。S0/S2 中 RVV 内核地址和机器码必须一致。比较 RVV 时保留 S0/S2、basic/reuse 中周期最小的合格实现，不能只取有利的较慢对照。

## 硬件身份

| 项目 | 固定身份 |
| --- | --- |
| 源码提交 | `6d2abe403b07c297b8830a7d4f06e370b0a8e070` |
| EMU SHA-256 | `1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63` |
| hardware-inputs.json SHA-256 | `2c580afa6095cda5e9d1680b7e91939b6f182b21c47357c77402c2d6b09d0a2c` |
| generated-artifacts.json SHA-256 | `0ed279de2f10071ab763457097bfd9fdf1e304c3f01caee542753d93417f7b28` |
| 源码／依赖／生成物 | 429 / 21,236 / 1,672 份，实际内容逐项验证 |
| 配置 | MinimalConfig，单核、单 EMU 线程，O2 两槽、T14 fused input、O2/T13 trace |

预检验证源码 Git blob、实际源码及依赖、实际生成物、成功构建状态、EMU、两个运行辅助文件、正常 NEMU 完整来源和 flash。构建元数据、命令与七份工具版本日志按独立新合同固定。`hardware_profile()` 在整批开始、结束核对完整实物；每次运行前后核对所有运行输入及 checker 身份。

此构建的实际 builder 是外部保存的资源适配副本，其 SHA-256 为 `c23603e89baa6e428e67104fc1a8cb3f128eec59d06b026807dcd26291797e56`。相对原脚本 `8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0`，仅绑定实际 ROOT、JVM heap 12G→8G／stack 16m、编译并行 2→4。两个身份分别验证，实际路径通过本地配置提供；不修改原脚本或旧构建记录。

## 运行顺序和样本数量

1. 校验原 build-only 状态及完整 26 ELF；交叉绑定 inventory 标签、`build.json.selection`、manifest 的 S0/S2、suite、dataset、shard，拒绝标签错配。
2. 编译固定 bit100 夹具源码，使用新输出路径和真实新哈希。保存编译 argv、编译器版本、DT_NEEDED、正常参考库哈希和源码快照。
3. 对 S2 smoke 执行一次实际负控，必须退出 1，且严格满足唯一 bit100 注入、同 PC/寄存器的 high-half mismatch、精确 `1<<36` 高半部差值和紧邻的唯一 ABORT。还核验加载参考库路径、ELF 中实际指令字及中止前 O2 部分轨迹。普通非零、超时、崩溃均不算通过。
4. 负控完成后，使用同镜像、同 EMU、同 flash 和正常 NEMU 启动新进程完成 S2 smoke；再完成 S0 smoke。二者均通过完整黄金值、CSR、退休数、真实 DiffTest 和 O2 排空门禁。
5. 执行 4 shard × 3 数据集 × 2 变体 = 24 正式运行。奇数数据集交换 S0/S2 顺序。无并行 EMU。
6. 对 dataset0 的 16×64 与 4×13 endtoend，重放两个变体，共 4 次，逐窗口周期、退休数、序号必须相同。

总数为 **30 次正常运行＋1 次预期拒错**。正式样本只有 performance、replay=0、phase=measured：4 shard × 2 变体 × 2 software × 2 method × 3 数据集 × 4 轮 = **384 窗口**。first、warmup、smoke、重放不充当新增正式样本。16 个汇总行中，每行分别有 vdot、RVV 两组，各 12 个样本；保留均值、总和、极值、总体标准差及所有原始值。

负控在第一次合法 vdot 后修改返回给 DiffTest 的状态副本，证明高位错误可被真实检测；它不按尾段 PC 选择注入，因此不声称专门对 S2 尾指令做故障注入。S2 的正常完整结果检查承担执行正确性验证。

## 配置与调用

复用原 GNU+nexus-am 构建命令得到 `CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN` 后，创建不提交的本地 JSON：

```json
{
  "hardware_source": "/path/to/merged-source",
  "build_record": "/path/to/merged-build-record",
  "build_driver": "/path/to/actual-recorded-build-driver.py",
  "canonical_build": "/path/to/canonical-build-only-output",
  "reference": "/path/to/verified/reference/build/riscv64-nemu-interpreter-so",
  "flash": "/path/to/verified/boot-flash.bin"
}
```

在同一检出的仓库根执行下列命令；变量分别指向自己的本地配置与全新输出目录。先核对协调 Issue 的认领、同机资源及运行输入保护。

```bash
python3 -B -m unittest discover -s team/optimizations/o2/r2-safe-tail -p 'test_*.py'
python3 -B team/optimizations/o2/r2-safe-tail/merged_screen.py \
  --repo "$PWD" --config "$R2_MERGED_CONFIG" \
  --output "$R2_MERGED_PREFLIGHT" --action preflight
python3 -B team/optimizations/o2/r2-safe-tail/merged_screen.py \
  --repo "$PWD" --config "$R2_MERGED_CONFIG" \
  --output "$R2_MERGED_RUN" --action run
```

每个输出必须不存在。预检不运行 EMU；run 会重新核对输入，但复用已经存在的 canonical ELF。运行目录 `runs/*/cwd` 有独立的辅助文件副本，不在共享硬件工作树中生成运行输出。

完成后的封存及独立离线复算：

```bash
python3 -B team/optimizations/o2/r2-safe-tail/merged_evidence.py \
  --repo "$PWD" --action pack --run "$R2_MERGED_RUN" --archive "$R2_MERGED_ARCHIVE"
python3 -B team/optimizations/o2/r2-safe-tail/merged_evidence.py \
  --repo "$PWD" --action audit --archive "$R2_MERGED_ARCHIVE" --output "$R2_MERGED_AUDIT"
```

封存路径必须是全新目录且位于所有输入之外；额外构建/主机测试/失败预检证据可用重复的 `--support` 参数加入。归档分别校验原始字节和确定性 gzip 字节，保留所有31次运行、26份链接产物、固定源码、实际编译命令、构建身份和原始轨迹。EMU、正常 NEMU、flash 和两份 AM 库仅保留固定哈希及来源，不把大型实物重复放进 Git。

归档准备入库时，先放到仓库内相应证据目录。普通 `git add` 会受原忽略规则影响而漏掉 ELF、BIN、对象和部分原始日志；仅对这批已审查的归档显式添加，再检查清单与 Git 索引的完整一致性：

```bash
git add -f -- "$R2_MERGED_ARCHIVE"
python3 -B team/optimizations/o2/r2-safe-tail/merged_index.py \
  --repo "$PWD" --archive "$R2_MERGED_ARCHIVE" --output "$R2_MERGED_INDEX_AUDIT"
```

`merged_index.py` 只读检查清单中每个文件及三个归档元数据文件均已暂存，且每个 Git blob 与封存字节相同；缺文件、多文件或文本转换均拒绝。它本身不暂存、不修改归档、不替代架构复算。索引审计输出使用新路径并随结果入库。本次实际漏303文件的状态已被该门禁拒绝，补全后965文件通过；见结果中的拒错和通过回执。

完整离线 auditor 使用 Linux/Python 3.10+ 和带有固定源码历史的本仓库，不调用 EMU、NEMU、汇编器或综合工具。它在临时目录解包原文，重做 ELF/黄金值、CSR/退休窗口、O2 事务、真实拒错日志、正常恢复、控制不变、重放和384样本统计；不只读取缓存 PASS。原固定生成器使用平台默认文本换行，原严格重生成检查按字节比较，本入口没有增加 Windows 换行适配；Windows 上的归档字节核验不能替代这项完整架构复算。复算结果明确注明没有重新核验当前机器的外部硬件/参考模型实物，也不是新一次性能测量。FU 接受/响应时间只作已测窗口内的观察诊断，不当作整窗口的因果分摊。

## 结果、保护和中断

`state.json` 记录真实新 EMU 启动数、active_result、active_pid、当前阶段、最终状态和起止时间。每次运行有实际 argv/cwd、输入哈希、stdout/stderr 原文及其哈希、真实退出码和 O2 observation。最终 `results.json` 包含全部正常记录、负控记录、384 样本、16 个汇总单元以及 S0/较快 RVV 比较。

只有完成全部门禁才写 `R2_S2_MERGED_SOFTWARE_SCREEN_PASS`。任何失败均保存原输出并停止扩大实验；不能修改原日志、黄金值或固定哈希以取得 PASS。

**本入口不支持断点续跑或仅重跑单个失败样本。** 任务活跃时先依据 state、真实进程和 Worker 检查，不能重复启动。需中断时按 Issue 的运行保护规则处理。任务确已结束后，先定位失败；保留旧输出，本入口的 `--action run` 在新目录重新执行完整 31 次批次，不拼接旧批次的部分结果。26 份已有静态构建可以再次严格核对后复用，不能把新 EMU 批次称为旧批次续跑。受保护物理输入在运行结束且确认释放前不得修改。
