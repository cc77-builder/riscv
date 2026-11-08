# prefix feature1 单次映射目标对照

本实验只比较已冻结prefix dot8+dot16 FU，在相同RTL、Nangate45典型库与同一1ns STA边界下，把ABC映射目标从1000ps收紧到800ps的效果。原prefix D1000记录a0c4dd60…为对照，不重跑旧点；Pgroup结果不参与本次硬件选择。该有限实验回答映射参数能否改善真实最差setup slack，不能把理论深度或ABC内部Delay直接当STA/芯片频率。

固定原prefix local-01，四个实际SV、三个map/STA模板、原result/inputs/final manifest、process及cost helper、Yosys/ABC/STA和库全部核SHA。所有旧输入只读；仅写全新的dot16-prefix-map800-20261108-main/local-01，不改resident、Git、官方代码、旧实验或在途prefix整核输入。

map.ys仅替换输出目录及唯一`-D 1000`为`-D 800`，完整逆变换必须恢复原件。timing.tcl只替换输出目录，保留1ns周期、0.05ns uncertainty/transition、0.1ns输入/输出预算、5fF输出负载、原wire-load与全部五类路径。四RTL的read顺序不变，时钟、复位、接口、两槽/E2/II1、算术和指令语义没有任何修改。native tools不使用Java/Verilator，环境沿原工具相关PATH和C locale；独立TMPDIR。

默认只输出计划；明确--execute才做恰好两条工程命令：Yosys映射≤300s，OpenSTA≤60s，总预算420s，CPU affinity[2]单核、nice5；受监督进程组退出及输入前后SHA核验后才形成完成状态。新输出已存在、SHA不符、非零退出、超时、未知cell、接口/DFF变化或未审约束警告均保留失败，不自动续跑或扫描一系列delay值。外层有限保护需覆盖回收。

以实际库面积、1678 DFF、完整220端口/2888bit接口、五类STA arrival/slack及setup warnings评估。D1000原值：面积17965.374，R2R1.079437ns/slack−0.156976ns，I2R1.163662ns/slack−0.238006ns。要求同时报告面积代价和最差slack，不只选好看的路径。低于20000是候选面积偏好，不改变1ns目标或官方评分合同。

原RTL功能证据可依其精确字节复用；不重新生成RTL或执行FU/父级/整核/guest，也不声称做了新gate-level等价证明。此次只是独立FU映射和pre-layout setup观察，未测hold、P&R、功耗、父级/整核PPA或应用性能。若没有足够实际改善，停止该单参数方向；若有改善，再按真实收益决定保留，不自动更改生产默认、旧报告或core-build-02。
