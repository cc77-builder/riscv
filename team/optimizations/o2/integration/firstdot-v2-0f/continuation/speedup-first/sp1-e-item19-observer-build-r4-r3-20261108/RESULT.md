# 第19项构建入口 R4-R3 结果（记录113）

**结论：Git目录修复PASS；接续入口宿主检查FAIL，整体HOLD。未启动本轮3600秒构建。正式仍为19/20，默认0f＋firstdot V2＋原C8不变。**

时间：2026-11-08T00:33:44.803702+08:00～2026-11-08T00:41:16.151410+08:00。本地分支`local/zjhwork-integration-20261024`，未提交，基点`347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。

## 实际工作与结果

|项目|结果|
|---|---|
|旧输入与进程核查|无冲突构建；复用原10＋6项及R4-R2的14项证据，文件身份保持|
|Git目录修复|仅创建629个原副本遗漏的空目录；127个Git仓库全部可识别|
|原Make所需版本信息|实际git log和git diff返回0；输出原样保存|
|原始生成物保存|1687文件、1,173,659,670字节物理快照，逐项hash一致|
|独立Resume.mk|原后处理与原生构建配方保留；强制后处理，不依赖SV时间戳|
|宿主通过项|原配方保持、Make干跑展开两项PASS，无JVM/firtool调用|
|真实小样Make后处理|命令退出0；检查器逐字节比较FAIL|
|本轮完整构建|0次，3600秒预算使用0秒；未进入原生EMU编译|
|本轮完整执行冻结|未完成，BUILD_ADMISSION=HOLD；已有成果已归档|
|构建后源身份核查|PASS；真实生成物、旧证据、原输入字节不变，Git逻辑身份不变|

## 为什么停止

本轮新增检查器`resume_guard.py`的`header()`用Python `bytes.splitlines(keepends=True)`模拟GNU sed行首插入`//`。已有Git差异输出包含147处裸回车CR，Python将它们也视为行界，额外插入294字节。GNU sed仅以LF分行，所以小样真实输出与检查器预期不同。

小样真实输出为248,324,454字节；原检查器预期为248,324,748字节。首次差异位于167,356,440字节，出现在历史日志的进度回车中。只读LF模型对比与原始小样输出完全一致，详见`OFFLINE_LF_ANALYSIS.json`。**这是新增宿主检查器的建模错误，不是已发现RTL错误，也不能据离线归因把宿主FAIL改成PASS。**

没有修改检查器后重跑，没有继续负控、完整冻结或真实构建。宿主门执行约18.446秒；它不消耗本轮未启动的完整构建预算，也不能把未使用预算视作继续执行授权。

## 保留与下一步

旧R4-R2 FAIL、锁、日志和所有1687个生成文件保持；本轮源码副本仅新增Git空目录。原始生成物快照在`/home/riscv/riscv-lab/item19-observer-20261107/r4-r2-raw-build`。真实目录的旧`.__head__`/`.__diff__`未被接续入口移动或改写。

下一轮仅修复检查器为LF分行并原样保留CR，使用现有真实小样输出补齐正负控。通过完整冻结后再一次有界接续构建，不重复JVM/firtool，不修改或规范化原Git日志内容。详见[NEXT_STEP](NEXT_STEP.md)。

三项指标本轮均NOT_TESTED；[指标表](METRICS.md)保留历史实测和边界。本轮没有EMU/NEMU运行、EDA、生产RTL/软件镜像变更、默认切换或GitHub上传。

## 证据

`GIT_DIRECTORY_REPAIR.json`、`REPAIR_RESULT.json`、`RAW_SNAPSHOT.json`、`HOST_RESULT.json`、`fixture/stdout.log`、`fixture/rtl/SimTop.sv`、`FIXTURE_DIAGNOSIS.json`、`OFFLINE_LF_ANALYSIS.json`、`POST_INPUT_CHECK.json`。`BUILD_CONTRACT_DRAFT.json`只是未准入草案。
