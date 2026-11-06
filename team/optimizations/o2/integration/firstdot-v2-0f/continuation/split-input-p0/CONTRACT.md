# P0：当前0f/C8的8×32 split-input调用与公平比较合同

合同ID：`zjhwork-0f-c8-split-fixed-a-8x32-v1`。日期：2026-10-28。P0完成的是版本、接口、生命周期和比较规则核查；新适配器、最终ELF/BIN及目标运行尚未产生。来源与实物锁见[SOURCE_LOCK.json](SOURCE_LOCK.json)，六类函数兼容核查见[STATIC_REVIEW.json](STATIC_REVIEW.json)。

**准入决定：P1_GO_FOR_OPTIONAL_INTERFACE_QUALIFICATION。** 分离权重/激活有真实消费者结构支撑，允许后续在当前0f上做可选接口资格验证。当前C8保持；不预告性能必然改善，不把供体每次288B打包的74.5%降幅套用到本项目。本次不执行P1。

## 1. 现在是哪一版

| 层级 | 固定身份 | 含义 |
| --- | --- | --- |
| 当前工作代码/远端zjhwork | `10b71ad4bff25cd2070e775c74a4717b01602f75` | 在R5/C8发布版上增加公开项目研究文档；本地另有上轮未提交的后续计划 |
| 当前生产硬件 | `0f12df675378556670afd0dd2153f47fcb330610` | O2两槽弹性FU＋H1低32位保存＋DIV取消保持修复；未采用C1/C2/C3 |
| `src`树 | `78a0c93852dced038f645205e33d36a520fedfcd` | 当前与0f相同；398文件与一个Git子模块指针分别锁定 |
| 实际clean-02构建源码 | `c823a8786e052c6e26f6915563c42b6d730dd8e3` | 不能把今天的文档HEAD冒充原EMU构建提交 |
| 软件入口 | firstdot V2四尺寸＋显式C8 8×32 | C8 API v1、完整对象、编译期选择；没有新dispatcher，公共默认未改 |
| 稳定资格 | R5/G5选定范围已验收并发布 | 保留原clean-02墙钟FAIL及组合13旧＋1新边界 |
| 供体 | `zufan@ffd668bf1bc80850d382f514d13bb00316c85582` | 固定文件API获取/旧快照逐blob核对，不整分支合并 |

EMU固定SHA256为`acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9`，正常NEMU为`62b1707c52a4c323468481e0c1863b79f244d9a3fd54aeb7b7d2ecb5f01a35ca`。配置为MinimalConfig、单核、EMU_THREADS=1；O2/T14/O2_TRACE/T13_TRACE启用，O1/T12_TRACE关闭。正常/故障NEMU、flash及工具的完整哈希见锁文件。

**构建应用必须使用clean-02的AM/klib。** AM为`b421e116992550ac29aa64f3116cc64f7bfad9a857b13eb773892cdaca20801a`，klib为`3147e2bf410a16f3fbecd077601c4ca96bd26d17f6a53fb2c928bf13df53eb63`。旧原xs-env目录中的库即使存在也不混用。GNU GCC11.4/binutils2.38沿用C8已核8工具；cc1/as/libgcc与Python实物也已补入锁文件；新构建再绑定最终完整命令。故障NEMU夹具构建时嵌入正常NEMU的绝对路径；逻辑角色不表示任意搬移可用。本机固定路径复用成立，若移动根必须先检查ELF依赖，必要时以新身份重建夹具，不改旧metadata。

## 2. 输入生命周期：事实与选择

