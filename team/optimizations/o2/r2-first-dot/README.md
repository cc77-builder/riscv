> 已封存的本地8×32/dataset0探针（2026-10-27）：其bc9/e66身份与原始合同继续保留用于追溯，不再作为活动开发队列。上游已完成独立完整矩阵及[firstdot V2源包](../r2-select/FIRSTDOT_STABLE.md)；后续按[当前路线](../../../docs/development-route-current.md)执行，不重复本页五次运行或旧dataset扩展计划。

# First-dot：8×32 首块初始化优化

合同：`r2-first-dot-8x32-admission-v1`。本模块是独立接续，保留 S1、R5、旧探针及其资格。

首块 VDOT 直接写各行最终结果寄存器，省去清零及第一次向量加法；后续块沿用 S1。复用已冻结的 `first-dot-probe-02`，不重新生成整套 16 个探针 ELF。首轮仅 `dataset0 / shard3 / 8×32 / endtoend`，S1 与 firstdot 各一份四槽镜像，含 basic/reuse 的 VDOT/RVV。

## 本次已实现的静态准入

`admit.py` 固定 S1 `merged-v2` 归档清单 SHA `a1af4314…`，核验并提取两镜像的 66 个路径，输出必须与源码及归档分离。它不接受缓存 PASS 作为准入依据：

- 按清单核验压缩/原始字节，S1 控制 BIN 必须与已合格 canonical S1 完全相同。
- 核验源快照、两条原构建命令及原日志；使用固定 `first_dot_probe.py` (`0bb3de51…`) 精确再生 manifest、汇编和数据，旧源文件不改。
- 检查实际 ELF/BIN、独立汇编对象、无重定位、四个 8 KiB 槽及完整 ALLOC 布局；槽外字节、数据和两个 RVV 槽均相同。
- 对实际机器码执行 8 个内核×9 组有限模型检查，含全 128 位、CSR、行边界及初始寄存器污染。
- 从实际 ELF 解码首条 VDOT：firstdot 的目标为 **v0**，原 S1 为 **v20**。输出新负控目标 PC/word/rd 及 bit64 掩码，不沿用旧 v20 断言。

成功状态为 `FIRST_DOT_8X32_STATIC_ADMISSION_PASS_NOT_EXECUTED`。`runtime_qualified=false`、`performance_qualified=false`；新增编译、EMU、NEMU 均为 0。这是新合同下的输入准入，不是新机器工具安装资格、动态 DiffTest 或性能验收。

使用同目录源码的 Linux LF 检出执行，默认读取仓库内冻结归档：

```bash
python3 team/optimizations/o2/r2-first-dot/admit.py --output /absolute/new-output
python3 -m unittest discover -s team/optimizations/o2/r2-first-dot -p 'test_admit.py' -v
```

归档位于其他只读位置时，准入用 `--archive`，测试用环境变量 `FIRSTDOT_ARCHIVE`。输出保留源身份、原始输入及检查结果；失败单独保存，不能覆盖或续写旧输出。入口不支持 Windows CRLF 源码的精确再生。

## 有界动态运行合同

`runtime.py` 与测试专用 `negative.c` 绑定本机已核验的 `bc9e5ae4… / e66a8900…` 硬件、正常 NEMU、flash、辅助数据及完整输入合同；不借用上游 `34bae/ff840` 的运行资格。该 EMU 是 O2/H1 实验配置、O1 关闭；O1/O2 **生产默认仍关闭**。任何输入、生成器、布局或硬件变化均建立新身份，重新核验受影响部分。

首批固定最多 **5 次串行 EMU**，不扫形状/数据集/布局：

1. firstdot 高位负控：仅在已解码的第一条 VDOT、实际 rd=v0 处将参考结果 bit64 异或 1。要求目标 PC/word/rd、128 位差异和终止位置精确相符，低 32 位及 CSR 不变；其他崩溃、超时、错误目标不能算负控成功。
2. 同 BIN 切回原正常参考，完成全部功能、全宽结果/CSR、退休与 O2 原流检查，证明正常恢复。
3. 同硬件/配置/输入条件执行原 S1 控制镜像。
4. firstdot 与 S1 各重放一次，全部 24 个窗口 cycle/instret 与各自首个正常执行一致。

