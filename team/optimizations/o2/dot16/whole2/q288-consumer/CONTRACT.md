# whole2 与 plain D：同镜像完整 Q288 筛选合同 v1

合同：`r3-dot16-whole2-q288-v1`。当前状态：UNBUILT / UNVERIFIED（源码准备），尚未执行新的 GNU 构建、preflight 或 guest。人工重启暂停期间不发布新的 PowerShell/WSL任务；恢复后先取得实际镜像与profile供复核，再决定唯一一次目标启动。

## 目标与写入范围

在同一新 ELF 中比较已验证 plain D 与已有 whole2 候选，保留 P 与 FR。此有限筛选只决定后续完整消费者应优先接入哪个 dot16 软件函数，不转移旧目标 PASS，不增加 ISA、RTL、ABI 探针、退休 trace 或 ASIC 验收。

写入仅本子叶；[范围登记6689409726](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6689409726)接续WORK6670578319/UPDATE6670959414及6674886539保留的consumer范围。原 [plain D Q结果](../../q288-consumer/RESULT.md)、whole2六文件、全部冻结运行和官方程序只读。不操作共享index，不新建检出。

## 基底与候选身份

基底是刚完成原始日志离线复核的完整 Q288 实际镜像源码归档：

- [plain D证据ZIP](../../q288-consumer/evidence-v1/evidence-01.zip)：SHA-256 `9056f62f93718b2afbe1dcea103b15b64f70292ae27546b78f544bb2249915f9`。
- 基底实际ELF：`216ed0418829bed5be00732670aed8d09532ca6f9615a68f9ea720fd05649fe5`。
- 基底生成器image.py：`ddf9052875b9de67d8a93209a70a90a835fdeba8d91b11317c0b4e24f80b761e`。
- [whole2原主机证据ZIP](../host-01-evidence.zip)：`4e1167fc4b1c635c56ef104201489c9f24e85af624ff0f0c73461e4b8fcbe05b`。
- ZIP内完整生成汇编 `files/host-01/generated/whole2.S`：`df2983a21ab85d982b51e7faa0710d536d2bd4afe5bc9c2b91577dd3450972c8`。

只取已生成汇编末尾完整 `q288_dot16_whole2`，不重新运行旧生成器或八正三负主机筛选。该函数完整412B SHA为 `b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6`，包括正确的 `X += 32` 后缀。原主机筛选的事实与适用范围见 [whole2/RESULT.md](../RESULT.md)，不把它当成本次目标周期证据。

## 接口、数据和新调用计划

M=K=288、GS32、36个八行tile、每行9组。56B RV64/lp64d context、128B最终slots、packed W/X/scale布局、所有fixture/golden、完整输出和逐组严格binary32次序均保持。P、FR、D接口和函数不变。W=whole2使用VLEN128下的两个完整向量寄存器加载，输入总字节数不变；返回VL8/e8/m1、vstart0/vcsr7、FRM0，允许正常fflags。这里没有新时钟、复位、FU接口、流水时延或吞吐保证。

| 槽 | 臂与函数 | kind | 新完整Q调用数 |
| --- | --- | ---: | ---: |
| 0 | P：q288_paired16_rvv | 5 | 6 |
| 1 | W：q288_dot16_whole2 | 0 | 7 |
| 2 | D：q288_dot16_vdot | 0 | 6 |
| 3 | FR：q288_fused_rvv4 | 5 | 10 |

计时顺序固定 `(3,0,1,2,3,3,2,1,0,3)`，即FR/P/W/D/FR、FR/D/W/P/FR。八次普通功能调用覆盖每臂datasets1/2；第九次是W的all−128满幅调用。十个窗口各保留一次同臂warmup和一次计时调用，总计29Q、8352个输出、10个窗口。满幅不计时，整数每组应为524288，独立golden沿用 `66c4c3af41f5c15c3228ce31c1bfc1be67e438e566d1def9499e6daa6b96e525`。

五项共享故障控制仍由首个P/dataset1调用检查。旧dot8 probe仍执行一次。W7+D6各每Q计划5184条dot16，合计67392条dot16加1条dot8；这些是计划数量，不声明已验证退休数量。whole2旧完整函数模型21090条、套用原11条计时开销后预计21101条，只作诊断，不设为验收门槛。

## 最小源码变换与实际镜像要求

从ZIP直接读取plain D的实际source，逐文件验证固定SHA。main.c只改变满幅调用 `q_wrappers[2]` 为 `[1]`，并把对应record的arm2改arm1；其prepare与min_judge已经是kind0，保持原样。data.h只改变合同字符串、增加whole2声明、slot1函数和methods里的第二项。原prepare、judge、guards、五controls、timer、功能循环和测量循环不改。fused.S保留完整基底并追加已有whole2整函数。每组source变换必须精确可逆。

沿用归档内原六编译单元、链接、objcopy共八条GNU命令，串行、CPU1，仅迁移输出根。原编译器、链接脚本、AM库和运行helper身份固定；不构建这些依赖。实际ELF应检查四个wrapper地址、methods/order/功能数组、原fixture和golden、timer/probe完整机器字，以及：

| 保留或新增函数 | 完整SHA-256 |
| --- | --- |
| P | `a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c` |
| W，412B | `b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6` |
| D，484B | `ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb` |
| FR | `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab` |

P/D/FR还须与基底实际ELF逐字节相等；W通过整函数SHA绑定既有完整候选，包括后缀。记录actual ELF/BIN、source derivation、所有编译子进程回收和输入前后身份；新镜像不能继承plain D旧镜像结果。

## 目标运行与选择边界

后续运行器从已验证的controller-03源 `79c58eb8bc2821d82f4b0daf74f0ac9f6f9f8a35a25cde35373607e48bda396b` 有限派生；取得真实新镜像后固定image builder/ELF/BIN身份、合同、P6/W7/D6/FR10计划与满幅归属。保持信号latch、唯一cleanup、全stderr+stdout失败门、行首Q_/QW筛选及完整43行协议检查，不新增运行框架。profile绑定全部实际输入，计数以新实物为准。

固定EMU `f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d` 与feature1 NEMU `cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae` 沿用既有1400B ABI与六合法动态证据；不重新探测或构建。实际guest必须经人工恢复、资源复核及主端新镜像/profile复核；本合同本身不启动guest，预算在具体launch/profile内冻结。

只计划一次新目标EMU。正常exit、真实DiffTest、指定reference、GOOD TRAP、完整协议、全部输出、输入身份及进程回收必须满足原有限Q合同。保留全部四个FR锚和两组反序W/D观察，不从旧ELF补样本，不删除不利窗口，也不追加其他实验的稳定性门槛。

若W正确且在同镜像两次观察中有清楚一致的周期优势，再优先接入完整消费者；优势不清楚或实现成本失衡时选择plain D，反馈原因，不接一串微优化或自动加测。当前筛选不授予完整forward、正式performance、完整退休窗口或ASIC PPA资格。

回退为不选择新独立镜像，旧plain D、RVV及所有冻结证据继续保留。无部署。
