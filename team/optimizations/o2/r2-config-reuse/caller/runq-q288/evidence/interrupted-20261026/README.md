# 中断 runq Q288 原字节快照

此目录只封存截至 2026-10-26 04:00:57（UTC+08:00）的实际源文件、构建、原始日志与状态。结果与适用边界见[上层 RESULT.md](../../RESULT.md)。

- 实现提交：`835448de73da46a8302351b93cdb399ff598fc85`；旧 v1 实现为 `1632fc66fcf8685af29ea3d1998f37fa8fc4569d`。
- 原始根：`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/runq-q288-20261026-0219`。
- 560 个普通文件，原始总长 59,111,205 字节；不包含符号链接。
- `raw.zip` 为 6,128,333 字节，SHA-256 `ab6596d427684c7c6f278342afed3bc32396bb7d5241d0bc1c163f210e3d93f0`；成员路径前缀 `raw/`，逐文件路径/大小/SHA 见 `manifest.json`。
- 创建时逐成员实际解压并核对 SHA，随后再次核对原件路径集、大小、mtime 和 inode。两个 campaign 均已结束且 `active_pid=null`。
- `campaign-02-user-priority-interruption.json` 保存用户磁盘优先导致 SIGTERM 的原因；`campaign-02/runs/recovery/result.json` 的 FAILED/-15 原样保留；重放未启动。

**NOT_QUALIFIED_COMPLETE_EMU。** 这不是完整运行/搬移审计 PASS，也不是消费者性能结果。取证时先核对 ZIP SHA 和每个成员清单，在新的外部目录解压；不要将该快照写回或覆盖现场失败目录。固定 T17 工具/EMU/参考输入仍由原身份记录与现有受保护实物提供，不能把 ZIP 当作自含整机运行环境。
