# Booth 候选：有限独立判断

## 结论

**支持做一个 9bit recode＋独立 neg carry＋20bit 两行的局部 FU/cost 点。** 它减少进入 P 前压缩树的部分积工作量，是不同于 Pgroup 排序的新结构机会。10bit 原构造正确，但独立 carry 允许直接简化成 9bit；无需同时维护或扫描两种实现。此结论不声称新 RTL 已正确、面积已下降或 STA 已改善。

建议保持首席提出的 20bit 两行和原 Finish20 模和方案；不把另一个“19bit 堆＋最后翻转符号位”数学等价表示也发展成候选。后者要改变 R 的表达，当前没有必要。

## 1. 全空间算术推导

Booth digit 表为 `000→0,001→1,010→1,011→2,100→−2,101→−1,110→−1,111→0`，窗口为 `b[2j+1:2j−1]`、`b[−1]=0`，所以四项满足 `sum(d[j]*4^j)=signed8(b)`。

令 `m=abs(d)*a`。在独立补偿位加入以前，取反后的有符号数是 `q=m`（n=0）或 `q=−m−1`（n=1）。由于 `m∈[−256,254]`，始终有 **q∈[−256,255]**，恰好可用 signed9。将 q 的 bit8 翻转后按 UInt9 解释为 B，则 `B=q+256`，故完整整数和 `B+n=d*a+256`。

关键极值：`a=−128,d=−2` 时 `q=255,B=511,n=1`，完整和是 **512**。它不是可截回 9bit 的行内结果；n 必须在 column `2j` 独立进入公共压缩堆。先对行做 9bit `+1` 再截断会把这项变成 0，构成实际反例。

零码可以规范化为 n=0，也可以使用便宜的原窗口最高位作为 n，令 `111` 为“逐位取反的零＋1”。两者都正确，但取反与 carry 必须使用同一个 n。选择零时全部 magnitude 位（包括符号位）均为 0；不能保留 a 的符号位，也不能只关闭零码 carry 而保留取反。

每 lane 的固定偏置是 `256*(1+4+16+64)=21760`；八 lane 为 174080。增加 **350208＝0x55800** 后，半堆准确等于 `S8+2^19`。原 10bit 方案相应为每 lane 43520、八 lane 348160、加 176128，同样成立。

真实范围为 `S8∈[−130048,131072]`、`S16∈[−260096,262144]`。feature0 对两行分别取 low19 后作模 2^19 和、按 signed19 解释，得到 S8。feature1 保留完整 20bit 位模式，两半总偏置为 2^20，在四行模 2^20 和中消失；signed20 足以表示 S16。

feature1 的 dot8 高半必须注入**两行合计 2^19**的 biased zero。若继续把高两行全清零，低半真实结果 0 时输出会成为 signed20 的 −524288。不得沿用旧 signed19 row 扩展规则；不要求新 row0/row1 各自具有某个固定符号位拓扑。

## 2. 已做的有限验证

- 本专家纯整数程序对 9bit、10bit 各穷举全部 65,536 对 signed8 输入；逐项和逐 lane 恒等式均成立。另检查原最高位负号控制产生的 24,576 个 `111` 负零项。
- 原生助手独立、不读取本程序，也穷举了 65,536 对输入及 262,144 个 digit 项，覆盖负零，未找到反例。
- 八/十六 lane 结论由逐 lane 恒等式、加法闭合与上述精确范围推出；程序另做了 50 个双半/模式边界组合。没有声称穷举 2^128 个操作数，也没有将整数模型当成生成 RTL 证明。

脚本 `booth_math_review.py`：5570 B，SHA256 `df1c4791ca6469ad56eba3563fb7778f6976a7a0ea6a8b7a5c8ce09e924b29e5`。

输出 `booth_math_review_result.json`：6456 B，SHA256 `64677b4994192edd11c62b42a77a3e1dbfd10bbb73f9fe913b1ac3899b8ea9c8`。

## 3. 结构机会与真实时序风险

按冻结源相同的固定压缩日程，仅做高度/FA/HA 计数：

| 每半 8 lane | 堆初始位数（含独立 carry 和常量） | FA | HA | 有工作的压缩层 |
| --- | ---: | ---: | ---: | ---: |
| 已有 BW | 514 | 477 | 17 | 10 |
| 10bit Booth 数学模型 | 356 | 318 | 21 | 8 |
| 9bit Booth 数学模型 | 325 | 288 | 20 | 8 |

