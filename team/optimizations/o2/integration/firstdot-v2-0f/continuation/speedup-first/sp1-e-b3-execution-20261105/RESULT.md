# SP1-E B3 两例执行接入：宿主准入停止

**结论：HOLD，新增目标进程0；正式执行闭包核验失败后已停止整批，没有重试或继续第二例。**

两例运行器和宿主机制完成；正式CPU4执行闭包核验因遗漏四个cwd配套文件失败，900秒宿主门未建立，按失败即停终止整批。两例均未运行，原o2-control继续HOLD。

| 项目 | 结果 | 证据边界 |
|---|---|---|
| 专用两例五角色运行器 | 已实现；开发检查10方法通过 | 当前源码已冻结，但实际准入不通过 |
| 独立宿主复核 | 26项运行器＋16项算术/实际历史回执控制通过 | 机制与历史日志验证，不是本轮新EMU结果 |
| 完整输入冻结 | FAIL | 首次legacy-control inventory拒绝缺项；没有产出EXECUTION_FREEZE |
| CPU4完整900秒门 | HOLD/NOT_ESTABLISHED | H失败，J/K/D未测，不能用已测解析时间代替总开销 |
| legacy-control | NOT_RUN | 未获得目标准入 |
| o2-all-pairs | NOT_RUN | 整批停止，没有跳过前例继续 |
| o2-control | HOLD不变 | 原完整预算依据仍不足 |

## 失败原因与只读归因

新运行器检查实际 cwd 支持输入时，假设旧 B3 HOST_FREEZE 已包含支持文件。旧清单的991项没有候选和0f两侧的 build/constantin.txt、build/plusArgs，首次实际 inventory 在候选 constantin.txt 处拒绝。后续只读归因确认四项均缺于清单，但实际文件存在；路径、大小和SHA均与真实B2 performance-d0-s03/EXECUTION_FREEZE.json精确条目一致。预算复核还验证了更早SP1-CD/R1来源。

这是本轮执行接入的输入闭包漏项。旧 HOST_FREEZE 本来就标注 HOST_ONLY_NOT_EXECUTION_FREEZE；不能因旧宿主合同PASS就认为已经覆盖真实运行输入，也不能用静态文件存在替代执行冻结。本轮未进入硬件功能验证，没有新增RTL失效证据。

| 真实文件（候选及0f各一份） | bytes | SHA256 |
|---|---:|---|
| build/constantin.txt | 611 | a1fd1d4de05919fec0257bacb550a3622c0f4ec2373e5cf230fc4233fb98c1bf |
| build/plusArgs | 155 | 160d9702d313cbe66be84ae88c2f45c3df9ed7b61b65e3ddeea25133ac6765ff |

精确四条绝对路径与原冻结来源见ROOT_CWD_PROVENANCE.json；本轮只核对，没有修改文件、旧冻结或失败记录。没有创建ADMISSION、RUN_AUTHORIZATION、EXECUTION_FREEZE或已消费执行锁。

## 已完成的实现与保留的失败

运行器复用原B0 common/supervisor，加入固定legacy→allpairs顺序、HOLD用例拒绝、一次性执行锁、真实exe/argv/env/cwd/参考映射/进程身份与资源回执、原始日志SHA、五角色比较和缓存绑定。每例900秒只计算宿主段，目标角色保留原硬截止，不允许预算互借。该机制的宿主控通过，尚未由本轮实际目标运行验证。

开发时首轮10方法中1项发现同硬件重放的额外架构摘要未被拒绝；已在正式预算尝试前增加非空及相等检查，最终10方法通过。初轮FAIL及原源码精确快照保留，适用SHA见runtime-tests/REVISION_01.json和RESULT_02.json。正式预算输入闭包失败发生后未修改运行器或重试，不把开发修订PASS覆盖正式FAIL。

最终runner SHA：`795b1d3c235482bf6601eb3f339171afb2815ab99a71867b6ea751b194290f7a`。common/supervisor与B0原字节一致。

## 预算与完整覆盖边界

CPU4完整历史日志读取、专用检查器解析和序列化实测：legacy-control 10.244443253秒；o2-all-pairs 3.417253458秒。这两项只代表P，不是整场宿主耗时。实际调用图每例13次完整闭包核验H、4次正常解析P＋1次拒错N、5次回执核验J、18次缓存重哈希K和元数据/清理开销；H首次失败后停止，J/K/D未测，公式总值为空。不能据部分数据签发900秒GO。暖缓存解析时间也不构成未来冷缓存上界。

每例5角色、300/1500×4秒、6300目标/7200外层、900宿主上限不变；整批10进程、12600目标/14400外层。负控guest100000；正常legacy800000/allpairs300000，原reserve16规则保留。CPU4、整组4线程、RSS12GiB、日志2GiB、seed1/RAM128MB/fresh均未放宽。

原覆盖未缩减：legacy 4组/128检查点/2157架构VDOT、65536B全32寄存器及512项vcsr、原7项取消/反压/绕回；allpairs 10例/1158架构VDOT、5120B全32寄存器与每例7CSR、6VIDIV＋6VFDIV完成下界。完整128位、bit100、退休身份与八维功能重放仍待真实目标验证。两例无合格性能计时窗，SQRT、timed DIV/SQRT和新性能资格不由它们代替。

## 路线与版本

SP1-E已验仍15/20。默认保持0f＋firstdot V2＋原C8，候选仍原P4初版一拍算术/两槽SP1，未切默认。生产445个文件和旧HOST冻结991项在收口时复核未变；没有EMU/NEMU运行、生产库加载、RTL修改、新核构建、EDA或GitHub写入。

下一轮只修宿主执行闭包：独立R1从真实历史来源加入四项annex和新闭包，补缺失/错路径/哈希漂移负控，重做完整900秒准入；本轮FAIL原样保留。完成后另给目标执行指令，不在当前回合自动修复继续。

[三项指标](METRICS.md) · [预算证据](budget-review/RESULT.md) · [独立复核](independent-review/REVIEW.md) · [下一轮指令](NEXT_STEP.md)。
