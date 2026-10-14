# T10 全核集成证据

2026-10-14，dev基准 `5389bde799f5ce1e7939e4eeed5fe9bcdc2325a3` 加当前未提交工作区。
候选合同 `vdot-s8x8-r32-v0.1`，源码包 SHA256 `b657e0896a10d6c9fadda54500a77b9c1819f1ca03c9d93dea47cd4884643901`，440项根编译输入、126个递归子模块。

本机结果：最终源码完整冷构建通过；20项代表性全核DiffTest（10合法/10非法、每项pre32/all32）通过并GOOD TRAP退出0；同一仿真器hello/vadd三组24项通过。6项真实单元/lint、实际合法/晚异常波形、编译失败与镜像损坏门禁均通过。T11完整验收保持开放。

| 材料 | 作用及边界 |
| --- | --- |
| [unit/check.json](unit/check.json) | 真实生产DecodeStage、FU及原始陷阱指令选择，共6项测试；全部32768编码、161译码请求、65586陷阱选择检查，局部控制覆盖见测试日志 |
| [classification-red/test.log](classification-red/test.log) | 修复前直接复现FuConfig自身VDOT向量分类缺口；共享EXU被其他FU分类不能替代它 |
| reference-build、reference-api | 固定NEMU基线/ISA补丁、NMIE复位1配置来源；实际DUT ABI下单步ebreak、非法VDOT、合法VDOT3项API检查 |
| failures/reference-reset、failures/late-mtval | 两次真实DiffTest退出1，保留未通过事实和源码定位依据 |
| failures/diagnostic-wave | 旧参考复位不一致时的DUT精确异常事件；诊断波形来自失败运行，不能计为全核通过 |
| failures/generic-compatible-timeout | 兼容参考下普通ebreak能正确记录，但整次入口自测退出124，不记7项完整通过 |
| [smoke/check.json](smoke/check.json)、[regression/check.json](regression/check.json) | 新仿真器实际VDOT全核与现有vadd运行，不是NEMU standalone或旧仿真器结果 |
| [wave/wave-summary.json](wave/wave-summary.json) | 140000～190000区间的合法请求/结果/提交及晚非法配置精确mtval；输入/输出ROB身份和物理目的保持，非法vec/v0写使能零 |
| negative-image | 镜像损坏被实际运行入口拒绝，旧PASS移除，原镜像精确恢复 |
| negative-compiler | 真实交付入口在编译器退出17后删除旧通过记录，未进入RTL验收 |
| source-used | 本轮程序与验证脚本的精确字节；运行脚本独立于冻结硬件编译输入绑定 |

本目录保存实际日志、来源清单和紧凑波形事件。大型FIR/RTL、仿真器、ELF/BIN、FST及原始事件CSV留在本机缓存或team/out，仅归档摘要；`archive.sha256`将覆盖本目录实际交付字节。

当前使用既有WSL/Clang19低内存构建环境，未修改永久WSL配额或新增临时交换文件。T11完整矩阵、高位/CSR故障注入、依赖与取消代表例、成员独立复现、ISA签字和性能均不由T10冒烟关闭。实现和复现入口见[接入说明](../../docs/t10-integration.md)。
