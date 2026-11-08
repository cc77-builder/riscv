# Booth3成本续接：控制器有限静态审查

## 结论与版本

**最新版未发现会导致错误成功或控制器层面无界等待的具体阻塞。** 初稿最终result写盘期间的pending信号缺少复查，主端已最小修复；本报告以修正版为准，不再将该问题列为未解决。没有运行EDA/控制器、访问Windows/WSL或修改候选源。

- cost_resume.py：21,597 B / SHA256 `317f1919138e0c2e69c9d48514667fe82a871a0ec4caf8d6cc5fb206390f594a`。
- CONTRACT.md：4,319 B / `fc6267cc664d900c143e21017f96b6adcab401c03aae642e00032a9a291fcfe0`。
- FIXED_INPUTS.json：2,878 B / `6766593ac8cf131c2326ac40f5236ec8c16968d4178eb5e27dedfbe51716bcde`。

## 预算与进程回收

300秒总截止从main预检入口起算，没有在EDA开始后重置。每次命令的until在Popen前固定且不超过总截止；轮询检查信号、总时限和单命令时限，退出后再次要求rc0并未超过until。serialize/reparse/STA各30秒、唯一f1映射60秒均受同一总截止约束。

子进程均start_new_session，发生超时/信号/错误时finally仍检查并清理整个组，记录exit/reaped/group_absent。实际核对同SHA的process_helper.py：`db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3`，TERM后最多轮询10秒，再KILL并`wait(timeout=10)`；不是无界wait。未回收或组仍存在会阻止整体成功，不能仅凭某条工具rc0通过。

最终原输入及产物扫描、artifact清单写盘后核总截止；最终result写盘及恢复处理器后再核deadline或已锁存pending信号，任一触发均改FAILED/local_cost_recorded=false并拒绝正常成功返回。300秒是成功预算，必要失败回收/保存可以晚于截止；外层360秒和实际cleanup仍由主端启动回执说明。

## 输入冻结与执行顺序

15条固定输入包含原FAILED02、f0真实mapped.json/Verilog/模板、旧inputs/overlay类清单、原算术及日志、固定比较器和基线/helper。控制器复核这些字节，并继承旧originals/snapshots、全部overlay类、四套生成SV及资源清单、新R证明日志、实际FU二进制、同库工具和约束身份。对重复pin不允许不同SHA，最终任何输入变化或不可读均记录并置FAILED。

原result必须仍为FAILED；新P/R证明和两态FU已完成但整体资格仍false、成本列表为空；原32命令已回收且旧进程组当前不存在才可继续。旧状态未被改写。input-cost-01和唯一fresh cost-resume-01固定，输入不得落入输出，所有新产物及模板写入新输出。

f0只读原映射，先做同一种序列化、完整终端图及明确名称双射核查，再做STA。只有f0形成完整成本记录才进入f1首次映射。f1 map模板只替换已冻结模块输入和新输出路径并完整逆还原，之后走同一图/STA门禁。任何一段失败都会跳过后续段；没有重试、增时、第二格式或参数扫描。

## 失败证据与结果范围

STA必须无Error/not found、唯一完成标记且五类路径存在，不能以rc0替代。f0既有6236cell/1658DFF身份只约束原f0；f1使用实际计数。负slack作为测量值保留，完整成本记录不冒称1ns时序通过。

正常错误路径记录FAILED并保留已写日志、映射/图及部分feature记录；finally生成的artifact-pins明确只是全部已产出文件清单，不是成功标志。完整成功须两feature结束、精确7条命令、唯一f1映射、最终输入不变、全部回收及总截止均满足。最终状态和外层退出/cleanup共同说明实际闭合，不能用部分结果或归档清单单独宣布成功。

本次仅可能增加同一候选的局部成本结果；旧balanced-local-02及更早FAILED保持，parent/fullcore/application/core-cost和生产默认资格不转授。本审查没有增加新的验收门槛或建议扩写异常框架。
