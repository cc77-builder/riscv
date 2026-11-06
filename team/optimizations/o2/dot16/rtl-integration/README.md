# dot16 弹性 FU 接入与验证

状态（2026-11-06 02:40Z）：本补丁已在常驻 WSL 工作区应用，并完成生产 Scala/Chisel 编译以及 FU、父级和解码的关闭/开启两态动态验证。各层使用新的合同、源码快照和运行身份；当前资格见下表。
它承接父目录 `CONTRACT.md` 的 `dot16-s8x16-r32-v0.1`，保留独立原型、T17、旧 NEMU 和整核历史证据的原身份。

| 层次 | 本候选结果 | 证据入口 |
| --- | --- | --- |
| FU | 两态实际通过；旧矩阵保留，新增 dot16 算术、混合流水、非法与取消/复位检查 | [VALIDATION_RESULT.md](VALIDATION_RESULT.md) |
| 父级 ExeUnit/FU | 两态实际通过；原 14 组和 20 项观察负控保留，新增关闭态 16 项、开启态 166 项实际接收 | [parent/RESULT.md](parent/RESULT.md) |
| 生产解码 | 两态实际通过；旧/新编码的实际运算类型及受阻快照保持得到动态核对 | [decode/RESULT.md](decode/RESULT.md) |

这些结果尚不构成整核 DiffTest、实际应用性能或 ASIC PPA 的资格。首次 FU 外置缓存失败与首次解码预检失败均在各层记录中保留。

## 修改与来源

`candidate.patch` 修改五个现有文件，并新增一个普通生产源文件：

| 路径（相对 `src/main/scala/xiangshan/backend/`） | 修改 |
| --- | --- |
| `decode/Instructions.scala` | 增加独立精确编码 `0x0e00000b/0xfe00707f` |
| `decode/VecDecoder.scala` | 仅启用候选时加入 dot16 表项，沿用单 uop、两向量源和完整目的写入 |
| `decode/isa/bitfield/RiscvInst.scala` | 用同一开关控制 dot16 的向量分类及无旧目的依赖处理 |
| `fu/wrapper/VDot.scala` | 增加内部 op=1；单请求 FU 拒绝启用 dot16 的构建组合 |
| `fu/wrapper/VDotElastic.scala` | 扩展 P 数据，复用两组八项算术，保留已有 P/R 控制 |
| `fu/wrapper/VDot16Feature.scala` | 新增严格解析的编译开关与弹性实现依赖检查 |

五个现有文件的 Windows 原字节已重新读取，均与 `352789e1975a3a409d39f67d143de6cf04938745` 的固定来源捕获相同。
主端随后提交报告和 NEMU 的 HEAD 为 `c981529dc6e493fb7deee8429b9ce05fd197497b`；补丁的实际应用守卫是
`source-manifest.json` 中每个文件的 SHA256，以及新增文件必须不存在，不能仅靠分支名称判断适用性。
未修改 `VDotDatapath.scala`、`VDotO2.scala`、FuConfig、父级、ROB/CSR、NEMU、旧验证器或官方程序。
两个未改算术/开关依赖的 SHA 也列入清单。

## 开关与关闭态

`VDOT_DOT16` 未设置或为 `0` 时关闭；`1` 时启用；其它值在 elaboration 中报错。
启用依赖 `VDOT_O2_ELASTIC=1` 和既有 O2 规则，因此还需要 `VDOT_T14_FUSED_INPUT=1`，
并排斥 O1 handoff、T12/O1 观察器等既有互斥组合。T13/O2 trace 的原约束继续生效。

译码表、`isVDot` 分类和弹性 FU 使用同一个 `VDot16Feature.enabled`。
关闭态不新增 dot16 译码项，不把该编码归类为已实现的向量点积，P 仍是8×16位，归约仍直接取原有八项结果。
开启后仍保留原 dot8 编码和 e8/m1/VL8 语义；dot16 使用内部 op=1，要求 e8/m1/VL16。
任意模式下均检查 vill、vm、vstart、SEW/LMUL，未知 FU op 仍非法。

## 数据、时钟和取消

