# C2：DIV 门控启动去 ready 依赖——本地实现与局部验证结果

2026-10-25（UTC+08:00）。本轮结论：**C2_LOCAL_PASS，进入面积/时序筛选候选；尚未采用。** 已完成生产 RTL 实现、独立 FU、真实 VFEX4 父级和新增 SQRT/双 lane/TE0 动态复位验证。未运行本版全核/NEMU、周期比较、综合或 STA；未上传 GitHub、未写 Issue。

当前获保留的主检出仍是 O2＋H1＋DIV 取消关钟修复 0f12df6，原 EMU 保持。C1 的既有时序否决保持；C2 是把 C1 busy＋owner 结构与新的门控启动式组合后重新验证的新候选。

## 1. 改动及固定身份

本轮修改前已说明具体改法，并冻结 [CONTRACT.md](CONTRACT.md)。唯一生产文件为 ExeUnit.scala；生产候选在独立 WSL 原生 Git worktree。

| 对象 | 完整身份 |
| --- | --- |
| 保留基线 | 0f12df675378556670afd0dd2153f47fcb330610 |
| 结构起点 C1（被否决） | 3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66 |
| 新 C2 本地源码提交 | 6704ce3502a7235cdb81697638c01ed23f6914f6 |
| C2 ExeUnit.scala SHA256 | febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6 |
| 基线 ExeUnit.scala SHA256 | fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa |
| 基线到 C2 的完整生产补丁 | [c2-production.patch](c2-production.patch)，包括 busy/owner 和本轮启动式 |

仅对 O2/VFEX4 的整数 DIV 和浮点 DIV/SQRT 改写门控：

~~~text
P_j = input.valid && selected(j)
      && !divBusy && !divOutValid && !VDotOccupied
      && !flush.valid && !reset

E_j = P_j || (divBusy && ownerIsThisFu)
~~~

P_j 不再经过 child.ready、fire 或派发 allowInput 的共享组合链。实际 parent.ready、child.valid、接受/ROB 捕获、divBusy 的取消/完成/接受优先级及写回通路保持既有协议；独立审查确认派发/输出尾部相对 0f 逐字节不变。owner 只在实际 divAccept 时更新。

保持项不受 flush/reset 组合遮罩：有占用时仍送出清理边沿，下拍释放后关钟。最终 ckAlwaysEn 优先级保留，VDot 门控和其他执行单元不在改写范围。新增运行断言检查 P_j==实际 child.fire 及 !divBusy=>两 DIV ready；断言不驱动控制，也没有代替外部测试。

## 2. 本轮真实运行结果

| 层级 | 实测结果 | 结论 |
| --- | --- | --- |
| 独立 FU | 22 定向＋10000 固定随机，完整128位；31499拍，23311接受=22460响应+739取消+112复位丢弃 | PASS |
| FU 吞吐 | 10021个连续 II=1 间隔；首响应2拍 | 只证明局部合同，不是应用 cycles/dot |
| 原真实父级 | 13组、35075拍；13611接受=13122响应+426取消+63复位丢弃 | PASS |
| 原父级即时关钟 | 48个取消恢复窗口、144个紧接空闲采样，额外脉冲0 | PASS |
| C2 补充真实父级 | 6组、115个定向场景、2959拍；213接受=141响应+54取消+18复位丢弃 | PASS |
| C2 补充即时关钟 | 54个取消窗口、162个紧接空闲采样，额外脉冲0 | PASS |
| 观察负控 | FU 4项＋原父级16项真实运行的 C++ 观察故障；新增7项离线日志变异，全部拒绝 | 分层 PASS；不是 RTL mutation |
| 生成结构 | 两条真正 DIV ClockGate.E 组合锥不含 ready/allowInput/childFire；同检查器对旧 C1 按预期拒绝 | PASS |
| 全核/NEMU、应用周期、面积/STA、功耗、整核 Fmax | 本 C2 身份未测 | NOT_TESTED |

原父级包含完整128位三路写回、ROB/pdest/VPU/perf身份、非法配置、反压、取消、九类 FU 切换和20,000拍随机混合。最终独立审计核对1119份去重输入、1298次源码哈希和126个依赖；C2、C1、原关钟修复三份35075拍日志逐字节相同（SHA256 a38e8d806dc84c46b16af6f3c17323ee5f404ba3eb221d94fa15e127bf22ee6d）。旧修复运行当时是4669c4基点＋工作树补丁，398份生产输入与后来的0f逐源相同，不能把旧运行HEAD伪写成0f。相同结论来自完整输入与轨迹比较，不只比较总计数。FU 和父级重用相同10,022个向量，不累加成两倍唯一数值用例。

### 新增的115个场景

| 场景 | 数量 | 实际覆盖 |
| --- | ---: | --- |
| SQRT数值＋反压 | 15 | 5组向量×0/1/7拍反压；FP32正常/subnormal/特殊值及FP64 |
| SQRT取消 | 48 | 两种lane偏斜×计算/单lane完成/双lane输出/反压×ready两值×三后继FU |
| SQRT ROB | 14 | 年龄、自身不取消、flag边界和完整wrap；计算/反压两相位 |
| TE0动态reset | 20 | INT DIV/FP DIV/SQRT×三相位×取消交叠；另两个空闲场景 |
| SQRT/FU切换 | 18 | 对VDot/整数DIV/FP DIV双向切换×三档反压 |

