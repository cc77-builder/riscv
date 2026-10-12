# 独立 vdot 硬件模块审查与交付

2026-10-12（北京时间），分支 `James_Hotten`。固定审查基准 `16b3f2fd24d8f218abadccca268bf37aa03e661c` 加本轮工作区及未跟踪源码；基准到HEAD没有新提交，因此实际范围为工作区差异。按code-review技能分别做Standards/Spec只读审查，主执行者做实际负控与复验。规格依据为 [vdot合同](../spec/vdot.md)、[接入接口](../spec/rtl-interface.md)、[原任务表](../香山vdot赛题_三人分工与Git协作.md) 与 [模块说明](../hardware/vdot/README.md)。

## Standards

初审两项P2，均属于测试入口与交付规范：

| 发现 | 修复与实际验证 |
| --- | --- |
| 复用成功证据目录时，emit/lint/test失败可留下旧check.json PASS | 入口立即删除旧结论；最终check.json同时绑定源码和向量摘要。从真实成功目录以故障launcher重跑，退出1且旧PASS消失；负控在PYTHONOPTIMIZE=1下通过 |
| 初次归档包含生成的VdotExec.sv，违反协作计划§4.4“不进入日常Git历史” | 删除待入库生成SV；保留SV摘要、firtool版本、生成/lint日志及命令，实际SV在忽略的team/out。初次日志/向量/来源记录保留历史范围 |

未发现生产Scala中具有实际影响的baseline smell。构建版本匹配根build.sc；Windows测试夹具修复约束夹具路径/换行，生产artifact_guard门禁保持。补验证默认sbt入口和含空格证据目录，SBT runMain内部参数添加路径引号。

## Spec

初审一项P2覆盖计划缺口，受控失败另发现诊断缺口：

| 发现 | 修复与实际验证 |
| --- | --- |
| 原计划RTL单元至少10000固定随机输入，初次只运行1000且未记录调整依据 | 增加到10000个不同随机请求；最终总12022项，11587合法/435拒绝。4000周期scoreboard仍独立计数，不冒充额外不同输入 |
| 原有withClue不会展开Chiseltest异常上下文，故意错误高位期望虽然失败却看不到源/配置 | 失败时显式打印VDOT_HW_DIAGNOSTIC，再抛原异常；实际故意填错D00目的byte15期望，测试失败并显示指令、tag、vd/vs1/vs2、源值、vl/vtype/vstart/VS、完整期望和实际值。原向量/RTL未修改 |

未发现生产模块数值或局部控制功能错误：16位signed乘积经17/18/19位加法树，符号扩展低32位并拼接96个零；编码及配置检查符合合同，非法仍有身份/cause2响应且无数据/VS使能。反压保持槽内容，连续替换只在握手时发生；flush优先于两种握手，pendingTag不被flush屏蔽。

## 最终验证与范围

当前证据入口为 [review/check.json](../evidence/vdot-hardware-20261012/review/check.json)，初次3022项归档保留原阶段，不能用它认定新源码通过。

- Verilator5.020 lint与四项真实接口测试通过；12022项逐项完整结果/身份/异常/使能检查。
- 10000固定随机请求经实际TSV去重，均不同；合法操作数字段覆盖全部32编号。这不证明真实RF/v0/别名路由。
- 4000周期scoreboard按真实握手核对2377接受=2189返回+188取消，另有737阻塞周期；12周期定向反压、同时替换、flush阻塞/可握手及occupied reset均有检查。
- 失败重跑旧PASS失效、真实错误高位期望与诊断字段的两项负控通过；负控的非零退出是预期失败，未计入功能成功。
- 最终源码/向量与测试记录摘要匹配，生成SV摘要和firtool版本保留；默认入口及含空格证据路径实际通过。
- 初次阶段的Windows/Linux各23个Python方法通过记录保留；这些模型/来源测试源码自当时通过后未变，未把它们计为12022条硬件执行。

两轴最终复审结论见 [复审记录](../evidence/vdot-hardware-20261012/review/final-review.md)；提交前核验源码/归档/暂存字节和Git空白检查。仓库缺少docs/agents/issue-tracker.md，技能建议后续用`/setup-matt-pocock-skills`配置议题跟踪；本次已有明确本地规格，不依赖外部议题或消息。

本次为T07的独立运算/局部控制交付，T06的团队确认及全核接口映射仍待落实。真实物理VL与配置依赖、v0/别名RF读取、vec/v0写回、ROB按年龄取消、精确异常PC、成功退休置VS Dirty、全核DiffTest、目标频率/面积和T13性能实验均未验收。数据路径的一拍延迟/每拍接受描述局部协议，不代表目标处理器频率或加速比。
