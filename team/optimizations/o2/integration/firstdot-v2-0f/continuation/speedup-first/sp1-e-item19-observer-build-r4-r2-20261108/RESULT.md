# 第19项构建入口 R4-R2 结果（记录112）

结论：**宿主准入 PASS；一次真实构建 FAIL，后续 HOLD。正式验收仍为19/20。**

开始：2026-11-08T00:10:44.745504+08:00；归档：2026-11-08T00:27:43.673220+08:00。本地分支 `local/zjhwork-integration-20261024`，未提交，基点 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`。默认仍为 **0f＋firstdot V2＋原C8**。

## 实际完成与停止位置

|项目|本轮结果|
|---|---|
|Make续行解析|合并反斜杠LF/CRLF后解析唯一逻辑命令；原参数逐项相等|
|已有验证复用|R4-R1闭包10项、适配器6项；原日志、源码副本和导出器类文件保持|
|新差异与冻结检查|14项PASS；24,596个源文件复用；完整文件输入清单冻结|
|真实有界构建|一次，490.888秒，make退出2；未重试、未加时|
|JVM导出|PASS，110.053秒，进程已退出|
|独立firtool|PASS，378.512秒，进程已退出；与JVM无采样重叠|
|资源|峰值RSS 9.692GiB／16GiB；峰值25线程；未触发时间或RSS限制|
|原Make后处理|FAIL：`coupledL2/.git`不被Git识别|
|Verilator/C++原生EMU编译|未到达；无新`build/emu`|
|运行后身份|冻结文件内容、根Git逻辑身份复核PASS；无残留构建进程|

原始FIR为1,038,022,048字节，`SimTop.sv`为832,917字节；构建目录1687个文件已在`PARTIAL_BUILD_PINS.json`逐项留档。SV存在只说明firtool输出完成；原Make的Git版本信息、断言等后处理未完成，不能当作完整构建成果，也不能直接依赖mtime继续make。

## 失败原因与证据边界

文件清单复制没有保存空目录。只读比较发现副本缺少629个Git目录，127个Git目录中原副本可识别127个，本轮副本仅3个。`coupledL2/.git`内的文件存在且哈希保持，但缺失`refs`等目录使Git仓库失效。原Make已留下217字节`.__head__`和空`.__diff__`，与Git版本差异后处理失败相符。

这不是RTL功能失败；也不是已完成第19项。文件内容冻结通过不等于目录结构闭包完整，本轮保留这个冻结盲点。未修复Git目录、未重跑后处理；旧FAIL、旧锁和本轮失败均保留。

## 三项指标与采用

本轮加速比、面积、时序均为 **NOT_TESTED**。分场景历史性能与Nangate45 FU/父级五档STA见[三项指标](METRICS.md)，全部明确为历史复用；不把宿主资源值当芯片指标。默认未切换，候选未获新增正式资格。

生产RTL、软件镜像、旧EMU/NEMU未变；没有EMU/NEMU运行、EDA、GitHub上传。下一步仅修复副本Git目录闭包并评审安全接续构建，详见[NEXT_STEP](NEXT_STEP.md)。

## 证据入口

- `FREEZE_CHECKS.json`、`BUILD_ADMISSION.json`、`INPUTS.json`、`EXECUTION_FREEZE.json`：解析和冻结。
- `build-run-01/STATE.json`、`stdout.log`、`stderr.log`、`telemetry.jsonl`：唯一真实构建与停止。
- `PHASES.json`、`GENERATED_CLOSURE.json`、`PARTIAL_BUILD_PINS.json`：阶段回执、生成物与摘要。
- `GIT_DIRECTORY_CLOSURE.json`、`GIT_METADATA_READONLY.json`、`RESOURCE_AND_GIT_SUMMARY.json`：只读归因。
- `POST_INPUT_CHECK.json`：构建后输入不变。