| 证据 | 已核实事实 | 本合同如何使用 |
| --- | --- | --- |
| 当前C8 example | 静态连续288B数组，仅编译/链接示例 | 不能证明业务需要每次从分离输入打包 |
| 当前C8普通C main/cases | 原数据已是连续A与x；复制到护栏区是测试准备，不是测得的业务开销 | 连续输入对照必须直接调用，不人为加入复制 |
| 供体split夹具 | 原连续数据被放到分离arena，每窗重置；旧wrapper每次复制256B A＋32B x | 原74.5%只绑定这一指定夹具，不能当作合理cached-packed实现的下界 |
| 固定runq上游 | 权重mmap只读，激活单独分配并重新量化；一次xq被Q/K/V共用 | 权重与激活有不同生命周期，分离输入具有真实使用理由 |
| 供体q288 | 权重预先转成tile布局；叶函数读取持久A块与x分组 | split只能减少额外拼接，不消除模型权重重排/量化的全部成本 |
| 供体fixed-weight | 每stream只复制A一次，每步更新32B x；既有N1/N4性能仍HOLD | 学习缓存公平性，不继承其性能资格 |

因此P1的**主场景为“固定A、变化x、已准备状态下的一次完整调用”**。对照C8允许保留A的256B副本，每次仅更新必要的32B x；split直接读取A/x。另测首次准备＋调用和原生连续输入，三者分别报告，不能混成总加速比。尚未将真实runq/QKV程序移植到当前0f；P1只验证其输入结构对应的有界8×32调用，不宣称完整模型成绩。

缓存由调用者显式管理，无隐藏分配或全局缓存。A在一个stream内不变；A内容或对象改变时，packed调用者必须重新准备，split重新绑定有效指针。x按次变化；任何实现都不得复用过期x或输出。正式性能使用已存在的三组8×32数据；额外交叉x序列只为验证缓存生命周期，不改原22＋10000数学测试向量或历史manifest。

## 3. 固定调用ABI

平台：裸机RV64/lp64d，VLEN恰好128（vlenb=16），VS已启用。vdot路径要求当前自定义编码及匹配NEMU；不授予Linux用户态或任意RVV平台资格。

~~~c
typedef void (*split_leaf)(const int8_t *a, const int8_t *x,
                           struct caller_slot *slots);
struct split_context {
    const int8_t *a;             /* offset 0 */
    const int8_t *x;             /* offset 8 */
    int32_t *y;                  /* offset 16 */
    struct caller_slot *slots;   /* offset 24 */
    split_leaf entry;            /* offset 32 */
};                              /* RV64 sizeof = 40 */
void split_full(struct split_context *);
~~~

| 对象 | 要求 |
| --- | --- |
| A | 256B，signed INT8、行优先8×32，可字节非对齐；调用期只读 |
| x | 32B，signed INT8，可字节非对齐；不要求紧邻A，调用期只读 |
| slots | 8×16B，首址16B对齐；各槽低32位为精确INT32累加，高96位全零 |
| y | 连续8个INT32、32B，自然对齐；完整调用包含从slots提取y |
| context | 正常对齐，40B；五个字段在调用过程中稳定；与所有输入/输出范围不重叠 |
| 别名/存活 | A、x、slots、y、context各字节范围互不重叠，存活覆盖调用；连续A/x可以属于同一分配的相邻不重叠子区间 |
| 状态 | 遵守RV64 C ABI保存义务；向量寄存器和配置允许覆盖；返回vl=8、vtype=0、vstart=0、vcsr=7，不恢复调用前向量配置 |

`struct caller_slot`只有C自然对齐，不能由类型推断16B对齐；调用者须显式对齐slots。接口不检查空指针、长度、别名或CPU能力，不添加未承诺的运行时保护。三参数函数不得强转成旧两参数函数指针。

C8仍使用`void entry(const int8_t *packed_ax, void *output_slots)`，输入连续288B且对齐16B。采用split只改变寻址接口，精确数学结果不变：每行`sum(A[r,k]*x[k]), k=0..31`，范围−520192～524288，适合INT32。后续任何紧密INT32返回改法仍须保留指令完整128位功能核查。

## 4. 最小来源闭包与兼容核查

供体`caller/split/evidence/library-v2/`下四源可作为未来P1运行库输入，本轮只固定来源，不集成执行：

