# C2 后续全核/NEMU与公平周期：只读准备记录

2026-10-25。状态：**READ_ONLY_CORE_INPUTS_READY_PENDING_COST_GATE**。本子任务只读现有源码、输入、既有回执并执行软件输入预检；没有启动 C2 全核构建、NEMU/EMU 仿真、综合或 STA，没有修改生产源码、旧运行或 GitHub。新 C2 全核与周期资格仍为 **NOT_TESTED**。

## 1. 身份与复用结论

| 对象 | 核对结果 |
| --- | --- |
| C2 独立根 | /home/riscv/riscv-lab/o2-c2-readyless-20261025/repo |
| C2 HEAD | 6704ce3502a7235cdb81697638c01ed23f6914f6，工作树干净 |
| C2 ExeUnit SHA256 | febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6 |
| 保留基线 HEAD | 0f12df675378556670afd0dd2153f47fcb330610 |
| 保留基线 EMU SHA256 | 2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8，实物匹配 |
| C2 build/ | 预检时不存在；无需移动主检出或旧 H1 的 build |
| 源码与依赖 | 对基线硬件 pins 核对 429 份源文件，唯一差异 ExeUnit.scala；21,236 份依赖全部逐文件匹配，无缺失 |
| 观察器 | ExeUnit 的 O2 trace 源码尾部逐字节相同；8 份通用构建/运行/检查器与主检出逐字节相同 |

源码观察器适配没有发现必需改动。实际生成 RTL 尚未经过本版 observe-profile 全核 elaboration，因此生成模块名、实际编译命令、生成物清单与新 EMU 身份必须在真实构建后再次绑定，不能用本记录代替构建验收。C2 局部补充测试只读层级输出所在的 parent 测试顶层，不得复制进全核或成本顶层。

## 2. 已完成的软件输入核对

原 run_suite.py --preflight-only 在 C2 根执行成功，输出 O2_PREFLIGHT_ONLY_PASS hardware_not_checked emulators_executed=0。命令、退出码和原输出在 inputs-preflight-01-command.json、inputs-preflight-01.log、inputs-preflight-01/。

| 固定输入 | 实物 SHA256／结论 |
| --- | --- |
| 正常 NEMU | efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4 |
| bit100 负控参考库 | 9b3aecf362b7c7ddb4f8bace355c2e0ee2cc919fd5f59eefc641db220ab40df0 |
| boot flash | a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994 |
| hello/vadd | 45d47558d3be5909aec37a4a2e1f51111a6019000dd58fe915f3a19390e5c33f |
| 控制程序 | b447c98209f5074072d7e36c77e63e92f8bd51a2cc05e2dbe7cfe857f4d37df7 |
| 8 分片功能／异常矩阵 | 原 117 唯一 case、124 次分片执行，全部固定镜像／来源及 corpus 核对通过 |
| dense | 原 T13 固定镜像与9份相关来源文件相等，生成内容及 ELF case 检查通过 |
| 两项 O2 supplement | diagnostic 1158 commits、control 1208 commits；两镜像与37份输入 SHA通过，详见 supplement-inputs.json |
| 公平周期镜像 | 原16份统一镜像、208份封存软件载荷逐字节匹配；每版原始计划215窗口，详见 performance-inputs.json |

**正常与负控参考库保持原绝对路径。** 负控 wrapper 包含固定正常库的 dlopen/DT_NEEDED 路径，不能随意移动或重建后沿用同一身份。参考根 /home/riscv/riscv-lab/t12-regression-20261013/nemu/reference，正常库相对该根为 build/riscv64-nemu-interpreter-so。本次无需重建 NEMU、flash、镜像或重新生成向量。

## 3. 启动前置与执行入口

只有本次 C2 同约束成本筛选通过，才允许依次执行下面阶段。筛选拒绝时本节保持准备记录，**不得启动全核或周期**。每项开始前核对真实 state/进程、C2 HEAD/源 SHA、已有 output 与 build 目录，不能覆盖失败记录。

通用脚本 ROOT 从脚本所在检出位置计算，必须在 C2 根调用 C2 的脚本。以下建议新输出根尚未创建；操作者需确认无同名运行，并由本轮新控制器绑定成本回执、源身份、命令、退出码和各步成功条件。

~~~bash
cd /home/riscv/riscv-lab/o2-c2-readyless-20261025/repo
C2_RUN=/home/riscv/riscv-lab/o2-c2-fullcore-20261025
python3 -B -m unittest discover -s team/optimizations/o2/fullcore -p 'test_*.py' -v
python3 -B -m unittest discover -s team/optimizations/o2/fullcore/workloads -p 'test_*.py' -v
python3 -B team/optimizations/o2/fullcore/build_fullcore.py --output "$C2_RUN/build-01" --profile observe
python3 -B team/optimizations/o2/fullcore/run_suite.py --output "$C2_RUN/core-01" --hardware-pins "$C2_RUN/build-01/hardware-inputs.json" --emu "$PWD/build/emu" --jobs 2
python3 -B team/optimizations/o2/fullcore/run_supplements.py --output "$C2_RUN/supplements-01" --hardware-pins "$C2_RUN/build-01/hardware-inputs.json" --emu "$PWD/build/emu" --jobs 2
python3 -B team/optimizations/o2/fullcore/recheck.py --campaign "$C2_RUN/core-01" --supplements "$C2_RUN/supplements-01" --output "$C2_RUN/recheck-01"
~~~

