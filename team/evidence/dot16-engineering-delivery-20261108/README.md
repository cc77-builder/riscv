# 香山 vdot 工程源码与实测指标交付

本工程包整理了已测 dot16 硬件的精确补丁、已闭合完整 forward 的源码，以及 prefix、W2/NP、packed-Ws 候选和各自的实测范围，供人工选择代码并更新技术文档。原 PDF、LaTeX、PPT 和视频保持原样。

本轮 prefix 父级验证与 packed-Ws K288 目标证据已发布到 `cc77-builder/riscv:zufan`，提交 `dc6611728bf8994094efd4b85725a55335182196`。代码包的交付身份由本目录所在提交和与 ZIP 同目录的 `code-audit.json` 中的完整 ZIP SHA 确定（该回执不在 ZIP 内）；该发布提交不改变下面各次实验的硬件、程序或测量身份。

## 如何选择入口

| 入口 | 对应源码与硬件 | 已有结果 | 使用边界 |
| --- | --- | --- | --- |
| 已测 dot16 整核 | `c981529dc6e493fb7deee8429b9ce05fd197497b` 加包内 `hardware/f149-measured/candidate.patch` | 固定六例整核冒烟；本文列明的软件目标实验使用其 EMU `f1491865…` | 发布分支的最新 HEAD 不是这一硬件身份的替代品。 |
| 已闭合 W/WQ 完整 forward | `software/closed-forward-W/`，共同 ELF `5ba0cd07…` | 四臂正确性通过；较快 RVV PQ 与较快 dot16 WQ 的同镜像周期比 1.156325× | D288/H768/L6 固定合成模型、准备后首次 p0/token1；TRACE0 周期观察。 |
| 新 N/NQ 完整 forward | `software/w2np-forward/`，共同 ELF `62a73b9d…` | GNU机器码、五例完整参考及四臂目标正确性均已闭合；同镜像较快RVV PQ与NQ周期比1.196049× | 固定合成模型、准备后首次p0/token1；TRACE0周期观察，正式应用性能资格仍为false。 |
| prefix 硬件候选 | `candidates/prefix/source/` | 局部算术/FU、真实父级功能及独立FU映射/STA | feature1 库面积 17,965.374；尚未采用到 f149 EMU，没有该硬件的应用周期。 |
| packed-Ws 软件候选 | `candidates/packed-ws/` | K288/K768参考；K288 normal0 八窗目标检查 | N平均周期再减少6.207615%；prepare在窗外，尚未接入完整consumer。 |

以上是不同层次、不同版本的结果。工程交付保留可用的已测入口与候选源码；没有把一个候选的面积、另一个硬件上的周期和第三个程序的基线拼成综合收益。

## 已测硬件的精确身份

实测补丁为9,252 B，SHA256 `5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416`。对应EMU为71,043,280 B，SHA256 `f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d`。

硬件配置为 `MinimalConfig`、单核、单EMU线程、`EMU_TRACE=0`、`NO_DIFF=0`；`VDOT_DOT16=VDOT_O2_ELASTIC=VDOT_T14_FUSED_INPUT=1`，其余五个已记录的handoff/trace开关为0。feature1 reference、flash及1,400 B ABI身份见 `hardware/f149-measured/SOURCE_BINDING.md` 和机器可读 `binding.json`。

原构建先完成Scala/Verilator生成，GCC原生编译失败；随后使用同一冻结生成物，以Clang19和GNU ld.bfd成功续编。包内九个fullcore驱动/合同文件与原硬件记录的长度、SHA一致。`resume_native.py` 绑定原失败生成物和路径，是历史续编入口；包根目录不是完整工程根，不能直接执行它并预期任意环境重建成功。

完整工程基底、子模块和工具链仍按原 `build-inputs.json` 定位。其SHA为 `76853412c2c2f27e3e91fbdb0c25b89064023c908d648aa33491372fb5d6231e`；原硬件435文件、依赖21,236文件和126个递归依赖身份没有被这个小源码包替代。

## 软件指标与原始证据

已闭合 W 实验的四臂周期为 P 17,378,319、PQ 16,594,945、W 15,139,851、WQ 14,351,452；比较使用较快合格RVV PQ，观察到周期减少13.519135%。Q表示该实验固定的激活量化优化；该旧实验的W2仍使用原FR路径。

新的 N 实验将K288与K768都接入N/P路径，原四臂作业于2026-11-08 01:26:19 UTC闭合，四路正确性和资源回收均通过，输入未变。其同镜像周期为P 16,920,555、PQ 16,129,141、N 14,276,120、NQ 13,485,355；相应窗口instret为4,958,760、4,567,702、3,239,096、2,848,037。较快RVV为PQ、较快dot16为NQ，观察周期比为**1.1960486765×，周期减少16.391363%**。它使用独立的共同ELF和软件路由，不能把旧W版更慢的PQ作为新NQ的分母。两次实验都保留各自同镜像对照，原W/WQ可作为回退参考。

原N目标results为21,805 B，SHA256 `13c45f846a8a26ad27996c6cd41faabd942da541131282f024c09dd5bb7e38f0`；完整64位UART原字已按整数重算，四路原始stdout、validation、campaign/owner终态和host回执保存在模块 `w2-np/target-20261108/summary.zip`。这是终态摘要包，未包含四份77,125,408 B目标镜像；完整镜像和原resource profile仍保留在原WSL冻结目录，摘要包不是完整运行归档。

