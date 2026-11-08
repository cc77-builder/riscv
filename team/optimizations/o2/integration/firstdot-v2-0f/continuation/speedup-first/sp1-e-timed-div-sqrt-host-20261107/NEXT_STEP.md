# 第20项下一批：三角色完整调用校准（尚未执行）

当前：宿主准备GO；正式五角色预算HOLD。第19项F2v压力补测暂存，正式18/20，默认0f＋firstdot V2＋原C8。本轮不是目标准入授权；不能自动调用launch_target.py。

## 已完成可复用

- G0原GNU/对象/链接、41项测试和40项fake ABI证据，137文件身份一致；ELF/BIN及bit100参考库不改、不重编译。
- 本轮11项适配方法闭合（8项复用未变通过、3项最终受影响检查），候选及0f合成完整54窗/432操作通过；完整当前组与guard的e64/e8/e64上下文适配通过。原两次宿主失败保留。
- 共享supervisor/watchdog/common/runtime_gate原样复用，3角色按硬件选择真实EMU和cwd；冻结35项输入，包含4个cwd配套文件和完整加载源码。无RUN_AUTHORIZATION、EXECUTION_REQUEST、LAUNCH.used、BATCH.used及target-01。

## 获得下一条执行授权后同轮完成

1. 先核对Issue活动、实际进程/资源、EXECUTION_FREEZE全部SHA及host/RESULT。核实未用入口与输出不存在，不触碰其他包运行或旧锁。保持第19项暂存。
2. 保存该轮真实用户指令为新的EXECUTION_REQUEST.txt；生成与当前operation_id、CONTRACT、EXECUTION_FREEZE、host/RESULT SHA绑定的RUN_AUTHORIZATION.json。它必须采用当前真实执行指令，不能复制本轮宿主请求充当执行授权；不改冻结输入。
3. 通过launch_target.py启动一次外部监督；实际脚本见本目录。串行bit100→candidate-normal→baseline-normal，三角色均限一进程，不扫描、不重试、不加时、不缩减54窗。完整资源与身份回执必须通过，不能只调用日志函数就算目标PASS。
4. 每角色按CONTRACT的300/1500/1500秒、10万/100万/100万guest，目标累计3300、宿主900、外层4200秒。CPU4、整个进程组4线程、RSS12GiB、合计日志2GiB，seed1/RAM128MiB/fresh reset/no snapshot。EMU max-cycles命令按既有机制扣除16拍监控余量，不擅改guest合同。
5. 两核完整结果通过后，逐窗控制/普通debug数据及432次归属必须相等，9格各自比较4个计分窗均值，超过2%即停。数值/CSR/指令身份/取消终态/超限任一失败停止剩余角色；保留原始stdout/stderr、收据及所有FAIL。
6. 收口仅给完整调用校准结论和预算评审；没有本轮同核重放，不提升18/20。若得到可靠完整样本且预算成立，保留这三角色作为固定身份证据，只提出必要两次重放的新合同。不得自动进入重放或宣称第20项通过。

70分钟是外层停止上限，不是保证完成时间。完整调用的真实墙钟/guest/日志量目前NOT_TESTED，不引用其他程序吞吐保证完成。

## 可复制指令

> 开始 SP1-E 第20项 timed DIV/SQRT 三角色完整调用有界校准，按 NEXT_STEP 先核查进程、冻结输入和宿主准入，接受本轮独立预算后串行执行 bit100拒错→候选正常→0f正常。分别300秒/10万guest、1500秒/100万guest、1500秒/100万guest；目标累计3300秒、宿主900秒、外层4200秒。保持完整54窗、432条DIV/SQRT、完整128位和CSR/退休绑定、逐窗控制相等及9格各自最多2%退化，沿用CPU4/整组4线程/RSS12GiB/日志2GiB。失败、未拒错、超限或退化即停，不重试、不加时、不跳过继续、不自动重放；第19项继续暂存。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub，完成后更新计分板并判断正式预算和必要重放。
