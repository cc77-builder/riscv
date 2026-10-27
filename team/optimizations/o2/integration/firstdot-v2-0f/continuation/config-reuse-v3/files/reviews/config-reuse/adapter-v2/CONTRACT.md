# 当前 clean 硬件上的配置复用首筛合同（待评审草稿）

外层合同：zjhwork-clean-config-reuse-8x32-d0-probe-v2。仅 8×32 / dataset0，firstdot 和 config-reuse 各一图。当前状态为 V2_HOST_COMPONENT_VERIFIED_TARGET_NOT_EXECUTED；本目录不是生产导入，也不是运行证据。

## 前置与来源

必须先完成当前 firstdot 组合验证和独立 clean 构建，再取得该 clean identity 上的 firstdot/S1 全矩阵：24 正常图、8 dataset0 重放、1 bit100 负控，共33进程；外层 current combination 资格检查必须通过。本探针不会修改原45文件 import manifest、旧 firstdot/T17 哈希或任何 RTL。

新导入源为 fcf4a11fc569cb2a8fcb4e18d96ec2764b228557 的独立26文件闭包，已有39依赖逐字节锁定。四份新适配器源码 probe.py、raw_audit.py、CONTRACT.md、import-manifest.json 单独冻结。测试文件不属于运行合同。clean identity 必须通过其原验证器，运行前后物理复核真实源码、EMU、NEMU、flash、工具、AM及构建元数据。

## “同镜像”措辞更正

配置复用是两个不同完整 BIN 的比较。公平性依据是相同硬件、输入、调用计划与固定地址布局；两个 BIN 在旧 leaf 范围外逐字节相同，范围内只允许已证明的 vsetivli x0 删除。不能把这称为“同一 BIN”。

新建 firstdot 对照的整个 BIN、独立 wrapper/public GNU 对象、源汇编、cases/header 必须逐字节等于本轮已合格 clean firstdot 的对应图；ELF 所有 ALLOC节及 leaf 对应也必须一致。S1 的两个8KiB RVV槽与 firstdot 对应槽相等。该代码身份不转移历史运行 PASS；本探针仍重新执行对照。

## 状态证明与编译约束

仅 VLEN128、合法立即AVL、直线正常完成路径。状态包括实际VL、SEW、LMUL、ta、ma、已知vstart=0及支配配置位置。仅完全相等配置且vstart已知为0才删。未知文本/控制流/标签/CSR/FOF/custom配置不合规必须清空全部知识。白名单普通向量指令只能保留已证明的vstart=0，不能由未知或非零推导为0。候选不出现未知屏障。

保留原 g.bind、g.verify_build、pairs、完整128位带毒寄存器数学模型、真实GNU指令解码、C ABI调用与退休检查。单独解码删除机器字，确认 vsetivli / rd=x0；其余机器字及顺序不变。firstdot变体也重算同一证明，但不执行删除。不得放宽绑定或手改指令计数。

## 有界执行

串行启动，CPU亲和性最多4核。保持 seed=1、128MB RAM、2,000,000周期上限及原超时、参考和flash。运行前须由操作者排查同机重负载。正向性能使用模拟器周期，不使用宿主墙钟。

恰好5个新EMU进程，顺序如下：

1. config-reuse实际首条vdot的bit100负控。
2. 同完整BIN、新PID、正常参考恢复，兼作候选正式结果。
3. firstdot正式结果。
4. firstdot独立进程重放。
5. config-reuse独立进程重放。

后两次将正常对照顺序反转。负控PC从当前候选ELF解析，要求vd0、0x0388000b、bit100、唯一差分不匹配、预期失败和合法O2部分轨迹；恢复必须通过原恢复门禁。

4个正常进程各24窗，共96正常窗；用于均值的正式窗口仅2图×16=32，每个 software/method 格4样本。重放逐项检查全部24窗的seq/cycles/instructions，共48对；first/warmup不用于正式性能统计但必须正确。恢复不得重复计数。

## 分离工程通过与性能决定

FUNCTIONAL_PASS 只表示本次正确性、差分、完整128位、CSR、精确退休与调用、校准、O2协议、负控及恢复全部通过。重放不一致仍保留这些逐项事实，但性能标记 INCONCLUSIVE。

PERFORMANCE_CANDIDATE 必须同时满足：
- config-reuse/reuse/vdot 正式周期总和严格小于本轮 firstdot/reuse/vdot；
- 严格小于本轮两变体、basic/reuse全部四种RVV格的最小总和；
- 两图全部24窗重放逐项相同；
- 相同完整BIN的firstdot新运行与已合格clean firstdot的全部24窗签名相同；
- 未改RVV控制格的全部6窗无未解释变化；其余三个非主候选格无未解释退化；这三个格的检查不以主候选胜出为前提。

不存在0.5%门槛，不在看到结果后加容差，不删样本，不只挑最快单窗，不把4样本范围或平均值当显著性证明。明确未胜两基线为 REJECT；重放/对照漂移或其他无法归因的退化为 INCONCLUSIVE，均不可自动扩测。严格源码或正确性失败为 FAILED，并保留失败目录。

PERFORMANCE_CANDIDATE 仅表示该8×32/d0探针值得另行决定扩测，不授予全矩阵、普通C库、性能默认或其他形状资格。4×13继续保留RVV；V2 firstdot默认保持。硬件面积/STA/频率/功耗和应用级LLM收益均NOT_TESTED。

## 留档

独立新输出目录，禁止覆盖与隐式续跑；记录源闭包、clean身份、本轮baseline资格与源码/ELF/BIN/对象对应、实际命令/退出/PID/时间、负控夹具、原始日志、全部窗口与结论。离线复算须重新解析原始证据；raw_audit.py提供本地原始日志复算：重验编译对象、完整窗口、负控/恢复、5个进程身份/顺序、重放与决策，并拒绝缓存统计与原文不一致。它不启动EMU、不修改原始日志、不重新测量硬件。完整配置复用5进程尚未实跑；目前只有既有firstdot日志的正常/负控审计与篡改负控已验证。尚无新的可移植压缩归档审计器，不能宣称独立归档复现完成。真正运行后更新版本数据档案及JSON，失败与不确定结果同样留档。

## v2 与 v1 的边界

v1 完整保留。v2 只修复分类与本地输入闭包审计：主候选 config-reuse/reuse/vdot 未胜出本身仍为 REJECT；其他三个 paired 格出现未解释退化，无论主候选胜或负均为 INCONCLUSIVE。性能严格小于双基线的阈值不变。

本地 audit_probe 从当前物理 identity 与 checker/build/image 输入按运行时同样规则重建完整 common，要求输入集合和每个 SHA 精确相等，审计前后复核共享实物。每个进程还单独复核其真实 cwd/AUX、BIN 与参考库；单条 record_audit 是组件核查，不能替代完整 audit_probe 的共享闭包门禁。审计前后物理 identity 也必须一致。

本版本不改变 8×32/d0 范围、五进程顺序、候选指令、负控目标、目标周期或默认配置。外层合同升为 v2，用于区分更严格的分类和审计记录；不将 v1 的主机/静态证据重新标记为 v2 目标验证。