上述是分阶段入口，不能无条件串行执行；每一步 rc=0 且对应严格状态通过才启动下一步。构建脚本本身要求新 output、无 build/、硬件源已提交、依赖 clean/pinned。配置沿用 MinimalConfig、单核/单线程EMU、Java12G、构建j2、T14=1、O2=1、O1=0、O2/T13观察=1其余观察=0，firtool 1.62.1。至多同时2个EMU；成本进程全部完成后再占用重型构建资源。

全核接收门槛沿用原合同：12 core＋2 supplement、13正常通过＋1真实bit100 DiffTest负控拒绝并同镜像正常参考恢复、117/124矩阵、完整128位结果/元数据/异常、七项legacy控制与六项O2联合覆盖、无未排空事务、严格原始日志复算通过并绑定C2新EMU和新pins。不得把旧0f的 PASS/EMU回执归到C2。现有全核合同不包含运行期reset；局部TE0动态reset证据的范围单独保留。

## 4. 公平周期的新控制器要求

旧 r3-div-gate/fullcore/launch.py、finish.py **不可直接重跑**，其源提交、旧输出、旧build移存及接受标记均针对0f。旧 r3-div-gate/performance/build_profile.py 和 compare.py **不可直接用于C2**：硬编码比较8b5024fc→0f、旧pins/EMU、old/new生产源式和生成差异。不要仅替换命令行 --after-pins 后绕过它们的保护；需要在新C2材料位置编写并冻结新控制器/审核器，原文件不改。

新控制器可复用原窗口检查、纯统计和严格O2分析逻辑，必须更新和核对以下身份：

1. before=接受的0f基线、after=刚通过全核的C2；两版完整源码、依赖、构建工具/命令/开关及新的全核接收回执逐项绑定。
2. 唯一生产源差异 ExeUnit；审查真实生成差异及只读观察器。旧模块差异白名单是上版结果，不是C2白名单；新的寄存器数/名字变动需实际审查。NewCSR中Git标记变化可规范化，不能忽略其他差异。
3. 同一16镜像（1校准+3功能+4场景×3数据集）、同正常库/flash、128MB、seed=1、EMU单线程、120分钟/200万周期保护。共同辅助输入 constantin.txt/plusArgs 实物核对。
4. 两版各4轮正式窗口；额外 batch/d0 重放两次。共36次新EMU、478校验窗口、192正式窗口=96配对；两版先后交替，最多2进程。
5. 保留正常DiffTest/GOOD TRAP/全部128位/真实退休计数、全局DUT周期和排空门禁；加速比为sum(RVV)/sum(vdot)，不扣计时开销，宿主耗时不算性能。
6. 每一正式配对 after 多1周期就报告退化；重放只验确定性不增加样本。运行PASS与周期不退化是两个判定。新原日志由冻结检查器独立重解析，并追加版本数据档案，NOT_TESTED层级保留。

基线旧全核 campaign-state=passed；基线旧公平周期 campaign-01 已结束，36作业、96正式配对完全一致的结论属于旧8b→0f比较，本次仅用于了解接收标准，不能转记为0f→C2成绩。

## 5. 风险与本记录边界

- C2 gate改变综合逻辑及寄存器布局，固定seed不保证内部随机化顺序一致；新全核负控/正常恢复和正式周期重放必须实际完成。
- O2 trace源码相同不等于生成全核已构建通过；特别注意异步共同reset、Backend TE=0条件仍来自全核实际生成结构。保留新断言输出的致命检查。
- 若新观察/生成器确需更改，先记录原因和新输入身份；生产RTL修改仍须提前告知用户，不能在旧候选身份下补改。
- 若成本筛选失败，主检出保持0f，C2全核、周期保持NOT_TESTED，不因软件输入已准备好而越过门禁。

身份检查见 identity-readiness.json。本目录为子任务接续材料，非第二套项目路线；最终结论、采用/拒绝、计分板及版本数据由主任务统一维护。

## 6. 补充：受双重门禁保护的全核控制器草稿

fullcore_controller.py 已通过 Python 语法检查及纯主机门禁测试，**未执行控制器、未构建或运行EMU**。默认不运行；根审查后复制到新C2材料目录才可带 --execute 进入。内部固定本候选与基线身份，屏蔽成本未通过、审计不匹配、缺字段、失败或源/证据变化；启动前要求C2 build不存在，不移动任何旧build。

输出终点为 C2_FULLCORE_REGRESSION_PASS_PENDING_GENERATED_REVIEW；保留生成差异、工具/命令比较和最终接受收据的独立审查步骤，cycle_comparison_authorized=false。主机测试5项方法包含21项字段损坏负控、18项缺字段负控、默认不执行及成本拒绝不启动进程；合成门禁控制不代表真实成本通过。详见controller-host-tests-01.log及命令回执。公平周期最小适配点见 PERFORMANCE_ADAPTATION.md。
