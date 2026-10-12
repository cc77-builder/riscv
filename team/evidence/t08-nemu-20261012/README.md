# T08 NEMU 实际验收证据

日期：2026-10-12（北京时间）。团队基准 `4d04e6b9f`；本轮未提交代码按补丁、源文件、配置及二进制摘要识别。NEMU 基线 `a48a11f208ff81ad765591d83271d1b339fb3861`，应用 `vdot-s8x8-r32-v0.1` 补丁 1.0.0，启用 CUSTOM_VDOT。

| 原始记录 | 结论 |
| --- | --- |
| [selftest](selftest/run.log) | 5 个 harness 用例和两项负控通过，退出 0 |
| [full](full/run.log) | 80 合法/算术 + 35 异常，115/115 通过，退出 0 |
| [random](random/run.log) | 48 定向 + 1,000 随机 + 35 异常，1,083/1,083 通过，退出 0 |
| [reproduced](reproduced/run.log) | 新检出应用交付补丁、独立构建后 115/115 通过，退出 0 |
| [standalone 构建](standalone-build/build.txt) / [配置与二进制版本](standalone-build/provenance.json) | 构建通过；重新调用交付脚本复核已应用补丁和重复构建 |
| [reference 构建](reference-build/build.txt) / [版本](reference-build/provenance.json) | 独立共享库构建通过 |
| [reference 链接](reference-build/link-check.txt) / [加载](reference-build/load-check.json) | 无未解析符号；实际动态加载及四项主要接口存在性检查通过 |
| [hello/vadd](hello-vadd/run.log) | 原程序 3 组/24 lane 通过，使用示例标识，不代表 T04 实际团队标识验收 |
| [Python 测试](model-tests.txt) | 14 项测试方法通过 |
| [相邻编码](encoding-review.json) | 补丁后 10 个相邻字不匹配 NEMU 主表；717 个香山命名表项静态解析无冲突 |

[summary.json](summary.json) 从实际日志中的数量、模式与退出码提取，不是替代运行的合成日志。完整原始日志保留 PASS、负控失败结果、初始化信息及最终 GOOD TRAP。所有记录均不宣称运行了 RTL/NEMU DiffTest。

各目录保存输入/源码/二进制摘要和实际 NEMU 配置。两种构建的 base SHA 仍是原提交，实际扩展版本必须同时引用 patch-manifest/provenance。脚本会禁止源码漂移；此处的新检出复验由同一协助工具执行，非作者环境复验仍待完成。

[packages.txt](packages.txt) 记录本次 WSL 构建依赖版本；编译二进制和全量生成数据留在 `team/out/`。本目录 `.gitattributes` 保留原始字节；`archive.sha256` 使用相对路径校验归档文件。SHA 文件中的绝对路径是本次原运行位置。

复现命令及测试范围见 [T08 记录](../../docs/t08-nemu.md)，补丁入口见 [NEMU 交付](../../patches/nemu/README.md)。真实 RTL、全核差分、故障注入、OoO 配置依赖和取消覆盖属于后续 T06/T07/T10/T11/T12。
