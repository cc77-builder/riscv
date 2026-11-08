> 最新追加：2026-10-27，第26条为8×32配置复用普通C调用验证；无新性能窗口，旧25条全部保留。详见文末第16节。

> 最新追加：2026-10-27，第25条为4尺寸×3数据集的新配置复用矩阵；第24条仍是历史8×32/d0探针，全部旧数据保留。详见文末第15节。

> 最新追加：当前 JSON 已有 **24 条记录**。第 13 节为同机干净复现（25 应用装载字节、768 窗口、96 C 输出一致，保留全核宿主时间限制）；第 14 节为配置复用 8×32/d0 筛选（273 cycles，候选保留，未切默认）。以下原导言中的“22条”“干净复现未完成”等措辞是第22条写入时的历史状态，原文保留。

# 香山 vdot 各版本运行数据档案

更新：2026-10-27（UTC+08:00）。本文件保存版本身份、测量口径、实测数据和采用依据；后续每版继续追加。原始实验合同和封存证据是最终依据。它不维护待办顺序；当前开发安排仍看 [开发路线](development-route-current.md)，执行过程仍记 [开发计分板](../../开发计分板.md)。

历史部分只读取已有成果，未重跑旧版本或补授资格。当前保留的生产实现是 **O2＋H1＋DIV 取消关钟修复 0f12df6**。C1、C2 已否决。C3-G0 的只读建议保留在第 10 节；随后实施的 **C3-HF 单次最小试验也已否决**：局部验证通过，面积 +0.184115% 超限，五档路径 20/45 通过、25/45 失败。三控制 D 最差虽下降 16.617459%，仍未通过完整合同。第 11 节追加本轮真实结果，旧记录保留各自当时状态。C3-HF 的新全核/NEMU、周期、功耗和整核 Fmax 均 NOT_TESTED；当前门控试验关闭，0f 与原 EMU 不变。

配套机器可读索引：[version-data-ledger.json](version-data-ledger.json)。索引含完整硬件/EMU 身份、22 条工程记录（第20条为评审/抽象控制，第21条为 C3-HF 真实局部及成本试验，第22条为当前 0f＋firstdot V2 的功能/周期组合资格）、原表文本、指定原 CSV/JSON 和输入 SHA-256。只列出历史执行实际支持的结果；未执行的层级写 NOT_TESTED，而不是 0。

第 12 节追加 firstdot V2 的当前组合实测：功能与 DUT 周期原文审计通过，严格墙钟时间线 FAIL 单独保留。硬件仍是 0f；源码已本地固定为 c823a878，干净复现尚未完成，配置复用与新面积/STA 仍为 NOT_TESTED。

## 1. 如何比较这些数字

- **同一 comparison/run ID 内才按原合同比较。** T14 原消融的 batch128 为 464 cycles；后续统一镜像中的 T14 为 453.25 cycles。两者镜像、观察器/构建及统计合同不同，不可拼接成连续硬件收益。
- **FU 拍数、全核窗口 cycles、面积和 STA 分开。** II=1 不等于应用每点积 1 cycle；同镜像周期不退化不意味着频率不退化。
- 加速比保留分母。微基准通常使用同版实测 RVV/vdot；硬件消融使用旧 vdot/新 vdot。S1/R4 使用同合同中最快合格 RVV，不拿较慢基线抬高比值。
- 确定性重放证明可复现，不增加独立样本。正式窗口之外的 first/warmup、失败、中断、负控和恢复仍保留。
- 综合面积是参考库单元 area 之和；STA 为布局前参考约束。所有硬件版本的实际整核 Fmax、布局布线和活动率功耗均 NOT_TESTED。本档案不推算比赛得分。

## 2. 版本与证据层级

PASS 仅适用于表中原合同和身份。“周期”指该版是否有已完成的相关真实测量，不表示任何工作负载均获益。

| 版本/工作 | 主要变化或用途 | 真实 FU/父级 | 全核/NEMU | 周期 | 面积/STA | 已有决定 |
| --- | --- | --- | --- | --- | --- | --- |
| T13 原基线 | 单请求、3 拍响应、II4 | 原阶段资格 | PASS | PASS | NOT_TESTED | 冻结对照 |
| T14 | 输入拍保存乘积，2 拍响应、II3 | PASS | PASS | PASS | 本轮 NOT_TESTED | 后续基础 |
| T15 | 独立 INT16×8、64 位结果 | 独立算术/实验包装 PASS；父级 NOT_TESTED | INT16 NOT_TESTED | 全核 NOT_TESTED | NOT_TESTED | 参数扩展证据 |
| O1 | vdot 同拍响应/再接受，II2 | PASS | PASS | PASS | O4 有限定结果 | 冻结对照/回退 |
| O2/B0 | 两槽弹性 FU，II1 | PASS | PASS | PASS | O4 有限定结果 | 后续主线基点 |
| O3 | O1/O2 GEMV 测量，非新 RTL 版 | 复用固定硬件 | 应用 PASS | PASS | 本轮 NOT_TESTED | 识别应用收益有限 |
| O4 | O1/O2 成本评估，非新 RTL 版 | 不重新仿真 | 不重新运行 | 只引用既有值 | 报告有效，1 ns 未收敛 | 保留取舍 |
| H1 | R 槽结果 128→32 位 | 原合同 PASS | PASS | 96 对窗口不变 | FU 少 2.33386% | 保留；后来发现 DIV 关钟缺项 |
| 合并 H1 | 6d2/1a23 硬件，新夹具回归 | 不转授新局部资格 | MERGE-REG PASS | S1/S2/R4 各自测量 | 本身份 NOT_TESTED | 软件实验固定硬件 |
| S1 软件 | 向量累加及对等 RVV 优化 | 无新硬件 | 应用 PASS | 固定布局 v2 PASS | NOT_TESTED | 三种整块尺寸采用；K13 vdot 不采用 |
| S2 软件 | 安全尾部 | 无新硬件 | 应用 PASS | 固定布局和强 RVV 探针 PASS | NOT_TESTED | 未胜较快 RVV，不扩大采用 |
| R4 入口 | 普通 RV64 C ABI GEMV 函数 | 无新硬件 | 普通 C/应用 PASS | 新调用窗 PASS | NOT_TESTED | 按形状选择 vdot/RVV |
| DIV-fix0f | 取消后停止多余 DIV 时钟 | 新严格门禁 PASS | PASS | 96 对窗口不变 | 父级面积小降，部分时序退化 | 当前保留 |
| C1 | busy＋owner 替代双 hold | PASS | NOT_TESTED | NOT_TESTED | 15/45 筛选失败 | REJECT，不采用 |
| C2 只读归因 | 固定端点/缓冲扇出分析 | 未运行新仿真 | NOT_TESTED | NOT_TESTED | 2 次补充 STA | 支持先证明新假设 |
| C2-G0 | 空闲必 ready 的控制证明 | 控制抽象 PASS；非 RTL 仿真 | NOT_TESTED | NOT_TESTED | NOT_TESTED | 可进入 C2 设计 |
| C2 本轮 | busy/owner＋门控启动去 ready 依赖，真实接收协议保留 | PASS（含 SQRT/双 lane 增补） | NOT_TESTED | NOT_TESTED | NOT_TESTED | 局部通过，未采用；下一步成本筛选 |
| C2-cost 新轮 | 相同 C2 的独立成本筛选，旧局部记录保持 | 引用旧局部资格，本轮未重跑 | NOT_TESTED | NOT_TESTED | 20/45 通过，25/45 超限 | REJECT，保留 0f |
| C3-G0 评审 | 提出只改 FP DIV/SQRT hold 置位的 C3-HF；尚无新 RTL | 抽象控制 PASS；真实 FU/父级 NOT_TESTED | NOT_TESTED | NOT_TESTED | 仅引用历史值 | 建议至多一次试验，未实施/未采用 |
| C3-HF 实测 | 仅 FP DIV/SQRT hold 置位去 ready 依赖；保留双 hold 和原 ICG 公式 | PASS（本轮新 FU、父级、补充及观察） | NOT_TESTED | NOT_TESTED | 面积超限；20/45 通过、25/45 失败 | REJECT，保留 0f，关闭当前门控试验 |

O0 是吞吐观察/分析工具及证据入口，R0 是固定输入/复现前提，R1/R3 只读审查不是新的跑分硬件。它们按所支持的具体实验记录归档，不另造“优化后的数字”。H1 的原 PASS 不掩盖后续新严格关钟门禁 FAIL；修复和失败证据均见 DIV-fix0f。

## 3. 同镜像微基准数据

### 3.1 T14 原消融合同

[原结果及全部 13 场景](t14-optimization.md)；[合同](../spec/t14-ablation.md)。逐 dataset 先取正式轮次中位数，配对比值另行取中位数。以下是几个代表值，完整表保留在 JSON 的 t14/source_tables 中。

| 场景 | 基础 vdot cycles | T14 vdot cycles | 配对硬件加速比 |
| --- | ---: | ---: | ---: |
| 单次 | 72.5 | 71 | 1.0211× |
| chain256 | 2114 | 1857 | 1.1384× |
| batch128 | 599.5 | 464 | 1.2906× |
| stream64 | 1126 | 1125.5 | 1.0009× |
| generic64（含 CSR 管理） | 428.5 | 274.5 | 1.5701× |

这组是旧硬件/新硬件消融，不是后面各轮 RVV/vdot 比值。generic64 较大比值不能推广成纯算术或应用收益。

### 3.2 T14/O1：2026-10-18 新同镜像比较

[结果和身份](../optimizations/o1/performance/README.md)。36 次主运行、478 校验窗、192 正式窗；16 份 ELF/BIN 相同。正式均值 cycles：

| 场景 | T14 | O1 | O1 周期减少 | O1 实测 RVV/vdot |
| --- | ---: | ---: | ---: | ---: |
| single | 71 | 71 | 0% | 1.201× |
| chain256 | 1857 | 1857 | 0% | 2.930× |
| batch128 | 453.25 | 362.5 | 20.02% | 1.870× |
| stream64 | 1127.5 | 1127.5 | 0% | 1.005× |

### 3.3 O1/O2：2026-10-19 新同镜像比较

[结果和身份](../optimizations/o2/performance/README.md)。O1 在相同硬件输入下重新构建，O2 复用已验收 G3 固定 EMU，工作负载两版实际新跑。36 次、478 校验窗、192 正式窗。

| 场景 | 本轮 O1 | 本轮 O2 | O2 周期减少 | O2 实测 RVV/vdot |
| --- | ---: | ---: | ---: | ---: |
| single | 71 | 71 | 0% | 1.201× |
| chain256 | 1857 | 1857 | 0% | 2.930× |
| batch128 | 362.5 | 221 | 39.03% | 3.068× |
| stream64 | 1127.5 | 1127.5 | 0% | 1.005× |

### 3.4 B0/H1 与 H1/DIV-fix0f：两轮独立不退化检查

[B0/H1](../optimizations/o2/result-width/h1/performance/B0_H1_RESULT.md) 与 [H1/DIV-fix0f](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md) 分属两轮新运行，各有 36 次 EMU、478 校验窗、192 正式窗、96 对逐窗比较。两轮均为逐对差值 0，不能合成一次四版本同步实验。

| 场景 | B0/H1 各自 vdot 均值 | H1/fix0f 各自 vdot 均值 | 每轮各版实测 RVV 均值 | fix0f RVV/vdot |
| --- | ---: | ---: | ---: | ---: |
| single | 71 | 71 | 85.25 | 1.200704× |
| chain256 | 1857 | 1857 | 5440.5 | 2.929725× |
| batch128 | 221 | 221 | 678 | 3.067873× |
| stream64 | 1127.5 | 1127.5 | 1133 | 1.004878× |

H1 减少存储，DIV 修复取消后的多余时钟；这两轮没有新增 cycles 加速收益。C1 和 C2-G0 没有全核周期成绩。

### 3.5 四项目统一测试：同一旧合同，单独存档

[完整比较与限制](unified-vdot-comparison-20261017.md)；[固定条件与公开源码身份](../workloads/unified-vdot/README.md)。本机实际运行64个全核镜像，384个正式窗口。每格为“自定义窗口平均 cycles / 该实现实测 RVV÷自定义”。这里只比较当时的 T14、Jade、试水、Redoop dot8 适配，不把后来 O2/C2 插入此表作为当前排名。

| 实现 | single1 | chain256 | batch128（四路×32） | stream64 |
| --- | ---: | ---: | ---: | ---: |
| 本项目 T14 | 71 / 1.201× | 1857 / 2.930× | 453.25 / 1.496× | 1127.5 / 1.005× |
| Jade | 70 / 1.218× | 1601.25 / 3.398× | 260.25 / 2.605× | 1126.25 / 1.006× |
| 试水 | 71 / 1.201× | 1857 / 2.930× | 292 / 2.322× | 1127.5 / 1.005× |
| Redoop（dot8 适配） | 90.25 / 0.953× | 3673 / 1.481× | 744.75 / 0.929× | 1155.5 / 0.981× |

Redoop 原生工作不同，表中已计入完成共同 dot8/full128 的软件适配；窗口外辅助代码并非逐字节相同。这里没有统一 PPA、真实频率或官方排名结论。

## 4. 应用数据按合同保存

### 4.1 O3：O1/O2，reuse/endtoend

[O3 合同和原始比较](../workloads/o3-gemv/README.md)。四尺寸、三数据集、basic/reuse、core/endtoend 全矩阵 768 正式窗；下表只是明确标注的 reuse/endtoend 切片，全部 comparison.csv 已纳入机器索引。

| GEMV | O1 vdot cycles | O2 vdot cycles | O2 周期减少 | O2 对较快 RVV |
| --- | ---: | ---: | ---: | ---: |
| 4×8 | 166.5 | 164 | 1.50% | 1.160× |
| 8×32 | 323.5 | 321.5 | 0.62% | 1.035× |
| 16×64 | 856.75 | 847.75 | 1.05% | 1.054× |
| 4×13 | 212 | 209.5 | 1.18% | 0.907× |

### 4.2 S1：合并 H1 硬件、固定布局 v2

[S1 全表](../optimizations/o2/r2-vector-accum/VALIDATION.md)。57 次主批、768 正式窗；另 4 次小尺寸重放不新增正式样本。下表均为 reuse/endtoend。

| GEMV | S0 vdot | S1 vdot | S1 周期减少 | 同合同最快 RVV | RVV/S1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4×8 | 164.5 | 155 | 5.7751% | 175 | 1.129032× |
| 8×32 | 318 | 278.25 | 12.5000% | 289 | 1.038634× |
| 16×64 | 846.5 | 701.25 | 17.1589% | 768.25 | 1.095544× |
| 4×13 | 210 | 212.75 | −1.3095% | 175 | 0.822562× |

S1 v1 布局改变 caller/加载地址，性能不进入采用统计，历史输出保留。禁止拿 v1 或旧 O3 均值替代 v2 的实际 S0 分母。

### 4.3 S2：固定布局主批与强 RVV 探针分别记录

[S2 结果](../optimizations/o2/r2-safe-tail/FIXED_RESULT.md)。主批 31 进程/384 正式窗；探针 5 进程/32 正式窗，探针仅 dataset0，不能冒称全 12 样本强 RVV 资格。

| 比较范围 | S0 vdot | S2 vdot | RVV / 解释 |
| --- | ---: | ---: | --- |
| K13 basic/endtoend，主批 | 246.25 | 298.25 | vdot 退化 21.117% |
| K13 reuse/endtoend，主批 | 210 | 187 | vdot 减少 10.952%；原 RVV 190/190.25 |
| K13 reuse/endtoend，dataset0 强 RVV 探针 | 不混入主批 | 187 | 较快 RVV 175.25；S2 慢 6.705% |
| 16×64 reuse/endtoend，主批 | 845.25 | 845.25 | 整 BIN 和窗口不变 |

旧 S2 K13 −10.621% 有布局混杂，仅保留为历史观察；固定布局重测的 −10.952% 是另一合同。当前未扩大 S2 采用。

### 4.4 R4：真实函数调用窗

[R4 原表及普通 C 验证](../optimizations/o2/r2-select/ENTRY_RESULT.md)。窗口包括参数传递、jal、完整叶函数和 ret。性能 33 进程/384 正式窗；另 3 个普通 C 进程验证 16 公共函数、48 不同 case、96 次正常调用。

| GEMV | S0 reuse vdot | S1 reuse vdot | 最快合格 RVV | 本合同选择 |
| --- | ---: | ---: | ---: | --- |
| 4×8 | 178.5 | 169.75 | 187.5 | S1 vdot |
| 8×32 | 335.5 | 292.5 | 300.75 | S1 vdot |
| 16×64 | 860 | 717.25 | 779.5 | S1 vdot |
| 4×13 | 219.25 | 219.75 | 187 | S1 RVV |

旧直线内核与新调用窗不能相减后宣称“纯 ABI 开销”；它们没有构成只改变调用的独立实验。S1/S2/R4 软件资格也不能直接转授到后来 C1/C2 新硬件。

## 5. 成本档案

下表每个值均有原独立实验，比较边界保持完整生产 FU/真实 VFEX4。O4→H1→fix0f→C1 的相邻配对按对应合同核验；没有把所有版本在本次重新综合。

| 版本 | FU 单元面积和 μm² | VFEX4 父级单元面积和 μm² | FU DFF | 父级 DFF | 数据来源 |
| --- | ---: | ---: | ---: | ---: | --- |
| O1 | 12525.142 | 281750.392 | 1048 | 16675 | O4 |
| O2/B0 | 17711.610 | 285271.700 | 1838 | 17267 | O4 |
| H1 | 17298.246 | 284879.882 | 1742 | 17171 | H1 实测 |
| DIV-fix0f | 17298.246 | 284614.946 | 1742 | 17172 | 修复后实测 |
| C1 | 复用固定相同 FU，未重测 | 284587.548 | 复用 1742 | 17171 | C1 父级实测，筛选否决 |
| C2 | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED | 待独立成本任务 |
| C2-cost 新轮 | 复用固定相同 FU，未重测 | 284496.310 | 复用 1742 | 17170 | 新父级实测，25/45 筛选失败；见第 9 节 |

H1 实际净减少 FU 2.33386%、父级 0.137349%；并非此前局部估计的 3.0277%/0.1879%。fix0f 父级面积少 0.092999%，但映射 DFF 多 1，来自原整数 DIV 保留/裁剪差异。C1 少 1 个 DFF，父级面积只少 0.009626%，不能把面积收益完全归因于单个 DFF。

共同参考条件：Yosys0.9/ABC1.01/OpenSTA2.0.17；Nangate45 typical 25°C/1.1V；库 SHA-256 为 8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1；ABC 1000ps、BUF_X1、5fF；STA ideal clock、5K wire-load、uncertainty/transition 0.05ns、IO delay 0.1ns、父级 TE=0。五档为 nominal 1ns/5fF、0.5ns/5fF、2ns/5fF、1ns/1fF、1ns/20fF，均非布局后签核。

### 5.1 nominal 路径到达时间（ns）

这是每类查询最坏路径，起止点可能改变；完整端点/slack/五档原表在各来源文件及 JSON 中。不得把 arrival 倒数当整核 Fmax。

| 路径 | O1/O4 | O2/O4 | H1 | DIV-fix0f | C1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| FU r2r | 1.154101 | 1.152729 | 1.163404 | 1.163404 | 复用 FU，未重测 |
| FU i2r | 1.186674 | 1.219926 | 1.190323 | 1.190323 | 复用 FU，未重测 |
| 父级 r2r | 3.219300 | 3.191926 | 3.166914 | 3.261218 | 3.235859 |
| 父级 i2r | 3.298250 | 3.245332 | 3.194971 | 3.314103 | 3.301439 |
| 父级 ready | 0.339943 | 0.274544 | 0.295424 | 0.247821 | 0.266115 |
| VDot r2r | 1.337530 | 1.321661 | 1.345889 | 1.356106 | 1.402385 |
| VDot i2r | 1.516260 | 1.540559 | 1.511395 | 1.474949 | 1.479503 |
| VDot r2o | 3.174139 | 2.807015 | 2.832115 | 2.776701 | 2.677773 |
| 父级全部 gate-enable 最坏 | 1.785938 | 1.915197 | 1.855397 | 1.888362 | 见各 ICG，不混查询 |

H1 在 20fF 的 ready 为 0.413792ns，对照 B0 0.324555ns，退化 89.237ps；不能只保留 nominal 或有利档位。两版 ready 仍有正 slack，但整体参考 1ns 均未收敛。

来源：[O4](../optimizations/o4/O4结构与时序评估.md)、[H1](../optimizations/o2/result-width/h1/H1_RESULT.md)、[fix0f](../optimizations/o2/r3-div-gate/PERFORMANCE_COST_RESULT.md)、[C1](../optimizations/o2/r3-div-gate/c1/RESULT.md)。

### 5.2 C1 及只读归因的专项数据

| nominal 查询 | fix0f | C1 | 结论 |
| --- | ---: | ---: | --- |
| 控制状态最差 D | 1.930584 | 0.798315 | 改善 58.649% |
| 整数 DIV ICG.E | 1.128021 | 1.727299 | 退化 53.126% |
| 浮点 DIV ICG.E | 1.888362 | 1.901547 | 退化 0.698% |
| VDot ICG.E | 0.873228 | 0.808116 | 改善 |
| 固定 lane4→同结果位 | 1.356106 | 1.401305 | 退化 45.199ps |
| 固定 lane6→同结果位 | 1.355025 | 1.402385 | 退化 47.360ps |

C1 五档的 VDot r2r、ready、整数 DIV ICG 共 15/45 项超容限，因此否决。只读归因新增两次 STA、20 查询：19 个有效路径，1 个 owner/Q 无路径；实际整数门控分支从 QN 出发，不能把无路径记 0ns。整数最坏门控路径 BUF 从 8→19 个，缓冲弧延迟合计 0.595722→1.366627ns。见 [归因报告](../optimizations/o2/r3-div-gate/c2-attribution/RESULT.md)。

## 6. 功能和扩展数据不能冒充跑分

| 版本/层级 | 已有数据 | 解释边界 |
| --- | --- | --- |
| T05/生产 INT8 数学与算术 | 22 定向＋10000 固定随机，完整 128 位结果 | 同一集合多层重跑不能累加唯一 case |
| T15 s8x8/r32 | 10022 数值；65572 协议拍；2 拍响应/II3 | 独立 ParamPipe |
| T15 s16x8/r64 | 94＋10000=10094 数值；65968 协议拍；2 拍响应/II3 | 35 位精确累加、低64位结果；生产全核 INT16 未接入 |
| H1 父级 | 34356 拍；9类切换；FU4＋父级16负控 | 原合同；不能替代后加严格关钟门禁 |
| DIV-fix0f 父级 | 35075 拍13组；48取消空闲窗/144采样0多余脉冲；28ROB定向；12DIV复位 | 真实 VIDiv/VFDiv/ClockGate；旧 H1 在新严格门禁实际拒绝 |
| fix0f 全核 | 13正常＋1bit100负控；117唯一case/124执行；5378 vdot提交 | 未新增运行期全核 reset |
| C1 | 状态4可达/1920转移；真实父级与 fix0f 日志字节相同 | 原浮点动态刺激为 DIV，没有 SQRT 动态资格 |
| C2-G0 | 主抽象48状态/33600转移；ROB65536项；5变异检出 | 有效初始化/正常接口下控制证明，不是新 RTL 数值仿真 |

C2-G0 的真实异步 reset 与同步测试夹具 bootstrap 条件分别记录，涵盖取消、浮点双 lane、SQRT 控制。详见 [G0 原结论](../optimizations/o2/r3-div-gate/c2-g0/RESULT.md)。无有效初始化的环境反例、所有故意破坏控制关系的反例均保留。

### 6.1 C2-local-20261025-01：本轮真实局部验证

候选提交 **6704ce3502a7235cdb81697638c01ed23f6914f6**，生产修改仅 ExeUnit.scala，文件 SHA256 为 febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6。候选在独立检出中组合 busy/owner 保持与不依赖 ready 的门控启动；对照仍为获保留的 fix0f。真实 parent.ready、child.valid、实际接收、ROB 捕获和响应协议保留。

| 本轮层级 | 实际数据/状态 |
| --- | --- |
| FU 完整结果与控制 | PASS；10022 向量、31499 拍；23311 接受、22460 响应、739 取消、112 复位丢弃；4 项观测故障负控全部检出 |
| 原真实父级矩阵 | PASS；35075 拍、13 组；13611 接受、13122 响应、426 取消、63 复位丢弃；16 项观测故障负控检出 |
| 原严格取消关钟 | 48 空闲窗口/144 采样，额外时钟脉冲 0；原父级日志与 fix0f/C1 固定日志 SHA 相同 |
| 新真实父级增补 | PASS；2959 拍、6 组，实际 SQRT、取消、ROB、切换、TE=0 动态复位 |
| SQRT 定向与控制 | 15 正常 SQRT、48 取消、14 ROB 定向、18 切换；这些覆盖标签有交集，不求和成唯一 case |
| 双 lane 实际不同步 | 两种方向分别 56/27 拍；不同步时取消各 6 例，均来自真实内部观测 |
| 空闲/复位增补 | 620 次空闲 ready 检查；20 个 TE=0 复位场景；162 次取消后即时空闲采样 |
| 增补负控 | 7 项离线观测变异全部检出；不是 RTL 故障注入 |
| 源码及生成控制结构 | 独立审查 PASS；两处 DIV 门控启动的生成控制锥去除 ready 依赖；旧 C1 被同检查器按预期拒绝 |
| 新全核/NEMU、同镜像 cycles、面积/STA、功耗、Fmax | NOT_TESTED |

本轮只能作 **LOCAL_VALIDATION_PASS_NOT_ADOPTED**：尚未采用 C2，也没有新的加速比或时序改善结论。下一步相对 fix0f 做同约束父级面积与五档 STA 筛选，通过后再进入新全核回归。完整结果见 [C2 结果](../optimizations/o2/r3-div-gate/c2/RESULT.md)，不可变证据入口为 [C2 manifest](../optimizations/o2/r3-div-gate/c2/evidence/20261025-local/manifest.json)。manifest 的最终 SHA 由本轮封存后补入配套 JSON；实际本地来源已逐项固定。

## 7. 完整身份索引

构建提交不等于后来文档提交；未提交候选必须同时记基点、patch 和逐源 SHA。完整身份见配套 JSON hardware_identities；下表便于定位。

| 记录 | 硬件/实际源码身份 | EMU SHA-256 前缀 |
| --- | --- | --- |
| T13 | 4460300e9557ad20ac152fa67b1827c5d62802dd | 9903d6d8b3d59bed |
| T14 原构建 | 2443fb1c101dfc5974ac208275a8b86d68a11e0f | 60521f406816846f |
| T14/O1 的 T14 | 72fc206a417e5781dded45433eae0de45f181458；继续编译2dee53fc | 081247df2c8220a3 |
| 原 O1 | 18c0ce08a40e889654bfe76d5435f272854ad7d0 | b13b05a3b03d2dd1 |
| G4 新 O1 | a239dace720b32216e83fb5a514930d334c69a26 | 6699225b76ceae47 |
| O2/B0 | b218cbc6e6b135e4ff219a902a9284a59d3c82c9 | ac0123280bf6c742 |
| H1 全核 | 8b5024fcbd96986871cc40ce8c9fb71a67c495eb | e37b3c267cae2903 |
| 合并 H1（S1/S2/R4） | 6d2abe403b07c297b8830a7d4f06e370b0a8e070 | 1a23dbab5f919da0 |
| DIV-fix0f | 0f12df675378556670afd0dd2153f47fcb330610 | 2d1db77cc407486a |
| C1 | 3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66 | NOT_TESTED |
| T15 独立 | 65f6159e305adc10b4f8bd67812f3a6460ccf360 | NOT_TESTED |
| C2-G0 | 审查 fix0f，未生成新硬件 | NOT_TESTED |
| C2 | 6704ce3502a7235cdb81697638c01ed23f6914f6 | NOT_TESTED |
| C3-HF | 77d0a1228f0da7d584d5c7375b404dcda9763cf3 | NOT_TESTED |

H1 成本轮实际身份是 9b6cf074 基点＋h1-production.patch＋candidate-inputs.json 的逐文件 SHA；不能把后来 H1 全核提交冒充较早未提交局部试验的构建来源。运行工具、参考 NEMU、flash、镜像、依赖、库及工具链另在每轮 manifest 中绑定。本档案固定这些来源文档/清单的 SHA，未声称已再次检查全部外置大二进制。

## 8. 后续每一版如何追加

1. **实验启动前**给新候选和比较分配永久 ID，例如 C2-local-20261025-01、C2-cost-日期-01、C2-core-日期-01；先存合同、基线身份、源码/patch哈希、配置和门槛。只完成局部验证就只记局部资格。
2. **每次真实运行**用新输出目录，保存命令、开始结束时间和时区、真实退出码、输入/工具/构建身份、原始 stdout/stderr、生成物清单；长期大二进制可以外置，但必须存大小、SHA及恢复来源。
3. **每次结论形成**新增 JSON record，不覆盖旧 record；本 Markdown 新增对应小节或表行，指向合同和不可变 evidence/manifest。相同候选的后续层级可以新增子 run 记录，并保留前一轮“当时未测”的时间边界。
4. **所有周期结果**保存逐窗口 CSV/JSON，包含 dataset、repeat、seq、phase、method、实际工作量、cycles、退休指令、镜像 SHA 和硬件身份。清楚写均值/中位数/配对比值，first/warmup/replay 不悄悄删掉。
5. **所有成本结果**保存完整层级边界、生成源/网表、工具/库 SHA、综合命令和 STA 约束；五档和所有原规定路径都保留。NO_PATH、FAIL、REJECT、NOT_TESTED 不能换成 0 或空格；保留起止点/slack。
6. **失败/否决照样存档。** 源码改了、检查器修了、布局改了，必须新身份/新 run；原错误记录不能覆盖成 PASS。取舍由既定合同判断，不能只挑最优一轮。
7. **发布前**核验 manifest、原始数据到汇总的复算和文档链接；跨 Windows/WSL 复制要逐文件比哈希。用户未授权推送时仅本地保存。计分板只加工程摘要和档案链接，不复制整套数据表。

新记录模板（也在 JSON 的 record_template 中保留）：

~~~json
{
  "record_id": "C2-cost-YYYYMMDD-01",
  "candidate": "C2",
  "baseline": "DIV-fix0f",
  "scope": "real-parent / FU / fullcore / application",
  "source_commit": "40 hex or NOT_TESTED",
  "source_snapshot_manifest_sha256": "64 hex or NOT_TESTED",
  "contract_path": "team/optimizations/.../CONTRACT.md",
  "contract_sha256": "64 hex",
  "configuration": {},
  "input_identities": {
    "emu_sha256": "NOT_TESTED",
    "nemu_sha256": "NOT_TESTED",
    "images_manifest_sha256": "NOT_TESTED",
    "toolchain_manifest_sha256": "NOT_TESTED",
    "library_sha256": "NOT_TESTED"
  },
  "execution": {
    "started_at": "ISO8601 with UTC offset",
    "finished_at": "ISO8601 with UTC offset",
    "commands_path": "evidence/.../commands.json",
    "exit_codes": [],
    "new_runs": 0,
    "reused_runs": 0
  },
  "verification": {
    "fu": "NOT_TESTED",
    "real_parent": "NOT_TESTED",
    "fullcore_difftest": "NOT_TESTED",
    "cycles": "NOT_TESTED",
    "area_sta": "NOT_TESTED",
    "power": "NOT_TESTED"
  },
  "statistics": {
    "aggregation": "mean / median / paired median / raw",
    "measured_windows": 0,
    "replay_windows": 0,
    "samples_path": "NOT_TESTED"
  },
  "metrics": [],
  "decision": "NOT_TESTED",
  "limitations": [],
  "evidence_manifest": "path + SHA256"
}
~~~

上述 0 是空模板中的计数占位，不是候选测量值；实际数据记录中的未测指标一律使用 NOT_TESTED。不要为了“填满每版”重复启动已完成的实验，也不要将旧版 PASS 自动继承给新候选。

## 9. C2-cost-20261025-01：同约束真实父级成本筛选

这是 C2-local 后新增的独立成本记录；旧轮当时的面积/STA、全核和周期 NOT_TESTED 保留。

候选 6704ce3502a7235cdb81697638c01ed23f6914f6；对照 0f12df675378556670afd0dd2153f47fcb330610。完整生产 CommonParentCostTop / VFEX4，O2 弹性和融合输入开启，O1/trace 关闭，TE=0。沿用第 5 节同一参考库、工具、综合及五档约束。

新执行 1 次父级综合、5 次标准 STA、两边共 10 次控制专项 STA；结果 **C2_SCREEN_REJECT**，45 项中 20 项通过、25 项失败。

| 指标 | fix0f | C2 | 变化 / 门槛 |
| --- | ---: | ---: | --- |
| 父级单元面积和 | 284614.946 | 284496.310 | -0.041683%；上限 284899.560946 |
| 父级 DFF | 17172 | 17170 | 实际映射 |
| nominal 控制 D 最差 ns | 1.930584 | 0.977028 | -49.392101%；上限 1.737526 |
| 未知单元 / ICG 数 | 0 / 3 | 0 / 3 | 完整生产边界 |

五档完整筛选如下。数值为 arrival / slack（ns）；arrival 上限为对照的 101%，原有正 slack 的 ICG 保持非负。icg0/1/2 是原报告查询标识，语义和起止点在 JSON 与原报告中保留。

| 档位 | 路径 | fix0f arrival / slack | C2 arrival / slack | arrival 变化 | 筛选 |
| --- | --- | ---: | ---: | ---: | --- |
| nominal | r2r | 3.261218 / -2.341112 | 3.296141 / -2.373648 | +1.070858% | FAIL |
| nominal | i2r | 3.314103 / -2.393998 | 3.338666 / -2.416173 | +0.741166% | PASS |
| nominal | vdot_r2r | 1.356106 / -0.433760 | 1.378167 / -0.455822 | +1.626790% | FAIL |
| nominal | vdot_i2r | 1.474949 / -0.549064 | 1.469347 / -0.547006 | -0.379810% | PASS |
| nominal | vdot_r2o | 2.776701 / -1.926701 | 2.959080 / -2.109080 | +6.568190% | FAIL |
| nominal | ready | 0.247821 / 0.602179 | 0.349254 / 0.500746 | +40.929945% | FAIL |
| nominal | icg0 | 1.888362 / -1.010883 | 0.505818 / 0.372885 | -73.213928% | PASS |
| nominal | icg1 | 1.128021 / -0.249725 | 0.488211 / 0.387873 | -56.719689% | PASS |
| nominal | icg2 | 0.873228 / 0.003779 | 0.945313 / -0.061260 | +8.255003% | FAIL |
| period050 | r2r | 3.261218 / -2.841112 | 3.296141 / -2.873648 | +1.070858% | FAIL |
| period050 | i2r | 3.314103 / -2.893998 | 3.338666 / -2.916173 | +0.741166% | PASS |
| period050 | vdot_r2r | 1.356106 / -0.933760 | 1.378167 / -0.955822 | +1.626790% | FAIL |
| period050 | vdot_i2r | 1.474949 / -1.049064 | 1.469347 / -1.047006 | -0.379810% | PASS |
| period050 | vdot_r2o | 2.776701 / -2.426701 | 2.959080 / -2.609080 | +6.568190% | FAIL |
| period050 | ready | 0.247821 / 0.102179 | 0.349254 / 0.000746 | +40.929945% | FAIL |
| period050 | icg0 | 1.888362 / -1.510883 | 0.505818 / -0.127115 | -73.213928% | PASS |
| period050 | icg1 | 1.128021 / -0.749725 | 0.488211 / -0.112127 | -56.719689% | PASS |
| period050 | icg2 | 0.873228 / -0.496221 | 0.945313 / -0.561261 | +8.255003% | FAIL |
| period200 | r2r | 3.261218 / -1.341112 | 3.296141 / -1.373648 | +1.070858% | FAIL |
| period200 | i2r | 3.314103 / -1.393998 | 3.338666 / -1.416173 | +0.741166% | PASS |
| period200 | vdot_r2r | 1.356106 / 0.566240 | 1.378167 / 0.544178 | +1.626790% | FAIL |
| period200 | vdot_i2r | 1.474949 / 0.450936 | 1.469347 / 0.452994 | -0.379810% | PASS |
| period200 | vdot_r2o | 2.776701 / -0.926701 | 2.959080 / -1.109080 | +6.568190% | FAIL |
| period200 | ready | 0.247821 / 1.602179 | 0.349254 / 1.500746 | +40.929945% | FAIL |
| period200 | icg0 | 1.888362 / -0.010883 | 0.505818 / 1.372885 | -73.213928% | PASS |
| period200 | icg1 | 1.128021 / 0.750275 | 0.488211 / 1.387873 | -56.719689% | PASS |
| period200 | icg2 | 0.873228 / 1.003779 | 0.945313 / 0.938739 | +8.255003% | FAIL |
| load001 | r2r | 3.261218 / -2.341112 | 3.296141 / -2.373648 | +1.070858% | FAIL |
| load001 | i2r | 3.314103 / -2.393998 | 3.338666 / -2.416173 | +0.741166% | PASS |
| load001 | vdot_r2r | 1.356106 / -0.433760 | 1.378167 / -0.455822 | +1.626790% | FAIL |
| load001 | vdot_i2r | 1.474949 / -0.549064 | 1.469347 / -0.547006 | -0.379810% | PASS |
| load001 | vdot_r2o | 2.756125 / -1.906126 | 2.938536 / -2.088536 | +6.618386% | FAIL |
| load001 | ready | 0.238594 / 0.611406 | 0.337792 / 0.512208 | +41.576066% | FAIL |
| load001 | icg0 | 1.888362 / -1.010883 | 0.505818 / 0.372885 | -73.213928% | PASS |
| load001 | icg1 | 1.128021 / -0.249725 | 0.488211 / 0.387873 | -56.719689% | PASS |
| load001 | icg2 | 0.873228 / 0.003779 | 0.945313 / -0.061260 | +8.255003% | FAIL |
| load020 | r2r | 3.261218 / -2.341112 | 3.296141 / -2.373648 | +1.070858% | FAIL |
| load020 | i2r | 3.314103 / -2.393998 | 3.338666 / -2.416173 | +0.741166% | PASS |
| load020 | vdot_r2r | 1.356106 / -0.433760 | 1.378167 / -0.455822 | +1.626790% | FAIL |
| load020 | vdot_i2r | 1.474949 / -0.549064 | 1.469347 / -0.547006 | -0.379810% | PASS |
| load020 | vdot_r2o | 2.852842 / -2.002842 | 3.035195 / -2.185195 | +6.391977% | FAIL |
| load020 | ready | 0.308999 / 0.541001 | 0.376593 / 0.473407 | +21.875152% | FAIL |
| load020 | icg0 | 1.888362 / -1.010883 | 0.505818 / 0.372885 | -73.213928% | PASS |
| load020 | icg1 | 1.128021 / -0.249725 | 0.488211 / 0.387873 | -56.719689% | PASS |
| load020 | icg2 | 0.873228 / 0.003779 | 0.945313 / -0.061260 | +8.255003% | FAIL |

全部筛选失败原因：

- nominal/r2r exceeds +1% (1.070858%)
- nominal/vdot_r2r exceeds +1% (1.626790%)
- nominal/vdot_r2o exceeds +1% (6.568190%)
- nominal/ready exceeds +1% (40.929945%)
- nominal/icg2 violates +1%/positive-slack gate
- period050/r2r exceeds +1% (1.070858%)
- period050/vdot_r2r exceeds +1% (1.626790%)
- period050/vdot_r2o exceeds +1% (6.568190%)
- period050/ready exceeds +1% (40.929945%)
- period050/icg2 violates +1%/positive-slack gate
- period200/r2r exceeds +1% (1.070858%)
- period200/vdot_r2r exceeds +1% (1.626790%)
- period200/vdot_r2o exceeds +1% (6.568190%)
- period200/ready exceeds +1% (40.929945%)
- period200/icg2 violates +1%/positive-slack gate
- load001/r2r exceeds +1% (1.070858%)
- load001/vdot_r2r exceeds +1% (1.626790%)
- load001/vdot_r2o exceeds +1% (6.618386%)
- load001/ready exceeds +1% (41.576066%)
- load001/icg2 violates +1%/positive-slack gate
- load020/r2r exceeds +1% (1.070858%)
- load020/vdot_r2r exceeds +1% (1.626790%)
- load020/vdot_r2o exceeds +1% (6.391977%)
- load020/ready exceeds +1% (21.875152%)
- load020/icg2 violates +1%/positive-slack gate

本候选未通过冻结成本合同，保留 fix0f，本候选全核与周期入口关闭。
本成本记录的新全核/NEMU、新同镜像 cycles、功耗和整核 Fmax 均为 **NOT_TESTED**。此前 C2-local 的 FU/父级资格按固定来源复用，本轮未重跑局部仿真。

这是布局前工程筛选，不是官方赛题门槛；不能把负 slack 忽略、将 arrival 倒数当整核 Fmax，或将相对改善当作已经完成 1ns 时序收敛。

[合同](../optimizations/o2/r3-div-gate/c2/cost/CONTRACT.md) · [完整结果](../optimizations/o2/r3-div-gate/c2/cost/RESULT.md) · [证据 manifest](../optimizations/o2/r3-div-gate/c2/cost/evidence/20261025-cost/manifest.json)。全部标准与专项路径、起止点和 slack 保留在 JSON 与原始报告中。

独立原文复算 C2_COST_INDEPENDENT_AUDIT_PASS、便携审计 C2_PORTABLE_COST_AUDIT_PASS、生产生成物审计 C2_COST_PRODUCTION_MODULES_PASS；审计通过确认数据与拒绝结论一致，不代表候选通过筛选。审计来源及 SHA 已追加至 JSON。

封存 manifest SHA256：d81ff41e4ae745a56172d2b75c6d85ceaa9e8f4c2fca7effc9a5e8bc4bf5d8c6。旧 18 条 JSON 记录逐字段保持，新增为第 19 条。

封存副本的 Linux 与 Windows 原生 Python 校验、数值复算均通过，均重现 20/45 通过及 C2 拒绝；没有新增全核或周期运行。完整回执见 [成本结果](../optimizations/o2/r3-div-gate/c2/cost/RESULT.md)。


## 10. C3-G0：最小改法可行性评审（2026-10-25）

记录 **C3-G0-20261025-01** 是只读设计评审与纯 Python 控制抽象运行，不是新硬件版本。建议至多一次 C3-HF 试验：从 0f 出发，只替换 FP DIV/SQRT hold 的置位条件，保持原门控公式、实际握手及全部其他状态；本轮没有实施。

新控制抽象有四组（两种概念方案×两种复位合同），每组48状态、38,400状态/输入组合、48,960后继，8种ROB初始历史；六项坏变体被拒绝，域外无有效初始化反例保留。只推荐 hold-only，未选择 gate+hold。重叠状态不相加为 RTL 覆盖率；模型 PASS 不转授新 RTL/FU/父级资格。

旧0f/C1/C2路径数字仅作为设计依据，不生成C3面积或周期数值。新RTL、真实FU/父级、面积/STA、全核/NEMU、同镜像周期和功耗均为 **NOT_TESTED**。当前保留0f，C1/C2否决保持。后续先局部正确性，再一次原约束成本筛选；失败则结束当前门控试验，成本全部通过才进入新全核/周期。

[完整评审](../optimizations/o2/r3-div-gate/c3-g0/RESULT.md) · [控制数据](../optimizations/o2/r3-div-gate/c3-g0/evidence/candidate-review/control-variants-01.json) · [证据manifest](../optimizations/o2/r3-div-gate/c3-g0/evidence/manifest.json)。

本次仅追加第20条，旧19条JSON记录与既有来源固定值逐字段保持。54份评审载荷封存，manifest SHA256：66ae381f1e2aafbed3d19a63b4b59bb7ce85c6f849279ac49d593a37e440cb8c。

## 11. C3-HF 单次最小试验：局部通过、成本否决（2026-10-25）

记录 ID：C3-HF-20261025-01。实际开始 2026-10-25T22:05:32.367527+08:00，完成 2026-10-25T22:41:41.712685+08:00。
[结果](../optimizations/o2/r3-div-gate/c3-hf/RESULT.md)、
[生产合同](../optimizations/o2/r3-div-gate/c3-hf/CONTRACT.md)、
[成本合同](../optimizations/o2/r3-div-gate/c3-hf/cost/CONTRACT.md)。
**REJECT，不采用，保留 0f，关闭当前门控试验。** 此结论不改变任何历史版本加速比。

唯一候选 77d0a1228f0da7d584d5c7375b404dcda9763cf3，ExeUnit SHA-256 150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7。
基线 0f12df675378556670afd0dd2153f47fcb330610。仅 FP DIV/SQRT hold SET 从真实 fire 改为 P_F；
两个 hold、divBusy、ROB、原 ICG.E 公式、实际接受协议、整数和 VDot 保持。
该单点试验不构成 C1/C2 完整两因素归因，亦未实施 gate＋hold 更大改法。

### 11.1 本轮实际局部验证

| 层级 | 实际结果 |
| --- | --- |
| 主机检查 | 49 父级＋2 FU，共 51 项通过 |
| FU | 22 定向＋10,000 随机，完整 128 位结果；31,499 拍，4 个坏观察被拒绝 |
| 原真实父级 | 13 组、35,075 拍；16 个坏观察被拒绝；本轮严格轨迹重放通过 |
| 补充父级 | 115 场景、6 组、2,959 拍；7 个坏观察被拒绝；实际完成 attempt 为 supplement-02 |
| C3 hold 观察 | 2,958 拍有效初始化域内 P_F＝实际 FP fire；FP/INT hold 符合原 fire 递推；9 个坏观察被拒绝 |
| 实际观察覆盖 | 143 次 FP 接受、15 次普通 SQRT、54 次取消、291 拍 FP 反压、20 个 TE0 复位场景／40 拍复位 |
| 取消后关钟 | 54 窗口、162 个立即空闲采样；0 多余时钟 |
| 独立局部审计 | C3_HF_LOCAL_INDEPENDENT_AUDIT_PASS，1103 个输入、126 依赖 |
| 全核/NEMU、周期、功耗、整核 Fmax | NOT_TESTED |

4＋16＋7＋9 是运行时/离线坏观察拒错，非 RTL 变异；观察覆盖存在重叠，不能累计为唯一覆盖率。
旧 C3-G0 抽象论证只复用，没有重复计入本轮 RTL 验证。
supplement-01 的测试观察器编译宽度告警失败保留，修正测试表达式后新 supplement-02 通过；
未把基础设施失败伪装成候选通过，也未修改生产 RTL 以绕过门禁。
保持位观察结论限定于测试顶层实际采样的有效同步 bootstrap 域，不是异步物理复位签核。

### 11.2 同约束成本和三状态 D

采用相同 CommonParentCostTop/MinimalConfig(1)、Nangate45 typical 25°C/1.1V、
Yosys 0.9／ABC 1.01／OpenSTA 2.0.17。ABC -D 1000 ps；BUF_X1 输入驱动、
理想时钟、5K_hvratio_1_1 wireload、uncertainty/transition 各 0.05 ns、I/O delay 0.1 ns、TE=0。
五档为 nominal(1 ns,5 fF)、period050(0.5 ns,5 fF)、period200(2 ns,5 fF)、
load001(1 ns,1 fF)、load020(1 ns,20 fF)。
实际一次新生产生成、一次综合、五档常规 STA、两边各五档定向 STA；
无第二候选、映射挑选或阈值放宽。

| 指标 | 0f | C3-HF | 冻结门槛与判定 |
| --- | --- | --- | --- |
| 父级参考库单元面积和 | 284614.946 | 285138.966 | +0.184115%；上限 284899.560946，FAIL |
| 父级 DFF | 17172 | 17171 | 实际映射，非预设数量 |
| 最差控制 D / ns | 1.930584 | 1.609770 | -16.617459%；上限 1.737526，PASS |
| ICG / 未知单元 | 3 / 0 | 3 / 0 | 完整生产边界 |
| 五档全部路径 | 45 项 | 20 PASS / 25 FAIL | 任一失败即否决 |

| 控制 D 端 | 0f (ns) | C3-HF (ns) | 变化 |
| --- | --- | --- | --- |
| divBusy | 0.870094 | 0.859954 | -1.165391% |
| FP hold | 1.930584 | 0.557445 | -71.125577% |
| INT hold | 1.506153 | 1.609770 | +6.879580% |

两边均绑定 divBusy、FP hold、INT hold 三个不同 DFF 的 D。FP hold 显著缩短至 0.557445 ns，
但当前最差已转为 INT hold 1.609770 ns；不能只展示有利的 FP 单点。
配套 JSON 保留三状态全部五档 arrival、slack、实际起止点与语义到 D 引脚映射。

### 11.3 五档 45 项完整比较

每项 arrival 最多比同档 0f 增加 1%；基线非负的 ICG slack 仍须非负。
这是本项目冻结筛选合同，并非官方比赛阈值；相对 PASS 不表示绝对时序收敛。

| 档位 | 路径 | 0f arrival / slack (ns) | C3-HF arrival / slack (ns) | arrival 变化 | 筛选 |
| --- | --- | --- | --- | --- | --- |
| nominal | r2r | 3.261218 / -2.341112 | 3.229321 / -2.305008 | -0.978070% | PASS |
| nominal | i2r | 3.314103 / -2.393998 | 3.283447 / -2.360285 | -0.925017% | PASS |
| nominal | vdot_r2r | 1.356106 / -0.433760 | 1.318106 / -0.395290 | -2.802141% | PASS |
| nominal | vdot_i2r | 1.474949 / -0.549064 | 1.566019 / -0.643681 | +6.174451% | FAIL |
| nominal | vdot_r2o | 2.776701 / -1.926701 | 2.852312 / -2.002312 | +2.723052% | FAIL |
| nominal | ready | 0.247821 / 0.602179 | 0.268650 / 0.581350 | +8.404857% | FAIL |
| nominal | icg0 | 1.888362 / -1.010883 | 1.975078 / -1.096782 | +4.592128% | FAIL |
| nominal | icg1 | 1.128021 / -0.249725 | 1.262832 / -0.384536 | +11.951107% | FAIL |
| nominal | icg2 | 0.873228 / 0.003779 | 0.874722 / 0.002292 | +0.171089% | PASS |
| period050 | r2r | 3.261218 / -2.841112 | 3.229321 / -2.805008 | -0.978070% | PASS |
| period050 | i2r | 3.314103 / -2.893998 | 3.283447 / -2.860285 | -0.925017% | PASS |
| period050 | vdot_r2r | 1.356106 / -0.933760 | 1.318106 / -0.895290 | -2.802141% | PASS |
| period050 | vdot_i2r | 1.474949 / -1.049064 | 1.566019 / -1.143681 | +6.174451% | FAIL |
| period050 | vdot_r2o | 2.776701 / -2.426701 | 2.852312 / -2.502312 | +2.723052% | FAIL |
| period050 | ready | 0.247821 / 0.102179 | 0.268650 / 0.081350 | +8.404857% | FAIL |
| period050 | icg0 | 1.888362 / -1.510883 | 1.975078 / -1.596782 | +4.592128% | FAIL |
| period050 | icg1 | 1.128021 / -0.749725 | 1.262832 / -0.884536 | +11.951107% | FAIL |
| period050 | icg2 | 0.873228 / -0.496221 | 0.874722 / -0.497708 | +0.171089% | PASS |
| period200 | r2r | 3.261218 / -1.341112 | 3.229321 / -1.305008 | -0.978070% | PASS |
| period200 | i2r | 3.314103 / -1.393998 | 3.283447 / -1.360285 | -0.925017% | PASS |
| period200 | vdot_r2r | 1.356106 / 0.566240 | 1.318106 / 0.604711 | -2.802141% | PASS |
| period200 | vdot_i2r | 1.474949 / 0.450936 | 1.566019 / 0.356319 | +6.174451% | FAIL |
| period200 | vdot_r2o | 2.776701 / -0.926701 | 2.852312 / -1.002312 | +2.723052% | FAIL |
| period200 | ready | 0.247821 / 1.602179 | 0.268650 / 1.581350 | +8.404857% | FAIL |
| period200 | icg0 | 1.888362 / -0.010883 | 1.975078 / -0.096782 | +4.592128% | FAIL |
| period200 | icg1 | 1.128021 / 0.750275 | 1.262832 / 0.615464 | +11.951107% | FAIL |
| period200 | icg2 | 0.873228 / 1.003779 | 0.874722 / 1.002292 | +0.171089% | PASS |
| load001 | r2r | 3.261218 / -2.341112 | 3.229321 / -2.305008 | -0.978070% | PASS |
| load001 | i2r | 3.314103 / -2.393998 | 3.283447 / -2.360285 | -0.925017% | PASS |
| load001 | vdot_r2r | 1.356106 / -0.433760 | 1.318106 / -0.395290 | -2.802141% | PASS |
| load001 | vdot_i2r | 1.474949 / -0.549064 | 1.566019 / -0.643681 | +6.174451% | FAIL |
| load001 | vdot_r2o | 2.756125 / -1.906126 | 2.831839 / -1.981839 | +2.747118% | FAIL |
| load001 | ready | 0.238594 / 0.611406 | 0.259698 / 0.590302 | +8.845151% | FAIL |
| load001 | icg0 | 1.888362 / -1.010883 | 1.975078 / -1.096782 | +4.592128% | FAIL |
| load001 | icg1 | 1.128021 / -0.249725 | 1.262832 / -0.384536 | +11.951107% | FAIL |
| load001 | icg2 | 0.873228 / 0.003779 | 0.874722 / 0.002292 | +0.171089% | PASS |
| load020 | r2r | 3.261218 / -2.341112 | 3.229321 / -2.305008 | -0.978070% | PASS |
| load020 | i2r | 3.314103 / -2.393998 | 3.283447 / -2.360285 | -0.925017% | PASS |
| load020 | vdot_r2r | 1.356106 / -0.433760 | 1.318106 / -0.395290 | -2.802141% | PASS |
| load020 | vdot_i2r | 1.474949 / -0.549064 | 1.566019 / -0.643681 | +6.174451% | FAIL |
| load020 | vdot_r2o | 2.852842 / -2.002842 | 2.928424 / -2.078424 | +2.649358% | FAIL |
| load020 | ready | 0.308999 / 0.541001 | 0.339873 / 0.510127 | +9.991618% | FAIL |
| load020 | icg0 | 1.888362 / -1.010883 | 1.975078 / -1.096782 | +4.592128% | FAIL |
| load020 | icg1 | 1.128021 / -0.249725 | 1.262832 / -0.384536 | +11.951107% | FAIL |
| load020 | icg2 | 0.873228 / 0.003779 | 0.874722 / 0.002292 | +0.171089% | PASS |

失败为面积 1 项，以及 VDot i2r、VDot r2o、ready、FP ICG.E、INT ICG.E
五类路径在五档中的 25 项；完整失败文本和实际起止点见配套 JSON。
原文独立成本审计 C3_HF_COST_INDEPENDENT_AUDIT_PASS，857 输入不变，
表明数据有效，**不表示候选通过成本筛选**。
父级 r2r 虽下降至 3.229321 ns，仍有负 slack；不得以其倒数冒充整核 Fmax。
完整父级 ABC 重映射可影响源码未改模块的路径；此数据不证明某一个布尔项是全部变化的唯一原因。

### 11.4 身份、原文与停止边界

[封存 manifest](../optimizations/o2/r3-div-gate/c3-hf/evidence/20261025-trial/manifest.json)
SHA-256：d59cb0ebaec8209a8683ce3b3f97fafabc4daedbd50e0a2e0f36caf948d3ce31。载荷 1131 份，包含实际新结果、局部/成本审计、
冻结输入、工具与二进制身份、原文路径和失败记录；压缩文件按 manifest 的 raw/stored 双 SHA 读取。
本台账将新来源仅追加到 c3_hf_source_pins／c3_hf_sources，旧 20 条及旧来源保持。

C3-HF 新 EMU、NEMU 差分、性能镜像及同镜像周期均 NOT_TESTED。保留 0f EMU
2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8，不能把它授予新候选。
本轮不产生新的加速比、功耗或比赛分数结论；当前门控支线结束，回到保留主线的稳定集成与 T17 干净复现。

## 12. 固定 0f 硬件上的 firstdot V2 组合验证（2026-10-26～27）

记录 ID：`FIRSTDOT-V2-DIVFIX0F-20261026-01`。本轮选择性引入 zufan 的 T17 工具与 firstdot V2，使用当前 O2＋H1＋DIV 取消关钟修复 0f 硬件实测。联合原文审计实际返回 0，状态为 **CURRENT_FIRSTDOT_CONTINUATION_FUNCTIONAL_CYCLES_AUDIT_PASS_WALL_CLOCK_LIMITED**。功能与 DUT 周期通过；**墙钟时间线 FAIL 单独保留**，不将其改写为完整无条件 PASS。干净复现、配置复用及新面积/时序仍为 NOT_TESTED。

### 12.1 公平比较口径及全部形状结果

相同 0f 模拟器、输入和观察器；S1/firstdot 两个软件版本使用成对固定布局与完整 RVV 代码槽。BIN 随软件变化，不能称为同镜像硬件消融。比较覆盖 4 形状 × 3 数据集 × S1/firstdot × basic/reuse × vdot/RVV。下表为包含 C ABI 调用/返回的 reuse 窗口算术均值，每项 12 个正式窗口（3 数据集 × repeat 2～5）；不扣除计时成本。最快 RVV 从全部四种 RVV 组合中选择，未采用较慢分母。JSON 保留每种形状的全部 8 个候选及精确值。

| 形状 | S1 reuse vdot cycles | firstdot reuse vdot cycles | 最快纳入 RVV cycles | 相比 S1 周期减少 | 相比最快 RVV 周期减少 | RVV/firstdot 加速比 | 当前组合选择 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 4×8 | 169.75 | 157.75 | 187.50 | 7.0692% | 15.8667% | 1.1886× | firstdot reuse vdot |
| 8×32 | 292.50 | 282.25 | 300.75 | 3.5043% | 6.1513% | 1.0655× | firstdot reuse vdot |
| 16×64 | 717.25 | 707.00 | 778.75 | 1.4291% | 9.2135% | 1.1015× | firstdot reuse vdot |
| 4×13 | 219.75 | 204.50 | 187.00 | 6.9397% | -9.3583% | 0.9144× | firstdot reuse RVV |

4×8、8×32、16×64 的 reuse vdot 分别减少 12、10.25、10.25 cycles；窗口退休指令分别为 54→44、202→182、672→632。4×13 的 firstdot vdot 虽比 S1 vdot 减少 15.25 cycles，仍比最快 RVV 多 17.5 cycles，即慢 9.3583%，因此保留 firstdot reuse RVV 回退。此形状 S1/firstdot reuse RVV 同为 187 cycles，并列最快。以上为本合同的应用窗口收益，不产生新的 RTL、整核 Fmax、功耗或比赛分数结论。

这四项选择已获得当前软硬件组合的原文资格；公共 stable 默认入口未切换，仍需干净复现完成后再决定默认集成。

### 12.2 运行数量与功能证据

| 项目 | 实测记录及本轮审计 |
| --- | --- |
| EMU 实际启动 | **38 次**：矩阵 34、普通 C 4 |
| 合格完成 / 中断 | **36 / 2**：矩阵 33 / 1，普通 C 3 / 1 |
| 续跑关系 | 新增 23 次；保留同轮已合格 13 次；原先实际启动 15 次中含 2 次中断 |
| 正式 / 重放窗口 | **384 / 192**；连同 first/warmup 共 768 个正常窗口 |
| 普通 C ABI | **16 个公共函数、48 个不同 case、96 次完整正常调用** |
| 全 128 位结果、NEMU 差分 | PASS |
| CSR 窗口与 O2 生命周期 | PASS |
| 高位负控及恢复 | PASS；firstdot 目的 v0 的 bit100 故障被拒绝，正常版本恢复 |
| 原文周期复算 | PASS；384 个正式样本身份、cycles/instructions 与留档逐条一致，32 个候选聚合重新核对 |
| 审计本身新增 EMU / NEMU | **0 / 0** |

两个中断记录和 null 退出码原样保留，不计入合格窗口与 96 次调用。已完成的负控没有重跑；同轮续跑不借用队友历史硬件 PASS。计数不能只写 36 而隐藏两次中断启动。

### 12.3 墙钟时间线失败与证据边界

| 验收维度 | 结果 |
| --- | --- |
| 功能与 DUT 周期原文检查 | PASS |
| 冻结同步控制流与回执支持的因果串行顺序 | PASS |
| 严格 UTC 墙钟时间线 | **FAIL** |
| 直接单调时钟记录 | NOT_RECORDED |
| 墙钟回退原因 | UNCONFIRMED |

旧矩阵 `formal-performance-s1-d0-s01` 的 finished 为 `2026-10-26T07:07:55.796377+00:00`，
随后 `formal-performance-s1-d1-s01` 的 started 为 `2026-10-26T07:07:55.252896+00:00`，
出现 **0.543481 秒**回退。两条原始 result 哈希、完整时间值和源码/回执绑定见配套 JSON 的 chronology。

冻结路径按同步 `Popen → wait → 校验 → finished/写盘 → 下一次 launch` 执行，控制器完成日志也保持该顺序；started/finished 来自 `datetime.now(timezone.utc)`，没有 monotonic 时间线。故此证据支持串行生命周期，不能独立证明精确主机时间间隔；不推测 NTP 或 WSL 时钟调整原因。并行的独立 C 运行也不能用来解释时钟回退。

DUT/CSR cycles 不由主机 UTC 相减得到，故功能/周期原文资格与此墙钟失败分开记录。原时间值未改、记录未重排、未设置容差。第一次审计工具导入失败及随后 v1 严格 chronology 检查失败均保留；v2 显式使用墙钟受限合同，没有将旧合同的 FAIL 改成 PASS。

### 12.4 硬件、软件、配置与证据身份

- 实际硬件构建源：`0f12df675378556670afd0dd2153f47fcb330610`。
- EMU SHA-256：`2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8`。
- NEMU SHA-256：`efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4`。
- firstdot/T17 选择性来源：zufan `fcf4a11fc569cb2a8fcb4e18d96ec2764b228557`，45 个文件（43 新增、2 原有相同）。
- 本地软件及工具源码提交：`c823a8786e052c6e26f6915563c42b6d730dd8e3`。这是运行后的源码提交，不是新 EMU 构建身份；提交后 25,869 项物理硬件输入复核 PASS，原 EMU 不变。
- 配置：MinimalConfig / 1 核，O2 elastic、T14 fused input 启用，O2/T13 观察开启，EMU_THREADS=1，seed=1，128MB RAM，max-cycles=2,000,000。
- JSON 内嵌 24 个矩阵镜像、普通 C 镜像、工具链、AM/klib、源清单、命令与实际进程记录的身份目录，并绑定 base、矩阵续跑、C 续跑及 v2 审计合同。

实际原文审计：
`/home/riscv/riscv-lab/software-import-20261026/reviews/resume-audit-fix-01/full-raw-audit-02/`。
封存 [manifest](/home/riscv/riscv-lab/software-import-20261026/reviews/resume-audit-fix-01/full-raw-audit-02/archive/manifest.json)
SHA-256：`b4f255c6cb81c02536f1797ee8938ab784888b4a65f90cf6b5fb5024f274d06c`。
共 1,756 份载荷，原文 966,485,449 bytes、存储 176,446,013 bytes，raw/stored 双 SHA 校验通过。
此封存仍依赖原外部构建输入才能重新进行原文审计；**不宣称独立可移植复算或干净复现完成**。

### 12.5 未测事项及干净复现尝试

本条的独立干净复现、配置复用、FU/父级重跑、新面积/STA、功耗和成员人工复现均 **NOT_TESTED**。生产 RTL 和公共 stable 默认入口不变；本轮未推送 GitHub。

单独的 `clean-01` 已尝试新构建，但返回 2、未生成新 EMU。其 Mill Git 历史查询报 `Could not read e524aeedab50586b2dbc86a2180380085c43a4cd`；linked worktree 本地克隆未保留真实浅克隆边界的构建准备问题另行修复。失败状态保留于
[clean-01/build/build-state.json](/home/riscv/riscv-lab/software-import-20261026/clean-01/build/build-state.json)，
不把构建失败算作当前已完成组合的功能/性能失败，也不给予干净复现资格。后续使用新的干净目录继续，完成后追加新的实测记录；再开展配置复用筛选。

本节与配套 JSON 为追加第 22 条记录，原 21 条历史记录及原来源内容保留。

## 13. 同机干净复现完成：CLEAN-FIRSTDOT-V2-DIVFIX0F-20261027-01

第23条记录。沿用0f硬件（O2＋H1＋DIV取消修复），软件/工具源码c823a；独立检出并重新构建NEMU、EMU、AM/klib和应用。保留本机已装工具及下载缓存，不等同新机器人工复现。

- 实际启动并结束53个目标进程，选用50个：全核14、矩阵33、新C3。原C3个功能通过但外层时间校验失败，保留并排除；无中断。49次exit0、4次预期负控exit1。
- 新旧25个应用镜像BIN/ELF装载段一致；768个完整窗口逐项一致；16公共函数、48case、96次C调用输出一致。联合原文审计通过。
- 全核117个不同功能case/124次执行及O2覆盖通过。宿主UTC曾推导出80.119ms重叠，墙钟容量仍FAIL；源码线程池上限3的证据PASS，未实测OS单调时钟并发。不能据此宣称宿主运行耗时或频率改善。
- 原C回执2.455386s时间异常及clean-01构建失败均留档；仅另跑3个C进程，未放宽C检查器，run02严格验收PASS。

| 形状 | S1 reuse vdot | firstdot reuse vdot | 最快同口径RVV | firstdot较S1减少 | RVV/firstdot |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4×8 | 169.75 | 157.75 | 187.50 | 7.0692% | 1.1886× |
| 8×32 | 292.50 | 282.25 | 300.75 | 3.5043% | 1.0655× |
| 16×64 | 717.25 | 707.00 | 778.75 | 1.4291% | 1.1015× |
| 4×13 | 219.75 | 204.50 | 187.00 | 6.9397% | 0.9144× |

单位cycles，包含C ABI调用/返回，3数据集每格12个正式样本。4×13继续RVV回退。公共stable默认入口未切换；配置复用另项筛选。新面积/STA/功耗、单独FU/父级重跑、成员人工验收均NOT_TESTED。

新EMU SHA-256: acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9。

新NEMU SHA-256: 62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca。

本地根：/home/riscv/riscv-lab/software-import-20261026/clean-02。完整结果full-reproduction-comparison-03.json，联合审计combination-audit-03。全部版本、命令、镜像、失败和manifest哈希见配套JSON本条。全核封存manifest为a80a1063…，联合封存eba6744d…，编排补充封存5798eb25…；后者包含152文件且已双SHA回读，不替代原文资格。原始档案依赖本地外部物理输入，不声称单独档案即可重建。

## 14. 配置复用有界筛选：CONFIG-REUSE-DIVFIX0F-CLEAN02-20261027-01

第24条。结果：**PERFORMANCE_CANDIDATE**；功能与原文复算PASS。限定8×32/dataset0/C ABI完整调用窗，每格4正式样本。候选BIN不同，硬件、数据、布局和调用计划相同；不称同完整镜像比较。

| 方法 | firstdot平均cycles | 配置复用平均cycles | 退休指令(firstdot→配置复用) |
| --- | ---: | ---: | --- |
| basic vdot | 645.50 | 643.75 | [276] → [267] |
| reuse vdot | 282.25 | 273.00 | [182] → [175] |
| basic rvv | 356.00 | 356.00 | [180] → [180] |
| reuse rvv | 300.75 | 299.00 | [124] → [123] |

reuse vdot相对firstdot减少3.277236%；相对本次最快RVV减少8.695652%，RVV/vdot=1.095238×。
未解释对照项：[]。功能与性能结论分开；决策：KEEP_FOR_EXPANDED_VALIDATION_ONLY，本次不扩大矩阵、不切stable默认、不推送。

实际7个目标进程：V2的2个保留并排除，V3新5个功能通过；5次正常exit0、2次预期负控exit1。选用V3的32正式窗口、含重放96窗口、48对全窗口重放（一致=True）；firstdot24窗口与原干净合格对照一致=True。高位bit100拒错及正常恢复、NEMU完整128位结果、CSR与O2生命周期均PASS。

V2停止原因是对照BIN被工具误作实际加载BIN，正常目标exit0且UART failures=0，不能因此把原失败验收改为PASS。V3只修复测试适配层，保留共享对照哈希校验；61项主机检查PASS，含真实旧日志失败复现及错误镜像/篡改拒绝。原失败原样封存。

V3首次独立审计又因循环变量遮蔽物理身份而误报；原失败保留。独立新审计器仅重命名两个循环变量，真实完整批次成功及模拟最终身份漂移仍拒绝两项检查PASS。新audit-02及completion-02通过，全程不新增EMU；冻结运行源码和旧日志不改。

候选来源zufan fcf4a11的26文件＋39相同依赖；新适配器V3及执行器独立绑定。生产RTL仍0f；全核默认选择未变。新多形状/多数据集矩阵、普通公共C应用、面积/STA/功耗、成员人工复现均NOT_TESTED。4×13继续RVV回退。

本地原始输出：/home/riscv/riscv-lab/software-import-20261026/config-reuse-clean02-02。封存manifest：d5cbde2b37239214c6632b891dd61d94f9483cb45b51b7cacedd293e6a898bd5；原文审计及所有版本/镜像/配置/命令/实测数值见配套JSON。档案验证仅为字节封存，原文复算仍依赖本地物理输入。


## 15. 配置复用四尺寸、三数据集扩展（第25条）


本轮在当前 O2 + H1 + DIV 取消保持修复（0f）硬件上，比较 firstdot 与配置复用软件。24 个新镜像、33 个新目标进程已完成；功能、全128位结果、NEMU差分及原文审计通过。各尺寸的性能采用结论见下表，稳定入口尚未切换。

### 比较口径

- 尺寸为矩阵 M×K，分别为4×8、8×32、16×64、4×13；输入为有符号INT8，K=13保留真实尾部处理成本。
- dataset0覆盖INT8极值、正负和零；dataset1为固定模运算序列；dataset2为固定种子的随机数据。
- 完整C ABI调用窗口包含调用/返回、配置、装载、计算和存储，不扣空测开销。相同硬件、数据、布局和计划，软件BIN不同。
- 每个尺寸的每个比较格含12个正式样本（3组数据各4次）。同时保留首次/预热以及dataset0独立重放。
- 比较对象包含firstdot/config-reuse × basic/reuse × vdot/RVV八格；RVV分母使用本轮最快的合格格。

### 各尺寸结果

| 尺寸 | firstdot reuse vdot cycles | 配置复用 reuse vdot cycles | 最快RVV cycles | 比firstdot减少 | RVV/vdot | 判定 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4x8 | 157.7500 | 153.0000 | 185.0000 | 3.0111% | 1.209150x | INCONCLUSIVE |
| 8x32 | 282.2500 | 273.0000 | 299.0000 | 3.2772% | 1.095238x | PERFORMANCE_CANDIDATE |
| 16x64 | 707.0000 | 702.7500 | 773.0000 | 0.6011% | 1.099964x | INCONCLUSIVE |
| 4x13 | 204.5000 | 205.5000 | 187.0000 | -0.4890% | 0.909976x | INCONCLUSIVE |

cycles为完整调用窗口的正式均值。PERFORMANCE_CANDIDATE要求聚合及每组数据均严格快于firstdot和最快RVV，同时无未解释控制漂移或其他格退化；REJECT与INCONCLUSIVE均保留原始数据。

### 逐数据集

下表只列逐组的局部指标判定；最终采用还受完整控制窗口与重放门禁约束，以上表总体判定为准。

| 尺寸 | 数据集 | firstdot cycles | 配置复用 cycles | 最快RVV cycles | RVV/vdot | 局部指标判定 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 4x8 | 0 | 157.7500 | 153.0000 | 185.0000 | 1.209150x | PERFORMANCE_CANDIDATE |
| 4x8 | 1 | 157.7500 | 153.0000 | 185.0000 | 1.209150x | PERFORMANCE_CANDIDATE |
| 4x8 | 2 | 157.7500 | 153.0000 | 185.0000 | 1.209150x | PERFORMANCE_CANDIDATE |
| 8x32 | 0 | 282.2500 | 273.0000 | 299.0000 | 1.095238x | PERFORMANCE_CANDIDATE |
| 8x32 | 1 | 282.2500 | 273.0000 | 299.0000 | 1.095238x | PERFORMANCE_CANDIDATE |
| 8x32 | 2 | 282.2500 | 273.0000 | 299.0000 | 1.095238x | PERFORMANCE_CANDIDATE |
| 16x64 | 0 | 707.0000 | 702.7500 | 773.0000 | 1.099964x | INCONCLUSIVE |
| 16x64 | 1 | 707.0000 | 702.7500 | 773.0000 | 1.099964x | INCONCLUSIVE |
| 16x64 | 2 | 707.0000 | 702.7500 | 773.0000 | 1.099964x | INCONCLUSIVE |
| 4x13 | 0 | 204.5000 | 205.5000 | 187.0000 | 0.909976x | INCONCLUSIVE |
| 4x13 | 1 | 204.5000 | 205.5000 | 187.0000 | 0.909976x | INCONCLUSIVE |
| 4x13 | 2 | 204.5000 | 205.5000 | 187.0000 | 0.909976x | INCONCLUSIVE |

### 控制差异与采用判断

- **8×32：保留性能候选。** 三组数据均为282.25→273 cycles，较firstdot少3.2772%，相对本轮最快RVV为1.095238×；控制窗口、同版本重放均一致。
- **4×8：保留收益信号，暂待归因。** 主项157.75→153 cycles；未改动basic RVV的正式均值仍为225.25，但部分首轮/正式窗口有±1周期变化。总体判定为INCONCLUSIVE，不能以平均相同替代逐窗门禁。
- **16×64：暂待归因。** 主项707→702.75 cycles，仅少0.6011%；未改动basic RVV的均值990→991，六窗记录也变化。总体判定为INCONCLUSIVE。
- **4×13：本轮不采用该候选，保留较优RVV。** 主项204.5→205.5 cycles，慢0.4890%，且慢于最快RVV的187 cycles；basic vdot与reuse RVV也有配对退化、未改RVV窗口存在差异。合同总体标记为INCONCLUSIVE，完整原因列表保存在record.json。

这些差异出现在已通过功能和NEMU差分的运行中。12个firstdot同BIN对照的288个完整样本与干净基线一致，8次同版本独立重放也一致；跨软件变体的控制周期变化因此仍需单独归因。本轮不修改门禁、不补跑到出现更好的结果，也不把静态少指令直接等同于性能收益。

### 验证与留档

24个镜像GNU/布局/再生检查通过，12个firstdot对照BIN及ELF装载内容与干净版本一致。实际启动33次：32次正常退出、1次预期bit100负控失败，随后同BIN恢复正常。新轮次未借用旧探针运行。
原文审计复核768个正常窗口，其中384个正式窗口；192个重放窗口对、288个firstdot历史同BIN对照窗口分别核对完整sample字典。重放一致性：True。
并发使用4个CPU，按同boot的单调时钟Popen/wait包络与阶段屏障检查；峰值：4。该包络不表示精确操作系统调度重叠。

92项主机测试通过。此前JSON键类型问题在主机组合测试中发现并修复；第一次启动因测试文件仍更新被源码锁拒绝，未构建或启动EMU，该失败回执保留。
原始证据归档逐文件回读通过：1841项，manifest SHA256：be8e45af31040e5a96c9b947587a02b1ef854aa2a0cf1014f4f7d6d05f4394c6。这不是新的便携环境重建。
固定版本、配置、24个镜像哈希、33个进程身份、全部32个比较格和逐数据集判定保存在record.json。

### 当前选择与下一步

本轮只完成数据集与尺寸扩展；生产RTL、默认入口和GitHub未改动。普通公共C应用路径尚未为配置复用版新增验证，面积/STA/功耗也没有新测量。
8×32优先补普通公共C调用路径验证；4×8和16×64先做只读控制差异归因，4×13保留既有较优RVV路径。相关门禁闭合后再考虑稳定入口。
只读复核确认12个firstdot镜像的288个完整样本与干净基线一致；15个未改动RVV控制格的完整8 KiB槽位逐字节相等。4×8、16×64、4×13的部分控制窗仍有周期差异，其微架构原因尚未确认，不能把它们当作噪声删除或放宽门禁。

原始工作目录：/home/riscv/riscv-lab/software-import-20261026/config-reuse-expanded-01

完整数据档案记录ID：CONFIG-REUSE-MATRIX-DIVFIX0F-CLEAN02-20261027-01


## 16. 8×32配置复用普通C调用（第26条）


当前 O2＋H1＋DIV 取消保持修复（0f）硬件上，**8×32 配置复用普通 C 调用验证通过**。本轮补齐实际 C ABI 调用的正确性、拒错、恢复和重放证据，未修改生产 RTL或稳定默认入口，未上传 GitHub。

### 本轮验证了什么

| 项目 | 实测结果 |
| --- | --- |
| 8×32 范围 | 4 个公共函数（basic/reuse × vdot/RVV）× 3 数据集，12 个不同用例；两轮正常运行共 24 次调用 |
| 完整夹具 | 保留 16 函数、48 不同用例；两轮共 96 次正常调用，全部通过 |
| 全宽结果 | 每行低 32 位 INT32 点积与标量模型一致，高 96 位清零；逐字节检查 |
| 边界与状态 | 输入不变、前后 canary、未用输出行及向量 CSR 检查通过；5 种软件错误自检全部检出 |
| 差分拒错 | 在8×32 reuse vdot内注入 vd0 的bit100错误，唯一mismatch被拒绝；同BIN恢复与独立重放通过 |
| O2 观察器 | 两轮均完整闭合；每轮1008次自定义提交，其中8×32为192次，无残留事务 |
| 机器码对应 | 16公共函数与此前12个配置复用矩阵单元逐字节匹配，共48次比较；8×32占12次 |
| 主机与原文审计 | 20项主机检查通过；GNU/ELF、原始UART/O2日志、版本/镜像/工具身份复核通过 |

### 真实运行与输入身份

- 新目标进程共3个，严格串行：1个预期拒错exit1、2个正常exit0；无中断。命令起止：2026-10-27T20:05:30.496475+08:00 至 2026-10-27T20:49:03.394487+08:00。
- 同一个C程序BIN：56805506eb98b68269c73a3645d8f75dff73b697e30dec5f93ccc4716089ad34。
- 实际注入PC：0x80000d64，指令字0x0388000b；不是复用性能探针的PC。
- 软件源码基点：c823a8786e052c6e26f6915563c42b6d730dd8e3；硬件：0f12df675378556670afd0dd2153f47fcb330610。
- EMU SHA256：acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9；NEMU SHA256：62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca。
- MinimalConfig、单核、EMU_THREADS=1、VLEN128；guest上限2,000,000 cycles、seed1、128MB RAM；每个进程外部超时7200秒，CPU亲和0–3。
- 保留原C检查器的严格UTC顺序验收，另用同boot单调Popen/wait包络与真实PID核对串行。包络不等于精确OS调度时刻。
- 普通C主程序和Makefile保持冻结原文。仅将48条调用表稳定排序，把8×32/dataset0/reuse/vdot放首项；输入数据及完整case多重集合不变，以保证负控命中目标函数。

### 如何使用这个公共函数

本次使用Nexus-AM裸机C程序，接口为普通RV64 lp64d双指针ABI；实际测试经C函数指针调用。该资格不扩展为Linux用户态运行或完整LLM推理验收。

~~~c
void config_reuse_gemv_8x32_reuse_vdot(const int8_t *packed_ax, void *output_slots);
~~~

输入为行优先8×32有符号INT8矩阵A，紧接32项向量x，共288字节。输入和输出各自16字节对齐、互不重叠。输出为8个16字节槽，共128字节；每槽低4字节是INT32结果，高12字节为零，不能按连续8个int32_t读取。环境须启用向量状态，并支持VLEN128及当前自定义vdot编码；函数会覆盖允许的向量/调用者状态。
实际构建源、头文件和C调用程序保存在qualified-public及仓库精简材料public目录。静态库、dispatcher和默认入口未在本轮新增。

### 性能结论的边界

两次正确性程序的整程序计数（含启动、标量检查、UART，不是点积性能窗口）：recovery: 871322 cycles / 1062247 retired instructions；replay: 871322 cycles / 1062247 retired instructions。

本C正确性程序未采集新的性能窗口。上一轮4尺寸×3数据集矩阵中，8×32为firstdot 282.25 → 配置复用273.00 cycles，比firstdot少3.2772%；同场最快RVV为299.00 cycles，加速比1.095238×，每格12个正式样本。这些是上一轮完整调用窗口的数据，不能写成本C程序新跑出的加速比。
本次确认这些已测函数可以经普通C调用并正确工作；性能采用候选具体为8×32 reuse vdot，basic等函数只分别保留各自已有数据。4×8、16×64和4×13的性能资格不随功能通过升级；此前控制差异与K13较慢的结论继续保留。

### 失败记录与后续

首次V1运行在EMU启动前因进程包装器未接收位置参数env/timeout而失败，新增EMU为0。原源码、构建、回执保留；V2修复参数透传并补真实主机子进程测试，再在新目录完成本轮。未改内层冻结验证器或放宽门禁。
归档首次因固定系统编译器为符号链接而拒绝，未生成档案；新版仅对构建回执中已固定的工具链路径保存链接文本、实际目标与相同SHA，其他链接仍拒绝。原失败回执保留，无新增EMU。
下一步可评审8×32候选的稳定入口范围；4×8/16×64仍先只读归因未改RVV控制窗差异，4×13保留较优RVV。若改调用/调度/布局，须验证相应新路径，不能直接继承旧周期数。

### 留档

- 记录ID：CONFIG-REUSE-C8-DIVFIX0F-CLEAN02-20261027-02；统一数据档案第26条。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/config-reuse-c8-02
- 工具：/home/riscv/riscv-lab/software-import-20261026/reviews/config-reuse/c8-v2/c8.py
- 原文审计：/home/riscv/riscv-lab/software-import-20261026/config-reuse-c8-02/audit-01.json
- 本地归档：/home/riscv/riscv-lab/software-import-20261026/reviews/config-reuse-c8-final-archive-03/manifest.json
- 归档包含589项，manifest SHA256：0e2285d8f8b95f9126f8d1d5014de62620be242522aba1486aae515912ca2144。逐文件压缩前后SHA及回读通过；这是本地字节封存，不是独立机器复现。
- 完整版本、配置、镜像、命令、PID、退出码和失败记录保存在配套JSON。新周期、面积、STA、功耗、成员人工复现均为NOT_TESTED。


## 17. 独立8×32 C8最小软件包（第27条）

**结果：PASS，可作为独立、显式选用的 C8 静态软件包使用。** 当前软件源码基点 c823a8786e052c6e26f6915563c42b6d730dd8e3，硬件保持 0f12df675378556670afd0dd2153f47fcb330610（O2＋H1＋DIV取消保持修复）。

本轮实现 `selected_gemv_c8.h`、完整单对象库构建、调用示例、当前身份验证器和主机测试。未切换旧四尺寸默认入口，未修改生产 RTL，未提交或上传 GitHub。执行者 @cc77-builder / Agent；本地包验收不是成员人工验收。

### 实际结果

| 验收项 | 本轮结果 |
| --- | --- |
| GNU 构建 | 固定 rv64gcv/lp64d/mno-relax，独立重建完整对象与原 C8 已验证对象全字节相同 |
| 完整对象 | 27,160 bytes；SHA256 f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3 |
| 静态库 | libxs_gemv_c8.a，仅一个完整 gemv.o；ar t/p、独立归档、确定性字节一致 |
| 符号与节 | 16 个原公共函数；单一16字节对齐.text；原对象无重定位；新增运行时别名/包装函数为0 |
| 别名与链接 | 缺省、0、1及宏展开为1共4模式；两个别名的 caller.o/linked.o 与直接调用逐字节相同 |
| 实际引用 | 每模式核对2个有序指针重定位、2个调用重定位；GNU可重定位链接后未解析符号为空 |
| 错误配置拒绝 | 17项集成负控：10种非法宏、4种错误别名、错误对象、错误库、缺失头文件 |
| 旧入口共存 | V1/V2分别与C8，两个包含顺序×旧新开关0/1，共16组，选择与版本保持 |
| 搬移 | SDK移到仓库外含空格目录；默认vdot及强制RVV示例均按文档flags编译/链接通过 |
| 主机检查 | 22项unittest通过，包括错误硬件/NEMU、混合配置、缺失数据集、伪造历史C资格及改哈希后错选择拒绝 |
| 构建门禁 | 额外3项Python优化模式负控通过：旧输出、仓库内输出、错误源码仍被拒绝 |
| 原始资格 | 当前0f身份及完整输入闭包复核；原33个矩阵进程＋3个C进程重审，48次叶函数锚点通过 |
| 新目标运行 | 0 EMU、0 NEMU；新示例运行、新最终ELF、新周期、面积/STA/功耗均为NOT_TESTED |

完整验收流水线：2026-10-27T21:36:30.342114+08:00 至 2026-10-27T21:38:56.981151+08:00，exit0；115份命令回执。新包首次集成验收即通过，原始输出与预期失败负控全部保留。

### 如何选用

使用 [构建与调用说明](../optimizations/o2/integration/firstdot-v2-0f/package/c8/README.md) 和 [完整 ABI 合同](../optimizations/o2/integration/firstdot-v2-0f/package/c8/CONTRACT.md)。头文件提供：

~~~c
#include "selected_gemv_c8.h"
xs_c8_gemv_8x32(packed_ax, slots);      /* configuration reuse vdot */
xs_c8_gemv_8x32_rvv(packed_ax, slots);  /* explicit reuse RVV */
~~~

`XS_C8_GEMV_FORCE_RVV=1` 将默认入口也选为 RVV；缺省或0为vdot。仅接受最终展开为字面量0或1，切换后重编相关翻译单元。

必须是 **VLEN恰好128**、VS已启用和已验证的RV64/lp64d平台。输入为16字节对齐的288字节有符号INT8 A[8][32]||x[32]；输出是16字节对齐的8×16字节槽，共128字节，输入输出不重叠。每槽低32位为结果、高96位清零。输出不能当作紧密的 int32_t[8]。原向量状态/CSR效果保持，详见合同。

完整库仍有16个函数及未调用vdot代码；显式RVV不等于纯RVV镜像或跨平台自动检测。旧 firstdot 包与四尺寸默认均保持。

### 性能含义与下一步

本轮证明新编译期入口在被测试的调用对象和可重定位链接中没有新增包装代码，并正确复用了已验证的同一完整对象。它不是新的性能测试，也不证明任意最终应用的布局或周期都相同。

此前第25条矩阵数据继续有效：8×32配置复用273.00 cycles，firstdot282.25，最快同场RVV299.00，加速比1.095238×；每格12正式样本。本轮没有把这些数值重新标成新实测。

最小包目标已完成。下一步若接入实际应用或产生新的最终ELF，先固定新调用布局/窗口合同，再做受影响路径的全128位正确性、差分拒错/恢复与重放；性能比较须用同路径firstdot/RVV对照。纯宏别名不需要新增wrapper。如果新增wrapper、dispatcher或CSR保护，需新的控制流检查，不能借用旧唯一jal/ret门禁。其他尺寸的4×8/16×64控制漂移仍可独立只读归因，4×13保留RVV。

### 证据与工程记录

- [机器可读记录](../optimizations/o2/integration/firstdot-v2-0f/package/c8/record.json)；[GNU与静态结果](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/report.json)；[当前资格绑定](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/qualification.json)。
- [固定输入](../optimizations/o2/integration/firstdot-v2-0f/package/c8/INPUTS.json)；[原文审计/构建工具](../optimizations/o2/integration/firstdot-v2-0f/package/c8/verify_c8_package.py)；[主机测试](../optimizations/o2/integration/firstdot-v2-0f/package/c8/test_c8_package.py)。
- [矩阵原文重审](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/matrix-raw-audit.json)；[C调用原文重审](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/c8-raw-audit.json)。
- [归档索引](../optimizations/o2/integration/firstdot-v2-0f/package/c8/evidence/archive-reference.json)；`evidence/commands/`保留115份命令及文本日志，ar提取的二进制stdout保留在完整外部归档。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-package-01。
- 外部完整归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-package-final-archive-01。
- 记录ID：C8-PACKAGE-DIVFIX0F-CLEAN02-20261027-01，统一版本档案第27条。

初版Makefile烟雾测试通过后，审查发现assert可能被Python优化模式跳过，改为显式退出并验证三项门禁；修正前后材料均保留。没有降低旧运行门禁、更新旧对象哈希或覆盖历史失败。


## 18. C8接回普通C最终镜像等价（第28条）

**PASS：C8 软件包已真实接入原普通 C 夹具，最终可执行内容完全等价。** 依照事先约定，复用第26条同镜像的功能、NEMU/O2、bit100拒错、恢复与重放证据；本轮无需新增全核仿真。

执行者 @cc77-builder / Agent；操作ID 20261027-cc77-builder-c8-relink。生产RTL保持0f，旧四尺寸默认不变；未提交或上传GitHub。

### 接入内容

- 原主程序只把底层头的包含改为 `selected_gemv_c8.h`。
- 8×32 reuse vdot/RVV × 三数据集，共6个函数表项改用 `xs_c8_gemv_8x32` / `xs_c8_gemv_8x32_rvv`。其余42项、数据、期望值、顺序和校验不变，没有重新生成测试向量。
- 真正从 `libxs_gemv_c8.a(gemv.o)` 链入完整合格对象；SDK程序源目录没有gemv.S，对象目录没有绕过库的gemv.o。GNU依赖文件和link map确认实际包含SDK头、实际抽取库成员。
- 在全新输出中分别构建原源码复制对照和SDK接入程序，保留原AM/klib和链接次序；只有输出路径和记录链接来源的选项不同。

源码见 [source](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/source/)，重建和完整核验见 [README](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/README.md)。

### 三方等价结果

比较对象：原已通过全核的C8镜像 → 本轮原源码复制对照 → 本轮SDK接入版。

| 项目 | 结果 |
| --- | --- |
| 完整BIN | 三者全字节一致，均31,440字节 |
| BIN SHA256 | 56805506eb98b68269c73a3645d8f75dff73b697e30dec5f93ccc4716089ad34 |
| 入口 | 均0x80000000；ABI flags及ISA属性一致 |
| PT_LOAD | 同地址、权限、对齐及完整内容；file30,024B，memory31,440B，零填充1,416B |
| 装载节 | 所有SHF_ALLOC节的位置、大小、权限、对齐及内容一致，包括BSS |
| 函数 | 16个公共函数及启动/主程序等5个函数的地址、大小和机器码一致 |
| 测试表与数据 | 48条64字节调用记录与原计划逐项匹配；12组输入数组地址及内容一致 |
| GNU链接 | 无未解析符号；map与实际子命令证明使用SDK库成员 |
| 完整ELF原字节 | 不同；差异仅在.debug_info、.debug_line、.debug_line_str |
| 独立GNU复核 | 分别objcopy --strip-debug后，三份完整ELF全字节一致 |
| 去调试ELF SHA256 | 7e26e295fb020a63334026f768ed4825372266465b4e6008973de966fefc04ab |

调试节保存源文件/头文件路径及行号等信息，构建目录与头文件发生变化会改变这些记录。保留原ELF，没有通过删除调试信息来掩盖装载差异：主检查器已先完整比较装载内容和计划，去调试检查是独立补充证据。

原ELF SHA256：02159c7ef78cb31eb24cf706bf2974eadea313710563f235f2b11a7bb922de56。  
复制对照ELF SHA256：cfad14278ee4a3590de9bcbe7589b808fd91959156cef93ba92a78a90db0d99b。  
SDK接入ELF SHA256：f0ddf1167c961101e70f58cfd012ae788d2965324ad057aa4ade5af1de5bc42e。

### 检查器拒错与输入保护

7项负控全部被拒绝：实际ELF代码字节改坏、调用表改坏、启动入口改变、BSS大小改变、ISA属性改变、输入计划改变，以及真实GNU链接错误空库。另有只改调试字节的正控，确认不会将纯调试变化判为行为改变。错误镜像只用于主机检查，没有送入全核。

627项完整输入与封存运行证据绑定当前0f、EMU/NEMU及GNU工具。原33个矩阵进程和3个C进程的审计关系及全部封存输出树保持；本轮没有重复解析相同原始日志或伪造新PASS。当前操作保存了真实新GNU构建和最终镜像等价证据。

成功流水线：2026-10-27T21:59:40.771873+08:00 至 2026-10-27T21:59:43.182911+08:00，exit0。两次GNU构建，8份主流水线命令回执，另3份去调试GNU检查回执。流程首次通过，负控和原始文件全部保留。

### 已完成与未新增的结论

当前C8包已从“对象/可重定位链接合格”推进到“接回原可运行C程序、完整镜像等价”。原16函数、48例/两轮96正常调用（8×32占12例/24调用）的功能资格可明确复用；不是本轮重新执行这些调用。

新增EMU/NEMU/全核运行均为0。当前验证的是原测试夹具的包化接入，不是新的实际应用或LLM推理。没有新的周期、面积、STA或功耗测量。原273 cycles与1.095238×属于第25条性能矩阵，不是本C程序新测数据。

最小软件包接入闭环已完成。后续选择具体应用后再固定新的输入/调用路径/最终镜像合同；需要新性能结论时使用同路径firstdot/RVV及必要的集成前对照。另可继续4×8、16×64控制差异只读归因；4×13保留RVV。生产RTL和旧默认均不因本次接入改变。

### 证据

- [完整数据记录](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/record.json)，统一版本档案第28条：C8-RELINK-DIVFIX0F-CLEAN02-20261027-01。
- [比较与负控结果](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/report.json)、[实际接入link map](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/integrated/link.map)、[GNU独立复核](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/postcheck/result.json)。
- [原图/新图比较](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/integrated/equivalence.json)、[输入身份](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/qualification/report.json)、[执行回执](../optimizations/o2/integration/firstdot-v2-0f/package/c8/relink/evidence/pipeline.command.json)。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-relink-01。
- 完整本地归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-relink-final-archive-01。
- 软件基点c823a8786e052c6e26f6915563c42b6d730dd8e3；硬件0f12df675378556670afd0dd2153f47fcb330610。当前状态为本地未提交材料，不能把基点SHA当作已包含本次修改的提交。


## 29. R5/G5 冻结与工程总验收（2026-10-27T22:58:45.908838+08:00）

状态：R5_G5_ENGINEERING_ACCEPTED_WITH_DECLARED_LIMITS。0f＋firstdot V2＋显式C8候选冻结；生产RTL与默认未改，未上传。

仅新执行o2-control-diagnostic 1次，原13项原文重验；组合功能/差分/O2覆盖及独立原文复算PASS。原clean-02全14项UTC容量FAIL保留；新选择集合严格UTC峰值3、新单进程单调包络峰值1。不是fresh14。

398生产源码、627个C8输入、31,440字节最终BIN和24,157冻结文件校验；35模型测试、11时钟门禁测试、FU/父级与T15旧归档复算通过。PPA证据审计不等于时序收敛；新性能/PPA/功耗/Fmax均NOT_TESTED。

[结果](../optimizations/o2/integration/firstdot-v2-0f/acceptance/RESULT.md) · [完整记录](../optimizations/o2/integration/firstdot-v2-0f/acceptance/record.json)。证据manifest SHA256：e5122e1c3eb5a4f25ca608ee87ed2e432b16758775d76ccb132599434e23137c。旧28条保留。



## 30. P1 split-input 最小迁入与 steady-d0 探针（2026-10-28T17:13:31.013620+08:00）

**P1_PROBE_HOLD**：9镜像静态与63主机检查通过；steady-d0负控/正常/独立重放及完整validation通过。各轮7组功能数据/312调用/8控制/2432退休vdot。两次共168计时窗，统计仅正常48正式普通窗；其余8镜像runtime NOT_TESTED。

同新窗口S-V **308.5**、最快观测S-R4 **340.5**、P-V **408.75 cycles**，观测比 **1.103727715×**。两顺序3%收益过线，但锚点605/605/626/606、跨度 **3.471074% > 1%**，停止扩大、不采用为升级。不能与旧273/299比较。

PPA沿用0f：FU17,298.246 / 父级284,614.946 μm²；nominal FU i2r1.190323、r2r1.163404、slack−0.268520ns；父级全局r2r3.261218、VDot r2r1.356106、最差已报告slack−2.393998ns。无新综合/STA/功耗/Fmax。

实际5个EMU进程（run01负控完成＋正常中断；run02负控/正常/重放），旧中断closure闭合、原文不改。只读分段21cycles锚点差主要为首个退休vdot接受前+19，不指定分支预测/缓存原因。完整原4窗、全部84窗、整数门槛与原始UTC/单调差在结果JSON及归档。

[完整结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/RESULT.md) · [结构化结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/RESULT.json)。
manifest：team/optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-v1/evidence/20261028-p1/manifest.json，SHA256 **b4713776247348ed7c8c4745e5c1f5b46254272af307cdee11a2048011e687b2**，2622载荷；原29条保持。

P0 SOURCE_LOCK.current_sources 中两份 ledger 标记 historical_snapshot_reference，但冻结 identity.check 实际将其当作当前路径 live pins。此次在全部运行和最终完整身份复核结束后才追加第30条；原 ledger 字节保存在本归档的 *.before。追加后旧完整 identity 对当前工作树拒绝属于预期复现边界，旧资格应在独立历史快照中用归档的旧 ledger 与原冻结输入复核，不能恢复当前文件凑 PASS，也不修改 identity.py 或回写旧 SOURCE_LOCK。新增 RESULT/证据后重建完整源码清单也须另立新身份。

本轮未改RTL/默认、未commit/push。后续不自动新增实验。


## 31. P2 首vdot调用路径归因（2026-10-28T17:57:12.483077+08:00）

**只读派生分析完成，不是新性能测量。** 基于P1相同steady-d0原文，正常/重放84窗归因一致、7变异拒绝及独立复算通过。4个正式慢窗41/48/69/76额外redirect绑定0x800015ac的正常退休JALR；快/慢leaf首退休45–47/55拍，随后到首vdot接受均51拍，首vdot入队到接受均19拍。差值已在入队前，支持间接调用控制流预测纠正所在到达区间归因，不能称特定BTB或固定9拍纯恢复。

20个正式split RVV普通窗也发生同调用纠正，必须重新测对照。决定值得一次P1-R1窗外conditioning调用点隔离；设计已写、未实现/未构建/未目标测试。原1%/3%门槛、P1 HOLD、稳定0f+C8保持。P2其他依赖链/Jade未开展。

三指标沿用旧值：P1观察308.5/340.5 cycles、1.103727715×仍HOLD；FU/父级面积17,298.246/284,614.946 μm²；参考nominal父级全局r2r3.261218ns、VDot r2r1.356106ns、已报告最差slack−2.393998ns（全字段见JSON）。新性能/综合/STA均NOT_TESTED。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/callpath-p2/RESULT.md) · [修订设计](../optimizations/o2/integration/firstdot-v2-0f/continuation/callpath-p2/REVISION_PLAN.md)。manifest SHA256 c70c41682b00ace838031406e691d416fcbbe491eb8fa7f33fece61d0c671011；59个归档载荷。原30条JSON和Markdown前缀保持；无commit/push。


## 32. P1-R1 准备调用隔离（2026-10-28T20:57:21.546706+08:00）

**P1_R1_PROBE_HOLD**；新候选正确性 PASS_STEADY_D0_ONLY；性能探针 HOLD。实际EMU 4 个，后处理新增目标0。

candidate S-V 310.00、最快观测RVV S-R4，同场RVV/S-V 1.099193548×；1%锚点=False，正反3%收益=True。

仅steady-d0；其余8镜像NOT_TESTED，重放不追加统计样本，默认/RTL未改。PPA继承0f：FU/父级17,298.246/284,614.946 μm²；nominal父级全局r2r3.261218、vdot r2r1.356106 ns、最差已报告slack−2.393998 ns；本轮无新面积/STA/功耗/Fmax。

[完整结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-r1/RESULT.md)。manifest SHA256 4604a8c369617fe3ac0d55bd4bf3d78deba568fb0777a5213ff2d21768796a32。原31条逐条深等值、旧Markdown前缀保留；全部失败/partial原文封存。未commit/push。

保留0f＋firstdot V2＋显式C8稳定版；停止该候选扩大，先复核本轮完整失败/未过门槛原因，不自动重试。


## 33. P2 依赖链只读归因（2026-10-28T23:53:08.308949+08:00）

**P2_DEPENDENCY_READONLY_COMPLETE**。复用0f三数据/12正式chain256窗、3072条vdot/3060依赖边；ACCEPT→MOVE1、MOVE→RESPONSE1、RESPONSE→下一ACCEPT5，合计7拍。每窗1857=37+255×7+2+33。ROB提前分配不证明IQ驻留；COMMIT非WB，后五拍逐段为静态模型。

398生产源码/原EMU身份一致；15主机检查、Jade2个ROI拒错通过；根分别fresh复算最终派生逐字相等。无新增EMU/NEMU/综合/STA。旧chain256加速比2.929725×与0f面积/时序沿用，1601/1602只是条件模型，不纳入实测成绩。

决定仅GO_FOR_P4_G0_READONLY_REVIEW：研究VDot内部2→1且保留两槽/全部协议，先评审组合锥和同约束成本门槛。没有允许改功能RTL；不先重建观察器或改共享后端。稳定0f+C8保持、P1-R1 HOLD保持。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/dependency-p2/RESULT.md) · [下一步](../optimizations/o2/integration/firstdot-v2-0f/continuation/dependency-p2/NEXT_STEP.md)。manifest SHA256 a8366da492856270e0eecbed6ede4a6c672618f2516b69578967aeaaf08add01。原32条保留；未commit/push。

## 34. P4-G0 一拍算术／两槽弹性只读评审（2026-10-29T00:31:40.273005+08:00）

**P4_G0_READONLY_REVIEW_COMPLETE_CONDITIONAL_GO**。唯一候选为组合乘加、无旧P且R可接收则新包直写R，否则存P低32结果；两槽身份/异常/取消/反压与DIV协议保持。默认0f＋firstdot V2＋显式C8不变。

320组抽象状态、连续8笔一拍/II1、4类错误拒绝通过；根独立复算协议/PPA提取逐字节相等。不是RTL/父级/全核PASS。新加速比、面积、STA均NOT_TESTED，无构建/综合/目标运行。

历史0f chain256=1857拍、RVV/VDot=2.929725×，FU/父级面积17298.246/284614.946 μm²；nominal父级最差setup slack−2.393998ns。1601拍、13.7857%下降仅条件模型；少96数据保存位、裸DFF理想差434.112μm²不等于净面积节约。

预声明G2：FU＋5%、父级＋1%面积上限，五档局部Q增长≤5%，输出/控制保护、全路径覆盖；全部为工程筛选而非官网门槛。GO只指值得下轮启动G1，未实施/采用，未进全核。G1先说明RTL改法；完成FU/真实父级/DIV/SQRT后再决定G2。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g0/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g0/CONTRACT.md)。manifest SHA256 2b5b55cda9411a64dc7a294c169d0a16380b666509154d12a93f00d9be4c003e。原33条保持，无commit/push。


## 35. P4-G1 一拍算术／两槽弹性局部验证（2026-10-29T01:14:23.782861+08:00）

**P4_G1_LOCAL_VALIDATION_PASS**。候选默认关闭，仅VDotO2.scala/VDotElastic.scala两处生产改动，改前已说明。当前HEAD加未提交patch构成候选，不能用HEAD单独代表源码。

10022完整128位向量全部通过，无反压10022响应均1拍、10021个II1间隔；FU24215接受守恒，9负控；真实父级14组13468接受守恒，20负控；SQRT115场景、54取消后162立即空闲钟样本全部关闭、7离线负控。关闭模式原FU/父级及功能生成物对照通过，默认未设置及8种错误配置已验证。

新程序加速比、面积、STA均NOT_TESTED。0f历史参考2.929725×（chain256）、FU/父级17298.246/284614.946μm²、nominal父级最差setup slack−2.393998ns不能转授候选。一拍是局部协议延迟，非程序2倍提速。

首次parent-01因identity注入先命中stability而被严格门禁拒绝，保留FAIL；只修注入窗口、不放宽检查，重建parent-02全部通过。无生产功能修复，完整正向日志修前后逐字一致。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g1/RESULT.md)；manifest SHA256 48ebb60bcf92745577cc3b80bdeeb0109a04fd9b460f883e23ffacdbddd19033；patch SHA256 86b34d6117d8f36609e152847a0cda763b3aeb5411908194489e5be882a47243。旧34条保持。

下一步仅P4-G2同约束综合和五档STA，继续按G0门槛筛选；本轮未执行G2、未构建全核、未NEMU/应用性能运行、未commit/push。


## 36. P4-G2 同约束综合与五档STA（2026-10-30T12:31:24.863291+08:00）

**P4_G2_NO_GO**。47项冻结门槛中41通过、6未通过；不进入G3，不采用，稳定0f行为＋firstdot V2＋C8保持。G1候选源码445份不变，本轮RTL修改0；HEAD加原未提交patch，不能用HEAD单独代表候选。

| 三指标 | 0f基线 | P4候选 |
| --- | ---: | ---: |
| chain256加速比 | 历史2.929725× | NOT_TESTED |
| FU面积μm² | 17298.246 | 18322.878（+5.923329%） |
| 含FU父级面积μm² | 284614.946 | 285241.642（+0.220191%） |
| nominal FU最差setup裕量ns | -0.268520 | -0.790381 |
| nominal父级最差setup裕量ns | -2.393998 | -2.337809 |

FU少96 DFF但多737 MUX，净面积+1024.632μm²；完整身份保留，主要新增选择位于R控制/perf写入锥。两模式4次映射、40档STA执行（20原组＋20覆盖），旧14×5组和候选70补充报告完整。两边界旧成本数值精确复现；全部失败门槛及五档Q见结果，未用改善项冲抵失败。

首次off-fu-coverage-01分析别名错误被严格断言拒绝，保留旧源与失败；仅改工具，新02通过。无全核/NEMU/性能或功耗测量；局部Q非整核Fmax，1ns负裕量不冒充时序闭合。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2/RESULT.md) · [完整逐项](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2/screening.json)。manifest SHA256 ff4224cfcd193e78b9c221864220c005d9f99f0dc818698e9a0491f27644754c。旧35条保持，无commit/push。

下一轮仅建议P4-G2R0只读成本复核，按全部失败项判断一次最小修订价值；不自动改RTL或进入G3。

## 37. P4-G2R0 R元数据／父级ready只读评审（2026-10-30T13:03:20.575600+08:00）

**P4_G2R0_GO_ONE_BOUNDED_REVISION**：只表示值得下一轮做一次元数据选择的最小修订。当前P4-G2仍NO-GO，47项41通过／6失败原样保留，不进入G3、不采用。稳定0f＋firstdot V2＋C8保持。

FU的790位R元数据中，784位各有两级MUX（1568个不同实例）；真实父级595位中593位相同。建议仅在一拍分支中把ctrl/perf写入改为完整的hold/move/directR三路互斥表达，其他数据、状态、ready与DIV均保持。

两个手工等价单元构型的毛面积节省208.544／625.632μm²，未包含控制/缓冲/映射，不是新综合成绩或上下界。父级ready仍需五档分别恢复5.243／5.243／5.243／5.535／6.844ps；共享负载分析不能保证改善。2048项主机位逻辑检查与4类错误反例、独立重放通过，仅为二值选择逻辑，不代替RTL验证。

| 三指标 | 本轮新修订 |
| --- | --- |
| 程序加速比 | NOT_TESTED |
| FU／父级面积 | NOT_TESTED |
| STA／时序 | NOT_TESTED |

旧G2实测仅作为归因参考：FU18322.878、父级285241.642μm²，nominal父级slack−2.337809ns／ready0.303064ns，候选加速比未测。0f历史chain256为2.929725×，不能转授新修订。

41项输入与445份候选源码未变，原patch SHA256 86b34d6117d8f36609e152847a0cda763b3aeb5411908194489e5be882a47243；生产RTL修改0、新EDA/全核/NEMU运行0、无commit/push。旧36条保持。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r0/RESULT.md) · [最小修订合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r0/REVISION_CONTRACT.md)。manifest SHA256 2c09801af8eeb90e6f17060300f82a47b2f23e1c1d29150e36b39cfc8bb3c053。下一轮仅建议P4-G2R1局部实现与验证，另轮再做原G2成本筛选；任一原门槛失败停止该次修订，不自动扩大。

## 38. P4-G2R1 R槽元数据最小修订局部验证（2026-10-30T13:29:29.086733+08:00）

**P4_G2R1_LOCAL_VALIDATION_PASS**。相对G1仅改VDotElastic.scala一拍分支的R ctrl/perf为完整hold/move/directR三路互斥选择，加恰一断言；数据、状态、ready、DIV和默认关分支不变。改前已说明；默认关闭、不采用、未进入全核。

| 本轮资格 | 实测 |
| --- | --- |
| 完整128位 | 22定向＋10000随机全部通过；10022一拍响应、10021个II1间隔 |
| FU | 24215接受守恒；9观察负控拒绝 |
| 真实VFEX4 | 14组、13468接受守恒；完整VPU/perf/异常，DIV切换/反压/取消/身份，20观察负控拒绝 |
| SQRT/双lane | 115场景；54取消后162立即真空闲钟样本全部关闭；7离线负控拒绝 |
| 默认关/拒错 | FU/父级重新通过，4/16负控；4/56模块严格诊断规范化后逻辑一致；默认未设置成功及8种错误配置拒绝 |
| 程序加速比、面积、STA | **全部NOT_TESTED**；不转授旧G2数值 |

五份新正向日志与G1逐字一致，非性能测量。生成夹具中常量元数据保留变化：FU的reg声明40/1354位→98/1994位，父级102/2580位→129/2607位；不是映射DFF/面积，成本轮需核查。

首轮汇总因“非VDot生成HDL都应相同”的过宽假设FAIL，完整留档；仅修分析方法，生产源/原checker不变。确认传播差异仅VDotElastic/ExeUnit/测试顶层，ready/busy/状态/断言片段经3个输入探针重命名一致，三个ClockGate连接一致；不声称整个候选父级生成图等价。

HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75＋完整补丁SHA256 9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5；本轮增量SHA256 fb85300a4600318c36964bc77518be3560a6c7ce50909272343744b17e602023。源码/配置/实际新二进制/日志均绑定；313冻结输入和444其他源码未变。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1/RESULT.md) · [完整数据](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1/aggregate.json)。manifest SHA256 75351b6eef5cedf28e976e592b9610ad0c0aecf3466e847cefc99a866c0ca412（938条，776去重gzip）。旧37条及原G2六项失败保留。

下一轮先FU同约束综合＋五档STA并核查常量元数据实际映射，合格后才做真实父级；原47项门槛不变。本轮无综合/STA/全核/NEMU/commit/push，稳定0f行为＋firstdot V2＋C8保持。

## 39. P4-G2R1 成本筛选（2026-10-30T14:41:16.082152+08:00）

**P4_G2R1_COST_NO_GO**；原47项 37 PASS / 10 FAIL。FU通过后才运行父级；默认0f＋firstdot V2＋C8保持，未采用。R1程序加速比NOT_TESTED。

| 本轮三指标 | R1实测 | 说明 |
| --- | ---: | --- |
| 程序加速比 | NOT_TESTED | 不借用0f历史成绩 |
| FU面积 μm² | 18086.936 | 相对0f +4.559364% |
| 含FU父级面积 μm² | 285473.062 | 相对0f +0.301501% |
| nominal FU最差slack ns | -0.776319 | 布局前局部参考 |
| nominal父级最差slack ns | -2.235609 | 负裕量保留；非整核Fmax |

[全部47项、五档及历版对照](../optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g2r1-cost/RESULT.md)。源码补丁 9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5；证据manifest 4ad0eba39ad487f15e7b4dfa8c8dfaae5331b57bd05921d4f9bfc1a5509d3b9d。常量位实际保留逐位归因，全部计入面积与STA；原数值门槛未改，分析工具两次失败和旧G2六项FAIL保留。旧38条不变；RTL修改0，全核/NEMU/性能0，无commit/push。

下一轮：开始 P4 收口后的只读路线评审：保持 0f＋firstdot V2＋C8，依据 P4/R1 的完整成本结果和现有应用瓶颈，判断还有没有值得启动的最小优化。不继续试改 P4、不修改 RTL、不构建全核、不上传 GitHub，给出 GO/NO-GO 和下一轮指令。


## 40. C8 8×32分段归约：GNU与宿主资格（2026-10-30）

记录C8-DEFERRED-HOST-20261030-01，状态**C8_DEFERRED_HOST_PASS_GO_D0_PROBE**。只到dataset0公平探针，不采用候选；当前0f＋firstdot V2＋C8保持。
新加速比/面积/STA均**NOT_TESTED**，目标EMU/NEMU为0。不得把本条称为全核验证通过。
GNU实际叶：vdot 164→156指令、13→5配置、656→624B；RVV112→108、13→9、448→432B。架构向量寄存器使用20→28、22→30；无spill/额外move。
最终attempt-03：310输入×3入口状态×4实现＝3720有限模型执行；29760完整128位输出槽、59520逐dot独立完整128位oracle核对，4原语、39负控、9对象/ELF/BIN重复构建字节一致。
三次宿主尝试原样保留；只统计最后一次独立覆盖，不把重复用例倍增。真实C引用与静态链接通过，夹具不是AM运行程序。
候选汇编SHA256 bdd86ba4552cca7f48865fa5740dc9c855152b4649407ef6e497d64d70691807；对象2a5b5dc774f3acc343eea2ec69fd08fa2ffe9093be9bfbd03dbf3095760b4157。
完整版本/工具/合同/负控/证据见[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/RESULT.md)及配套JSON；下一轮按[冻结探针合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-v1/PROBE_CONTRACT.md)，先构建实际AM及observer适配，再最多5串行目标进程；本轮未启动、未改RTL、未上传。

## 41. C8 分段归约 dataset0 公平探针（2026-10-30）

**HOLD_TEST_HARNESS_BUDGET_REVIEW，不采用候选。** 真实AM A/B、静态及宿主负控、首条NV的bit100实际拒错通过。正常恢复没有完成，没有合格性能窗口。

| 新三指标 | 结论 |
| --- | --- |
| 加速比 | NOT_TESTED |
| 面积 | NOT_TESTED，RTL未变 |
| 时序 | NOT_TESTED，未做STA |

A/B各53,572B，所有ALLOC布局相同，仅NV/NR叶代码不同。静态窗口instret OV/NV/OR/NR＝175/167/123/119；不能当作实测cycles。实际C校验函数84组、177,408次宿主扰动；退休/跳转/计数及阈值负控通过。

2/5个目标进程：A拒错24.906965秒PASS，PC0x80004854、word0x0388000b、vd0、bit100；A正常534.868194秒后主动SIGTERM（−15），后三项NOT_TESTED。原因是本Agent把15项校验器负控重复放进84次目标功能调用，额外1,260项自检导致明显前序开销、预算预检不足。80,794是前两条不同调用首dot提交间隔，**不是叶延迟或加速比**。主动停止未触发硬上限，不写成超时，也不据此判断候选性能失败；原campaign NO_GO退出门禁保留，候选决定HOLD。

1%锚点、逐窗控制精确相等和正反3%收益均未实际验证，原门槛不变。下一轮仅先修框架重复自检与预算审计，保留84功能调用及完整检查、原四叶和计时窗口；新镜像/新预算重新开始，不能续借本轮部分资格。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0/RESULT.md)及配套JSON；manifest SHA256 c94290a60dcf121420ab0e59cd2b9b67ddf561c6ecf7012a5625ab9f009db834，119条归档。5298运行输入、926保护文件、src补丁9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5复核未变。旧40记录保持，无RTL/新核/EDA/commit/push。

## 42. C8 分段归约 dataset0 公平探针 R1（2026-10-30）

**HOLD_ANCHOR_AND_GAIN_SCREEN，不采用、不扩围。** 测试框架修复后，84次功能调用、32个计时窗口、完整128位/CSR/寄存器/范围检查、NEMU差分、退休与O2身份审计通过；原1%锚点及正反3%收益门槛失败，实际2/5串行进程后自动停止。

| 实现 | 正向均值 cycles | 反向均值 cycles | 全部正式均值 cycles | 每窗instret |
| --- | ---: | ---: | ---: | ---: |
| 原C8 vdot OV | 273.50 | 274.00 | 273.75 | 175 |
| 分段归约vdot NV | 273.00 | 273.00 | 273.00 | 167 |
| 原C8 RVV OR | 301.00 | 301.00 | 301.00 | 123 |
| 分段归约RVV NR | 278.00 | 278.00 | 278.00 | 119 |

**以上仅A图诊断观察，不是公平资格已通过的性能成绩。** OV四锚点273/274/274/268，跨度2.238806%>1%；OR四锚点301，跨度0%。NV正反分别仅比OV少0.183%/0.365%，均未达3%。原始最快RVV/NV＝278/273＝1.018315×，不得排除更快NR改用OR分母。B校准、A/B重放、跨镜像逐窗控制精确相等均NOT_TESTED，保留原门槛。

| 新三指标 | 资格 |
| --- | --- |
| 合格加速比 | NOT_QUALIFIED；1.018315×仅诊断观察 |
| 面积 | NOT_TESTED；硬件保持0f |
| 时序 | NOT_TESTED；未做STA/新核构建 |

R1仅移出目标端1260重复校验器自检及84恢复复检，validate调用1460→116；84功能与32性能调用不变，宿主177408扰动和1260自检保留。新旧A/B共24项叶/计时/功能入口的机器码、地址、长度逐项相同。新A/B各52868B，仅NV/NR叶666字节不同；原53572B镜像和主动停止失败记录不覆盖。

bit100拒错PASS（PC0x80004854、word0x0388000b、vd0），单调耗时32.307366s；A正常exit0，3065.826606s，O2接受/移动/响应/入队/提交各1856。实际4线程CPU4–7；未超硬限、未人工停止、未重试。正常单调时间与UTC显示差211.463253s，原因NOT_ATTRIBUTED，两者保留；7200s预算只按冻结单调时钟判断。新增DIV/STALL/KILL覆盖为0，不借本次扩张硬件资格。

HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75、原src补丁9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5保持；固定5583输入、1179保护文件复核未变。完整镜像/工具/合同/轨迹/时钟及已知显示路径说明见[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0-r1/RESULT.md)和[JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/deferred-reduction-c8-d0-r1/RESULT.json)。归档manifest SHA256 bed28543a868b72af5fccc69f51055274a5ca7ebafab4081cc9f637beb247230，141载荷；旧41记录及失败保持。

下一轮只读归因：解释末OV锚点6周期差异与NV/OV、NR/OR等待和依赖；不自动新开EMU、修代码、改RTL、构建新核或上传。当前仍0f＋firstdot V2＋原C8。


## 43. P3 FP32→QKV最小迁入与宿主门禁（2026-10-30）

**P3_HOST_PASS_GO_0F_ADAPTATION_AND_BUDGET_ADMISSION；HOST_ONLY。** 供体固定ffd668bf1bc80850d382f514d13bb00316c85582；生产保持0f＋firstdot V2＋原C8，不采用P3为默认。

| 项目 | 实际值／资格 |
| --- | --- |
| 源闭包 | 143项＋2项API；19历史Git对象；最小运行包8文件25140B |
| GNU最终镜像 | ELF 50004cbc4436c8bd52edfae198527be48c224fb1baffc1e9986038e8bc3109f1；BIN fc43caac20b07a6241b20d88fc37e1acc530cb1e1eea89d0b6bef70e4c76c459 |
| 构建/对象/链接/搬移 | PASS；6函数实际字/重定位、完整只读数组和路由、字段布局、去重、两个普通C链接入口、独立路径及包替换重链相等 |
| 完整数值 | 864量化元素/27尺度；2真实位置×2方法×3投影＝3456直接输出比较，1728唯一参考；另4 wrapper完整路径 |
| 完整128位 | 124416笔dot写入、192次slotstore逐笔独立检查，低32/高96均验证 |
| CSR/ABI/负控 | 宿主静态和模型PASS；5迁入负控、11机器字变异、14值/CSR/ABI负控、5类非法域；14策略合成测试 |
| 新加速比 /面积 /STA | NOT_TESTED /NOT_TESTED /NOT_TESTED |
| 当前硬件、旧成绩 | 没有改变0f；供体3.473%不转授；没有把新host指令数当cycles |
| 目标执行 /全核构建 | 0 /0；真实fflags/异常/DiffTest和新应用周期NOT_TESTED |
| 下一步 | GO仅进入0f身份/观察器/3%selector适配和预算准入；最多3进程合同已给出，NOT_READY_TO_RUN |

有效数值轮为attempt05；attempt01挂钩/变异定位失败、attempt04身份NUL构造失败保留。算法与GNU镜像未变，02/03早期PASS不替代最终身份门禁，不累计重复覆盖。两项FP机器字负控有提前拒绝限制，FP ABI敏感性由fs0/fs11值负控单独证明。

当前源码HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75，local/zjhwork-integration-20261024，原src补丁9327fa6f472f1869a41d04ceb515a7f8b76bae338279719568512571f88610d5；639保护文件与7运行时身份不变。记录人为@cc77-builder / Agent，operation 20261030-cc77-builder-p3-qkv-host。本轮未提交、未上传。

证据：[P3结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/RESULT.md)、[JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/RESULT.json)、[manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/evidence/manifest.json)、[下一轮合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-qkv-v1/PROBE_CONTRACT.md)。原始输出software-import-20261026/p3-qkv-host-20261030-01。预算18M/7200只为硬上限，缺可完成性证据不能开跑；旧42记录及失败保持。

## 44. P3-0f探针适配与预算准入（2026-10-30）

**HOST_ADAPTER_PASS / HOLD_BUDGET_NOT_DEMONSTRATED；HOST_ADAPTER_ONLY。** 保持0f＋firstdot V2＋原C8；P3不切默认。复用上轮冻结ELF/BIN，0个目标进程、0次核构建、0项RTL修改、0次GitHub写入。

| 项目 | 结果 |
| --- | --- |
| 0f身份 | 3519项物理运行/构建pins、2723生成物；另核对429实际硬件源；本轮冻结4303项 |
| 真实配置 | EMU_THREADS=1，O2两槽、T13/O2开启；CPU4–7/4个OS线程不是四模型线程 |
| 离线整规模观察器 | 155521笔合成提交，62208笔计时退休与O2 cycle/ROB/PC绑定；24CSR＋24计数入队 |
| 真实旧日志兼容 | C8原32窗、1856提交、512计时绑定重新解析PASS；不是新P3运行 |
| 门禁与负控 | 最终tests-05共22组通过；包含14个1%/3%整数策略用例，失败即停、回执、首bit100绑定及重放拒绝 |
| 解析器开销实测 | 合成293661026B stderr＋802B stdout，183.473969宿主秒，峰值6664052736B（6.206GiB） |
| 目标预算 | HOLD。旧C8吞吐498.287guest cycles/s仅用于情景估算；缺完整P3周期、吞吐/资源上界 |
| 新加速比 / 面积 / 时序 | **NOT_TESTED / NOT_TESTED / NOT_TESTED** |

冻结ELF 50004cbc4436c8bd52edfae198527be48c224fb1baffc1e9986038e8bc3109f1；
BIN fc43caac20b07a6241b20d88fc37e1acc530cb1e1eea89d0b6bef70e4c76c459。
14边界/42投影/17量化/5049标量除法、主机审计14977比较等成本全部保留。正式FR/TA/FR/FR/TA/FR顺序、1%锚点和最慢TA相对最快FR少3%不变。合成cycles不记作硬件性能，供体3.473%不转授。

7200秒只是正常单进程硬限；按旧吞吐350万guest cycles约7024秒、400万约8027秒，均是条件情景，不能据此宣称P3必超时或必完成。日志点估计约761MB不是上界，真实解析峰值也未确定。budget_admitted=false，next_role=null，正式三项全NOT_STARTED，不自动校准/加时/重试。

保留identity-01误读模型线程数、tests-01模块重名、tests-02语法、tests-03负控末行截断、tests-04错误流无效变异及source-map定位失败；最终通过没有改原合同或输入。
3615保护文件、HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75和原src补丁不变，前43记录保持。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/RESULT.md)、
[JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/RESULT.json)、
[manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/evidence/manifest.json)：
3673e11b8aa2504f3d858417c025d233bae1bfe8360ba2104c6630b6a3fd6c6b，102载荷。
下一轮建议另立独立短校准合同，仅在用户另行指令后最多2串行/2700秒获取吞吐和日志进度；不能自动进入正式探针，详见[NEXT_STEP](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-0f-adapter-v1/NEXT_STEP.md)。

## 45. P3独立短校准（2026-10-30）

**HOLD_THREAD_LIMIT_NO_NORMAL_CALIBRATION。** 1/2个目标进程，负控24.422046秒后整组线程峰值5>4，SIGKILL/exit−9；正常2400秒未启动。不是300秒超时，也不是候选数学失败；无自动重试、加时或正式探针。

| 项目 | 实测或资格 |
| --- | --- |
| 首指令及注入 | PC0x80001d44/word0x0388000b/vd0，O2 cycle12580；bit100标记已出现 |
| 完整拒错 | 未取得规范mismatch/ABORT/exit1，NOT_PASSED |
| RSS / 原始日志 | 77725696B；stdout961B＋stderr38039B |
| 线程 / 清理 | 5>4；检测到清理0.116474秒，存活组成员0 |
| 正常吞吐、完整QKV周期 | NOT_MEASURED |
| 7200秒预算 | HOLD_NOT_DEMONSTRATED |
| 新加速比 / 面积 / 时序 | NOT_TESTED / NOT_TESTED / NOT_TESTED |

另保留 **FAIL_NEW_RUNNER_SOURCE_FREEZE_INCOMPLETE**：context通配导入覆盖HERE，导致新运行器/测试/合同6项未入预冻结；镜像和EMU/NEMU原哈希不变，但不能授完整运行资格。原freeze不改，事后源码清单不替代预冻结。

10秒、20秒快照只有EMU自身4线程；触发瞬间缺PID/TID明细。固定DiffTest源码错误打印含system/popen辅助进程，是候选机制，尚未证明第5个的实际身份。原有界门禁保持，不排除辅助进程或回填PASS。8真实宿主机制＋8门禁用例通过，但未覆盖源路径遮蔽缺陷。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/RESULT.md) · [完整JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/RESULT.json) · [证据manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/evidence/manifest.json)。
保持0f＋firstdot V2＋原C8，前44条不变。下一轮先修源冻结和触发观测，仅宿主验证，按[NEXT_STEP](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-v1/NEXT_STEP.md)；本轮不再运行EMU/NEMU、未改RTL/构建核/上传。

## 46. P3校准运行器R1宿主修订（2026-10-31）

**HOST_GO_SINGLE_CPU_CALIBRATION_CANDIDATE，HOST_TOOLS_ONLY。** 生产0f＋firstdot V2＋原C8不变，本轮0次EMU/NEMU。

| 项目 | 实际结果 |
| --- | --- |
| 路径/源冻结 | 显式pc_context.CAL_HERE，8必需源码/合同，4324项测试前冻结；旧V1错误清单及缺项/漂移均拒绝 |
| 触发快照 | 保存当次PID/PPID/PGID/SID、进程/TID出生ticks、命令/亲和；先持久化再回收，首原因保留 |
| 宿主测试 | 14组PASS，13实际宿主进程，目标0 |
| 四核运行时基线 | 主运行时4线程，峰值4 |
| 四核诊断夹具 | 主运行时4＋子sh1＝5，THREAD_LIMIT正确停止，触发PID/TID明细完整 |
| 单核CPU4诊断 | 两次正常结束，整组峰值均3，不超过原4线程上限 |
| 新加速比 / 面积 / 时序 | NOT_TESTED / NOT_TESTED / NOT_TESTED |
| 7200秒预算 | HOLD，尚无正常QKV吞吐 |

夹具仅链接原始冻结verilated.o/verilated_threads.o/spikedasm.o，不含VSimTop或NEMU；诊断占位程序仅用于宿主可控采样。已证明这一宿主机制，未追溯证明旧目标第5个线程身份。模型threads()=1与运行时按亲和建立的宿主池分开记录。

预算仍CPU允许4–7、整组4线程（含助手）、RSS12GiB、日志合计2GiB、300/2400/2700秒和各100万guest。建议launch_cpus=[4]，属于原允许子集；不增加预算、不豁免shell。新运行wrapper和授权须列入下一次预冻结，当前没有目标启动CLI。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/RESULT.md) · [JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/RESULT.json) · [manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/evidence/manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-short-calibration-r1/NEXT_STEP.md)。
4540既有保护输入及原RTL补丁不变，前45条/上轮两项失败保留，无commit/push。

## 47. P3单核亲和有界校准（2026-10-31）

**TARGET_PREFIX_ONLY / HOLD正式预算**；稳定0f＋firstdot V2＋原C8不变。HEAD 10b71ad4bff25cd2070e775c74a4717b01602f75，记录ID P3-SINGLE-CPU-CALIBRATION-20261031-01。

| 项目 | 实测 |
| --- | --- |
| bit100拒错 | PASS，23.401695秒，12586 guest，exit1，首PC/word/vd/高位mismatch绑定 |
| 正常校准 | INCOMPLETE，1599.320037秒，999988 guest，原生guest限额，exit0不等于GOOD TRAP |
| 正常前缀吞吐 | 625.258220 guest cycles/秒 |
| 覆盖 | 31105条vdot；首RVV窗开始855738周期，1窗启动/0窗完成，2次CSR起始采样 |
| 冻结ELF前缀 | 65288退休记录、67782/110580条首窗动态指令吻合；仅进度资格 |
| 资源 | CPU4，两项线程观测峰值1；正常RSS81133568字节，日志73290448字节；组清理完成 |
| 两项目标墙钟 | 1622.721732秒，最多2串行，无重试/正式探针 |
| 7200秒预算 | HOLD；按前缀速率约容纳4501859周期，完整14调用无可信耗时上界 |
| 新加速比/面积/时序 | NOT_QUALIFIED_NO_COMPLETE_PAIR / NOT_TESTED / NOT_TESTED |

4502项预冻结、5项本轮必需源、10组宿主门禁通过；4487旧保护文件与RTL补丁保持。事后前缀核对的list/tuple实现失败已保留并修正，0次目标重跑。旧46条及全部失败不覆盖。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/RESULT.md) · [合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/CONTRACT.md) · [证据manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/p3-single-cpu-calibration-v1/evidence/manifest.json)，SHA 695b2db238836b7089839e20c1b55269d0e9a3993c0bcdb38041623c84be0ea3。


## 48. SP1-A/B 原P4恢复与全核观察器适配（2026-11-03）

**SP1_AB_PASS_GO_SP1_C，实际目标HOLD_RUNTIME_ANNEX，用户选择PENDING_USER_SELECTION。** 稳定0f＋firstdot V2＋原C8不变。新加速比NOT_TESTED，成本为通过关闭生成物核验后复用的原G2 trace-off值，未做新综合/STA。

| 版本与资格 | chain256加速比 | C8 8×32加速比 | FU面积μm² | 含FU父级面积μm² | nominal最差setup FU/父级ns |
| --- | ---: | ---: | ---: | ---: | ---: |
| 稳定0f，历史各工作负载实测 | 2.929725×，5440.5/1857 | 1.095238×，299/273 | 17298.246 | 284614.946 | −0.268520 / −2.393998 |
| 原P4 G1/G2，历史候选 | NOT_TESTED | NOT_TESTED | 18322.878 | 285241.642 | −0.790381 / −2.337809 |
| SP1-A/B，原P4＋新观察器 | NOT_TESTED | NOT_TESTED | 18322.878，trace关闭历史复用 | 285241.642，trace关闭历史复用 | −0.790381 / −2.337809，历史复用 |

| 档位 | 参考周期ns | 负载fF | FU Q/ns | FU最差setup/ns | 父级Q/ns | 父级最差setup/ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | +0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

六组局部on/off通过，20项配置通过，35组宿主/18432年龄枚举通过。FU31497拍、父级34998拍、SQRT2923拍功能流逐字节一致，完整128位与全部旧负控保留。原G0 NO-GO与本轮5项构建/工具集成FAIL保留。398源码补丁重放通过，源码patch为e1842a5f52a27fda2bea30f791921d6acefd63c54b415912adb8a1e3438be682。

[完整结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-ab/RESULT.md) · [JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-ab/RESULT.json) · [证据manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-ab/evidence/local-archive/manifest.json)，SHA 6102ef860cb840085ec62f06de84ffaee6df857a31bc6e9354b8553b6e4e48e4。原47条保持，不切换默认、不上传。下一轮按NEXT_STEP进行SP1-C/D的有界同镜像验证。


## 49. SP1-C/D 新EMU与有界chain-d0（2026-11-04）

**SP1-C通过；SP1-D在第3角色后的跨硬件退休记录公平检查失败，整轮STOPPED/HOLD。** 实际仅3个目标，两个重放均未启动。候选观测均值1601.25 cycles、RVV/vdot=3.397658×，相对同批0f的1857 cycles观测减少13.772213%；这组数值尚未取得最终公平及重放资格。

| 版本/本轮资格 | RVV平均cycles | vdot平均cycles | 观测RVV/vdot | FU面积μm² | 含FU父级面积μm² | nominal setup FU/父级ns |
| --- | --- | --- | --- | --- | --- | --- |
| 0f，单次正常对照通过 | 5440.5 | 1857 | 2.929725× | 17298.246 | 284614.946 | −0.268520 / −2.393998 |
| SP1一拍候选，公平/重放未验收 | 5440.5 | 1601.25 | 3.397658×（未最终合格） | 18322.878 | 285241.642 | −0.790381 / −2.337809 |


| 档位 | 参考周期ns | 负载fF | FU Q/ns | FU setup/ns | 父级 Q/ns | 父级 setup/ns |
| --- | --- | --- | --- | --- | --- | --- |
| nominal | 1.0 | 5.0 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5.0 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5.0 | 1.790381 | +0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1.0 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20.0 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |


成本复用原G2 trace-off，同Nangate45局部边界；新综合/STA为0，C8候选NOT_TESTED。实际3/5目标、总监督562.672秒，资源/清理PASS；跨硬件退休分组检查FAIL保留，重放2项NOT_RUN。第49条JSON记录完整身份、24窗观测、成本与归因。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd/RESULT.md) · [JSON](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd/RESULT.json) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd/evidence-manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd/NEXT_STEP.md)。旧48条保留，稳定0f＋firstdot V2＋原C8不变。


## 50. SP1-C/D-R1 宿主修订与合同冻结（2026-11-04）

**GO：宿主修订与新合同冻结完成；正式目标性能仍 HOLD，等待新合同下完整五角色。** 原 SP1-C/D STOPPED/FAIL 及两个未运行重放不回写，默认保持 0f＋firstdot V2＋原 C8。本轮没有 EMU/NEMU、RTL、全核构建、综合/STA 或 GitHub 写入。

- @cc77-builder / Agent；2026-11-04，UTC+08:00，日期级记录，不估算人工工时；未提交，基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。
- 检查器72、运行器45、独立审验60项PASS；3个Python归档回放、24窗及7个接口/最终资格负控通过。仅为宿主证据。
- 原三角色离线控制符合R1口径；旧FAIL保留，真实重放仍缺。2604pin/43源冻结通过，新used锁不存在。

| 版本与资格 | RVV平均 cycles | vdot平均 cycles | RVV/vdot | FU面积 μm² | 含FU父级面积 μm² | nominal setup FU/父级 ns |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 0f，原同批单次正常对照 | 5440.5 | 1857 | 2.929725× | 17298.246 | 284614.946 | −0.268520 / −2.393998 |
| SP1一拍候选，原单对观察；最终资格HOLD | 5440.5 | 1601.25 | 3.397658×，未最终合格 | 18322.878 | 285241.642 | −0.790381 / −2.337809 |
| 本轮R1宿主修订 | NOT_TESTED | NOT_TESTED | 无新增目标成绩 | 复用上行 | 复用上行 | 复用上行 |


| 档位 | 参考周期 ns | 负载 fF | FU Q/ns | FU setup/ns | 父级 Q/ns | 父级 setup/ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | +0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |


成本为原G2 trace-off同约束复用，未新增综合/STA；原单对观察未升级为正式成绩。JSON档案第50条保存身份和资格，前49条不变。独立评审初次路径错误及原失败脚本留档。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/RESULT.md) · [新合同](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/CONTRACT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/NEXT_STEP.md)。下一步仅在另获用户指令后启动新五角色，不自动扩围、改RTL、换默认或上传。


## 51. SP1-C/D-R1 新合同五角色探针（2026-11-04）

**GO：SP1-D 的 dataset0/chain256 五角色公平周期探针通过。** 可以进入SP1-E扩围合同与宿主准入评审，尚未取得全部数据集、C8或默认采用资格。

- @cc77-builder / Agent；2026-11-04 UTC+08，实际UTC起止见RESULT.json；未提交，基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。
- 本轮新EMU目标5个，目标合计926.517秒、整轮955.233秒；独立审计PASS、指标复算PASS。没有RTL/全核/EDA/默认切换/GitHub写入。

| 本轮版本 | RVV均值 cycles | vdot均值 cycles | RVV/vdot加速比 | FU面积 μm² | 含FU父级面积 μm² | nominal setup FU/父级 ns |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 0f同批对照 | 5440.5 | 1857 | 2.929725× | 17298.246 | 284614.946 | −0.268520 / −2.393998 |
| SP1一拍候选 | 5440.5 | 1601.25 | 3.397658× | 18322.878 | 285241.642 | −0.790381 / −2.337809 |


本轮候选相对同批0f的vdot周期减少 13.772213%，RVV均值退化 0.000000%；AB/BA分别减少 13.785676% / 13.758751%。这些数值只描述本轮chain256。


| 档位 | 参考周期 ns | 负载 fF | FU Q/ns | FU setup/ns | 父级 Q/ns | 父级 setup/ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | +0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |


面积与五档时序为原G2 trace-off同库同约束复用，周期为本轮新测，C8候选和trace-on PPA仍未测。数据档案第51条，原50条和原FAIL保留。下一步：SP1-E-G0扩围合同与宿主准入，先不运行目标。

[本轮结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/run-20261104-01/RESULT.md) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/run-20261104-01/evidence-manifest.json) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-cd-r1/run-20261104-01/NEXT_STEP.md)。默认仍0f＋firstdot V2＋原C8，由用户最终选择。


## 52. SP1-E-G0 扩围合同与宿主准入（2026-11-04）

**GO：扩围合同与宿主门禁完成。HOLD：尚不能启动整个矩阵或授予新应用性能资格。** 下一步仅原C8 dataset0的专用运行器、执行冻结及有界探针；是否真正启动取决于下一轮明确授权和全部宿主准入门禁。

已冻结20用例：12微基准（chain-d0已合格复用）、3原C8性能、1完整48调用普通C、3既有功能保护、1新54窗DIV/SQRT软件。micro313项新控＋35项继承控、C8 44项控、保护41项控通过；另8个新bit100库80项fake ABI控、C8 12叶等价及独立25项控/参考库错SHA拒绝通过。历史日志仅离线复核，不增加目标资格。

保留本轮micro初次12项fixture失败、保护初次缺dispatch模块ERROR、独立静态复核常量笔误及全部旧FAIL；修正后宿主通过，不覆盖原失败。没有运行EMU/NEMU、加载生产参考库、改RTL、构建新核、综合/STA、切默认或上传。

| 版本/资格 | RVV/vdot（chain-d0） | RVV / vdot均值cycles | C8加速比 | FU面积μm² | 含FU父级面积μm² | nominal setup FU/父级ns |
| --- | --- | --- | --- | ---: | ---: | --- |
| 0f，对照历史实测 | 2.929725× | 5440.5 / 1857 | 1.095238×，历史299/273 | 17298.246 | 284614.946 | −0.268520 / −2.393998 |
| SP1，第51条chain-d0已合格 | 3.397658× | 5440.5 / 1601.25 | NOT_TESTED | 18322.878 | 285241.642 | −0.790381 / −2.337809 |
| 本轮SP1-E-G0 | 无新增实测 | NOT_TESTED | NOT_TESTED | 无新增，复用上行 | 无新增，复用上行 | 无新增，复用上行 |

| 档位 | 周期ns | 负载fF | FU Q/ns | FU setup/ns | 父级Q/ns | 父级setup/ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | +0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

成本为Nangate45 Typical1.1V25℃、Yosys/ABC/OpenSTA原G2 trace-off局部FU/含FU真实父级同约束复用，不是全核面积或签核Fmax；候选trace-on PPA未测。nominal父级ready路径0.303064ns、gate-enable路径1.713544ns；主要路径及全部五档起止点保存在METRICS.json。1ns参考下负slack仍保留，不宣称1GHz时序收敛。上一轮chain周期减少13.772213%、RVV退化0，仅适用于dataset0/chain256。

数据档案第52条；前51条及旧FAIL保留。 @cc77-builder / Agent；操作ID `20261104-cc77-builder-sp1-e-g0`；任务记录起止 2026-11-04T16:05:23.352029+08:00 至 2026-11-04T16:47:04.820320+08:00，不代表人工投入。未提交，HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g0/RESULT.md) · [证据manifest](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g0/evidence-manifest.json) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g0/NEXT_STEP.md)。


## 53. SP1-E-G1 原C8 dataset0有界探针（2026-11-04）

**C8 dataset0 完整五角色合格。** 全部五角色和独立审计/指标复算通过，仅授原C8 dataset0资格；其他dataset、普通C48调用、DIV/SQRT和默认采用均未转授。

原campaign状态：`PERFORMANCE_PASS`；停止原因：`无`。原始角色/资源/时间/日志与独立审查见JSON，失败和未运行项原样保留。

操作者：@cc77-builder / Agent。BEFORE开始 `2026-11-04T09:01:51.088843+00:00`；收尾 `2026-11-04T10:16:17.254704+00:00`（均保留UTC偏移），北京时间收尾 `2026-11-04T18:16:17.254704+08:00`。记录的是本轮任务时间跨度，不是人工工时。

实际启动目标 5 个；目标活动墙钟 1861.555 秒；campaign总墙钟 1986.099 秒；留存日志 19844105 字节。五角色预算6300秒、外层7200秒，未用剩余额度重试或扩围。

宿主门禁：40项运行器测试及63项独立集成均PASS。独审初版 `sp1-e-g1-independent-final-admission-v1` / `HOLD_FINAL_ADMISSION` 与失败项 `["all_execution_pins_physical", "freeze_pin_set_exact", "git_identity"]` 原样留存；修订复核 `sp1-e-g1-independent-final-admission-r1-v1` / `GO_ONE_BOUNDED_C8_D0_ATTEMPT` 单独记录，不覆盖初版。宿主PASS不替代本轮真实目标资格。

| 角色 | 开始UTC（偏移+00:00） | 结束UTC（偏移+00:00） | UTC跨度秒 | monotonic监督秒 | 角色上限秒 | UTC是否在限额内 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| candidate-bit100 | 2026-11-04T09:23:11.089331+00:00 | 2026-11-04T09:23:52.317338+00:00 | 41.228007 | 42.018458 | 300 | 是 |
| candidate-normal-recovery | 2026-11-04T09:23:55.025243+00:00 | 2026-11-04T09:31:03.265570+00:00 | 428.240327 | 439.934237 | 1500 | 是 |
| baseline-normal-calibration | 2026-11-04T09:31:10.476140+00:00 | 2026-11-04T09:42:58.917470+00:00 | 708.44133 | 727.487007 | 1500 | 是 |
| candidate-replay | 2026-11-04T09:43:09.107241+00:00 | 2026-11-04T09:48:10.525253+00:00 | 301.418012 | 303.139725 | 1500 | 是 |
| baseline-replay | 2026-11-04T09:48:24.041308+00:00 | 2026-11-04T10:08:12.782167+00:00 | 1188.740859 | 349.108964 | 1500 | 是 |

Campaign总监督monotonic `1986.098985` 秒，UTC跨度 `2789.903813` 秒；差额 `803.804828` 秒。差异原因 `NOT_ESTABLISHED`，不推断休眠、调度或时钟校准。UTC各角色/总和/外层是否均在对应限额内：`True`。正式资源门禁沿用运行前冻结的monotonic合同，UTC独立观察同时保留；不删除差异或把两种时钟写成相等。加速比仅由同镜像guest计时窗口周期计算，UTC和宿主monotonic均不用于换算性能。

| 版本／本轮资格 | reuse RVV均值 | reuse vdot均值 | 原reuse RVV/vdot | FU面积 μm² | 含FU父级面积 μm² | nominal setup FU/父级 ns |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 0f | 299 | 273 | 1.095238×；本轮合格 | 17298.246 | 284614.946 | -0.26852 / -2.393998 |
| SP1一拍候选 | 299 | 272 | 1.099265×；本轮合格 | 18322.878 | 285241.642 | -0.790381 / -2.337809 |

| 版本 | basic-vdot | basic-RVV | reuse-vdot | reuse-RVV | basic RVV/vdot | min(两RVV)/reuse-vdot辅助值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0f | 643.75 | 356 | 273 | 299 | 0.55301 | 1.095238 |
| SP1 | 642.5 | 356 | 272 | 299 | 0.554086 | 1.099265 |

| 本轮四格对照 | 0f均值cycles | SP1均值cycles | cycles变化%（SP1/0f−1） | 四格2%保护 |
| --- | ---: | ---: | ---: | --- |
| basic-vdot | 643.75 | 642.5 | -0.194175% | PASS |
| basic-rvv | 356 | 356 | 0% | PASS |
| reuse-vdot | 273 | 272 | -0.3663% | PASS |
| reuse-rvv | 299 | 299 | 0% | PASS |

本轮reuse-vdot相对0f周期减少 0.3663%；本轮新测加速比与四格原始值如上。

主加速比始终为同次原reuse-RVV/reuse-vdot；basic对照和min-RVV辅助值分列，不使用未采用278周期RVV或历史分母。first/warmup只验证，不进入每格4窗均值。

| 档位 | 参考周期ns | 负载fF | FU Q/ns | FU setup/ns | 父级 Q/ns | 父级 setup/ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

面积和五档STA复用第51/52条原G2 trace-off，Nangate45 Typical1.1V25℃，局部FU及含FU真实父级；无新EDA、非全核面积、非签核Fmax。负slack保留，不能宣称1GHz收敛。第51条chain-d0的3.397658×仍仅属于chain，不转作C8成绩。

默认保持0f＋firstdot V2＋原C8，未改RTL、未构建新核、未上传。HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；生产445文件与BEFORE一致。数据档案追加第53条，前52条与旧FAIL保留。

开始 SP1-E 原C8 dataset1：复用G1五角色机制，先按冻结case适配镜像与bit100绑定，冻结执行合同、全源码及公平对照并通过宿主检查；全部通过后仅运行该case五角色，保持300/1500×4秒、总6300/7200秒及原资源/guest上限、四格2%和精确重放门槛。失败即停、不重试、不加时、不扩围、不改RTL、不构建新核、不切默认、不上传GitHub，完成后更新三指标、给出GO/HOLD和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d0/RESULT.md) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d0/evidence-manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d0/NEXT_STEP.md)。


## 54. SP1-E-G1 原C8 dataset1有界探针（2026-11-04）

**C8 dataset1 完整五角色合格。** 全部五角色和独立审计/指标复算通过，仅授原C8 dataset1资格；其他dataset、普通C48调用、DIV/SQRT和默认采用均未转授。

原campaign状态：`PERFORMANCE_PASS`；停止原因：`无`。原始角色/资源/时间/日志与独立审查见JSON，失败和未运行项原样保留。

操作者：@cc77-builder / Agent。BEFORE开始 `2026-11-04T10:27:08.983617+00:00`；收尾 `2026-11-04T11:33:20.195749+00:00`（均保留UTC偏移），北京时间收尾 `2026-11-04T19:33:20.195749+08:00`。记录的是本轮任务时间跨度，不是人工工时。

实际启动目标 5 个；目标活动墙钟 2295.995 秒；campaign总墙钟 2487.92 秒；留存日志 19844104 字节。五角色预算6300秒、外层7200秒，未用剩余额度重试或扩围。

宿主门禁：48项运行器测试PASS。独立集成原run01保持FAIL：产品已在 `C8: actual image path` 正确拒绝dataset0镜像，而测试断言仅预期后面的 `UART begin`，因此断言失败。合计72项合同控制来自54项原PASS复用、1项离线确认正确拒错及17项原未执行补项PASS；这是71项普通测试PASS加1项离线资格确认，不能写成原运行72项全部PASS。原FAIL、原源码和原日志均不改写，不重跑原run01。本轮独审收据 `[{"schema": "sp1-e-g1-c8-d1-independent-final-admission-v1", "status": "GO_ONE_BOUNDED_C8_D1_ATTEMPT", "failures": []}]` 按真实状态逐项保留，不预设初FAIL或R1。上轮d0初版失败仍保留旧包，未移作本轮失败。宿主PASS不替代本轮真实目标资格。

| 角色 | 开始UTC（偏移+00:00） | 结束UTC（偏移+00:00） | UTC跨度秒 | monotonic监督秒 | 角色上限秒 | UTC是否在限额内 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| candidate-bit100 | 2026-11-04T10:48:36.386733+00:00 | 2026-11-04T10:49:23.506645+00:00 | 47.119912 | 49.520162 | 300 | 是 |
| candidate-normal-recovery | 2026-11-04T10:49:30.552085+00:00 | 2026-11-04T10:59:04.664775+00:00 | 574.11269 | 596.663046 | 1500 | 是 |
| baseline-normal-calibration | 2026-11-04T10:59:14.909080+00:00 | 2026-11-04T11:07:38.468838+00:00 | 503.559758 | 525.601249 | 1500 | 是 |
| candidate-replay | 2026-11-04T11:08:04.983071+00:00 | 2026-11-04T11:17:57.234707+00:00 | 592.251636 | 618.573623 | 1500 | 是 |
| baseline-replay | 2026-11-04T11:18:42.694297+00:00 | 2026-11-04T11:26:45.767804+00:00 | 483.073507 | 505.790574 | 1500 | 是 |

Campaign总监督monotonic `2487.920133` 秒，UTC跨度 `2378.35713` 秒；差额 `-109.563003` 秒。差异原因 `NOT_ESTABLISHED`，不推断休眠、调度或时钟校准。UTC各角色/总和/外层是否均在对应限额内：`True`。正式资源门禁沿用运行前冻结的monotonic合同，UTC独立观察同时保留；不删除差异或把两种时钟写成相等。加速比仅由同镜像guest计时窗口周期计算，UTC和宿主monotonic均不用于换算性能。

| 版本／本轮资格 | reuse RVV均值 | reuse vdot均值 | 原reuse RVV/vdot | FU面积 μm² | 含FU父级面积 μm² | nominal setup FU/父级 ns |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 0f | 299 | 273 | 1.095238×；本轮合格 | 17298.246 | 284614.946 | -0.26852 / -2.393998 |
| SP1一拍候选 | 299 | 272 | 1.099265×；本轮合格 | 18322.878 | 285241.642 | -0.790381 / -2.337809 |

| 版本 | basic-vdot | basic-RVV | reuse-vdot | reuse-RVV | basic RVV/vdot | min(两RVV)/reuse-vdot辅助值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0f | 643.75 | 356 | 273 | 299 | 0.55301 | 1.095238 |
| SP1 | 642.5 | 356 | 272 | 299 | 0.554086 | 1.099265 |

| 本轮四格对照 | 0f均值cycles | SP1均值cycles | cycles变化%（SP1/0f−1） | 四格2%保护 |
| --- | ---: | ---: | ---: | --- |
| basic-vdot | 643.75 | 642.5 | -0.194175% | PASS |
| basic-rvv | 356 | 356 | 0% | PASS |
| reuse-vdot | 273 | 272 | -0.3663% | PASS |
| reuse-rvv | 299 | 299 | 0% | PASS |

本轮reuse-vdot相对0f周期减少 0.3663%；本轮新测加速比与四格原始值如上。

主加速比始终为同次原reuse-RVV/reuse-vdot；basic对照和min-RVV辅助值分列，不使用未采用278周期RVV或历史分母。first/warmup只验证，不进入每格4窗均值。

| 档位 | 参考周期ns | 负载fF | FU Q/ns | FU setup/ns | 父级 Q/ns | 父级 setup/ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

面积和五档STA复用第51/52条原G2 trace-off，Nangate45 Typical1.1V25℃，局部FU及含FU真实父级；无新EDA、非全核面积、非签核Fmax。负slack保留，不能宣称1GHz收敛。第51条chain-d0的3.397658×仍仅属于chain，不转作C8成绩。

默认保持0f＋firstdot V2＋原C8，未改RTL、未构建新核、未上传。HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；生产445文件与BEFORE一致。数据档案追加第54条，前53条与旧FAIL保留。

开始 SP1-E 原C8 dataset2：复用G1五角色机制，先按冻结case适配镜像与bit100绑定，冻结执行合同、全源码及公平对照并通过宿主检查；全部通过后仅运行该case五角色，保持300/1500×4秒、总6300/7200秒及原资源/guest上限、四格2%和精确重放门槛。失败即停、不重试、不加时、不扩围、不改RTL、不构建新核、不切默认、不上传GitHub，完成后更新三指标、给出GO/HOLD和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d1/RESULT.md) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d1/evidence-manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d1/NEXT_STEP.md)。


## 55. SP1-E-G1 原C8 dataset2有界探针（2026-11-04）

**C8 dataset2 完整五角色合格。** 全部五角色和独立审计/指标复算通过，仅授原C8 dataset2资格；其他dataset、普通C48调用、DIV/SQRT和默认采用均未转授。

原campaign状态：`PERFORMANCE_PASS`；停止原因：`无`。原始角色/资源/时间/日志与独立审查见JSON，失败和未运行项原样保留。

操作者：@cc77-builder / Agent。BEFORE开始 `2026-11-04T11:41:44.820212+00:00`；收尾 `2026-11-04T14:08:30.582789+00:00`（均保留UTC偏移），北京时间收尾 `2026-11-04T22:08:30.582789+08:00`。记录的是本轮任务时间跨度，不是人工工时。

实际启动目标 5 个；目标活动墙钟 1929.886 秒；campaign总墙钟 2096.836 秒；留存日志 19844104 字节。五角色预算6300秒、外层7200秒，未用剩余额度重试或扩围。

宿主门禁：48项运行器测试本轮PASS。独立集成78个叶级结果分为54项本轮新接口测试和24项精确源码/原证据复用；对应72类合同控制=48新类别+24复用类别。6种错集控制分别对d0/d1参数化，因此78叶结果不等于新增78类。复用项不称本轮重跑；旧d1原run01断言FAIL仍留在历史证据，不转作本轮FAIL，也不覆盖成PASS。本轮独审收据 `[{"schema": "sp1-e-g1-c8-d2-independent-final-admission-v1", "status": "GO_ONE_BOUNDED_C8_D2_ATTEMPT", "failures": []}]` 按真实状态逐项保留，不预设初FAIL或R1。上轮d0初版失败仍保留旧包，未移作本轮失败。宿主PASS不替代本轮真实目标资格。

| 角色 | 开始UTC（偏移+00:00） | 结束UTC（偏移+00:00） | UTC跨度秒 | monotonic监督秒 | 角色上限秒 | UTC是否在限额内 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| candidate-bit100 | 2026-11-04T11:56:06.436640+00:00 | 2026-11-04T11:56:45.446890+00:00 | 39.01025 | 40.348054 | 300 | 是 |
| candidate-normal-recovery | 2026-11-04T11:56:49.985117+00:00 | 2026-11-04T12:04:44.631642+00:00 | 474.646525 | 496.160399 | 1500 | 是 |
| baseline-normal-calibration | 2026-11-04T12:04:55.815405+00:00 | 2026-11-04T12:13:02.592039+00:00 | 486.776634 | 492.046748 | 1500 | 是 |
| candidate-replay | 2026-11-04T12:13:23.790243+00:00 | 2026-11-04T12:20:55.844933+00:00 | 452.05469 | 469.655627 | 1500 | 是 |
| baseline-replay | 2026-11-04T12:21:26.287988+00:00 | 2026-11-04T12:28:20.594752+00:00 | 414.306764 | 431.889449 | 1500 | 是 |

Campaign总监督monotonic `2096.835792` 秒，UTC跨度 `2023.263848` 秒；差额 `-73.571944` 秒。差异原因 `NOT_ESTABLISHED`，不推断休眠、调度或时钟校准。UTC各角色/总和/外层是否均在对应限额内：`True`。正式资源门禁沿用运行前冻结的monotonic合同，UTC独立观察同时保留；不删除差异或把两种时钟写成相等。加速比仅由同镜像guest计时窗口周期计算，UTC和宿主monotonic均不用于换算性能。

| 版本／本轮资格 | reuse RVV均值 | reuse vdot均值 | 原reuse RVV/vdot | FU面积 μm² | 含FU父级面积 μm² | nominal setup FU/父级 ns |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 0f | 299 | 273 | 1.095238×；本轮合格 | 17298.246 | 284614.946 | -0.26852 / -2.393998 |
| SP1一拍候选 | 299 | 272 | 1.099265×；本轮合格 | 18322.878 | 285241.642 | -0.790381 / -2.337809 |

| 版本 | basic-vdot | basic-RVV | reuse-vdot | reuse-RVV | basic RVV/vdot | min(两RVV)/reuse-vdot辅助值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0f | 643.75 | 356 | 273 | 299 | 0.55301 | 1.095238 |
| SP1 | 642.5 | 356 | 272 | 299 | 0.554086 | 1.099265 |

| 本轮四格对照 | 0f均值cycles | SP1均值cycles | cycles变化%（SP1/0f−1） | 四格2%保护 |
| --- | ---: | ---: | ---: | --- |
| basic-vdot | 643.75 | 642.5 | -0.194175% | PASS |
| basic-rvv | 356 | 356 | 0% | PASS |
| reuse-vdot | 273 | 272 | -0.3663% | PASS |
| reuse-rvv | 299 | 299 | 0% | PASS |

本轮reuse-vdot相对0f周期减少 0.3663%；本轮新测加速比与四格原始值如上。

主加速比始终为同次原reuse-RVV/reuse-vdot；basic对照和min-RVV辅助值分列，不使用未采用278周期RVV或历史分母。first/warmup只验证，不进入每格4窗均值。

| 档位 | 参考周期ns | 负载fF | FU Q/ns | FU setup/ns | 父级 Q/ns | 父级 setup/ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

面积和五档STA复用第51/52条原G2 trace-off，Nangate45 Typical1.1V25℃，局部FU及含FU真实父级；无新EDA、非全核面积、非签核Fmax。负slack保留，不能宣称1GHz收敛。第51条chain-d0的3.397658×仍仅属于chain，不转作C8成绩。

默认保持0f＋firstdot V2＋原C8，未改RTL、未构建新核、未上传。HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；生产445文件与BEFORE一致。数据档案追加第55条，前54条与旧FAIL保留。

开始 SP1-E 原 C8 普通 C 48 调用的宿主合同与预算准入评审。复用固定 0f/SP1 EMU、NEMU 和最终 SDK 镜像，保留全部 48 调用、其中 12 个 C8 调用及 1008 次 custom；核对完整128位结果、数值/CSR/ABI、首条 bit100 绑定、身份和独立重放。按功能验收明确必要角色，分解完整运行与宿主检查开销，单独冻结 guest/墙钟上限及失败即停条件；不得套用性能镜像30万guest上限、删调用、把功能整程序周期当性能加速比，或把历史墙钟线性外推成完成保证。预算依据不足就 HOLD。先不运行 EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，也不自动改跑micro或DIV。完成后给出GO/HOLD和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d2/RESULT.md) · [证据](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d2/evidence-manifest.json) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-g1-c8-d2/NEXT_STEP.md)。


## 56. SP1-E 原C8普通C48宿主准入评审（2026-11-04）

**静态合同 GO；C48 目标执行准入 HOLD。** 未发现冻结调用表/数值/镜像不一致；当前组合完整运行墙钟上界没有证据，专用执行闭包也未完成。暂存此项，保留全部验收覆盖，不等于放弃最终SP1验收。

操作：20261104-cc77-builder-sp1-e-c8-c48-g0；@cc77-builder / Agent；2026-11-04T14:13:38.593740+00:00 至 2026-11-04T14:40:35.028282+00:00，记录跨度非人工工时。无目标/RTL/新核/EDA/GitHub写入，默认不变。完整48/1008保留；新三指标NOT_TESTED，历史记录51～55仍有效。

| 已验收工作负载／历史复用 | 0f vdot/RVV cycles | SP1 vdot/RVV cycles | 0f 加速比 | SP1 加速比 |
|---|---:|---:|---:|---:|
| chain256 dataset0 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| 原C8 reuse dataset0 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| 原C8 reuse dataset1 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| 原C8 reuse dataset2 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| 本轮C48普通C功能程序 | NOT_TESTED | NOT_TESTED | 不适用：0性能窗 | 不适用：0性能窗 |

| 历史同约束成本 | 0f | SP1一拍候选 |
|---|---:|---:|
| FU面积 μm² | 17298.246 | 18322.878 |
| 含FU父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | -0.268520 | -0.790381 |
| nominal父级setup slack ns | -2.393998 | -2.337809 |

| SP1历史档位 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

成本均为原G2历史复用、非全核或Fmax签核，负slack保留；路径端点见本轮METRIC_SNAPSHOT.json。

路线影响：C48暂存HOLD，缺完整预算与独立执行闭包；下一轮仅建议chain-d1合同/宿主准入，不自动运行。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-c8-c48-g0/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-c8-c48-g0/NEXT_STEP.md)。


## 57. SP1-E micro chain-d1 宿主准入与执行冻结（2026-11-05）

**GO：chain-d1 合同、宿主准入和执行输入冻结完成，可进入下一轮独立授权的五角色有界探针。** 本轮未运行目标；chain-d1 在 SP1 上的功能与性能仍 NOT_TESTED。

操作ID 20261104-cc77-builder-sp1-e-micro-chain-d1-host；@cc77-builder / Agent；2026-11-04T14:47:18.861904+00:00 至 2026-11-05T11:49:44.043581+08:00（含中断，非人工工时）。完整12窗/1536custom，10%收益/2%RVV/ABBA均正及精确重放不变。预算6300/7200秒GO一次有界尝试，目标未启动。

| 工作负载（历史复用另注） | 0f vdot/RVV cycles | SP1 vdot/RVV cycles | 0f 加速比 | SP1 加速比 |
|---|---:|---:|---:|---:|
| chain256 dataset0，历史51 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| 原C8 reuse dataset0，历史53 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| 原C8 reuse dataset1，历史54 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| 原C8 reuse dataset2，历史55 | 273/299 | 272/299 | 1.095238× | 1.099265× |
| **本轮 chain-d1 新五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 同约束历史成本 | 0f | SP1 一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU真实父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal 父级 setup slack/ns | -2.393998 | -2.337809 |

| SP1历史档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1 nominal关键路径（历史） | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 含FU父级 ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 含FU父级 gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 含FU父级 all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

成本全部原G2历史复用，非全核/Fmax签核；新三项指标NOT_TESTED。按用户要求优先加速比，允许合理面积/时序代价，不新增更严PPA门槛；保留负slack。

路线：下一轮仅chain-d1五角色探针；执行前复核输入/资源并生成新授权记录，C48 HOLD不变，默认0f＋firstdot V2＋原C8保持。无新EMU/NEMU/RTL/核构建/EDA/GitHub写入。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d1-g0/RESULT.md) · [下一轮指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d1-g0/NEXT_STEP.md)。


## 58. SP1-E micro chain-d1 五角色探针（2026-11-05）

**GO（仅 chain-d1 用例）：五角色探针与独立复核通过；VDOT 周期下降 13.772213%，同机 RVV/VDOT 加速比由 2.929725× 提高至 3.397658×，RVV 退化 0%。** 四个正常角色各完成 12 窗和 1536 次 custom，共 48 窗/6144 次；bit100 实际拒错、完整 128 位结果、退休/CSR、AB/BA 和双方精确重放通过。此次增加 dataset1 覆盖，未改 RTL，不能作为一次新的硬件优化或整个 SP1-E 完成。默认仍为 0f＋firstdot V2＋原 C8，候选最终采用等待用户决定。

@cc77-builder / Agent，20261105-cc77-builder-sp1-e-chain-d1-target；2026-11-05T04:01:17.021132+00:00至2026-11-05T12:35:57.680056+08:00，任务跨度非人工工时；真实目标进程5个，正式墙钟1468.527秒。

| 本轮同镜像角色 | vdot正式均值/cycles | RVV正式均值/cycles | RVV/VDOT加速比 |
|---|---:|---:|---:|
| candidate-normal-recovery | 1601.25 | 5440.5 | 3.397658080× |
| baseline-normal-calibration | 1857.0 | 5440.5 | 2.929725363× |
| candidate-replay | 1601.25 | 5440.5 | 3.397658080× |
| baseline-replay | 1857.0 | 5440.5 | 2.929725363× |

initial：vdot周期下降13.772213%，RVV退化0.000000%，AB/BA收益分别13.785676%/13.758751%。

replay：vdot周期下降13.772213%，RVV退化0.000000%，AB/BA收益分别13.785676%/13.758751%。

| 历史同约束面积/μm² | 0f | SP1一拍候选 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

历史nominal 0f FU/父级setup slack分别-0.268520/-2.393998 ns。

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

面积/STA均原G2历史复用，trace-off局部边界，非整核PPA；新EDA为0，保留负slack。生产RTL与默认不变，无新核/上传。宿主UTC与单调时钟约99秒差异已留档，预算依冻结单调时钟；离线复算的初稿CRLF解析FAIL和修订PASS均保留，未重跑目标。

路线影响：开始 SP1-E micro chain-d2 的合同与宿主准入准备：复用已验收 chain-d1 机制，核查 G0 冻结镜像、12 窗、1536 次 custom、bit100、完整 128 位结果、退休/CSR 及精确重放，完成最小运行器适配和 6300/7200 秒预算评审。保持 10% 收益、2% RVV 退化及 AB/BA 门槛，预算不足就 HOLD。先不运行 EMU/NEMU、不改 RTL、不构建新核、不做 EDA、不切默认、不上传 GitHub；完成后给出 GO/HOLD 和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d1-g0/target-20261105-01/RESULT.md) · [下一步](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d1-g0/target-20261105-01/NEXT_STEP.md)。


## 59. SP1-E micro chain-d2 宿主准入与执行冻结（2026-11-05）

**GO：chain-d2 的合同、宿主准入及执行输入冻结完成，可进入下一轮单独授权的五角色有界探针。** 本轮未运行 EMU/NEMU，SP1 chain-d2 目标正确性及加速比仍为 NOT_TESTED，默认保持0f＋firstdot V2＋原C8。

@cc77-builder / Agent；20261105-cc77-builder-sp1-e-chain-d2-host；2026-11-05T04:38:53.794288+00:00 至 2026-11-05T12:48:46.027709+08:00，任务跨度非人工工时。

运行器69项宿主门禁、独立预冻结100项、冻结后31项全部通过。覆盖错误dataset、全部128位结果与高96位、接收源、退休数量/融合分组、CSR、缺窗、bit100绑定、10%/2%精确边界、AB/BA与原始精确重放。实际加载12个Python模块及4个动态JSON均在执行源闭包中；缺失目标授权在启动前拒绝，宿主假进程不能冒充真实EMU。

d1/d2的主计算.text、kernel/main/linker/generator及加载布局相同；唯一可执行字节差为打印数据集编号1→2，输入/期望数据区68字节变化。历史d2完整0f为120824 guest cycles、12窗/1536custom；同EMU/NEMU的d1正常角色最慢328.155秒、完整五角色1468.527秒，均按单调计时留档。新d2完整宿主解析实测4.956863秒；26次解析与12次旧闭包重哈希的固定工作量投影157.362秒，小于900秒宿主预留。最终4548项冻结共651590256字节，实际包含全部verify的31项终检耗时1.402076秒，未出现实质增加的宿主成本。以上完整程序与实测证据支持一次有界尝试，不能保证未来调度下一定完成，也不能证明d2已有收益；外层单调硬限保持有效。

| 工作负载与测量范围 | 0f vdot/RVV cycles | SP1 vdot/RVV cycles | 0f 加速比 | SP1 加速比 |
|---|---:|---:|---:|---:|
| chain-d0，历史第51条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d1，历史第58条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| **本轮 chain-d2 新同镜像五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 历史同约束成本 | 0f | SP1 一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU真实父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal 父级 setup slack/ns | -2.393998 | -2.337809 |

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

三指标新测NOT_TESTED，以上成本均历史同库/同边界trace-off复用，负slack保留。生产445文件未变；0新EMU/NEMU/参考库加载/RTL/核/EDA/GitHub写入。宿主脚本失败修订保留，未重跑目标。

路线影响／接续：开始 SP1-E micro chain-d2 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和1536次custom、10%收益、2% RVV退化、AB/BA及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d2-g0/RESULT.md) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d2-g0/NEXT_STEP.md)。


## 60. SP1-E micro chain-d2 五角色探针（2026-11-05）

**GO（chain-d2）：五角色有界探针与独立复核全部通过。** VDOT均值1857→1601.25 cycles，降低13.772213%；RVV均值5440.5 cycles不变，加速比2.929725×→3.397658×。四个正常角色各完成12窗/1536次custom，共48窗/6144次；bit100实际拒错、完整128位、退休/CSR、AB/BA和双方精确重放通过。结合第51/58条，chain三数据集已闭合；本轮新增dataset2覆盖，收益与d0/d1一致。完整SP1-E仍未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

@cc77-builder / Agent，20261105-cc77-builder-sp1-e-chain-d2-target；2026-11-05T04:51:08.653767+00:00至2026-11-05T13:17:15.150939+08:00，任务跨度非人工工时；真实目标进程5个，正式墙钟1347.981秒。

| 本轮同镜像角色 | vdot正式均值/cycles | RVV正式均值/cycles | RVV/VDOT加速比 |
|---|---:|---:|---:|
| candidate-normal-recovery | 1601.25 | 5440.5 | 3.397658080× |
| baseline-normal-calibration | 1857.0 | 5440.5 | 2.929725363× |
| candidate-replay | 1601.25 | 5440.5 | 3.397658080× |
| baseline-replay | 1857.0 | 5440.5 | 2.929725363× |

initial：vdot周期下降13.772213%，RVV退化0.000000%，AB/BA收益分别13.785676%/13.758751%。

replay：vdot周期下降13.772213%，RVV退化0.000000%，AB/BA收益分别13.785676%/13.758751%。

| 历史同约束面积/μm² | 0f | SP1一拍候选 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

历史nominal 0f FU/父级setup slack分别-0.268520/-2.393998 ns。

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

面积/STA均原G2历史复用，trace-off局部边界，非整核PPA；新EDA为0，保留负slack。生产RTL与默认不变，无新核/上传。宿主时钟核查按实际结果留档，预算依据冻结单调时钟；历史FAIL保留，本轮未重试目标。

路线影响：开始 SP1-E micro single-d0 的合同与宿主准入准备：沿用 G0 冻结矩阵，核查同镜像12窗、6次custom、bit100、完整128位结果、退休/CSR、平衡执行顺序及精确重放，完成最小运行器适配和6300/7200秒预算评审。按G0固定single的vdot与RVV各自最多2%退化门槛；预算依据不足就HOLD。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出GO/HOLD和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d2-g0/target-20261105-01/RESULT.md) · [下一步](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-chain-d2-g0/target-20261105-01/NEXT_STEP.md)。


## 61. SP1-E micro single-d0 宿主准入与执行冻结（2026-11-05）

**GO（宿主准入）：single-d0合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d0的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

@cc77-builder / Agent；20261105-cc77-builder-sp1-e-single-d0-host；2026-11-05T05:20:45.150558+00:00 至 2026-11-05T13:33:53.988317+08:00，任务跨度非人工工时。

运行器92项、独立预冻结114项、独立冻结后32项全部通过。完整12窗/6次custom、全128位和接受源、退休融合/CSR、single专用bit100、逐窗控制相等、两方法各2%精确边界及八类原始重放字段已核查。首轮负控发现ENQUEUE编码未绑定，已仅在本轮宿主adapter补强并复核，G0冻结检查器未改。执行闭包5095项/134源码；实际12个模块和5个动态JSON全部在冻结清单。缺失运行授权在目标启动前拒绝，冻结未消费。

历史同镜像single-d0完整0f记录为72465 guest、12窗/6custom，覆盖完整启动、每窗寄存器搬运/CSR/结果与自检、UART及GOOD TRAP。最近同运行时chain-d2完整单调墙钟1347.981秒、目标累计1202.740秒、非目标145.241秒仅作运行机制参考，不线性外推single完成保证。新single完整收据解析实测1.775218秒，正常26次解析投影46.155679秒；最终5095项/673027925字节冻结完整verify实测1.604002秒，按保守12轮verify加26次正常解析投影约65.404秒，低于900秒预留。负控解析、监督、身份、序列化、清理等开销不视为零，另由历史完整非目标记录交叉支持。依据支持一次有界尝试，未来CPU/资源改变或输入/预算依据不足仍HOLD；硬上限保持6300/7200秒。

| 工作负载与资格 | 0f VDOT/RVV cycles | SP1 VDOT/RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT |
|---|---:|---:|---:|---:|
| chain-d0，历史第51条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d1，历史第58条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d2，历史第60条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| **本轮single-d0新五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 历史同约束成本 | 0f | SP1一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal父级setup slack/ns | -2.393998 | -2.337809 |

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点→终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

新三指标NOT_TESTED，以上成本为历史同库/边界trace-off复用；负slack保留。生产445项未变；零新EMU/NEMU/生产库加载/RTL/新核/EDA/GitHub写入。宿主失败修订保留，不属于目标重试。

路线影响／接续：开始 SP1-E micro single-d0 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d0-g0/RESULT.md) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d0-g0/NEXT_STEP.md)。


## 62. SP1-E micro single-d0 五角色探针（2026-11-05）

**GO（single-d0）：五角色有界探针和独立复核全部通过。** VDOT平均周期71→70，下降1.408451%；RVV维持85.25cycles，加速比1.200704225×→1.217857143×。四个正常角色各12窗/6custom，共48窗/24次；专用bit100拒错、完整128位结果、退休/CSR、逐窗控制及双方精确重放通过。只增加single-d0资格，未新增RTL优化；完整SP1-E仍未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

@cc77-builder / Agent，20261105-cc77-builder-sp1-e-single-d0-target；2026-11-05T05:40:49.953747+00:00至2026-11-05T13:57:41.955645+08:00，任务跨度非人工工时；真实目标进程5个，正式墙钟834.653秒。

| 本轮同镜像角色 | vdot正式均值/cycles | RVV正式均值/cycles | RVV/VDOT加速比 |
|---|---:|---:|---:|
| candidate-normal-recovery | 70.0 | 85.25 | 1.217857143× |
| baseline-normal-calibration | 71.0 | 85.25 | 1.200704225× |
| candidate-replay | 70.0 | 85.25 | 1.217857143× |
| baseline-replay | 71.0 | 85.25 | 1.200704225× |

initial：vdot周期下降1.408451%，RVV退化0.000000%，AB/BA子组变化（仅描述）分别1.408451%/1.408451%。

replay：vdot周期下降1.408451%，RVV退化0.000000%，AB/BA子组变化（仅描述）分别1.408451%/1.408451%。

| 历史同约束面积/μm² | 0f | SP1一拍候选 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

历史nominal 0f FU/父级setup slack分别-0.268520/-2.393998 ns。

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

面积/STA均原G2历史复用，trace-off局部边界，非整核PPA；新EDA为0，保留负slack。生产RTL与默认不变，无新核/上传。宿主时钟核查按实际结果留档，预算依据冻结单调时钟；历史FAIL保留，本轮未重试目标。

路线影响：开始 SP1-E micro single-d1 的合同与宿主准入准备：复用 single-d0 机制，核查 G0 冻结镜像、12窗和6次custom、专用bit100、完整128位结果、退休/CSR及精确重放，完成运行器适配和6300/7200秒预算评审。按G0保持VDOT与RVV各自最多2%退化、逐窗控制相等和平衡执行顺序，预算不足就HOLD。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d0-g0/target-20261105-01/RESULT.md) · [下一步](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d0-g0/target-20261105-01/NEXT_STEP.md)。


## 63. SP1-E micro single-d1 宿主准入与执行冻结（2026-11-05）

**GO（宿主准入）：single-d1合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d1的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

@cc77-builder / Agent；20261105-cc77-builder-sp1-e-single-d1-host；2026-11-05T06:00:59.972544+00:00 至 2026-11-05T14:09:17.047795+08:00，任务跨度非人工工时。

运行器97项（47机制＋50适配）、独立预冻结114项和冻结后32项全部通过。核查single-d1专用镜像/数据与12窗/6custom，负数点积完整128位000000000000000000000000fffe0400、退休逻辑17/21及instret12/16、CSR、专用bit100、两方法各2%精确门槛和八类原始精确重放；误用d0图像、case、raw、收据、旧freeze均拒绝。冻结5426项/143源码，实际12个模块及5个动态JSON全部闭合；缺失运行授权在启动前拒绝，锁未消费。

d1历史完整0f为72465 guest、12窗/6custom、3387546字节日志，完整程序核查通过。与d0的kernel/main源和.text逐字一致，仅0x80003aa8的dataset打印常量0→1及数据区38字节不同，没有删减验证。最近同运行时single-d0五角色实测单调834.652753秒、目标771.211695秒、非目标63.441059秒，提供完整机制参考，不转授d1资格。新d1完整收据解析1.665232322秒；最终5426项/687207816字节冻结的根级完整verify为1.526349759秒，独立verify＋import观察4.274064319秒。取较大观察值按12轮verify加26次正常解析作保守工作量投影约94.585秒，低于900秒宿主预留。负控解析、监督/身份、序列化和清理仍计入完整外层；这些是观测与投影，不是未来数学最坏保证。依据足以准入一次有界尝试，资源或输入漂移时仍HOLD，6300/7200秒硬上限不变。

| 工作负载与资格 | 0f VDOT/RVV cycles | SP1 VDOT/RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT |
|---|---:|---:|---:|---:|
| chain-d0，历史第51条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d1，历史第58条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d2，历史第60条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| single-d0，历史第62条 | 71.0/85.25 | 70.0/85.25 | 1.200704× | 1.217857× |
| **本轮single-d1新五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 历史同约束成本 | 0f | SP1一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal父级setup slack/ns | -2.393998 | -2.337809 |

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点→终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

新三指标NOT_TESTED，以上成本为历史同库/边界trace-off复用；负slack保留。生产445项未变；零新EMU/NEMU/生产库加载/RTL/新核/EDA/GitHub写入。历史宿主失败保留，本轮未重试目标。

路线影响／接续：开始 SP1-E micro single-d1 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d1-g0/RESULT.md) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d1-g0/NEXT_STEP.md)。


## 64. SP1-E micro single-d1 五角色探针（2026-11-05）

**GO（single-d1）：五角色有界探针、独立指标及功能审计通过。** VDOT平均周期71→70，下降1.408451%；RVV维持85.25cycles，加速比1.200704225×→1.217857143×。四个正常角色各12窗/6custom，共48窗/24次；专用bit100拒错、完整128位结果、退休/CSR、逐窗控制及双方精确重放通过。仅新增single-d1资格，本轮未改RTL。完整SP1-E尚未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

@cc77-builder / Agent，20261105-cc77-builder-sp1-e-single-d1-target；2026-11-05T06:12:00.708439+00:00至2026-11-05T14:32:57.676210+08:00，任务跨度非人工工时；真实目标进程5个，正式墙钟801.857秒。

| 本轮同镜像角色 | vdot正式均值/cycles | RVV正式均值/cycles | RVV/VDOT加速比 |
|---|---:|---:|---:|
| candidate-normal-recovery | 70.0 | 85.25 | 1.217857143× |
| baseline-normal-calibration | 71.0 | 85.25 | 1.200704225× |
| candidate-replay | 70.0 | 85.25 | 1.217857143× |
| baseline-replay | 71.0 | 85.25 | 1.200704225× |

initial：vdot周期下降1.408451%，RVV退化0.000000%，AB/BA子组变化（仅描述）分别1.408451%/1.408451%。

replay：vdot周期下降1.408451%，RVV退化0.000000%，AB/BA子组变化（仅描述）分别1.408451%/1.408451%。

| 历史同约束面积/μm² | 0f | SP1一拍候选 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

历史nominal 0f FU/父级setup slack分别-0.268520/-2.393998 ns。

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

面积/STA均原G2历史复用，trace-off局部边界，非整核PPA；新EDA为0，保留负slack。生产RTL与默认不变，无新核/上传。宿主时钟核查按实际结果留档，预算依据冻结单调时钟；历史FAIL保留，本轮未重试目标。

路线影响：开始 SP1-E micro single-d2 的合同与宿主准入准备：复用 single-d1 机制，核查 G0 冻结镜像、12窗和6次custom、专用bit100、完整128位结果、退休/CSR及精确重放，完成运行器适配和6300/7200秒预算评审。按G0保持VDOT与RVV各自最多2%退化、逐窗控制相等和平衡执行顺序，预算不足就HOLD。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d1-g0/target-20261105-01/RESULT.md) · [下一步](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d1-g0/target-20261105-01/NEXT_STEP.md)。


## 65. SP1-E micro single-d2 宿主准入与执行冻结（2026-11-05）

**GO（宿主准入）：single-d2合同、运行器适配、正负控、预算评审与执行冻结完成，可在下一轮明确指令后启动一次五角色有界探针。** 本轮未运行EMU/NEMU，single-d2的SP1目标正确性及加速比仍NOT_TESTED；默认0f＋firstdot V2＋原C8不变。

@cc77-builder / Agent；20261105-cc77-builder-sp1-e-single-d2-host；2026-11-05T06:38:14.593741+00:00 至 2026-11-05T14:47:50.796890+08:00，任务跨度非人工工时。

运行器103项（50机制＋53适配）、独立预冻结114项和冻结后32项全部通过。核查single-d2专用镜像/数据与12窗/6custom，低8项有符号正负抵消为0、完整128位00000000000000000000000000000000，全部6次接受源及高96位独立校验；退休逻辑17/21及instret12/16、CSR、专用bit100、ENQUEUE身份、两方法各2%精确门槛和八类原始精确重放均有正负控。d0/d1镜像、case、raw、收据、旧freeze误用均拒绝。冻结5771项/152源码，实际12个自定义模块及5个动态JSON全部在闭包；缺授权在启动前拒绝，正式执行锁未消费。

d2历史完整0f为72465 guest、12窗/6custom、3387546字节日志，完整程序核查通过。与d1的kernel/main源和.text逐字一致，仅0x80003aa8的dataset打印立即数1→2及数据区70字节不同，没有删减验证。最近同运行时single-d1五角色实测单调801.857455595秒、目标737.658433015秒、非目标64.199022580秒，提供完整机制参考，不转授d2资格。CPU4完整d2收据解析运行器1.701140831秒、预算独立解析1.651666442秒，取较大观察值。最终5771项/701571765字节冻结根级完整verify为1.706213595秒，独立verify/import为1.675858319秒，完整独立子进程1.731043953秒。仍保留较慢继承哈希观察3.064420625秒作固定工作量投影：26次正常解析＋12轮哈希/verify约81.002709106秒，小于900秒预留。负控解析、监督/身份、序列化和清理仍计入完整外层；这些是完整程序证据、宿主观测和工作量投影，不是未来最坏墙钟保证。支持准入一次有界尝试，输入/资源漂移或准备预算不足仍HOLD；6300/7200秒硬上限不变。

| 工作负载与资格 | 0f VDOT/RVV cycles | SP1 VDOT/RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT |
|---|---:|---:|---:|---:|
| chain-d0，历史第51条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d1，历史第58条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| chain-d2，历史第60条 | 1857.0/5440.5 | 1601.25/5440.5 | 2.929725× | 3.397658× |
| single-d0，历史第62条 | 71.0/85.25 | 70.0/85.25 | 1.200704× | 1.217857× |
| single-d1，历史第64条 | 71.0/85.25 | 70.0/85.25 | 1.200704× | 1.217857× |
| **本轮single-d2新五角色** | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED |

| 历史同约束成本 | 0f | SP1一拍候选 |
|---|---:|---:|
| FU面积/μm² | 17298.246 | 18322.878 |
| 含FU父级面积/μm² | 284614.946 | 285241.642 |
| nominal FU setup slack/ns | -0.268520 | -0.790381 |
| nominal父级setup slack/ns | -2.393998 | -2.337809 |

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点→终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

新三指标NOT_TESTED，以上成本为历史同库/边界trace-off复用；负slack保留。生产445项未变；零新EMU/NEMU/生产库加载/RTL/新核/EDA/GitHub写入。历史宿主失败保留，本轮未重试目标。

路线影响／接续：开始 SP1-E micro single-d2 五角色有界探针，按 NEXT_STEP 先核查已有进程、冻结输入和资源，再依次完成 bit100 拒错、候选恢复、0f 校准、候选重放和0f重放。保持6300/7200秒预算、CPU4/整组4线程、原guest/RSS/日志上限、完整12窗和6次custom、VDOT与RVV各自最多2%退化、逐窗控制相等及精确重放门槛。失败即停，不重试、不加时、不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新加速比、面积、时序，给出结论和下一轮指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d2-g0/RESULT.md) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d2-g0/NEXT_STEP.md)。


## 66. SP1-E micro single-d2 五角色探针（2026-11-05）

**GO（single-d2）：五角色有界探针、独立指标与功能审计通过。** VDOT平均周期71→70，下降1.408451%；RVV保持85.25cycles，加速比1.200704225×→1.217857143×。四个正常角色各12窗/6custom，共48窗/24次；专用bit100拒错、完整128位全零、接受源、退休/CSR、逐窗控制及双方精确重放通过。结合第62/64条，single三个数据集已分别完成目标验收，收益一致；本轮补齐数据覆盖，未新增RTL优化。完整SP1-E尚未验收，默认0f＋firstdot V2＋原C8不变，最终采用由用户决定。

@cc77-builder / Agent，20261105-cc77-builder-sp1-e-single-d2-target；2026-11-05T06:56:32.525610+00:00至2026-11-05T15:14:16.423579+08:00，任务跨度非人工工时；真实目标进程5个，正式墙钟774.160秒。

| 本轮同镜像角色 | vdot正式均值/cycles | RVV正式均值/cycles | RVV/VDOT加速比 |
|---|---:|---:|---:|
| candidate-normal-recovery | 70.0 | 85.25 | 1.217857143× |
| baseline-normal-calibration | 71.0 | 85.25 | 1.200704225× |
| candidate-replay | 70.0 | 85.25 | 1.217857143× |
| baseline-replay | 71.0 | 85.25 | 1.200704225× |

initial：vdot周期下降1.408451%，RVV退化0.000000%，AB/BA子组变化（仅描述）分别1.408451%/1.408451%。

replay：vdot周期下降1.408451%，RVV退化0.000000%，AB/BA子组变化（仅描述）分别1.408451%/1.408451%。

| 历史同约束面积/μm² | 0f | SP1一拍候选 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

历史nominal 0f FU/父级setup slack分别-0.268520/-2.393998 ns。

| SP1历史STA档位 | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 历史nominal关键路径 | arrival/ns | required/ns | slack/ns | 起点 → 终点 |
|---|---:|---:|---:|---|
| FU/ready | 0.218001 | 0.85 | 0.631999 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| FU/all_max | 1.709455 | 0.919074 | -0.790381 | io_in_bits_data_src_0[14] (input port clocked by core_clk) → c8968 (rising edge-triggered flip-flop clocked by core_clk) |
| 父级/ready | 0.303064 | 0.85 | 0.546936 | io_out_ready (input port clocked by core_clk) → io_in_ready (output port clocked by core_clk) |
| 父级/gate_enable | 1.713544 | 0.877842 | -0.835702 | c201714 (rising edge-triggered flip-flop clocked by core_clk) → c203281 (rising clock gating-check end-point clocked by core_clk) |
| 父级/all_max | 3.259825 | 0.922016 | -2.337809 | io_in_bits_vpu_vsew[1] (input port clocked by core_clk) → c201899 (rising edge-triggered flip-flop clocked by core_clk) |

面积/STA均原G2历史复用，trace-off局部边界，非整核PPA；新EDA为0，保留负slack。生产RTL与默认不变，无新核/上传。宿主时钟核查按实际结果留档，预算依据冻结单调时钟；历史FAIL保留，本轮未重试目标。

路线影响：开始 SP1-E 剩余验收收口与共享运行器复用评审：结合已通过的chain、single和原C8性能三数据集，固定剩余必验清单、暂缓项、验收终点和执行批次；复用已验证的公共宿主机制，只补用例/镜像差异检查。保留各case完整覆盖、原性能门槛、6300/7200秒预算及失败即停要求，不用代表性抽样替代未验证项。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后给出必要缺项、GO/HOLD及下一批执行指令。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d2-g0/target-20261105-01/RESULT.md) · [下一步](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-micro-single-d2-g0/target-20261105-01/NEXT_STEP.md)。


## 67. 2026-11-05 SP1-E剩余验收收口与共享运行器复用评审

GO：六个batch/stream用例集中做共享宿主迁入与差异准入；HOLD：剩余目标执行及完整SP1-E。20项必验中9项已通过、11项待完成；未变公共机制复用，逐case完整覆盖和原门槛保留。默认0f＋firstdot V2＋原C8不变。

本轮新增加速比/面积/时序均NOT_TESTED；已通过case仍9/20。剩余6个micro集中准备、2个保护后续准备、3个预算HOLD。共享入口尚未实现，全部11个剩余case目标执行未准入。保持每case6300/7200秒、完整覆盖、原门槛、失败即停。

| 负载（各d0/d1/d2已分别验证） | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f加速比 | SP1加速比 | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| chain | 1857 | 1601.25 | 5440.5/5440.5 | 2.929725363× | 3.397658080× | 13.772213% |
| single | 71 | 70 | 85.25/85.25 | 1.200704225× | 1.217857143× | 1.408451% |
| C8-basic | 643.75 | 642.5 | 356/356 | 0.553009709× | 0.554085603× | 0.194175% |
| C8-reuse | 273 | 272 | 299/299 | 1.095238095× | 1.099264706× | 0.366300% |

C8-basic仍慢于RVV；不能只展示chain最高倍数代表端到端应用收益。

| 历史面积/μm² | 0f | SP1 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

Nangate45 Typical 1.1V 25℃，原G2 trace-off局部边界；不是整核PPA、布局布线签核或Fmax。0f nominal FU/父级setup slack为−0.268520/−2.393998ns。

| SP1原五档STA | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

原P4严格G2的NO-GO和SP0放宽成本预算的后续准入记录均保留，不将本轮标成新EDA或消除负slack。


本轮只做有限收口规划；完整验收须20项全部闭合，HOLD不当PASS。下一轮B0只实现共享宿主入口及六例差异门禁，不启动目标。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-closeout-review-20261105/RESULT.md) · [完整计划](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-closeout-review-20261105/PLAN.md) · [下一轮](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-closeout-review-20261105/NEXT_STEP.md)。


## 68. 2026-11-05 SP1-E B0六用例共享宿主入口与准入

GO：batch/stream六例共享宿主入口、差异正负控、实际执行冻结和有界预算准入完成；batch三例可在下一轮明确授权后整批执行。本轮没有EMU/NEMU或新性能资格，完整SP1-E仍9/20已验，默认0f＋firstdot V2＋原C8不变。

开始 2026-11-05T07:37:54.659384+00:00；结束 2026-11-05T08:10:45.939102+00:00（记录时区UTC+08：2026-11-05T16:10:45.939102+08:00）；@cc77-builder / Agent；操作ID 20261105-cc77-builder-sp1-e-b0-shared-micro。

共享入口＋六份冻结实物完成；420逐例功能、204收据、12共享/9角色/4授权单元测试（授权39子检查），六份冻结138项正负控通过。保守宿主投影554.529≤900秒，原6300/7200秒不变。无目标/生产库/RTL/全核/EDA/默认/GitHub改动；未采用候选不因宿主GO自动采用。

本轮新加速比、面积、时序均NOT_TESTED；以下旧实测按原合同复用。

| 负载（各d0/d1/d2已分别验证） | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f加速比 | SP1加速比 | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| chain | 1857 | 1601.25 | 5440.5/5440.5 | 2.929725363× | 3.397658080× | 13.772213% |
| single | 71 | 70 | 85.25/85.25 | 1.200704225× | 1.217857143× | 1.408451% |
| C8-basic | 643.75 | 642.5 | 356/356 | 0.553009709× | 0.554085603× | 0.194175% |
| C8-reuse | 273 | 272 | 299/299 | 1.095238095× | 1.099264706× | 0.366300% |

C8-basic仍慢于RVV；不能只展示chain最高倍数代表端到端应用收益。

| 历史面积/μm² | 0f | SP1 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

Nangate45 Typical 1.1V 25℃，原G2 trace-off局部边界；不是整核PPA、布局布线签核或Fmax。0f nominal FU/父级setup slack为−0.268520/−2.393998ns。

| SP1原五档STA | 周期/ns | 负载/fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

原P4严格G2的NO-GO和SP0放宽成本预算的后续准入记录均保留，不将本轮标成新EDA或消除负slack。


路线接续：下一轮只运行B1 batch d0/d1/d2，逐例五角色，整批首错停止，最多15进程/18900目标秒/21600外层秒，不能借预算或自动进入stream。原FAIL及本轮宿主夹具/报告写入失败均保留。

[结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/RESULT.md) · [下一轮完整指令](../optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/NEXT_STEP.md)。


## 69. 2026-11-05 SP1-E B1 batch三数据集有界执行

B1 batch d0/d1/d2五角色全部通过；完整SP1-E必验进度从9/20推进到12/20。默认仍为0f＋firstdot V2＋原C8，SP1候选未切默认；stream及其余保护缺项未冒充通过。

开始2026-11-05T08:18:16.724676+00:00；结束2026-11-05T09:46:42.297275+00:00；记录时区UTC+08：2026-11-05T17:46:42.297275+08:00；@cc77-builder / Agent；操作ID 20261105-cc77-builder-sp1-e-b1-batch-target。

目标进程15/15，目标累计2436.957/18900秒，批次外层2779.241/21600秒；每例6300/7200秒、原资源/guest与失败即停合同不变。已完成角色按各自覆盖独立复核，完整五角色才授予该例性能资格；不以local latency或bit100代替完整性能资格。

本轮周期为同镜像、同运行参数的新实测；面积和时序为原G2同候选trace-off局部边界历史复用。各数据集分别列出，不合成总加速比。

| 数据集 | 五角色资格 | 0f VDOT cycles | SP1 VDOT cycles | 0f RVV cycles | SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 | RVV退化 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| d0 | PASS | 221 | 221 | 678 | 678 | 3.067873303× | 3.067873303× | 0.000000000% | 0.000000000% |
| d1 | PASS | 221 | 221 | 678 | 678 | 3.067873303× | 3.067873303× | 0.000000000% | 0.000000000% |
| d2 | PASS | 221 | 221 | 678 | 678 | 3.067873303× | 3.067873303× | 0.000000000% | 0.000000000% |

每角色12窗全部保留，其中每算法4个measured窗计算均值；first/warmup不混入均值。每VDOT窗128次custom、每正常角色768次；instret为VDOT232/RVV552。首次和重放比较均须单独通过VDOT/RVV最多2%退化及逐窗控制相等；同硬件8项摘要精确重放。AB/BA描述结果保留，但不移植chain的10%门槛。完整144窗明细（若整批通过）见metric-review/review-r1/all-windows.csv。

| 历史面积 μm² | 0f | SP1 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

Nangate45 Typical 1.1V 25℃，原G2 trace-off局部FU/父级范围；新综合、新STA均NOT_TESTED，不代表整核、布线签核或Fmax。0f nominal FU/父级slack分别−0.268520/−2.393998ns。

| SP1历史五档STA | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1 nominal关键路径 | arrival ns | required ns | slack ns |
|---|---:|---:|---:|
| fu/r2r | 1.020088 | 0.924317 | -0.095771 |
| fu/i2r | 1.709455 | 0.919074 | -0.790381 |
| fu/ready | 0.218001 | 0.85 | 0.631999 |
| parent/i2r | 3.259825 | 0.922016 | -2.337809 |
| parent/ready | 0.303064 | 0.85 | 0.546936 |
| parent/vdot_i2r | 2.176863 | 0.919473 | -1.25739 |
| parent/gate_enable | 1.713544 | 0.877842 | -0.835702 |

原P4严格G2 NO-GO、各档负slack及放宽预算的SP0准入并存；本轮不会消除旧失败。历史chain最高加速比不能代替batch或C8端到端收益。完整成本来源、其他档路径和起止端点保留于METRICS.json。


宿主离线审计两项首轮格式/时钟边界误判已修订并补正负控；原FAIL完整保留，没有目标重试或冻结运行器改动。

路线影响：开始 SP1-E B2 stream 三数据集五角色有界执行：按 NEXT_STEP 先核查进程和冻结输入，确认B1全通过，再按 d0→d1→d2 串行执行 performance-d0-s03、performance-d1-s03、performance-d2-s03。每例保持6300/7200秒及原CPU4、整组4线程、RSS12GiB、日志2GiB与guest上限；整批最多15个目标进程、18900秒目标累计、21600秒外层预算，不借用预算。保留完整12窗、384次custom、递增地址/三条退休融合及专用bit100、VDOT/RVV各自最多2%退化、完整128位、退休/CSR、逐窗控制及精确重放。任一失败立即停止整批，不重试、不加时、不跳过继续、不自动扩围。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新三项指标和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B1-batch/RESULT.md) · [下一轮完整指令](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B1-batch/NEXT_STEP.md)。


## 70. 2026-11-05 SP1-E B2 stream三数据集有界执行

B2 stream d0/d1/d2五角色全部通过；完整SP1-E必验进度从12/20推进到15/20。默认仍为0f＋firstdot V2＋原C8，SP1候选未切默认；其余保护及普通C调用缺项未冒充通过。

开始2026-11-05T09:52:15.251079+00:00；结束2026-11-05T11:55:58.830922+00:00；记录时区UTC+08：2026-11-05T19:55:58.830922+08:00；@cc77-builder / Agent；操作ID 20261105-cc77-builder-sp1-e-b2-stream-target。

目标进程15/15，目标累计3523.837/18900秒，批次外层3895.471/21600秒；每例6300/7200秒、原资源/guest与失败即停合同不变。已完成角色按各自覆盖独立复核，完整五角色才授予该例性能资格；不以local latency或bit100代替完整性能资格。

本轮周期为同镜像、同运行参数的新实测；面积和时序为原G2同候选trace-off局部边界历史复用。各数据集分别列出，不合成总加速比。

| 数据集 | 五角色资格 | 0f VDOT cycles | SP1 VDOT cycles | 0f RVV cycles | SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 | RVV退化 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| d0 | PASS | 1127.5 | 1126.25 | 1133 | 1133 | 1.004878049× | 1.005993341× | 0.110864745% | 0.000000000% |
| d1 | PASS | 1127.5 | 1126.25 | 1133 | 1133 | 1.004878049× | 1.005993341× | 0.110864745% | 0.000000000% |
| d2 | PASS | 1127.5 | 1126.25 | 1133 | 1133 | 1.004878049× | 1.005993341× | 0.110864745% | 0.000000000% |

每角色12窗全部保留，其中每算法4个measured窗计算均值；first/warmup不混入均值。每VDOT窗64次custom、每正常角色384次；instret为VDOT648/RVV904。首次和重放比较均须单独通过VDOT/RVV最多2%退化及逐窗控制相等；同硬件8项摘要精确重放。AB/BA描述结果保留，但不移植chain的10%门槛。完整144窗明细（若整批通过）见metric-review/all-windows.csv。

整程序guest cycles与计时窗均值分开留档；整程序包含启动、自检、输出及窗外控制，不能替代冻结窗口的性能门槛。

| 数据集 | 候选首次/重放 guest cycles | 0f首次/重放 guest cycles |
|---|---:|---:|
| performance-d0-s03 | 109372 / 109372 | 109336 / 109336 |
| performance-d1-s03 | 109372 / 109372 | 109336 / 109336 |
| performance-d2-s03 | 109372 / 109372 | 109336 / 109336 |

| 历史面积 μm² | 0f | SP1 |
|---|---:|---:|
| FU | 17298.246 | 18322.878 |
| 含FU真实父级 | 284614.946 | 285241.642 |

Nangate45 Typical 1.1V 25℃，原G2 trace-off局部FU/父级范围；新综合、新STA均NOT_TESTED，不代表整核、布线签核或Fmax。0f nominal FU/父级slack分别−0.268520/−2.393998ns。

| SP1历史五档STA | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| SP1 nominal关键路径 | arrival ns | required ns | slack ns |
|---|---:|---:|---:|
| fu/r2r | 1.020088 | 0.924317 | -0.095771 |
| fu/i2r | 1.709455 | 0.919074 | -0.790381 |
| fu/ready | 0.218001 | 0.85 | 0.631999 |
| parent/i2r | 3.259825 | 0.922016 | -2.337809 |
| parent/ready | 0.303064 | 0.85 | 0.546936 |
| parent/vdot_i2r | 2.176863 | 0.919473 | -1.25739 |
| parent/gate_enable | 1.713544 | 0.877842 | -0.835702 |

原P4严格G2 NO-GO、各档负slack及放宽预算的SP0准入并存；本轮不会消除旧失败。历史chain最高加速比不能代替stream或C8端到端收益。完整成本来源、其他档路径和起止端点保留于METRICS.json。


B1历史宿主FAIL及其修订保留；本轮stream差异正负控和终态离线复算通过，没有目标重试或冻结运行器改动。

路线影响：开始 SP1-E B3 原功能保护的专用宿主合同与预算准入：集中核查 legacy-control、o2-all-pairs、o2-control，复用未变公共机制，明确当前候选的完整功能、取消/反压、DIV混合、CSR/全向量结果、负控及重放合同，补齐专用收集器和宿主正负控。按原每例6300/7200秒及资源约束逐例审查预算，guest上限按各自冻结工作量论证，不套用micro的300000上限；o2-control证据不足继续HOLD，不借时、不加时、不重复短校准。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后逐例给出GO/HOLD、必要缺项和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B2-stream/RESULT.md) · [下一轮完整指令](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b0-shared-micro-20261105/batches/B2-stream/NEXT_STEP.md)。


## 71. 2026-11-05 SP1-E B3 原功能保护宿主合同与预算

三例宿主合同与检查器完成；legacy-control/o2-all-pairs有条件预算GO进入执行接入，o2-control预算HOLD。当前三例均非TARGET_READY，专用运行器/执行冻结/CPU4完整宿主900秒门尚待下一轮。

开始2026-11-05T12:01:34.959734+00:00；结束2026-11-05T12:20:08.393782+00:00；记录2026-11-05T20:20:08.393782+08:00；@cc77-builder / Agent；操作ID SP1-E-B3-HOST-20261105-01。

三例当前候选目标功能均NOT_TESTED；完整SP1-E仍15/20。本轮检查器93项初版＋修订针对性门、独立合同/预算核查及源身份保护通过；旧证据保持，不新增目标/RTL/核/EDA/GitHub操作。

本轮加速比、面积、时序新测量均为NOT_TESTED。以下仅复用第70条B2历史实测/原G2历史成本，不把宿主测试PASS计成新硬件收益。

| 指标 | 0f | SP1候选 | 来源/资格 |
|---|---:|---:|---|
| stream d0/d1/d2 VDOT均值cycles，各例相同 | 1127.50 | 1126.25 | B2同镜像完整五角色 |
| stream d0/d1/d2 RVV均值cycles，各例相同 | 1133 | 1133 | B2同镜像完整五角色 |
| stream RVV/VDOT，各例相同 | 1.004878049× | 1.005993341× | B2，VDOT下降0.110864745% |
| FU面积μm² | 17298.246 | 18322.878 | 原G2局部trace-off |
| 含FU真实父级面积μm² | 284614.946 | 285241.642 | 原G2局部trace-off |
| nominal FU setup slack ns | −0.268520 | −0.790381 | 历史1ns/5fF |
| nominal父级setup slack ns | −2.393998 | −2.337809 | 历史1ns/5fF |

Nangate45 Typical 1.1V 25℃，不是整核面积、签核或Fmax，负slack继续保留。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1.0 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2.0 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1.0 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1.0 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

全部关键路径、起止点和来源保留在METRICS.json；原严格G2 NO-GO不因本轮宿主通过而变成时序PASS。三个功能保护程序无RVV对照性能窗，不新增2%退化资格。


路线影响：开始 SP1-E B3 两例执行接入与有界验证：仅 legacy-control→o2-all-pairs，先接入专用五角色外层，核验真实进程/参考映射及资源回执，完成执行源码冻结、宿主正负控和CPU4下完整核验/解析开销审计；实际调用图的宿主开销须通过900秒门，全部准入后再串行执行两例。每例保持300/1500×4秒、目标6300/外层7200秒；整批最多10个目标进程、目标12600秒/外层14400秒，不借时。负控guest各100000，正常guest分别800000/300000，CPU4/整组4线程/RSS12GiB/日志2GiB不变。保留原完整功能、128位、CSR、bit100、八维功能精确重放；不把无计时窗程序当性能测试。任何准入或执行失败立即停止整批，不重试、不加时、不跳过继续；o2-control保持HOLD，不扩围、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-protection-host-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-protection-host-20261105/NEXT_STEP.md)。


## 72. 2026-11-05 SP1-E B3 两例执行接入：宿主闭包FAIL，整批HOLD

两例运行器和宿主机制完成；正式CPU4执行闭包核验因遗漏四个cwd配套文件失败，900秒宿主门未建立，按失败即停终止整批。两例均未运行，原o2-control继续HOLD。

开始 2026-11-05T12:26:23.071225+00:00；结束 2026-11-05T12:53:19.201144+00:00；记录 2026-11-05T20:53:19.201144+08:00；@cc77-builder / Agent；操作ID SP1-E-B3-EXECUTION-20261105-01。

运行器最终10方法PASS，独立26项机制＋16项算术/历史回执控PASS；正式完整冻结核验遗漏四个cwd支持输入，900秒总门未建立。只读确认文件存在且与真实B2冻结一致；保留开发初次FAIL及本轮正式FAIL。新增目标0，两例NOT_RUN，o2-control继续HOLD，进度15/20不变。未修改生产RTL、构建新核、运行EDA、切默认或上传。

本轮加速比、面积、时序均为 NOT_TESTED；两例保护程序没有合格 RVV 计时对照，不能从功能通过或宿主开销推算加速比。以下为此前 B2 同镜像五角色结果和原 G2 局部成本的历史复用，未重新运行。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

全部来源、关键路径和逐窗历史重放资格保存在 METRICS.json；本轮宿主失败不改写既有性能结果，也不新增 SP1 功能资格。


路线影响／接续：开始 SP1-E B3-R1 宿主闭包修订：保留本轮 FAIL 和旧 HOST_FREEZE，在独立目录从已验证的真实 B2 执行冻结中提取候选及0f的 constantin.txt、plusArgs 四项精确路径、大小和SHA，建立可追溯输入 annex，并修订新执行闭包；补齐缺失、错路径、内容漂移负控，冻结新运行器源码，再做独立复核和CPU4实际调用图的完整900秒宿主开销门。保持两例完整功能及每例6300/7200秒、整批12600/14400秒和原资源/guest上限，失败即停、不重试、不加时；o2-control继续HOLD。本轮仅做宿主修订与准入，不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后逐例给出GO/HOLD、更新计分板，并仅在全部GO时给出两例串行执行指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-execution-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-execution-20261105/NEXT_STEP.md)。


## 73. 2026-11-05 SP1-E B3-R1 四文件执行冻结与宿主预算准入

四项cwd配套输入已从真实B2原冻结精确迁入，17方法及独立29项门通过；CPU4完整宿主预算两例468.345019776/331.801223876秒均低于900秒，正式执行冻结及最终增量复核通过。只完成宿主准入，目标进程0、两例未运行，旧FAIL保留，SP1-E仍15/20。

开始 2026-11-05T13:02:48.343032+00:00；结束 2026-11-05T13:22:50.287618+00:00；记录 2026-11-05T21:22:50.287618+08:00；@cc77-builder / Agent；操作ID SP1-E-B3-R1-HOST-20261105-01。

新宿主runner仅增加annex和inventory接入，源SHA 43af0b919f37da7dccbeea0955ebb0c192f9b34aa43f749e590f9a5bee362d91。17方法/独立29项正式门通过；两例各1010项执行冻结完成；旧65文件、991项HOST输入、445生产源码不变。第72条FAIL保留，本轮不是硬件修复或新目标PASS。原角色/完整覆盖/预算不降低，无EMU/NEMU/RTL/新核/EDA/默认/GitHub变化。

本轮加速比、面积、时序均为 NOT_TESTED；两例保护程序没有合格 RVV 计时对照，不能从功能通过或宿主开销推算加速比。以下为此前 B2 同镜像五角色结果和原 G2 局部成本的历史复用，未重新运行。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

全部来源、关键路径和逐窗历史重放资格保存在 METRICS.json；本轮宿主准入不改写既有性能结果，也不新增 SP1 功能资格。

## 本轮新增的宿主预算证据（不属于三项硬件指标）

| 用例 | 公式计算预留/秒 | 原宿主门/秒 | 余量/秒 | 准入 |
|---|---:|---:|---:|---|
| legacy-control | 468.345020 | 900 | 431.654980 | GO |
| o2-all-pairs | 331.801224 | 900 | 568.198776 | GO |

预留使用完整实测H/J/K/D/I、身份未变的历史P、固定4倍裕量和历史A。属于当前CPU4暖缓存下的实证预留，不是已发生的目标耗时，也不保证任意2GiB日志或冷盘都满足900秒。原实际900秒停止条件不变。


路线影响／接续：开始 SP1-E B3-R1 两例五角色有界执行，按 NEXT_STEP 先核查已有进程、冻结输入、独立最终增量复核及未消费锁，再为本轮明确创建目标授权，按 legacy-control→o2-all-pairs 串行执行。每例保留300/1500×4秒、目标6300秒/外层7200秒/宿主900秒；整批最多10个目标进程、目标12600秒/外层14400秒，不借预算。负控guest各100000，正常guest分别800000/300000，CPU4、整组4线程、RSS12GiB、每例日志2GiB以及原seed/RAM/reset不变。保持完整覆盖、128位、退休身份、CSR、bit100拒错与正常恢复、八维功能精确重放；这些功能程序没有性能计时窗。任何失败立即停止整批，不重试、不加时、不跳过继续、不扩围；o2-control继续HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板的三项指标及资格状态，给出结论和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/NEXT_STEP.md)。


## 74. 2026-11-05 SP1-E B3-R1 两例执行：首bit100的PC归属检查失败，整批停止

B3-R1整批在legacy首个bit100角色停止：注入PC0x80000298，DiffTest诊断PC为同提交组首0x80000294，冻结检查器要求二者相等而拒绝。真实运行1目标/8339guest/20.819646708秒；正常角色0、allpairs未启动。资源与清理通过，独立fail-stop审计通过但功能资格0；不重试，SP1-E仍15/20。

开始 2026-11-05T13:47:16.883096+00:00；结束 2026-11-05T14:02:18.538875+00:00；记录 2026-11-05T22:02:18.538875+08:00；@cc77-builder / Agent；操作ID SP1-E-B3-R1-TARGET-20261105-01。

启动前原两例冻结/独立检查通过；1个真实EMU加载冻结NEMU/负控库，exit1且实际v0高位差异恰bit100，但诊断使用组首PC，原严格PC相等门拒绝。未修改/重试；旧宿主GO、第72条FAIL及本轮FAIL各自保留。独立fail-stop审计通过不等于功能PASS。未来按用户偏好联合必要宿主修订和多项评审，随后仅对已准入白名单批量执行。

本轮加速比、面积、时序均为 NOT_TESTED；两例保护程序没有合格 RVV 计时对照，不能从功能通过或宿主开销推算加速比。以下为此前 B2 同镜像五角色结果和原 G2 局部成本的历史复用，未重新运行。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

全部来源、关键路径和逐窗历史重放资格保存在 METRICS.json；本轮负控资格失败不改写既有性能结果，也不新增 SP1 功能资格。


## 本轮真实负控尝试

| 指标 | 实际值 |
|---|---:|
| 目标进程/正常角色 | 1 / 0 |
| guest cycles | 8339 |
| 目标active墙钟/秒 | 20.819646708 |
| 单例外层/秒 | 22.807869535 |
| 单例宿主/秒 | 1.988222827 |
| 整批外层/秒 | 24.183595747 |
| 采样线程峰值 | 1 |
| 采样RSS峰值/bytes | 75628544 |
| 保留原始stdout＋stderr/bytes | 53865 |

这是一段拒错负控前缀，冻结检查器判为FAIL，不能由8339 guest或20.82秒外推完整程序预算、正常功能或加速比。原宿主预算468.345/331.801秒来自第73条准入，不是本轮实测目标耗时；未达到资源上限不等于通过负控。


路线影响／接续：开始 SP1-E B3-R2 拒错归属修订与剩余项集中宿主评审：保留B3-R1原FAIL、日志和已消费锁，在独立目录修订保护负控的PC归属检查，严格绑定冻结注入PC/指令字/目的寄存器、当前提交组及唯一bit100差异，不得忽略PC或仅凭exit1放行。用本轮真实日志做离线复核，补齐错误组、历史同PC、错误指令/寄存器/bit、重复注入和非预期退出等正负控，冻结新检查器依赖与执行闭包，独立审查预算影响。同轮集中核对o2-control、原C8普通C48、timed DIV/SQRT的真正宿主缺项与完整预算依据，复用未变公共证据，不重复无收益的短探针；无实质新依据就保留HOLD。保持原完整覆盖、五角色、6300/7200秒及900秒宿主门、原资源和失败即停，不重试、不加时。本轮先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；一次交付各项GO/HOLD、更新计分板，并仅为全部准入的精确白名单给出下一批串行执行指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/execution-01/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r1-host-20261105/execution-01/NEXT_STEP.md)。


## 75. 2026-11-05 SP1-E B3-R2 严格提交组修订与三项联合评审：宿主HOLD

严格提交组与组末最后写入者检查器已实现，真实R1日志和多写入者正控所在的前17方法通过；第18方法的错误dst变异因同时匹配历史slot15与当前slot31而断言失败，未调用该变异的生产checker，正式宿主门HOLD。方法19–23及后续运行器/独立正式门/预算门均NOT_RUN；目标0。三个暂缓项无当前组合完整预算新证据，继续HOLD；SP1-E仍15/20。

开始 2026-11-05T14:12:02.047935+00:00；结束 2026-11-05T15:06:33.735750+00:00；记录 2026-11-05T23:06:33.735750+08:00；@cc77-builder / Agent；操作ID SP1-E-B3-R2-HOST-20261105-01。

首17方法PASS不能替代全部门禁；第18错误dst夹具在历史与当前环各命中一次，唯一替换断言FAIL、该子控未调用checker。原R1 FAIL、R2 FAIL和未执行门禁分开留档。三个HOLD完整预算一次集中核查完成，无新当前组合证据；新发现1497秒旧o2-control及排除1秒C48合成收据。无新目标、RTL或EDA成果，默认保持。

本轮加速比、面积、时序均为 NOT_TESTED；两例保护程序没有合格 RVV 计时对照，不能从功能通过或宿主开销推算加速比。以下为此前 B2 同镜像五角色结果和原 G2 局部成本的历史复用，未重新运行。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

全部来源、关键路径和逐窗历史重放资格保存在 METRICS.json；本轮宿主修订不改写既有性能结果，也不新增 SP1 功能资格。



新实测加速比、面积、时序均 NOT_TESTED。R2本轮没有运行目标或EDA；宿主检查耗时另记budget-review，不能当作guest性能收益。历史详细数据与关键路径见 HISTORICAL_METRICS.json，原始证据路径继续有效。


路线影响／接续：开始 SP1-E B3-R3 夹具修订与两例批量验收：保留 R1/R2 原 FAIL、日志及旧锁，在独立目录仅修正错误目的寄存器负控的定位，精确锚定当前环尾 slot31、PC0x80000370 和完整行，先检查所有变异目标的唯一性。保持严格当前提交组、组末最后写入者完整128位、CSR/身份/重放及原完整覆盖，完成新源码冻结、全部宿主正负控、运行器接入、独立审查和900秒宿主预算准入；未变公共机制复用。全部门禁通过且两例均GO后，在同一轮仅按 legacy-control→o2-all-pairs 串行运行五角色。每例300＋4×1500秒，目标6300/外层7200/宿主900秒；整批最多10目标、目标累计12600秒、外层14400秒，不借预算。负控100000guest，正常分别800000/300000guest；CPU4、整组4线程、RSS12GiB、每例日志2GiB及原seed/RAM/reset不变。任一正式宿主门或目标失败立即停止，不重试、不加时、不跳过继续；三个暂缓项保持HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后一次更新计分板、三项指标及下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r2-host-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r2-host-20261105/NEXT_STEP.md)。


## 76. 2026-11-05 SP1-E B3-R3：23项checker与6项运行器通过，独立启动身份前提FAIL后HOLD

R3完成test18精确行定位，checker23/23、runtime6/6及源码二进制溯源PASS；独立门新增的准备快照boot相等条件遇WSL启动代际变化而FAIL，对抗控制0项。该前提比原执行身份协议过严，不是RTL或guest功能失败。按单轮失败即停，预算0次、目标0个；整体HOLD，SP1-E仍15/20。

开始 2026-11-05T15:19:25.401749+00:00；结束 2026-11-05T15:46:57.183856+00:00；记录 2026-11-05T23:46:57.183856+08:00；@cc77-builder / Agent；操作ID SP1-E-B3-R3-20261105-01。

准备期间boot32bd2caf→a06b9f10，btime晚于快照约75秒；新增的“准备快照boot必须持续不变”前提过严，是宿主合同问题而非RTL/guest功能失败。按冻结失败即停，预算与目标均0；原失败和两次准备辅助脚本失败保留。修正范围限test18精确当前行，生产checker/RTL不变。

本轮加速比、面积、时序均为 NOT_TESTED；两例保护程序没有合格 RVV 计时对照，不能从功能通过或宿主开销推算加速比。以下为此前 B2 同镜像五角色结果和原 G2 局部成本的历史复用，未重新运行。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

全部来源、关键路径和逐窗历史重放资格保存在 METRICS.json；本轮宿主修订不改写既有性能结果，也不新增 SP1 功能资格。



新实测加速比、面积、时序均 NOT_TESTED。R3本轮没有运行目标或EDA；宿主检查耗时另记budget-review，不能当作guest性能收益。历史详细数据与关键路径见 HISTORICAL_METRICS.json，原始证据路径继续有效。


路线影响／接续：开始 B3-R4，按 NEXT_STEP 在独立目录仅修订宿主准入的启动身份绑定：BEFORE.boot_id保留为历史快照，正式准入/执行前记录实时boot并绑定后续目标PID/start_ticks/单调时钟，不允许跨boot拼接运行。保留R1/R2/R3全部FAIL及旧锁；复用未变且身份匹配的23项checker、6项运行器和溯源证据，补齐该合同变更的正负控及尚未完成的独立对抗门、执行冻结和900秒预算门。全部通过且两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色。每例300＋4×1500秒、目标6300/外层7200/宿主900秒；整批最多10目标、目标累计12600秒/外层14400秒，不借时；负控100000guest、正常800000/300000guest、CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式门或目标任一失败即停，不重试、不加时、不跳过继续；三个暂缓项保持HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板、三项指标和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r3-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r3-20261105/NEXT_STEP.md)。


## 77. 2026-11-06 SP1-E B3-R4：HOLD

开始：2026-11-06T00:00:02.772841+08:00；结束：2026-11-06T00:46:59.722251+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R4-20261105-01。

B3-R4已修正准备期启动身份范围：旧boot只作历史，真实批次仍绑定boot/PID/start_ticks/单调时钟；4项新差异与65项独立检查一次通过，原6项运行器和23项checker按身份复用。唯一宿主预算进程超过900秒仍未返回，核实身份后在观测1012.62秒时发送SIGTERM，超限112.62秒已如实留档；两例预算均HOLD/null，EMU目标0，不重试，SP1-E仍15/20。

宿主差异新测 4 项：PASS_RUNTIME_HOST_TESTS；旧 runtime 6 项及 checker 23 项仅复用、未重跑；独立 65 项：PASS_B3_EXECUTION_HOST_REVIEW；预算：HOLD_B3_HOST_BUDGET。

- legacy-control：HOLD；host_budget_seconds=None；failure_stage=None；error=None
- o2-all-pairs：HOLD；host_budget_seconds=None；failure_stage=None；error=None

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | NOT_RUN | 0 | 0 | False |
| o2-all-pairs | NOT_RUN | 0 | 0 | False |

本轮新加速比、面积、时序均 NOT_TESTED。功能保护通过和宿主耗时不构成性能收益；默认仍为0f＋firstdot V2＋原C8。以下数值和关键路径保留原条件，未重跑EDA或性能对照。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

本轮实际目标进程 0，新增合格功能用例 0；没有新增性能合格项。完整历史数值、来源和未通过的时序条件见METRICS.json。

下一轮：开始 B3-R5：在独立目录仅修订宿主拒错检查器两条CSR行的空白匹配，将同行空白限制为[ \t]，并补齐预算测量的独立进程外墙钟监督；核查实际批次宿主解析也受原900/7200/14400秒限制可靠约束，必要时作最小外部监督接入。保留R1至R4全部失败、原24,558,348字节成本夹具、完整数值/CSR/身份/重放合同及原预算，不缩样、不加时。复用未变的运行器、身份、溯源证据，集中完成受影响正负控、外部超时小夹具、独立复核和一次预算准入；全部通过且两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色。每例300＋4×1500秒、目标6300/外层7200/宿主900秒；整批最多10目标、目标12600/外层14400秒，不借时；负控100000guest，正常800000/300000guest，CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式门或目标任一失败立即停止，不重试、不跳过继续、不扩围；三个暂缓项保持HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板、三项指标及下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r4-20261105/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r4-20261105/NEXT_STEP.md)。


## 78. 2026-11-06 SP1-E B3-R5：HOLD

开始：2026-11-06T10:19:51.632869+08:00；结束：2026-11-06T10:46:56.938495+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R5-20261106-01。

B3-R5完成两条CSR正则的同行空白修复，checker27/27一次PASS；新增进程外超时监督，runtime10/10及12次宿主进程夹具清理一次通过。独立审计错误地把历史出处符号链接也要求为直接canonical路径，在执行0/41项对抗控前FAIL；240项冻结内容及4份别名的字节/SHA均一致。这是本轮审计新增条件导致的假阻断。按失败即停，预算0次、EMU目标0，保留全部记录，整体HOLD、SP1-E仍15/20。

宿主差异新测 10 项：PASS_RUNTIME_HOST_TESTS；checker本轮新测 27 项：PASS_STRICT_NEGATIVE_CHECKER_HOST；旧runtime 6＋4 项仅复用、未重跑；独立实际 0 / 计划41，历史 65 项仅复用出处、未重跑：HOLD_B3_R5_INDEPENDENT_HISTORICAL_ALIAS_CHECK；预算：HOLD_B3_HOST_BUDGET。

- legacy-control：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_HOST_PREREQUISITE_FAILED_BEFORE_BUDGET；error=AssertionError: frozen file drift /home/riscv/riscv-lab/speedup-first-20261103/sp1-ab/candidate/difftest/src/test/csrc/difftest/difftest.cpp
- o2-all-pairs：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_HOST_PREREQUISITE_FAILED_BEFORE_BUDGET；error=AssertionError: frozen file drift /home/riscv/riscv-lab/speedup-first-20261103/sp1-ab/candidate/difftest/src/test/csrc/difftest/difftest.cpp

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | NOT_RUN | 0 | 0 | False |
| o2-all-pairs | NOT_RUN | 0 | 0 | False |

本轮新加速比、面积、时序均 NOT_TESTED。功能保护通过和宿主耗时不构成性能收益；默认仍为0f＋firstdot V2＋原C8。以下数值和关键路径保留原条件，未重跑EDA或性能对照。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

本轮实际目标进程 0，新增合格功能用例 0；没有新增性能合格项。完整历史数值、来源和未通过的时序条件见METRICS.json。

下一轮：开始 B3-R6：在独立目录仅修独立审计的路径校验适用范围，历史出处与宿主冻结文件按原路径、字节数和SHA校验，允许已有符号链接；记录解析目标作为审计信息，不新增别名白名单或额外准入条件。真实执行路径的canonical、boot/PID/start_ticks、完整结果和重放检查保持。冻结准备与正式校验采用一致逻辑；未运行的终态审计只在授予功能PASS时要求GUARD_PASS，FAIL收据仍可如实审计。保留R1至R5全部FAIL和旧锁，复用身份匹配且未变的27项checker、10项外部监督及旧身份/溯源证据，不重复无关测试。集中完成剩余独立审查、执行冻结和一次外部900秒监督预算测量；原两份24,558,348字节成本夹具不缩样。全部通过且两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色，每例300＋4×1500秒、目标6300/外层7200/宿主900秒，整批最多10目标、目标12600/外层14400秒；负控100000guest、正常800000/300000guest，CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式门或目标任一失败即停，不重试、不加时、不借时、不跳过继续、不扩围；三个暂缓项保持HOLD。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板、三项指标和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r5-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r5-20261106/NEXT_STEP.md)。


## 79. 2026-11-06 SP1-E B3-R6：HOLD

开始：2026-11-06T11:14:20.923904+08:00；结束：2026-11-06T11:33:14.118243+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R6-20261106-01。

B3-R6已修正历史出处检查：准备与正式验证使用同一原路径/字节数/SHA逻辑，304项冻结内容及4份历史别名通过；运行器和checker保持R5原字节，27＋10项证据明确复用、未重跑。独立审查唯一正式尝试在首个CSR正控API调用时报explicit scope/run id：审查脚本误传HOST_FIXTURE_NOT_TARGET，生产既有合法值为HOST_FIXTURE。首个正控调用1次、完成0/41；这是Agent编写的审查脚本参数错误，不是RTL、CSR结果或预算超限。按失败即停，预算0次、EMU目标0，保留原FAIL，整体HOLD，SP1-E仍15/20。

本轮checker新测0 / REUSED 27项：PASS_STRICT_NEGATIVE_CHECKER_HOST；runtime新测0 / REUSED 10项：PASS_RUNTIME_HOST_TESTS；原R3 6项及R4 4项仅保留更早历史出处。独立实际 0 / 计划41，历史 65项仅复用出处、未重跑：HOLD_B3_R6_INDEPENDENT_CONTROL_SCOPE_ERROR；预算：HOLD_B3_HOST_BUDGET。

- legacy-control：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_CSR_CONTROL_CALLER_SCOPE_BEFORE_BUDGET；error=ValueError: explicit scope/run id
- o2-all-pairs：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_CSR_CONTROL_CALLER_SCOPE_BEFORE_BUDGET；error=ValueError: explicit scope/run id

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | NOT_RUN | 0 | 0 | False |
| o2-all-pairs | NOT_RUN | 0 | 0 | False |

本轮新加速比、面积、时序均 NOT_TESTED。功能保护通过和宿主耗时不构成性能收益；默认仍为0f＋firstdot V2＋原C8。以下数值和关键路径保留原条件，未重跑EDA或性能对照。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

本轮实际目标进程 0，新增合格功能用例 0；没有新增性能合格项。完整历史数值、来源和未通过的时序条件见METRICS.json。

下一轮：开始 B3-R7：在独立目录仅将CSR独立审查共享调用点的scope改为生产已有合法值HOST_FIXTURE；沿用非空host run_id和既有全部41项覆盖，不新增条件、不为测试放宽生产API。复用R5已通过且字节未变的27项checker、10项外部监督及现有身份/溯源证据，复用R6历史路径检查修复。先逐项静态核对本次改动调用的签名、合法scope和返回字段，再冻结并完成剩余独立审查及一次原夹具900秒外部监督预算测量；保留R1至R6全部FAIL和旧锁，不缩样、不重复无关测试。两例均GO后，同轮仅按legacy-control→o2-all-pairs串行执行五角色，每例300＋4×1500秒，目标6300/外层7200/宿主900秒；整批最多10目标，目标12600/外层14400秒，不借时，负控100000guest、正常800000/300000guest，CPU4/整组4线程/RSS12GiB/每例日志2GiB及原seed/RAM/reset不变。正式审查、预算或目标任一失败即停，不重试、不加时、不跳过继续、不扩围；三个暂缓项继续HOLD。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板、三项指标和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r6-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r6-20261106/NEXT_STEP.md)。


## 80. 2026-11-06 SP1-E B3-R7：PASS_FUNCTIONAL

开始：2026-11-06T11:38:31.560496+08:00；结束：2026-11-06T13:17:09.632907+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R7-20261106-01。

B3-R7仅把独立CSR审查共享调用的scope修正为生产API已有HOST_FIXTURE，生产runtime/checker原字节保持，27＋10项通过证据明确复用、未重跑。剩余41项独立控一次PASS；唯一外部900秒预算测量18.948秒通过，两例宿主预算664.466/527.922秒均GO。随后按原合同串行完成legacy-control→o2-all-pairs两例各五角色，共10个真实目标全部通过；完整128位、退休/CSR、身份、资源及精确重放均通过独立终态复核，新增两项功能资格，SP1-E由15/20推进到17/20。整批目标累计4708.455秒、原生外层4783.570秒、外部监督4783.682秒，未重试、未加时、未扩围；原R1至R6失败完整保留。默认0f＋firstdot V2＋原C8保持，未修改RTL、未构建新核、未做EDA、未上传GitHub。

本轮checker新测0 / REUSED 27项：PASS_STRICT_NEGATIVE_CHECKER_HOST；runtime新测0 / REUSED 10项：PASS_RUNTIME_HOST_TESTS；原R3 6项及R4 4项仅保留更早历史出处。独立实际 41 / 计划41，历史 65项仅复用出处、未重跑：PASS_B3_EXECUTION_HOST_REVIEW；预算：GO_B3_HOST_BUDGET。

- legacy-control：GO；host_budget_seconds=664.4656078536575；预算通过，无失败
- o2-all-pairs：GO；host_budget_seconds=527.9218119536602；预算通过，无失败

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | FUNCTIONAL_PASS | 5 | 5 | True |
| o2-all-pairs | FUNCTIONAL_PASS | 5 | 5 | True |

本轮新加速比、面积、时序均 NOT_TESTED。功能保护通过和宿主耗时不构成性能收益；默认仍为0f＋firstdot V2＋原C8。以下数值和关键路径保留原条件，未重跑EDA或性能对照。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |

本轮实际目标进程 10，新增合格功能用例 2；没有新增性能合格项。完整历史数值、来源和未通过的时序条件见METRICS.json。

下一轮：开始 SP1-E B4：集中完成o2-control与原C8普通C48的共享运行器差异接入，并冻结专用bit100→候选完整正常调用→0f完整正常调用的有界校准合同；复用R7已验证的拒错组归属、退休/CSR、进程外监督、身份与重放公共机制，只补两个负载的实际差异，保留o2-control原完整覆盖以及C48的48调用/1008次custom和完整结果/CSR/ABI。逐项明确镜像与专用故障参考身份、guest/资源上限、每角色/每例/整批独立预算及失败即停；不得用R7其他负载吞吐直接充当保守上界，不借用已完成批次预算。同步核对timed DIV/SQRT已有软件与计时合同，只补真实缺项，分别列出公平窗口、运行器接入和预算缺口，不把allpairs功能通过当作计时资格。已有合法证据直接复用，不重复泛化评审，不重跑R7已通过用例。完成后交付可审阅的准确进程清单、完整调用校准运行合同及下一批执行指令；校准的新预算需明确获用户授权后执行。此轮先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r7-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b3-r7-20261106/NEXT_STEP.md)。


## 81. 2026-11-06 SP1-E B4：两例宿主GO，正式验收17/20

开始：2026-11-06T13:30:52.886182+08:00；结束：2026-11-06T14:17:51.698000+08:00。操作人：@cc77-builder / Agent（沿用用户此前确认账号，本轮未声称新登录核验）；操作ID：SP1-E-B4-HOST-20261106-01。执行方式：并行独立宿主叶接入，串行有限宿主测量和根端收口；不是成员人工验收。

B4完成o2-control与原C8普通C48最小差异接入、共享三角色校准运行器及完整输入冻结。两例各27项差异覆盖通过，另补o2精确前缀15项、C48精确PC6项、共享10项及JSON写读修订5项。原夹具标签、模块冲突和首次JSON冻结FAIL保留，受影响部分在本轮独立修订并验证。最终宿主经验预算235.713/213.416秒，均低于900秒；支持请求下一轮最多6进程完整调用校准，不保证目标在2400秒内结束。timed DIV/SQRT复用137份原文件身份及旧测试，实际运行接入与完整预算仍HOLD。本轮目标0，SP1-E仍17/20，默认0f＋firstdot V2＋原C8，未改RTL/新核/EDA/上传。

| 项目 | 最终宿主结果 | 保留范围 |
| --- | --- | --- |
| o2-control | GO；27项基础差异覆盖＋15项精确前缀 | 16组/256trial/1208custom/全寄存器结果；历史FULL_STALL=0不篡改 |
| 原C8普通C48 | GO；27项基础差异覆盖＋6项精确PC | 48调用/1008custom/384完整128位结果/CSR/ABI/尾部 |
| 共享与冻结 | 10项联合控PASS；最小写读修订5项PASS | 旧10项按未变语义复用；旧tuple/list FAIL和首份freeze保留 |
| 900秒宿主预算 | o2-control235.713秒；C48 213.416秒 | 当前CPU4经验包络＋硬限额；不是目标运行完成上界 |
| timed DIV/SQRT | HOLD；137份旧文件身份核对PASS | 复用已有软件/41宿主测试，缺共享运行接入和完整目标预算 |

最终入口`runtime-r1/calibration_guard.py`，源码版本`b8726ede70ef14e45071ecd5051041d25b800b3eab95bda011f8b349f83fc797`；两份`cases-r1`各338项输入冻结已实际写读通过且未消费。`ADMISSION.json`仅为宿主GO，没有目标授权。校准拟两例各3角色，共最多6目标、每例300＋2400＋2400秒/目标5100/宿主900/外层6000秒；整批目标10200/外层12000秒。新预算待下一条执行指令授权，旧正式5角色6300/7200秒及正常1500秒不变。

**进度17/20→17/20。** 本轮目标0；下一轮完整调用校准也不冒充正式验收。两例以后正式验收通过可19/20，timed保护再通过才20/20。没有新加速比/面积/时序测量，三项均NOT_TESTED；下面数值仅原条件历史复用，不重复测量或扩大资格。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


源码445项和历史证据1599项保持原字节。默认仍0f＋firstdot V2＋原C8；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完整版本/镜像/参考/文件清单及证据SHA见RESULT.json、两份EXECUTION_FREEZE和METRICS.json。

下一轮：开始 SP1-E B4 两例完整调用有界校准：按 NEXT_STEP 使用最终 runtime-r1/calibration_guard.py，先核查已有进程、宿主准入、两份 cases-r1 冻结输入及未消费锁。接受本轮新校准预算后，仅按 o2-control→original-c8-c48 串行，每例 bit100 拒错300秒/10万guest→候选完整2400秒/150万guest→0f完整2400秒/150万guest；每例最多3目标、目标累计5100秒、宿主900秒、外层6000秒，整批最多6目标、目标10200秒、外层12000秒，不借时。保持CPU4、整组4线程、RSS12GiB、每例日志2GiB和原seed/RAM/reset，保留o2-control的16组/256trial/1208custom及C48全部48调用/1008custom/384完整128位输出、CSR/ABI、当前提交组bit100与物理运行身份。失败或超限立即停止整批，不重试、不加时、不跳过继续。只收集完整调用正确性、周期、吞吐、进度和资源，重新判断原五角色6300/7200秒预算，不自动进入正式验收或timed DIV/SQRT。校准不增加17/20资格。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板及三项指标状态，给出结论和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/RESULT.md) · [精确校准合同](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/CALIBRATION_CONTRACT.md) · [下一轮指令](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/NEXT_STEP.md)。


## 82. 2026-11-06 SP1-E B4完整调用校准：STOPPED，17/20

开始：2026-11-06T14:27:32.639267+08:00；结束：2026-11-06T14:41:18.377067+08:00。操作人：@cc77-builder / Agent（本轮GitHub连接器身份已核实）；操作ID：SP1-E-B4-CALIBRATION-20261106-01。实际模式：唯一有界guard串行目标，辅助Agent只读独立核查；不是成员人工验收。

B4按最终runtime-r1和新授权实际启动唯一首例o2-control bit100进程，9243 guest/19.937916秒后冻结检查器报instruction ring slots/destination；整批STOPPED，guardian CHILD_EXIT_1且清理完成，后5目标未启动，未重试。确切触发是非当前提交组历史slot06的dst32被整环dst<32检查拒绝，当前组为slots10–13；数值部分观察一致但不翻转FAIL。实际身份/349份资源采样/原始日志/清理独立通过。完整正常调用0，原正式预算仍HOLD，验收17/20不变，三项新指标NOT_TESTED，稳定默认不变。

| 负载 | bit100 | 候选完整 | 0f完整 |
| --- | --- | --- | --- |
| o2-control | 已运行；检查器FAIL、未获拒错资格 | NOT_RUN | NOT_RUN |
| 原C8普通C48 | NOT_RUN | NOT_RUN | NOT_RUN |

确切失败在历史slot06/PC0x800002e8的raw dst32：整个32槽指令环被提前要求dst<32，真实当前组却仅slots10–13（head0x2f8/cmtcnt4/tail13）。输出端raw dest为uint8；不得无依据将32改写为编码vd28。宿主合成夹具未复现该真实历史字段。独立算术/bit100部分一致不替代冻结检查器完整资格，原FAIL不翻转。

| 实际墙钟与资源 | 结果 |
| --- | ---: |
| 目标数 / 后续未运行数 | 1 / 5 |
| guest cycles | 9243 |
| 目标活跃 / role总秒数 | 19.937915666 / 19.951715726 |
| case总 / case宿主秒数 | 21.906911395 / 1.968995729 |
| batch总 / guardian总秒数 | 23.950217391 / 24.037230848 |
| 峰值线程 / RSS | 1 / 71.875MiB |
| 采样 / 完整日志字节 | 349 / 40468 |

实际目标身份、CPU4、进程出生、参考映射、资源及清理通过独立核查；guardian保留GUARD_FAIL/CHILD_EXIT_1，cleanup_ok=true。不是超时或资源耗尽。原host GO只覆盖宿主准备，不覆盖本次真实拒错失败。旧授权及batch/首例锁已消费，未重试、未清锁、未跳过继续，源/镜像/预算不改。

**正式验收17/20→17/20。** 完整正常调用0，没有当前两核完整耗时新依据，原1500秒/正常角色及6300/7200秒正式合同继续HOLD。不能外推9243guest短启动吞吐，也没有同核精确重放资格。

本轮三项主要指标：加速比NOT_TESTED；面积NOT_TESTED；时序NOT_TESTED。下面仅保留原条件历史复用，不将bit100目标墙钟当公平性能结果。

| 历史工作负载 | 0f VDOT cycles | SP1 VDOT cycles | 0f/SP1 RVV cycles | 0f RVV/VDOT | SP1 RVV/VDOT | VDOT周期下降 |
|---|---:|---:|---:|---:|---:|---:|
| B2 stream performance-d0-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d1-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |
| B2 stream performance-d2-s03 | 1127.50 | 1126.25 | 1133/1133 | 1.004878049× | 1.005993341× | 0.110864745% |

| 历史局部成本 | 0f | SP1 |
|---|---:|---:|
| FU 面积 μm² | 17298.246 | 18322.878 |
| 含 FU 的真实父级面积 μm² | 284614.946 | 285241.642 |
| nominal FU setup slack ns | −0.268520 | −0.790381 |
| nominal 父级 setup slack ns | −2.393998 | −2.337809 |

Nangate45 Typical 1.1V 25℃，原 G2 trace-off 局部 FU/真实父级综合；不是整核面积、签核或 Fmax。负 slack 和原严格 G2 NO-GO 均保留。新 trace-on 成本仍 NOT_TESTED。

| SP1历史五档 | 周期ns | 负载fF | FU Q/ns | FU slack/ns | 父级Q/ns | 父级slack/ns |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 1 | 5 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| period050 | 0.5 | 5 | 1.790381 | -1.290381 | 3.337809 | -2.837809 |
| period200 | 2 | 5 | 1.790381 | 0.209619 | 3.337809 | -1.337809 |
| load001 | 1 | 1 | 1.790381 | -0.790381 | 3.337809 | -2.337809 |
| load020 | 1 | 20 | 1.790381 | -0.790381 | 3.391613 | -2.391613 |

| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |



默认仍0f＋firstdot V2＋原C8，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完整实际版本、命令、角色、镜像/参考SHA、boot/PID和证据见本轮RESULT.json与原生记录；未采用候选未合入默认。

下一轮建议：开始 SP1-E B4-R2 宿主修订与两例完整调用校准：保留本轮真实FAIL、原始日志、授权和消费锁，在独立修订目录仅修正历史指令环raw dst解析与当前提交组架构目的地检查的作用范围，按冻结输出端uint8字段定义处理历史槽，不把32改写成28，不放宽当前组/ELF/最后写入者/完整128位/CSR/bit100判据。使用本轮真实日志做离线正控，补齐历史dst32、当前组非法目的地、槽序/尾指针/组计数及数值身份负控，复用未变通过证据；完成最小差异审查、实际输入冻结写读及宿主预算影响核对。全部GO后，在新源码/合同/授权和独立输出下同轮执行o2-control→原C8普通C48，每例bit100300秒/10万guest、候选完整2400秒/150万guest、0f完整2400秒/150万guest；每例目标5100/宿主900/外层6000秒，整批最多6目标、目标10200/外层12000秒。CPU4、整组4线程、RSS12GiB、每例日志2GiB、原完整覆盖与seed/RAM/reset保持。新批次任一失败即停，不重试、不加时、不借旧剩余预算、不跳过继续、不自动进入正式验收；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板和三项指标状态，给出结论和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/execution-01/RESULT.md) · [确切失败归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/execution-01/independent-review/FAILURE_ATTRIBUTION.md) · [实际预算分析](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/execution-01/budget-review/RESULT.md) · [下一轮指令](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-calibration-host-20261106/execution-01/NEXT_STEP.md)。


## 83. SP1-E B4-R2 宿主修复与两例完整调用校准（停止留档）

记录ID SP1-E-B4-R2-20261106-STOPPED；操作ID SP1-E-B4-R2-20261106-01；@cc77-builder / Agent。
开始 2026-11-06T14:49:09.465823+08:00，结束 2026-11-06T15:38:51.986292+08:00；未提交，基点 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e。

B4-R2最小raw dst范围修复与宿主准入通过；新独立批次bit100拒错通过，候选o2-control完整程序GOOD_TRAP、256次试验零错误、1208次退休完整128位重算一致，但原覆盖门KILL_P/PARTIAL_KILL未触发，整批按合同STOPPED。仅启动2/6目标，其余4个NOT_RUN，清理正常、旧FAIL和锁保留。候选1562.610640秒超过原正式1500秒，低于本轮2400秒；不授完整校准或正式验收资格，进度仍17/20，默认保持0f＋firstdot V2＋原C8。

| 用例/角色 | 结果 | guest cycles | 活跃墙钟/s |
| --- | --- | ---: | ---: |
| o2-control bit100 | NEGATIVE_PASS | 9243 | 20.617259 |
| o2-control candidate-full | 程序完整结束、数值证据一致；覆盖FAIL | 702861 | 1562.610640 |
| o2-control baseline-full | NOT_RUN | — | — |
| 原C8普通C48 bit100 | NOT_RUN | — | — |
| 原C8普通C48 candidate-full | NOT_RUN | — | — |
| 原C8普通C48 baseline-full | NOT_RUN | — | — |


只修历史32槽指令环raw dst范围（uint8 0..255），选出的当前提交组仍要求架构目的地<32；槽顺序、尾指针、当前组、ELF/ROB、完整128位、CSR及bit100判据保持。没有把历史dst32改写为vd28。真实旧日志与26项差异验证一次PASS；运行器4项差异验证一次PASS，复用原10+5项未变证据。两例各339项执行冻结通过，独立宿主审查通过，900秒宿主预算经验估计分别235.921543秒和213.416454秒。新合同、授权、消费锁及独立输出生效，旧FAIL和锁保留。

每例最多3目标：bit100 300秒/10万guest，候选及0f各2400秒/150万guest；每例目标5100/宿主900/外层6000秒，整批最多6目标/10200秒目标/12000秒外层，CPU4/整组4线程/RSS12GiB/每例日志2GiB。实际只启动2个，目标累计1583.227898秒，case宿主8.742916秒，case总1591.970814秒，batch总1593.974286秒，guardian总1594.082341秒。candidate-full峰值1线程、74.625MiB，29005份采样；没有资源或墙钟限制触发。guardian以GUARD_FAIL/CHILD_EXIT_1收口，清理正常，无遗留本批目标。后4个角色未启动，没有重试、加时或跳过失败继续。

候选stdout记录16组、256次试验、131072字节寄存器检查、failures=0及GOOD_TRAP，进程exit0。离线使用冻结观察器验证状态关系，并从真实输入独立重算1208次退休的完整128位结果，全部一致，高96位同时检查。CSR证据是冻结目标的结束自检、DiffTest及程序摘要，不能写成逐trial打印了CSR快照。

原collector还要求KILL_P、KILL_R、PARTIAL_KILL发生。真实轨迹5283个STATE中pValid=1为0、outready=0为0，最大占用1；1618次ACCEPT均DIRECT_R，ENQUEUE_P/MOVE为0，KILL_R=26、KILL_P=0、PARTIAL_KILL=0。这是实际覆盖缺口，不是简单事件名漏翻译。数值证据不能越过原覆盖门；没有生成正常角色完整validation，不能将完整校准写成PASS。本轮没有据此认定RTL算错，也未宣称P槽取消在所有情况下不可达。冻结源码支持在持续ready前提下P为空；真实父级写回priority1仍有仲裁依赖，其他写回竞争负载可能占用P，须单独评估。

candidate-full活跃1562.610640秒，超过原正式1500秒62.610640秒（4.174%），低于本轮独立校准2400秒。原1500/6300/7200正式合同仍HOLD；不能自动沿用2400作为正式新限额。0f O2与C48正常调用时长仍未测，不能用短bit100或本次候选吞吐外推。没有同核精确重放，没有公平计时加速比；17/20不增加。


本轮新增加速比、面积、时序均为NOT_TESTED：完整功能校准没有公平RVV计时窗，也未做EDA。下面仅为历史同口径复用，不是本轮新跑分。


以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |



路线影响：17/20不变；原正式预算HOLD。默认0f＋firstdot V2＋原C8不变，未改RTL/构建新核/EDA/上传GitHub。

下一轮指令：开始 B4-R3 取消覆盖合同与剩余校准方案收口：保留 B4/R2 原FAIL、原始日志和消费锁，复用本轮bit100、1208次完整128位结果、程序完整结束及资源证据。先针对SP1直接入R、P槽未占用的真实路径，核对已有FU/真实父级反压和两槽取消证据能否组成完整分层覆盖；不能替代的全核覆盖，给出能实际触发的最小补测设计，不直接删掉KILL_P/PARTIAL_KILL要求。同步依据1562.61秒实测修订正式预算提案，明确0f O2和原C8普通C48尚缺的校准角色、证据复用边界、下一批进程和独立预算。只做必要宿主差异验证与合同准备，不重跑已完成目标、不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后给出GO/HOLD及可整批执行的下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r2-20261106/RESULT.md) · [覆盖归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r2-20261106/terminal-review/FAILURE_ATTRIBUTION.md) · [预算报告](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r2-20261106/calibration-budget/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r2-20261106/NEXT_STEP.md)。


## 84. SP1-E B4-R3 取消覆盖、最小补测与剩余校准宿主准备

记录ID SP1-E-B4-R3-20261106-HOST-REVIEW；@cc77-builder / Agent；操作ID SP1-E-B4-R3-20261106-01。
时间 2026-11-06T15:48:40.206821+08:00～2026-11-06T16:08:55.862482+08:00。未提交，基点 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e。

B4-R3宿主准备完成：同源码组件证据和R2真实数值/拒错证据可复用；原全核P槽及部分取消覆盖仍HOLD。已形成FEX0/F2v写回竞争的最小补测设计，实际命中NOT_TESTED。剩余四角色新独立校准预算设计GO（7500秒目标/9300秒外层），但数值专用adapter和显式角色运行器尚未接入，执行准入HOLD。未运行任何EMU/NEMU或新测试，未改RTL/构建/EDA，17/20及默认0f＋firstdot V2＋原C8保持。

六个局部运行与全核冻结的398份生产源码匹配；真实父级KILL_P54/KILL_R88/PARTIAL_KILL49等仅按组件范围复用。原全核0/26/0不变；R2的11项真实输入已冻结为numeric-only摘要，完整case资格false。F2v优先级0与VFEX4优先级1共用口3是必要补测方向；无新ELF和命中证据，不原样重跑旧程序。

剩余角色：O2 0f正常2400秒；C48 bit100300秒、候选正常2400秒、0f正常2400秒；每例宿主900秒，O2外层3300、C48外层6000，整批4目标/7500target/9300outer。预算草案GO、实际接入HOLD；只补显式角色和numeric-only API，复用公共监督。原正式1500/6300/7200和全核取消覆盖继续HOLD。

本轮新增加速比、面积、时序均为NOT_TESTED：只做宿主评审，没有运行目标或EDA。下面仅为历史同口径复用，不是本轮新跑分。


以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](METRICS.json)。


本轮没有新目标、RTL/宿主差异测试、源码修改、构建、EDA、默认切换或GitHub写入；只读审查和文档/JSON为本轮新增。正式进度17/20保持。

路线影响／接续：开始 B4-R4，按NEXT_STEP实现校准专用数值摘要和剩余四角色运行器，复用未变公共机制，只补角色/参考库/退出码/历史身份/冻结差异正负控及宿主预算准入。保留R2原FAIL和旧锁，不重跑已完成的o2-control bit100与候选正常。全部准入后，以新冻结身份和独立授权，仅串行运行0f O2正常→C48 bit100→C48候选正常→C48 0f正常；接受新独立预算：最多4目标、目标累计7500秒、整批外层9300秒，O2目标2400/宿主900/外层3300秒，C48目标5100/宿主900/外层6000秒；各角色和资源按本轮草案。失败即停、不重试、不加时、不借旧余量、不自动进入正式验收。新取消覆盖补测镜像不在该批执行，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板和三项指标，给出下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r3-20261106/RESULT.md) · [覆盖矩阵](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r3-20261106/coverage-review/RESULT.md) · [补测设计](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r3-20261106/stimulus-review/DESIGN.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r3-20261106/NEXT_STEP.md)。


## 85. B4-R4四角色完整调用：4个角色通过，C48比较失败即停（2026-11-06）

- @cc77-builder / Agent；操作ID `SP1-E-B4-R4-20261106-01`；起止 2026-11-06T08:35:58.275394+00:00 ～ 2026-11-06T10:41:21.789429+00:00；本地收口 2026-11-06T18:41:21.789429+08:00。含自动等待，不作人工工时。
- HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，分支 `local/zjhwork-integration-20261024`；默认不变，正式17/20。
- B4-R4宿主15＋8项、独立审查和预算门通过；剩余四个真实角色各自通过，O2数值配对完成。C48最终跨硬件accepted_sources_sha256比较失败，整批STOPPED且清理正常。只读逐条归因确认1008条有效低64输入、非数据字段、完整128结果及48调用UART均相同，96条仅未消费高64不同；原FAIL保留，最小宿主口径修订设计GO，当前C48整case/正式验收HOLD。未改RTL/新核/EDA/默认或上传，进度17/20。
- 宿主15/15＋8/8、独立复核及成本门GO；四目标仅执行一次，R2历史目标复用不重跑。

|角色|guest cycles|active秒|监督秒|单角色结果|
|---|---:|---:|---:|---|
|o2-control / baseline-full|703,135|1588.517917|1588.535824|FULL_CALL_PASS|
|original-c8-c48 / bit100|13,738|29.398773|29.407729|NEGATIVE_PASS|
|original-c8-c48 / candidate-full|871,768|1854.085414|1854.100318|FULL_CALL_PASS|
|original-c8-c48 / baseline-full|871,326|1956.443881|1956.458273|FULL_CALL_PASS|

整批active5428.445985/7500秒、外层5457.889599/9300秒；资源及清理正常。C48最后accepted_sources_sha256比较失败，保留原STOPPED；1008有效低64/完整128结果/其余来源字段/48UART相同，96条差异只在未消费高64。三条新正常角色均超旧正式1500秒，该旧门继续HOLD。O2基线覆盖不替代SP1候选P/partial。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r4-20261106/RESULT.md) · [失败归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r4-20261106/terminal-review/FAILURE_ATTRIBUTION.md) · [实际预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r4-20261106/actual-budget-review/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r4-20261106/NEXT_STEP.md)。

### 三项指标：本轮NOT_TESTED，以下历史复用

加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r4-20261106/METRICS.json)。


### 路线影响／接续

开始 B4-R5 最小比较合同修订与离线复核：保留 B4-R4 原FAIL、原始日志、授权和消费锁，在独立目录为 C48 增加按退休链绑定的有效低64位输入摘要，仅用于跨硬件比较；完整128位结果、PC/编码/配置/控制字段及同硬件raw128精确重放要求保持。复用四个已完成角色和未变宿主机制，使用两份真实完整日志补齐高64差异正控、低64/结果/身份及同硬件高64漂移负控，做独立复核。通过后同轮准备复用既有三角色＋两次新重放的明确合同和实测预算提案，不自动授正式资格。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板，给出GO/HOLD和下一批指令。

445份production、160份旧历史文件未变；原FAIL/锁保留，无RTL/新核/EDA/默认/GitHub写入。


## 86. B4-R5：C48有效输入摘要修订与离线复核（2026-11-06）

- 操作ID：`SP1-E-B4-R5-20261106-01`；执行者`@cc77-builder / Agent`（Agent）。
- 起止：`2026-11-06T12:44:51.758924+00:00` → `2026-11-06T13:17:38.530350+00:00`（UTC+00:00）；包含中断等待，不计人工工时。
- HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；分支 `local/zjhwork-integration-20261024`；默认 **0f＋firstdot V2＋原C8**。
- **宿主修订与两重放设计GO；实际执行/真实重放/正式验收HOLD。** 宿主27PASS，独立2016条完整128位等式＋3负控PASS。首轮独立包装失败在解析日志前发生并保留；R1修包装，核查主体未改。
- 跨硬件仅投影vs1/vs2低64，其余字段、完整128位结果、同核raw128/observer/guest精确重放保持；96条未消费高64差异得到解释，低64或结果高位漂移仍拒绝。
- 新目标0；不改判R4失败，不重跑四目标。445生产文件及322历史文件匹配；无RTL/新核/EDA/默认/GitHub写入。正式 **17/20**。
- 提案：复用三历史C48角色，未来仅两次重放；各2400秒/150万guest，target4800、host900、outer5700秒。实际runner/执行闭包/最终成本待完成；下一轮可一次授权准入后同轮两角色，当前不得自动执行。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r5-20261106/RESULT.md) · [下一步](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r5-20261106/NEXT_STEP.md)。

### 三项指标留档

本轮仅修订宿主比较并离线复核既有日志，0个目标、0次EDA；新增加速比、面积、时序均为 **NOT_TESTED**。以下18条性能、面积及五档STA按原合同历史复用，数值未变。

默认为 **0f＋firstdot V2＋原C8**，SP1候选未切默认；正式验收 **17/20**。宿主通过不构成真实重放或C48正式资格。原G2严格成本门NO-GO保留。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r5-20261106/METRICS.json)。

### 接续

开始 B4-R6，按 NEXT_STEP 完成 C48 两次重放运行器、三份历史角色绑定、完整执行冻结及必要宿主差异、独立审查和预算准入；复用未变证据，不重做旧宿主全套。全部通过后接受新独立预算，同轮串行执行 candidate-replay→baseline-replay，最多2个新目标，每角色2400秒/150万guest、目标累计4800秒、宿主900秒、整批外层5700秒。保持CPU4、整组最多4线程、RSS12GiB、日志2GiB、完整48调用/1008custom/128位结果、同硬件raw128/observer/guest精确重放及跨硬件active64。保留旧FAIL和锁，失败即停、不重试、不加时、不扩围，不重跑既有三角色、不自动进入其他用例。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板并给出结论和下一轮指令。


## 87. B4-R6：两次重放运行器接入，宿主导入FAIL停止（2026-11-06）

- 操作ID`SP1-E-B4-R6-20261106-01`；@cc77-builder / Agent；起止`2026-11-06T13:37:05.817023+00:00` → `2026-11-06T14:16:37.393124+00:00`（UTC+00:00，含环境等待，不作人工工时）。
- HEAD`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`；分支`local/zjhwork-integration-20261024`；默认 **0f＋firstdot V2＋原C8**。
- **STOPPED/HOLD**：唯一正式host在test_delta导入时选中旧G0 fixtures.py，缺authorization_fixture。cost脚本同样裸导入风险已定位但未执行。AST/静态审查漏掉完整冷导入集成，原PASS与新FAIL都保留。
- 运行器实现与351项执行冻结完成；宿主57源码/363输入冻结；规划9方法、实际执行0，成本0、目标0。外部监督exit1、1.395338548秒、cleanup=true、无剩余存活子进程。未创建目标授权，不重试。
- 独立57/363/351及445生产/406旧文件全部MATCH。host final_inputs_unchanged=false是失败分支未到postcheck，实际源未漂移。默认与正式 **17/20** 不变；无RTL、新核、EDA、GitHub写入。
- 准备期仅恢复Ubuntu命令入口一次，未改配置，当时无正式测试或目标；独立留档。两重放2400各/150万guest、target4800/host900/outer5700预算未使用，实际host成本尚未测。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r6-20261106/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r6-20261106/NEXT_STEP.md)。

### 三项指标留档

本轮在正式宿主入口导入测试模块时停止：9项方法实际执行0、成本测量0、目标0。新增加速比、面积、时序均为 **NOT_TESTED**。以下18条性能、FU/父级面积及五档STA按原合同历史复用，原数值未变。

默认 **0f＋firstdot V2＋原C8**，正式进度 **17/20**。没有新的硬件失败或性能结论。原G2严格成本门NO-GO、R4 FAIL及本轮宿主FAIL各自保留。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r6-20261106/METRICS.json)。

### 接续

开始 B4-R7，按 NEXT_STEP 保留 B4-R6 原FAIL与消费锁，在新独立身份和目录中仅修复宿主测试、成本脚本的 fixtures 同名导入，使用绝对路径和唯一模块名并核对来源。按真实加载顺序补冷进程完整导入正控及必要错路径负控，复用未变运行器和历史证据；完成原差异门、执行冻结、独立审查和预算准入后，同轮串行 candidate-replay→baseline-replay。接受最多2目标、各2400秒/150万guest、目标累计4800秒、宿主900秒、外层5700秒及原资源/完整覆盖/精确重放要求。失败即停、不重试、不加时、不扩围，不重跑三历史角色、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板和下一轮指令。


## 88. B4-R7：冷导入修复与C48两次重放通过，18/20（2026-11-07）

- 操作ID `SP1-E-B4-R7-20261106-01`，@cc77-builder / Agent；启动 `2026-11-06T14:59:26.299918+00:00`，收口 `2026-11-06T16:23:03.240762+00:00`。目录按启动日20261106保留，完成日北京时间2026-11-07。
- **新合同C48功能验收PASS：17/20 → 18/20**。默认仍为 **0f＋firstdot V2＋原C8**，第19项O2候选P槽/部分取消、第20项timed DIV/SQRT仍待补齐。
- 修复两处裸fixtures导入，绝对路径＋唯一模块名＋冻结来源检查；实际冷导入/2负控、原9方法、成本及独立审查PASS。原R6 FAIL/锁保留；六个运行器Python源字节不变。
- 唯一正式host外部13.310258522秒/exit0/cleanup；经验成本准入194.206609216秒。只运行两个新目标，三份历史C48角色复用；每核完整48调用/12C8/1008custom/完整128结果，原CSR/ABI合同保持。

|角色|guest cycles|target active/s|结果|
|---|---:|---:|---|
|candidate-replay|871768|1965.817567241|完整功能＋同核精确重放PASS|
|baseline-replay|871326|1649.103523405|完整功能＋同核精确重放PASS|

两核active64/full128/UART比较PASS；同核raw128/observer/guest均精确相等。target累计3614.921090646/4800秒，batch host14.592558516/900秒，guardian3629.562323962/5700秒；峰值1线程、CPU4、RSS/log均合规，清理完成。独立71项及65453条资源样本通过；57/363/351冻结、445生产和479旧文件MATCH。原1500秒模板与旧formal标记不变，本记录只授新合同C48功能资格。

无RTL/新核/EDA/默认切换/GitHub写入。新三指标均NOT_TESTED，以下保留历史实测，不能用本轮总guest或宿主耗时计算新加速比。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r7-20261106/RESULT.md) · [独立终态审计](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r7-20261106/terminal-review/AUDIT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r7-20261106/NEXT_STEP.md)。

### 三项指标（历史复用）

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-b4-r7-20261106/METRICS.json)。

### 下一轮指令

开始 SP1-E O2（第19项）最小软件补测准备，按 NEXT_STEP 复用现有 bit100、两核完整数值和 R4 配对证据，在独立目录实现 R3 设计的最小 F2v 写回竞争软件，补候选 P 槽及部分取消覆盖的触发方案，完成 GNU 构建、对象审计、完整128位和CSR/ABI宿主正负控，冻结有限相位与新校准/重放合同及预算。复用未变机制，不新增反方向硬门；先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后给出GO/HOLD及下一批执行指令。


## 第89条：SP1-E O2（第19项）最小软件补测准备 · 2026-11-07

**GO：软件与宿主准备；HOLD：目标执行与第19项正式验收。** 当前18/20，默认0f＋firstdot V2＋原C8。选定attempt-02，41调用/77退休/17静态PC；GNU和对象审计、8方法选择器、4方法镜像集成、538项C判定、bit100只编译与独立审查通过。image-check-01宿主FAIL和旧FAIL/锁完整保留。

本轮EMU/NEMU、RTL、新核、EDA、默认切换、GitHub写入均0。新加速比/面积/时序NOT_TESTED；下表历史三指标原样复用。445生产文件与596旧文件无漂移。下一轮先接入运行器和严格新guard拒错，完成执行冻结与宿主预算准入；新提案两角色300秒/10万guest→900秒/30万guest，target1200/host900/outer2100秒。有限校准不保证命中或完成，未命中即停，不自动重放。原O2两次精确重放与补测资格仍待，第20项独立待验。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-host-20261107/RESULT.md) · [冻结合同](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-host-20261107/CALIBRATION_REPLAY_CONTRACT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-host-20261107/NEXT_STEP.md)。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-host-20261107/METRICS.json)。

### 下一轮指令

开始 SP1-E O2（第19项）补测运行器接入与有界校准，按 NEXT_STEP 复用本轮 attempt-02 镜像和已通过宿主证据，完成新 guard 的严格拒错检查、运行器差异接入、完整执行冻结、独立复核及900秒宿主预算准入。全部通过后，接受新独立预算，同轮串行执行 bit100拒错→候选正常校准，最多2个目标：分别300秒/10万guest、900秒/30万guest，目标累计1200秒、宿主900秒、外层2100秒，原CPU4、4线程、RSS12GiB、日志2GiB限制不变。保留41调用/77退休、完整128位、CSR/ABI及S0/S1真实观察链；失败或未命中即停，不重试、不加时、不扩相位、不自动进入重放或第20项。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板，给出结论和下一轮指令。


## 第90条：SP1-E O2补测接入与有界校准 · 2026-11-07

**HOLD：唯一宿主准入失败，未启动目标。** 8方法7通过1失败；第三方法含无效负控替换（默认dst32，却替换dst255），只读定位该确定缺陷并保留未记录子例索引的证据边界。外层0.954496469秒exit1，清理完成，LAUNCH/ADMISSION锁保留，无重试。118项执行冻结已完成；成本与运行时独立方法复核未执行。445生产文件、上一轮208文件和118冻结输入无漂移。

正式18/20，默认0f＋firstdot V2＋原C8。EMU/NEMU、RTL、新核、EDA、默认切换、GitHub写入均0。新加速比/面积/时序NOT_TESTED，历史三指标见下表。下一轮只修夹具与命名负控，复用其余7方法证据；新身份准入通过后执行原两角色300秒/10万guest→900秒/30万guest，target1200/host900/outer2100，同一外层包含准入和后处理，不借本轮余量。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-20261107/RESULT.md) · [终态](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-20261107/TERMINAL_AUDIT.json) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-20261107/NEXT_STEP.md)。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-20261107/METRICS.json)。

### 下一轮指令

开始 SP1-E O2 补测接入 R1，按 NEXT_STEP 最小修复负控夹具的无效替换：使用实际存在的历史环dst字段，并检查替换命中及字节确实变化，给各子例明确标签。保留本轮FAIL与锁，复用7项通过证据，只补受影响负控、冷导入、执行冻结、独立方法复核和宿主预算准入。全部通过后，以新独立身份同轮串行bit100拒错→候选正常，接受原300秒/10万guest、900秒/30万guest、目标累计1200秒、宿主900秒、外层2100秒及原资源/完整覆盖要求。失败或未命中即停，不重试、不加时、不扩围、不自动重放；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板和下一轮指令。


## 第91条：SP1-E O2补测接入R1 · 2026-11-07

执行者 @cc77-builder / Agent；操作ID `SP1-E-O2-CANCEL-CALIBRATION-R1-20261107-01`；工作起止 2026-11-07T11:45:52.663426+08:00 ～ 2026-11-07T11:55:00.635684+08:00（任务区间，不是人工工时）。HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。

**HOLD：宿主准入PASS，真实bit100日志解析FAIL后停止。** 负控精确命中/字节变化修复完成，13具名子例PASS、3方法PASS；7旧方法按AST/源码复用，冷导入与新测重叠1项，独立方法并集9项。10项独立方法静态/ELF复核PASS（同一Agent，不是队友签核），宿主成本估值345.931220秒小于900秒，143项冻结完成。

原两角色已同轮准入并执行到首角色：1个真实bit100目标25.976018秒/11668guest，外层35.826946秒，峰值1线程/RSS74711040字节/39824字节日志，资源通过、清理完成。预期guard注入与bit100差异确实出现，但检查器不识别历史UART访问的合法(S)标签，在严格日志验收处FAIL；当前group仅slot7 guard，异常格式在历史slot10/13。候选正常未运行；无S0/S1命中结论。原FAIL/锁保留、无重试。

正式18/20不变，默认0f＋firstdot V2＋原C8。143冻结、445生产、前两轮208＋50文件无漂移；RTL/新核/EDA/默认切换/GitHub写入均0。新三指标NOT_TESTED，下表原样复用历史18行性能及局部面积/五档STA。下一轮在新身份补合法历史tag语法并用本轮完整真实日志核全链，必要宿主准入后同轮执行原两角色；不拆成无关准备回合、不降低完整覆盖。第19项仍需命中与约定重放。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r1-20261107/RESULT.md) · [终态](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r1-20261107/TERMINAL_AUDIT.json) · [解析归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r1-20261107/review/FAILURE_DIAGNOSIS.json) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r1-20261107/NEXT_STEP.md)。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r1-20261107/METRICS.json)。

### 路线影响／接续指令

开始 SP1-E O2 补测接入 R2，按 NEXT_STEP 最小补齐合法历史环 S/D/W 标签解析，明确当前拒错提交组不能用 skip/delayed 指令作证；用 R1 完整真实日志一次性核查整个拒错检查链，补针对性正负控，保留原FAIL与锁，复用未变宿主证据。全部宿主、冻结、独立方法复核和预算门通过后，以新身份同轮串行原 bit100拒错→候选正常两角色，保持300秒/10万guest、900秒/30万guest、目标1200秒、宿主900秒、外层2100秒及原资源和41调用/77退休、S0/S1完整覆盖。失败或未命中即停，不重试、不加时、不扩围、不自动重放；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板并给出下一批指令。


## 第92条：SP1-E O2补测接入R2 · 2026-11-07

执行者 @cc77-builder / Agent；操作ID `SP1-E-O2-CANCEL-CALIBRATION-R2-20261107-01`；起止 2026-11-07T12:01:06.424843+08:00 ～ 2026-11-07T12:19:27.753771+08:00（任务区间，不是人工工时）。工作树HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，具体执行版本以冻结输入/EMU哈希为准。

**HOLD：两个真实角色完成，功能PASS，S0/S1覆盖NOT_HIT。** 历史环合法S/D/W解析最小修复，当前拒错组带tag仍拒绝；R1完整真实日志离线全链PASS但旧FAIL保留。9宿主方法PASS、4未变方法复用、8合法tag正例和33具名负控通过；184输入冻结，独立方法复核与宿主成本筛选365.702722秒通过。未另开宿主额度。

实际bit100 PASS：25.398553秒/11668guest；正常GOOD TRAP：607.969222秒/268036guest，41调用/84协议行、77退休、81次完整128位及有效输入/身份/元数据和逐调用数值/CSR通过。81次均DIRECT_R并响应，ENQUEUE_P/STALL/KILL_P/PARTIAL_KILL=0，S0/S1 witness均为空；4个已接受较年轻分配后续squash不能替代FU杀P。功能通过不等于覆盖通过。

目标累计633.367775秒，batch宿主12.523900秒，外层645.963262秒；两角色资源/清理PASS，无超限。GUARD_FAIL是NOT_HIT按合同停止，未重试、未加时、未扩围、未重放。184冻结、445生产和此前324文件无漂移。RTL/新核/EDA/切默认/GitHub写入均0。正式18/20，默认0f＋firstdot V2＋原C8保持。

本轮新加速比/面积/时序NOT_TESTED，下表历史18性能行及面积/五档STA原样复用。下一轮集中只读归因S0为何无反压，再对齐S1，提出有可信重叠窗口的最小软件设计及完整验证/预算合同；不重复原镜像探针，不仅凭长DIV假说盲改，不自动进入重放或第20项。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r2-20261107/RESULT.md) · [终态](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r2-20261107/TERMINAL_AUDIT.json) · [覆盖事实](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r2-20261107/review/NOT_HIT_FACTS.json) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r2-20261107/NEXT_STEP.md)。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-calibration-r2-20261107/METRICS.json)。

### 路线影响／接续指令

开始 O2 补测 R3：基于 R2 完整真实日志，集中完成 S0/S1 未命中的只读时序归因与最小软件修订设计。先解释为何81次均DIRECT_R、没有STALL或ENQUEUE_P，再核对F2v压力、e32/e8切换、操作数重载及S1重定向的先后关系，区分实测与推断。给出有依据的最小改动清单、完整覆盖合同、可复用门禁和下一批预算；没有可信重叠窗口就HOLD，不重复同镜像探针。本轮先不改软件或RTL、不运行EMU/NEMU、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并给出下一轮指令。


## 第93条：SP1-E O2补测R3只读归因与M1设计 · 2026-11-07

执行者 @cc77-builder / Agent；操作ID `SP1-E-O2-CANCEL-R3-READONLY-20261107-01`；起止 2026-11-07T12:30:33.924772+08:00 ～ 2026-11-07T12:48:59.958798+08:00（任务区间，不是人工工时）。工作树HEAD `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，候选实际来源由SP1-C冻结和R2执行身份限定。

**只读归因完成；M1最小软件宿主实现GO，目标和第19项资格HOLD。** 重算R2完整日志：81次接受后1拍响应、40对B均在A响应同拍DIRECT_R；1008条活动STATE没有R有效反压。四次指定S1 probe的VFEX4取消分别晚于B响应39/7/7/7拍，不能代替杀P留R。四个S0/四个probe及全部40对PC/seq/ROB时间线已存档。

17份候选源码与SP1-C构建前冻结一致，真实构建日志证明F2v与VFEX4共用VF/V0口3，FMV_X_W解码的FCVT和F2v又同用FEX0。旧FMV排在8条压力后，随后地址add和v8重载，缺乏及时独立释放；S1 DIV只依赖地址，未依赖v8完成或A接受。F2v精确排空、VTYPE/加载/发射分摊无动态观测，不伪称实测。

拟议M1仅提前FMV、以e8零增量vadd替代重载，并将原S1除法前置且真实门控FP生产者，把phase留在分支链。保持41调用/77退休、320F2v、原完整输入/128位结果/CSR/ABI。设计有机制依据，但没有保证重叠的已测窗口；不重跑原镜像、不增加phase或压力，不自动重放。下一批仍建议bit100 300秒/10万guest、正常900秒/30万guest，目标1200/宿主900/外层2100秒；只作一次有界校准提案，不冒充完成上界。

本轮代码改动0、目标0、GNU/新核/EDA0、默认/GitHub写入0；445主源码+445候选源码+405旧材料+184冻结输入无漂移。正式18/20，默认0f＋firstdot V2＋原C8。本轮三指标NOT_TESTED；下表历史18性能行及局部成本原样续档。

[只读归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/RESULT.md) · [设计合同](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/DESIGN_CONTRACT.md) · [验证与预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/VALIDATION_BUDGET.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/NEXT_STEP.md)。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r3-readonly-20261107/METRICS.json)。

### 路线影响／接续指令

开始 O2 补测 R4，按 NEXT_STEP 在独立目录实现 R3 的单一 M1 软件修订：将 FMV 移到 F2v 压力之前，用 e8 零增量 vadd 替代 v8 重载；将 S1 原除法前置并真实门控 FP 生产者，原 phase 只调整分支依赖。保留41调用、77退休、320条F2v、原数据、完整128位及CSR/ABI合同。集中完成 GNU 构建、对象/链接审计、新PC和bit100绑定、必要差异正负控、执行冻结及原两角色预算评审；复用未变证据，失败即停，不扩相位、不增加调用。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；全部通过后给出一次两角色有界校准的GO/HOLD及执行指令，更新计分板。


## 94. O2补测R4：M1软件构建通过，宿主首次准入HOLD（2026-11-07）

- 身份：cc77-builder / Agent；当前分支local/zjhwork-integration-20261024，HEAD 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e。开始与结束时间见对应RESULT.json；历时不作为人工工时。
- 结果：独立M1软件、一次GNU构建、对象/链接审计、新PC/bit100编译绑定通过；第一项宿主闭包检查FAIL后停止，未修后重试。正式验收仍18/20，默认0f＋firstdot V2＋原C8不变。
- 改动：FMV前移、e8零增量vadd替代v8重载、S1原商前置并门控FP生产者；保持41调用/77退休/320架构F2v及5份C/数据/头文件。实际9叶17处custom，BIN 11456字节，SHA256 ff97f03e88624b28c7964faae3c82baa1f199a021f6caab817a1fba753740f46。
- 准确停点：冻结器漏列BASE_REUSE已声明的原fixtures.py出处，校验器要求它。该文件存在且hash正确，实际本地夹具和analyzer均已冻结；279项内容hash相符但闭包不完整。本轮清单生成/校验未对齐，不能将其写成数据运算FAIL或预算超时。
- 首次worker 0.392654秒；外部监督0.432922秒，CHILD_EXIT_1，cleanup_ok=true。13个计划测试方法及预算测量均NOT_RUN；94个序列负控等为计划数量，不是通过数量。新目标/EMU/NEMU/EDA均0，无生产RTL改动、默认切换或GitHub上传。
- 已保留：原FAIL、279项旧冻结及使用锁；445＋445份生产源码、434份旧轮文件、R2的184项和R4的279项hash检查不变。原93条记录原样保留。
- 下一步：R4-R1仅对齐已声明出处清单，复用本轮M1源码、ELF/BIN、对象与bit100组件，不再生成或编译。新身份下集中完成剩余宿主门和一次900秒成本准入；新目标仍HOLD。

### 三项主要指标与历史实测

本轮加速比、面积、时序均NOT_TESTED。以下续列完整18行历史窗口数据、FU/父级面积、五档STA与关键路径；它们不是M1新运行成绩。原G2严格成本NO-GO保留。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](METRICS.json)。


### 路线影响与下一轮指令

开始 O2 补测 R4-R1，按 NEXT_STEP 最小修复冻结器与必需文件清单的不一致，将 BASE_REUSE 已声明的原始 fixtures.py 作为出处输入纳入新冻结。复用 R4 已通过的 M1 源码、GNU ELF/BIN、对象审计和 bit100 组件，不重新生成或编译；保留 R4 原 FAIL、279 项旧冻结及锁。以新身份完成尚未运行的差异正负控、旧完整日志离线复核、独立方法复核和一次900秒宿主预算准入，不新增无关条件。失败即停、不重试、不加时；先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。全部通过后给出原两角色校准的GO/HOLD与下一轮指令，更新计分板。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-host-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-host-20261107/NEXT_STEP.md) · [指标与来源](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-host-20261107/METRICS.json)。


## 95. O2补测R4-R1：宿主准入GO，进入下一轮第19项M1目标校准（2026-11-07）

- 身份：cc77-builder / Agent；operation_id SP1-E-O2-CANCEL-M1-R4-R1-HOST-20261107-01，HEAD 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e，分支local/zjhwork-integration-20261024。起止时间见RESULT.json；不将历时记为人工工时。
- 最小改动：冻结器共用未改required_paths，补原fixtures.py出处，保留实际读取的不可变对象文本。新身份382输入，含原279输入。测试第一方法按用户禁止重生成要求用R4与原构建输入字节一致性替代重新生成；原3项清单负控对准漏项，未新增无关条件。
- PASS：13宿主方法（1.845秒）、94项序列负控、6项bit100绑定负控、3项清单负控；原R1/R2三份完整真实日志离线复核、17处custom的ELF/BIN独立方法复核通过。同一Agent复核，不是队友人工签核；原538 C检查按源码/日志复用，不重跑。
- 预算：单次worker 11.997725秒，外部监督12.056357秒、GUARD_PASS/exit0/cleanup_ok。50000额外STATE解析9.524341秒，原有限样本公式估计381.265913秒<900秒。不是EMU耗时预测或完成保证。
- 复用：全部M1源、ELF/BIN/PC及bit100组件不重生成、不编译；BIN ff97f03e88624b28c7964faae3c82baa1f199a021f6caab817a1fba753740f46。41调用/77退休/84UART/320架构F2v及原完整结果、CSR/ABI合同不变。
- 原始保护：445＋445生产源码、585旧轮文件及原279/当前382冻结核验不变。原R4 FAIL、原R2 NOT_HIT和锁保留，无重试；新EMU/NEMU/参考库加载/构建/EDA/GitHub写入均0。
- 状态：正式18/20，默认0f＋firstdot V2＋原C8。GO只表示宿主准入完成；下一轮即可真实两角色校准，不需重复宿主准备。覆盖命中及必要重放通过后才能记19/20，不自动进入第20项。

### 三项主要指标与历史实测

本轮新加速比、面积、时序均NOT_TESTED。历史18行窗口、FU/父级面积、五档STA及关键路径原样续档；原G2严格成本NO-GO保留。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](METRICS.json)。


### 路线影响与下一轮指令

开始 O2 第19项 M1 两角色有界校准，按 NEXT_STEP 复用 R4-R1 已通过的宿主准入和382项冻结，先核查进程与输入并完成新目标授权绑定，不重编译、不重跑宿主整套。随后串行执行 bit100拒错→候选正常，分别300秒/10万guest、900秒/30万guest；最多2个目标进程，目标累计1200秒、宿主900秒、外层2100秒。保持CPU4、整组最多4线程、RSS12GiB、日志2GiB，以及41调用、77退休、完整128位、CSR/ABI和S0/S1覆盖合同。失败或未命中即停，不重试、不加时、不扩围、不自动重放；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板，给出第19项剩余重放安排和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-r1-host-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-r1-host-20261107/NEXT_STEP.md) · [三指标与来源](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-r4-r1-host-20261107/METRICS.json)。


## 96. O2第19项M1两角色有界校准：功能PASS，必需覆盖NOT_HIT（2026-11-07）

- 开发时间：2026-11-07 13:48:42～2026-11-07 14:01:44（UTC+08:00）；历时不作为人工工时。身份cc77-builder / Agent，operation_id SP1-E-O2-CANCEL-M1-CALIBRATION-20261107-01，HEAD 347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e，分支local/zjhwork-integration-20261024。
- 实际执行恰好2个目标：bit100拒错25.727555秒/11653guest/预期exit1，严格提交组绑定及实际回执PASS；候选正常583.112479秒/267282guest/exit0/GOOD TRAP，41调用/84UART/77退休及完整结果、CSR/ABI合同通过。
- 覆盖未命中：78接受全部DIRECT_R，77响应、1次KILL_R；P入队、反压、P/R双占用、KILL_P及PARTIAL_KILL均0。S0/S1见证0/0，正式18/20。原R4-R1宿主准入通过不代替真实覆盖，原R4 FAIL和R2未命中保留。
- 新时序证据：phase4 A在262038接受/262039响应，B在262039进入R、262040被实际ROB0:45取消；A在262043退休。这是R槽取消，不是P中杀B/R中留A。phase0/1/2的probe B未进入FU。944条STATE观察均outready1、无P占用；动态F2v grant和branch PC仍未采集。
- 预算与资源：目标活动608.811574秒，worker宿主1.962269秒，外部610.835181秒（10分11秒）；各role/guest、1200/900/2100总预算均满足。峰值1线程；RSS最高78512128字节；原始日志3569613字节、无截断、清理通过。外部GUARD_FAIL/CHILD_EXIT_1保留，原因是完成后的NOT_HIT传播，不是超时。
- 版本保护：复用382项冻结及13方法宿主证据，无重编译；445＋445生产源码、711份旧轮文件及授权/镜像保持。无重试、无加时、无扩围、无重放；不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。
- 后续R5只读定位没有父级反压/P入队的原因，依据真实日志与实际构建判断一次最小软件修订GO/HOLD；没有可信触发窗口则暂存，不重复同镜像或扫phase。默认0f＋firstdot V2＋原C8不变。

### 三项主要指标与历史实测

本轮267282guest是校准刺激总数，没有RVV公平计时窗；与R2软件布局不同，不能计算硬件加速比。新加速比、面积、时序均NOT_TESTED。以下18行历史窗口、FU/父级面积、五档STA及关键路径原样续档，原G2严格成本NO-GO保留。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](METRICS.json)。


### 路线影响与下一轮指令

开始 O2 补测 R5，按 NEXT_STEP 只读分析 M1 两角色真实日志，先解释为何944条STATE观察中outready均为1、没有反压和P入队，再核对phase4的A响应、B进入R及取消顺序。复用本轮功能、bit100、资源与宿主证据，不重跑同镜像、不扫描相位、不新增无关门禁。结合现有源码和实际构建给出一次最小软件修订的GO/HOLD及验证合同；没有可信触发窗口就暂存补测方向。先不改代码、不运行EMU/NEMU、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并给出下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-calibration-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-calibration-20261107/NEXT_STEP.md) · [三指标与来源](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-m1-calibration-20261107/METRICS.json)。

## 97. O2补测R5只读归因：最小软件修订HOLD，暂存触发方向（2026-11-07）

- 工作日期2026-11-07（UTC+08:00）；操作`SP1-E-O2-CANCEL-R5-READONLY-20261107-01`，cc77-builder / Agent。只读分析早于归档快照，未记录精确开始时刻，不补造工时。归档时刻见RESULT.json。
- 基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，本地分支`local/zjhwork-integration-20261024`；默认0f＋firstdot V2＋原C8，正式18/20，未切默认。
- 复核382项冻结、17份源码及与候选EMU同一生成清单的6份生成RTL；按ROB分配代/固定call_plan复原40对A/B。78接受全DIRECT_R、77响应均1拍、37对B.accept=A.response；944个STATE均outready1，P入队/输出STALL/双槽占用均0。77个有效输出时刻未与FEX0向量写回请求同时竞争；实际仲裁存在，ready不是绑高。
- M1的vadd.vx拆分为I2v临时向量和向量ALU，8条vfmv不能按8拍连续写回压力计算。四个S0的ROB→FU等待由R2的38/39/41/44降为M1的19/20/25/26拍，但未形成反压；此为不同刺激归因，不能当加速比。
- phase0/1/2的B在接受前取消；phase4 A于262038接受、262039响应，B于262039直接进入R，262040被杀。没有“R保A/P杀B”。动态F2v grant和I2v/vialu释放时刻仍缺，无法给出可信的最小软件触发窗口。
- 决定：只读归因完成；M2软件修订HOLD/方向暂存，不再盲调phase、增压或重跑同镜像。保留M1功能/bit100/资源PASS、原NOT_HIT/GUARD_FAIL及旧锁；不新增无关门禁，不削减第19项原覆盖。
- 本轮新目标/EMU/NEMU/构建/EDA/重试/相位扫描均0，软件/RTL/运行器未改，未上传GitHub。新加速比、面积、时序均NOT_TESTED，以下历史三项指标完整续档；严格G2成本NO-GO保留。

### 三项指标：按原合同复用

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/METRICS.json)。


### 路线影响与下一轮指令

开始 SP1-E 第20项 timed DIV/SQRT 宿主准备与预算评审，按 NEXT_STEP 暂存第19项F2v反压补测，复用已有DIV/SQRT功能、身份和运行器证据，集中明确计时负载、同镜像公平窗口、必要差异检查、最少角色及完整预算。已有部分直接复用，只补真正缺项；依据不足就HOLD，不以第20项替代第19项覆盖。先不运行EMU/NEMU、不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后给出GO/HOLD、可执行批次和下一轮指令。

[只读结论](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/RESULT.md) · [完整时间线](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/analysis/PAIRS.csv) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/NEXT_STEP.md) · [三项指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-o2-cancel-r5-readonly-20261107/METRICS.json)。

## 98. 第20项timed DIV/SQRT宿主准备：HOST GO，正式预算HOLD（2026-11-07）

- 工作日期2026-11-07（UTC+08:00），cc77-builder / Agent，操作`SP1-E-TIMED-DIV-SQRT-HOST-20261107-01`；归档快照/结论时间见BEFORE/RESULT，不补造此前未记起始工时。
- 基点347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e；本地local/zjhwork-integration-20261024。第19项F2v反压补测暂存，正式18/20，默认0f＋firstdot V2＋原C8。
- 复用原9552B镜像、3数据集×3算子×6调用＝54窗/432条DIV/SQRT/1条guard，9格各4计分窗、20条窗口退休/instret差15、完整128位输入输出和CSR、精确重放合同均保留。137份旧材料SHA一致，原GNU/41项测试/40假ABI控不重跑。
- 独立接入候选和0f观察器、当前提交组bit100及三角色执行/外部监督；实际guard为e64/VL2读入→e8/VL8 vdot→e64/VL2写出，只增加冻结PC/word对应的load/配置检查。11适配方法有PASS证据，原两次宿主FAIL（上下文不适配、夹具ROB负索引）原位保留，修订未触目标软件/RTL。
- 宿主CPU4完整合成54窗/432算子解析与哈希/配对约1.380秒，不能作为目标时间上界。正式五角色6300/7200秒继续HOLD；准备的最少完整校准为bit100300秒/10万guest→候选1500秒/100万guest→0f1500秒/100万guest，目标3300＋宿主900＝外层4200秒，未来独立授权才执行。
- 冻结35项输入及4份cwd配套文件；无执行授权/消费锁/target输出。共享监控机制未变、失败即停、不重试/加时/自动重放。校准不会提升18/20，第20项最终须预算和必要重放闭合。
- 本轮新目标/EMU/NEMU/GNU/新核/EDA均0，无RTL/镜像修改、无默认切换或GitHub上传。三项指标及DIV/SQRT退化率NOT_TESTED，历史数值如下完整续档，原严格G2成本NO-GO保留。

### 三项指标：历史复用

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/METRICS.json)。


### 路线影响与下一批指令

开始 SP1-E 第20项 timed DIV/SQRT 三角色完整调用有界校准，按 NEXT_STEP 先核查进程、冻结输入和宿主准入，接受本轮独立预算后串行执行 bit100拒错→候选正常→0f正常。分别300秒/10万guest、1500秒/100万guest、1500秒/100万guest；目标累计3300秒、宿主900秒、外层4200秒。保持完整54窗、432条DIV/SQRT、完整128位和CSR/退休绑定、逐窗控制相等及9格各自最多2%退化，沿用CPU4/整组4线程/RSS12GiB/日志2GiB。失败、未拒错、超限或退化即停，不重试、不加时、不跳过继续、不自动重放；第19项继续暂存。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并判断正式预算和必要重放。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/RESULT.md) · [预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/BUDGET_REVIEW.md) · [下一批](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/NEXT_STEP.md) · [指标来源](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-host-20261107/METRICS.json)。


## 第99条：第20项 timed DIV/SQRT 三角色校准（2026-11-07）

第20项三角色校准按墙钟上限停止：bit100通过，候选正常超时，0f正常未启动。完整正常样本和9格配对均缺，HOLD；正式18/20，默认0f＋firstdot V2＋原C8不变。

@cc77-builder / Agent；操作ID `SP1-E-TIMED-DIV-SQRT-CALIBRATION-20261107-01`。预执行快照 2026-11-07T07:03:12.690385+00:00，记录 2026-11-07T15:33:19.171714+08:00；实际运行25分24秒不计作人工工时。基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，未提交。

bit100 23.572946秒/9205 guest PASS；候选正常1500.000183秒被外部TARGET墙钟监督终止，原GUARD_FAIL、锁和RUNNING中间态保留。真实2个目标；0f未启动，无重试/重放。26/54组标记、208/432退休仅为局部观察，14条完整UART，无正常收据/汇总/最终guest；不得转为完整功能、9格2%或跨硬件PASS。监督清理及输入不变核对通过。

### 三项指标留档

第20项三角色校准按墙钟上限停止：bit100通过，候选正常超时，0f正常未启动。完整正常样本和9格配对均缺，HOLD；正式18/20，默认0f＋firstdot V2＋原C8不变。

本轮新加速比、面积、时序均NOT_TESTED；纯DIV/SQRT保护负载的9格退化率亦NOT_TESTED。原始FAIL与锁保留，不把26个标记窗口或208条退休算作完整通过。以下18行性能、FU/父级面积及五档STA均为历史复用。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/METRICS.json)。


### 路线影响与下一轮指令

开始第20项 timed DIV/SQRT 预算收口与最小开销方案评审：基于本轮1500秒超时日志，核查窗口外校验、格式化输出与UART成本，比较保留原镜像的新独立预算和最小窗口外输出调整，选出一个有依据的方案并冻结下一批合同。保留54窗、432算子、完整结果、CSR/退休绑定、逐窗控制相等、9格2%及精确重放要求，复用已通过bit100与未变证据；依据不足就HOLD，不重复同预算校准、不缩减覆盖。先不改代码、不运行EMU/NEMU、不构建新核、不做EDA、不切默认、不上传GitHub；第19项继续暂存，完成后给出GO/HOLD和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/RESULT.md) · [预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/BUDGET_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/NEXT_STEP.md) · [证据清单](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-calibration-20261107/EVIDENCE_MANIFEST.json)。


## 第100条：第20项预算收口与原镜像四角色设计（2026-11-07）

第20项预算收口完成：GO仅限原镜像四角色适配设计；当前目标准入HOLD，未运行EMU/NEMU。选择保留原镜像、复用真实bit100，以新独立停止预算完成两次正常及两次重放；未选择输出改版。正式18/20，默认0f＋firstdot V2＋原C8不变，第19项继续暂存。

@cc77-builder / Agent；操作ID `SP1-E-TIMED-DIV-SQRT-BUDGET-REVIEW-20261107-01`；快照 2026-11-07T07:45:53.164174+00:00，记录 2026-11-07T15:54:39.654815+08:00；基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，未提交。

只读核查真实26标记窗/208退休及14完整UART行；调用间隔中位22974周期/4766条退休，实际ELF确认每窗192～194条标量除法/求余、至少210～211次UART状态读/数据写。不能把全部窗外耗时归给UART。保留原镜像方案，避免输出改版引入新布局、解析及bit100绑定。137材料/35冻结和未变11方法复用，独立字节/计数方法复核通过；无新代码或目标。

拟定剩余四角色各4800秒/200万guest，目标19200＋执行宿主900＝执行外层20100秒；两次正常九格通过后才重放。新预算只为提案，非已准入上界或新执行授权；旧1500秒FAIL/原正式预算HOLD保留。全部通过最多推进19/20，第19项仍HOLD。

### 三项指标

第20项预算收口完成：GO仅限原镜像四角色适配设计；当前目标准入HOLD，未运行EMU/NEMU。选择保留原镜像、复用真实bit100，以新独立停止预算完成两次正常及两次重放；未选择输出改版。正式18/20，默认0f＋firstdot V2＋原C8不变，第19项继续暂存。

本轮目标/构建/EDA均0，新加速比、面积、时序及九格退化率NOT_TESTED。窗口外操作计数和约3185秒情景不是新性能资格；以下数据全部为原同口径历史复用。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/METRICS.json)。


### 接续指令

开始第20项原镜像四角色接入与有界验收，按 NEXT_STEP 复用原ELF/BIN、0f/候选EMU及已通过bit100，完成四角色差异接入、历史证据绑定、必要宿主检查和执行冻结。全部准入通过后，同轮执行候选正常→0f正常，九格比较通过后再执行候选重放→0f重放。我接受新的每角色4800秒/200万guest、目标累计19200秒、执行宿主900秒、执行外层20100秒预算。保持54窗、432算子、完整结果与CSR/退休绑定、逐窗控制相等、9格2%及精确重放。任一失败即停，不重试、不加时、不借用预算、不增加角色；第19项继续暂存。不改RTL、不改目标软件或重编镜像、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并给出结论和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/RESULT.md) · [冻结设计](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/DESIGN_CONTRACT.json) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/NEXT_STEP.md) · [证据清单](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-budget-review-20261107/EVIDENCE_MANIFEST.json)。


## 记录101：第20项四角色宿主准入FAIL，未启动目标（2026-11-07）

第20项四角色接入已实现，但宿主准入 FAIL，目标准入 HOLD。首6项方法通过，第7项负控错误选中首调用窗口，预期拒绝未发生；第8项未执行。遵守失败即停，本轮EMU/NEMU为0，正式进度仍18/20，默认0f＋firstdot V2＋原C8不变，第19项继续暂存。

@cc77-builder / Agent；`SP1-E-TIMED-DIV-SQRT-FOUR-20261107-01`；2026-11-07T16:10:49.080333+08:00。已接受新预算但宿主准入未通过；本轮6 PASS/1 FAIL/1 NOT_RUN，外部耗时2.913725秒。新增负控将seq2首调用误作计分窗口，原比较器正确排除repeat0；下轮语义定位measured窗口，复用6项通过证据后补剩余准入。原FAIL/锁全部保留。

# 本轮三项指标与历史对照

第20项四角色接入已实现，但宿主准入 FAIL，目标准入 HOLD。首6项方法通过，第7项负控错误选中首调用窗口，预期拒绝未发生；第8项未执行。遵守失败即停，本轮EMU/NEMU为0，正式进度仍18/20，默认0f＋firstdot V2＋原C8不变，第19项继续暂存。

本轮新加速比、面积、时序及第20项九格退化率均为 **NOT_TESTED**。没有目标执行或EDA，不能把宿主合成夹具作为硬件测量。本轮历史数值不变；新宿主证据不增加功能验收计数。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](METRICS.json)。


### 下一轮

开始第20项原镜像四角色 R1：按 NEXT_STEP 最小修复宿主负控的计分窗口定位，用 dataset/op/repeat 语义键唯一选择 measured 窗口并断言实际命中，保留原 FAIL 与锁，复用本轮6项通过证据及未变运行器。集中完成受影响测试、尚未执行的冷进程导入与授权拒绝检查、新执行冻结和宿主准入；全部通过后，同轮串行执行候选正常→0f正常，九格配对通过后执行候选重放→0f重放。沿用已接受的每角色4800秒/200万guest、目标19200秒、宿主900秒、外层20100秒预算及原资源、完整54窗/432算子、9格2%与精确重放门槛，复用bit100。失败即停、不重试、不加时、不扩围；不改RTL或镜像、不构建新核、不做EDA、不切默认、不上传GitHub，第19项继续暂存。完成后更新计分板并给出下一轮指令。

[完整结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-20261107/RESULT.md) · [NEXT_STEP](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-20261107/NEXT_STEP.md) · [证据清单](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-20261107/EVIDENCE_MANIFEST.json)。


## 记录102｜2026-11-07 第20项四角色 R1：ITEM20_PASS，19/20

第20项四角色 R1 已通过：候选正常、0f正常、候选重放和0f重放全部完成，九格配对及两次精确重放通过。正式验收由18/20推进到 **19/20**；第19项继续 HOLD。默认仍为 **0f＋firstdot V2＋原C8**，没有切换或上传。

开始 2026-11-07T16:14:37.817328+08:00；记录 2026-11-07T19:34:48.366405+08:00（UTC+08:00）；cc77-builder / Agent；操作ID `SP1-E-TIMED-DIV-SQRT-FOUR-R1-20261107-01`。Git `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e` / `local/zjhwork-integration-20261024`，源码身份由118项冻结与445/398源码快照确定。宿主最小负控修复复用6项PASS，补齐2项PASS；按当前用户授权一次性完成四角色，没有重试。

|角色|结果|单调计时活动秒数|guest cycles|完整窗口/算子|峰值线程|峰值RSS MiB|
|---|---|---:|---:|---:|---:|---:|
|candidate-normal|PASS|3389.801730|1265777|54/432|1|74.629|
|baseline-normal|PASS|3274.078525|1265427|54/432|1|72.375|
|candidate-replay|PASS|2698.085476|1265777|54/432|1|71.625|
|baseline-replay|PASS|2741.615482|1265427|54/432|1|72.750|

目标累计12103.581212/19200秒，执行宿主27.808091/900秒，外层12131.477884/20100秒；各角色4800秒/200万guest限制满足。两次精确重放PASS，历史bit100复用。所有本轮进程已结束，原FAIL与锁保留。UTC与单调耗时差异已记录，不替代单调预算。

# 第20项四角色 R1：新保护结果与历史三项指标

第20项四角色 R1 已通过：候选正常、0f正常、候选重放和0f重放全部完成，九格配对及两次精确重放通过。正式验收由18/20推进到 **19/20**；第19项继续 HOLD。默认仍为 **0f＋firstdot V2＋原C8**，没有切换或上传。

## 本轮新增 timed DIV/SQRT 测量

以下每格均值仅取 repeat2～5。first/warmup 不进入均值，但仍通过完整结果、CSR、退休及重放检查。九格全部满足候选/0f ≤ 1.02；8格相同，dataset0/vdivu下降0.25周期（0.168067%）。这是共享执行资源的保护验收，不是新增VDOT加速比。

|dataset|算子|0f均值 cycles|候选均值 cycles|候选相对0f变化|原2%门槛|
|---|---|---:|---:|---:|---|
|0|vdivu|148.75|148.50|-0.168067%|PASS|
|0|vfdiv|208.00|208.00|0.000000%|PASS|
|0|vfsqrt|216.00|216.00|0.000000%|PASS|
|1|vdivu|149.00|149.00|0.000000%|PASS|
|1|vfdiv|208.00|208.00|0.000000%|PASS|
|1|vfsqrt|224.00|224.00|0.000000%|PASS|
|2|vdivu|124.00|124.00|0.000000%|PASS|
|2|vfdiv|208.00|208.00|0.000000%|PASS|
|2|vfsqrt|216.00|216.00|0.000000%|PASS|

本轮 VDOT/RVV 加速比、面积和 STA 新测均为 **NOT_TESTED**；没有运行VDOT性能负载或EDA。下列已有测量按原合同复用，未改写成此次实测。完整新54窗×4角色数据见 [all-windows.csv](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/all-windows.csv)，原始摘要见 [qualification.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/target-01/qualification.json)。

## 历史加速比、面积与时序（复用）

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/METRICS.json)。


路线影响：第20项通过，正式18/20→19/20。第19项仍暂存；后续只评审最小缺失时序观测与定点触发，未经下一轮授权不实施或重跑。无RTL/镜像更改，无新核/EDA，默认不变、未上传。

下一轮指令：开始 SP1-E 第19项最小观测与定点补测设计评审：基于 R5 已冻结结论与现有候选构建，明确 FEX0 向量写回请求、I2v/vialu 释放及 VDOT 响应的相对时序缺口，先核对现有可见信号，再设计必要的最小观察补丁与有界触发合同。保留 S0/S1 原覆盖、完整结果、取消及精确重放要求；没有可信触发窗口就 HOLD。只做设计和成本评审，不改代码、不运行 EMU/NEMU、不构建新核、不做 EDA、不切默认、不上传 GitHub；完成后给出 GO/HOLD 和下一轮指令。

[本轮结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/RESULT.md) · [原始数据与身份](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/RESULT.json) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/NEXT_STEP.md) · [manifest](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-timed-div-sqrt-four-role-r1-20261107/EVIDENCE_MANIFEST.json)。


## 记录103｜2026-11-07 第19项最小观察设计：GO_DESIGN / HOLD_TARGET

**最小观察方案设计GO；第19项定点修订/目标补测HOLD。** 现有证据不足以给出可信FEX0/VDOT碰撞窗口。正式仍19/20，默认0f＋firstdot V2＋原C8不变；第20项PASS保持。

快照起点 2026-11-07T20:19:47.366915+08:00；记录 2026-11-07T20:27:09.729472+08:00，cc77-builder / Agent，操作 `SP1-E-ITEM19-OBS-DESIGN-20261107-01`。分支 `local/zjhwork-integration-20261024`，Git `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。只读核查当前源码、实际生成仲裁和旧R5证据，未变源码445/398份；不冒称独立成员验收。

新增结论：FEX0 vector请求缺少真实时间轴；I2v/vialu拆分共享ROB，需u.robIdx而非非first的allocatePtr建立身份；PerfDebugInfo无PC；生产输出可前递，WB grant不能等同消费。拟以默认关闭开关，在VDotO2.scala、ExeUnit.scala、WbArbiter.scala、Rob.scala四处添加只观测侧带；VDotElastic与数据通路/ready/仲裁保持。设计文档不是已实施补丁。

没有可信定点触发窗口，M2和第19项目标继续HOLD。下一轮可实现观察器并做必要宿主/局部中性，不自动构建全核或启动诊断；300/900秒两角色只是预算提案，新增打印开销未测。原S0/S1、完整128位、CSR/ABI、bit100及重放合同不减。第20项PASS保留，正式仍19/20。

# 第19项观察设计：三项指标留档

本轮只读设计，EMU/NEMU、新构建及EDA均0；新加速比、面积、时序和新观察器运行开销全部 **NOT_TESTED**。正式19/20，默认0f＋firstdot V2＋原C8。以下为按原合同复用的历史事实，不是新构建实测，也不自动批准候选切换。记录102的timed DIV/SQRT九格保护PASS继续有效，不能当作VDOT加速比。

以下逐数据集保留同镜像窗口均值；加速比均为该硬件上 RVV cycles / vdot cycles。不可把硬件候选相对0f的收益与RVV/vdot加速比混为一项。

|负载|dataset|0f vdot|候选 vdot|0f/候选RVV|0f RVV/vdot|候选 RVV/vdot|候选vdot周期下降|记录|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|51|
|chain-256|1|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|58|
|chain-256|2|1857.000000|1601.250000|5440.500000/5440.500000|2.929725363×|3.397658080×|13.772213%|60|
|single-1|0|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|62|
|single-1|1|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|64|
|single-1|2|71.000000|70.000000|85.250000/85.250000|1.200704225×|1.217857143×|1.408451%|66|
|batch|0|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|1|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|batch|2|221.000000|221.000000|678.000000/678.000000|3.067873303×|3.067873303×|0.000000%|69|
|stream|0|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|1|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|stream|2|1127.500000|1126.250000|1133.000000/1133.000000|1.004878049×|1.005993341×|0.110865%|70|
|original-C8-8x32-basic|0|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|53|
|original-C8-8x32-reuse|0|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|53|
|original-C8-8x32-basic|1|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|54|
|original-C8-8x32-reuse|1|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|54|
|original-C8-8x32-basic|2|643.750000|642.500000|356.000000/356.000000|0.553009709×|0.554085603×|0.194175%|55|
|original-C8-8x32-reuse|2|273.000000|272.000000|299.000000/299.000000|1.095238095×|1.099264706×|0.366300%|55|

## 历史面积与五档STA

范围：Nangate45 Typical 1.1V/25°C、原G2关闭观察器的局部FU及含VDot的真实父级；不是全核面积，不是布线后签核，不是已实现Fmax。原G2严格成本门NO-GO事实保留，本轮只复用数值。

|边界|0f面积(µm²)|候选面积(µm²)|变化|
|---|---:|---:|---:|
|FU_um2|17298.246|18322.878|5.923329%|
|inclusive_parent_um2|284614.946|285241.642|0.220191%|

|档位|T(ns)|load(pF)|0f FU slack|候选FU slack|0f父级slack|候选父级slack|候选FU Q|候选父级Q|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|nominal|1.0|0.005|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|0.5|0.005|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|2.0|0.005|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|1.0|0.001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|1.0|0.02|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q按原表 T−最差setup slack 对比值保留，不能直接写成全核实际周期。JSON保留所有原始路径及关键路径筛选：FU主路径为operand→R槽，父级nominal为vsew→内部寄存器，load020最差移至fflags输出；ready与gate_enable另列，不混同主路径。


| 档位/边界 | 历史最差路径起点→终点 | slack ns |
|---|---|---:|
| nominal/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| nominal/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| period050/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -1.290381 |
| period050/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.837809 |
| period200/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | 0.209619 |
| period200/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -1.337809 |
| load001/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load001/父级 | `io_in_bits_vpu_vsew[1] (input port clocked by core_clk)` → `c201899 (rising edge-triggered flip-flop clocked by core_clk)` | -2.337809 |
| load020/FU | `io_in_bits_data_src_0[14] (input port clocked by core_clk)` → `c8968 (rising edge-triggered flip-flop clocked by core_clk)` | -0.790381 |
| load020/父级 | `c201714 (rising edge-triggered flip-flop clocked by core_clk)` → `io_out_bits_fflags[1] (output port clocked by core_clk)` | -2.391613 |


完整历史源表、ready/gate路径及数据集原证据pins见[METRICS.json](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/METRICS.json)。


路线影响：不重复旧M1和phase扫描，先补最小观察能力；四处观察修改前再次说明具体RTL改法。无代码/目标/构建/EDA/默认切换/GitHub写入。

下一轮：开始第19项最小观察器实现与宿主验证：按 DESIGN 和 OBSERVATION_SCHEMA，先说明四个 RTL 源文件的具体改法，在独立候选目录实现默认关闭的调度/写回侧带观察，保持原数据通路、仲裁、ready 和 SP1/T13 协议；完成微操作身份与时序解析正负控、默认关闭检查和必要局部观察中性验证，并评审构建及一次诊断的预算。保留 S0/S1 原覆盖和第19项 HOLD；先不构建全核、不运行 EMU/NEMU、不改软件镜像、不做 EDA、不切默认、不上传 GitHub。完成后给出 GO/HOLD 和下一轮指令。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/RESULT.md) · [设计](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/DESIGN.md) · [预算和触发合同](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/BOUNDED_CONTRACT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/NEXT_STEP.md) · [manifest](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observation-design-20261107/EVIDENCE_MANIFEST.json)。


## 记录104：第19项最小观察器实现与宿主验证

GO_HOST_IMPLEMENTATION_HOLD_TARGET。独立四文件overlay增加默认关闭侧带；四单元编译、六项旗标、十二次局部CHIRRTL、六对功能投影和七组身份正负控通过。仅局部结构中性，不是事件仿真/形式证明/全核PASS。生产445、旧候选398源码和历史443输入未变。旧FAIL及锁保留。正式19/20，默认0f＋firstdot V2＋原C8；本轮全核构建、目标和EDA均0。

本轮新加速比、面积、时序均NOT_TESTED，历史指标按原合同复用：

|指标|0f|SP1候选|
|---|---:|---:|
|chain-256三数据集 RVV/VDOT|2.929725×|3.397658×|
|batch三数据集 RVV/VDOT|3.067873×|3.067873×|
|C8 reuse三数据集 RVV/VDOT|1.095238×|1.099265×|
|FU面积 μm²|17298.246|18322.878|
|含DIV父级面积 μm²|284614.946|285241.642|
|nominal FU Q ns|1.268520|1.790381|
|nominal父级Q ns|3.393998|3.337809|

历史Nangate45同约束边界数据，Q=T−最差setup slack，不是全核频率。完整18格窗口/五档STA/原证据在本轮METRICS.json，未覆盖旧记录。

下一步：独立观察EMU构建及诊断准入，3600秒仅建议构建停止上限，不代表当前已授权。目标预算因新打印/解析开销未知继续HOLD；保留S0/S1和重放，不生成M2或扫描phase。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-impl-20261107/RESULT.md) · [三项指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-impl-20261107/METRICS.json) · [预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-impl-20261107/BUDGET_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-impl-20261107/NEXT_STEP.md)


## 记录105：独立观察EMU构建准入HOLD

**HOLD_HOST_SUPERVISOR_STARTUP_RACE。** 独立物理副本24596文件/精确4个既有观察补丁差异已核对；新宿主监督入口出现启动CPU亲和竞态，正常及非零退出用例FAIL，超时用例的泛化FAIL断言不足以授予资格。按要求停止；实际构建0次，3600秒使用0秒，没有新EMU或目标。原生产445/候选398/历史443输入不变。正式19/20，默认不变。保留原FAIL，不现场修复重跑。

下一轮：exec前设置CPU亲和，永久保存夹具回执并启用failfast；最小宿主门和剩余外部依赖冻结通过后，同轮一次3600秒独立构建。无需重跑未变RTL验证或复制源码；不自动进入诊断。[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-20261107/NEXT_STEP.md)。

### 三项指标（历史复用）

|工作负载|数据集|0f VDOT cycles|SP1 VDOT cycles|0f RVV cycles|SP1 RVV cycles|0f加速比|SP1加速比|
|---|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|chain-256|1|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|chain-256|2|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|single-1|0|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|single-1|1|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|single-1|2|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|batch|0|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|batch|1|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|batch|2|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|stream|0|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|stream|1|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|stream|2|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|original-C8-8x32-basic|0|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|0|273.0|272.0|299.0|299.0|1.095238×|1.099265×|
|original-C8-8x32-basic|1|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|1|273.0|272.0|299.0|299.0|1.095238×|1.099265×|
|original-C8-8x32-basic|2|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|2|273.0|272.0|299.0|299.0|1.095238×|1.099265×|

历史Nangate45映射面积（μm²）：FU 0f=17298.246、SP1=18322.878；含DIV父级0f=284614.946、SP1=285241.642。

|档位|0f FU slack ns|SP1 FU slack ns|0f父级slack ns|SP1父级slack ns|SP1 FU Q ns|SP1父级Q ns|
|---|---:|---:|---:|---:|---:|---:|
|nominal|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q=T−最差setup slack，不能当全核实际周期。FU历史主路径operand→R槽；父级nominal为vsew→内部寄存器，load020转为fflags输出；完整起终点、ready/gate路径和原来源在METRICS.json。以上全部是历史复用，本轮三项指标NOT_TESTED。


## 记录106：R1宿主通过，实际构建因RSS超限HOLD

R1 exec前亲和、正常/非零/超时回收3项宿主PASS；本轮唯一一次全核构建已启动，Scala及Chisel展开完成，firtool阶段在378.804秒触发RSS_LIMIT，380.636秒回收完毕。峰值17211658240字节，高于16GiB上限约30.32MiB；峰值84线程，日志284189字节。没有重试、加时或新EMU/NEMU运行。正式19/20，默认0f＋firstdot V2＋原C8不变。

失败后7820外部/449保护输入未变；独立源码清单仅.git/index字节改变，HEAD与暂存逻辑条目一致，原字节检查FAIL保留。生产445/旧候选398源码重新核对未变。下一轮R2复用已编译类、分阶段结束Mill后再展开，保持原后处理/16GiB，并使用新的独立单次3600秒预算；不自动进入诊断。[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r1-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r1-20261107/NEXT_STEP.md) · [资源归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r1-20261107/RESOURCE_ANALYSIS.md)。

### 三项指标（历史复用，本轮未测）

|工作负载|数据集|0f VDOT cycles|SP1 VDOT cycles|0f RVV cycles|SP1 RVV cycles|0f加速比|SP1加速比|
|---|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|chain-256|1|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|chain-256|2|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|single-1|0|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|single-1|1|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|single-1|2|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|batch|0|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|batch|1|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|batch|2|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|stream|0|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|stream|1|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|stream|2|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|original-C8-8x32-basic|0|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|0|273.0|272.0|299.0|299.0|1.095238×|1.099265×|
|original-C8-8x32-basic|1|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|1|273.0|272.0|299.0|299.0|1.095238×|1.099265×|
|original-C8-8x32-basic|2|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|2|273.0|272.0|299.0|299.0|1.095238×|1.099265×|

历史Nangate45映射面积（μm²）：FU 0f=17298.246、SP1=18322.878；含DIV父级0f=284614.946、SP1=285241.642。

|档位|0f FU slack ns|SP1 FU slack ns|0f父级slack ns|SP1父级slack ns|SP1 FU Q ns|SP1父级Q ns|
|---|---:|---:|---:|---:|---:|---:|
|nominal|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q=T−最差setup slack，不能当全核实际周期。FU历史主路径operand→R槽；父级nominal为vsew→内部寄存器，load020转为fflags输出；完整起终点、ready/gate路径和原来源在METRICS.json。以上全部是历史复用，本轮三项指标NOT_TESTED。


## 记录107：R2消除Mill并存，JVM＋firtool仍触发RSS上限

R2新增3项宿主门PASS，复用R1监督；同classpath直接top.SimTop，原Make后处理不变。唯一一次构建352.629秒触发RSS_LIMIT，353.065秒回收完毕；峰值17232977920字节（16.049GiB），31线程、250327字节日志。没有Mill父进程，约10GiB JVM与6.04GiB firtool仍并存；未生成EMU，不重试或加时。

24595源码＋18061外部＋456保护输入及逻辑索引前后全部PASS，旧R1索引字节FAIL保留。正式19/20，默认0f＋firstdot V2＋原C8；新三指标NOT_TESTED。下一轮R3评审CHIRRTL→退出JVM→独立firtool→原Make后处理，先确认FIR/附属闭包，再接受新的单次3600秒构建，保持16GiB。本轮无目标/EDA/切换/上传。[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r2-20261107/RESULT.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r2-20261107/NEXT_STEP.md)。

### 三项指标（历史复用，本轮未测）

|工作负载|数据集|0f VDOT cycles|SP1 VDOT cycles|0f RVV cycles|SP1 RVV cycles|0f加速比|SP1加速比|
|---|---:|---:|---:|---:|---:|---:|---:|
|chain-256|0|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|chain-256|1|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|chain-256|2|1857.0|1601.25|5440.5|5440.5|2.929725×|3.397658×|
|single-1|0|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|single-1|1|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|single-1|2|71.0|70.0|85.25|85.25|1.200704×|1.217857×|
|batch|0|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|batch|1|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|batch|2|221.0|221.0|678.0|678.0|3.067873×|3.067873×|
|stream|0|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|stream|1|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|stream|2|1127.5|1126.25|1133.0|1133.0|1.004878×|1.005993×|
|original-C8-8x32-basic|0|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|0|273.0|272.0|299.0|299.0|1.095238×|1.099265×|
|original-C8-8x32-basic|1|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|1|273.0|272.0|299.0|299.0|1.095238×|1.099265×|
|original-C8-8x32-basic|2|643.75|642.5|356.0|356.0|0.553010×|0.554086×|
|original-C8-8x32-reuse|2|273.0|272.0|299.0|299.0|1.095238×|1.099265×|

历史Nangate45映射面积（μm²）：FU 0f=17298.246、SP1=18322.878；含DIV父级0f=284614.946、SP1=285241.642。

|档位|0f FU slack ns|SP1 FU slack ns|0f父级slack ns|SP1父级slack ns|SP1 FU Q ns|SP1父级Q ns|
|---|---:|---:|---:|---:|---:|---:|
|nominal|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|period050|-0.768520|-1.290381|-2.893998|-2.837809|1.790381|3.337809|
|period200|0.731480|0.209619|-1.393998|-1.337809|1.790381|3.337809|
|load001|-0.268520|-0.790381|-2.393998|-2.337809|1.790381|3.337809|
|load020|-0.268520|-0.790381|-2.413199|-2.391613|1.790381|3.391613|

Q=T−最差setup slack，不能当全核实际周期。FU历史主路径operand→R槽；父级nominal为vsew→内部寄存器，load020转为fflags输出；完整起终点、ready/gate路径和原来源在METRICS.json。以上全部是历史复用，本轮三项指标NOT_TESTED。


### 记录108：第19项构建入口 R3 宿主HOLD

2026-11-07T22:20:37.015103+08:00～2026-11-07T22:25:54.013149+08:00；@cc77-builder / Agent（会话身份），操作ID `SP1-E-item19-build-R3`。基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。串行宿主草稿和4项参数检查、小样编译通过；原入口展开因夹具遗漏ArgParser日志配置而FAIL，已回收。FIR等价尚未执行。完整构建0次/0秒，3600秒预算未使用；未修改RTL、镜像、默认或上传。正式19/20。

下一步仅新身份修复小样参数初始化，集中核查变换后FIR/附属闭包；不绕过PrintModuleName/PrintControl风险。全部准入后才能一次3600秒/16GiB构建。保留原FAIL和HOST.lock。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-20261107/RESULT.md) · [评审](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-20261107/DESIGN_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-20261107/NEXT_STEP.md)。


### 记录109：第19项构建入口 R3-R1 真实序列化差异HOLD

2026-11-07T23:08:59.173824+08:00～2026-11-07T23:13:07.536751+08:00；@cc77-builder / Agent（会话身份）；操作ID `SP1-E-item19-build-R3-R1`，基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。小样改为原ArgParser初始化，编译及原SV/CHIRRTL生成全部返回0。4项参数检查通过；FIR内PrintModuleName输出不一致：稳定模块名变成JVM对象标识。失败即停；离线核5条注解/6个尾部文件一致，不覆盖FIR失败。

**正式19/20，完整构建0次/0秒，默认不变。** 保留所有旧FAIL，无重试、EMU/NEMU、EDA、生产RTL或镜像修改、默认切换、上传。下一轮R4设计独立工具导出香山变换后FIR与注解，先证闭包等价，全部准入才一次3600秒/16GiB构建。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-r1-20261107/RESULT.md) · [序列化归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-r1-20261107/SERIALIZATION_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r3-r1-20261107/NEXT_STEP.md)。


### 记录110：第19项构建入口R4，重复注解侧文件HOLD

2026-11-07T23:16:46.853219+08:00～2026-11-07T23:23:15.275955+08:00；@cc77-builder / Agent（会话身份）；操作ID `SP1-E-item19-build-R4`；基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。独立导出器编译、默认原入口与导出生成、JVM退出后的firtool均PASS；完整FIR、原RTL目录10件及6个尾部文件逐字节一致。输出集合多出722字节重复注解侧文件而FAIL，已停止，disable-all未执行。

正式19/20，3600秒完整构建0次/0秒，默认0f＋firstdot V2＋原C8不变。未运行EMU/NEMU、EDA，未改生产RTL/镜像，未上传。下一步R4-R1只收口隐式侧文件输出，保留FIR注解；复用已过证据并完成必要闭包/PrintControl验证，全部准入才一次3600秒/16GiB构建。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-20261107/RESULT.md) · [归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-20261107/SIDECAR_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-20261107/NEXT_STEP.md)。


### 记录111：第19项构建入口R4-R1，宿主通过／冻结HOLD

2026-11-07T23:41:20.567692+08:00～2026-11-07T23:48:47.309214+08:00；@cc77-builder / Agent（会话身份）；操作ID `SP1-E-item19-build-R4-R1`；基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。仅抑制重复注解侧文件后，默认/disable-all共10项闭包和6项构建适配器检查通过。24,596文件独立副本完成，原Make干跑exit0。冻结代码将带反斜杠续行的第一物理行送shlex而报错；失败即停，未补跑或完整构建。

正式19/20，完整构建0次/0秒，默认不变。生产RTL/镜像未改，无EMU/NEMU/EDA或上传。下一轮R4-R2仅修逻辑行提取并补完冻结，复用10+6证据及现成build-03副本，准入通过才一次3600秒/16GiB构建。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r1-20261107/RESULT.md) · [失败归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r1-20261107/FREEZE_FAILURE.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r1-20261107/NEXT_STEP.md)。


### 记录112：第19项R4-R2，生成通过／Git目录闭包导致后处理FAIL

2026-11-08T00:10:44.745504+08:00～2026-11-08T00:27:43.673220+08:00；@cc77-builder / Agent（会话身份），未提交，基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。复用10＋6项证据和24,596文件副本，新解析/冻结14项通过。唯一构建490.888秒、峰值RSS9.692GiB，JVM110.053秒与firtool378.512秒均PASS且串行退出；原Make因coupledL2/.git无效失败，未进入原生EMU编译。已停止，无残留。

只读确认文件复制遗漏629个Git目录，原127仓库可识别、副本仅3个。FIR/SV原始输出已冻结但Make后处理未完成，不可直接按mtime恢复构建。输入后检PASS，原FAIL与锁保留。正式19/20，默认0f＋firstdot V2＋原C8不变；本轮三项指标NOT_TESTED，历史实测保持。无EMU/NEMU、EDA、生产RTL/镜像变更或上传。下一轮仅修目录闭包并验证安全接续，使用新独立预算，不重复JVM/firtool。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r2-20261108/RESULT.md) · [归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r2-20261108/GIT_DIRECTORY_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r2-20261108/NEXT_STEP.md)。


### 记录113：第19项R4-R3，Git目录修复PASS／宿主LF模型FAIL

2026-11-08T00:33:44.803702+08:00～2026-11-08T00:41:16.151410+08:00；@cc77-builder / Agent（会话身份），未提交，基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。仅补629个Git空目录，127仓库可识别；原始1687件生成物物理快照并核对。独立接续Make保留原后处理，原配方与干跑两项PASS。小样Make退出0，但检查器将147处裸CR误作行界，多插294字节而FAIL。只读LF模型精确解释，不覆盖原失败，不修后重跑。

正式19/20、默认0f＋firstdot V2＋原C8不变。真实完整构建0次/0秒，未进入完整执行冻结。三项指标NOT_TESTED、历史实测保持；没有EMU/NEMU/EDA、生产RTL或镜像变更、切默认或上传。下一轮仅修LF模型、复用现有输出补负控并完整冻结；全部通过再新独立3600秒/16GiB剩余构建，不重复JVM/firtool。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-20261108/RESULT.md) · [归因](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-20261108/LF_SEMANTICS_ANALYSIS.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-20261108/NEXT_STEP.md)。


### 记录114：第19项R4-R3-R1，新观察EMU构建PASS

2026-11-08T01:06:22.126707+08:00～2026-11-08T01:26:24.784778+08:00；@cc77-builder / Agent（会话身份），未提交，基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。仅修检查器LF语义，15项宿主、8项完整冻结PASS。一次接续构建851.429秒，峰值7.480949GiB；原Make后处理1608SV及79其他文件精确核查PASS，Verilator/C++/链接退出0。JVM/firtool未重跑；EMU为71,379,320字节，SHA `fc25f9e2a22cc1c51e4a4884c03c6d84e950fcbb1925eb55a448de104273f742`。后检输入/旧证据保持、无残留。UTC时间戳差807.711738秒，原差异保留，未授UTC一致性审计资格。

正式仍19/20，构建阻塞解除，诊断准入待做；默认0f＋firstdot V2＋原C8保持。没有EMU/NEMU运行、EDA、生产RTL/镜像变化、切换或上传；新加速比/面积/时序NOT_TESTED。下一轮可集中做两角色诊断准入，依据充分且新授权后300/900秒运行；诊断未命中保留，不冒充第19项PASS，不自动M2或重放。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-r1-20261108/RESULT.md) · [固定EMU](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-r1-20261108/FROZEN_EMU.json) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-build-r4-r3-r1-20261108/NEXT_STEP.md)。


### 记录115：第19项两角色诊断准入HOLD，目标0次

2026-11-08T01:37:40.592213+08:00～2026-11-08T01:46:37.061546+08:00；@cc77-builder / Agent（会话身份），未提交，基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。新EMU、原M1/参考库与8个动态依赖身份核对，编译后6/6/4/4/1观察点与设计一致。目标时长增量依据不足，旧保守新侧带界对整批40万guest为2311201080字节，不能证明2GiB够用（不是实际超限）。格式细化脚本把NX参数类型当显示进制而断言FAIL，留档未重跑；流式适配/新正负控/执行冻结尚未完成。

记录114构建PASS保持，正式19/20、默认0f＋firstdot V2＋原C8不变。目标0次、预算0秒，新三项指标NOT_TESTED；无RTL/镜像/构建/EDA/上传变化。下一批集中修格式分析、完成完整日志界/流式检查器/宿主成本；没有目标开销依据HOLD并提出独立校准合同，不用正式两角色偷偷试跑。

[结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-20261108/RESULT.md) · [预算](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-20261108/BUDGET_REVIEW.md) · [下一轮](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-20261108/NEXT_STEP.md)。


### 记录116：观察EMU完整诊断与有效字段中性通过，继续M2

2026-11-08T02:13:17.235181+08:00；@cc77-builder / Agent（会话身份）；基点347b1ae7，未提交。

诊断完成，原批次STOPPED保留，完整真实日志离线修复比较口径后PASS。正式仍19/20，S0/S1未命中；默认0f＋firstdot V2＋原C8不变。

- 14项宿主测试、10万流式事务、425冻结输入。bit100 24.981秒/11653 guest，完整拒错通过。
- M1正常 574.819秒/267282 guest；完整41调用、84 UART、77 custom、DiffTest PASS。725条侧带事务完整身份/排空，52903条实际微操作记录。
- 两角色累计599.800秒、原始日志14663801字节，原CPU4/4线程/12GiB/2GiB与300/900秒上限保持；无残留。
- 原比较误把整段输入日志SHA当语义摘要，触发FAIL；真实差异仅无效P的prob/ppdest和无效R的rrob/rpdest。新离线比较保留全部有效字段/控制/周期，2200条逐项相等；5项定向正负控通过。宿主夹具两次误引用本镜像不存在的T13流也保留，最终使用实际SP1提交字段；CSR依据为实际C判断器，不伪称存在T13采样。原批次JSON、冻结源码及原FAIL均未改写。
- 完整40个A调用时序：36次S1末次F2v写回比A响应早8拍，S0四相位早9/11/17/18拍。此前无反压有了可定位原因。

下一步自主实施M2定点软件补测：F2v源增加fmul+fsgnj依赖链，vdot输入、零加、分支、原四相位、41调用和原S0/S1合同不变。先构建与宿主审计，再新身份有界执行。没有新RTL/核构建/EDA/默认切换/上传。新加速比、面积、时序NOT_TESTED；历史三项指标见METRICS。

[结果](team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-r1-20261108/RESULT.md) · [时序表](team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-r1-20261108/review/TIMELINE.json) · [接续](team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-observer-diagnostic-r1-20261108/NEXT_STEP.md)


## 2026-11-08 记录117：M2未命中，保留19/20

结论：NOT_HIT，19/20。bit100、41次功能调用、77次custom、完整128位与CSR/ABI、NEMU差分通过；P入队和真实父级反压均未命中，不计为第19项通过。

两个进程合计605.237秒，正常267234 guest cycles/579.294秒，均在预算内。完整时序：S1全部36次F2v结束早于A响应5拍；S0原四相位差4/7/9/15拍。M2确实后移压力，但不足以重叠，原FAIL和锁保留。

下一步仅在scratch ft3链再加两条依赖FMUL；数据、分支、原相位与完整覆盖不变。此前考虑一条，完整S1证据显示不足，故选择两条；不扫描相位。

本轮未测性能、面积、时序，均NOT_TESTED。历史SP1 chain加速比3.397658×（0f 2.929725×）；FU面积18322.878 μm²、父级285241.642 μm²；标称Q分别1.790381/3.337809 ns（Q=T−slack，不是全核Fmax）。未切默认，未上传。

证据：`team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-m2-fp-pressure-20261108/RESULT.json`。


## 2026-11-08 记录118：M3 完整未命中

NOT_HIT，19/20。bit100与完整41调用、77custom、全128位、CSR/ABI、NEMU差分通过，正常267397 guest/580.931秒。两个目标累计606.085秒；未重试、未加时。

40个A中39个在F2v末写后3拍响应，另一项5拍；P/反压仍0。FEX0与VFEX4共享写口且OG0也仲裁，VFEX3与VFEX4共享读口，不能将压力延迟视为独立旋钮。完整时序及源码支持一次M4：多一条依赖FMUL把F2v首写后移约4拍，使A/B有机会先经过OG0/OG2。保留旧FAIL、原相位和覆盖。

M3最初PC清单仍引用M2的宿主准入已撤销（零目标），runtime-r1绑定新manifest并通过负控后才启动。三个指标本轮NOT_TESTED；历史chain3.397658×、FU18322.878 μm²/标称Q1.790381ns、父级285241.642 μm²/Q3.337809ns均未重测。默认0f未切换，未上传。

证据：`team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-m3-runtime-r1-20261108/RESULT.json`。


## 2026-11-08 记录119：M4 全核命中 S0/S1，重放待完成

结论：GO 进入最终重放；仍为19/20，尚未把校准等同最终验收。bit100拒错25.346秒/11668guest通过；正常586.634秒/267845guest通过；目标总611.980秒。

|覆盖|真实证据|
|---|---|
|S0|phase0，R=A seq1，B seq2在17988进入P，17989双槽占用；双方完整响应/提交|
|S1|phase4第九次指定probe，R=A seq76/ROB1:30，B seq77/ROB1:36在262616进入P；262617来自ROB1:35的取消杀P保R；A在262624响应；B无响应/提交|
|完整检查|41调用、77提交、78接受，完整128位及实际C端CSR/ABI检查、NEMU差分；725侧带响应闭合|
|累计事件|ENQUEUE_P34、STALL296、KILL_P1、PARTIAL_KILL1|

M1/M2/M3原未命中记录保留。M4仅软件scratch依赖链，无RTL/EMU重构或默认切换。

本轮加速比、面积、时序均NOT_TESTED；历史SP1chain3.397658×（0f2.929725×）；FU18322.878 μm²、Q1.790381ns；父级285241.642 μm²、Q3.337809ns。Q为T−slack，非全核时钟。

下一步集中完成原SP1功能EMU观察中性、补测同核精确重放、0f补测数值对照及原o2-control双核重放。保留原覆盖、每角色预算和失败即停；不切默认、不上传。

证据：`team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-m4-fp-pressure-20261108/RESULT.json`。


## 2026-11-08 记录120：SP1最后第19项通过，20/20，可供选用

@cc77-builder / Agent；操作ID `SP1-E-ITEM19-FINAL-ACCEPTANCE-20261108`；执行UTC 2026-11-07T18:56:10.037564+00:00～2026-11-07T20:11:47.361417+00:00，留档北京时间2026-11-08T04:12:06.210904+08:00；基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，未提交。

五角色全部通过：原SP1补测与观察中性、同核重放、0f补测对照、原控制镜像SP1/0f重放。S0真实双槽和S1杀P保R在原功能EMU命中并精确复现；原16组/256试验/1208提交/131072字节覆盖保留。目标4550.961秒，宿主22.148秒，外层4573.154秒，预算及清理通过。

原失败/未命中和旧预算HOLD保留，本轮新性能/面积/STA均NOT_TESTED。建议采用原SP1，最终默认选型由用户决定；没有切默认或上传。主目录历史P4-R1不等于候选，采用入口为独立原SP1源码与release-candidate。

[完整结果](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/RESULT.md) · [20项矩阵](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/MATRIX.md) · [候选包](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/release-candidate/README.md) · [三项指标](../../team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/METRICS.md)。

路线接续：第19项验证关闭，不重复探针；用户选择后再集成默认入口和发布。


### 记录120时间口径补充

首角色UTC起止差比单调时钟elapsed少35.33771秒，实际调钟原因未独立确定，**不授予UTC时间连续一致资格**。其余四角色差约0.023～0.047秒。原始时间戳、回执、外层监督记录均保留。冻结合同与运行器使用`time.monotonic()`及外部截止监督：目标累计4550.961秒、宿主22.148秒、外层4573.154秒，均满足原预算；该UTC差异不改写guest周期、功能结果或精确重放结论。

见配套`CLOCK_RECONCILIATION.json`；这是时间记录差异说明，不把旧clean-02或历史UTC问题追溯改成PASS。
