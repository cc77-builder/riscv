# R3 父级 perf v2 原始证据

本包对应 `20261025-LiZufan001-r3-perf-0001`。177 份载荷、保存字节 4,381,568；[manifest.json](manifest.json) SHA-256：`6a12ae4bb166d16f871375b606a165673a0aa71e49c329138fde9e742c8e49d6`。

## 内容与边界

- `files/run-01`：Mill 直接执行失败；未生成 RTL。
- `files/run-02`：真实 Scala/Chisel、Verilator、正向日志、20 项观察负控、源码／依赖／生成物／二进制身份及真实退出码。
- `files/run-source`：成功运行时的全部修改源与合同快照；未修改的源码由发布基点与 source.json 识别。
- `files/post-source`：最终 gzip 读取版审计器及其固定控制 checker／合同；没有覆盖运行源。
- `files/runtime`：原文／gzip 的最终审计、8 类篡改、T17 实物及消费者绑定、旧网表子集复核、准备／失败状态及运行位置。
- `files/executed-tools`：本轮实际分析及封存脚本。
- [external-artifacts.json](external-artifacts.json)：实际二进制与缓存的原生位置和身份。

大于 262144 字节的文本使用 mtime=0 的确定性 gzip。Manifest 同时绑定原始与保存字节；没有把压缩文件的哈希冒充原始日志哈希。交付回执单列于 [../delivery/](../delivery/)，不循环纳入自身 manifest。

## 离线复算

从包含本次工具的完整团队仓库运行。输出必须是新路径，不需要 EMU、硬件工具、原运行目录或个人凭据：

~~~bash
R3_EVIDENCE=team/optimizations/o4/perf/evidence/r3-parent-v2
python3 -B team/optimizations/o2/result-width/h1/seal.py --verify "$R3_EVIDENCE"
python3 -B team/optimizations/o4/perf/audit.py \
  --control "$R3_EVIDENCE/files/run-02/result.log.gz" \
  --metadata "$R3_EVIDENCE/files/run-02/metadata.log.gz" \
  --negative-checks --output /tmp/r3-perf-audit-new.json
~~~

第一步复用现有 format-1 字节验证函数，输出沿用其历史 `O2_H1_ARCHIVE_BYTE_CHECK_PASS` 名称；这里只表示归档字节核对，**不授予新的 H1 功能、PPA 或整核资格**。第二步才执行 R3 完整控制／payload 复核并做 8 类篡改拒收。单独检查 manifest 不能代替第二步，也不等于重新执行 RTL。

重新生成硬件时读 [CONTRACT.md](../../CONTRACT.md)。工具需按固定版本准备；本机 Mill 文件为 polyglot，Python 直接 exec 会失败，本轮使用 `files/runtime/bin/mill` 所示的私有 Bash 包装。换机器应绑定该机器实际安装的 Mill 路径，不能照搬个人绝对路径。

[结果与消费者判断](../../RESULT.md)准确区分本轮新父级验证、历史成本复用和未新增的完整应用／PPA 资格。
