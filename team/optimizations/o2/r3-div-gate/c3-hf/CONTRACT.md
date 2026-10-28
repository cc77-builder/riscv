# C3-HF 单次最小候选合同

冻结于2026-10-25，用户授权一次最小范围试验；修改RTL前已说明。本轮不写GitHub，不修改保留生产基线及旧失败证据。

## 身份与唯一生产范围
基线0f12df675378556670afd0dd2153f47fcb330610，独立候选只修改 src/main/scala/xiangshan/backend/exu/ExeUnit.scala。保留O2双hold、busy/ROB、真实分派/接收/输出、整数、VDot算术、取消释放、所有原ICG表达式、legacy/O1。
仅FP DIV/SQRT hold SET由真实fire换为 P_F=inputValid&&selectedFP&&!divBusy&&!divOutValid&&!VDotOccupied&&!flush&&!reset，原uncerLat适用条件/接受优先级/RegInit不变。前向只读Wire不增加状态。
概念依据见../c3-g0/RESULT.md；有效初始化域 P_F=actualFpFire，域外反例保留。共享异步与已有效bootstrap的同步夹具区分。

## 局部验证
源码/依赖固定、候选提交及完整补丁留档；源绑定控制抽象/生成结构检查及测试顶层只读P=fire/保持状态检查。原FU完整128位10022向量、身份/异常/反压/取消及4负控；真实父级原13组及16负控；沿用C2补充115场景/SQRT/双lane偏斜/TE0动态复位/54取消窗与7离线负控，标注旧suite名不代表新候选名。
旧C2 PASS不能转授；本轮真实输出独立。仅测试夹具允许添加诊断，不得将assert/观察反馈为生产控制。记录reset/bootstrap限制；观察错绑/遗漏、负控接受或关键日志缺失拒绝。

## 同约束筛选
局部资格及独立审查通过后，只做这一版父级综合、五档STA及两边同条件控制查询。复用固定O4生产接口、工具/库/端口/约束；baseline原封存身份逐项核实，未知/缺失不能记0。
五档：(1ns,5fF)、(0.5ns,5fF)、(2ns,5fF)、(1ns,1fF)、(1ns,20fF)。
45项各自arrival<=0f同档101%：r2r/i2r/vdot_r2r/vdot_i2r/vdot_r2o/ready和FP/INT/VDot三ICG.E；基线正slack的ICG须非负。
before/after均绑定FP hold、INT hold、divBusy共3状态，均须映射到不同DFF的D；不查询owner，不要求双hold消失。nominal全部控制D最差<=1.737526ns，baseline须重现1.930584ns。父级面积<=284899.560946参考库单位，3ICG、未知单元0。保存全部路径、起止点、slack及失败。
这不是官方门槛，也不等于绝对1ns/整核Fmax/功耗收敛。

## 停止与后续
不实施第二候选或自动扩大为gate+hold；不能放宽阈值、false path或挑选映射重跑。
功能或冻结成本门禁实质失败：归档否决，保持0f，关闭本轮门控试验。测试/脚本基础设施故障保存原失败、修复依据与新输出，不冒充候选通过或重做第二候选。
全过才可进入新全核/NEMU与同镜像周期，不以旧EMU替代新验证；采用仍须完整证据。每个新层级数据独立追加版本档案，旧20条保留。
