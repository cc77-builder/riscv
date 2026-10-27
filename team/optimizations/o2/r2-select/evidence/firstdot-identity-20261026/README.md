# firstdot V2 清单硬件身份修复

操作 20261026-LiZufan001-r5-identity-0203；原软件基点 926b2e2a。

原验证器核对了固定 T17 原件，却没有把公开清单中的 hardware 三字段与
该身份比较。真实反例只把 emu_sha256 改为 64 个零，原 CLI 仍 exit 0、
R5_FIRSTDOT_STABLE_SOURCE_PACKAGE_PASS。反例后原清单逐字节恢复。

本次在固定输入 SHA 检查之后、原文审计与 GNU 构建之前，强制比较
source_commit、emu_sha256、reference_sha256 的完整字典。预期值来自
已经固定哈希的 identity-02.json；原来的 T17 语义/原文审计仍继续执行。
结果同时记录实际绑定的 hardware。原清单只更新验证器自身 SHA。

实际 CLI 回归拒绝 7 类错误：三个身份字段分别伪造、hardware 缺失、
hardware 为列表、多余字段、缺少 EMU 字段；每例都因明确身份错误失败，
且没有进入构建。合法清单随后通过完整原文、GNU 三模式、V1 回退、
错误库/配置和搬移 SDK 验证。完整对象仍为 27,416 B，SHA256
b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af。

原合同、V1、firstdot 汇编/头、旧证据、RTL 和官方程序没有改变。
新增 EMU/NEMU 为 0，不新增应用性能资格。
[清单](manifest.json)给出每一归档成员的 SHA；[原始载荷](payload.zip)
包含反例、7 次 CLI 拒错、合法全量验证、前后源码和执行脚本。ZIP CRC 及
全部成员原字节哈希已读回验证。

复核修复可运行当前 verify_firstdot_stable.py 的正常 CLI；针对性回归脚本
在载荷 source/fix-and-regression.py 中，其原地实验入口有原版本 SHA 和
反例终态门槛，不应对新版本盲目重放。负例 JSON、命令输出和明确错误都已保留。