| 文件 | SHA256 |
| --- | --- |
| caller.h | `8f8ebbdfc64f506549b8fcb91700fc80dd91b1fd0a5be64aaed504ebcfa0c38e` |
| split.h | `94ccdc8e6212c0c0d7ef0e8795c8edcdc9a02e173802bea18965bbce5e01e222` |
| split.c | `607026fc8e1c96adc60b6e5c762954a91f963eb589c51655024a8a6b99783a52` |
| kernels.S | `381a2a71c76defee1deb4299229d4e478ab514963638210f14bc2454e071c41f` |

同时固定来源合同/结果/library.json、寻址证书、访问轨迹和固定权重消费者作为审查依据。旧`run.py/library.py`绑定供体T17及额外52项依赖、旧对象与父级工具，**不能原样启动，也不能修改旧pins凑通过**。P1新增当前0f适配器和独立输出，复用当前已有6类packed函数及供体4源。

| 算法ID | 现有packed实现 | split入口 | 函数长度 |
| --- | --- | --- | ---: |
| V | config-reuse/reuse vdot，即当前C8 vdot | split_gemv_8x32_vdot | 656B |
| R0 | S0/basic RVV | split_gemv_8x32_rvv0 | 1060B |
| R1 | S0/reuse RVV | split_gemv_8x32_rvv1 | 740B |
| R2 | config-reuse/basic RVV | split_gemv_8x32_rvv2 | 676B |
| R3 | firstdot/reuse RVV | split_gemv_8x32_rvv3 | 452B |
| R4 | config-reuse/reuse RVV，即当前C8 RVV | split_gemv_8x32_rvv4 | 448B |

本轮已从现存C8、firstdot和S0对象读出6个完整函数，长度/机器码SHA均与供体基准相同。供体split汇编与这些现有源逐条对照，差异只包括前两条参数搬移和X寻址：先保存a2的slots，再令a2=A；X保留在a1，原A+256/264/272/280改成x+0/8/16/24。其余算术/CSR/输出不变。

这是**已有对象＋供体汇编的静态兼容检查**，不是新编译或新ELF证书。P1仍须从实际链接ELF验证全部机器字、允许改动、符号、长度、重定位及真实控制流。当前C8完整对象保留，不靠裁剪或偷换旧库取得对照；所有5种RVV保留，不事后删掉最快者。

## 5. 三个独立测量窗口

所有方法结束时产生同样的128B slots和32B y。wrapper自身捕获参数、栈保存/恢复、间接leaf调用、leaf配置/加载/计算/存储、y提取和wrapper返回均在窗口内。timer自己的48B栈帧与参数捕获在首个cycle读取前，恢复在末个cycle读取后，不在cycles差内；计数器/fence协议不扣空测。

| profile | 窗口前已成立 | packed/C8窗内 | split窗内 | 用途 |
| --- | --- | --- | --- | --- |
| **steady，主指标** | A固定且packed A缓存已准备；当前x已产生 | 仅更新32B x，调用leaf，提取y | 直接读A/x，调用leaf，提取y | 判断固定权重稳态收益 |
| **first，首次成本** | A/x已是8×32/32的有效tile数据，缓存尚未准备 | 准备256B A＋更新32B x，再计算和提取 | 从相同A/x开始计算和提取 | 显式给出首次调用成本，不能替代稳态结果 |
| **native，连续输入控制** | 输入已经连续288B且对齐 | 无复制，直接计算和提取 | a指向前256B，x指向后32B，计算和提取 | 检查已连续输入场景，禁止人为给C8加打包 |

profile的first只指逻辑上未准备packed缓存，不代表冷cache；第0轮“首次”仅是采样顺序，共同conditioning后不能宣称冷启动性能。首次窗口不含模型权重从原矩阵重排、量化、分配；这些输入准备对双方一致在窗外，报告不得称完整QKV或端到端模型。首次和稳态分别直接计时，不用不同N总周期相减推算稳态。计时对照放入同一配对ELF；旧273/299和供体308.5/334.25不能作新分母。