负控额外记录参考 ABI 的全部 1400 字节，要求异或差异恰好为 byte808/bit0，并再次读取参考模型确认其内部状态未改变；不只检查低32位或一条错误字符串。终止要求 exit1、单次精确高位不一致、唯一 ABORT，以及完整16组/32行提交环中的实际目标。固定版本把 `v0wen` 独立导出，诊断 `wen` 不含它，因此此目标打印 `wen=0`；只对四条精确计数器读指令接受 `(S)`，目标不能跳过。正常运行检查数学、全部向量高位、CSR、实际机器码退休、校准窗口和384次 O2 提交及排空。

当前加固生成器与旧探针的冻结版本不同。运行检出明确覆盖两份已认证的旧生成器以精确复算原镜像，其余运行检查器保留当前版本；覆盖清单纳入证据，不能称为当前干净源码重建。GEMV 的 RVV 每块处理16元素，8×32共16次 widening multiply/reduce；运行器只对此固定形状使用独立几何校验，要求实际退休与精确再生源计数同时等于16，不套用 dot8 微基准的32次规则。

两份首个正常执行合计 **32 个正式窗口**（每镜像四内核×4次，排除 first/warmup）；重放不增加正式样本。basic 留作诊断，主要选择对象为 reuse VDOT；与原 S1 reuse VDOT、两镜像中实际较快的 RVV 做完整 endtoend 配对。已有 8.25 周期余量仅作历史背景，不是新硬件收益。先通过精确负控/恢复及完整原流检查，再计算均值、离散度和相对周期；静态少 32/20 条指令不能算周期改善。

任何准入、负控、恢复或重放失败即停止，不改门槛；无正收益则保留稳定 S1/R5，不扩大矩阵。只有首轮正收益后才安排三数据集及其他形状的采用矩阵，不能用 dataset0 探针替代完整选择资格。

### v1 停止与 v2 显式接续

v1 首次预检因旧生成器身份不符停止，实际0次 EMU；隔离源闭包后只运行1次负控，实际触发正确的 v0 bit64 差异，但旧通用诊断解析器不识别计数器 `(S)` 和 v0 `wen=0`，故原状态为 FAILED，未启动正常运行。两个失败输出及原源码保持不变。

`r2-first-dot-8x32-runtime-v2` 使用上述严格解析器。可选 `--negative-parent` 只接受代码内固定 SHA 的这一个 v1 失败输出；重新校验全部输入、进程收据和原始负控日志，再导入其结果，原 FAILED 不改。新输出必须与父目录分离，预算为 **1次真实旧负控＋4次新正常执行＝5次**。不提供任意断点续跑、任意父输出或失败重试模式；后续失败仍立即停止。

运行参数为 `--output`、`--admission`、`--hardware-root`、`--hardware-pins`、`--input-contract`、`--source-base`，均绑定独立 LF 源闭包和认证输入。`audit_runtime.py --run RUN --output NEW_REPORT` 重新计算全部原日志及正式/重放样本，必须导入清单记录的原执行 `runtime.py`；审计器可使用单独的新源码快照。`FIRSTDOT_RUN=RUN python3 -m unittest discover -s team/optimizations/o2/r2-first-dot -p test_runtime.py -v` 对实际证据做拒错测试，不启动 EMU。缺真实夹具直接失败，不静默跳过。

若新审计器与原执行源码分开存放，直接运行新目录下的脚本会导入新 `runtime.py` 并被身份门禁拒绝。将 `EXEC_MODULE` 指向原执行的 `r2-first-dot` 目录、`NEW_AUDITOR` 指向新审计脚本，使用显式导入方式：

```bash
python3 -c 'import runpy,sys; sys.path.insert(0,sys.argv.pop(1)); runpy.run_path(sys.argv.pop(1),run_name="__main__")' \
  "$EXEC_MODULE" "$NEW_AUDITOR" --run "$RUN" --output "$NEW_REPORT"
```

本次实际启动命令和源码哈希保存在运行封存的 `final-raw-audit.json`；不覆盖原执行目录来迁就审计。

本次实际结果及本机恢复位置见[动态验收记录](../../../docs/latest-integration-20261023.md#firstdot-负控恢复与配对性能2026-10-24)；早期静态资格见同文的 GNU11/firstdot 准入节。
