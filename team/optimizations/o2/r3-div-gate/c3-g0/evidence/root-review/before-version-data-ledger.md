# 香山 vdot 各版本运行数据档案

更新：2026-10-25（UTC+08:00）。本文件保存版本身份、测量口径、实测数据和采用依据；后续每版继续追加。原始实验合同和封存证据是最终依据。它不维护待办顺序；当前开发安排仍看 [开发路线](development-route-current.md)，执行过程仍记 [开发计分板](../../开发计分板.md)。

历史部分只读取已有成果，未重跑旧版本或补授资格。当前保留的生产实现是 **O2＋H1＋DIV 取消关钟修复 0f12df6**。C1 已否决；C2 先完成局部验证，随后新增的 [C2 成本筛选](../optimizations/o2/r3-div-gate/c2/cost/RESULT.md)有 25/45 项超限，亦不采用，全核与周期保持 NOT_TESTED。旧 C2-local 章节和表行保留其当时未测状态；新增数据单列第 9 节。

配套机器可读索引：[version-data-ledger.json](version-data-ledger.json)。索引含完整硬件/EMU 身份、19 条实验记录、原表文本、指定原 CSV/JSON 和输入 SHA-256。只列出历史执行实际支持的结果；未执行的层级写 NOT_TESTED，而不是 0。

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
