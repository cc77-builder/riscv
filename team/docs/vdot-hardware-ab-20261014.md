> 历史硬件候选报告，实验包未启用、未晋升。正文关于RF/旁路直至融合乘法的组合路径描述已由[时序前审](t12-timing-precheck.md)纠正：`NewPipelineConnect`存在真实数据寄存边界。当前仅合入软件/验证成果，硬件晋升要求见[整合报告](t12-zufan-integration-20261014.md)，以下历史结果不改写。

# VDot 硬件性能审查与输入级融合实验

版本：0.1；2026-10-14；状态：审查完成，模型/工件检查通过，真实 RTL A/B 阻塞，候选未晋升。模板：engineering-docs / general。

## 1. 范围与当前结论

固定实读基线 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`。本任务独立于 T12 全核/RVV 主实现；只读 Windows 发布 clone 干净，已创建 `hardware/hardware-repo` 独立副本。未写 implement、旧 WIP、共享旧 Linux repo、NEMU 或公共分支，未 Push。

VFEX4 不定延迟 busy **不支持响应握手同拍接受下一条**。仅改 FU piped=true 或加队列不会解除它。当前 E0 接受、E2 沿后 valid、E3 响应、无背压 II4 是局部时序，不能代替全核发射、RAW/退休周期或频率。

只选择 input-stage fusion：in.fire 同沿锁存八个乘积，跳过仅为下一拍乘法准备的输入寄存级，保留平衡归约和结果寄存。源码预测 E0 乘积、E1 沿后 valid、E2 响应、II3；**尚未实测，不能宣布收益**。它可能少占用共享 EXU 一拍，但会把乘法加入外部旁路/输入采样路径。

生产源码字节保持不变。候选仅为 [独立 patch](../evidence/vdot-hardware-ab-20261014/experiments/fuse-input-stage.patch)，应用后构造参数 `experimentalFuseInputStage=false` 默认关闭；只有专属 FU elaboration 的 `--fuse-input-stage` 选 true。未打开全核生产路径。

## 2. 已确认输入与约束

内部合同仍为 [ISA](../spec/vdot.md) 与 [RTL接口](../spec/rtl-interface.md) 的 `vdot-s8x8-r32-v0.1`；未替代官方澄清或人工签字。

| 项目 | 保留要求 |
|---|---|
| 算术 | 低八个 signed int8，16位乘积→17→18→19位平衡加法树，和范围 -130048…131072 |
| 目的 | 低32位补码、高96位零、完整128位写回；不用oldVd/tail/Mgu合并 |
| 合法域 | VLEN128、e8/m1、实际重命名VL=8、vstart=0、vill=0、vm=1；四种vta/vma均合法 |
| 身份 | in.fire快照RobPtr含flag、pdest、目的类型、vpu/调试字段；单请求 |
| 取消 | 真实RobPtr.needFlush，环绕与flush-self；取消优先响应；redirect拍禁止新输入 |
| 异常 | 非法一次有身份响应、illegalInstr、零数据/禁写；精确trap仍需全核验收 |
| v0/别名 | 保留既有重命名/旁路/V0依赖；FU控制位通过不能替代真实寄存器路径 |
| reset/背压 | reset抑制ready/valid并丢弃在途；未取消阻塞响应及全部身份稳定 |

授权 Linux 目录 `/home/lizufan/xiangshan-t12-perf-20261014/hardware-repo`、`hardware-runs` **未能实读/创建**。WSL枚举返回 E_ACCESSDENIED；没有猜测发行版、用户、SSH入口或资源。Windows实际可用 Python3.13.13、Git2.53.0.windows.3、Java21.0.10、Icarus12.0 devel；无 Mill/firtool/Verilator/Yosys/OpenSTA。Icarus无法替代真实Chisel/FU RTL生成。

## 3. 方案与技术说明

### 3.1 FU与共享后端的实际限制

以下基线行号可按 [source.sha256](../evidence/vdot-hardware-ab-20261014/source.sha256) 复查。

| 层次 | 源码事实及影响 |
|---|---|
| FU | [VDot.scala](../../src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala) 28–75行四态，42行只有IDLE ready、43行RESP valid；RESP fire转IDLE，下一拍才接受 |
| 配置 | [FuConfig](../../src/main/scala/xiangshan/backend/fu/FuConfig.scala) 583–604行非流水/UncertainLatency；VDot第22行require拒绝只改piped |
| 资源 | [Parameters](../../src/main/scala/xiangshan/Parameters.scala) 456行VFEX4含Vfdiv/Vidiv/VDot，VfWB/V0WB port3 priority1，共用IQ/读端口 |
| busy | [ExeUnit](../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala) 127–143行busy，224/226行in.valid/ready受!busy；out.fire清除为寄存更新 |
| OG2 | [Og2ForVector](../../src/main/scala/xiangshan/backend/datapath/Og2ForVector.scala) 38–61行每拍更新valid，not-ready向IQ返回block走重试，不是自动保持队列 |
| 写回 | [WbArbiter](../../src/main/scala/xiangshan/backend/datapath/WbArbiter.scala) 177–184行notWrite、224行不定延迟ready取实际仲裁；357–360行fire才传completion，反压同时延长RESP/busy |
| one-hot | ExeUnit321–322行输出one-hot断言；不能不改仲裁/身份就让共享FU并发响应 |
| 门控/唤醒 | ExeUnit71–125行不定延迟in.fire置enable、out.fire清；真实门控恢复、VL/RAW源依赖/读端口与IQ重调度均可能增加全核间隔 |

同拍释放反例（源码推导）：请求A响应前busy=1，该拍out.valid/out.ready=1。即使B的FU ready=1，ExeUnit.in.ready仍0，B不能fire；该沿busy变0，下一拍才可能接受。FU队列空位不改变!busy。仅VDot改piped还会被wrapper拒绝，且Vfdiv/Vidiv仍使latencyCertain=false；单份控制/ROB快照也没有扩展。

### 3.2 候选与代价

| 选择 | 可能收益 | 决定 |
|---|---|---|
| 保留生产基线 | 已验收协议 | 本次保留 |
| 输入级融合 | 预测少一拍FU/共享EXU占用 | 唯一实验候选，外部采样路径变长，未晋升 |
| FU级II1/队列 | busy下无真实II1 | 本次否决，不能以局部漂亮II代替全核收益 |
| 宽串行加法/重写CSA | 没有PPA证据 | 不做，保留窄平衡树 |
| 共享EXU同拍释放 | 可能消除释放气泡 | 通用后端合同/关键ready路径风险大，不纳入本次最小改动 |

候选只改变输入采样与下一状态；killed优先级、reset、RESP/背压、非法判定、目的控制、基类DataHoldBypass和断言保留。没有多请求共用一份ROB/pdest/control。

基线乘法位于局部srcReg→productsReg；融合后的路径包括实际RF/旁路来源、源mux、ExeUnit分发/复制源选择、乘法→productsReg。模块边界不切断组合时序。归约仍productsReg→三层扩位加法→resultReg。无STA不能确定是否成为全核关键路径。

srcReg声明128位但高64未使用，resultReg高96常零，低32符号扩展也有冗余；基类unused快照可能裁剪。**不能把减少256位声明输入寄存称为减少256个物理触发器。** 本次cells/depth/面积/Fmax/功耗均未知。

理论II4→II3表示局部最小间隔减少25%、理想接受率增加1/3，均非实测全核加速。真实时间比较应为 `C_B × T_B < C_A × T_A`，C为相同全核窗口周期、T为实际可闭合周期；不能承诺得分。
### 3.3 真实接口A/B实验包

[fu_ab_test.cpp](../evidence/vdot-hardware-ab-20261014/experiments/fu_ab_test.cpp)复用原fu_test.cpp的scoreboard和环形年龄oracle；算术期望只读原22+10000数据。两binary分别声明 `VDOT_RESPONSE_LATENCY=3/2`，除约定时序外不更改算术/身份/非法域期望。

| 计划检查 | 方法；本次RTL全部NOT_RUN |
|---|---|
| 算术/身份 | 同10022组/顺序，完整128位、ROB含flag、pdest、vec/V0、vpu与调试身份 |
| 背压/II | 同每请求0/1/2/7拍、持续valid；fire记账；未接受输入持续扰动 |
| 合法/非法 | 同22条件与16策略/vxrm；ctrl.vl干扰而实际VL源合法；异常一次且禁写 |
| 取消 | 同8年龄/self/wrap×ready0/1；基线年龄1/2/3/10、候选1/2/9覆盖全部实际寄存阶段/RESP/阻塞7拍；64/48场景 |
| reset | 基线4/候选3实际占用阶段；清在途、恢复、无幽灵响应 |
| 压力 | 同固定种子5000拍算法；因在途分布不同，随机总计不能直接当性能A/B |
| 守恒 | accepted=responded+killed+reset_dropped+pending；最终pending0；watchdog |
| 负控 | identity改错、cancel-leak伪造valid、drop隐藏成熟输出；应exit1且有注入/失败标记；尚无真实失败日志 |
| 原回归 | 默认false下原模型/datapath/FU脚本；两变体VLEN256真实require拒绝 |

逐拍TSV保存pre-edge握手、reset/flush、双侧身份、完整结果、写使能/异常/控制/调试字段与真实post-edge out.valid。基线首次pre-edge valid为accept+3、post-edge为+2；候选为+2/+1。runner从trace计算直方图/min-II并保留raw/gzip、SHA、命令/工具版本/elapsed/exit；**当前没有真实trace或A/B数值**。Scala/C++尚未真实编译，不能把准备好的checker当已通过。

## 4. 待确认事项与风险

| 编号 | 阻塞/风险 | 补齐证据 |
|---|---|---|
| H-ENV | WSL E_ACCESSDENIED | 允许执行会话实读Linux发行版/用户/路径/资源/工具；不换工具绕过拒绝 |
| H-GIT | 创建本任务Git分支引用被拒绝 | 允许正常元数据写入后形成本地提交；当前commit=null，不能cherry-pick不存在SHA |
| H-RTL | 真Chisel/FU编译/A/B/负控未运行 | Chisel→firtool→Verilator --assert、默认回归、双trace/负控 |
| H-TIMING | 外部输入路径增加乘法，无STA | 同Liberty/PVT/时钟、实际RF/旁路起点到product端点；孤立FU输入零到达时间不足签字 |
| H-CORE | 共享EXU/门控/OG2/写回/precise trap未候选验收 | 独立候选全核配置，保持DiffTest；v0/别名/VL/CSR/RAW/WAW/取消/wrap/旧vdiv-vfdiv竞争 |

门控疑点的最小复现（源码推导，**未仿真**）：EnableClockGate=true；发射不定延迟VDot，使in.fire置uncer_en_reg=1；响应前命中取消、out.fire=0；之后不发新请求。enable仅in.fire/out.fire两分支更新，可能一直为1，直到reset或后续响应。busy/FU状态仍能恢复，因此不是已证明的功能死锁，也没有功耗实测。需真实EXU观测enable/clock确认；本次不改通用门控、不增加第二补丁。

## 5. 验证与证据

### 5.1 本次实际完成

| 项目 | 实际结果 | 原始证据 |
|---|---|---|
| 基线/发布status | HEAD与授权一致，发布无修改 | source-head.log / source.sha256 |
| 原模型35项 | PASS，unittest1.160s；命令墙钟1.2587s、exit0 | [完整日志](../evidence/vdot-hardware-ab-20261014/logs/original-model-unittest.log) |
| generate --check | PASS，5文件字节一致、exit0 | [日志](../evidence/vdot-hardware-ab-20261014/logs/original-model-generate-check.log) |
| 原manifest向量导出 | PASS，22+10000、exit0；TSV SHA `901a7be30e62b81bcd3df55b20538a5ba9c879ba9c7c34f28b8c0421d8e6a327` | [日志](../evidence/vdot-hardware-ab-20261014/logs/prepare-vectors.log) |
| patch可应用性 | PASS，git apply --check exit0；未实际应用生产 | [日志](../evidence/vdot-hardware-ab-20261014/logs/patch-check.log) |
| 审查/实验工件 | 已完成可review；不等于RTL正确性 | [实验目录](../evidence/vdot-hardware-ab-20261014/experiments/) |

工件校验曾两次因Windows clone CRLF与Git/发布LF的原始字节比较失败，已保留失败记录；修正仅为Git/发布比较统一换行，同时保留clone初始字节SHA核对。没有修改生产逻辑或模型期望。runner语法、CLI守卫、报告本地链接及生产快照检查随后PASS；Scala/C++编译仍NOT_RUN。

每条本次命令的argv/cwd、elapsed与实际/预期exit见 [local-checks.json](../evidence/vdot-hardware-ab-20261014/local-checks.json)。完整工具版本日志保存；Linux资源/Liberty未知，不声称全机无其他安装工具。

### 5.2 历史与本次边界

已有 [rtl-fu-20261013/results.log](../evidence/rtl-fu-20261013/results.log)记录六类、71258拍、accepted11245/responded10960/killed271/reset14，是**历史回执，未本次重跑**，不能为候选签字。基线E0/E2/E3/II4有历史FU验收/接口文档与当前源码核查支持。

| 指标 | 基线 | 候选 |
|---|---|---|
| 首次post-edge valid | E2：历史+源码；本次NOT_RUN | 预测E1；NOT_RUN |
| 最早response | E3：历史+源码；本次NOT_RUN | 预测E2；NOT_RUN |
| 最短accept间隔 | 4：历史+源码；本次NOT_RUN | 预测3；NOT_RUN |
| 全核RAW/吞吐周期 | 本子任务未实测 | NOT_RUN |
| generic cells/depth | NOT_RUN | NOT_RUN |
| 面积/Fmax/功耗/STA | UNKNOWN | UNKNOWN |

没有真实A/B、RTL负控、综合、STA或候选EMU；不能把准备脚本/字段或模型PASS算进这些结果。

## 6. 下一步与复跑条件

本任务所有进程同步收尾；**未启动整核重编，无后台任务**。先解除环境阻塞，在用户授权Linux独立repo确认源码/dirty work/完整固定依赖/主任务资源，旧环境只读复用。

以下是准备好的入口，**未执行**；Linux目录来自用户授权，工具/xs-env必须提供现场实读值：

```bash
cd /home/lizufan/xiangshan-t12-perf-20261014/hardware-repo
git apply --check team/evidence/vdot-hardware-ab-20261014/experiments/fuse-input-stage.patch
git apply team/evidence/vdot-hardware-ab-20261014/experiments/fuse-input-stage.patch
python3 -B team/evidence/vdot-hardware-ab-20261014/experiments/run_ab.py \
  --repo "$PWD" \
  --out /home/lizufan/xiangshan-t12-perf-20261014/hardware-runs/fresh-ab-run \
  --firtool-dir "$VERIFIED_FIRTOOL_DIR" --xs-env "$VERIFIED_XS_ENV_ROOT"
```

runner拒绝其他repo根/复用输出；并行1、JVM堆4G、现场至少6GiB可用内存。只构建局部FU/datapath，不构建CPU；候选全核配置/EMU需协调。不能为绕过当前WSL拒绝把命令送另一工具。

可选 `--structural-proxy` 若真实Yosys存在，使用同顶层、同flatten/synth流程作generic cells统计；未带Liberty/物理约束，不能称面积/主频/功耗。若解析/综合失败保留日志，不造PPA。所有功能仿真保持 --assert，模型期望/黄金NEMU/DiffTest不改。

只有默认回归、双变体真实矩阵/负控、外部critical path/STA验收、候选全核DiffTest和公平周期/时间比较均满足才值得晋升。若全核无收益或时序代价抵消少一拍，则否定本候选、保留基线，不连续堆后端大改。当前成果是**未晋升的审查与实验包，优化验收未完成**。