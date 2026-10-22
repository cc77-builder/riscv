# T13 本地证据包

日期：2026-10-15。最终结果 `T13_FAIR_CYCLE_COMPARISON_PASS`。本轮未推送 GitHub；人工复核尚待队友完成。

[结果报告](../../docs/t13-performance.md) · [测量约定](../../spec/measurement.md) · [工具与源码](../../workloads/vdot-perf/README.md)

## 内容与选择规则

- `images-v3/`：48 个原版镜像的源码快照、编译 ELF/bin、反汇编、计划、黄金数据、命令及版本回执。
- `images-stream-v4/`：9 个访存修正版镜像；两种方法使用同一 64 字节对齐输入地址。
- `campaign-v3/`：126 次原版实际运行；其中 27 次旧访存运行完整保留为诊断，统一排除。
- `campaign-stream-v4/`：27 次修正后的访存运行。正式选择合计 126 次运行、108 次全核功能调用、1,404 个性能窗口。
- `support/analysis-v1/`：原始验收结果、每次运行检查、全部窗口/配对/汇总 JSON 与 CSV。原始三次重放均保留，逐窗口完全一致。
- `support/calibration-02/`、`support/smoke-build-02/`：正式 fence 校准的 13 个窗口及编译工件。01 版与旧 EMU 预检仅作诊断。
- `support/host-tests-01/`：18 项单元测试、实际 C 判定器错误注入、14 项实际工件损坏测试；这些是主机检查。
- `support/reference-02/`：49,900 次固定 NEMU 序列执行，属于参考层；01 版接口失败日志及 compact 编译失败回执也保留。
- `hardware-build/`：固定硬件源码、依赖和构建参数摘要；失败与成功构建日志均保留。
- `figures/`：全部阶段配对比值图、可编辑 PDF/SVG、选择记录与图形 QA。

日志用 `.log.gz` 无损压缩；校验器解压后比对原始字节摘要，不把压缩后的哈希当作原运行哈希。`archive-files.json` 对核心原始材料逐一记录原始与归档摘要；`file-manifest.json` 另外覆盖最终包内全部文件（不含该清单自身）。

`external-artifacts.json` 固定 EMU、NEMU 参考库和启动 flash 的摘要；这些大体积外部二进制不随包分发。离线校验不需要它们，重新执行硬件时必须另行获得匹配工件。本地依赖曾以共享 Git 对象方式克隆，构建源 manifest 记录了依赖版本；不能仅复制原开发目录就假定依赖独立可用。

## 离线复算

在完整仓库根目录，或包含配套源码/模型数据的 review-snapshot 根目录执行。需要 Python 3.10+，仅标准库；输出目录必须尚不存在。

```bash
python3 -B -m unittest discover -s team/workloads/vdot-perf -p 'test_*.py' -v
python3 -B team/workloads/vdot-perf/verify_archive.py \
  --archive team/evidence/t13-performance-20261015 \
  --output /tmp/t13-offline-review-new
```

Windows 可将 `python3` 替换为本机 Python，并指定一个新的 Windows 输出目录。预期最后出现 `T13_OFFLINE_REPLAY_PASS`，且 `recomputed_result_identical=true`。复算校验原始字节、源码再生成、ELF、计数器事件、全部样本和最终比值；它不是再次执行 RTL，也不代替团队人工评审。

每个计时窗口包含共同 fence 和控制开销，不减空窗口周期。通用调用的 CSR 管理开销、首次访存的顺序影响、被排除的原访存版本均在报告中说明。
