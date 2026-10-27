# C2 实际 RTL 独立复核

候选：6704ce3502a7235cdb81697638c01ed23f6914f6；ExeUnit.scala SHA256：febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6。审查身份：/root/c2_rtl_contract_review。

## 源码结论：PASS

候选相对保留基线 0f12df675378556670afd0dd2153f47fcb330610 的生产改动仅 ExeUnit.scala。相对 C1 的完整源码差异由三个明确新增片段构成：提前声明 ClockStartAllowed Wire；在 ownedDivGate 下覆盖最终 clk_en 并加启动等价断言；在 DIV 控制块连接不含 ready 的启动允许谓词并加空闲就绪断言。逐字节移除这三片段即可还原 C1 ExeUnit，机检记录见 source-review.json。

从 val busy 起直到文件末与 0f 基线逐字节相同，因此实际派发 allowInput、selectedReady、parent.ready、source.valid、childFire 单一接收断言、child输入/ROB绑定和输出路由均未改变。divAccept、divRobIdx、divOutFire、divReady、divCancelled、busy更新优先级仍为原式。新增 owner 仅在 divAccept 时更新。

## 作用域与连接

vdotElastic 仍只允许固定 VFEX4 + 三种准确 FU + uncertain latency；ownedDivGate 还要求 VIDiv 或 VFDiv 类型。O1和旧模式的 vdotElastic=false，原寄存uncer保持与fire门控的else分支保持相同；其他执行单元同理。EnableClockGate=false 时没有物理gate改动，新增不变量检查仍只在O2分支。当前FuConfig.ckAlwaysEn仅CSR/Fence，因此两DIV的最后always-on覆盖不成立。

StartAllowed、busy、owner 均在gate循环之前创建 WireDefault，在后续块用 := 连接，避免 Scala val 前向初始化问题。clk_en 的 C2赋值在旧when链之后且处于 elaboration if，因此 ownedDivGate 时无条件覆盖旧fire赋值；并不是在旧条件上仅追加一个新OR项。实际生成RTL还需独立确认没有残留ready路径。

## 取消、复位与断言

hold = divBusy && owner 使用当前寄存B和owner，未经过flush/reset/cancel掩码。匹配取消当拍仍给活跃DIV时钟，边沿后B清除，子状态依同一ROB取消回idle，再次空闲才关钟。输出完成同样保留该释放边沿；无关redirect不清B，且start受flush禁止，所以不发生误切换。

clockStart===fu.io.in.fire 在 !reset 时检查，且start自身含 !reset。divBusy||divReady同样在 !reset 检查，直接监视G0结论，并非用断言作为功能假设或过滤输入。有效初始化之前的任意状态不在合同中；同步夹具首次TE=1 bootstrap、真实全核共享异步复位仍分别记录。合法动态reset可在TE=0运行，旧B保持活跃子reset边沿；空闲子已为idle。当前源码保持这项条件，不新增reset强行开钟。

断言读取ready会增加仿真/断言逻辑中的扇出，但只要它们不驱动gate E，就不构成门控启动路径仍依赖ready。综合成本阶段必须按原生产工具配置去除仿真断言，不能把这一点替换成随意删除真实ready逻辑。

## 验证范围

此结果是实际源码独立审查，不是功能仿真、PPA或全核结果。父级测试应落实PREIMPLEMENTATION.md所列TE=0、SQRT、双lane、取消、负控与逐拍同基线关系。源码没有阻断项。

## 生成结构检查接续

check_generated_cone.py 从真实两DIV门控E端起，解析当前firtool split RTL的wire/assign和实例连接，跨层回溯至输入或寄存器边界。保留寄存D历史依赖不继续回溯。未解析符号、多驱动、组合环会失败。

冻结C1实际父级RTL负对照已拒绝两个gate：路径中出现DIV ready、allowInput、childFire，记录为 old-c1-cone.json；检查器首次Python re.Match切片错误发生在图遍历前，原因及修复单独保留 parser-first-attempt.json，没有修改任何生成RTL。

候选生成结构检查已完成，见下节。

## 实际生成 RTL：PASS

parent-01/rtl 实际生成物两个 DIV 门控均通过跨层组合锥检查，每个锥有13个寄存器/输入边界，覆盖8份生成模块。没有遇到未解析符号、多驱动或组合环；两个锥均没有 DIV ready、allowInput、childFire/selectedReady 组合依赖。ClockGate.sv 与冻结 C1 逐字节相同。

- 浮点 E = clockStart | (divBusy & ownerIsFp)。
- 整数 E = clockStart_1 | (divBusy & ~ownerIsFp)。

两启动项经真正的 cfg.fuSel 解码，共用不含ready的 StartAllowed。E 锥仍读取 DIV/SQRT FSM 的 outputValid 判定和 VDot p/rValid，这是合同保留的占用检查；不能误写成完全不依赖子状态。所有者/占用寄存器的历史D输入没有被展开为当前组合路径。

三个运行断言均实际保留在生成RTL中，不能拿结构检查代替它们的动态通过。旧C1实际RTL负对照在相同检查器下检出ready、allowInput、childFire并按预期拒绝。最终输入SHA重新核对通过，详见 final-review.json、c2-generated-cone.json 和 old-c1-cone.json。