每条指令的两个源保持128位。dot16 的低/高64位分别送入原 `VDotProducts`，各产生八个 signed16 乘积。
P 的256位保存这些乘积；若接受的是 dot8，则在接受沿将高八项写零，后级不用额外保存或重读当前输入 op。
两组原 `VDotReduce` 各给出精确 signed19 部分和，取其低19位后做 signed20 加法，再符号扩展至低32位。
R 仍只保存32位最终结果，输出仍以高96位零组成完整128位。新末级加法放在 P→R 路径，输出端没有 split16 的额外加法。

沿用 `FuncUnit` 现有单时钟域的上升沿和复位连接，不新增时钟、复位或跨域状态。
P/R valid 继续使用原 `RegInit(false.B)`；`reset.asBool` 为真时禁止输入、输出握手。
最终复位网络的同步/异步形式仍由原工程 elaboration 决定，本补丁不改变它。本轮 FU/父级生成物中的 P/R 为同步高有效复位，实际复位丢弃及恢复检查见对应结果；这不替代整核复位网络或时序签核。

在本候选启用的弹性实现中，dot8 和 dot16 的周期协议相同：

| 指令 | 接受 E0 | E1 | 最早输出握手 E2 | 理想 II |
| --- | --- | --- | --- | --- |
| dot8 | 保存低八乘积、高八置零和完整控制 | P 归约后进入 R | 输出完整128位结果 | 1拍 |
| dot16 | 保存十六乘积和完整控制 | P 归约后进入 R | 输出完整128位结果 | 1拍 |

上述两拍时延和一拍发起间隔已由本轮 FU/父级连续请求场景实际核对，适用范围为相应测试边界。
关闭候选时，用户所选的原 baseline/T14/O1/O2 流水线保持原有行为，不统一改成上述弹性时序。

`killP`/`killR` 仍由各自槽内的完整 `robIdx.needFlush(io.flush)` 判定；任意 redirect 都禁止新接受。
未被命中的老 R 可以响应；被命中的槽不能响应或迁移。满槽背压、同沿旧 R 响应/旧 P 迁移/新请求接受的条件完全沿用原代码。
新输入配置只影响新接受的乘积和 `acceptedCtrl`；移动到 R 的异常、写使能、目的和性能身份仍来自旧 P。
非法请求保留精确异常并关闭 vec/v0 写使能，R 数据沿用原非法分支清零；没有新增 CSR 或 fflags 写入。

## 验证路径与适用范围

实际完成了源字节核对，以及在云端仅含七个源码文件的独立副本上的补丁检查：
`git apply --check --whitespace=error-all`、正向应用后六文件逐 SHA 核对、反向检查与回退。
回退后七个原文件逐字节恢复，新增文件不存在；该副本没有 Git index，也不是 Windows/WSL 生产工作树。
检查记录见 `review.json`；候选完整性以 `source-manifest.json` 的补丁与结果 SHA 为准。

补丁应用后完成的新生产构建、FU/父级及解码验证按本页顶部索引查阅。参考模型、整核 DiffTest、目标应用周期与 EDA 需要各自对应的源码、合同和真实记录；本目录不转移其它来源的资格。现有原型的139263次响应比较或独立成本数字保持原有适用范围。

固定来源 `build.sc` 的 `vdotDecode`、`vdotElasticFu`、`vdotElasticParent` 都依赖完整 `xiangshan` 模块，
因此新文件属于正常生产源集合，无需更改官方构建源清单。原 O2 `run_rtl.py` 不记录 `VDOT_DOT16`；
本轮通过新团队入口保留并可逆派生原测试，分别记录 `VDOT_DOT16=0/1`、全部输入身份和工具链。解码使用原 harness 的只读端口扩展与独立小构建，核心 classpath 由官方任务导出。
原 G1/G2 的 op=1 负例同时保持 VL8；启用新指令后该输入仍然非法，但原因已包含 dot16 的 VL 不符，不能据此证明 op=1 未被支持。
这些旧例已保留；新 FU/父级合同另外覆盖 op=1/VL16 的合法路径和真正未分配的其它 op，旧负例与历史结果保持原样。

后续集成需将本补丁与匹配的新参考模型、软件消费者和整核证据对应。dot16 与更强 GS32 RVV 的胜负仍取决于公平的实际应用测量；FU 的 II 和时延不能直接替代应用加速、1GHz 或功耗结论。
