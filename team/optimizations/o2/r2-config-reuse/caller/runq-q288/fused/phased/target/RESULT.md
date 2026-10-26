# Q288 phased：完整目标对照闭合

结论：`PHASED_PREFERRED_IN_FIXED_PLAN`，本合同选择 `q288_phased_vdot`。这是软件排程收益，T17/RTL与R5默认未改变。资格只覆盖固定合成、已量化、已打包288×288 Q；具名RVV对照和原fused入口保留。

| 方法 | 原始周期 | CSR instret |
|---|---|---|
| fused-vdot | 62742, 62716 | 52529, 52529 |
| phased-vdot | 60314, 60336 | 49613, 49613 |
| fused-rvv4 | 67292, 67311, 67300, 67293 | 35681, 35681, 35681, 35681 |

- phased-vs-current-fused-vdot：最慢候选 60336 对最快基线 62716，保守少 3.794884878% 周期。
- phased-vs-named-fused-rvv4：最慢候选 60336 对最快基线 67292，保守少 10.337038578% 周期。

八窗顺序 `FR,FV,PV,FR | FR,PV,FV,FR`，各窗前执行相同方法完整Q selfwarm；四个FR均纳入1%锚点和分母。0.5%最坏候选对最好基线门槛在实验前冻结；replay不是额外样本。源码与合同见 [CONTRACT.md](CONTRACT.md)，原始选择及身份见 [summary.json](evidence/target-v1/summary.json)。

## 正确性与原文复现

negative按预定拒绝高96位错误；recovery/replay均完整DiffTest、6336输出、22次Q调用、124417 custom/41472 timed custom和32 CSR/COUNTER事件通过。两份validation原字节一致，stderr各304,166,013字节且SHA `8006c9d0d1e59614b005916168d85b8d5e2ccba8a29ad2a0aca8982c2f15096c`相同。运行收据保留真实起止时间和PID，不用回放增加样本数。

冻结源码提交 `34092ebcf579a5de76e70cadfb6a5333173891ae` 的106项源保持不变。真实build-03 ELF SHA `bcbe7088f3548813d8ea24fd3a71ce5cb268e7074e7573bb74680d641e5a33b4`、BIN SHA `73bc3a0e8b6d172cb427b09c2f6ff5ca2e0b56c0e0c1617b426cdc20bf84342d`。实际GNU编译/权威object、全部数组与完整机器路径通过；8项数组/FP、3项PV双重语义和5项selector控制保留。

归档原文171成员、615,329,232字节，ZIP 42,860,576字节、SHA `4f585031c9b621da75e192f82557972b06cad3c46f401931318cc2e4ebc6efc5`。隔离新Python进程仅使用归档源闭包、必要历史Git对象与明确补充审计器完成复算，原依赖guard和完整原文结果相等检查通过。启动端仍需要这些已交付补充审计源码，不宣称仅凭单ZIP可运行。命令/guard/进程收据位于 [fresh-source](evidence/target-v1/fresh-source/result.json)。

## 已保留的失败和适配

build-01缺失旧q288_full链接根、build-03启动器误要求调试段也逐字节相等，以及首次归档tuple/list缓存比较失败均保留在support及原运行目录。没有重写旧结果或重跑EMU。build-02/03的实际BIN和全部LOAD段相同，仅3个调试section变化；build记录的构建时HEAD仍保留其原值。

首次归档的唯一差异是四个 `phased_certificate.mode_phases` 元素的tuple/list表示。新 [archive_json.py](archive_json.py) 依据 [限定合同](ARCHIVE-JSON-CONTRACT.md) 只转换这一字段，继续执行原完整相等判据，并通过3项类型/值拒错及其他字段不隐藏控制。原106源、缓存和失败回执均未改；新归档使用02身份，隔离子进程使用同一适配。

## 范围与使用

此处既不计pack/量化/权重初始化，也不包含token、训练模型质量或ASIC数据；同ELF仍包含固定代码/地址上下文。原fused/FR与R5默认可回退。完整接受坐标与消费者跨度见 [COST.md](COST.md)，退休跨度不等于独占执行成本。
