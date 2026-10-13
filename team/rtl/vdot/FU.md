# vdot FU 包装层与控制验证（T07-B）

> 2026-10-13 本机续验收：固定候选 C 的组合及真实 FU 重新生成/编译/测试 PASS；见 [最新报告](../../merge/2026-10-13-zjhwork-into-zufan.codex-review.md)。现已发布到团队及 Fork zufan，见 [发布记录](../../merge/2026-10-13-zjhwork-into-zufan.publication.md)。下一班核对最终 SHA 并记录接收；以下旧日期/证据仍为历史记录。

2026-10-13 已实现真实香山功能单元 [VDot.scala](../../../src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala)，继承 `VecNonPipedFuncUnit`，使用真实 `FuncUnitIO`、`FuConfig` 和 `RobPtr.needFlush`。**带 RTL 断言的 Verilator 验证通过 6 类场景、71,258 个周期。** [归档证据](../../evidence/rtl-fu-20261013/README.md)保存实际命令、版本、摘要、结果和预期拒错日志。

本轮完成独立 FU，不代表指令已经能在 CPU 中执行。尚未新增译码或把 `VDotCfg` 加入 `VFEX4`，NEMU、真实写回仲裁、ROB 异常提交和全核 DiffTest 均待后续集成。

## 1. 实现接口

合同仍为 [`vdot-s8x8-r32-v0.1`](../../spec/vdot.md)。本次没有修改候选机器码、数学模型或 JSONL 数据。

| 内容 | 实现 |
| --- | --- |
| 数据通路 | 复用 T07-A 的 `VDotProducts/VDotReduce`；输入、8 个乘积、最终结果分别寄存 |
| 状态机 | IDLE → MUL → REDUCE → RESP；最多一条请求在途，不在响应握手同拍接受下一条 |
| 正常输入 | `in.fire` 才保存两源和非法标志；基类按同一 fire 保存 ROB、pdest、向量控制和调试字段 |
| 向量配置 | 实际 VL 取第五源；SEW/LMUL/vill/vm/vstart 取请求的 `ctrl.vpu`；不拿 `ctrl.vpu.vl` 代替重命名 VL |
| 支持范围 | VLEN=128、e8/m1、VL=8、vstart=0、vill=0、vm=1；vta/vma/vxrm 不影响算术 |
| 内部操作码 | `VDotOpType.s8x8 = 0`，9 位 FU 操作码；其他内部操作值防御性报非法，与 ISA 编码分配无关 |
| 输出反压 | RESP 中 valid 不依赖 ready；结果、异常和全部响应身份保持到握手或匹配取消 |
| 取消 | 保存的真实 RobPtr 调用 `needFlush`；匹配取消当拍屏蔽响应并释放占用，取消优先于 out.ready |
| 新请求与 redirect | 任意 redirect 当拍不接受新请求；较老在途请求不命中取消时仍继续 |
| 异常 | 返回一次 `exceptionVec(illegalInstr)=1` 的响应，数据置零、vecWen/v0Wen 均为零；保留 ROB/pdest 身份 |
| 复位 | valid/ready 在 reset 期间关闭，状态回 IDLE；复位丢弃未完成请求 |
| 目的类型 | 保留输入选择的 vecWen 或 v0Wen；接受端断言恰好一类目的，非法响应关闭两者 |

`FuType.vdot` 追加在原有枚举之后，保留其他类型编号；加入向量分类。`FuConfig.VDotCfg` 声明非流水、不定延迟、五源、128 位结果、向量/V0 写使能和非法指令异常，且不声明整数/浮点/VL/fflags/vxsat 写入。`needVecCtrl/isVecArith` 已更新，尚未更改执行资源列表或译码表。

如果 E0 接受输入，E1 保存乘积，E2 沿后结果 valid，E3 最早响应握手，E4 最早接受下一条。测试验证该接口时序及无反压启动间隔 4 周期；反压 1/2/7 拍时相应延长。这里不包含调度、读寄存器、写回或 CPU 提交延迟。

RTL 内部断言检查目的类型、合法响应的高位零、异常禁写以及整份响应在反压期间稳定。脚本用 `verilator --assert` 启用断言。

## 2. 一键复现

在完整、已初始化子模块并安装配套工具的香山仓库中运行：

```bash
# 当前代码已发布在共享 zufan；测试绑定自己已核对的完整 SHA
# 已有开发目录先检查未提交工作，再按真实接收 SHA 切换，勿盲目 pull
bash team/scripts/check-vdot-fu.sh
```

自定义输出位置：

```bash
VDOT_OUT_DIR="$PWD/team/out/vdot-fu/my-run" \
  BUILD_JOBS=2 bash team/scripts/check-vdot-fu.sh
```

