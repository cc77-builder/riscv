# C2-G0：父级空闲时子 DIV 必然 ready 的控制证明

2026-10-25（UTC+08:00）。**结论：C2-G0 在当前固定实现、有效初始化及正常同步接口条件下通过，可进入 C2 候选设计。** 本轮完成的是源码绑定的控制抽象归纳证明、细状态包含检查和独立审查；没有修改 RTL，没有执行新 RTL 仿真、全核、NEMU、综合或 STA，也未上传 GitHub。

生产源码保持 0f12df675378556670afd0dd2153f47fcb330610，原 EMU SHA 为 2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。仍采用 O2＋H1＋DIV 取消关钟修复。C1 仍被否决，不因本轮 G0 通过而恢复采用。合同见 [CONTRACT.md](CONTRACT.md)。

## 1. 究竟证明了什么

记 B 为 ExeUnit 中寄存的 divBusy，RI 为 VIDiv.io.in.ready，RF 为 VFDivSqrt.io.in.ready。在有效初始化后、非复位的稳定采样时刻：

~~~text
!B => RI && RF
~~~

B 不等于组合 elasticDivOccupied。后者原本就是 B OR divOutValid OR !divReady，若用它的否定推 ready，会变成定义恒真，无法支持优化。本轮用独立更新的 B 与真实子控制状态证明，未以目标性质过滤状态。

实际门控启动对应的接受谓词为：

~~~text
P_j = inputValid && selected_j && !B
      && !intOutValid && !fpOutValid
      && !VDotOccupied && !flush && !reset

fire_j = P_j && RI && RF
~~~

组合模型在全部可达状态逐转移检查 P_j 与实际 DIV fire 相等。由不变量，P_j 成立时 RI/RF 已成立，因此可提出“仅在门控启动项使用 P_j”的候选。**实际 parent.ready、child.valid、事务接受、ROB 捕获与结果协议仍按原实现保留。** 本轮没有将该候选写进生产源码。

证明范围是控制安全性：不依赖除法何时完成，不证明除法一定结束，不证明算术结果、物理门控毛刺、异步复位恢复/移除时间或新版本面积时序。

## 2. 复位边界已按真实配置闭合

### 实际全核：共享异步复位

以前的成本／父级夹具是同步复位，不能直接代表全核。本轮将当前 EMU 与 10 个相关生成 RTL 逐一比对先前冻结的构建清单，11/11 身份相同，source_commit 为 0f12df6，配置为 MinimalConfig／observe。

真实层级 Backend → ExuBlock_2 → ExeUnit_17 → VIDiv／VFDivSqrt → 内部 DIV／SQRT 直接传递同一 reset。父 B、两份 hold、整数 top FSM、两个浮点 lane 内的 DIV 和 SQRT 都使用 posedge reset 异步复位。Backend 中 TE 为 0。

所以 shared reset 有效断言并稳定后，不需要门控时钟边沿就能建立：

~~~text
B = HI = HF = 0
integer = IDLE
lane0.DIV = lane0.SQRT = lane1.DIV = lane1.SQRT = IDLE
RI = RF = 1，所有 DIV outputValid = 0
~~~

ROB／数据寄存器初值不必相等；空闲时不使用其保存身份，下一次真实接受再共同捕获。模型从八组不同 ROB 历史颜色开始，未隐含假定它们初始相同。

### 同步夹具：有效初始化与后续动态复位分开

同步夹具必须先给所有子 FSM 有效复位边沿，现有 TE=1 bootstrap 可以提供。首次复位之前若子 FSM 未初始化、门关且 TE=0，确有 B=0 但子 not-ready 的环境反例；它被保存，不能靠仿真器默认初值消除。

**已经有效初始化后**，动态 reset 即使 TE=0 也保持不变量：活跃子由旧 hold 保留边沿，非活跃子本来已 idle。主模型分别检查了“每次复位 TE=1”的原夹具合同与“bootstrap 后任意 TE”的更宽环境，两者均通过。

详见 [复位与身份审查](evidence/review-reset/REPORT.md)、[构建身份](evidence/review-reset/generated-identity.json)、[初始化反例](evidence/review-reset/reset-edge-probes.json)。

## 3. 接收、完成和取消为何保持不变量

