# Booth3 一次成本续接：图比较与流程独立审查

2026-11-08，云端有限只读审查。读取最终控制器、合同、固定输入及 `review-pro2/REVIEW.md`，并核对固定 `fa_serialization.py` 的 `circuit()` 和原 cost helper。未导入或执行控制器，未运行 EDA、转换、STA、FU 或 PC 操作，未修改源码。

**最终结论：未发现阻止既定一次300秒续接的确定问题。** 唯一发现的末端信号窗口已由根端最小修复并静态确认。实际 serializer、回读图和 STA 是否通过仍待本次运行；本报告不转授旧 FA 的运行结果，也不预测 OpenSTA 能在30秒内完成。

## 最终审查身份

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| `cost_resume.py` | 21597 | `317f1919138e0c2e69c9d48514667fe82a871a0ec4caf8d6cc5fb206390f594a` |
| `CONTRACT.md` | 4319 | `fc6267cc664d900c143e21017f96b6adcab401c03aae642e00032a9a291fcfe0` |
| `FIXED_INPUTS.json` | 2878 | `6766593ac8cf131c2326ac40f5236ec8c16968d4178eb5e27dedfbe51716bcde` |
| `review-pro2/REVIEW.md` | 6777 | `b3895d3c46dc34a397f8badb027f786f7a1de36151c2098f1eb5f8cf44e5fa57` |

初读控制器为21507 B / `843f6959…`：最终落盘前已检查pending，但最后一次 `save(result)` 期间若信号被latch，恢复handler后只再查deadline，可能遗漏该取消。根端最终版本在成功断言/打印前同时复查deadline和pending，必要时写 `FAILED`、`local_cost_recorded=false`，并按真实时间设置超预算字段；该具体窗口已闭合，没有新增验收门槛。

## 完整电路比较

固定图函数文件实际SHA为 `82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a`，与固定输入及导入前检查一致；模块有main保护，导入仅复用定义，不执行旧FA流程。

转换顺序正确且不含新的优化：原 `mapped.json` → `splitnets`（无 `-ports`）→ split JSON及 `write_verilog -noattr -norename` → 同一Liberty回读 → `hierarchy -check`、`check -assert` → reparsed JSON。代码先检查序列化Verilog无concat左值残留，再要求split的完整图与原图相等；两项都通过后才执行回读、比较回读图，最后进入STA。

`circuit()` 保留top端口名/方向/位宽/offset/upto/signed，全部cell type/parameters/端口方向及位宽，以及逐位端口、cell终端的连接分区和独立的0/1/x/z常量标签。只忽略位编号、没有电路终端的别名和展示属性；memory、process及net初始化属性明确拒绝。

回读改名只允许已审的确定规则：原cell名以`$`开头时增加一个字面反斜杠，其余不变。检查映射值无碰撞、目标集合恰好覆盖所有回读cell，再仅对cell字典键做逆映射，调用同一完整图函数。没有删字符、模糊匹配、按数量代替连接或丢弃x常量。类型、参数、端口/连接任一变化都会使图不等；graph/mapping/输入JSON/输出Verilog均记录新SHA。

Pro2已读取的f0原件为6236cells、1658DFF、220ports，所有cell名以`$`开头且没有反斜杠美元名，固定命名规则适用。实际新回读仍必须通过完整双射与图检查，不能从该静态前提推定通过。该证明只覆盖已映射网表序列化保持电路，不宣称RTL-to-mapped等价。

## f0优先、f1次数与固定约束

f0使用已冻结的实际 `mapped.json` 和map日志，不重新综合或ABC。只有f0完成转换、完整图、无错误STA、五类路径和原常量端点检查，才向 `cost_results` 追加feature0。任何异常都会离开循环，保存失败并回收；feature1分支还显式要求列表中恰有已完成的feature0，故f0失败不会启动f1映射。

f1只执行首次且唯一一次映射。新map来自固定production feature1完整模板，仅替换已冻结Booth3四模块读取块及输出路径，完整逆变换必须恢复模板；库、ABC D1000、驱动/负载及其余pass保持。新输入SV与清单均来自先前已核SHA的实际生成物。之后复用同一序列化、图和STA流程。

成功路径恰为7个命令：f0 serialize/reparse/STA，随后f1 map/serialize/reparse/STA。记录明确f0新映射0次、f1新映射1次，没有把整个流程称为零mapping。没有循环重试、第二种格式或参数扫描。

f0实际TCL中目标目录恰出现7次，分别是网表和六份报告；新TCL仅目录替换，逆替换恢复全部原文。f1同样使用固定原TCL。1ns时钟、0.05ns uncertainty/transition、0.1ns I/O delay、5fF负载及原线负载模型保持。STA必须无Error/“not found”、唯一完成标记，并取得r2r/i2r/r2o/i2o/ready及setup检查；exit0或完成标记单独不足以通过。

## 数值与资格口径

面积按同一Liberty的实际cell histogram独立求和，并核对map日志打印面积；DFF按实际cell类型计数。采用原 `parse_path()`，要求路径存在、数值有限、arrival非负，同时保留slack原符号；constant-warnings使用回读设计检查，未知/非恒定端点不放行。与固定prefix基线按相同feature比较面积、DFF、五类arrival/slack。

`nominal_setup_met` 与 `area_within_20000` 是测量结果，不是伪造通过条件。局部成本完成可以包含负slack，不能据此宣称1ns闭合。这里的面积为库面积数值，不能自动解释为布局后的物理面积或应用收益。

旧local-01/02仍只读FAILED，已有P/R/FU证据仅按固定身份复用。新结果只允许两feature完整成本、输入未变、所有子进程回收、预算及信号全部通过后置 `local_cost_recorded=true`；parent/fullcore/application/core-cost/生产默认等边界保持false。`artifact-pins.json`明确只是所有已产物（含失败）的清单，不是成功标记。

## 预算、输入与收尾

从预检入口即计总300秒；CPU2、nice5及单线程环境固定。serialize/reparse/STA各30秒，f1 map60秒，实际命令再受总剩余额度限制；正常退出后仍核截止，异常时以原helper清理整组，最终复核所有原始/生成输入及reaped/group_absent。固定新输入、唯一新输出和原记录路径相互隔离，未见写旧结果/网表的执行路径。

外层360秒及最迟07:10 UTC实际启动应由既定外部提交/启动器落实；本次静态审查只覆盖控制器中的相对300秒预算，不声称已经检查主机实时占用或外层启动参数。无需增加本任务之外的测试或工具适配；任一步失败按合同停止并保留原始证据。
