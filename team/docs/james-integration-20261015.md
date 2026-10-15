# James_Hotten 分支整合与复审（2026-10-15）

按用户要求，忽略 main 的整合路线，审查其他分支后普通合并到本地 James_Hotten；用户随后明确确认改用 **VFEX4**。当前生产源码统一为 VFEX4 / VDot，不启用输入融合或 II3。此次未推送远端，main 保持 `9d49a225619871f6bf5ec0481e5a504c4dbee703`。

## 来源与合并范围

| 来源 | 固定提交 | 实际合入进度 |
| --- | --- | --- |
| 本地 James_Hotten | `9bb544812df9b424e399ae3ca91899a904f583bd` | 原独立模型、异常验证、基线、构建/来源门禁和全部历史证据 |
| cc77-builder/zufan | `f090665130107282be0990a7664aebf26e491b87` | VFEX4共同基线、NEMU1.1、T10/T11、T12 original190/lean199、软件判定器及独立审查 |
| cc77-builder/zjhwork | `2c0bf8e283d400c1c946ca75f890f266d7758411` | 可选RTL观测、控制压力程序/判定器、11运行完整T12归档 |
| cc77-builder/zufan-t12-review-20261014 | `f188f6f7588270714d94d970fe36f2f2cdda15b9` | 已是zufan祖先，随普通合并完整保留，无需重复合并 |
| LiZufan001/zjhwork | `5227c030fdae9b6087fd995a00a3535b15f6aefc` | 已包含于cc77-builder/zjhwork |
| LiZufan001/zufan | `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3` | 已包含于两条最新开发线 |
| 两仓库远端 James_Hotten | `a978b3b8fe731dd9422a41f80d9d53e40c775656` | 已包含于本地James历史 |

两个普通合并提交分别为 `f10ec37ec`、`3daad934d`。没有 cherry-pick 压平、回滚其他分支或改写历史。完整祖先校验见 [branch-inclusion.json](../evidence/james-integration-20261015/branch-inclusion.json)。

## 架构与冲突处理

1. **唯一生产路线。** `src/`、`build.sc`、`.gitmodules` 与 zjhwork 固定提交完全一致；依赖gitlink保持原固定版本。VDotCfg为非流水不定延迟，绑定VFEX4，与Vfdiv/Vidiv共享资源；正确读取物理VL，完整128位向量/V0写回，经ROB完成/取消。局部E0/E2/E3、II4不能冒充全核延迟。
2. **异常配置统一。** NEMU补丁1.1.0，基线`a48a11f208ff81ad765591d83271d1b339fb3861`，NMIE=1、MDT=0，显式启用CUSTOM_VDOT_XS_TVAL及TVAL_EX_II。满足精确VDOT、VS非Off、合法vtype、vstart=0且物理VL!=8的晚异常按平台给xTVAL=0；保留检查，不通过跳过DiffTest消除差异。
3. **保留James成果并标明适用范围。** 原VFEX1的7个独有源码/测试移到`team/legacy/james-vfex1`，旧FU/译码入口明确退出并指向VFEX4测试；独立VdotExec实验仍可构建，源码与生成器路径同步调整。原共享配置和CSR实现可从9bb固定提交恢复，不能用归档片段覆盖生产树。James来源/依赖/镜像门禁、20项冒烟程序、独立模型与历史证据继续保留；新运行必须绑定新构建。
4. **区分T12硬件配置。** `t12-tests.py`与`verify_t12_evidence.py`保留trace-off固定EMU来源门禁，明确为历史配置；当前树带可选观测源码，不能直接复用它的旧二进制。带观测控制测试使用`t12-regression.sh`/`run-t12-suite.py`。没有去掉源码比较或改写旧runtime pins。
5. **旧证据不变。** James/zufan/zjhwork分别933/798/820个历史归档文件全部保持同一Git blob；这些集合有重叠。tar/gzip保留禁用文本换行转换属性。未启用的实验补丁继续仅作实验材料。

## Standards

独立规范初审未发现RTL观测反向影响数据通路或新增judge API破坏旧调用。发现并处理了历史T12入口固定旧硬件、旧VFEX1测试可能被当作新验收的问题：保留拒绝门禁，明确历史入口，归档旧测试并更新当前进度。保留归档检查器的通用换行解析，避免UART CRLF/RTL LF混合导致伪失败。

