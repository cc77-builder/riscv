# H1 低 32 位保存：实现与局部验证

2026-10-21：**已实现并完成本轮验证。** 先读 [H1 实现与验证结果](H1_RESULT.md)、[合同](CONTRACT.md) 和 [全部 70 项时序对照](timing-comparison.csv)。

- 10,022 个唯一向量的完整 128 位结果、FU/真实 VFEX4 父级控制、4+16 项观测值负控通过；II=1、无阻塞响应 2 拍保持。
- 完整 FU 面积下降 2.33386%，完整父级下降 0.137349%，两边均减少 96 个 DFF。
- 五档参考 STA 完成，部分路径回退；20 fF 父级 ready 增加 89.237 ps。两版均未满足 1 ns 参考目标，审计通过不表示时序收敛。
- 候选值得进入后续全核回归；当前没有 H1 全核/NEMU 或新性能测量，整项 R1 和最终采用未完成。

原始工作根为 `/home/riscv/riscv-lab/o2-h1-result32-20261021`。`campaign-state.json` 记录 11 个顺序阶段真实通过；不要重复启动已完成 campaign 或覆盖原始结果。实际身份是 `9b6cf07` 加 `h1-production.patch` 与逐文件 SHA，不是 HEAD 本身。

`run_campaign.py` 是从源码执行硬件步骤的入口；`validate_functional.py` / `compare_cost.py` 只读核查已有证据。执行命令及依赖见结果记录。新审计检查器共 12+20 项主机测试通过。

证据归档见 [manifest](evidence/20261021-local/manifest.json)，压缩格式及字节复核命令见结果记录；封存不包含 obj/缓存/运行二进制。审计需要原始工作目录及 B0 资料，不能直接把归档路径冒充原始工作目录。

当前生产源码含 H1，但 `repo/build/emu` 仍是 B0；R0 锁仍标识 B0。未改默认开关，本轮未提交或推送 GitHub；自动复核不代替成员人工 ACK。
