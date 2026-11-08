# 原 prefix feature1 显式 FA_X1 映射：计划独立审查

## 结论

**赞成按所述范围做一次有界映射筛查。** 对已识别的 FA 成对等式逐一替换，比引入全局提取或重写更容易限定变动范围；保留原 D1000、四件冻结 RTL 的身份、相同 FU 边界和 1 ns STA，可以回答这一具体映射选择是否有成本收益。没有发现需要改成更大方案或先增加整核/FU实验的理由。

当前只是计划审查：尚未审新转换代码、读取实际库文件或运行 EDA，不能据此宣布实际替换、映射、时序或新网表等价已通过。下面是该计划内需要落到代码和报告上的细节，不是额外工程验收门槛。

## 已读依据

| 文件 | SHA256 |
| --- | --- |
| `source-review/prefix-candidate-v1/controller/prefix.py` | `8f33f550c9b7e74e8190cb5f5a2cfdcc693a783d86ae905ec3e60c7ad10d148c` |
| `verification/prefix-pgroup-candidate-01/controller/verify_csa.py` | `e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de` |
| `verification/prefix-map800-preparation-01/map800.py` | `f854197eb5b3291d927d8cdbb88d6d1192f0411542c5a0d95ca88dfc64d8421c` |

`verify_csa.py` 的固定语法完整解析原模块，按名称配对 sum/carry、核输入集合和每组二态真值表，并核完整 DAG、位权、消费关系与最终行。`prefix.py` 将已有结构证明绑定到实际相同 CSA 字节，同时检查无丢弃 carry、两行最高位和真实 wrapper 绑定。这是可复用的原输入依据，不能直接把原 proof 的 SHA 改写成新文件 SHA。

## 实现时最重要的五点

### 1. 证明实际发出的实例，而不只证明转换器打算发什么

已有 checker 的 Parser 只接受 wire/assign，不能直接接受 FA_X1 实例后还宣称原 checker 通过。可继续用它识别固定原始输入；转换器再对实际输出中的每个实例做一个很小的封闭解析。

每对应一一对应原 sum/carry：A/B/CI 是原 xor 的三个有序 scalar operand，S/CO 分别接原 sum/carry；五个命名端口必须唯一、完整，无遗漏、额外端口、别名或输出互换。逐对八值比较须计算**实际端口连接后的** S、CO，与原两条表达式比较。主端给定的库公式满足二态关系 `A+B+CI = S+2*CO`；实际执行仍需将所采用的 FA_X1 名称、标量方向和两项函数绑定到原固定 Liberty SHA，避免只对硬编码“理想全加器”自证。

完整 inverse 应从实际候选文本和已核对的替换记录恢复原文件，并比较原完整字节；不能用“直接返回保存的原文件”充当 inverse。17 个 HA、全部部分积/常量、声明、行拼接及其他字节保留。这样支持**指定生成模块的局部二态替换等价**，不宣称 X/Z 行为或后续完整 mapped netlist 等价。

### 2. 477 是单模块计数；feature1 有两个 CSA 实例

`prefix.py` 的 `wrapper_binding` 明确规定 feature1 实例为 `products`、`highProducts`，不是四个实例；“四件 RTL 输入”也不等于四份 CSA。

因此，转换层应记录 **477 对 FA / 17 个 HA**；feature1 层次展开前的预期显式 FA 数为 **2×477=954**。最终 mapped JSON 应报告实际计数及其解释，不把477当作整个FU的FA总数。若工具消除或改写部分实例，应按实际输出解释，不能仅靠源级计数宣布指定 leaf 已保留。

“双输出活性”宜明确为 S/CO 均有正确连接并可达其结构消费者，不能仅凭非空连接就写成动态激活覆盖。此项与已有全实例 pin 覆盖检查合并即可，不需要另开仿真。

### 3. map800 的脚本派生不能原样复用

`map800.py:derive` 会把 D1000 改成 D800；本实验应保留 **D1000**。同文件对 read_verilog 的检查当前还要求读取四个旧路径，必须精确改为“一份派生 CSA + 三份原冻结 RTL”，否则可能实际仍映射旧模块。

建议继续采用完整脚本 inverse：除了隔离输出路径、唯一 CSA 输入路径及明确的 `read_liberty -lib` 声明，其余映射与 STA 文本保持原版。固定原 Liberty、Yosys/ABC/STA、abc.constr、时钟/uncertainty/I/O/load/wire-load。功能模型不进入综合；工具是否保留期望的 leaf 由实际 mapped 结果说明，不从命令写法预先推定成功。

### 4. 真实 leaf 必须同时进入面积和 STA 解释

已有框架的库面积独立求和、Yosys面积对照、完整220端口/2888bits和1678 DFF比较、五类路径与收尾检查可以保留。FA_X1 必须是该固定库的真实单元，S/CO 的实例方向、面积及实际 STA 路径解释一致；不能因单元名存在于面积表就忽略未链接端口或时序缺口。

新报告应区分预期 Liberty leaf 与未解析的非库 blackbox。保持原常量端点分类，注意是否新增缺失时序/未约束对象；不把原已分类端点重新升级成额外阻塞条件。这里核的是同一次计划已有的映射/STA输出，不建议新增完整网表形式验证作为此次筛查前置。

### 5. 结果标签必须反映映射输入的实际变动

`map800.py` 的 `unchanged_rtl=True`、`rtl_functional_evidence_reused=True` 不能原样照抄为此次候选结论。原冻结文件及生产Scala没有改动，但一份派生映射输入SV的字节确实改变。

建议分别记录：原冻结输入未改、三份RTL字节相同、一份CSA受控替换、局部二态替换核对结果；继续保留 `mapped_netlist_equivalence_tested=false`、无新FU/core运行、无新应用/整核成本资格和默认实现未变。不要把原 prefix 的 FU/父级 PASS 标成这份新 mapped netlist 的新执行结果。

## 比较结论与更简单方案

主要比较对象应是**原 prefix D1000** 的同边界记录；D800可以作为独立历史观察，不与此次 FA替换合并成一个变化。固定原 xor operand 顺序到 A/B/CI 适合作第一点；即便二态功能对称，不同 pin 的时序仍应由真实库及路径决定，不能由这一点宣称所有 FA pin 分配已最优。

直接实例化会改变后续 Boolean 优化可跨越的边界，因此测到的是“显式 FA leaf 加其余相同流程”的整个 FU 映射效果，不能把最终时序变化全部归因于孤立FA门延迟。报告面积、arrival和slack各自变化，主要依据原先关键路径；不由一条非关键路径改善推算频率或应用收益。

**当前方案已经足够简单。** 复用固定 Parser/配对规则，新增一个短的成对替换与实际实例检查函数，保留现有 map/STA 驱动即可。不建议为这一点引入全局 extract_fa、通用 technology-mapping 框架、引脚排列搜索，或新增 FU/整核轮次。待实际成本结果出现后再判断是否值得继续；本报告没有预设采用结论。

本审查仅云端读文件并写此报告；没有访问 PC/Pro、执行 EDA、修改源码或改变已有工程资格。