主审最终检查确认生产源完全匹配zjh固定版本、仅可选观测、shared judge兼容、旧硬件未残留在生产编译树、全部历史归档字节保留。未发现剩余阻塞性规范问题。独立规范复审代理第二次调用因服务额度中断，不能将主审最终检查表述为第二次独立规范签字。

## Spec

独立规格审查发现1项验收漏洞：`check-vdot-regression.py`允许已被redirect取消的在途请求产生RESPONSE，只要其不再COMMIT即可被判通过，违反接口取消约定。

已修复：RESPONSE拒绝cancelled请求；ACCEPT拒绝cancelled/retired请求。新增两项反例，在修复前均错误放过，修复后正确拒绝；检查器29项测试全部通过。加强后的检查器对原始真实T12归档重新计算仍通过。这证明旧归档符合加强后的检查要求，未证明原RTL曾发生该错误。

独立第二轮规格复审确认该问题已关闭，未发现新的阻塞偏差。NEMU1.1晚VL的xTVAL=0符合继承平台规则的合同；II3未启用。T13、官方合同冻结、人工签字、虚拟化、STA/PPA继续开放。

## 本次实际验证

验证源为 `e5df93c7b69134d2e67959bbe1c5a409404ad46b`。在新建WSL native检出中从已有本地依赖克隆126个固定子模块，无系统安装；Java21、Mill0.12.3、firtool1.62.1、Verilator5.020，详见版本日志。编译结束时检出干净，之后最终提交只增加报告/归档和入口文档。

| 检查 | 本次结果 | 证明边界 |
| --- | --- | --- |
| Python主机测试 | **157通过**，包含取消反例及原James10项来源门禁 | 主机判定/生成/绑定逻辑 |
| 独立模型测试 | **35通过**；两套oracle对22定向+10000随机一致 | 数学/数据，不是DUT |
| C异常judge | **25检查**，普通及UBSan均通过 | C判定逻辑 |
| C T12 judge | **98,321检查**，普通及UBSan均通过 | 全32寄存器位翻转、scratch与CSR判定 |
| NEMU xTVAL策略头文件 | **1,114,256检查通过** | 补丁策略，不是新NEMU运行 |
| Scala真实香山依赖与根源码 | 编译通过，372个根Scala源 | 当前生产编译兼容性 |
| VDotDatapath | lint及**10,022组**仿真通过；bit0/bit127注入预期exit1 | 组合RTL |
| VDot真实FU | trace关/开均lint通过；各**6类、71,258周期**通过 | 真实Bundle/RobPtr的FU，未覆盖整核EXU/ROB行为 |
| FU负控 | 身份错误、取消泄漏预期exit1；VLEN256被明确拒绝 | 防止伪通过和不支持配置 |
| 实际译码RTL | lint及**131,109事务**通过 | 译码组件 |
| T12控制/117矩阵归档 | **T12_ARCHIVE_RECHECK_PASS**；117唯一/124分片记录、控制及负控等11运行重新检查 | 旧真实运行日志复算，新增DUT为0 |
| zufan归档 | 274项SHA与两tar读取；按原源码重新生成两套输入且摘要完全一致；10分片重新判定190/199均PASS | 原日志/计划/回执，不是新运行，也未重读原开发机运行二进制 |

FU两次均记录accepted=11245、responded=10960、killed=271、reset_dropped=14，满足事务守恒；非法响应90，反压25700周期。两次相同输入不是加倍的唯一覆盖。所有负控检查了预期错误标记，不仅看非零退出码。

完整命令、原始日志、源码/RTL摘要和中间失败尝试见 [本次证据](../evidence/james-integration-20261015/README.md)。初次Windows测试的两个GCC编译失败没有计为通过，最终使用项目既有Linux环境全部通过。

## 完成与下一步

本次完成的是分支成果审查、VFEX4统一、验收漏洞修复、普通合并，以及新主机/组件验证和历史日志复验。新全核运行数为 **0**；两组190/199计划不能加成389个唯一ISA用例，也不能据原始rdcycle窗口报告加速比。

下一步应在统一来源上固定新EMU/reference/镜像，重跑控制117矩阵与软件对照，再校准计数边界推进T13。官方歧义、成员签字、非作者整核复现、M/HS/VS委托虚拟化、STA/PPA及最终交付均未关闭。

评审统计：Spec发现1项检查器问题，已修复；Standards识别的整合适用范围问题已处理。两轴最终无已知阻塞项；这不代表未运行范围已通过。
