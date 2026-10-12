# 综合审查问题修复与复审

日期：2026-10-12（北京时间），分支 `James_Hotten`。源码复核基准 `7cd588a8fb132e568fc9d07eb761310ac557120a` 加工作区全部 T09/审查修复；原始问题见 [综合审查](completed-tasks-audit.md)。本轮由用户授权修复、复审、提交推送；不替团队成员签字。

## 修复与关闭依据

| 问题 | 源码处理 | 实际检查与边界 |
| --- | --- | --- |
| S01：忽略源码绕过 | [artifact_guard.py](../scripts/artifact_guard.py) 校验固定Git树的实际字节，扫描包括忽略目录在内的编译源码/头文件；构建依赖文件补齐实际消费输入；锁定依赖复用相同门禁 | 外层 PYTHONOPTIMIZE=1 下6项真实源码/头文件注入拒绝，恢复后standalone/reference均构建成功 |
| S02：旧镜像配新源码摘要 | 两条驱动产生 workload-provenance.json，运行前核对构建源码/模型/生成器/输入/镜像、arch/mode、固定AM源码/库 | 两个真实main.c注释注入均在guest执行前拒绝，源码复原且镜像不变；模式/数据/镜像篡改另有单元负控 |
| S03：实际解释器与来源错配 | NEMU schema 2绑定提交、五文件补丁、角色、配置、源码及生成输入快照、二进制；正式入口要求NEMU_HOME及实际对应binary，强制校验 | 两入口均拒绝wrong-checkout及changed-config；standalone完整运行与reference来源校验分别通过。vdot归档实际binary/image/data/mode/timeout，RTL还记录flash/ref/ram/max-cycles |
| V01：VS漏检/转换缺失 | [harness.S](../workloads/vdot-exceptions/harness.S) 在所有向量准备后设置VS，stub紧接读回；判定器要求合法Dirty，异常拒绝非Off降级，同时允许Initial/Clean被实现升Dirty | Initial/Clean/Dirty均有真实日志；生产判定器25项、七项harness自测及异常Dirty→Initial运行负控通过；Python日志负控拒绝同类伪PASS |
| V02：单一scratch布局 | 生成器1.2.0保留原48定向数据，增加160布局/别名及96政策/vxrm/vxsat/VS交叉，随机化操作数编号 | baseline两平台实际各1304项，全部32寄存器、1147操作数三元组、18种scratch布局、96交叉；32768项仍只表示分配算法检查 |
| V03：诊断不全 | 保存真实指令前全32寄存器并与输入逐字节比较；[diagnostics.c](../workloads/vdot-exceptions/diagnostics.c) 打印编号、源前后值、完整实际/期望目的、首个post错误字节及PC；baseline导出begin/end边界 | 实际C输出的受控高位错误指出v10/byte15，带真实pre_src快照；正例均pre32_checked=1。快照有效标志帮助区分观察失败，CSR-only失败仍由配套结果行说明 |
| V04：当前规格残留旧状态 | 规格0.1.5-draft限定“尚未实现”为2026-10-11历史检查，并链接T08 | ISA合同仍vdot-s8x8-r32-v0.1；数值、编码、合法域及异常行为未改变，NEMU五文件补丁未改变 |

共享门禁减少两条驱动原先不一致的校验逻辑；关键检查使用显式异常，不依赖可被优化关闭的assert。run阶段不重新生成输入，来源变化要求重新构建。默认vdot NEMU超时600s用于扩展规模，运行记录保存实际值；主机耗时不用于硬件性能结论。

## 重新验证

当前原始记录、编译来源与检查输出见 [修复证据](../evidence/audit-fixes-20261012/README.md)。

| 检查 | 结果 |
| --- | --- |
| Python模型/门禁/日志/布局回归 | 23个测试方法通过；包括伪PASS、错误CSR/VS/mask/边界、缺失/重复/篡改和完整寄存器分配约束 |
| 原生C判定器/诊断 | 25项检查通过；受控目的高位错误诊断输出核对通过 |
| QEMU harness | 7项自测、3项负控通过；未扩展full正确拒绝并退出3，不计作vdot通过 |
| NEMU来源构建 | 固定基线+补丁的standalone/reference分别构建，通过schema2校验；reference加载与四个DiffTest导出接口检查通过 |
| NEMU vdot full | 1304合法+37异常=1341项，退出0/GOOD TRAP，无失败或不可达状态，Initial/Clean置脏及完整pre/post快照检查通过 |
| RVV baseline | QEMU与NEMU各1304项，退出0，布局/CSR维度按上表核验；begin/end全序列为13条，算术区间为3条 |
| 优化模式来源负控 | 6项未知源码注入拒绝；vdot及baseline各3项旧源码/错配检出/配置漂移拒绝，guest未执行且源码/配置/镜像复原 |

两轴独立只读复审：Spec未发现本轮范围内阻断缺陷；Standards首轮指出vdot缺少显式运行参数。补齐参数记录并重编译、重新运行后，再次复核无遗留可操作问题。复审结论限本轮软件修复范围，原始历史问题和旧归档不改写为当时已修复。

## 剩余验收与优化

T03三位成员审查、Q01～Q07及候选合同冻结、非作者复现仍待落实；vdot RTL、真实全核DiffTest、取消/配置依赖与虚拟化状态分支、T13双方配对及硬件周期测量均未完成。不能凭本次PASS数量关闭这些条目。

门禁验证固定候选产物的来源一致性，不是可抵抗恶意重写Git、摘要和构建日志的签名供应链。明确生成配置头实际字节与依赖文件显式列出的 `/usr` 头文件进入快照；上游 `-MMD` 不枚举全部系统头文件，未审计整个操作系统/编译器所有动态库。NEMU原始基线及任意非候选配置不能使用正式候选入口冒充验收，新增配置需独立定义来源类型。

baseline仍保留13条核心序列；未来可评估减少vset或复用零seed，须验证高位清零、别名、CSR恢复及对称测量边界。先完成RTL与独立复现，再以真实周期决定优化收益。
