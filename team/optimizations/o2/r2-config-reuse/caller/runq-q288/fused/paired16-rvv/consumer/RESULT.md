# Paired16 完整消费者参考验证结果

**已验证：新增 `r2_w2_paired16_forward` 在固定模型三个连续位置的完整参考正确性。** 实际 GNU 构建、固定 ELF 的八路机器码审查、负控→恢复→重放均通过。没有启动新 EMU，尚无完整消费者目标整核或应用周期资格；父 paired16 的 `HOLD_CONTEXT_VARIATION` 保持。

对应 [CONTRACT.md](CONTRACT.md) 与 [Issue #2 WORK6675138317](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6675138317)。来源基线为两仓实际核验的 `c981529dc6e493fb7deee8429b9ce05fd197497b`；本叶的具体候选由源码 SHA 和运行清单标识。工程输入与小证据清单见 [provenance.json](evidence/reference-v1/provenance.json)。

## 改动与实际链接

新 API 直接从原 norm/W2 实际父构建的 FR-cache 模板派生，只把 Q/K/V、Wo、W1/W3、classifier 七处 K288 调用改到 P。唯一 W2 行仍为原 `route_fr`，实际 K768 分支选择 `q768_fr`。旧四个 C 消费者、旧公开 API、方法枚举 0–4 与方法 5 非法域均保持。

为复用已经闭合的构建和验证路径，`bind.py` 从固定 SHA 的 GS32 三个自研控制器生成新控制器；所有源码编辑逐项、整文件可逆。历史支持快照、scalar 恢复收据、norm/W2 父、数值验证器及进程 owner 的身份不改。实际生成清单见 [controller-binding.json](evidence/reference-v1/controller-binding.json)。本叶集成应同时保留已交付的 GS32 consumer 固定模板，或保留清单所指的冻结 controller。

| 实际对象 | 字节或身份 |
|---|---|
| 新完整 ELF | SHA `2f7fc718a6c3a388d514392649a1f6fb824f68a1b6d8223eec37855fced63ab9` |
| 新 BIN，95,574,384 字节 | SHA `90da6843776979702f4b4a7574f39946eeb0de1f43327d7b4ab88d70d6a245e1` |
| `q288_paired16_rvv` | 1,096 字节，SHA `a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c` |
| 原四个 K288/K768 汇编函数 | 完整体均与父构建相同；norm 通过原链接身份检查 |
| 实际 build result | SHA `20ea73489949dc0fe4673e635984dc1ae72ce9e679476b34657cc007312ac361` |
| 原数值验证器 | SHA `7273e2c7953bd47321c518bb559c6d2f88f5153d19bd7751bc7b3bc710753285` |
| 原进程 owner | SHA `bee89ca4424110f244560b1ab0529c80fd4e9736dd274c49690026754dbf8475` |

P 的整个函数包含 X=-128 guard 和 592 字节内嵌 FR 回退。新 ELF 完整体逐字等于原 host ELF，并非只提取快速支路。本次三个 token 不宣称覆盖每一种 guard 动态分支；相关 full-s8 域核证沿用未改函数的既有叶级证据。

### 八路实际机器字

`review_routes.py` 检查新 ELF 的完整函数范围、八处函数指针准备及调用，没有使用旧 ELF 地址或仅凭同名符号判断。下表是 `R_RISCV_CALL` 的 AUIPC 地址，实际 JALR 在其后 4 字节。

| 调用点 | 调用 PC | 实际传入的函数指针 |
|---|---|---|
| Q | `0x80005368` | `q288_paired16_rvv` |
| K | `0x80005390` | `q288_paired16_rvv` |
| V | `0x800053b8` | `q288_paired16_rvv` |
| Wo | `0x80005684` | `q288_paired16_rvv` |
| W1 | `0x8000571c` | `q288_paired16_rvv` |
| W3 | `0x80005744` | `q288_paired16_rvv` |
| W2 | `0x800057e0` | `q288_fused_rvv4`，原 FR |
| classifier | `0x80005890` | `q288_paired16_rvv` |

八处实际调用均到 `route_matmul=0x80002e9c`，指针准备段没有覆盖 a5 或直接分支跳入内部。完整与尾 panel 都通过保存于 s4 的实参指针调用。W2 的 `0x80003164` 相等分支跳过 TA 覆盖，最终调用 `q768_fr=0x80000180`。旧 API 的 `0x80006598` 仍将大于 4 的方法返回 NULL；新 API 的 `0x800067d8` 调用 `consumer_paired16_cache=0x80005124`。实际审查结果为 [routing-review.json](evidence/reference-v1/routing-review.json)，SHA `65a3b8f8a0657cfe36b28e523fc5ccfefa85d1b2073da0b09021a35d06731df0`。

## 三个真实参考进程

实际运行固定 `reference-adapter-04` 与原参考库 `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`。使用同一 95 文件闭合支持快照，运行前已重审旧 scalar raw dump；完整数值和清理判据没有放宽。

| 过程 | UTC 开始—结束 | 实际 PID / 退出 | 判定 |
|---|---|---|---|
| GNU 构建外层操作 | 02:28:56.396—02:29:02.623 | Windows PID171636 / 0 | 构建成功，cleanup=true |
| negative | 02:33:32.558—02:33:36.091 | Linux PID389 / 2 | BAD94，原完整状态比较器在 byte152476 拒绝预定单比特差异 |
| recovery | 02:33:36.246—02:33:41.164 | Linux PID391 / 0 | 三步完整状态、模型、flags PASS |
| replay | 02:33:41.319—02:33:46.320 | Linux PID392 / 0 | 完整复现 recovery 的判定与计数 |

全部时间为 2026-11-06。参考外层操作从 02:33:30.202 到 02:33:47.157，耗时 16.916 秒，exit0、cleanup=true；参考子进程均 direct-child-reaped、process-group-absent，最终 active_pid=null。原操作标识与执行 SHA 见 [host-receipts.json](evidence/reference-v1/host-receipts.json)。CPU0 短窗口完成后已释放，没有新增 EMU。

恢复/重放执行 tokens 1、7、19，对应 positions 0、1、2。每步 3,691,424 字节完整状态逐字通过原独立 golden；最终 live state 相同，五个模型输入不变，未用观测区保持零，fflags 均为 `[1,1,1]`。两正常过程的完整 snapshots SHA 为 `be5e938c1405d866bb1c2f776805b4dca95a53fa6a02808f7a93f1b4ece8bb85`，live state SHA 为 `1c2b3ff1c04fda9deb3a2a02aee820c4bbfe46a8f187186c6f7945ff8d8d0674`，与既有正确消费者结果相同。

guest 内还实际执行了未初始化、空 state、token/position 越界及旧 method5 的拒绝检查。原验证器输出中的 `method` 字段仍用其历史字段名，值 `1345402417` 在此是独立入口标签 `0x50313631`；它从未传给旧方法分派。

- [results.json](evidence/reference-v1/results.json)：`PAIRED16_CONSUMER_REFERENCE_CAMPAIGN_PASS`，SHA `8337c10151aec9982fcda8af0b9f5ae16045dc470376ffa2aeb879dc4d43b9ce`。
- [state.json](evidence/reference-v1/state.json)：实际三个过程和终态，SHA `74ee021f9cdbf98c81bfe57d2b494918b0a65d10e54814f9fefd731ebf88dc5b`。
- [postrun-audit.json](evidence/reference-v1/postrun-audit.json)：270 个固定运行输入全部原 SHA，0 漂移；源和独立路由检查器也保持。

这些 JSON 含 64 位整数；审核须保留原始 JSON 数字精度，不能经 JavaScript Number 重新序列化。

## 退休指令诊断与性能边界

以下是参考执行的完整 forward 窗口 `instret_after - instret_before`；它们是不同 ELF 的架构退休量，不是香山周期。

| 位置 | 原 FR-cache | GS32 | Paired16 |
|---|---:|---:|---:|
| 0 | 7,502,872 | 4,828,781 | 5,175,361 |
| 1 | 7,532,699 | 4,858,608 | 5,205,188 |
| 2 | 7,561,908 | 4,887,817 | 5,234,397 |

P 每步相对 FR-cache 少 2,327,511 条；相对 G 多 346,580 条，恰等于 172 个完整 Q288 panel × 2,015 条内核窗口差。未采新的逐 PC trace，这只是一致性诊断。P 在原局部目标运行中的 raw 周期信号与这一退休量排序不同，因此不能按退休量决定实际较快实现。详细来源和计算见 [reference-instructions.json](evidence/reference-v1/reference-instructions.json)。

P 与 G 正确性 harness 都有两次完整状态零扫描，历史 FR harness 的准备不同；整进程退休总数不作公平应用比较。本次没有应用周期数据，也不能把三步 reference PASS 升级为全部 256 步、任意模型、双状态并发或目标整核资格。

## 复现与回退

完整原始产物保留于：

```text
/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/paired16-consumer-20261106-pro3/
  controller-01/          固定模板派生后的三控制器与 binding.json
  build-01/               GNU 命令、实际源码、ELF/BIN、模型、身份与反汇编
  review-controller-01/   实际运行的固定 ELF 路由检查器
  routing-review-01.json
  reference-01/           negative、recovery、replay 的镜像/raw dump/日志/回执
  postrun-audit.json
```

原 norm/W2 父、GS32 支持闭包、scalar 恢复视图和 P host 输入均保留在各自原路径。所有重建及重放使用新输出，不回写旧目录。`bind.py --template <固定GS32控制器目录> --host <原P host-01> --output <新controller目录>` 可重建控制器；实际构建 argv 见运行根的 `build-command.json`，使用显式 `--support-snapshot` 和原 `--scalar-view`。`review_routes.py` 只接受当前已人工审查的 ELF；新 ELF 身份须重新核机器字，不能照搬旧地址/资格。

原调用入口和默认选择保持，调用方恢复旧入口即可回退。下一步若需测完整应用，由主端另定公平目标合同与资源窗口，保留实际较快且合格的 RVV 对照；本叶不自行开启长 EMU 或放宽旧 P 选择条件。
