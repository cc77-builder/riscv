> **历史记录：** 本文描述原 James 候选及当时配置。2026-10-15 已统一为 VFEX4 / NEMU 1.1.0；当前入口见 [整合报告](james-integration-20261015.md)，历史日志不计作新实现的运行结果。

# T08 NEMU 实现与验收

日期：2026-10-12（北京时间）。工作分支 `James_Hotten`；团队基准 `4d04e6b9f2696301cd0dc0237b59b97540b2e848`。本轮代码、补丁和证据随该分支提交交付；尚未推送。

**NEMU 候选 vdot 已实现，standalone 全部 115 个必需用例及 1,000 个固定随机输入通过；新检出应用补丁后复验通过。参考共享库构建、链接和加载检查通过。T08 本地实现与验收完成，A/B/C 人工复核及实际 RTL/NEMU 全核差分仍待后续任务。**

## 1. 实现与交付

采用 [固定基线加补丁](../patches/nemu/README.md)，明确 `a48a11f... + 补丁1.0.0 + CUSTOM_VDOT=y` 才是本次扩展版本。普通 versions.env 的 NEMU_REV 保留原基线；[manifest](../patches/nemu/manifest.json) 锁住补丁和实际源码，配套构建另记录 config/binary 摘要。

源码改动为 Kconfig、isa-all-instr.h、主 decode.c、rvv/exec.h 和新增 rvv/vdot.h。与普通 OP-V 分派分离，只读取向量寄存器、写一个完整向量目的，沿用特权及异常框架。内部 R 字段解析不意味着整数目的写回；helper 直接访问 cpu.vr。

helper 在任何目的写入和 VS Dirty 前检查状态；在写回前缓存两份参与源，避免别名覆盖。显式 signed int8 到 int32 转换和八项求和无需饱和/舍入；`(uint32_t)sum` 零扩展进低 64 位，高 64 位写零，实现高 96 位清零。vl/vtype/vstart/vxrm/vxsat/vcsr 不写回。

## 2. 实际验收

| 检查 | 结果 |
| --- | --- |
| NEMU 中运行 harness selftest | H00～H04、两项负控通过，退出 0；证明入口/恢复/观察在目标参考环境成立 |
| 原始 full 集合 | 80 合法/算术 + 35 异常，共 115/115 通过，failed=0，unreachable=0，退出 0 |
| 扩展随机集合 | 48 定向 + 1,000 随机 + 35 异常，共 1,083/1,083 通过；随机期望来自独立 T05 模型 |
| 补丁复现 | 从固定提交新检出、应用交付补丁、独立构建 standalone；115/115 再次通过 |
| 原 hello/vadd 回归 | 3 组 / 24 lane，通过且 GOOD TRAP；使用示例 identity，不能据此关闭 T04 的真实团队标识验收 |
| 参考共享库 | 独立参考配置构建通过，ldd -r 无未解析符号；实际动态加载及四个主要 difftest 接口检查通过 |
| 相邻编码复核 | 应用补丁后 X07/X08 的 10 个字仍不匹配当前 NEMU 主表；717 个香山命名表项静态检查无冲突 |
| Python 回归 | 14 个测试方法通过，包括新增加的随机 workload 规模/manifest 验证 |

原 full 约 14.7 秒；1,083 项约 133.3 秒，这是主机模拟运行耗时，只用于安排测试，不代表处理器性能。随机批次设置 300 秒超时。QEMU 与 NEMU 对 ebreak 的 mtval 值不同，程序原样记录；本轮没有做两者逐状态等价断言，后续 RTL/NEMU 的 mtval 差异仍须按真实平台处理。

实际日志、退出码、构建配置与摘要见 [T08 证据](../evidence/t08-nemu-20261012/README.md)。本次使用 WSL Ubuntu-HDL；NEMU 开发与两种构建放在 Linux 缓存目录，主仓库只交付补丁、脚本、文档及证据。

## 3. 复现与扩大随机覆盖

先按补丁 README 构建，再运行普通 selftest/full。扩展随机批次需使用独立数据和镜像目录，确保构建与运行的变量一致：

```bash
export VDOT_DATA="$PWD/team/out/t08-random-data"
export VDOT_RANDOM_COUNT=1000
export VDOT_SMOKE_RANDOM_COUNT=1000
export AM_HOME=/你的固定nexus-am目录
TEAM_EVIDENCE_DIR="$PWD/team/out/t08-random-build" bash team/scripts/vdot-tests.sh build-xs full
export VDOT_IMAGE="$PWD/team/out/t08-random-build/vdot-exceptions.bin"
export NEMU_HOME="$HOME/riscv-lab/vdot-nemu/standalone"
export VDOT_NEMU_BIN="$NEMU_HOME/build/riscv64-nemu-interpreter"
export VDOT_RUN_TIMEOUT=300s
TEAM_EVIDENCE_DIR="$PWD/team/out/t08-random-run" bash team/scripts/vdot-tests.sh run-nemu full
```

生成器升为 `1.1.0`，模型仍是 `1.0.0`；默认 32 个随机 smoke 不变，已入库定向数据及 ISA 行为不变。VDOT_DATA/随机规模可配置；完整数据、头文件和 manifest 始终来自同一次配置，运行前继续校验输入与镜像摘要。

## 4. 剩余事项

- A/B/C 人工复核候选语义、补丁和测试；非作者在自己环境复现。此次“新检出复现”由同一协助工具执行，不代替非作者验收。
- A 按 T06/T07/T10 接入 RTL 的实际 VL 依赖、配置快照、v0/全宽写回、异常完成与取消；本轮未修改或仿真香山 RTL。
- C 在 T11/T12 用本次 reference 产物运行真实 DiffTest，确认完整向量/CSR 比较与故障检出；共享库加载通过不等于全核差分通过。
- B/C 推进 T09 baseline，并补充 scratch、CSR 恢复和性能测量合同。T03 仍待成员冻结与歧义处理记录。
