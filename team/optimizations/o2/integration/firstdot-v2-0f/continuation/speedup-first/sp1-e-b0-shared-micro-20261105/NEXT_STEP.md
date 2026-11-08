# 下一轮：B1 batch三数据集有界执行

六例B0宿主准入已完成。下一轮只执行batch三例，stream三例保留已准入待执行状态；完整SP1-E仍9/20已验。

开始 SP1-E B1 batch 三数据集五角色有界执行：按 NEXT_STEP，先核查已有进程及冻结输入，明确仅 performance-d0-s02、performance-d1-s02、performance-d2-s02，按 d0→d1→d2 串行执行，每例最多5个角色进程。每例保持6300/7200秒、原guest及CPU4/整组4线程/RSS12GiB/日志2GiB上限；整批最多15个目标进程、目标累计18900秒、外层21600秒，预算互不借用。每个正常角色完整12窗、768次custom，VDOT与RVV各自最多2%退化，完整128位、源操作数、退休/CSR、逐窗控制相等及双方八项精确重放全部保留。任一用例任一门禁失败立即停止整批，不重试、不加时、不跳过继续、不自动进入stream。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新三项指标，给出结论和下一轮指令。

## 固定入口与执行前材料

1. WSL主目录为本文件所在的 `sp1-e-b0-shared-micro-20261105`；以 `CASE_ADMISSIONS.json`、`SHARED_SOURCE_VERSION.json` 和各case的 `EXECUTION_FREEZE.json` 为身份入口。
2. 新用户指令后才记录三份逐case及一份整批授权，按 `runtime/batch.py` 的严格schema绑定实际freeze/annex/output摘要。B0没有创建授权文件、消费锁或目标输出。
3. 整批授权文件固定为 `batches/B1-batch/RUN_AUTHORIZATION.json`；逐case为 `cases/<case-id>/RUN_AUTHORIZATION.json`。核查CPU0～3队友保护、CPU4资源及既有进程；先宿主verify，再由共享入口串行调用。
4. 执行入口：`python3 -B runtime/batch.py run <绝对路径的整批授权JSON>`。不得直接循环启动EMU或临时改case/预算。每例目标输出固定为 `cases/<case-id>/target-01`；整批为 `batches/B1-batch/target-01`。
5. 每例依次bit100→候选恢复→0f校准→候选重放→0f重放。上一步完整通过才进入下一步；batch失败不启动后续case或stream。
6. 外层7200秒包括本例实际预检、监督、审计和清理；批次21600秒也包含整批预检。它们是硬截止，不是工期承诺。原negative/normal guest为100000/300000，命令保留16cycle native余量。

本轮GO是进入下一轮有界尝试的宿主准入，不是新候选功能、性能、整批执行或默认采用PASS。
