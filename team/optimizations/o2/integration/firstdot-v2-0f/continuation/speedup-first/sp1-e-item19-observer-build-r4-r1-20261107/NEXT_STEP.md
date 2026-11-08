# 下一轮：R4-R2 完成冻结并构建

开始第19项构建入口R4-R2：仅修复Make干跑输出的续行解析，复用R4-R1的10项闭包、6项适配器检查及24,596文件源码副本，不重新编译或重复已过检查。补齐完整输入冻结与准入后，执行一次3600秒总预算、16GiB有界构建。保留原FAIL，失败即停、不重试、不加时；不运行EMU/NEMU、不改生产RTL或软件镜像、不做EDA、不切默认、不上传GitHub。

## 直接复用的现场

- 修订Export.scala已通过默认与disable-all两组共10项闭包检查；FIR、内嵌注解、尾部和完整RTL目录文件逐字节一致，重复侧文件已解决。
- BUILD_HOST_RESULT.json记录6项适配器检查通过，包括原参数映射、错误参数/路径拒绝、阶段wait/reap及非零失败传播。
- SOURCE_COPY.json记录24,596文件物理副本，目录`/home/riscv/riscv-lab/item19-observer-20261107/build-03/source`。没有build输出，不要再复制全仓或借其他已有EMU。
- 本轮make-dryrun.stdout/stderr是原Make sim-verilog干跑，返回0。命令包含反斜杠续行；冻结脚本只取第一条物理行交给shlex.split，发生No escaped character。FREEZE_FAILURE.json保留真实失败。
- 现有日志离线拼接逻辑行后，参数和原合同精确相等，原Make后处理标记完整；见FREEZE_PARSE_DIAGNOSIS.json。这是失败后只读诊断，未据此改回PASS或执行构建。

## 最小接续

把冻结程序保存为文件，在解析时先合并反斜杠续行，再用shlex.split提取完整mill命令。直接读取已冻结的原干跑日志，不需要再次执行Make干跑。只做该解析的必要正负控和剩余源码/外部依赖/旧输入保护冻结；保留旧失败脚本片段和新身份。不要重编Export.scala或重新执行已通过的10+6门。

BUILD_CONTRACT.json、BUILD_ADAPTER.json、build_once.py、mill_adapter.py和bin/mill已准备，但完整INPUTS.json/EXECUTION_FREEZE.json未生成，BUILD_ADMISSION.json为HOLD。补齐这些输入之后才能启动一次构建；此前不得手工把HOLD改成PASS。复用冻结B1编译缓存与新导出classes，阶段顺序为导出JVM完成并回收→独立firtool→原Make后处理/原生EMU编译。

总3600秒/聚合RSS16GiB/CPU4–5/线程128/日志2GiB保持，不按阶段重置预算。R4-R1实际全核构建0次、预算使用0秒；未创建RUN.lock或ADAPTER.lock，不存在需要继续等待的构建进程。正式19/20，默认0f＋firstdot V2＋原C8不变。
