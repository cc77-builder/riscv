> 当前统一分支状态（2026-10-17）：完整旧 pilot 硬件流已重放通过，见 [回执](../../evidence/james-sync-20261017/o0-trace.json)。下文环境/下载限制是来源分支当时记录；O0完整矩阵仍未关闭。当前解析器固定摘要以 analyze.py 的 PARSER_BLOB 为准，整合依据见 [复核记录](../../docs/james-sync-20261017.md)。

# O0：归档来源核验与真实轨迹重放入口

基点：`492db2d9e2a5041db5e0a7d1dec16555a7e1b205`；唯一发布目标 `cc77-builder/riscv:zjhwork2`。本批是 O0 的推进，不是 O1 RTL 优化，也不是最终 T16 报告。

## 已实际完成与未完成

本次已把一个预先选定的 T14 batch128 样本的 `analysis.json`、运行 `result.json`、原始 `stdout.log.gz` 搬到执行容器，核对 Git blob，解压后再检查 SHA256。12 个原始程序计时窗口逐项与分析记录一致，运行身份、镜像/EMU/reference/flash 摘要以及正常完成顺序通过检查。

**尚未完整搬运和重放该样本的硬件 `stderr.log.gz`；O0 未关闭，O1 尚未修改。** 该文件确实存在于 GitHub，大小 176,256 字节，Git blob 为 `757ff41dae73226efc6670e6b7c68ccc2a5d7b5d`。不是文件缺失或权限判定。当前容器直连下载遇到 DNS 解析错误，连接器可以返回 Base64 片段，但本次尚未完成整个硬件流的传输。严格重放尝试因执行容器缺少该文件退出 2；没有降级后伪报轨迹通过。

## 为什么增加这个入口

原 `analyze.py` 接受调用者指定的日志、退出码和延迟。它能检查记录内部一致性，却不能仅靠 PASS 横幅证明 stdout、stderr、EMU 和性能镜像来自同一次已归档运行。

新增 `replay_archive.py` 是其外部来源校验层，不改原 O0 分析器和 T12 检查器：

1. 使用 `pilot-t14-batch128.json` 固定原 Git 提交、文件路径和 Git blob；拒绝路径穿越、摘要改变和缺文件。
2. 比较原 `result.json` 与分析记录的两条原始流摘要，核对退出码、单核、仿真线程和实际命令中的镜像、reference、flash、EMU 摘要。不执行归档中的命令。
3. 校验原始 stdout 的 12 条 `T13_P`、六轮 AB/BA 顺序、首次/预热/正式分类、控制自检、唯一成功 summary 和其后的 GOOD TRAP。原始 64 位计数器用整数核对，不转换成浮点。
4. 默认 `--level trace` 必须取得完整 stderr，并核对其压缩存储 blob 和解压摘要，调用原 O0/T12 时钟映射，再与归档 FU 计数和延迟直方图比较。缺少日志绝不退回 program 模式后记成功。
5. 按已校准窗口导出接受间隔和响应同拍 busy 等待样本。FU 观测包含投机请求，与程序点积数分开；跨窗口的大间隔不能解释为单元 II。

默认校验层完整源码和测试见本目录，原 `src/`、NEMU、ISA、T05 数据、`build.sc` 与历史封存证据均未修改。

## 本次真实样本核对

固定样本为旧 T14 性能测试 `performance-d0-s06-r0`：dataset 0，replay 0，四路独立点积乘 32 轮，每个 vdot 窗口 128 次点积。本次选择理由是调查独立吞吐，不是挑选最高加速样本。

| 证据 | 本次处理 | 结果/边界 |
|---|---|---|
| 原运行 result + analysis | 实际读取、Git blob 和跨文件一致性检查 | 同一镜像、同一双流摘要、exit=0 |
| 原始 stdout.gz | 实际解压，核对存储/原始摘要和 12 窗口 | 正式 vdot 周期 `[465,464,464,464]`；RVV `[678,678,678,678]` |
| analysis 中 FU 汇总 | 只核对原记录的计数关系，未从硬件流重新计算 | 原记录为 768 接受/768 响应/0 取消/0 反压、响应 2 拍、最小接受间隔 3 拍 |
| 原始 stderr.gz | 未完成整个文件的传输 | 真实逐拍诊断仍待完成，不报告 busy 等待次数 |
| 52 项主机测试 | 实际执行，无跳过 | 51 项合成/边界检查及 1 项真实程序日志复核；非 RTL 验证 |

不要将这些旧 T14 窗口与新四项目统一基准的 **453.25 cycles** 直接相减。这里也没有测出任何新硬件收益。归档的 768 事务包括六次调用；本次只复核程序日志，不据此独立证明这些事务的硬件行为。

## 复跑

从完整 `zjhwork2` 仓库根目录运行，不需要新建 EMU，也不需要 Mill/Verilator：

```bash
# 默认严格层：完整旧硬件流离线重放；输出必须不存在。
python3 -B team/optimizations/o0/replay_archive.py \
  --output team/out/o0-batch128-trace.json

# 明确选择小范围核对：不会返回 hardware trace pass。
python3 -B team/optimizations/o0/replay_archive.py \
  --level program --output team/out/o0-batch128-program.json

python3 -B -m unittest discover \
  -s team/optimizations/o0 -p 'test_replay_archive.py' -v
```

两种模式都拒绝覆盖已有结果，也拒绝向 `team/evidence/` 内写新文件。工具从已评审的 pins 读取退出码，不允许手填一个 exit=0 冒充原运行成功。pins 和 SHA 用于绑定来源、防止意外混用，不是人工签名或抵抗同时篡改全部工件的证明。

`program` 返回 `O0_PROGRAM_LOG_RECHECK_PASS_TRACE_PENDING`；`trace` 完成一个样本才返回 `O0_PILOT_TRACE_REPLAY_PASS_NOT_FULL_O0`。即使 pilot trace 通过，也还不是全部 O0 矩阵、新 RTL 仿真、O1 父级联调、完整 ISA 验收或新性能实验。原 27 项 O0 测试器未修改；本批新增 52 项测试单独统计。

## 本批证据与接续

[证据目录](evidence/20261017-archive-gate/) 保存本次实际测试日志、程序流复核、严格轨迹重放的阻塞记录及源码摘要。旧证据不覆盖。合成测试调用的是固定的原始 O0 分析器/T12 映射，不是重新写一个近似解析器；合成轨迹不属于硬件运行证据。

接下来先用完整原始 stderr 完成该 pilot 的逐拍重放，之后扩展到冻结的四场景以及方案中固定 256 点积、1/2/4 路、相同/不同输入的诊断矩阵。补齐接受—响应图、空拍原因及尚未证实的解释后，再决定 O1 最小改动。不能只根据汇总中的“最小间隔 3”就把全部差距归到父级 busy。
