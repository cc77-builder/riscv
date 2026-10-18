# O1 运行日志独立门禁

`runtime_gate.py` 修复首轮全核驱动的 ANSI 颜色边界问题：真实终止行中的颜色代码结束于字母 `m`，旧 `\bABORT\b` 不一定匹配。旧门禁会接受额外彩色 ABORT，又会拒绝去色后的同一预期负控日志。原始回执和反例保留；全核活动任务使用的 `fullcore/` 文件暂不改动。

新门禁先去除完整 ANSI CSI 控制码，统一解析视图的换行；未知或截断的转义，以及其余 C0/C1 控制字符（保留换行和制表符）拒绝。正常路径出现任何 ABORT、差分错误、断言或其它已知失败标记均拒绝。预期负控必须 exit 1，并同时满足唯一完整 bit100 注入记录、唯一匹配的向量高 64 位差分、注入与差分的 PC/目的寄存器相同、两值只相差高 64 位中的 bit36，以及紧接该差分的唯一 `Core 0: ABORT at pc = ...` 终止行。额外彩色/无色 ABORT、重复注入/差分、错误 PC/位差、GOOD TRAP 和无关失败均拒绝。

## 两个 PC 的语义

差分故障定位使用注入 PC 与 mismatch PC。ABORT 行单独记录 `abort_event_pc`，不强求与故障 PC 相同，也不硬编码此次值。

- [emu.cpp](../../../../difftest/src/test/csrc/verilator/emu.cpp) 的 `display_trapinfo()` 从 `get_trap_event()->pc` 读取终止打印字段（本轮源码 1003–1012 行）。
- [difftest.h](../../../../difftest/src/test/csrc/difftest/difftest.h) 的 `get_trap_event()` 返回 `dut->trap`。
- [Rob.scala](../../../../src/main/scala/xiangshan/backend/rob/Rob.scala) 的 `DiffTrapEvent.pc` 来自提交的 `isXSTrap` 对应 `trapVec`/`PriorityMux`；普通差分 `STATE_ABORT` 没有保证该字段等于错误提交 PC。`refproxy.cpp` 的 mismatch 输出使用 `dut->commit[0].pc`。

本次真实日志的注入/差分 PC 是 `0x80001bdc`，ABORT event PC 是 `0x800016b0`；这种差异按上述字段语义处理，不据此推断 ABORT 字段一定陈旧或是另一个故障。

## 证据与调用边界

`run.log` 是 `stderr.log + stdout.log` 的派生文本。注入位于 stderr，差分与紧邻 ABORT 位于 stdout；拼接后的位置不能证明跨流时间顺序。门禁不要求注入行在派生文本中的时间先后；绑定依据是唯一标记、PC、寄存器与确切位差。同 stdout 的 mismatch→ABORT 顺序可核验。独立源码审计保存在 `runs/o1-negative-abort-source-review-01`，包含实际字段来源和原始行号。

原始文件摘要由 raw bytes SHA256 绑定。`analyze.input_sha256` 是调用者传入 UTF-8 文本的摘要；`Path.read_text()` 与保留 CRLF 的直接 decode 可能不同。此次离线复核分别记录原始字节与规范化解析视图，绝不改原始日志。

```bash
python3 -B -m unittest discover -s team/optimizations/o1/audit -p test_runtime_gate.py -v
python3 -B team/optimizations/o1/audit/runtime_gate.py \
  --log /absolute/completed/negative-vdot/run.log --mode negative --exit-code 1 \
  --output /absolute/new/negative-gate-result.json
```

这些是主机门禁检查与原始日志离线复核，不是新 EMU 运行。`NORMAL_FAILURE_MARKERS_CLEAR` 仅表示未发现已知失败标记，仍需原有工作负载、DiffTest、身份/覆盖与运行退出码验收。首轮驱动集成补丁暂存外部，等待全部 12 项仿真结束后应用、测试并重审原始日志。
