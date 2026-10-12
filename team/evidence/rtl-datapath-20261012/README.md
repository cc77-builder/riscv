# T07-A 点积组合算术 RTL 验证记录

**结论：22 组定向 + 10,000 组随机，共 10,022 组完整 128 位结果全部匹配。** 被测对象是生产 Chisel 算术源码生成的 SystemVerilog，经 Verilator 编译运行；没有用 Python 函数替代 DUT。

| 项目 | 本次记录 |
| --- | --- |
| 合同 | `vdot-s8x8-r32-v0.1`；没有修改模型、manifest 或测试向量 |
| 任务/分支 | T07-A，`zjhwork` |
| 执行时间 | 2026-10-12 23:42:15 至 23:42:28，UTC+08:00 |
| 执行前提交 | `ec7c2a4cc762fc6f616a9ebdb5ec0e37ea7187bf`，测试时包含本轮尚未提交的实现 |
| 被测文件标识 | [source.sha256](source.sha256) 记录实际运行的生产源码、构建定义、测试器、脚本和输入摘要；以摘要识别未提交工作树 |
| DUT | `VDotDatapath`，连接 `VDotProducts` 和 `VDotReduce`，无时钟的组合逻辑 |
| 工具 | GraalVM JDK 21.0.12；Mill 0.12.3；Scala 2.13.15；Chisel/插件 6.6.0；firtool 1.62.1；Verilator 5.052；clang++ 19.1.7；Python 3.10.12 |
| 退出状态 | `exit_code=0`，见 [check.status](check.status) |

命令从完整 WSL 香山仓库运行：

```bash
cd /home/riscv/riscv-lab/xs-env/XiangShan
VDOT_OUT_DIR="$PWD/team/out/vdot-datapath/20261012-t07a-final" \
  bash team/scripts/check-vdot-datapath.sh
```

关键结果：

```text
VECTOR_CHECK_PASS suite=directed count=22
VECTOR_CHECK_PASS suite=random count=10000
VDOT_DATAPATH_SUITE_PASS suite=directed count=22
VDOT_DATAPATH_SUITE_PASS suite=random count=10000
VDOT_DATAPATH_PASS directed=22 random=10000 total=10022
FAULT_DETECTION_PASS bit=0 expected_exit=1
FAULT_DETECTION_PASS bit=127 expected_exit=1
VDOT_DATAPATH_CHECK_PASS (combinational RTL only; no FU protocol/CPU/NEMU validation)
```

上面 VECTOR 行省略了摘要字段，原始完整输出保存在 [check.log](check.log)。两个故障自检在 D00 的 RTL 读回结果上分别翻转 bit 0、bit 127，均产生 `VDOT_DATAPATH_MISMATCH` 且返回 1；外层脚本把这种预期的拒错判为通过。它们不修改 RTL 或黄金数据，不计入 10,022 组正常算术通过数量。

## 归档内容

| 文件 | 用途 |
| --- | --- |
| [check.log](check.log) | 版本、实际命令、输入摘要、全部步骤和最终状态标记 |
| [results.log](results.log) | 正常比较结果计数，失败时测试器会输出完整 128 位源和结果 |
| [inject-0.log](inject-0.log)、[inject-127.log](inject-127.log) | 低位和高位读回错误被拒绝的证据 |
| [verilator-build.log](verilator-build.log) | 实际 C++ 编译/链接命令和 Verilator 构建报告 |
| [source.sha256](source.sha256) | 构建/算术/测试/输入文件的准确摘要 |
| [rtl.sha256](rtl.sha256) | 生成的 `VDotDatapath.sv` 摘要，生成文件本身保留在忽略的输出目录 |
| [check.status](check.status) | 退出码和结束时间 |

从仓库根可检查归档摘要所对应的源码是否仍然一致：

```bash
sha256sum -c team/evidence/rtl-datapath-20261012/source.sha256
```

后续若修改任何被记录的源码，这个历史检查将合理地失败；应重新验证并归档新记录，不覆盖原始期望数据来消除差异。

## 实际覆盖与限制

- 现有定向包含 `-130048/131072` 端点、负数低 32 位补码、单 lane 和源高半部干扰；所有用例比较四个 32 位字，包含高 96 位。
- 输入校验核对合同、schema、模型/生成器源码摘要、两个 JSONL 摘要以及 22/10,000 实际数量；本次数据未重新生成。
- 单独 Mill 目标只编译生产算术模块与发射入口，生成 RTL 中可见 16→17→18→19 位扩位和最后的 96 位补零。
- 故障注入只证明本地 RTL 读回比较器能够拒绝所注入错误，不代表全核 DiffTest、完整故障覆盖率或形式证明。
- 未实现/验证 FU ready/valid、反压、取消、ROB/目的身份、配置异常、寄存器重命名、VFEX4 接入及 NEMU。未测面积、频率、CPU 周期、吞吐或性能加速比。

下一步按 [RTL 接口设计](../../spec/rtl-interface.md) 完成 T07-B 包装层。复现和模块说明见 [team/rtl/vdot](../../rtl/vdot/README.md)。
