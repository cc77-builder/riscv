# SP1-E B3-R1：四文件冻结修订与宿主准入

**结论：GO，仅限两例宿主准入；本轮没有启动任何EMU/NEMU。**

四项cwd配套输入已从真实B2原冻结精确迁入，17方法及独立29项门通过；CPU4完整宿主预算两例468.345019776/331.801223876秒均低于900秒，正式执行冻结及最终增量复核通过。只完成宿主准入，目标进程0、两例未运行，旧FAIL保留，SP1-E仍15/20。

| 用例 | 宿主预算预留 | 900秒余量 | 执行冻结 | 本轮目标结果 |
|---|---:|---:|---|---|
| legacy-control | 468.345020s | 431.654980s | 1010项，通过 | NOT_RUN |
| o2-all-pairs | 331.801224s | 568.198776s | 1010项，通过 | NOT_RUN |

## 本轮具体修改

仅新宿主runner增加runtime_input_annex及inventory接入。固定真实B2 performance-d0-s03/EXECUTION_FREEZE.json的路径、大小和SHA，从其pins精确提取候选和0f的build/constantin.txt、build/plusArgs四项；annex、原B2清单、旧正式FAIL也纳入执行闭包。四文件均为原字节，不是重新生成。重复、多余、漏项、改来源、同内容换路径、自行改SHA均不得通过。未递归导入B2的大量测试同名文件。

原common/supervisor逐字节复用；角色、预算、guest上限、实际进程身份、资源回执、检查器和八维功能重放保持。原B3目录65文件、HOST清单991项以及445生产源码收口时核验未变。旧闭包FAIL仍保留为FAIL，没有改成PASS。新runner SHA `43af0b919f37da7dccbeea0955ebb0c192f9b34aa43f749e590f9a5bee362d91`。

## 正式验证与执行冻结

源码与测试先冻结，再单次执行17方法（原10方法加7组annex检查），全部PASS。独立输入审计通过，29项独立检查包含真实临时文件删除、同大小内容变化、canonical路径替换、同内容拷贝冒充来源和annex自声明身份的拒错；真实四个文件始终只读。各正式门均只有一次，无失败后重试。

两例先完成1005项完整inventory，其后加入ADMISSION和四项最终回执，每例正式EXECUTION_FREEZE为1010项。最终新增元数据大小与原16MiB/64份预留已独立核验；详见independent-review/FINAL_FREEZE_REVIEW.json。初始独立RESULT里预留的FINAL_DELTA_REVIEW名称，由该最终复核文件明确承接，不改写已冻结receipt。

HOST_ADMISSION不是目标执行授权。没有RUN_AUTHORIZATION，没有被消费的case/批次执行锁，也没有真实target-01输出。budget-review/synthetic-cost-only下的PID、进程标志、日志和采样只是离线成本夹具，不能被解释为真实目标运行或功能PASS；它们未进入真实case输出目录。

## 900秒预算的依据与限制

冻结公式为 `4×(13H+5P+5J+18K+64D+I)+166.949342724≤900`。H完整输入核验取两例较大0.652519480s；J为1.960080438s；K为0.037299352s；D为0.080114831s；I采用新旧较大0.044810048s。P继承身份未变的原CPU4完整日志解析10.244443253s/3.417253458s，明确没有重贴为新目标证据。

准备阶段修正旧成本草案的小日志及重复PID问题。新合成成本夹具含双份完整legacy日志24,558,348B、44,252,950B遥测、30002采样点和四个不同PID/TID；调用未修改的实际receipt/check_cached来测处理开销。夹具身份与生产目标资格分开，测量后没有缩小夹具、降低4倍系数或额外A预留。

两例468.345/331.801秒是公式计算的宿主预留，均不是全核实际运行时间。证据适用于CPU4、现有页缓存和冻结工作量；不是任意2GiB极限日志、冷盘或未来一定完成的保证。原6300目标/7200外层/900宿主、4线程/12GiB/2GiB及guest硬停止不放宽，后续真实执行超限仍必须失败即停。

## 覆盖、指标和接续

legacy完整4组/128检查点/2157架构VDOT、65536B全32向量寄存器、512项vcsr及原7项控制；allpairs完整10例/1158架构VDOT、5120B全32寄存器、每例7CSR、6VIDIV＋6VFDIV下界均保持。bit100、完整128位、退休身份、实际DiffTest及精确重放仍待下一轮目标证据；这两个功能程序没有合格性能计时窗，不替代timed DIV/SQRT。

SP1-E仍15/20；本轮新加速比、面积、时序均NOT_TESTED，历史成绩单独复用。默认仍0f＋firstdot V2＋原C8，候选仍原SP1，不切换。未改RTL、构建新核、运行EDA或写GitHub。下一轮可以仅执行这两例，全部通过后进度才到17/20；其余三个HOLD不自动解除。

[下一轮完整指令](NEXT_STEP.md) · [三项指标与历史成本](METRICS.md) · [预算明细](budget-review/RESULT.md) · [最终冻结复核](independent-review/FINAL_FREEZE_REVIEW.md)。