| 事件 | 父级行为 | 子单元行为及必要条件 |
| --- | --- | --- |
| 接受整数 DIV | 父 B、整数 hold 置位，捕获 ROB | fire 自身开启接受边沿，VIDiv 捕获同一 ROB，integer 离开 IDLE；浮点保持 IDLE |
| 接受浮点 DIV／SQRT | 父 B、浮点 hold 置位，捕获 ROB | 两个 lane 同时启动相同类型；每 lane 未选中的另一引擎保持 IDLE |
| 正常推进／反压 | B 与相应 hold 保持 | 允许任意迭代时长，各 lane 可不同步；输出等待不会自行释放父级 |
| 整数输出 fire | 父 B 与整数 hold 清除 | top 同拍回 IDLE；16 个内部子已在该拍或更早回 IDLE |
| 浮点输出 fire | 只有两个 lane 都输出且外部 ready 才释放 B | 两 lane 收到同一个 finish_ready；先完成的 lane 保持输出态，等另一个完成后同拍回 IDLE |
| 匹配取消 | B 清除；hold 在边沿后清除 | 活跃子使用同一保存 ROB，得到相同 needFlush；旧 hold 保留取消边沿，各子同拍回 IDLE |
| 无关 redirect | 不清 B／hold | 不误取消活跃事务；flush.valid 同时禁止新接受 |
| reset | 按已核实的复位域清 B／hold | 真实全核异步清子；同步夹具按有效边沿清子 |

父子 ROB 相等来自同一接受边沿和同一输入：parent divRobIdx=RegEnable(inputROB,divAccept)，child outCtrl=DataHoldBypass(inputCtrl,childFire)，分派保证父子 fire 一致。忙期间不接收第二个 DIV，身份不能被覆盖。忙子 wrapper 选择保存 ROB；空闲子可能使用当前输入 ROB，但 flush 只让其继续 idle。

对固定 MinimalConfig 的 128 个 ROB 编码 × 128 个 redirect 编码 × valid × flushItself，共 65,536 项比较验证了相同身份的取消谓词一致性，覆盖 flag 不同、自身取消等情况。结构论证来自同输入／同表达式，不把抽象模型的两个 ROB 颜色说成真实 ROB 只有两个槽位。

## 4. 整数内部与浮点细状态的覆盖

整数 VectorIdiv 是 idle／divide／output 三态。16 个内部子为 8×I8、4×SRT16、2×SRT32、2×SRT64；top.finish 必须等待全部内部 outvalid。top 进入 output 后，内部子获得 out_ready，即使外部反压也会先清内部状态，结果由 top 寄存器保持。

独立整数检查保留任意一个内部子细 FSM，用非确定信号表示其余子是否全部完成，且 finish 必须包括当前代表子 outvalid。该论证适用于每个子实例；SRT 位宽只影响被放宽的算术完成条件。详见 [整数审查](evidence/review-int/REPORT.md)。

浮点保留每个 lane 的 DIV 六态、SQRT 四态，独立完成时刻与初始化分支。wrapper.ready 是四个引擎的 IDLE 条件；wrapper.outValid 是两 lane finish 的 AND，而每 lane 内部 finish 是 DIV／SQRT 的 OR。模型证明同 lane 两操作不会重叠，输入 opcode 后续变化不会启动未选中的引擎。

本轮修正上轮范围描述：固定 VFDivSqrt 的 is_vec_i 恒为 true，生成 RTL 已裁去标量 DIV／SQRT 特殊值直接早完成分支。SQRT 的一拍／两拍初始化选择和独立迭代等待仍被覆盖；特殊值不会绕过固定实例的 ready／finish 状态规则。**这是 SQRT 控制覆盖，不是 SQRT 算术仿真。** 详见 [浮点审查](evidence/review-fp/FP_REVIEW.md)。

## 5. 机器检查及独立审查结果

主模型把各引擎压缩为 I（空闲）／R（运行）／O（输出）；R 每拍都允许保持或完成，比真实数据路径允许更多行为。没有固定迭代次数、没有公平性假设。算法遍历到状态集合闭合，检查全部后继；不是有限拍随机测试。

| 检查 | 状态／输入规模 | 结果 |
| --- | --- | --- |
| INT＋双 lane DIV/SQRT＋父 B／双 hold／ROB，真实异步复位 | 48 可达状态、33,600 转移 | PASS |
| 同步夹具，复位时 TE=1 | 48 状态、31,680 转移 | PASS |
| 同步夹具，已 bootstrap 后任意 TE 动态复位 | 48 状态、33,600 转移 | PASS |
| 从任意合法控制编码建立异步复位基例 | 1,944 初态组合 | PASS |
| FP 细状态模型，sync／async 分别 | 各 38 状态、11,184 转移 | PASS |
| FP 细状态到实际主模型 unit_next | 640 输入组合、660 具体后继 | 全部包含 |
| 整数 top 到主 I/R/O | 384 输入组合 | 全部包含 |
| 任意 I8 内部代表子 | 9 状态、10,368 转移 | PASS |
| 任意 SRT 内部代表子 | 10 状态、11,520 转移 | PASS |
| 固定全核 ROB 谓词比较 | 65,536 项 | PASS |

