# SP1-E B0：六用例共享宿主入口与准入结果

GO：batch/stream六例共享宿主入口、差异正负控、实际执行冻结和有界预算准入完成；batch三例可在下一轮明确授权后整批执行。本轮没有EMU/NEMU或新性能资格，完整SP1-E仍9/20已验，默认0f＋firstdot V2＋原C8不变。

| 用例 | 正常角色窗口 | custom | 宿主准入 | 当前SP1目标结果 |
|---|---:|---:|---|---|
| batch-d0 | 12 | 768 | GO，有界尝试 | NOT_TESTED |
| batch-d1 | 12 | 768 | GO，有界尝试 | NOT_TESTED |
| batch-d2 | 12 | 768 | GO，有界尝试 | NOT_TESTED |
| stream-d0 | 12 | 384 | GO，有界尝试 | NOT_TESTED |
| stream-d1 | 12 | 384 | GO，有界尝试 | NOT_TESTED |
| stream-d2 | 12 | 384 | GO，有界尝试 | NOT_TESTED |

一份共享runtime、六份不可变描述符/合同/annex/freeze，旧冻结目录与公共common/supervisor字节保持。batch保留四个custom位置和vd10～13；stream保留递增地址、三条退休融合与专用bit100。新增逐已提交指令的源操作数及完整128位manifest顺序检查，比较两侧均独立匹配完整12窗，不以平均值相等掩盖漏窗。

宿主证据：420项逐例日志/负控，204项独立收据检查，12项共享派发测试，9项逐角色失败/外层截止测试，4项授权接口测试含39项子检查，以及六份实际冻结的138项正负控。计数口径各异，不相加包装成覆盖率。历史G0退休分组及未变资源监督器按源码身份复用。所有模拟PID、授权和目标回调明确标为宿主夹具，未冒充新目标结果。

最终freeze/verify单次约1.882～2.039秒；预算H还取预期完整并集核验3.350117秒，保守宿主工作投影554.529秒≤原900秒预留。每例6300/7200秒、三例18900/21600秒、CPU4/整组4线程/RSS12GiB/日志2GiB均保持；这是有界运行准入依据，不是未来完成时间保证。

两项宿主开发问题留档：授权负控夹具字典别名导致首轮两项负控未拒绝，修正夹具后通过；预算报告生成的一次引号语法错误已修正。另收紧实际收据到固定target-01/NN-role，旧420项功能函数AST未变，修订后的204项收据测试通过。没有目标重试、历史FAIL删除或门槛降低。

当前完整验收仍9/20；六例仅从“宿主待准备”推进为“可有界执行”。o2-control/C48/新timed DIV预算HOLD及其他保护缺项按原计划保留。下一轮只执行batch三例，不自动进入stream或默认切换。

[下一轮指令](NEXT_STEP.md) · [逐例准入JSON](CASE_ADMISSIONS.json) · [冻结与负控](independent-review/freeze-attempt01/RESULT.json) · [预算闭合](independent-review/BUDGET_CLOSURE.json) · [既有三项指标](METRICS_REUSED.md)
