# R3 / VDot carry-save 归约筛选

结论：**STOP_SCREEN，不采用该候选**。完整 FU 的归约路径只改善 0.885%，面积增加 0.546%，i2r 退化 1.917%，未达到[事前合同](CONTRACT.md)。生产 RTL 与稳定 C/RVV 入口保持现有版本。

- [结果与技术边界](RESULT.md)：真实生成 RTL 证明、FU 验证、完整 FU 面积/时序及失败记录。
- [candidate.patch](candidate.patch)：只供独立实验检出使用的候选补丁，没有应用到本分支生产 RTL。
- [证据索引](evidence/archive.json)、[原始比较](evidence/comparison.json)、[全部路径表](evidence/paths.csv)、[接续定位](evidence/handoff.json)。
- [归档](evidence/r3-evidence-v1.zip)：493 份载荷，包含全部成功/失败运行输出、源码/工具身份、生成物、实际命令和最终证明；外部省略清单为空。
- [recheck.py](recheck.py)：从归档恢复并重新审计原文，无需启动 EDA 或 EMU。

## 首选复算

在本提交的完整仓库检出中，用 Python 3 执行；输出路径必须不存在：

```sh
python3 -B team/optimizations/o4/reduce/recheck.py \
  team/optimizations/o4/reduce/evidence/r3-evidence-v1.zip \
  --output /tmp/r3-recheck-new.json
```

期望 `R3_SEALED_RECHECK_PASS`，`decision=STOP_SCREEN`，`files=493`、`raw_sta_profiles=10`、`proof_negative_controls=5`、`fu_negative_controls=4`。程序使用同仓库未修改的 O4 原文审计器，验证载荷 SHA256、源/生成物/映射/STA 关联，重新生成算术证书并核对负控反例，重新计算固定门槛。它只把历史路径前缀映射到临时解包目录进行读取，原证据文本不改写，也不读取旧运行目录。

ZIP 使用 O4 已有 gzip/manifest 封存格式；单个大载荷为 gzip。可直接查看 manifest，再按 `entries[].gzip` 恢复对应文件。仓库局部 `.gitattributes` 将 ZIP 标为二进制，避免根目录文本规则改变证据字节。

## 工具与重建边界

实验源码基点为 `6ffe7f94839b08df8de2558c35d482e1b90288e8`。使用 Linux 原生独立 baseline/candidate 检出及新输出目录；只在 candidate 应用补丁。完整的实际参数和执行脚本位于归档 `launchers.json`，运行定位与依赖来源见 `evidence/handoff.json`、归档 `setup-01.json`、双方 `*-gen-01/source.json`。个人绝对路径是本次执行事实，复建应替换为显式配置的新目录。

[experiment.py](experiment.py) 的 `elaborate`、原 O4 的 `synthesize.py` / `timing.py`、原 O2 的 `run_rtl.py` 是实际入口；分别使用 `--help` 查看参数。当前提供的补丁及冻结驱动对应上述源码基点，不将后续生产变更自动视为同一实验。全局四核预算；两次 JVM 生成顺序执行，G1 与双方 EDA 可在总预算内分配 2+1+1 核。当前筛选已结束，复算现有证据通常足够；新的实现或工具条件须建立新实验身份。

[structural_proof.py](structural_proof.py) 对实际生成的 `VDotReduce.sv` 经 Yosys 得到的网表做全输入域算术证书校验。它是本轮成功的证明方法。[formal_cec.py](formal_cec.py) 保留 ABC CEC 备用入口和严格结果解析；本轮 SAT/CEC 尝试超时或预检查失败，没有得到 CEC PASS。

[sta_compat.py](sta_compat.py) 只将等长、单比特拼接赋值拆为对应标量赋值，使 OpenSTA 2.0.17 能读取 Yosys 0.9 输出。对本次网表已核实重读后的完整结构相同，未重新映射、改变约束或换库。该适配仅用于团队实验输入，不修改官方程序。

不扩大到真实父级 G2、整核、应用或物理设计。若要重开该路线，先提供新的原始路径证据和有针对性的修订假设；不能把本次正确性 PASS 转移给新候选。