这些数字属于不同抽象和重复场景，不能相加成 RTL 测试覆盖率。最终主结果见 [system-proof-02.json](evidence/system-proof-02.json)，实际主函数的细化包含见 [composition-check.json](evidence/composition-check.json)。首轮 system-proof-01 与对应源码快照保留；第二轮增加了任意 TE 的同步动态复位检查，没有丢弃失败或择优。

五种主模型变异全部出现 **B=0 但子 not-ready** 的目标反例，而非只触发辅助断言：

| 人为破坏 | 最短反例长度 |
| --- | ---: |
| 取消当拍提前断钟 | 2 步 |
| 浮点漏处理取消 | 2 步 |
| 浮点捕获错误 ROB | 2 步 |
| 两 lane 输出汇合错误改成 OR | 3 步 |
| lane1 漏复位 | 2 步 |

这些是检查器的负控，**不是当前 RTL 的合法反例**。另外保留无有效 bootstrap 的环境反例。整数与 FP 局部模型也各自做了负控，不将相同错误重复计为独立 RTL 验证。

[独立主模型审查](evidence/review-int/SYSTEM_MODEL_REVIEW.md)确认：目标性质没有被用来修复／过滤状态；busy 与 hold 独立更新；接受约束来自原 RTL；ROB 颜色只抽象至多一个活跃 DIV 和当前输入的相关身份；VDot 占用可任意变化，属于更宽的抑制环境。此审查由 Agent 完成，不代替团队成员人工确认。

## 6. 对 C2 的具体决定

**G0 已闭合，建议进入有界 C2 设计与实现阶段。** 新方向是只将门控启动项从 fire_j 改为已证明等价的 P_j，以切断门控启动对 RI/RF 的组合依赖；不移除真实接收侧的 ready 检查。

若沿用 C1 的 busy／owner 状态编码，仍须在独立候选中组合验证，并相对获保留的 0f12df6 比较。C1 局部功能结果和本轮 G0 不能代替新候选回归。

下一轮在修改 RTL 前先说明具体文件与表达式，锁定 C2 合同。随后按序：

1. 只做最小门控改写，保留接受／输出／ROB／取消清理边沿。
2. 真实 FU／父级严格验证，补实际 SQRT、双 lane 不同步、复位与取消交叠刺激；完整 128 位及原负控继续保留。
3. 做同约束父级面积与五档 STA，保留 ready、VDot、各 ICG 的原筛选门槛。
4. 筛选通过才构建新身份全核与 NEMU 回归，再做同镜像周期比较。失败则关闭候选，保留现版。

本轮没有证明 C2 能提升频率、面积或加速比，未开始 C2 RTL。下一次综合仍可能因其他控制来源或全局映射重排失败；G0 只解决能否安全去掉该门控 ready 依赖的问题。

## 7. 证据与复现

- [主系统控制模型](system_model.py)；[实际组合包含检查](check_composition.py)。
- [源码与结果审计](reviews/final-audit.json)；[归档清单](evidence/manifest.json)。
- 原始输出根：/home/riscv/riscv-lab/o2-c2-g0-20261025。
- 全部原始命令／退出码随 evidence 保存。复现输出必须选择新文件名，脚本拒绝覆盖已有结果。
- 本轮只读 Issue 到评论 6395289906，没有 GitHub 写入；队友工作区和旧封存保持原样。
- 最终审计核对65份去重输入，44份证据载荷共251,126字节；身份、命令退出码与模型层级均通过。Windows 本地交付回执位于 reviews/。当前生产源码仍为 0f12df6。

在仓库根运行主检查示例（输出改为新的临时位置）：

~~~bash
python3 -B team/optimizations/o2/r3-div-gate/c2-g0/system_model.py \
  --output /tmp/c2-g0-system-proof-new.json
python3 -B team/optimizations/o2/r3-div-gate/c2-g0/check_composition.py \
  --fp-dir team/optimizations/o2/r3-div-gate/c2-g0/evidence/review-fp \
  --output /tmp/c2-g0-composition-new.json
~~~

这是有源码审查和机检支撑的控制证明；未进行全部 RTL 自动形式等价、物理复位签核、新 RTL 数值／全核或 PPA 验收。
