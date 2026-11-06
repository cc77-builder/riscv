# Row32 W8 的静态成本与未决性能

本分析解释为什么保留候选，却不按宏指令减少直接宣称加速。所有展开公式绑定 T17 源码提交 `34bae6d4acceac939f958199dae53c14bc1f6183`；这是**declared decode-uop projection**，不是实际issue数量、RF访问、访存事务或周期。

## 完整Q路径

| 路径 | 完整函数宏指令 | 声明的解码uop | Vimac计算分片 |
| --- | ---: | ---: | ---: |
| 原FR | 35,670 | 73,732 | 10,368 |
| GS32 v2固定源副本 | 20,123 | 59,165 | 10,368 |
| rowlane32 W8 v1 | 14,361 | 53,321 | 20,736 |

FR与row32的宏数量已由本轮真实ELF有限模型独立核对。GS32这一行来自其只读生成器副本，SHA256 `216571084e75823a67a86d72627a8c6e9ca304e23a7f640720f83ad6dac1793f`；它不转移GS32的任何目标结果。三份完整函数源、固定公式、逐操作和逐VTYPE计数，以及只依赖Python的复算入口保存在 [cost-source.zip](evidence/screen-v1/cost-source.zip)；将其解压至新scratch目录后执行`python3 uop_projection.py`即可重算。

row32相对GS32的宏数量少28.6339%，声明uop少9.8775%。两者的VSET宏数量分别为165与2,270，差2,105条；这占总声明差值5,844的36.0%。如果仅作敏感性分析，为每条VSET扣除一个附加声明操作，差距缩到6.5718%；**这不修改正式声明计数，也不是实际issue预测**。

## 完整声明数的分解

下表把同类操作相加，三列都精确求和到上表总数。`li/mv`按各自实际单条addi编码计；这里只列已核实的指令子集。

| 类别 | FR | GS32 v2 | row32 W8 |
| --- | ---: | ---: | ---: |
| 标量加载/寻址、CSR、分支与返回 | 8,372 | 5,133 | 5,749 |
| VSET | 8,428 | 4,540 | 330 |
| 向量立即数初始化 | 5,292 | 768 | 1,542 |
| W/X向量字节加载 | 11,664 | 8,748 | 7,776 |
| `vwmul.vv` | 10,368 | 10,368 | 0 |
| `vwredsum.vs` | 20,736 | 20,736 | 0 |
| 结果收拢move/slide | 4,536 | 4,536 | 0 |
| `vsext.vf2` | 0 | 0 | 10,368 |
| `vwmacc.vx`，含标量广播 | 0 | 0 | 23,328 |
| 两整数累加器合并 | 0 | 0 | 648 |
| FP转换/乘法/加法 | 2,916 | 2,916 | 2,673 |
| strided Ws加载 | 1,296 | 1,296 | 810 |
| Y与完整slots写回 | 124 | 124 | 97 |
| **合计** | **73,732** | **59,165** | **53,321** |

关键映射见固定 [VecDecoder](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/VecDecoder.scala) 和 [UopInfoGen](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/UopInfoGen.scala)：

- `vwmacc.vx`映射`VEC_VXW`，e16/m4时为`2×4+1=9`，其中8个计算分片、1个标量搬运；`vsext.vf2`为4。
- `vwmul.vv`与`vwredsum.vs`分别采用`VEC_VVW`、`VEC_VWW`，声明数都是`2×LMUL`。不能把GS32 reduction误按一般归约类型计数。
- FR收拢阶段实际为VL4/e32/m1，每条`vslideup.vi`为2；六条共12。把它误读为m2会夸大row32优势。早期局部估算480及11.7%已撤回；正确的整数子集比较是FR432对row32 W8的424，仅少1.85%，且这张子集表不包括完整循环。
- unit-stride表使用`simple_emul`，不是原VTYPE的`simple_lmul`。`vle8`在e16/m4下的EMUL为2，故声明3。strided load/store在本nf0范围为EMUL+2；whole-register `vs1r`为2。
- `vmv.v.i`走`VEC_VXV`，为LMUL+1；`vfmul.vf`也含附加搬运。VSET声明为2，其中可含附加NOP；它们不应全部当作真实计算资源服务量。

## 主要反证与实际成本边界

row32仍完成82,944个精确乘积，但使用e16 widening MAC，Vimac计算分片从10,368增至20,736。它同时取消原整数归约/收拢，把另一部分工作改为Vialu符号扩展。固定 [FuConfig](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/fu/FuConfig.scala) 的延迟或源级分片数不能独自证明哪个资源是实际瓶颈；发射、共享RF/写回、缓存和依赖仍可能改变排序。

新候选的实际ELF模型按每次完整Q读取W82,944B、X2,592B、Ws10,368B、Xs324B和context48B。W/Ws大小未变；X/Xs重复读次数从36降为9。这里是架构层地址足迹，不等于缓存miss、DRAM流量或实际周期。

权重必须转换为新转置布局。一个Q的最少逻辑读写量是82,944B读加82,944B写，但该下界不含任何目标时间或缓存假设。既有基线本身也有packing，未来摊销应使用实际差额`P_new−P_old`，并区分模型加载、首token和后续token边界。W16路径会把权重字节数翻倍，当前暂停。

一个只读备选是按3个k暂存e8/m2 widening产品，再以e16/m4 `vwadd.wv`累入e32/m8，保留full s8和严格FP。每个32行×GS32块的整数算术声明数仍为416，仅把128个计算分片从Vimac移到Vialu，并增加21个VSET宏。两种路径的W加载都为EMUL2/3个声明uop，没有加载声明节省。

固定 [Parameters.scala](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/Parameters.scala) 的`vfSchdParams`（Git blob `0abf4a0c5fb3a0f498cc4ba33c5f2bd143190886`）提供了一个具体结构依据：Vialu配置在VFEX0、VFEX2各有一实例，Vimac仅在VFEX0；VFEX2使用另一组VfRD3/4/5及独立VfWB1。VFEX0与VFEX1的Vipu/Vfcvt/Vfalu共享VfRD0/1/2及VfWB0，优先级不同。这使把部分工作移往第二Vialu有结构空间，但不是实际调度均分、独立无限带宽或两倍吞吐的证明。

该B3备选尚未实现；当前没有row32在目标上的资源饱和或依赖等待证据。应保留这一条件化机会，由真实参考执行和有界目标成本决定是否投入，不因存在成熟先例或两Vialu配置就直接替换当前候选。

本分析与[功能结果](RESULT.md)共同支持保留候选和最小后续选择，不支持完整应用加速、默认入口变更或新PPA结论。
