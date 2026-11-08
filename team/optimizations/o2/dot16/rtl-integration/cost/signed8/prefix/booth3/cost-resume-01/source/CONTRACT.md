# Booth3：唯一一次固定成本续接

合同 `dot16-booth3-one-shot-cost-continuation-v1`；2026-11-08 UTC。

本合同完成已经通过新算术与FU阶段的同一Booth3候选尚未完成的成本检查，不提出新RTL、Gold、软件或工具版本。原local-01和local-02分别保持FAILED，不修改任何原输入、日志、诊断报告或资格字段。原整体资格仍false；新结果只记录本合同的局部成本和明确复用的阶段证据，不转授parent/core/application/物理PPA资格。

## 固定输入与功能前提

读取local-02原result `63cee9334942c7e60405cef939ef3020b1817e5ee147cc7e12b22339884d9121`，新R19/3与R20/6证明、实际P结构证明、两feature FU和八项负控已经完成。实际DUT/top SV与failed01一致。源码仍为datapath `880ba4c2…`、wrapper `1bc16225…`：128bit接口、同步高有效valid reset、两槽、E0接收/E1推进/E2最早响应、无阻塞II1，feature0存3×19bit、feature1存6×20bit，dot8高半biased zero不变。本次没有新功能仿真或时延/吞吐修改。

`FIXED_INPUTS.json`绑定实际f0网表、失败结果、输入/类快照、原日志和基线/工具辅助脚本。控制器继承并复核旧inputs的全部originals/snapshots、生成SV/清单、R证明日志、FU二进制和同库工具身份，前后核对不变。f0实际6236cells、1658DFF、220ports；不把这些数量当成f1的预测或新门槛。

## 唯一路径及禁止扩展

1. f0复用原映射，不重新综合或ABC。使用既有`read_json → splitnets`（没有`-ports`）→`write_json → write_verilog -noattr -norename`，随后按同一Liberty回读并hierarchy/check。无手工Verilog改写、优化pass或第二格式。
2. 导入原`fa_serialization.py`（SHA `82738e4c…`）不变的`circuit()`。原与split的完整图必须相等。对回读cell名只允许已审的完整双射：原名以`$`开头则加一个字面反斜杠，其余不变；无碰撞且目标集合完全相同，然后反向改cell字典键并调用同一`circuit()`。类型、参数、端口几何、全部逐位终端、0/1/x/z常量均保留；拒绝memory/process/init。新图和双射有自己的hash，不能转授旧FA PASS。不存在RTL-to-mapped等价主张。
3. f0转换无concat-LHS残留、图相等后才运行一次30秒STA。原完整TCL只能替换网表/输出目录，反向必须恢复全部原文本。仍用原Nangate45典型库、1ns时钟、0.05ns uncertainty/transition、0.1ns I/O delay、5fF输出负载及原线负载模型；五类路径与原constant-warnings检查保持。无Error、唯一完成标记和全部报告缺一不可。
4. 只有f0完整成本通过，才补f1首次且唯一一次固定映射。从原production feature1完整map模板派生，只替换已生成Booth3模块读入列表和隔离输出目录，严格反向恢复；ABC D1000、库、驱动、负载及其他pass不变。随后执行同一种转换、完整图核对和一次30秒STA。其映射次数独立记为1，不称作整个流程零mapping。

任一超时、转换/图/别名不符、STA错误或门禁失败立即停止，不增时、不补第二格式、不试其他参数。f0失败时不得启动f1映射。原FA路线仍停止，本合同只复用其已审通用图函数和序列化方法，不重跑FA候选。

## 资源、回收与结果

固定CPU2单核、nice5、所有子进程继承亲和与单线程环境；总体≤4核。每次serialize/reparse≤30秒，STA各≤30秒，f1 map≤60秒。**总预算300秒从预检开始计算，外层360秒含清理；最迟2026-11-08T07:10:00Z实际启动。** 超时/信号回收整组；所有进程必须reaped/group_absent。原输入保持只读，新输入仅`input-cost-01`，唯一新输出`cost-resume-01`，无新checkout。

成功需两feature全流程、输入未变、回收和总预算全部满足，状态为`BOOTH3_SERIALIZED_TWO_FEATURE_COST_COMPLETE`，`local_cost_recorded=true`。单feature中间点与整体失败分别记录；失败原件及已生成图/日志完整保存。`artifact-pins.json`只是已产出文件清单，不能当作成功标记。报告独立列真实库面积、DFF及五类arrival/slack，与prefix同口径比较，不把library area units写成物理面积，不从负slack宣称频率或应用性能收益。
