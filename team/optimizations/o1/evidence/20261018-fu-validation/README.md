# O1 三模式 FU 本地验收记录（2026-10-18）

**真实 FU 验证通过，父级和全核验证待完成。** 本目录是工程证据，T16 正式报告继续后置。目标发布分支为 `cc77-builder/riscv:zjhwork`；发布操作的最终 SHA 回执另存本地，本文不把构建提交与后续文档提交混用。

从 `zjhwork2:75dce60e2c5a4d99c8c1193abf5f9946ea1704e4` 复用 O0 与 O1 候选。本次修复环境加载顺序及负控假通过问题；首轮真实编译另外暴露两处 `FuType.vdot` 缺少 `.U` 的类型错误，修复后重新执行全部三模式。正式被测源码为 **`db0408aa42afc13e3ff93e865f26a2d5bfb02c93`**，开始运行时工作树补丁为空。

## 实测结果

| 模式 | FUSED_INPUT / HANDOFF | 首次响应延迟 | 无反压最小接受间隔 | 结果 |
| --- | --- | ---: | ---: | --- |
| 基础版 | 0 / 0 | 3 拍 | 4 拍 | 通过 |
| T14 | 1 / 0 | 2 拍 | 3 拍 | 通过 |
| O1 | 1 / 1 | 2 拍 | 2 拍 | 通过 |

三模式均运行原有 22 组定向＋10,000 组随机数值数据，比较完整 128 位结果。基础版与 T14 使用未修改的原 FU 检查器；O1 使用同拍交接检查器，包含 0/1/2/7 拍反压、旧身份/写使能/异常/向量控制/调试标记绑定、48 个重定向组合、3 个复位时点及 10,000 拍随机控制。O1 算术流强制 10,021 次交接，96 条合法/非法交替流额外强制 95 次交接。三模式控制矩阵并非完全相同：旧检查器含 22 个具体非法值，候选使用 8 类代表值。

O1 总计接受 13,626、响应 13,212、取消 388、复位丢弃 26，事务守恒；同拍交接 12,237 次，输出等待 26,659 拍。数字见 [候选原始结果](fu-02/result.log)。基础版 [结果](fu-02/legacy-0/results.log) 与 T14 [结果](fu-02/legacy-1/results.log) 分别为 71,258 和 61,108 个测试周期；这些测试总周期不作为应用性能比较。

四种 O1 负控（身份、写使能、结果高位、取消泄漏）均以退出码 1 和各自准确失败原因检出。它们是 **C++ 读回观测破坏**，不是 RTL 修改或全核 DiffTest 注入。漏检使用独立 `O1_FU_FAULT_ESCAPED` / exit 3，不再算作检出。基础版/T14 原有两种负控及 VLEN=256 拒绝检查也通过。

## 命令、版本与来源

完整环境与固定依赖下，从仓库根目录运行，输出目录须不存在：

```bash
python3 -B -m unittest discover -s team/optimizations/o0 -p 'test_*.py' -v
python3 -B -m unittest discover -s team/optimizations/o1 -p 'test_*.py' -v
bash team/optimizations/o1/check-handoff.sh /absolute/new/fu-output
```

O0 113 项主机检查在 `c52dc65` 通过，后续仅修复 ExeUnit 两处类型转换，O0 文件未变；O1 26 项在最终被测源码通过。主机测试不替代 RTL 仿真。

- [统一机器回执](verification.json)：命令、源码 SHA、模式、覆盖、明确未完成项。
- [实际调用及退出码](fu-02-invocation.json)、[完整 runner 日志](fu-02/runner.log)、[结束状态](fu-02/runner.status)。各模式目录保存 elaboration、Verilator 编译、结果和负控原始日志。
- [生成 RTL、可执行文件、向量摘要](artifacts.json)：生成物在本机保留，构建目录和二进制不进入日常 Git 提交。
- [运行前源码摘要](fu-02/source.sha256)、[运行后核对](fu-02/source-after.log)、[含两旧模式的追加摘要核对](source-manifests-recheck.json)。
- [固定依赖](dependencies.json)、[运行后全部 126 个嵌套 Git 目录版本及清洁性核对](dependencies-after.json)。依赖从本机已有仓库按 gitlink 提交克隆；未复制源工作树改动。普通 `git submodule status` 的初始化标记不作为本次版本依据。
- [O0/O1 独立主机复核](o0-host-01/receipt.json)、[类型修复后 O1 复核](o1-host-after-compile-fix/receipt.json)。旧 O0 16 个证据文件与 Git 原字节一致。
- [首轮失败调用](fu-01-invocation.json)、[失败编译日志](fu-01/legacy-0/elaboration.log)：源 `c52dc65`，退出码 1，未生成 RTL；不能算通过。

实际使用 Java/GraalVM 21.0.12、Mill 0.12.3、firtool 1.62.1、Verilator 5.052、Python 3.10.12。三个 Verilator 构建日志实际调用 `clang++` 19.1.7，并非仅由工具预检推断。`BUILD_JOBS=2`、`JAVA_OPTS=-Xmx12G -Xss16m`；生成顶层 `VDotFuTestTop`，MinimalConfig 单核参数、VLEN=128、ROB=48，Verilator assertions 启用。

## 后续边界

本次编译了香山 Scala，但生成顶层仅实例化真实 VDot FU；**未生成或运行真实 ExeUnit/VFEX4 父级，未运行新 EMU/全核 DiffTest 或统一性能基准**。默认 O1 开关仍为 0；旧 T12/T13 观察器在 O1 模式下仍拒绝启用。原 O0 的 738 次 busy 匹配复用为诊断依据，没有新增 O0 性能矩阵或全核加速比。

下一步为真实 VFEX4（含向量整数/浮点除法）父级联调，验证 busy、分流、时钟和 ready 反馈，再补 O1 观察器、全核功能/控制回归及同镜像性能 A/B。FU 接受间隔从 3 降到 2 不能直接宣称应用加速 1.5×，也没有 Fmax/PPA 或人工 ACK 结论。