FP64 的最小正 subnormal 与 9 交换两 lane，实际观察 lane_finish=1 共27拍、lane_finish=2 共56拍；在偏斜瞬间取消两方向各6例，未提前合并输出。不是用两 lane 预计相同的 FP32 初始化虚构覆盖。正有限 SQRT 常量以 Fraction 精确平方核对12项；实际 RTL 运行核查全部128位结果与 flags。包含 -1 的 canonical NaN/NV、±0、+∞；不声称穷尽 IEEE 舍入或全部浮点数值。

原父级同步测试夹具先 TE=1 有效 bootstrap，之后新增20个动态reset场景全部 TE=0（40个reset采样拍）。该条件与 G0 一致；不把它宣称为 TE0 同步冷启动或全核异步复位电气签核。

## 3. 观察与结构证据的边界

[补充测试合同](parent/TEST_CONTRACT.md)冻结时标为草稿，实际运行成绩以本结果及封存日志为准。新增观察只对新生成的测试顶层增加只读层级输出：两lane ready/finish和真实divBusy。保存修改前top与逐模块pre/post SHA，唯一变化为测试top；55份生产 ExeUnit/VIDiv/VFDiv/SQRT 等SV/V模块保持逐字节不变；归档说明的计数称谓澄清见[附注](reviews/annotation.md)。此带观察测试top不用于后续面积/STA。

原严格schema1逐拍replay完整保留。补充checker只另行定义六组覆盖，不放宽ready、时钟、ROB、生命周期守恒；7种坏观察均被拒绝。payload由真实C++ scoreboard检查，离线控制replay不冒充第二次载荷计算。

[check_generated_cone.py](check_generated_cone.py)跨模块追溯实际ICG.E至寄存器Q/顶层输入，遇到未解析、多驱动、组合环则失败。两DIV各41节点、13边界；历史寄存器D依赖不算当前周期组合锥。旧C1的同检查器负对照检出真实ready/fire路径。这是生成结构审查，不能替代映射后STA或完整RTL形式等价。

## 4. 复现、失败与封存

候选本地根：/home/riscv/riscv-lab/o2-c2-readyless-20261025/repo。原始输出在其上级的 fu-01、fu-02、parent-01、supplement-01。主检出材料位于 team/optimizations/o2/r3-div-gate/c2/。

原验证命令（在候选完整源码根运行，输出必须为全新绝对目录）：

~~~bash
python3 -B team/optimizations/o2/run_rtl.py fu /absolute/new/fu-output
python3 -B team/optimizations/o2/run_rtl.py parent /absolute/new/parent-output
python3 -B team/optimizations/o2/parent/check_trace.py \
  --log /absolute/new/parent-output/result.log --output /absolute/new/parent-replay.json
python3 -B /absolute/materials/c2/parent/run_c2_parent.py \
  /absolute/candidate/repo /absolute/new/supplement-output
python3 -B /absolute/materials/c2/check_generated_cone.py \
  --rtl /absolute/new/parent-output/rtl --output /absolute/new/cone.json --expect pass
~~~

复现新候选可取得0f完整源码/锁定依赖后，在独立工作区应用完整c2-production.patch；也可使用本地候选提交。候选源码提交不包含本次主检出新增的材料目录，补充测试入口须使用上述材料绝对路径。不能把候选命令直接在仍为0f的主检出运行并称为C2。

本轮递归依赖126项均与Git pin一致。首轮FU在编译前因 src/main/resources/aia 未初始化而被预检拒绝；恢复遗漏的嵌套gitlink后，使用新fu-02输出通过，fu-01失败原样保留。补充脚本草稿的include路径语法检查失败、结构解析器首轮错误亦保留；不计为生产RTL失败，也不删掉失败记录。

封存入口：[evidence/20261025-local/manifest.json](evidence/20261025-local/manifest.json)。保留原始命令/退出码、日志、源码与依赖身份、生成RTL、测试源码、gold向量、补丁、审查和失败。大型文本确定性gzip；obj、缓存与可执行文件不入材料，二进制SHA和大小保留。核验时同时复算压缩载荷及解压原文SHA。375份载荷共32,771,655原文字节，压缩后5,218,859字节；manifest SHA256为5fe7ea1cd978cf14ef371380a51e64d942673e1c62c7ac3748698418237b1428。Linux与Windows原生Python均已对封存原文重新执行严格父级replay、补充覆盖和7负控，全部通过；见[Linux回执](reviews/linux-archive-check.json)与[Windows回执](reviews/windows-archive-check.json)。版本数据另见[统一档案](../../../../docs/version-data-ledger.md)。

## 5. 下一关卡与采用条件

下一步是本C2与保留0f的**同约束父级综合＋五档STA**。按冻结合同：控制D最差nominal≤1.737526ns；父级/VDot/ready/各ICG指定路径不得超过基线101%，原正slack门控保持非负；面积≤284614.946×1.001，未知单元0。五档完整记录，不只挑有利结果；这是内部筛选线，不是官方评分标准。

成本筛选通过才进入C2新身份全核/NEMU、同镜像周期及必要组合回归；失败则保留0f，记录C2否决与原因。当前没有新的加速比、面积收益或频率提升结论。以后每轮将真实数据追加到版本档案，失败、退化与未测层级同时保留。