环境要求同[环境说明](../../docs/environment.md)：JDK 21、Mill 0.12.3、Scala 2.13.15、Chisel 6.6.0、firtool 1.62.1、Verilator 5.052、C++ 编译器和 Python 3.10+。`JAVA_HOME` 和 `CHISEL_FIRTOOL_PATH` 可指向匹配工具。

`vdotFu` Mill 目标依赖真实 `xiangshan` Scala 模块，首次可能编译依赖和主源码；只生成 FU 测试顶层，不生成或编译全核 emu。生成进程堆上限 4G，脚本默认构建并行度 2。生成物保存在忽略的 `team/out/` 中；指定同名输出目录会更新同名日志，保留历史应换目录。

成功标记为 `VDOT_FU_CHECK_PASS`，`check.status` 退出码必须为 0。身份/取消故障注入及 VLEN=256 elaboration 是**预期失败**：前两项必须返回 1 且匹配失败原因，后者必须出现 `VDot requires VLEN=128`。任意不符合预期的失败或假通过都会使脚本返回非零。

## 3. 测试如何判断正确

[GenerateVDotFu.scala](GenerateVDotFu.scala) 只把平坦测试端口连接到真实 VDot Bundle，没有重新实现状态机、点积或取消判断。测试配置取 `MinimalConfig(1)` 的 core 参数，ROB 为 48 项；适配层没有 EXU/时钟门控/ROB 模块。

[fu_test.cpp](fu_test.cpp) 用单个在途事务记录输入快照，并按“接受周期 + 3 是最早响应握手周期”检查时序；没有复制 RTL 的四态状态变量。取消期望用 96 槽位环形距离计算，并限制比较双方处在有效 ROB 窗口，包含两次 flag 翻转方向。算术期望只读原有 T05 数据，不在测试器里重新实现点积。

| 场景 | 实际检查 |
| --- | --- |
| 10,022 组原始数据 | 持续 valid、反压 0/1/2/7 拍、精确启动间隔；完整 128 位、ROB flag/value、pdest、vec/V0 写使能、异常、配置快照与 64 位调试身份 |
| 22 项非法条件 | 其他 3 个 SEW、7 个 LMUL、6 个 VL、3 个非零 vstart、vill、vm、内部 op；异常只响应一次且禁写，测试器仍验证保留的身份 |
| 16 组策略组合 | 四种 vta/vma × 四种 vxrm；ctrl.vpu.vl 故意设置为 255，实际 VL 源为 8，仍应成功 |
| 空闲时 redirect | 同拍 valid 不应被接受，后续无幽灵响应，可以恢复发射 |
| 64 组 redirect | 8 种年龄/自身/环绕关系 × MUL/REDUCE/RESP/RESP 已阻塞 7 拍 × ready=0/1；取消后恢复及较老请求存活 |
| 4 阶段复位 | MUL、REDUCE、RESP、已反压 RESP；复位清除未完成事务，之后恢复正常响应 |
| 5,000 周期压力 | 固定 `mt19937` 种子 `0x20261013`，交替 valid/ready、合法/非法配置、redirect 和 reset；逐拍记账并设 watchdog |

总计 `accepted=11245、responded=10960、killed=271、reset_dropped=14`，最终无在途请求，满足 `11245 = 10960 + 271 + 14`。响应中 90 条为非法配置（22 条定向，加上随机压力中的非法响应）；这些计数不是新增 10,022 组数学向量。

额外在**测试器读回**处注入错误：一次改 pdest，一次在取消时伪造 out.valid；均被外部检查器拒绝。注入不修改生产 RTL，不代表 RTL 故障覆盖率或全核 DiffTest 的故障注入。

## 4. 未覆盖的接入层与下一步

FU 单元测试允许直接注入 VM/vill/vstart 等控制，有些状态在真实译码阶段就会拒绝；因此不能把这批用例直接算作 CPU 陷阱通过。VS Off 检查属于译码/特权路径，本 FU 没有 mstatus 输入。

以下仍需集成验证：准确 custom-0 译码和单 uop、源/目的重命名及 v0 物理路径、VL 唤醒依赖、OG2 重试、VFEX4 busy/时钟门控和其他 FU 竞争、写回仲裁、ROB 精确异常、CSR 副作用，以及 NEMU 协同验证。当前 `v0Wen` 单元通过只证明响应控制位，不能替代 v0 寄存器通路测试。

下一步按计划推进 NEMU 独立扩展与 T10 译码/VFEX4 接入，并先回归 hello/vadd，再执行真实 vdot 程序及 DiffTest。原“全部开发保持 zjhwork”是合并前历史用法；发布并接收后改为共享 `zufan` 独立工作区错峰推进；核心接口合并前仍需另外两名成员人工复核。
