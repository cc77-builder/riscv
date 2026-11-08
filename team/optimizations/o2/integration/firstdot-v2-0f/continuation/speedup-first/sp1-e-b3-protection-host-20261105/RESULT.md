# SP1-E B3 原功能保护：宿主合同与预算准入

三例宿主合同与检查器完成；legacy-control/o2-all-pairs有条件预算GO进入执行接入，o2-control预算HOLD。当前三例均非TARGET_READY，专用运行器/执行冻结/CPU4完整宿主900秒门尚待下一轮。

默认保持0f＋firstdot V2＋原C8，待验SP1仍原P4初版一拍算术/两槽弹性候选。本轮没有EMU/NEMU运行或生产库加载、RTL/全核/EDA/默认/GitHub改动；既有外部波形任务未停止、修改或计成本轮目标。

| case | 宿主合同/检查器 | 完整历史guest / 原UTC秒 | 另一次同BIN UTC秒 | 正常guest停点 | 本轮决定 |
|---|---|---|---:|---:|---|
| legacy-control | PASS | 376582 / 763.464 | 783.280 | 800000 | GO进入执行接入；目标仍HOLD待外层/900秒门 |
| o2-all-pairs | PASS | 126918 / 249.503 | 262.357 | 300000 | GO进入执行接入；目标仍HOLD待外层/900秒门 |
| o2-control | PASS | 703135 / 1308.260 | 1485.433 | 1500000，仅HOLD草案 | HOLD完整预算依据不足 |

预算沿用每例五角色300/1500×4秒、6300目标/7200外层，CPU4、PGID4线程、RSS12GiB、日志2GiB、seed1/RAM128MB/fresh reset。原完整历史seed0且无当前资源回执，clean-02同BIN使用不同EMU/ref且旧UTC审计失败保留；完整历史可支持前两例一次硬限额尝试，但不是未来保证上界。o2-control较慢观察只余约14.6秒，不能借用别的角色余量。

## 专用功能合同

- legacy-control：4组/128检查点/2157架构VDOT，65536B全32寄存器检查和512项vcsr；保留原7项取消、反压及绕回。只有VDOT＋VIDIV历史流量，浮点DIV由all-pairs承担。FULL_STALL只保留实际统计，未追加单例硬门槛。
- o2-all-pairs：9个128dot调度例＋1个九有向配对例，共10例/1158架构VDOT；5120B全32寄存器、每例7CSR，6VIDIV＋6VFDIV的最少12次完成下界从manifest求出。
- o2-control：16组/256trial/1208架构VDOT，131072B全32寄存器，结尾5CSR；P/R与部分取消必须实际覆盖，不伪造其历史FULL_STALL。
- 三份首条bit100按ELF/BIN/PC/word/vd固定；真实拒错和正常恢复仍未运行。三个程序均无vfsqrt.v和合格性能窗，SQRT本地证据及未来timed负载范围不混用。

## 检查器与证据

专用collector核对SP1/O2 schema、冻结图像/参考、完整接受源点积128位、PC/word/目的身份、原UART自检、CSR合同及覆盖。全部向量寄存器与CSR数值依靠冻结目标自检＋未来实际live DiffTest，不能声称它们均被观察器完整打印。四正常角色做同镜像架构比较，同硬件精确比较八项功能摘要；无性能窗的samples/counter显式N/A且事件数0，不用None==None冒充通过。日志PASS始终标记requires_runtime_receipt，不能代替实际进程/来源/资源回执。

93项首版宿主控、R1覆盖21项、R2 CSR合同6项和离线CLI 1项分别通过，最终版本适用范围见collector/RESULT.json。初版归档曾把末尾CRLF规范化为LF，独立复核发现SHA差异；已新增与原冻结SHA完全相同的11487字节快照，旧错误快照和FAIL保留，纠正映射见collector/PROVENANCE_ADDENDUM.md，不能把初版93项直接贴到最终SHA。独立合同复核重验126项G0输入、4runtime对象和44本地回执；root另核对445生产源与844保护输入不变。

## 必要缺项与下一步

下一轮仅接入legacy-control和o2-all-pairs：复用未变supervisor，新增专用五角色回执适配、真实/proc执行身份与参考映射、一次性执行锁/完整源闭包，验证失败即停及拒绝HOLD用例；按实际调用图测CPU4完整hash与日志解析成本，900秒门不过则HOLD。HOST_FREEZE仅保证本轮宿主资料身份，不是EXECUTION_FREEZE，也不含目标授权。满足全部门后且用户授权才可最多10进程有界执行，不重试或跳过失败继续。

SP1-E已验仍15/20。剩余五项没有因为宿主PASS而新增目标资格；o2-control、普通C48、新timed DIV/SQRT仍HOLD。下一步完整指令见NEXT_STEP.md。

[三项指标与历史来源](METRICS.md) · [检查器结果](collector/RESULT.json) · [合同复核](contract-review/RESULT.md) · [预算分析](budget-review/RESULT.md) · [下一轮指令](NEXT_STEP.md)。
