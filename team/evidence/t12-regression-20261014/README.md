# T12 完整回归证据（2026-10-14）

最终 11 项实际运行全部满足预期，`T12_FULLCORE_SUITE_PASS`，驱动退出码 0；完整结论与边界见 [T12 报告](../../docs/t12-regression.md)。本轮位于独立本地分支 `local/t12-regression`，未推送共享远端，人工复核待办。

控制程序提交 2,157 条 vdot；93 条接收后取消、2 条 FU 内取消、20 次写回反压，ROB/FTQ 绕回 214/315 次。原 117 唯一用例经 8 分片完整通过；bit100 负控被准确拒绝，相同镜像正常参考库对照通过。主机 108 项单测和分层组件结果分别保存，不与全核结论混用。

## 目录

- `suite/`：11 项原始 `stdout.log.gz`、`stderr.log.gz`，真实退出码、命令/输入摘要、运行回执及检查结果。`run.log.gz` 是逐字节 stderr + stdout 的派生文件，`uart.log.gz` 是移除观察记录后的派生视图；后者还含仿真器日志，并非纯 UART 原始流。
- `suite/hardware-pins.json.gz`、`reference-provenance.json.gz`、`functional-*-build.json.gz`：实际硬件、参考库、各镜像来源。`build/` 另存构建日志、版本、最终软件 SHA 和完整启动参数。
- `control/`：压力序列与独立检查点、manifest、输入摘要和反汇编；`matrix/`：原 T11 各分片数据及构建来源。
- `components/`：数学模型、独立组合/FU/解码和主机检查记录，保留各自范围。
- `historical/`、`historical-attempts.json`：失败与中断历史，明确排除；本机原件保留在 `/home/riscv/riscv-lab/t12-regression-20261013`。
- `clock-and-streams.md`：门控时钟对齐及分开采集两条输出流的原因。
- `archive-manifest.json`：存储字节和解压内容 SHA-256；压缩仅改变容器，未删改原始流。

## 离线复核

在包含本证据与原 T11 母数据的完整仓库中执行（Python 3.10+，无需重新仿真）：

```bash
python3 -B team/scripts/check-t12-archive.py team/evidence/t12-regression-20261014 \
  --expected-source 117ecbf40e107872e046311f556cc4fdf3f733d7 \
  --expected-emu e879356c4f3ad027a708de3adbabb7285ab6e36196426854040460d1e394b4de \
  --expected-reference efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4 \
  --expected-flash a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994
```

应输出 `T12_ARCHIVE_RECHECK_PASS`。这是对已保存原始日志和回执的重新计算，不是新的 DUT 执行、签名或人工评审。原负控真实 exit1 是预期拒错；其正常对照真实 exit0。失败历史不能计入本轮通过数，性能/PPA/虚拟化不能据此宣称通过。
