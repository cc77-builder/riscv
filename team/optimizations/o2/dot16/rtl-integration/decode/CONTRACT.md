# dot16 生产解码与只读运算类型探针合同

本目录是新增团队验证输入。运行前本合同不代表解码已通过；最终状态以各次源码、生成物、命令和真实退出码为准。原完整 harness、原测试、官方构建和生产六路径候选均保持原样。

## 源码与可观测边界

固定基线为 `c981529dc6e493fb7deee8429b9ce05fd197497b`，叠加上级 `source-manifest.json` 的六路径生产补丁 `5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416`。原 `GenerateVDotDecode.scala` SHA256 为 `c4b275bbc5e8f63f189ad55fc646b15d27d9216fd4497537c5c4bec66e3f3204`；原 `decode_test.cpp` 为 `06ba8130d98de5521126ec26a2f7dd17b85aeba51085f38a07d184468f91095b`。

`VDot16DecodeProbe` 继承原 `VDotDecodeTestTop`，只增加两个 Output，连接原生产 `DecodeUnit` 的 `simple.io.deq.decodedInst.fuOpType` 和生产 `DecodeUnitComp` 已有的 `out.fuOpType`。位宽从实际信号类型取得。不复制解码器、不覆盖原 IO、不插入功能逻辑。生成器保留原 `MinimalConfig(1)` 及日志参数。

输入为原 32 位指令、valid/ready、redirect、vtype/vstart/VS 状态；时钟上升沿采样，复位高有效。沿用原握手模型：复杂解码输出在下游 group ready 时才呈 valid；受阻时继续核对原元数据和运算类型。这里没有 VL 输入，不能将 VL=8/16 的执行检查伪装为解码测试，也不声称验证 Rename、寄存器别名执行、RF、ROB 提交、整核异常或应用吞吐率。

编码要求：旧 dot8 MATCH=`0x0200000b`，新 dot16 MATCH=`0x0e00000b`，MASK=`0xfe00707f`。启用时两者均精确识别为 VDot、生成一条 micro-op/一次写回，实际 simple/complex 运算类型分别为 0/1。禁用时新编码不得归类或路由为 VDot；这仅证明当前分类边界，不单独证明整核非法指令 trap 链。

## 构建路径

根 `build.sc` 和原生成器不改。从正式 `xiangshan.runClasspath` 任务导出当前生产核心的已编译 classes、依赖和资源，再用本目录独立小 `ScalaModule` 的正式 `unmanagedClasspath` 入口编译原 harness 源与新增 probe 源。仅复用核心 classpath，不引入另一个已编译的同名 harness。

固定同一 Scala 2.13.15、Chisel 6.6.0、Chisel compiler plugin 6.6.0，以及原 reflectiveCalls/macro-annotations/tasty-reader 选项；普通 classpath 不能代替 compiler plugin。核心导出使用已审查、真实且原已被 Git 忽略的 `out/dot16-fu-20261106-pro2` 缓存。独立 probe 的源码工作目录和输出都位于该次仓外运行目录；它没有官方构建的 VcsVersion 任务，不需要修改 Git 配置或伪造 `.git`。

Mill 0.12.3 的单目标 `show` stdout 按完整 JSON 数组解析，stderr 单独保存。PathRef 按四字段解析，最后字段保留完整绝对路径，不从混杂日志中截取或修复 JSON。原始导出、路径顺序、每个 jar/资源/类文件的内容身份都保留，运行后再次核验 classpath 未变化。

首轮 `decode-flag0-01` 在 classpath 存在性预检停止，尚未编译 probe：真实导出 135 项中有 23 个不存在的标准资源目录。Mill 的 `resources`/`compileResources` 默认声明这些路径，`PathRef.apply` 允许路径不存在；此次失败是新运行器的存在性假设过严。该轮原始输出、源码快照、exit=1 和清理回执保留，不追认通过。后续新运行保留全部条目及顺序，仅允许 `run.py` 中从首轮导出逐项核对的 23 个相对资源路径缺失，记录为 `missing-resource`，且结束时仍须保持相同身份。不会创建这些目录、过滤条目或接受缺失的 JAR/classes、未知路径及悬空符号链接。生产源码、原构建和测试矩阵不变。