BW 行是既有实际结构证明；两个 Booth 行是本文的结构模型，**不是已生成或映射结果**。9bit 比旧 BW 少约 39.6% 的模型 FA，足以支持一次有限试验，但绝不等于整 FU 面积减少 39.6%。新重编码、one/two 选择、条件取反、控制扇出和缓冲要付出代价；10bit 多出的互补高位也可能被综合优化。

已读取原 prefix 实际报告：feature1 I2R **1.163662 ns / −0.238006 ns slack**，R2R **1.079437 ns / −0.156976 ns slack**，面积 **17965.374**。I2R 输入网络存在两级缓冲，其输出 cap 分别为 14.223768/17.899281 fF。Booth 的共享 neg/one/two 驱动多位部分积，新的负载与 slew 可能吃掉少两层压缩的收益。独立 neg carry 避免行内进位链，应保留。

Pgroup 的实际结果已经显示源级依赖深度减少并不保证 I2R 改善；其连续八个 XOR/XNOR 单元弧约 0.499031 ns。不能再用“更少门级/宏项”直接预测新延迟。

R 仍是两次压缩＋最终前缀，没有结构上的必然提速。P 表示、常量和连接变化可改变 R 的实际映射，因此需要看本点已有合同中的完整路径类别和 slack，不能只比 I2R arrival 或 ABC 内部 delay。P 名义宽度增加 4bit 不等于一定增加 4 个映射 DFF；哪些位成为常量，以实际生成/映射为准。

## 4. 保持的工程边界与取舍

128bit 接口、dot8 忽略高64bit、dot16 全16个 signed8 lane、P/R 两槽、E2/II1、同步 valid reset 均保持。两行和该事务的 pCtrl/pPerf 同一 `io.in.fire` 捕获；dot8 biased-zero 也在 P 捕获处完成。move 只读旧 P，stall/kill/flush/reset 和非法事务的结果置零沿用原事件关系；禁止 R 使用随后到达的 isDot16 修正旧请求。

按首席现有局部算术/FU/cost 合同验证实际新生成物即可，本审查不新增整核或应用前置门槛。如果实际面积/最坏 STA 组合没有目标相关收益，保留原 prefix 并结束这一路，不自动扩大排序、位宽、映射参数矩阵。若有收益，再由首席决定是否值得进入父级与整核，不把局部 PASS 自动转移。

E2/II1 保持意味着这里直接追求面积和时序余量，不能单凭这个改动声称应用 cycle-count 降低或全核频率上升。

## 5. 原始依据与范围

源缓存（已读取并实算 SHA）：`/workspace/scratch/f9116701fd09/verification/prefix-pgroup-candidate-01/base/source/`：

- `VDotDatapath.scala` 8780 B，`1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb`。
- `VDotElastic.scala` 8999 B，`912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92`。

原结果：`/workspace/scratch/f9116701fd09/source-review/prefix-candidate-v1/actual-result.json`，205865 B，`a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0`。它给出旧 512PP/477FA/17HA、全10层结构及 cost 数据。

原时序抓取：`/workspace/scratch/f9116701fd09/verification/prefix-critical-path-review-01/timing-paths.json`，31261 B，`2fef6e0f136b0065cb726aa45df4caa186b9027e359790a09d9b531ed06456f3`。其中原 f1 i2r 文本6785 B、`f4a78f9a442534ba299c73a4e4f9d7a9229491e8b8efc8877f770df329c53476`；r2r 文本6579 B、`7d15b374b37ff44718c11ac75e8e2149d31a8b8fe2fb2e62762b8290755412d4`，本次从 JSON 取出的 UTF-8 文本均重新散列吻合。

上述时序来自既有 Windows `runs/dot16-prefix-20261107-main/archive-01/raw.zip`，30765219 B、`a711b159fdc6e92805f8c4760ee7d72fd1382691c8c797809382b8572391b0ab`。本次没有重新下载或验证整个 ZIP。

Pgroup 取舍：`/workspace/scratch/f9116701fd09/verification/prefix-pgroup-candidate-01/review/TIMING_DECISION.md`，8411 B、`630a65f751fcbfbbcb6acab4b9a33e0b9c532c03eb6f4d2bf6f603fb71182acf`。

外部原始论文核对仅使用其精确 Booth 背景部分：K. Kim 等，JSTS 19(5), 435–445 (2019)，Section II 的精确编码、独立负补偿项及编码开销说明，https://doi.org/10.5573/JSTS.2019.19.5.435 。本文没有采用该文后续的近似乘法方案或引用其 PPA 收益；实际候选正确性依据是以上自行推导和有限穷举。

本次只读冻结源/结果并做轻量云端整数运算；没有 PC、EDA、构建、EMU、主仓、Git index、官方代码或候选 RTL 写入。
