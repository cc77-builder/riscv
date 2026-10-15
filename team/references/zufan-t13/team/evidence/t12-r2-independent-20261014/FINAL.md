> 本文件是独立审查的只读展示副本。正文相对路径指向同目录审查包解压后的 `independent-review/`，原始正文保存在归档中，不代表所有源码副本直接铺在 GitHub 目录。参见 [README](README.md)。

# Independent T12 / VDot review — final

已完成可访问固定源码的独立审查，产物全部位于本 review 目录。**没有晋升硬件候选，没有声称全核性能通过。**

- **真实输入路径已纠正**：bypass 与 VFEX 之间有 `NewPipelineConnect` 数据寄存器，不能把 RF/旁路与融合乘法跨寄存器相加。融合仍需验证 product 路径、归约路径、redirect/ready、ICG、setup/hold/fanout；还可能失去输入操作数隔离。取消后门控使能不清是源码推导风险，尚待真实 EXU 验证。
- **更强 RVV 基线已真实汇编并在固定 NEMU 参考中验证**：通用13→8条、已知配置11→6条、四路batch26→15条；包含全部32,768种寄存器编号组合、2,016组边界/状态/别名、1,000随机组、旧序列328组及两个batch版本。不是周期加速比。
- **确认验收缺口**：接受超64位计数/不足退休量；compact digest不绑定周期；receipt不核对实际镜像/日志；多个长循环终态无法证明次数；异常恢复可擦除瞬时v10错误。合成反例和真实编译 C verifier 注入均可复现；不把这些称为已发生的 RTL bug 或已绕过真实逐步 DiffTest。
- **排除无依据的 timeout 归因**：hex/decimal18项边界检查和C/Python digest一致；13个原stress body连同原trap harness、C judge在短参考执行中全部返回，摘要`2e51e6e6b71a5ebd`。四个旧全核切片仍是exit124、无end，全部NOT_ACCEPTED。

主报告：[EARLY_TIMING_REVIEW.md](EARLY_TIMING_REVIEW.md)、[RVV_BASELINE_REVIEW.md](RVV_BASELINE_REVIEW.md)、[TIMEOUT_REVIEW.md](TIMEOUT_REVIEW.md)。结构化结论/分类/精确行号/命令退出码：[REVIEW.json](REVIEW.json)。逐文件Git blob/SHA：[SOURCE_INDEX.md](SOURCE_INDEX.md) 及 [source manifest](evidence/source_manifest.json)。

固定生产审查 SHA：`b8272f2e8a62557437869c936b6ea9ce5fff84fe`，相关 RTL 与团队 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3` 相同。VDot blob为`9e393f3ee4d0cafc002d5fa1c301b0761da16882`。参考库SHA256为`e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae`。598份固定源码/历史证据完整性检查通过。

Draft #1 `f8e8276681e0f4cfdc4ce0d8e2a76ebb4897493e` 在四个相关本地Git对象库不可解析；没有联网补取，也没有将主任务的并发工作区内容冒充它。原研究融合patch已独立散列，`git apply --check` exit0，未应用到生产。

**未完成的晋升门槛**：候选真实RTL A/B与集成clockgate/OG2/WB/ROB验证、真实STA/Liberty/PVT/SDC、布局后setup/hold、功耗/面积/频率、同硬件公平全核周期测量，均NOT_RUN。发现本地Yosys/Verilator路径不等于具有可签字的工艺时序流程；未用generic gate统计冒充PPA。建议主实现先替换冗余RVV序列并加强验收，再以实际可闭合周期与全核周期共同决定融合是否值得。

复现（仅短参考与脚本检查，不构建AM或整核）：

```bash
cd /home/lizufan/chatpc-workspaces/xiangshan-t12-20261014-r2/review
./scripts/run_validation.py
```

工具路径、版本、SHA与每条命令在 `logs/*.command.json` / [tool_inventory.json](evidence/tool_inventory.json)。NEMU驱动的早期单步ABI、解码缓存、非零vstart探测失败保留在单独日志；最终对应检查exit0，失败没有冒充DUT问题。

没有子代理、其他AI模型调用、网络、提权或安全设置修改、AM构建、重EMU、Git push、父目录repo/runs或旧工程写入。所有本审查普通子进程均同步等待退出；收尾检查见 [FINAL.json](FINAL.json) 和 [cleanup.json](evidence/cleanup.json)。
