# C2-cost 档案增量集成说明

本目录仅准备增量，不修改主仓。旧 18 条 JSON record 的规范化 SHA 已固定在 before.json；第 18 条 C2-local 的 PPA/fullcore/cycles 保持当时 NOT_TESTED。

完成测量后新增 C2-cost-20261025-01。新增独立 Markdown 小节以及成本表新行，不把 C2-local 当时未测的表行改写为后来实测。顶部当前状态可标明新轮次结论并链接新小节，旧章节的当时结论保留。原 JSON source_tables、extra_data、source_pins、archive_pin_refs 保留；将新条目的原始数据与 source pin 追加成 c2_cost。所有新增行应包含五档/45 项、控制 D、面积和失败路径。工具执行成功、工程筛选通过、1ns 收敛是三个不同结论。

本轮没有重新执行 FU/父级仿真，参考此前不可变 C2-local 资格，不能冒充新跑。当前新全核和新周期均 NOT_TESTED；若成本通过后再运行，应另加 C2-core 与 C2-cycle 永久记录，不回写本成本轮的未测字段。

主协调者封存证据后，填入新证据 manifest 的 SHA、RESULT.md pin 及独立审计状态。合并后应验证旧 18 条 record 字段和值未变、原来源 SHA 未被覆盖、新来源都可追踪。不要覆盖旧的 Windows 快照。