context设置、方法选择、标量golden与guard初始化、共同conditioning和UART均在窗外。steady每次使用已准备的同一A，不能每窗重复制A；本次源x保持x_d，packed缓存的x区在窗外置为x_((d+1)%3)，窗内必须更新到x_d。split对同一额外缓存做相同窗外处理，但被测调用不得访问它。A缓存只在stream开始准备一次，包括conditioning恢复在内都不得重写A；native不执行旧缓存x毒化。不得把测试框架的guard清理或未计时输入准备混称业务成本。

三profile均含六算法×packed/split＝12方法。方法编号固定`P-V,P-R0,P-R1,P-R2,P-R3,P-R4,S-V,S-R0,S-R1,S-R2,S-R3,S-R4`。每窗共同conditioning用相同split-firstdot-RVV和相同规则，其输入/输出缓冲区与被测缓存分开；之后恢复合同指定状态。共同conditioning不证明所有微架构状态完全相同，仍靠锚点和逐窗重放检查。

## 6. 输入与功能资格

正式原始输入固定为C8 `relink/source/cases.h`中的`r4_c_input_3_0/1/2`，各288B；SHA、A/x切片SHA见锁文件，不重新生成旧数据。使用原3组及全−128、全127、混合极值、全零4种明确构造的功能数据；这些是新调用合同功能集，旧模型/旧结果不改。

功能必须包含：

1. 六算法的新旧接口都对独立标量oracle检查8行、全部128B slots及32B y，不能只比较摘要。
2. 每个固定`A_d`连续调用`x0→x1→x0→x2`；packed只在stream开始准备A，返回x0必须正确；随后换A并显式重新准备，覆盖旧A/旧x缓存误用。不同x组合仅作功能压力，不混入原三组性能样本。
3. 分离输入两种非相邻非对齐布局：`(A,x)=(arena+97,+35)`及`(+39,+427)`；性能主布局为`(+96,+32)`。native输入16B对齐。packed内部缓存/slots保持16B对齐。
4. 检查输入与空隙不变、完整输出与guards、packed steady不改A区；split不得访问额外适配工作区的packed缓存，native公共连续A与x是合法源区间而非禁读缓存。按profile解析实际源范围，另检查ABI保存义务及返回CSR。功能中覆盖原统一入站状态和不同合法向量配置；不能说供体已测任意入站状态。
5. 实际ELF轨迹核对：A的256B向量读取覆盖；basic RVV对x重复8次、其他类一次；vdot每调用32条custom；完整slots/y写出；复制字节次数必须符合所选profile。不能只看C源猜编译器行为。
6. 框架低位、高位、guard、输入污染、过期x/错误返回状态等负控必须被判定器检出；另有实际NEMU vd0 bit100负控→同BIN正常恢复→独立正常重放。桩函数主机测试不授ISA/全核资格。

非法指令配置仍沿用0f/R5已合格合同；本包不改ISA，C API不承诺替调用者检查非法地址、别名或VLEN。

## 7. 采样、准入与停止规则

新采样规则在P0先固定，既有供体v2规则和HOLD不改。新应用3%及锚点1%是本队筛选规则，不是赛事评分标准。

每个`profile×dataset`生成一个冻结ELF，共9个待构建镜像；每个ELF内12个方法同硬件/输入/工具/链接环境比较。各镜像6轮：第0轮首次、第1轮预热、第2～5轮正式；偶数轮正序、奇数轮逆序。每轮开始/结束各测一次相同的该profile split-vdot锚点。每镜像84窗＝72普通＋12锚点，其中48普通正式＋8锚点正式。每实现/profile跨3数据集共12正式样本，正反序各6；每dataset×顺序为2正式样本。

