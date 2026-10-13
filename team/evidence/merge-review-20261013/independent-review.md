# 固定候选 C 的独立代码复核

2026-10-13，复核者：本次本机 Codex（非原 ChatGPT 合并执行者）。复核对象为 `45bea984445e6f07d0d9c0ee8e42302e225ba0b3`，尚不代替团队真人接收或核心接口签字。

## 1. 范围与结论

逐项阅读生产 RTL、基类、FuConfig/FuType、RobPtr、平坦测试适配器和 C++ scoreboard，未发现本次合并引入的生产实现错误。下表是源码审查结论，动态复跑结果另见本次新日志；不以历史测试替代新运行。

## 2. 实现检查

| 检查点 | 实现依据与判断 | 边界 |
| --- | --- | --- |
| 算术位宽 | `VDotDatapath.scala` 每 lane 对低 64 位切 8 个 signed8，乘积 signed16，`+&` 树逐级 17/18/19 位；signed32 扩展后拼接高 96 位零，覆盖 -130048 至 131072 | 没有饱和、舍入或 128 位整体符号扩展 |
| 接受/响应 | `VDot.scala` 的 IDLE/MUL/REDUCE/RESP 状态只在 IDLE、无 flush、无 reset 时 ready；RESP valid 与 ready 无关。E0 接受、E1 乘积、E2 沿后 valid、E3 最早响应握手、E4 再接受 | 单请求 FU，最小 II=4；不是流水 II=1 或 CPU 延迟 |
| 身份快照 | `FuncUnit.scala:connectNonPipedCtrlSingal` 用同一 `in.fire` 的 RegEnable 保存 ROB/pdest/vpu/perf；输入寄存器与 illegalReg 在同一握手保存。`VecNonPipedFuncUnit` 的 outCtrl 在没有新 fire 时保持 | 忙时改变输入不应改变已接收事务 |
| 反压稳定 | RESP 无握手不改 state/result；无 in.fire 不改身份。heldResponse 对整份输出比较，matching kill/reset 时允许撤回 | 不要求 valid=0 时未初始化数据寄存器有定义 |
| 非法配置 | VL 来自第五源的 `srcVConfig.vl`，其他配置由 `ctrl.vpu` 取；非法结果为零，只置 illegalInstr，关闭 vecWen/v0Wen，仍响应一次并保留身份 | VS Off、完整译码、特权和架构可达状态由后续集成负责 |
| flush | 保存的 ROB 调 `RobPtr.needFlush`，检查 valid、isAfter 和 self；killed 优先于状态推进且当拍屏蔽 out.valid。因此 out.ready 不能让被取消响应写回；较老或同龄非 self 保留 | ROB 相对年龄须在有效窗口内；测试用独立 96 槽距离模型而非拷贝 RTL isAfter |
| reset | reset 当拍关闭 ready/valid，RegInit 将状态清空；旧数据寄存器虽不清零，不能生成无主响应。stall 标志复位为 false | 不包含全核复位时序签核 |
| FU 声明 | `VDotCfg` 五源、非流水、不定延迟、128 位结果、vector/V0 目的及 illegalInstr；FuType 追加而不重排旧枚举，needVecCtrl/isVecArith 含 vdot | 尚未加入 VFEX4/译码；不能由 allConfigs 注册推断全核已接入 |
| 测试独立性 | C++ 以接受时间+3、单 pending 和环形距离判断时序/取消；算术期望来自已校验固定 JSONL，不重算 DUT 同构加法树；匹配完整 128 位及身份 | 故障注入改读回结果，只证明比较器敏感性，非 RTL 故障覆盖率 |
| 事务守恒 | 每周期维护 accepted/responded/killed/reset_dropped/pending；驱动前后分别核对 ready、valid 和账目，drain 有 watchdog；主循环检查 II=4+stalls | 有限随机种子与定向测试，不是形式化穷尽证明 |

## 3. 合并与测试脚本审查

独立 Git 对象审计检查 M 第一父 Z、第二父 S、C 第一父 M、祖先关系、两侧独有路径 blob/模式、10 个 gitlink、版本锁。README 按双方相对 BASE 的新增行检查；基线的“尚未实现 vdot”被 S 正常替换，不能要求过时基线句子仍逐字存在。Windows Git 重新计算自动合并树为 `17bb1dd1adf572c15625df7ea931b5575051f081`，与 M 一致。

FU 16 项摘要与 C 对应；组合 9 项与原提交对应，当前仅 build.sc 因源侧新增 vdotFu 目标变化。C 相对 M 仅四个入口/报告文件，生产、模型及历史证据完整保留。

两个原始 RTL 脚本要求真实 elaboration、Verilator 重建、完整数据数量和预期失败检查。FU 使用 `--assert`，非法 VLEN 必须包含指定 require 原因；负控必须返回 1 并命中失败文字。检查器未修改，未修改黄金数据或测试数。

## 4. 后续集成风险

需要在单独工作包验证 custom-0 译码、单 uop、重命名/v0 物理路径、VL 依赖、VFEX4 busy/时钟门控、OG2 重试、写回仲裁、ROB 精确异常和 CSR 副作用；随后 NEMU、hello/vadd 回归、全核 DiffTest、周期性能与 PPA。共享分支的成员暂停写入/未发布工作/运行中任务和真实 ACK 尚未得到证明，代码审查不构成发布窗口。
