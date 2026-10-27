# R3 DIV取消关钟修复：全核构建与NEMU差分结果

本轮完成新EMU构建、14项实际全核作业和严格原文复算。源码为O2＋H1＋DIV取消关钟修复。

本地硬件提交：0f12df675378556670afd0dd2153f47fcb330610；EMU SHA256：2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。

- 13项正常差分通过，1项bit100负控被DiffTest按预期拒绝，随后同镜像正常库恢复通过。
- 117唯一功能/异常case，8分片执行124次；正常提交5378条vdot。
- hello/vadd、控制、dense及两项补充诊断通过；110项主机测试通过。
- 严格复算核对429份硬件源码和21236份依赖；完整128位结果和O2控制检查保持。

| O2覆盖 | 次数 |
| --- | ---: |
| MULTI_INFLIGHT | 2829 |
| TRIPLE_OVERLAP | 2133 |
| FULL_STALL | 13 |
| KILL_P | 37 |
| KILL_R | 29 |
| PARTIAL_KILL | 1 |

配置为MinimalConfig/单核/单线程EMU，O2及T14融合开启、O1关闭，O2/T13观察开启。NEMU/镜像/观察器和判据沿用固定合同。

本轮只证明整核正确性与差分链路；取消后零多余时钟脉冲证据仍来自前轮真实父级严格检查。未做新公平周期A/B、综合STA、功耗测量或运行期全核reset，不代签人工验收。

旧H1 build保存在/home/riscv/riscv-lab/o2-h1-build-before-r3-div-gate-20261024。当前build/emu是修复版。下一步以同镜像进行修复前后周期不退化检查，再做同约束成本/STA。

仅本地提交，无GitHub推送。原始工作根：/home/riscv/riscv-lab/o2-r3-div-gate-fullcore-20261024。

查看[合同](CONTRACT.md)、[封存清单](evidence/20261024-fullcore/archive-manifest.json)；原始命令、退出码、日志及生成物哈希随证据保存。

## 交付复核（2026-10-25，UTC+08:00）

实际全核执行及Linux严格复算于2026-10-24 23:58完成，交付复核跨至10月25日。
[归档](evidence/20261024-fullcore/archive-manifest.json)包含319份载荷：原文230472792字节，封存18699120字节；manifest SHA256为3d81f60cf9d71ee545545549ae7ac218dad9c51c8a01263abbc7b9a8e2320b2f。
[Linux便携复核](reviews/portable-linux.json)与[Windows原生复核](reviews/portable-windows.json)均通过，结果逐字段一致：13条完整轨迹、1条预期bit100拒错截断轨迹。
便携复核只验证封存字节、原始退出码／日志绑定及O2轨迹，不重新执行EMU/NEMU，也不代替前文Linux严格架构／输入来源复核。

相对原H1，429份硬件输入中只有ExeUnit.scala变化，21236份依赖相同；生成的VDotElastic、VIDiv、VFDivSqrt、ClockGate四个子模块逐字节相同，修复位于真实父级ExeUnit_17。
本次新构建仍确认H1低32位保存、公开输出高96位清零；原始证明见归档内runs/generated-source-check.json及build-01/generated-artifacts.json。

运行中观测到14:08至22:46的墙钟长间隔；恢复检查时原EMU进程仍存活并继续输出，没有停止或重启测试。
具体主机原因未确认，原始时间戳保留，证据为归档内runs/execution-gap-observation.json。
因此不能将本轮墙钟总跨度当成连续CPU计算时长，更不能据此计算处理器加速比。本轮未做新公平周期比较。

源码修复及五份局部门禁测试已保存为本地提交；文档／证据继续本地保存，未推送GitHub，未发布Issue评论。
下一步保留O2＋H1旧版作为对照，以同镜像、同参考库和相同配置验证修复版周期不退化，再做同约束综合／STA；这些项目仍未测。
