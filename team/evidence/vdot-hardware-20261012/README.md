# 独立 vdot 硬件单元实际证据

2026-10-12（北京时间），James_Hotten，源码基准16b3f2fd2加初次实现工作区；本目录顶层保留3022项阶段记录。最新12022项及审查修复见 [review/check.json](review/check.json) 和 [审查报告](../../docs/vdot-hardware-review.md)。完整接口与运行方法见 [模块说明](../../hardware/vdot/README.md)。本轮没有运行香山全核或guest DiffTest，没有测量目标频率、面积或硬件加速比。

| 记录 | 实际结论 |
| --- | --- |
| [check.json](check.json) / [emit.log](emit.log) | 初次生成SV摘要；Scala2.13.15/Chisel6.6.0/firtool1.62.1。生成SV留team/out，按团队规则不入日常Git |
| [lint.log](lint.log) / [commands.txt](commands.txt) | Verilator5.020 lint通过；记录实际生成/lint/测试命令 |
| [vectors.tsv](vectors.tsv) / [vectors-manifest.json](vectors-manifest.json) | 独立Python模型产生3022项期望：2587合法、435拒绝；记录实际向量和源码摘要 |
| [test.log](test.log) / [check.json](check.json) | 四项真实Verilator接口测试通过；完整结果/身份/异常/使能、12周期反压、同时替换、flush和occupied reset |
| [test.log](test.log) | 4000周期scoreboard，2377接受=2189返回+188取消，737阻塞；flush期间pendingTag保持可见、未取消身份正常返回 |
| [model-regression-windows.txt](model-regression-windows.txt) / [model-regression-linux.txt](model-regression-linux.txt) | 两平台各23个Python方法通过 |
| [windows-fixture-before-fix.txt](windows-fixture-before-fix.txt) | 初次Windows检查暴露三个测试夹具错误：临时路径别名、Git换行及恢复源码字节；保留原失败，不计入当前通过 |
| [reviewed-source.sha256](reviewed-source.sha256) | 生产模块、生成器、模型、构建、测试与入口源码及修复后的来源测试夹具摘要 |

Windows来源测试夹具改为canonical路径、LF初始字节和局部core.autocrlf=false；恢复原源码使用同一LF字节。生产artifact_guard门禁没有放宽，旧软件补丁与归档未改变。

原始test.log含WSL在Windows挂载盘生成文件时的短暂mtime/clock-skew警告；本次完整编译及所有仿真测试实际成功，最终退出0。推荐正式团队复现从Linux文件系统检出运行，避免跨文件系统时间戳差异；这些主机警告不用于硬件时序结论。

源码检查按接口进行：signed 8x8乘积为16位，三层+&为17/18/19位并符号扩展低32位，输出显式拼接96个零；配置只有vta/vma可非零，全部actual VL、reserved/vill/vstart及VS Off拒绝；非法有响应且副作用控制为0。有效请求、源快照和响应tag在握手时关联，反压保持槽内容。flush屏蔽两种握手并清槽；unmasked pendingTag支持适配层按ROB身份选择取消，out.fire之后的回滚由全核负责。

当前tag不包含ROB年龄格式；真正的按年龄取消、同周期新请求过滤、v0/别名RF读取、物理VL生产者依赖、vec/v0完整写回、精确异常PC与退休置VS Dirty均待适配层/全核验证。单元的3022项覆盖不等于这些集成条件已完成，T06/T07整项及T10/T11保持未验收。

归档复制原执行字节，不包含sbt/Verilator对象或可执行文件。源码和数据摘要识别构建时未提交内容；team.sha是当时HEAD，不冒充本轮提交。archive.sha256核对本目录，.gitattributes防止Git转换原始记录。

本轮复审修复旧PASS失效、随机规模与真实失败上下文，并验证默认sbt入口与含空格证据目录。后续原始记录置于review/，顶层旧日志及当时源码摘要保持原样，不能拿旧check.json认定新源码通过。生成Verilog不纳入Git，保留摘要/版本/生成及lint日志；以最终 [审查报告](../../docs/vdot-hardware-review.md) 的源码绑定为当前验收依据。
