# 融合目标证据的独立宿主资源适配 v1

合同 `r2-s3-fused-offline-audit-host-budget-v1`。仅用于 `r2-s3-runq-q288-fused-target-v1` 已终结的 negative/recovery/replay 原始证据离线复算；不启动 EMU，不增加性能样本，不改变 98 份冻结输入、官方程序、固定参考、目标周期/超时或任何正确性/性能接受条件。

原团队 fixed-weight archive helper 的新源审计子进程有 180 秒宿主墙钟上限；该数字不属于数值或比较门槛。融合每正常进程有 103,681 条自定义提交，双日志复算与路径重建的宿主开销增大，180 秒存在资源超时风险；仅凭数量不认定旧调用必然超时。本合同预检后直接使用有回执的适配执行，不制造或声称一次未发生的旧路径失败。

保持原 `fused/target/archive.py`、fixed-weight helper、全部软件/原始记录和新源审计判定的字节。适配仅在当前 launcher 的 helper 名字空间安装 subprocess 代理，不替换全局 subprocess。只允许一次精确的 `Python -I -B` 固定 guard / 固定融合审计脚本调用；验证 98 份新源字节、8 个原 denied-root 参数、原 action/capture 调用形态。其宿主上限由 180 改为 **900 秒**；argv、环境、cwd、所有拒绝原始依赖访问的参数及原结果比较原样使用。30 秒 Git 调用不变。

真实子进程在独立进程组中运行，stdout/stderr从开始直接落盘。成功、非零退出、超时和启动异常都写真实回执；超时仅终止自己建立的进程组并保存原始流。临时目录销毁前复制已存在的 guard/audit JSON；未产生的诊断如实标记缺失。完整冻结审计仍必须返回原 `FUSED_TARGET_ARCHIVE_FRESH_SOURCE_AUDIT_PASS`，且完整结果与原始归档相等，才能接受。包装器自身不伪造 PASS、放宽数值或吞掉异常。

先运行三个实际小子进程控制，检查成功、退出7、写两路流后超时均留下正确状态和完整流；这不使用 EMU。真实执行前后保存适配器/本合同、原审计器、98源和原ZIP manifest的 SHA；输出在所有输入之外的新目录。新源 probe 仍为 Python文件/枚举及显式子进程路径检查，不宣称操作系统级 sandbox。

本适配是一个独立可回退的宿主执行入口。原 `archive.py --action audit-snapshot` 保留原样，旧 acc8 完成归档无需重跑。结果、回执、原文以及本适配源码随融合目标交付；未得到真实目标完整结果前不执行该离线全量审计。
