# R5/G5 冻结候选与工程验收入口

本目录按 [合同](CONTRACT.md) 做冻结与验收；最终状态以 RESULT.md 和 record.json 为准。freeze.json 是含未提交修改的文件快照身份，HEAD 不能代替它。当前阶段未授权发布，不产生提交或 GitHub 写入。

## 使用哪一版

- 硬件：0f12df675378556670afd0dd2153f47fcb330610，O2 两槽、H1 低32位保存、DIV取消保持修复；MinimalConfig、单核、VLEN128。
- 完整四尺寸软件入口：既有 firstdot V2，4×8 / 8×32 / 16×64 选 reuse vdot，4×13 选 reuse RVV。
- 8×32 配置复用：通过独立 [C8 包](../package/c8/README.md) 显式选用；完整普通C接入程序位于 [relink/source](../package/c8/relink/source/)，[重建命令](../package/c8/relink/README.md)。不添加混合调度或隐式切换公共默认。
- RVV 回退：C8 显式调用 xs_c8_gemv_8x32_rvv，或重编选 XS_C8_GEMV_FORCE_RVV=1。其包级可编译资格不自动转授为新整程序的运行成绩。
- 当前实物：WSL 外部根 /home/riscv/riscv-lab/software-import-20261026，C8 SDK 在 c8-package-01/sdk，最终测试镜像在 c8-relink-01/integrated。路径属于本机证据身份，搬迁时需按合同重新绑定，不能随意改旧锁。

## 冻结和恢复

freeze.json 固定所有本轮开始时的24,157个非忽略常规文件（导航文件除外），也包含历史失败材料，并不表示全部历史候选都被采用。
外部 r5-g5-acceptance-01/frozen-workspace.tar.gz 保存这些文件并逐项回读验证，摘要记录在对应 .json。
该快照不含 .git 历史和仓库外子库/工具/构建缓存，不能宣传为单包离线重建环境。
恢复时仅解包到全新空目录，并逐项校验 freeze.json；不要覆盖现有工作区。
完整依赖、子库、NEMU补丁及工具身份沿用 clean-02/identity/current.json 与其 build/support 清单；
[干净复现工具](../clean/)和[完成记录](../continuation/clean02-final/README.md)保留实际独立检出与构建命令。同机已装工具和下载缓存复用，不是新机器人工复现。

## 补跑与离线复算

clock_supplement.py 只新执行控制诊断1项，并重新解析原13项；参数 --source/--adapter 必须指向 clean-02/checkout/source 及其本目录对应 clean 子目录，不能指向准备目录中的同名适配器。
它使用新的输出目录，原始失败和所有既有记录不覆盖。
audit_composite.py 仅离线重验完成的13+1组合，0新EMU；不把旧14项批次重新标成墙钟PASS。

本机实际命令保存于 evidence/ 中的 *.command.json，生产RTL无修改。数据档案保留原墙钟受限条目；新组合另记。
