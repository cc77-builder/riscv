# 固定 CSA 生成物的 FU / cost 续接合同 v4

合同：`dot16-fused-signed8-csa-continuation-v4`。这是一项固定 predecessor 的有限续接，不是通用 resume、不扩大 SAT 预算，也不修改已完成或失败的旧运行。

## 基线、接口与流水

直接表示基线为本轮 R19/R20：wrapper `70dcc27381d3e7226eeff333c943d35b982ec1fdd37b75b680060a13aaf94e2a`，datapath `50522c0cd2700f7f852872049533bc31f79ce811ad2ed53da2c1d333cece45e2`，真实 local-01 result `f42f7285ff8a357877c546d433251b1dc8c8eef66ee9218c9e3b2c002ca0a261`。其 dot16 面积为 21040.866，r2r/i2r arrival 为 1.189326/1.209418 ns，名义 1 ns 未满足。旧 signed8 local-03 的 product 全输入证明只作为固定对照身份，不能自动转给新 CSA。

保持原 128 位输入与输出、字节序、指令与合法性要求、完整 control/perf、P/R 两槽、ready/valid、redirect/kill、同步高有效 valid 复位。数据和 metadata 不增加复位。上升沿 E0 接收，E1 P→R，E2 最早响应，连续无阻塞 II=1。所有 accepted/move 使能及输出高96位零保持。source-derivation.json 的七项精确变更须逆向恢复 R19/R20 wrapper 全部字节；旧 datapath 的2925字节原样保留，新增模块只由新 wrapper 采用。

## 算术与微架构

每个 half 处理8对 signed8，共512个1位部分积。只有 `(i==7) xor (j==7)` 的14项/product取反；取反后的加权 heap 等于该乘积加32512。八份 heap 加 bit18 与 bit11，恰等于真实8项和加2^19。固定列阈值为 `[63,42,28,19,13,9,6,4,3,2]`；超额至少2使用FA，超额1使用HA；每层只消耗前层已有位，新carry只流入下一层下一列。全部运算按模2^19解释，不能把中间heap当作不溢出的有符号和。

P保存两行19位编码，而不是逐项16位乘积。本固定压缩树具有更强的不变量：没有被丢弃的高carry，row0[18]=1，row1[18]=0。因此两行的无符号整数和是S+2^19，分别解释成SInt19后的整数和恰为S。P后把2/4行分别asSInt并pad到19/20位，再用这个固定宽度的普通加法规约。中间截位是模2^19/2^20运算，模加法满足结合律；最终8项和[-130048,131072]、16项和[-260096,262144]均在相应有符号范围内，所以重建精确。不能仅凭一般模19恒等而采用这条直接路径：实际生成证明必须另外核实无高carry舍弃与上述两个最高位。

本轮 source-01 在尚未运行时采用通用的“每half模19还原后再求和”路径；其核心算术正确，但合同对“分别有符号解释两行”的一般禁止过强。本 source-02 基于已核固定布局不变量，在首次真实小试前改成更简单的直接求和，不改变压缩树、不构成测试矩阵。source-01原件保留。dot8仍在同一个accept边沿把高half的两行都置零，此时两行的signed和也是零；P后不再注入常数，也不读取后来输入的模式。

## 先前实际执行与续接边界

source-03 / local-02 原 result 为 103298 B，SHA256 `84b752a19a62d6e436d347cdd1273110c6530bd6024c41eecd58fbd8574e450d`。内部 2026-11-07T19:29:48.734033Z 开始，19:32:56.685056Z FAILED；host 19:32:58.0712692Z exit1、cleanup_complete=true。编译、四套生成、实际组合结构证明共六命令 exit0；第七独立 miter 达到外部120s期限并被原控制器回收。日志在39622变量/111869子句的Solving处结束，没有SUCCESS、FAIL或ERROR。独立SAT只能记录 `UNKNOWN_EXTERNAL_TIMEOUT`，不得记录solver PASS或反例。原合同允许完整结构证明独立支撑组合算术；本版修复的是未完成步骤的接续方式，不改变证明内容或接受反例。

原输入清单612f760a4d593a1899e7079c98a4fde5b2d14e702435cb09ffc1425e5f981616、20文件overlay清单d76cd45beda440ecc8fdc64ced5dc796e19c1e8641d7ebd7e8e12c8e401e242a、classpath清单d9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902及完整结构报告9483d70f24876e7c89281e559d3d062355c0787e38a7f3fd7ab9cf36d3cd8ad6已经只读取得SHA。控制器固定这些身份以及原SAT输入、日志、source03控制器和合同；核对原七项command完整结束、前六项exit0、第七精确TimeoutExpired和全部进程回收，不接受其他前序或失败。

1. 所有原inputs originals/snapshots、compiled classes、真实四套SV、两类manifest、完整classpath和工具身份重新核对，并在末尾再核对。前序进程组若仍存在即拒绝，不发送kill、不改归属。
2. 新local-03原样复制四套实际SV及相对路径manifest（两类原manifest均已确认仅相对token），保留原生成来源字段；执行原封闭文件集合、manifest、模块实例、源码逆向、P/R表达式检查。四套实际CSA继续是108563B SHA68227036423ff34235b275546dc7d2341fb5e890857e1b9098f4bc070f9545f6。复用的是已实际生成的相同字节，不声称发生新编译/生成。
3. 原样保存实际结构证明和gold/gate/prove/log，重新绑定结构report至相同RTL及checker。该证明覆盖全部2^128二态组合输入，477FA/17HA、无舍弃carry、row0/row1最高位1/0；四个wrapper精确检查和源逆向另外绑定P后解码。无全FU顺序形式化或X/Z承诺。SAT明确UNKNOWN，禁止重跑、扩预算或调整输入。
4. 只执行原控制器尚未开始的26个子命令：两feature各lint/build/positive/四种fault运行及原负控分类共22个，再两feature各map/STA共4个。C++、vectors、正向coverage和负控检查器完全不改；同原完整common-FU、Nangate45、ABC驱动/负载、名义1ns五类STA，映射模板只允许原有精确模块列表与输出路径置换。单次候选，无参数矩阵。
5. CPU1、absolute nice5、单worker、总1200s；原各步骤有限预算不放大。结果commands只列本次实际26条，另显式记录6项复用和1项未重试。所有旧FAILED、日志、输入均不改，源/工具/生成物审计完成才可给本次FU及成本结论。相对Rwidth报告新增收益，面积/时序不达目标照实报告。

生产默认、常驻WSL源码和缓存、原N/P整核运行均不变。本地FU/组合证明与综合STA之外的parent、整核、应用性能和core cost资格仍false。只有实际收益值得时再决定进一步集成验证。