先构建并冻结9镜像的共同源码/输入/命令、每镜像完整功能调用清单和最终装载内容，再仅运行`steady-d0`的负控、正常、重放。steady-d0功能、路径、重放及锚点通过，且正反两个顺序格均满足S-V两窗和≤0.97×P-V及10条合格RVV各自两窗和的最小值，才准入其余8镜像。否则停止性能扩展，只记录该镜像实际验证过的功能范围或按规则提出一次有依据的新修订；不得提前授予未执行的first/native wrapper或完整三数据集资格。未改变原镜像/调用计划时保留首轮d0结果，不反复重跑挑样。所有重放用于一致性，不增加统计样本。

| 判定 | 固定规则 |
| --- | --- |
| 锚点 | 每dataset/profile的正式锚点按首尾×正反序分4组，各2窗；组总cycles的max/min−1≤1%（以100×max≤101×min整数比较），否则该profile为HOLD_CONTEXT_VARIATION |
| 明确RVV分母 | 各profile将五类RVV的packed和split共10条实现均列出；以跨三数据集12正式窗总周期最小者作为“最快合格RVV”。它是本次候选集合最低观测值，不声称所有实现的全局最优 |
| 加速比 | 同profile的最快合格RVV总cycles / 所选vdot总cycles；不能跨profile或跨ELF批次拼分母 |
| 稳态性能采用 | S-V对当前P-V和10条合格RVV，在每dataset×顺序格都需至少少3%周期；即S-V两窗和≤0.97×该格各对照两窗和的最小值。执行时使用100×S≤97×B的整数比较，计数差须正且无回绕。此逐格最小值仅作保守筛选下界，不冒充一个固定实现 |
| 接口与算法分开 | 全功能合格但不达3%可保留可选接口能力；若split-RVV更快，保留RVV显式选择。都不自动替换C8 |
| first/native边界 | 分别报告稳定性、周期和代价；只在steady胜出，可限定分离/已准备场景采用，不能推广至native或首次调用 |
| 失败/修订 | 保留所有原样本与失败。最多一次有证据支持的修订，必须新版本/新目录、先冻结合同和镜像；不事后加预热、换慢RVV或松门槛 |

三profile完整矩阵最多9×3＝27次EMU，含最初探针3次；初筛若结束，未执行项写NOT_TESTED。无需新硬件构建/综合/STA；如新源码、工具、地址/布局或调用计划变动，重新明确对应资格，不能只凭叶函数相同继承旧周期。

资源冻结为：EMU单进程串行、threads=1；GNU构建最多2任务，不与EMU/EDA重任务并发。固定EMU参数seed=1、RAM=128MB；正常执行清除XS_NEGATIVE_VECTOR_TARGET，故障夹具执行设为vdot并核实实际命中。每次EMU最多3,000,000 guest cycles、7200秒单调时钟硬上限，每个stdout/stderr原始流最多512MiB；超限终止整组并保留FAIL，不自动续预算。运行前记录空闲资源和输入身份，运行后保留退出码、完整原文/observer/CSR及独立审计。若静态执行计划估算不适合预算，在任何EMU启动前另立修订合同，不能运行后倒改。

## 8. P0完成条件与P1实际入口

P0完成标志：当前版身份与旧证据边界明确；真实生命周期已核实；运行库4源、6算法及现存依赖锁定；ABI/窗口/输入/公平规则已固定；新软件/ELF/结果明确未产生。没有新性能/PPA，原29条版本档案不追加虚构记录。锁中的版本档案SHA是P0时点历史引用；P1后续合法追加新结果不回改本锁，也不据此判断硬件改变。

P1建议新叶目录为`continuation/split-input-v1/`，输出另设独立运行目录。先实现GNU构建与当前0f身份适配，复用4源及6类旧函数，构造缓存公平wrapper和判定器；完成所有主机/对象/最终链接证书与拒错后才运行steady-d0。不得直接执行供体run.py或改共享生成器、旧C8库、firstdot默认、冻结输入及生产RTL。

本合同不是P1执行授权。任何新生产RTL修改前仍须提前说明；本轮不Git提交/推送或发送Issue消息。实际活动与成员保护仍按仓库协作入口核查，P0只对固定快照开展独立本地审查。
