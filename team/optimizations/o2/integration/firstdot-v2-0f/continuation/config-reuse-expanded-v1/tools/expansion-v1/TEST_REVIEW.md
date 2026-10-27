# 扩展矩阵独立主机测试与合同审查

## 范围与边界

本轮仅为 4 个形状 × 3 个数据集的测试扩展提供独立主机测试，不改生产 RTL、冻结工具或既有结果，不上传 GitHub。测试文件为本目录 `test_matrix.py`。所有合成字典和临时小文件都是拒绝逻辑测试夹具，不能作为目标 EMU、NEMU 差分或性能通过证据。

固定范围：shard 1/3/5/7 分别为 4×8、8×32、16×64、4×13；dataset 0/1/2；firstdot 与 config-reuse 两变体，共 24 个正式镜像。调度应含 1 个 bit100 故障负控、24 个正式正常进程（其中一个为紧随负控的同 BIN 恢复）、8 个 dataset0 独立重放，总计 33 个新目标进程。旧探针的进程不能充当本轮样本。

## 独立审查意见

1. 上游汇总从实际传入的 records 推导预期列表，缺镜像可能自洽通过；控制器必须先按固定矩阵与调度做完整性检查。
2. 每形状、每格的 12 个正式样本是 3 个数据集各 4 样本的总和。需要总量与逐数据集同时判定，避免某个数据集退化被平均改善掩盖。不同形状分别保留结论。
3. 主格 config-reuse/reuse/vdot 必须严格优于 firstdot/reuse/vdot 及当前四个 RVV 格中的最快者；没有事后增加的百分比阈值。控制样本漂移、独立重放不等或其他格退化时返回 INCONCLUSIVE，不把异常遮成收益。
4. 共同输入中 12 个对照 BIN 的路径集合必须精确相等并验证字节摘要；只从单进程输入角色中移除这些已知对照 BIN，完整外层输入映射仍受验证。不能按 `.bin` 后缀宽泛忽略输入。
5. 并发证据应使用同一 boot_id 的单调时钟、不同正整数 PID 及明确的 spawn/wait 保守包络；不能用 UTC 时间估计值宣称精确 OS 并发。并发预算与进程数分别验证。
6. 负控和恢复须绑定同一个镜像及配置；负控必须真正命中向量目标 bit100，恢复必须用正常 NEMU 参考模型、干净故障环境及先负控后恢复的时间关系。

## 实际执行记录

### 轮次 H01：已完成接口的局部主机测试

命令：

```bash
cd /home/riscv/riscv-lab/software-import-20261026/reviews/config-reuse/expansion-v1
python3 -B -m unittest -v test_matrix.InventoryTests test_matrix.DecisionTests test_matrix.ImageScopeTests
```

实际结果：28 项通过，unittest 耗时 0.033 s，测试进程退出码 0。本轮没有失败项。控制器正在继续实现其他接口，因此这不是最终全套结果。

已覆盖：

- 固定 24 镜像和 33 进程；缺失、重复、额外项、错误形状/数据集/类型拒绝。
- 每格 12 个正式样本与显式 4 样本逐数据集评估；缺格、重格、样本或总量错误拒绝。
- 主格与两类基准的严格比较、最快 RVV 选择、控制漂移和其他格退化。
- 总体改善但单数据集主格打平或其他格退化；聚合总量不等于数据集总和拒绝。
- 精确 12 个比较 BIN 的摘要与角色检查；额外或缺失 BIN、错误摘要、缺文件、符号链接拒绝。

## H01 时点尚未验证

- timing/recovery 全套主机测试：等待控制器接口完成。
- 24 镜像的目标工具链构建、33 个目标进程、全宽结果、真实 NEMU 差分和协议观察器：NOT_TESTED（由主任务实际运行后留档）。
- 运行审计器及目标原始日志复核：NOT_TESTED。
- 普通公开 C 调用方式扩展：NOT_TESTED，本轮范围外。
- 性能候选采用、默认配置变更、生产 RTL 修改及 GitHub 上传：未进行。

H01 记录时间：2026-10-27T10:41:03.034810+00:00
matrix.py SHA-256: a2018b713d747eabc11e1b6acdbc369de8a3c391f4e41ebb60ac24c798b288b3
test_matrix.py SHA-256: ca17561b8cd418659f4ce60216ef9cafdabe94a8de9795839ee62a891e5e4e3a

## 后续主机测试记录

### H02：timing / recovery 接口完成后的全套

实际执行 `python3 -B -m unittest -v test_matrix`：45 项通过，0.033 s，测试进程退出码 0。新增单调时间包络、并发越限、PID/boot 身份及负控恢复绑定测试全部通过。