packed-Ws的K288同镜像均值为 P 45,639.5、N 27,353.5、packedP 45,047.5、packedN 25,655.5周期。N自身改善6.207615%，P自身改善1.297122%；较快RVV packedP与packedN的周期比1.755861×，仅适用于该固定完整调用窗口。没有据此宣称相对旧技术文档再改善75.59%，也没有推断完整应用收益。

对应现有PDF各表的更新建议见 `METRIC_UPDATE.md`。它明确旧dot8微基准、C8、不同完整forward和新K288的测量边界。当前没有证据证明原技术文档的各项性能统一改善50%。同工作量、同窗口、同频下速度提高50%要求周期比1.5×；周期减半要求2×。

模块权威记录位于共享仓库：

- `team/optimizations/o2/dot16/rtl-integration/fullcore/RESULT.md`：已测硬件的构建和固定冒烟。
- `team/optimizations/o2/dot16/rtl-integration/cost/RESULT.md`：CSA/prefix局部成本、时序和父级功能。
- `team/optimizations/o2/dot16/first-forward/RESULT.md`：旧W四臂与新N四臂的不同实验身份及状态。
- `team/optimizations/o2/dot16/whole2/RESULT.md`：packed-Ws局部参考、目标观测和范围。

源码包不重复包含大型raw归档、模型、EMU/NEMU、生成缓存和工具链；它们的位置、版本和SHA由包内 `external-dependencies.json` 及模块记录给出。历史失败、UNKNOWN和原始日志继续保留。压缩包的逐成员字节身份以 `manifest.json` 为准。

## 包内源码与原执行身份

原构建的文本源码和控制器已从冻结目录逐项取回，没有用后来模块的同名文件替代。旧、新两份原 `inputs.json` 的 SHA 分别为 `98e39b7d…` 和 `9ee7e2dd…`，它们由对应已闭合 build result 固定；其中 81 项和 87 项控制器路径都与实际源字节相符。源码捕获前后身份未变，没有运行捕获到的程序。

| 包内位置 | 内容 |
| --- | --- |
| `hardware/f149-measured/` | 精确补丁、源码清单、硬件结果和九份原 fullcore 驱动/合同，以及来源说明。 |
| `software/closed-forward-W/build-01/source/` | 原 W 完整 forward 的21份文本构建输入。 |
| `software/closed-forward-W/controller-01/` | 原81项 reference controller完整相对目录；合同为实际旧版本 `789a2565…`。 |
| `software/w2np-forward/build-01/source/` | 新 N/P 完整 forward 的22份文本构建输入。 |
| `software/w2np-forward/controller-01/` | 新87项 reference controller完整相对目录。 |
| `software/w2np-forward/target-controller-01/` | 新132项目标controller，其中93项support；与reference controller分别保存。 |
| 两个软件profile的 `evidence/` | 各自原build result和inputs；不会改写原绝对路径或SHA。 |
| `candidates/prefix/`、`candidates/packed-ws/` | 当前候选源码和对应控制器/合同，资格按本文各自范围解释。 |

旧、新build原目录各另有4个 `.o` 对象，原件及身份仍保留在外部证据中，不把它们算成“源码缺失”或放进小代码包。控制器之间即使存在相同字节，也保留完整各自相对目录，满足原binding读取关系。

独立stage入口保留在 `software/w2np-forward/prepare/`；target入口位于 `software/w2np-forward/target/`。其中 `launch_target.py` 的完整SHA已由原闭合owner的执行pin固定；合同、派生说明及事后来源材料仍保留各自身份标签。`owner/launch.py` 供launcher导入原进程监管函数，它自己的 `main()` 仍绑定旧作业，不是新W2启动命令。这些不同用途均可在manifest中核查。

这是精确源码和工程证据的便携交接包，仍依赖完整仓库、子模块、AM/klib、norm/quantize对象、模型与gold/TLS fixtures、原资源profile和工具链。`standalone_buildable=false`；解压目录不是可直接替代原工程根的工作区。收录上游或官方程序只为保留输入身份，不授权修改其行为。

## 采用与回退

按原manifest检查补丁前置SHA和新增文件不存在，再在授权的隔离输入上应用；确认应用后SHA，沿对应合同验证。回退前检查后置身份和反向补丁适用性，保留其他人的修改。当前Windows主仓、resident工作区和运行输入均有保护约束，打包本身不切换任何生产或在途输入。

prefix保持128bit架构接口、两槽、E2最早响应及无阻塞II1；P每半区两条19bit row，R分别为19/20bit。局部feature1面积比匹配原始dot16基线24,017.406减少25.1985%，但名义1ns时序仍不满足；这不是物理布局布线、功耗或整核成本结果。父级通过只增加其已解码请求边界的功能证据。若采用这一候选，需要独立的整核验证，已有f149的PASS与周期不自动转移。

本次软件交接优先保留新NQ入口及其同镜像PQ对照，旧W/WQ和原RVV路径继续作为回退参考；这只适用于上述已验证固定工作负载，不自动替换任意应用的默认路径。在录屏、资源与共享工作区条件允许后，再执行已准备的prefix整核入口。每项采用决定以实际结果和可复现输入为依据，不因源码包收录了候选就改变默认实现。
