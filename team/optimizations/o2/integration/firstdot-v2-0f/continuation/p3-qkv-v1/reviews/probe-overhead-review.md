评审时间：2026-10-30T21:50:56+08:00

# P3 目标开销、计数与 0f 探针适配只读评审

结论：**保留现有 main 的最小迁入方向 GO；旧供体 runner 不可直接执行；新目标运行须先完成 0f 身份、观察器、3% selector 和预算适配。** 本评审只读源及既有归档，不执行候选、构建、EMU/NEMU，不改 vendor。

## 1. 可从实际循环严格导出的工作量

下表适用于原样 `vendor/.../forward-host/active/target/main.c` 与 `generate.py`。这是静态工作量证明，非新机器上的耗时测量。具体指令计数须再绑定最终 GNU ELF。

| 项目 | 推导 | 正常完整进程 |
| --- | --- | ---: |
| dataset1 功能 boundary | arm=0,1 各一次；main:105-110 | 2 |
| dataset0 warm boundary | ORDER=(FR,TA,FR,FR,TA,FR) 每窗一次；main:111-115 | 6 |
| dataset0 measured boundary | 六窗各一次；main:116-119 | 6 |
| 完整 boundary | 2+6+6 | 14 |
| 完整 Q/K/V 投影 | 每 boundary 三次 | 42 |
| TA boundary / Q | 功能1 + 暖2 + 测2 | 5 / 15 |
| FR boundary / Q | 功能1 + 暖4 + 测4 | 9 / 27 |
| 应用输出 | 14×3×288 | 12096 个 FP32 |
| 独立量化探针 | dataset0、1、语义夹具2 | 3 |
| 全量化调用 | 14+3 | 17 |
| 量化 group / element | 17×9 / 17×288 | 153 / 4896 |
| 每 FP32 输入读两遍 | 17×288×4×2 | 39168 B |
| 量化输出写入 | 17×(288+9×4) | 5508 B |
| dot8 每 Q / 每 TA boundary | 288×9×4 / 再乘3 | 10368 / 31104 |
| custom 提交（正常） | 15×10368+开头故障探针1 | 155521 |
| 计时内 custom | 2×31104 | 62208 |
| 四计数器采样点 | 6×4 | CSR_SAMPLE=24、COUNTER_ENQUEUE=24 |
| prepare | 故障1+语义3+功能2+暖6+测6 | 18 |

量化固定汇编每次 FP 操作清单由 `path.py:133-135` 强制核对：load576、move10、abs288、max288、divide297、round288、scale_store9。17 次合计分别为 **9792、170、4896、4896、5049、4896、153**。原 `.option norvc/norelax` 量化器按伪指令均单字展开，循环推导每次 `3+9*(3+32*5+2+32*7+3)+1=3532` 条，17 次 60044 条；仍需实际对象的展开审计，不能据此计算处理器 cycles。

42 个投影的数学乘积数量为 42×288×288=3,483,648；这不是 3,483,648 条机器指令，也不等于 guest cycles。FR 和 TA instret 合法地不同。

## 2. 六项目标 judge 负控是否造成重复算术

**没有重复运行 QKV 或量化。** `main.c:109` 只在 dataset1/arm0 的一次功能调用之后执行 `controls`；每个变异只修改现有结果/指针，调用 judge 后恢复。六个负控不在任何计时窗内，且不会每窗再做。与早先 C8 反复执行完整算术自检的情形不同，现阶段没有证据支持为了节省预算先改这个 main。

正常完整进程有 14 次常规 judge、6 次变异 judge、1 次恢复 judge，共 **21 次 judge**；加 3 次单独量化探针，共 **24 次 quantized**。其中 15 次 judge 全程通过，6 次按下表提前返回。以下为原 C 分支的逻辑比较/乘加次数，假设正例原本完全正确，且每次只注入指定单点错误，不冒充最终机器指令条数。

| 变异 | q 比较 | scale 比较 | y 比较 | slot 参考 MAC | slot 低32比较 | slot 高32字比较 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| q[0] 翻转 | 1 | 0 | 0 | 0 | 0 | 0 |
| scale[0] 翻转 | 288 | 1 | 0 | 0 | 0 | 0 |
| K输出[0] 翻转 | 288 | 9 | 289 | 256 | 8 | 24 |
| V slot0 high[2] 翻转 | 288 | 9 | 864 | 544 | 17 | 51 |
| y尾 guard 翻转 | 0 | 0 | 0 | 0 | 0 | 0 |
| context.fp 指向 dataset0 | 288 | 9 | 864 | 768 | 24 | 72 |
| 六变异小计 | 1153 | 28 | 2017 | 1568 | 49 | 147 |
| 恢复 judge | 288 | 9 | 864 | 768 | 24 | 72 |

加入所有正常检查及独立量化检查后，全进程逻辑比较为 q=6337、scale=190、y=14977；slot 参考 MAC=13088、低32比较409、高32字比较1227。guards 被调用25次（fault1+24 quantized），其中仅 guard 变异提前返回。六变异及恢复增加 y 比较2881、slot参考MAC2336，**没有增加完整投影或额外 custom**。

这些数字可用于目标开销预检，但不能单凭逻辑次数保证墙钟够用。全部原始权重 248832 B 仅用于 slot 参考，不应和 packed 权重合并后误删；任何删控/预计算都会改变新 ELF 与目标审计条件，必须另开明确修订，不能静默改变已冻结 v1。

## 3. 直接复用供体运行器的具体风险