### H03：完整调度到审计的组合测试发现 JSON 键类型缺陷

加入严格 records 库存及主机组合夹具后，实际执行同一命令：51 项中 50 项通过、1 项 ERROR，0.985 s，测试进程退出码 1。

失败用例：`ControllerAuditIntegrationTests.test_real_schedule_receipt_hooks_summary_schema_and_audit_join`。失败位置：`raw_audit.py` 的决策复核；异常为 `ValueError: cached shape decisions/replay differ`。

原因：`decide_shape()` 返回的 `dataset_decisions` 使用整数键 0/1/2；写入 JSON 后变为字符串键，审计器重新调用 evaluate 得到整数键，导致合法结果也无法通过相等性校验。已通知控制器维护者在输出边界使用字符串键；不能放宽审计器相等检查来掩盖问题。

H03 对应控制器 SHA-256：`603a902e3159adc7978cb2f9d11187f5a6051e62a21bd738975bd955079612aa`。

组合夹具真实调用 `Matrix.run()`、调度器、进度回调、33 份记录写盘、计数与相位屏障、单调时间包络、`Matrix.evaluate()`、冻结 summarizer 函数体及 `audit_matrix()`。仅目标 spawn 与 GNU/原始 trace 重解析是明确的替身，Popen 被禁止调用。全部产物在临时目录销毁；测试字典中的进程计数不能计入真实 EMU 运行，更不能认定硬件或性能通过。

### H04：修复后组合路径通过，诊断文本匹配测试需调整

2026-10-27T10:46:22.974682+00:00 实际执行 55 项，54 项通过、1 项 FAIL，2.273 s，退出码 1。完整 run→audit 正向组合已通过。唯一失败是测试使用 `cached statistics` 正则，而审计器准确诊断为 `cached nested statistics differ from raw samples`，故测试断言未匹配；产品拒绝行为正确。仅将测试正则改为 `cached.*statistics`，未修改控制器、审计器或放宽错误拒绝。

H04 测试文件 SHA-256：`f29e161d005bc363c63e94e6a50e960c1754c7c9bb4503657423fa8922ce0cd0`。

### H05：最终独立主机测试

2026-10-27T10:46:38.281655+00:00，实际执行 `python3 -B -m unittest -v test_matrix`：**55 项全部通过，2.393 s，退出码 0**。运行前后对以下四个文件计算 SHA-256，身份一致。

| 文件 | SHA-256 |
| --- | --- |
| matrix.py | `0eecb8aaee9093b43030658eb75c30dbceb05a8156729922ce321fe0635839c9` |
| raw_audit.py | `9aeca96415e1d6153ae398fa653c949196426bf57caaea5692ee34c204de13cf` |
| test_matrix.py | `93ce6e4f5c70391bc5ad19b9284c4fda33f29e976ef2f792fc768ab3cd7f270a` |
| CONTRACT.md | `626c2843f277af52bdf18fc459aacfa8c3e194041cf37da976e2d91a53add9a8` |

相比 H01，最终补齐：

- 32 份正常/重放记录的固定库存、顺序、身份、状态、类型与 24 窗口数量。
- 单调时间、boot/PID 绑定、1～4 工人并发预算、相位边界及同 BIN 负控恢复。
- 真正调用完整 `Matrix.run()` 到 `audit_matrix()` 的主机组合路径，覆盖进度回调落盘、完成计数、缓存汇总、JSON 键类型和只读审计。
- 独立验证每个形状保留自己的结论；一个形状的 firstdot 完整样本漂移不会污染其他形状判定。
- 未纳入正式平均值的 RVV 首次窗口指令数漂移也会令该形状 INCONCLUSIVE。
- 重放比较完整样本字典；即使 cycles/instructions 未变化，repeat 元数据漂移仍会被识别。
- 缓存 nested summary 被修改后，审计器在统计一致性检查处明确拒绝。
- 决策公开结构通过 JSON 往返，防止 H03 的整数键问题重现。

## 当前交接结论

主机逻辑与组合接口测试完成，55 项全部通过；H03 的真实 schema 缺陷已由控制器修复，H04 的测试诊断正则误匹配也已修正，两次失败保留。只修改本目录的 `test_matrix.py` 与本说明，未改生产 RTL、MAIN、冻结工具或旧证据。

本测试任务未运行任何真实 EMU / NEMU / GNU 构建，不给出扩展矩阵硬件通过或加速结论。真实 24 镜像构建、33 个目标进程及原始日志审计由主任务另行执行和留档；普通公开 C 调用扩展仍为 NOT_TESTED。
