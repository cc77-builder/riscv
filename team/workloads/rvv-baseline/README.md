# T09 普通 RVV baseline

本目录复用 James 固定提交 `a978b3b8fe731dd9422a41f80d9d53e40c775656`。以下平台 PASS 是来源的历史结果，本轮仅通过主机测试，目标平台/CPU 周期未运行；见 [T10/T11 本轮记录](../../docs/t10-t11-20261013.md)。

候选合同 `vdot-s8x8-r32-v0.1`，序列 `rvv-vdot-s8x8-r32-v1`。使用 vwmul.vv/vwredsum.vs 精确完成低八项 signed int8 点积，显式清零目的高 96 位，恢复实际入口 vl/vtype。源码不执行 custom-0 指令；cases 中的候选 word 只用作寄存器组合索引和日志标识。

入口、scratch 和测量边界见 [measurement.md](https://github.com/cc77-builder/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/team/spec/measurement.md)。生成器选择偶数对齐 product 对和两份 scalar scratch，排除操作数及 v0；实际完整目的、非 scratch 向量寄存器和六项 CSR 由复用的 T05-E harness/判定器检查。初始化/读回的配置变化位于被测区间之外。

WSL/Linux 在团队仓库根执行：

```bash
# 默认 304 定向（含256扩展）+1000随机，timeout默认300s
bash team/scripts/baseline-tests.sh virt

export AM_HOME=/你的固定nexus-am目录
TEAM_EVIDENCE_DIR="$PWD/team/out/t09-xs-build" bash team/scripts/baseline-tests.sh build-xs
export BASELINE_IMAGE="$PWD/team/out/t09-xs-build/rvv-baseline.bin"
export NEMU_HOME="$HOME/riscv-lab/vdot-nemu/standalone"
export VDOT_NEMU_BIN="$NEMU_HOME/build/riscv64-nemu-interpreter"
TEAM_EVIDENCE_DIR="$PWD/team/out/t09-nemu" bash team/scripts/baseline-tests.sh run-nemu
```

BASELINE_DATA 默认 team/out/t09-data；BASELINE_RANDOM_COUNT/BASELINE_SMOKE_RANDOM_COUNT 默认都是 1000。生成、构建和运行需使用同一数据目录和规模；运行 NEMU 时不重新生成数据，而是强制校验构建来源中的源码/生成器/模型、arch/mode、固定AM、镜像和输入摘要。小规模检查可另设独立 BASELINE_DATA 并将两个计数设为 32；不要在另一运行途中覆盖数据。

QEMU virt 只需现有标准 RVV；NEMU 需 standalone 产物，正式验收入口使用schema 2来源已绑定的T08候选解释器；baseline指令序列本身仅使用标准RVV。任意原始NEMU产物不能冒充候选来源验收。nexus-am 必须是 versions.env 中的固定提交且无已跟踪改动。build-xs 是香山启动目标编译，run-nemu 是参考解释器执行，不等于香山 RTL 已运行。

当前脚本在两个平台各1304/1304通过，实际1147个操作数组合、18种scratch布局、全部32个寄存器及96种政策/CSR/VS交叉。高位、非 scratch 和 CSR 破坏均被负控检出，scratch 变化按声明被允许；生成器另穷举 32768 种编号组合的分组/非重叠约束。历史1048项见 [T09 记录](https://github.com/cc77-builder/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/team/docs/t09-baseline.md)；当前来源门禁、布局/状态覆盖和复审见 [审查修复](https://github.com/cc77-builder/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/team/docs/audit-fixes.md)。