| 位置 | 已读源码事实 | 新 0f 适配要求 |
| --- | --- | --- |
| active/target/generate.py:10,85 | 旧合同名、separation_threshold_ratio=[199,200] | 新合同身份和 97/100；不能仅改文字 |
| active/target/run.py:84-97 | 1%锚点正确，但收益仅0.5%；qualified仅反映stable | 使用新3%策略，明确功能/锚点/收益资格分离 |
| active/target/run.py:160-171 | positive=98000/100000，即2% | 新3%下该样本必须拒绝；不得沿用旧positive期待 |
| caller/split/run.py:282-290 | normal()返回即记PASS，继续replay；selection失败本身不抛错 | recovery之后先检查correctness、所有计数、anchor、3%gain，任一失败即停止，不进入第3进程 |
| active/target/run.py:199、runtime_experiment.py:157-168 | 默认identity-02.json，并硬绑定T17 parent/profile SHA | 必须新建0f实物身份适配；不能放宽旧T17 gate后冒充相同证据 |
| caller/split/run.py:246,269,275-280 | 临时构建negative；依赖vdot env、vd=0、bit100、第一custom PC及0x0388000b | 复用已核验负控NEMU必须同时核验其实际开关和首PC语义；不以文件名代替绑定 |
| active/target/run.py:135-145 | O2_TRACE_PASS、两槽、全部custom PC顺序和计数硬绑定 | 新0f observer schema/信号及最终ELF PC必须审计适配，不删掉路径约束 |
| caller/split/run.py:255,272 | 128MB guest RAM、guest cap以及固定7200秒 | guest RAM不等于宿主RSS；新runner另设实际RSS、日志、线程与monotonic预算 |

新 `probe_policy.py` 已进行只读审查（SHA256 `64a48cc65205ddd10a177d4b44ff8436d85948f28433e803b5b7b5417b812c54`）：强制六窗、原顺序、正整型cycles，四FR和两TA全保留；`100*max(FR)<=101*min(FR)` 与 `100*max(TA)<=97*min(FR)` 均正确。其14项自检是合成门槛测试，不能记为目标性能结果。本子审查未执行该测试；root报告的测试结果须另由实际日志承载。该函数只做周期筛选，需由新runner外层先完成镜像、功能、DiffTest、CSR/路径/计数门禁。

## 4. 7200秒上限需要明确的前置判断

拟定最多3个串行进程：fault最多1M guest/300秒，normal与replay各最多18M guest/7200秒，总最多14700秒；每进程RSS≤12GiB、日志≤2GiB，亲和核4–7且最多4线程。这些可以作为**不可自动增长的硬上限**，不证明正常进程一定能完成。

本机已有 C8 R1 证据可提供谨慎的预算参照。已重新核验下列归档的压缩/解压 SHA 与其 manifest 一致：`../deferred-reduction-c8-d0-r1/evidence/payload/clock-audit.json`、`runs/02-A_normal_recovery/record.json.gz`、`stdout.log`。其正常进程为 1,527,663 guest cycles / monotonic 3065.826605928秒，约 **498.2875 guest cycles/秒**。同一记录的 Host time=2854350ms 与 UTC 显示间隔较短，限制必须沿用 monotonic，不能换时钟缩短耗时。

在这一历史吞吐下，7200秒约相当于3.588M guest cycles，远非18M。作为粗略风险判断，供体14个QKV边界按其约25万cycle/边界已接近3.5M，再加启动、校验与日志；这只是跨输入/机器的**预算风险估计**，不是本机QKV预报或新的测量，不应记入性能档案。新0f执行可能更快或更慢，因此不能写“预计53分钟即可”。

建议下一轮在任何EMU前完成：

1. 用新 ELF 冻结以上全部调用/量化/校验次数、实际路径长度、日志事件计数及预计最大日志体积；核对既有0f历史样本的身份/模式是否可比。
2. 读取本机可用RAM/并发负载，确认12GiB预算不会触发WSL swap压力；核4–7实际存在且所有EMU线程受限，持续记录RSS、日志和monotonic时间。
3. **不为了校准自动追加第4个进程。** 在normal同一进程设置事前冻结的进度/预算检查点，依据其已完成阶段和剩余固定调用保守评估。该检查只可提前停止资源不合理的运行，不能因速度较慢自动提高预算或改变采样计划。
4. 若静态/历史证据不足以允许在7200秒上限下开展完整normal，应先报告预算未就绪；单独校准应另轮明确授权，并独立合同，不从3进程配额外偷跑。不能把fault启动速度外推完整QKV吞吐。
5. normal正确但anchor/gain不合格也应停止，不重放、不删窗；normal超时记TIMEOUT/INCOMPLETE，不硬归因于候选性能。只有全部门禁通过才进行同BIN replay，replay不是额外统计样本。

## 5. 采用建议

本轮原样14边界软件计划与6项轻量judge负控可保留；无需先为删负控修改main。下一轮最小工作应是0f身份/observer/selector及有界runner适配、静态开销复核。必须先把真实0f观察器开销纳入预算准入；证据不能支持在硬上限内完成或需要扩大预算时，应HOLD，不能启动正常进程，也不能自动另开试跑。本轮不提高预算。498 guestcycles/秒只属于旧工作负载实测，3.5M只属供体量级估算，两者不可相除后保证QKV的ETA。当前结论为**GO进入适配及预算准入 / NOT_READY_TO_RUN**，不能给0f新性能PASS。
