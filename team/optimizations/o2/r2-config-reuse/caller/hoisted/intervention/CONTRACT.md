# R2-S3：单镜像前序干预 v1

操作：`20261026-LiZufan001-context-intervention-0000`。基点：`537cc2ea28e98ede1e72c1d2d7767613de9f6356`。
本合同在首次构建和运行前固定；不改写旧 hoisted/split/fixed-weight 合同或 HOLD。

## 问题与干预

既有 `../CONTEXT_RESULT.md` 观察到旧 h0/h1 的相同 vdot 目标在共同间接调用附近具有不同的退休前沿和连续 redirect 关联。
本实验只回答：在一个 ELF 中保持目标、地址、数据和恢复路径相同，仅切换两种前序 RVV，能否在预定顺序中重现该关联？
不比较最快内核，不选择生产默认，不把坐标差解释成预测器执行延迟。

前序 A 为 `r4_gemv_8x32_basic_rvv`，B 为 `r4_gemv_8x32_reuse_rvv`。
目标始终为 `config_reuse_gemv_8x32_reuse_vdot`；三者机器码必须与既有合格完整对象相同。
复用原 hoisted `caller_full` 和四个既有 timer 的原文（实际仅调用 full timer）。
双方通过同一个 `caller_full` 间接调用点，固定 8×32、dataset0、同一 A/x/context/workspace/y/measurement 地址。

每试次执行：统一初始化 → 前序 full 计时 → 完整输出检查并保存判定/计数器 → 同路径初始化 → 目标 full 计时 → 同样检查并保存判定/计数器。
初始化恢复完整 A/x、输出槽、workspace、边界 guard，以及 `vl=8/vtype=0/vstart=0/vcsr=7`。
对外 UART 全部在40个窗口结束及判定负控之后输出。窗口内保存完整调用，包括打包、leaf、提取和 ABI 开销。
前序窗口也记录独立 ELF 路径、counter 和退休，前序周期不作为选型指标。

## 固定计划、预算及验证

- 单个 BIN；前置4试次 `ABBA`（全部留证，不进入正式分组）。
- 正式16试次 `ABBA BAAB ABBA BAAB`，每臂8个；共20试次、40窗、640条实际退休 vdot。
- 每窗使用相同全宽输出、输入不变、guards、CSR 检查。结束后执行原六项判定故障控制，恢复后再检查正常状态；无额外 vdot。
- 运行时表项选择前序，目标固定；GNU验证绑定真实 ELF 中20个表项、两个前序指针、唯一目标指针及三条独立动态路径。
- 新合同使用团队既有构建/串行运行器；只在独立 Python 进程适配生成计划和 normal 审计，旧检查器/官方参考程序文件不修改。
- 正常审计覆盖全部40窗和20个目标：原 counter/ROB/PC/word/fence 检查、完整 O2 协议、DiffTest/GOOD TRAP、640提交、全宽结果与六控制；不能使用旧36窗 normal 的 PASS。
- 最多三次串行 EMU：首个 vdot 的真实 bit100 故障拒绝 → 同 BIN 正常恢复 → 独立进程重放。正常两次全部窗口、退休前沿与事务关联必须完全一致；重放不算额外独立样本。
- 每次最多3,000,000拍、7200秒。总CPU≤4，测量时无其他重构建/EDA/EMU。正常失败则停止性能解释，保存原失败；不通过扩拍或增样本追求期望结果。
- 先完成 GNU/独立路径与针对性证据拒错检查，再运行。使用固定 T17 identity-02 的 EMU、AM、正常参考和 flash；输入前后核验，不重建RTL，不修改官方源码/判定。

## 预先规定的分析与终点

列出每个试次的目标完整周期/指令、调用→leaf首条退休间隙、连续 origin 数与状态、origin→leaf间距、首ACCEPT坐标、32事务响应时延。保存完整原始日志及前沿哈希、里程碑和逐事务关联，审计时从实际 ELF 与日志重建全部退休前沿；不重复存放可重建的大数组。
使用既有 `context_prefix.py` 的保守完整 ROB 连续性检查：marker内同指针、下一拍parent配对、无中途退休/杀死、同拍禁止退休与redirect。
标量 origin 有效性仍依赖固定 RTL 语义；不声称日志直接观测了分配代号、预测/实际目标、redirect原因或取指恢复。

正式16试次分为四个原定4试次块，逐块报告 A/B 的连续 origin 数、call→leaf间隙和完整周期和；同时列出全部原值。
仅当四块都满足 A 的唯一连续 origin 数多于 B，且 A 的 call→leaf 间隙和大于 B，才标记 `REPRODUCED_PREDECESSOR_ASSOCIATION`。
若只满足一部分则为 `MIXED_PREDECESSOR_ASSOCIATION`；两项都没有在任何块出现则为 `NOT_REPRODUCED_IN_THIS_PLAN`。
出现多个仍连续的origin则标为 `INCONCLUSIVE_AMBIGUOUS_ORIGIN`，不能强制归到有/无组。
完整周期和仅描述，不另设采用门槛，不因方向相反或结果不佳追加样本。

无论结果如何均在本计划收束。前序处理还会改变指令历史、执行时长、缓存、物理映射等状态，交错顺序不能复位这些状态；重现最多支持本干预方案足以改变后续观察，不能归因到某个预测器或某条指令。
不重现不表示所有前序效应不存在。旧 `HOLD_CONTEXT_VARIATION`、R5、split资格、完整应用与ASIC PPA边界保持。

## 复现入口

从包含本模块的仓库根运行 `python3 -B <本目录>/intervention.py --repo "$PWD" --action build --output <新原生build>`，
然后使用同一入口的 `run --build <build> --output <新run> --operation-id <本轮ID>`。
默认身份文件是仓库中固定 T17 `identity-02.json`；实际依赖位置来自该文件。
`audit --build <build> --run <run> --output <新JSON>` 只做原文离线复算，不访问物理EMU或启动仿真。
`checks` 覆盖预定判定方向、真实 ELF 表项与重哈希错误表项，并可对完整原文执行 UART/回执/负控观察拒错控制。
`pack` 与 `audit-archive` 复用原证据封存/解包器；归档复算仍需包含本模块及既有合格对象的完整固定仓库检出，源码快照用于身份核对，不冒称仅凭 ZIP 即可独立构建。
失败输出保持，不覆盖或自动重放未知副作用。
