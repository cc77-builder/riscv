# T07-B FU 包装层验证记录

**结果：真实 VDot FU 的 6 类场景全部通过，共 71,258 个周期。** Verilator 开启 RTL 断言；输入握手、完整结果、身份、异常、反压稳定性、取消和复位均按周期检查。

| 项目 | 记录 |
| --- | --- |
| 日期/时区 | 2026-10-13，Asia/Shanghai（UTC+08:00） |
| 运行时间 | 12:05:00 至 12:05:22 |
| 分支/测试前提交 | `zjhwork` / `5227c030fdae9b6087fd995a00a3535b15f6aefc` |
| 测试工作树 | 包含本次尚未提交的 FU、配置与测试改动；具体内容由 [source.sha256](source.sha256) 标识 |
| 合同与输入 | `vdot-s8x8-r32-v0.1`；T05 的 22 定向、10,000 随机 JSONL 及 manifest 均未修改 |
| DUT | `VDot` 继承真实 `VecNonPipedFuncUnit`，使用真实 `RobPtr.needFlush`；测试顶层为 `VDotFuTestTop` |
| 配置 | MinimalConfig(1) core 参数，VLEN=128，ROB=48；仅实例化 FU |
| 工具 | GraalVM JDK 21.0.12、Mill 0.12.3、Scala 2.13.15、Chisel/插件 6.6.0、firtool 1.62.1、Verilator 5.052、clang++ 19.1.7、Python 3.10.12 |
| 退出状态 | `exit_code=0`，见 [check.status](check.status) |

实际命令：

```bash
cd /home/riscv/riscv-lab/xs-env/XiangShan
VDOT_OUT_DIR="$PWD/team/out/vdot-fu/20261013-t07b-run1" \
  bash team/scripts/check-vdot-fu.sh
```

主要结果：

```text
VDOT_FU_GROUP_PASS arithmetic=10022 stalls=0,1,2,7 continuous-valid identity-snapshot latency-II
VDOT_FU_GROUP_PASS illegal=22 policy-vxrm=16 renamed-VL exception-no-write
VDOT_FU_GROUP_PASS idle-flush input-not-accepted recovery
VDOT_FU_GROUP_PASS redirect-matrix=64 MUL-REDUCE-RESP-stalled older-self-wrap handshake-priority
VDOT_FU_GROUP_PASS reset-phases=4 no-ghost-response recovery
VDOT_FU_GROUP_PASS random-control cycles=5000 seed=0x20261013 conservation-watchdog
VDOT_FU_PASS groups=6 cycles=71258 accepted=11245 responded=10960 killed=271 reset_dropped=14 illegal_responses=90 stall_cycles=25700
FU_FAULT_DETECTION_PASS fault=identity expected_exit=1
FU_FAULT_DETECTION_PASS fault=cancel-leak expected_exit=1
VLEN_GUARD_PASS unsupported=256
VDOT_FU_CHECK_PASS (real FU RTL and RobPtr; no EXU/CPU/NEMU integration validation)
```

`accepted = responded + killed + reset_dropped`，最终无遗留事务。定向异常 22 条与压力测试异常合计 90 次响应；取消和 reset 清除的事务不应产生后续响应。状态计数口径见 [FU 测试说明](../../rtl/vdot/FU.md)。

## 归档文件

| 文件 | 内容 |
| --- | --- |
| [check.log](check.log) / [check.status](check.status) | 实际命令、工具版本、输入摘要、每步状态和退出码 |
| [results.log](results.log) | 全部 6 类场景结果及事务总计 |
| [elaboration.log](elaboration.log) | 真实 XiangShan 模块依赖下的 FU RTL 发射记录 |
| [verilator-build.log](verilator-build.log) | C++ 编译/链接命令及构建报告；脚本命令包含 `--assert` |
| [inject-identity.log](inject-identity.log) | 测试器读回 pdest 被翻转后，身份比较失败并返回 1 |
| [inject-cancel-leak.log](inject-cancel-leak.log) | 取消时测试器伪造有效响应，控制比较失败并返回 1 |
| [invalid-vlen.log](invalid-vlen.log) | VLEN=256 的生成请求因 `VDot requires VLEN=128` 被明确拒绝 |
| [source.sha256](source.sha256) / [rtl.sha256](rtl.sha256) | 测试所用源码/输入及生成 SV 的摘要 |
| [dependencies.txt](dependencies.txt) | 归档时 `git submodule status` 的直接依赖版本，与本次运行使用的工作树一致 |

从仓库根运行 `sha256sum -c team/evidence/rtl-fu-20261013/source.sha256` 可验证当前文件与记录对应；后续代码改变后应保存新证据，历史摘要不应被改成新值。生成 RTL、二进制、TSV 和构建目录保留在 `team/out/`，不进入日常提交。

## 结论边界

本次证明 FU 在已执行场景中的接口行为符合本队草案；既有算术通过记录在 [T07-A](../rtl-datapath-20261012/README.md)。无反压的结果 valid 在接受后 E2 沿后出现，E3 最早输出握手、E4 最早下一次输入；这不是全核指令延迟或性能提升结论。

没有实现或运行 vdot 译码、VFEX4 接入、全核写回/ROB 异常、NEMU 扩展或 DiffTest。VS Off、真实 CSR 更新、v0 物理路径、寄存器别名、EXU 共享/时钟门控属于后续集成。读回故障注入证明测试器会拒绝所注入错误，不等于 RTL 形式证明或全核比较路径验证。

本轮自检不代替团队其他两名成员的人工接口评审；工作仅提交 `zjhwork`。