入口依据：[Mill 0.12.3 JavaModule](https://github.com/com-lihaoyi/mill/blob/a6b3b7225a989ff8e8aa548f1af74278dcaac18f/scalalib/src/mill/scalalib/JavaModule.scala)、[PathRef 格式](https://github.com/com-lihaoyi/mill/blob/a6b3b7225a989ff8e8aa548f1af74278dcaac18f/main/api/src/mill/api/PathRef.scala)、[Scala compiler plugin 配置](https://github.com/com-lihaoyi/mill/blob/a6b3b7225a989ff8e8aa548f1af74278dcaac18f/scalalib/src/mill/scalalib/ScalaModule.scala)。

## 保留与追加的检查

原 C++ 通过 11 处受控文本变换生成新测试，必须能逆变换逐字节重建完整原件。原主循环、字段/异常/写使能/快照/边界比较、旧 encoding 邻位回归及 vadd 回归均保留；新增观察和新矩阵放在新运行中。旧请求始终选择 op0 编码。

每态保留原 131109 次完成事务：4 种 ta/ma × 32³ 个寄存器组合，32 个 SEW/LMUL 配置，vill、VS-off、vstart、v0 和 redirect 后恢复。实际增加 simple op0 比较 131109 次；complex op0 比较 131373 次，其中 33 个停顿场景各额外观察 8 次。原停顿场景继续核对完整字段。

| 状态 | 新增内容 | 实际观察要求 |
|---|---|---|
| 关闭 | 新编码 4×32³ 个组合的组合分类检查，共 131072 次；不当作接收事务 | `classified=0` 且 `simple_vdot=0`；旧完成事务仍为 131109 |
| 开启 | 新编码同一套 131109 次事务及 17 个 MASK 邻位回归 | simple op1 比较 131109 次、complex op1 比较 131373 次；新旧合计 262218 次完成事务 |

新编码受阻时，后续输入被明确切换为旧 dot8 编码并扰动 vtype/vstart，而复杂解码的在途结果必须继续保持 op1 及原快照。新矩阵逐项复用原完整字段比较，因此同时观察寄存器字段、VL 依赖类别、非法配置、写使能、无 old-vd 依赖、单 uop 边界等；不将仅存在某个编码常量当成动态运算类型验证。

两项新增观察负控分别只在 C++ 读回后翻转 simple/complex 的实际 op 值，必须真实返回 1，且日志精确包含对应 injection 和 operation mismatch。关闭态在旧首事务拒绝；开启态先执行全部旧事务，在新首事务拒绝。这是新增端口比较链的拒错测试，不是 RTL 故障覆盖率或整核差分测试。

## 执行与证据

每态使用新运行目录、CPU1/jobs=1、4 GiB JVM、单处理器声明、900 秒累计运行预算。每个耗时命令按剩余预算限时并独立建立受控进程组，PASS 前再次确认累计耗时；外层工具采用 1000 秒上限。超时清理并保留失败记录，不自动重放未知结果，不覆盖旧输出。实际入口显式设置已验证的 JAVA_HOME、CHISEL_FIRTOOL_PATH、COURSIER_CACHE 和工具 PATH；环境只记录选定构建变量，不记录凭据。

必须实际完成 classpath 导出、新模块编译/Chisel elaboration、RTL lint、Verilator 构建、完整正例和两项负控。正例成功记录中的事务和比较次数由实际执行累加，入口严格校验完整两行结果。所有源码、生产候选、完整硬件输入、126 固定依赖、classpaths 和 probe 源在前后保持身份一致。

保留 `inputs.json`、源码快照、可逆派生证明、`compiler-inputs.json`、依赖清单、原 classpath stdout/stderr、类文件与资源内容清单、全部命令/退出码、生成 RTL 与二进制 SHA、正负结果及终态。失败运行保持原样；如需修正团队测试器，采用新源身份和新运行，不把旧 PASS 自动转移。
