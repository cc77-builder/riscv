# 当前合并基线的新夹具回归合同

合同：`o2-merged-regression-new-fixture-v1`。本入口只验收同一份已构建合并硬件的架构、异常、拒错恢复和 O2 事务覆盖；不构建硬件、不比较性能。旧固定夹具合同及其失败／缺项原文保留。

## 固定身份与验收集合

| 对象 | 身份或要求 |
| --- | --- |
| 硬件源码 | `6d2abe403b07c297b8830a7d4f06e370b0a8e070` |
| EMU | `1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63` |
| 硬件 pins | `2c580afa6095cda5e9d1680b7e91939b6f182b21c47357c77402c2d6b09d0a2c` |
| 配置 | MinimalConfig，1 core，1 EMU thread；O2 elastic=1、T14 fused=1、O2/T13 trace=1，O1 handoff/O1 trace/T12 trace=0 |
| 正常 NEMU | `efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4`；验证实际源码／构建来源 |
| 新负控 | `6e8b3488bb4cc516f05a7aa81c40b9d5e66085e275d4fbe27da85f05748b9a5f`；复用 S2 已保存的实际编译产物及来源，固定 C 源码 `7b39400d…`，不重新编译 |
| 新 pair 镜像 | 原 canonical matrix0 BIN，`b8b7e1a7032070bdfdfc2a747ab6453011ea9959ebd5ac52ca21b439d4d113b3` |
| 复用 core | hello-vadd、functional-1…7、control、dense-batch128，精确 10 项 |
| 新 core | negative-vdot → functional-0，精确 2 项；相同镜像的新进程，正常启动必须晚于负控退出 |
| 复用补充 | o2-diagnostic、o2-control-diagnostic，精确 2 项；各自完整排空并重算覆盖 |
| 总集合 | 精确 12 core＋2 supplement＝14；只有本次 pair 是新增执行，复用不能计作新运行 |

原 `9b3aecf3…` 负控缺失仍是旧合同的 BLOCKED，不把新二进制写成相同身份。旧 B0/H1、S2 选定组合、R2-SELECT 四尺寸、T17 独立复现及 PPA 均不从本合同取得 PASS。

## 复用规则

`merged_regression.py` 将原检查器绑定到 6d2 的 Git blob、实际 Linux 源码和当前独立软件检出，三者逐字节一致。三个历史调度适配入口及两个 scheduler 另锁实际 SHA；已审查的适配仅涉及实际 ROOT、明确保持缺失负控为 BLOCKED、两并行／四并行调度与已完成结果接续。原黄金数据、正常任务检查器和旧脚本不修改。

当前来源链为：hello 从 `core-normal-partial-01` 经 `core-normal-parallel-02` 复制到 `core-normal-parallel-04`；functional-1/2 从 02 复制到 04；其余选定正常任务在 04 执行。每一跳核对完整文件集合与字节、result SHA、来源／目标、原时间和实际执行入口。最早批次保留了未更新的 RUNNING state，必须同时核对其明确退休记录；这不表示仍在运行，也不把该旧整批状态改成 PASS。原 functional-0 和 BLOCKED negative 作为历史保留，不进入新选定集合。

复用任务全部从 stdout、stderr、实际退出码及派生 run.log 重新计算，要求后者严格等于 stderr＋stdout。正常结果通过原完整架构／异常／提交检查，control 独立满足七个 legacy 义务，dense 满足原 12 窗口及双槽重叠条件。六个 O2 目标仅从合格完整轨迹重新取并集，补充任务必须使用同一硬件与共享检查器。

旧 driver 未记录的 PID 或新增运行字段不补造；历史四并行只用作正确性证据，不据其运行耗时推导性能。实际引用链、旧状态及文件哈希保存在 `adoption-provenance.json` 与 `runtime-inputs.json`。

## 新负控、恢复与输入保护

先完成复用原文审计，再启动串行 pair。每次实际启动、PID、开始／结束时间、退出状态和原始流分别记录；PID 明确为 `timeout` 进程组首进程，可沿其子进程定位 EMU。state 的 `active_result` 指向正在更新的 `runtime.json`，`active_process_group` 用于活跃定位；失败尝试也保留，不根据测试结果删除启动次数。

每个新进程使用独立 cwd，辅助文件位于 EMU 实际读取的 `cwd/build/constantin.txt` 与 `cwd/build/plusArgs`，运行前后核对固定哈希。命令保留旧 matrix 合同的 128MB RAM、5,000,000 max-cycles、120m timeout、完整正常参考路径；两次仅切换参考库及 `XS_NEGATIVE_VECTOR_TARGET`。负控要求 bit100 精确拒错、原始 stdout 中唯一相邻 mismatch→abort、实际 ELF 的 PC／指令字绑定，以及合法 O2 部分轨迹。恢复必须以正常 NEMU 新启动、退出0，通过完整 matrix0 黄金数据及完整事务排空。

硬件源码／依赖／生成物、EMU、normal NEMU、flash、旧 workload／checker／raw 记录、新夹具及 controller 在整个运行期间保持输入保护。保护定位与释放只在协调 Issue 管理，文档不维护持有人表。

## 执行与原文复算

本地 JSON 配置必须且仅包含以下路径键，个人绝对路径保存在运行目录的 `runtime.local.json`／`local-config.json`：

```json
{
  "hardware_source": "/absolute/retained/hardware-checkout",
  "build_record": "/absolute/legacy-base/build-02",
  "build_driver": "/absolute/legacy-base/tools-attempt02/build_fullcore_local.py",
  "reference": "/absolute/normal-nemu",
  "flash": "/absolute/boot-flash.bin",
  "legacy_base": "/absolute/legacy-base",
  "fixture_dir": "/absolute/retained-s2-run/negative-fixture"
}
```

从已确认软件仓库根执行，所有输出使用新路径：

```bash
python3 -B -m unittest discover \
  -s team/optimizations/o2/fullcore -p 'test_merged_regression.py'
python3 -B team/optimizations/o2/fullcore/merged_regression.py \
  --repo "$PWD" --config "$MERGE_REG_CONFIG" \
  --output "$MERGE_REG_RUN" --operation-id "$MERGE_REG_OPERATION"
python3 -B team/optimizations/o2/fullcore/merged_regression.py \
  --repo "$PWD" --action audit --campaign "$MERGE_REG_RUN" \
  --output "$MERGE_REG_AUDIT"
```

`run` 不支持中断续跑，不得对原输出重新启动。发生中断先核对 state、实际进程和输入保护；修正后若确需再执行，应使用新输出并记录前次实际启动。`audit` 不启动 EMU，但仍要求保留 Linux 实物输入及原来源链；它从原14项 raw 记录重算并比较架构／覆盖语义结果，不将 archive-byte 检查称为完整架构复算。若仅能访问归档字节，应按相应证据层级报告。

## 本次结果

实际选定集合与 Linux 实物审计已通过；2026-10-24 接续完成原 archive-02 的完整离线架构／控制／O2 复算。
本轮没有新增 EMU。12 core＋2 supplement、13 条完整正常轨迹及 1 条预期拒错轨迹齐全；
六个 O2 覆盖目标全部满足。controller 与原始运行／归档字节保持不变。
输入清单的 JSON 键顺序差异已在独立证据工具中修复，不改变判定标准。
具体身份、证据、命令、失败保留与适用边界见 [MERGED_REGRESSION_RESULT.md](MERGED_REGRESSION_RESULT.md)。
