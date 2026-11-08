# 验证结果

2026-11-08 在本分支最终提交上执行的检查。命令见[复现说明](REPRODUCE.md)，整理阶段的命令记录和日志在 [verification/](verification/)。

| 检查 | 结果 |
| --- | --- |
| 交付文件清单 | `python3 -B submission/verify.py`：全部文件 SHA-256 与 [MANIFEST.json](MANIFEST.json) 一致；`src` 树为 `78a0c93852dced038f645205e33d36a520fedfcd`，与受测硬件提交 `0f12df6753` 相同；10 个子模块固定提交一致 |
| 参考模型与确定性数据 | `team/scripts/check-vdot-model.sh`：35 项测试通过，5 个数据文件重新生成后逐字节一致 |
| 静态接入 | `team/scripts/check-vdot-integration-source.py`：32,768 个寄存器编码组合、17 个固定位邻域、22 个定向与 10,000 个随机向量全部通过；NEMU 补丁 SHA-256 `6c165bf5…5f24db` |
| 宿主检查器 | `team/tests`：146 项通过 |
| GEMV 工作负载工具 | `team/workloads/o3-gemv`：35 项通过 |
| 日志读取工具 | `submission/logs/test_read_log.py`：7 项通过 |
| 归档日志 | `read_log.py verify`：9,679 个归档成员校验通过 |
| firstdot / C8 | 两套软件库重建成功，示例编译与可重定位链接通过，C8 `gemv.o` SHA-256 为 `f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3`，与固定身份一致（见 [verification/](verification/)） |
| 最终两槽 FU 与 VFEX4 父级 RTL | `team/scripts/check-vdot-o2.sh fu`、`parent`（mill + Verilator 5.052）：FU 10022 组向量通过、连续请求 10021 次每拍发起，4 种注入故障全部检出；父级正向回放通过，16 种注入故障全部检出。日志见 [verification/o2-check-20261108/](verification/o2-check-20261108/) |
| 微基准重测程序 | `team/workloads/unified-vdot/retest.py`：10 项单元测试通过；16 个镜像在 Linux 上构建成功；smoke 镜像在本机 EMU 上运行两次均为 `SMOKE_RETEST_PASS`。记录见 [verification/performance-retest-20261108/](verification/performance-retest-20261108/) |
| 报告 | 四份 PDF 的 SHA-256 与 `reports/output/build-receipt.json` 一致；封面队名“啊对对对对”；正文无占位 |

报告中的周期、面积和时序数据来自各实验的原始运行，日志按原路径保存在 [logs/](logs/README.md)，可用 `read_log.py` 查找和阅读。
