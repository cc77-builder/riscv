# T05-E 异常 workload

本程序已实现准备、独立陷阱入口、现场记录、完整向量读回、严格判定及汇总。已在 QEMU 通过 harness 自测，已编译固定 nexus-am 的香山 ELF/bin；实际 vdot 的 NEMU/RTL 路径仍待 T08/T11 验收。

程序关联 [异常方案](../../spec/exception-tests.md)、[T05 数据](../../tests/README.md) 与 [本次评审](../../docs/t05-t05e-review.md)。默认 `full` 模式包括 80 个算术/合法状态用例和 35 个异常子例，先完成处理程序自测，再运行扩展用例。任一合法对照失败立即停止扩展验收；不可达初态算覆盖缺口，整体非零退出。

Linux/WSL 命令从仓库根执行；使用安装了 RISC-V GCC/binutils 和 QEMU system 的环境：

```bash
bash team/scripts/vdot-tests.sh host
bash team/scripts/vdot-tests.sh virt-selftest
bash team/scripts/vdot-tests.sh virt-full-negative
```

`virt-selftest` 不使用 vdot：H00 以 vadd 验证合法执行/观察，H01～H04 用 ebreak 验证 cause=3、PC、VS Off、vstart7、vill/vl0 的现场保存；两项负控分别填错 expected PC 和目的高字节期望。自测只输出 `extension_pass=false`。`virt-full-negative` 在未扩展 QEMU 上确认合法 vdot 被拒绝、完整模式退出 3；这是失败检出证据，不是 vdot 功能通过。

香山目标要求 [versions.env](../../versions.env) 的 nexus-am 提交；库应检出在 Linux 文件系统中，以保留符号链接和源码换行。构建脚本校验 SHA 与已跟踪文件；不调用 AM 的 `__am_init_cte64`，程序沿标准 boot/start → trm → main 的 M 模式启动路径运行。

```bash
export AM_HOME=/你的固定nexus-am目录
bash team/scripts/vdot-tests.sh build-xs selftest
bash team/scripts/vdot-tests.sh build-xs full

# NEMU standalone 可执行文件与 DiffTest 共享库是两个不同构建产物。
export NEMU_HOME=/你的NEMU源码目录
export VDOT_NEMU_BIN=/你的standalone解释器路径
bash team/scripts/vdot-tests.sh run-nemu selftest
# 扩展实现后才期望 full 通过：
bash team/scripts/vdot-tests.sh run-nemu full

export VDOT_EMU_BIN=/你的香山build/emu
export VDOT_NEMU_REF=/你的配套参考共享库
bash team/scripts/vdot-tests.sh run-rtl full
```

产物默认放在 `team/out/t05e-<action>-<mode>/`，可设置 `TEAM_EVIDENCE_DIR`。run-nemu/run-rtl 默认取同模式 build-xs 产物；`VDOT_IMAGE` 可指定另一份已带构建校验记录的镜像。运行前校验输入及镜像摘要；保存实际 team/NEMU SHA、工作区、输入/源码/二进制摘要、编译器与运行退出码。RTL 运行还必须满足真实 DiffTest 和 GOOD TRAP 标记。

`run-rtl` 使用既有 boot-flash 模板、128MB、5,000,000 周期上限；普通运行不生成波形。可用 `VDOT_MAX_CYCLES`、`VDOT_RUN_TIMEOUT` 调整上限，调整值与运行命令一起归档。脚本不构建 NEMU 或 RTL；没有对应产物时不能声称通过。

实现和观察边界：

- [harness.S](harness.S) 在一个汇编调用内完成所有向量准备、执行和读回，中间不调用 C。独立 512 字节 trap 栈，以 mscratch 切换并保存 GPR；屏蔽中断，返回时恢复 mtvec/mscratch/mie/mstatus。
- 每个机器字有固定 fault/resume 标签；错误 PC/cause、未 armed 陷阱走错误记录和 abort 路径，不泛用 mepc+=4。嵌套陷阱设置错误并终止，外部运行有超时。
- 非零 vstart 在加载及 vset 完成后最后设置。VS Off 在 pre-CSR 捕获后最后关闭，fault 前只读取 mstatus；trap 先保存 raw mstatus，启用 VS 后才读取向量 CSR，phase=2 表示恢复访问后的读取。
- 先捕获 post-CSR，再清 vstart 并设 e8/m1/vl16 读取全部 32 个 128 位寄存器；两个输入和全部非目的均参与预期比较。该观察操作会改变配置，不能拿观察后的 CSR 当现场。
- [judge.c](judge.c) 将不可达状态、协议错误、错因/错 PC、CSR 变化、完整寄存器变化、内存哨兵变化分开判定；[check-vdot-run.py](../../scripts/check-vdot-run.py) 复核 ID、数量、模式、现场与独立数据。只有实际全部比较通过才标记 all32_checked=1。

`mtval` 原样记录，不强行规定所有非法指令都返回非零机器字；实际 RTL/NEMU 差异应由 DiffTest 暴露，不能屏蔽。vlenb 在入口检查为 16。异常子例保持 opcode/长度，静态未冲突的 X07/X08 仍需扩展接入后重新译码检查；完整跑通不替代取消/配置依赖压力测试或 T11 故障注入。
