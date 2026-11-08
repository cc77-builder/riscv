# 下一轮指令

开始 SP1-E B3-R1 两例五角色有界执行，按 NEXT_STEP 先核查已有进程、冻结输入、独立最终增量复核及未消费锁，再为本轮明确创建目标授权，按 legacy-control→o2-all-pairs 串行执行。每例保留300/1500×4秒、目标6300秒/外层7200秒/宿主900秒；整批最多10个目标进程、目标12600秒/外层14400秒，不借预算。负控guest各100000，正常guest分别800000/300000，CPU4、整组4线程、RSS12GiB、每例日志2GiB以及原seed/RAM/reset不变。保持完整覆盖、128位、退休身份、CSR、bit100拒错与正常恢复、八维功能精确重放；这些功能程序没有性能计时窗。任何失败立即停止整批，不重试、不加时、不跳过继续、不扩围；o2-control继续HOLD，不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub。完成后更新计分板的三项指标及资格状态，给出结论和下一轮指令。

## 本轮与下一轮的界线

本轮只完成HOST_ADMISSION和两份EXECUTION_FREEZE，没有RUN_AUTHORIZATION、目标执行锁或目标输出。下一轮必须核对ADMISSION、independent-review/FINAL_FREEZE_REVIEW.json及所有冻结输入，读取真实进程和Issue活动，确认预算/源码适用后才能创建一次性目标授权。RUN_AUTHORIZATION按runtime-tests/API.md和冻结runner协议填写，并核对最终新增元数据总量仍在16MiB/64文件预算内；不得手填GO绕过任何receipt或更改本轮源码。

运行入口仅为已冻结runtime/runner.py的run-batch；不得先手工运行某一角色作为热身。目标仍使用既有0f/SP1 EMU/NEMU和两例原ELF/BIN，不重建。任何输入身份或预算前提变化就HOLD，禁止在已冻结目录原地修复继续。

两例全通过后SP1-E由15/20到17/20；o2-control、原C8普通C48、新timed DIV/SQRT仍是三个独立HOLD，不自动启动，也不据此切默认。
