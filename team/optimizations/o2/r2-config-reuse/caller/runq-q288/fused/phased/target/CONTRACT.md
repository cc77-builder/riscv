# Q288 phased 独立目标合同 v1

合同：`r2-s3-runq-q288-phased-target-v1`。本合同在运行前冻结，只验证既有 phased 排程是否改善固定合成、预打包 288×288 / GS=32 完整 Q。依据见 [已封存周期诊断](../../target/COST.md)。不修改旧合同、权威代码、RTL、参考或 R5 默认；旧 fused/acc8 已闭合批次不重跑。

## 1. 一次候选与同 ELF 比较

三行固定为 FV=`q288_fused_vdot`、PV=`q288_phased_vdot`、FR=`q288_fused_rvv4`，id=0/1/2，context leaf algorithm=0/0/5。FR 是此前具名对照集合中较快的 RVV；本合同不重新覆盖全部现存 RVV。PV producer/checker/旧合同分别固定 SHA `2b487c60…2399`、`8537f850…fd9`、`142f536d…fd2`；实现保存完整 SHA。

新 ELF 只加入这一版现有 PV，原 FV/FR、六个既有整数叶、acc8 包装和共同计时器的完整函数字节不变。实际新 ELF/BIN、函数地址、数组指针、编译命令与工具链分别绑定；旧镜像周期不能迁移为本次观测。未参与三路调用的旧 acc8 包装以显式链接根 `--undefined=q288_full` 保留，仅供完整字节核验，保持普通链接 GC，不增加动态调用。共同 prepare/judge/五项破坏检查保留原源逻辑，三路使用同一输出布局、poison、guard 和 CSR 状态。

PV 直接复用原独立机器字证书及 **131 条** core 检查，不调用旧 140 条 `check_full` 判据。它保留每行 g0→g8 的两乘一加、完整 288 输出位、末组八个 128 位槽、精确读写足迹、整数/FP ABI 和 CSR；core 字节固定 `ada26193770cfcbf3de5871722055721ad3cbcee4875ef4f61ef7c4b4a37c74f`。模型检查绑定新 ELF 的真实地址、context 与返回点。

## 2. 固定调用计划与计数

功能顺序：FV/PV/FR 各 x1，随后 FV/PV/FR 各 x2，共六次；第一个数据集为 x1，确保 context 指针破坏控制不是空操作。

计时顺序：**FR,FV,PV,FR | FR,PV,FV,FR**。每个计时窗之前恰好做一次同方法、完整 Q 的 x0 selfwarm；warm 与 timed 前分别执行相同 prepare。所有四个 FR 点均为有效观测和锚点，全部进入性能分母。计时使用原四 CSR 围栏和实际机器路径，不以 marker 外围跨度替代 cycle CSR。

| 每个正常进程 | 固定数量 |
| --- | ---: |
| 完整 Q（功能 / warm / timed） | 22（6 / 8 / 8） |
| FV / PV / FR 完整 Q | 6 / 6 / 10 |
| 完整 Q 输出位检查 | 6,336 |
| 动态整数 core / 每 Q | 7,128 / 324 |
| 独立整数叶调用 | 0 |
| 全阶段 custom COMMIT，含 probe | 124,417 |
| 计时 custom | 41,472 |
| CSR_SAMPLE / COUNTER_ENQUEUE | 各 32 |
| FP 元素 convert / mul / add | 57,024 / 114,048 / 57,024 |

这些数量分别适用于 recovery 与 replay，**不适用于预期在 probe 处退出的 negative**。兼容旧字段 `functional_calls=22` 指全部 Q；新增 `explicit_functional_calls=6` 明确实际功能次数。`inline_calls=22` 包含 FV、PV、FR，不表示仅旧 fused 符号或仅计时调用。

## 3. 运行前和真实目标门禁

构建输出放在检出外，保存全部源闭包及 SHA、实际 GNU 命令、返回码、ELF/BIN 对应、原权威 object 字节。再生成源必须完全相同。所有三路 × x0/x1/x2 的实际 PC/word/数值路径闭合；数组/调用表/数据集、三路 FP 舍入顺序及 PV 错误 X/W/归约源的实际 ELF 破坏必须被相应检查拒绝。selector 反证覆盖快 end-anchor、context 失稳、仅胜 FR 不胜 FV、均值掩盖慢点。

固定既有 T17 EMU/NEMU/flash/AM、seed 和单核配置。依次独立进程执行原 vd0 bit100 probe 负控、正常恢复、正常重放；probe PC 从本次 ELF 解析，不能用旧地址。正常运行须完整 Good Trap、UART/call plan、T13 四 CSR 和新路径、O2 两槽协议、全部 custom PC/身份及计数闭合。重放只验证可复现性，不增加性能样本。

每个进程保留既有 12M DUT cycles / 7200s 上限，任何失败保留原始命令/日志/退出状态，禁止追调候选到通过。只运行单个 EMU，宿主所有构建/验证总预算≤4核；性能运行避开同机重型任务。冻结前、运行后与封存复算均核对完整来源，不修改已有98份冻结源。

## 4. 预定判断（整数门槛）

先要求 `100*max(FR四点) <= 101*min(FR四点)`，否则 `HOLD_CONTEXT_VARIATION`，无晋升结论。

PV 晋升同时要求：
- `200*max(PV两点) <= 199*min(FV两点)`；
- `200*max(PV两点) <= 199*min(FR四点)`。

以上全体最坏对最好门槛已蕴含块内门槛；仍报告两块原值。若 PV 不胜 FV，则保留原入口；只胜 FV 不胜 FR，则记录软件局部结论但不晋升 PV。原 FV 是否在本次新 ELF 中优于 FR 也按相同 0.5% 门槛独立判断，R5 默认始终不变。任何均值排名都不能覆盖不合格观察或排除较快 FR。

## 5. 结论与封存边界

封存继续复用原始 raw-audit、依赖守卫与原结果逐字段相等判据。新 archive 只将原 helper 唯一的 180 秒隔离 Python 调用适配为 900 秒，并复用固定 SHA `0fa2f707…9d91` 的既有 `host_audit.py:durable_child`；此文件加入补充审计器集合并随归档新源复制。适配要求准确的新 child 脚本、完整来源/审计器 SHA、固定 Python/guard、原 action 和全部八个禁止根目录，其他 subprocess 调用原样转发。进程命令、标准输出/错误、退出/超时、退出时 guard/audit 诊断在临时目录销毁前持久保存。宿主预算不改变 guest 周期上限、运行门禁或性能验收。

只有 negative/recovery/replay、完整原文逐成员封存及隔离新源复算通过，才能给本合同自己的目标结论。保留所有失败/原始证据，旧结果和回退不变。获胜最多证明整体 phased 排程在此新固定计划中的净收益，不能把收益全部归给 vset、FU 局部包络或少指令。

不计 pack、量化、token、完整模型、模型质量或 ASIC PPA；不把固定合成 x0 数据扩展为通用应用结论。若不通过预定性能门槛，本合同停止该候选，不为寻求通过而追加观测或事后调整验收。依据用户本轮补充要求，后续继续深化其他技术假设的研究；不同路线必须另行定义来源、实验条件与验证合同，不将本批结论转移到新候选。
