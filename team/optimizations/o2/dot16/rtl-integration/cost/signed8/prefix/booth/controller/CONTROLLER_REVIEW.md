# Booth9控制器：独立有限审查

## 结论与版本

**当前修正版未发现阻止该单点本地FU/cost筛查的静态问题。** 初稿存在命令截止及最终成功落盘后的预算缺口，已在任何候选执行前修正；原准备稿保留。新算术源码与verify_booth的完整正确性由并行独立审查负责，本报告不重复该任务，也不把静态检查写成实际生成、FU或STA成功。

| 审查文件 | 字节 | SHA256 |
| --- | ---: | --- |
| controller/booth9.py | 46330 | `6681fce5cc739206c5922e025d76ae0a75334d57502b089902b5a7a72f05ea60` |
| controller/controller-derivation.json | 14468 | `68ea0c414c37d4f7aedefd301bc078defef8067acc077009957ce671361068f3` |
| controller/controller.diff | 20783 | `da0d6b641a0131b4c7ffe4f34e732e0a3b55c939d6433be1169eb734c7aef6a4` |
| controller/BOOTH_CONTRACT.md | 7069 | `85e449a5328e74a8894728e3d1c3816b081ded1ce4d39c79681ec2b45949300b` |
| source/source-derivation.json | 11734 | `72b19ecbc899c0175c86a31e1032607b65897999c17117e2de21f21fac7c7eae` |

## 1. wrapper的数据表示绑定合理

feature0要求两个P寄存器均为19位，实际捕获表达式明确取`_products_row0/1[18:0]`，Finish19直接接收保存的两行。若实际新CSA证明两行和为S8+2^19，则逐行截低19位后求模和等于S8模2^19；S8的真实范围可由有符号19位恢复。

feature1要求四个P寄存器均为20位：低半两行不截断，高半dot16时取完整20位。dot8时在接受请求的同一边沿保存高半`(20'h80000,20'h0)`，其和为2^19。两半偏置在Finish20的模2^20加法中抵消，因此dot16恢复S8_low+S8_high，dot8恢复S8_low。R阶段只使用已保存P行，没有依赖后来输入的isDot16进行修正，也没有对新的unsigned行做符号扩展。

`wrapper_binding()`对实际生成文本要求：一/两个CSA实例的完整四端口与输入半部切片、完整P寄存器声明及每行唯一写表达式、一个精确Finish19/20实例及全部连接、对应宽度的prefix结果、唯一illegal-zero或prefix-result的R写表达式，以及未变的架构输出扩展。feature1的无偏置零、19位截断或沿用旧符号扩展均不符合这些检查。

生成文本的非数据顺序赋值比较本身不是整个时序控制证明；这里同时依赖下述完整源码逆派生和本次新的FU测试。报告没有将其升级为全FU顺序SAT或RTL到映射网表等价。

## 2. 非数据状态与prefix SAT复用前提保持

四处wrapper编辑仅涉及P数据位宽、unsigned rowWords、低半捕获切片和高半dot8偏置零。完整逆还原核验表明时钟、valid reset、accept/move、kill/flush、ctrl/perf保存、R传递条件及架构输出扩展的其余源码逐字保持。内部feature1 P行增长为20位已在合同和结果字段明确披露，未错误宣称所有状态宽度不变。

旧Finish19/20处理的是任意输入行的固定宽度模和。控制器要求旧两项SAT记录分别为2×19和4×20、unconstrained_inputs=true、真实PASS且无重试/反例，并绑定原gold/gate/script/log完整SHA与成功日志。新四套cost/FU生成物必须实际逐字匹配对应原Finish SV，随后再次将新SV的SHA核对旧miter的actual_rtl_sha256。因此改变P行编码不破坏这两项无约束模块证明的适用前提。

旧乘法SAT超时仍明确保存为历史UNKNOWN；新P的arithmetic_structure_proof_reused=false，必须由新verify_booth消费实际生成CSA字节得到新结构证明。旧FU PASS只作为冻结工具/输入来源，新feature0和feature1各自仍须通过完整正向及identity/wen/high/cancel四类负控；不存在直接转授旧FU资格的分支。

## 3. 逆派生已独立核实

对当前controller-derivation的31项编辑按逆序逐项唯一替换，精确恢复45,126 B的原Pgroup控制器，SHA256为`794544ddfb3455b05deaffe8588d3c9715d02446ac04c50fe2710c6caaaafc0e`。重新计算的统一diff与controller.diff完全相同。顶层函数仅wrapper_binding与run改变。

对source-derivation的一项datapath和四项wrapper编辑分别逆还原，得到完整冻结prefix基板：

- VDotDatapath.scala：8780 B / `1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb`。
- VDotElastic.scala：8999 B / `912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92`。

候选源码SHA分别为`f0a8bbe58440c6113aa56f848387c6b4e4a487d71ec2832a1e43fca55d3a8245`及`0fcc5df10355ee1e6382678ba40bc9d7ddf830b560dcc469c46e6a6888441556`，与控制器和派生记录一致。这些是实际云端字节比较，不仅采用派生JSON的exact_inverse自述。

## 4. 预算修正、回收与输入冻结

初稿`2ba91465…`在Popen及一次结果写入后重新计算命令until，check也只核信号；最终成功结果落盘后缺少总截止核对。此问题已报告主端。当前版从run入口建立同一1200秒deadline，check核信号及绝对总截止，每条命令在Popen前固定`until=min(deadline,now+limit)`，不再启动后重置；最终成功result落盘后再check，超时或信号会重写FAILED并抛出。失败回收及失败记录持久化不受成功预算截断。

原准备稿及派生/diff保存在preparation-controller-01；该目录的PREPARATION.json明确为NOT_EXECUTED_PREPARATION_RETAINED，未把它记录成一次实际工程失败。

CPU参数只允许2且预算必须为1200秒，nice5、make-j1及子进程继承CPU亲和保留。每条外部命令独立进程组，finally继续使用固定helper清理、reap并记录group_absent；没有重试、加时或新参数扫描。启动器的实时资源检查和CPU1 K768运行状态由主端实际回执说明，不由本次云端静态审查推定。

原输入与输出路径隔离，源、基板、工具、原FU输入、classpath及复用SAT原件均绑定；快照须与原pin相同。成功前复核原输入、快照、新class、生成文件和原classpath。cost的原ABC/STA模板仅允许模块读入列表及输出路径替换，并要求完整逆还原；记录实际DFF/面积/五类路径，不将预计增加四个P数据位当成映射门禁。负slack继续保留；完成筛查不等于1ns通过。

## 资格与范围

新的实际生成/结构证明、两组FU测试、两组局部cost完成后才可能设置本轮局部资格。parent/fullcore/application/core-cost仍为false，new_core_builds/new_core_runs为0，生产默认不变。没有以结构FA减少或局部面积推定应用性能/物理PPA。

本审查仅做本地只读源码/合同分析、逆派生及diff核对，没有执行控制器、EDA、构建、仿真或访问PC；未修改候选源或增加验收门槛。实际新RTL能否匹配这些严格绑定以及真实FU/cost结果，仍由本次单点运行的原门禁和回执决定。
