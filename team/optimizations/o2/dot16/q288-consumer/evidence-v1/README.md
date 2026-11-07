# Q288 原始证据归档

本目录对应 [RESULT.md](../RESULT.md) 和 [REFERENCE.json](../REFERENCE.json)，合同 `r3-dot16-q288-consumer-v1`。

| 文件 | 身份 |
| --- | --- |
| evidence-01.zip | 1495216B，SHA-256 `9056f62f93718b2afbe1dcea103b15b64f70292ae27546b78f544bb2249915f9` |
| manifest.json | 33836B，SHA-256 `c2b51be3df377f76cf631bc2d2e6b9bbb42a7af93f853f75c86f5d7493a4a7ce` |

ZIP包含111个原文件，共9918838B，以及内部manifest。每个成员的原始路径、字节数和完整SHA列于manifest；实际归档操作逐成员验证CRC和SHA，并验证原文件前后不变。归档原操作 `0844a5921b2fa4d9e47903bfc930fdee.33573b01fbe3d530c1098d3251cb6f8a` 于2026-11-06 15:44:55.511–15:44:57.411Z完成，exit0、cleanup=true。

## 重点入口

以下为ZIP内相对路径：

| 路径 | 用途 |
| --- | --- |
| files/image-01/ | 实际新ELF/BIN、源码、构建命令与日志、派生及ELF绑定检查 |
| files/preflight-01/ | 第一版运行器及预检原件，未据此启动guest |
| files/preflight-02/ | 唯一目标运行使用的第二版运行器及80项冻结profile |
| files/latch-probe-01/ | 真实子进程取消/句柄交接/清理探针 |
| files/target-01/ | 唯一目标的原stdout、stderr和FAILED状态 |
| files/controller-03/ | 行首筛选修正后的run.py、唯一变换证明、audit.py及原失败主机回执 |
| files/offline-audit-01/ | 原失败复现、同raw通过、三项负例、原件副本及身份检查 |
| files/windows/ | Windows控制器副本、实际构建/探针/目标与审计回执、历史launch plan |

原目标由controller-02执行：EMU exit0，外层host exit1；`files/target-01/status.json`保持FAILED。controller-03只修正协议行选择，将含任意位置Q_改成行首Q_/QW；原generic failure gate及完整顺序检查保持。离线审计原操作 `0844a5921b2fa4d9e47903bfc930fdee.c189e2a0a8190b38732de506fd4dd2cc` 正常完成，无新guest。其result为离线复核PASS，不能反写或替代原目标失败记录。

三项负例的实际输入/结果已包含：缺Q_CALL、保持43行的QW重复/缺索引、未知Q_行。五项guest共享judge故障控制、29完整Q、8352输出及10个CSR窗口均按原合同解释；不授予完整forward、正式performance、完整退休窗口或ASIC资格。

## 复现与保留边界

可从归档读取原始证据并按manifest核对成员。重新执行已有image.py或audit.py需要准备其记录的冻结输入；这些工具的路径与profile针对原常驻WSL环境，不承诺解压后可在任意机器直接运行。

完整EMU、feature1 NEMU、编译器及原AM依赖不重复打包，保留在profile记录的物理路径，并以完整SHA固定身份。新运行应使用新输出位置及经审阅的新profile，不覆盖原target、原FAIL或原离线审计。本档案没有硬件重建、ABI探针、额外guest或whole2实验。

Windows固定审阅副本位于 `D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\runs\dot16-q288-20261106-pro3\review-03\`。原件仍保存在 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-q288-20261106-pro3/`。review-03仅为审阅副本，ZIP成员清单以本目录manifest为准。
