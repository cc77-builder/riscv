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
python3 -m unittest discover -s team/optimizations/o2/r2-first-dot -p 'test_*.py' -v
```

归档位于其他只读位置时，准入用 `--archive`，测试用环境变量 `FIRSTDOT_ARCHIVE`。输出保留源身份、原始输入及检查结果；失败单独保存，不能覆盖或续写旧输出。入口不支持 Windows CRLF 源码的精确再生。

## 下一阶段运行合同（待实现/实测）

本次没有运行器或已运行的负控。先绑定本机已核验的 `bc9e5ae4… / e66a8900…` 硬件、正常 NEMU、flash、辅助数据及完整输入合同；不借用上游 `34bae/ff840` 的运行资格。任何输入、生成器、布局或硬件变化均建立新身份，重新核验受影响部分。O1/O2 生产默认仍关闭。

首批固定最多 **5 次串行 EMU**，不扫形状/数据集/布局：

1. firstdot 高位负控：仅在已解码的第一条 VDOT、实际 rd=v0 处将参考结果 bit64 异或 1。要求目标 PC/word/rd、128 位差异和终止位置精确相符，低 32 位及 CSR 不变；其他崩溃、超时、错误目标不能算负控成功。
2. 同 BIN 切回原正常参考，完成全部功能、全宽结果/CSR、退休与 O2 原流检查，证明正常恢复。
3. 同硬件/配置/输入条件执行原 S1 控制镜像。
4. firstdot 与 S1 各重放一次，全部 24 个窗口 cycle/instret 与各自首个正常执行一致。

两份首个正常执行合计 **32 个正式窗口**（每镜像四内核×4次，排除 first/warmup）；重放不增加正式样本。basic 留作诊断，主要选择对象为 reuse VDOT；与原 S1 reuse VDOT、两镜像中实际较快的 RVV 做完整 endtoend 配对。已有 8.25 周期余量仅作历史背景，不是新硬件收益。先通过精确负控/恢复及完整原流检查，再计算均值、离散度和相对周期；静态少 32/20 条指令不能算周期改善。

任何准入、负控、恢复或重放失败即停止，不改门槛；无正收益则保留稳定 S1/R5，不扩大矩阵。只有首轮正收益后才安排三数据集及其他形状的采用矩阵，不能用 dataset0 探针替代完整选择资格。

本次实际结果及本机恢复位置见[本地整合记录](../../../docs/latest-integration-20261023.md#gnu11-r5-闭合与-firstdot-准入2026-10-24)。
