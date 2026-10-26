# TA 候选：固定 T17 源码硬件前提审查

审查人：`/root/coordination_audit`。时间：2026-10-26 05:45:11 UTC。固定来源提交：`34bae6d4acceac939f958199dae53c14bc1f6183`。

## 结论与身份边界

对本候选的无掩码普通 `vle8.v`，在 `e8,m1,vl=8,vstart=0,vma=0` 下把 `vta=0` 改为 `vta=1`，固定源码会在知道对应重命名 VL 非零后取消 old-vd 就绪等待，并把该源改成不读 RF 的数据源。这不只是改变尾部合并结果。

本结论是源码结构性前提，不是 TA 目标运行或周期收益资格。没有运行构建或 EMU，没有修改生产仓库、官方程序或规则。

归档 T17 `hardware-inputs.json` 解压字节 SHA256：
`7c42a8130e71b39e8f5ca08d7d662a85ac58f677040c6293d38007b007ac0dcc`。

T17 EMU SHA256：
`ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`。

主线程已经将下面 **11 个关键文件**与真实归档 pins/物理源逐字节匹配：DecodeUnitComp、NewDispatch、EntryBundles、IssueQueue、DataPath、Parameters、Configs、Backend、ExeUnitParams、IssueBlockParams、DecodeUnit。本审查从固定提交取回相同源码，复算 SHA256；同时以 Git blob 格式复算 SHA1，每项均匹配 GitHub blob ID。追加配置 6 文件的实际归档匹配由主线程确认。

其余 7 个支撑文件（VecDecoder、DataSource、Vsetu、VSet、VldMergeUnit、Mgu、ByteMaskTailGen）只标记为**来自同一固定提交的代码证据**；本审查没有声称其物理文件已另行匹配 T17 pins。完整机器可读范围、SHA 与片段见 `hardware-source-review.json`。

## 1. Load 和 custom vdot 的 old-vd 来源不同

[src/main/scala/xiangshan/backend/decode/DecodeUnitComp.scala:1754–1778](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/DecodeUnitComp.scala#L1754-L1778) 的普通 `VEC_US_LDST` load uop 明确设置：

```scala
csBundle(i + 1).lsrc(2) := dest + i.U // old vd
csBundle(i + 1).ldest := dest + i.U
```

[src/main/scala/xiangshan/backend/decode/VecDecoder.scala:167–175](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/VecDecoder.scala#L167-L175) 的普通 VLD decode 将第三源设为 `SrcType.vp`。[src/main/scala/xiangshan/backend/decode/DecodeUnit.scala:1046–1059](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/DecodeUnit.scala#L1046-L1059) 另行计算 `isDependOldVd` / `isWritePartVd`；普通非 indexed、非 fault-only-first、`vstart=0` 的 e8/m1 load 不受这些固有保留条件阻止。

Custom vdot 在 [src/main/scala/xiangshan/backend/decode/DecodeUnit.scala:1073–1078](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/DecodeUnit.scala#L1073-L1078) 和 [src/main/scala/xiangshan/backend/decode/DecodeUnitComp.scala:356–371](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/decode/DecodeUnitComp.scala#L356-L371) 已直接设置 `srcType(2/3)=no`、`isDependOldVd=false`、`isWritePartVd=false`，VL 仍是重命名源。TA 候选优化的假设针对普通 load 的尾部保留依赖，不能表述为再消除一次 custom old-vd。

## 2. Dispatch 的确定性条件

[src/main/scala/xiangshan/backend/dispatch/NewDispatch.scala:324–330](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/dispatch/NewDispatch.scala#L324-L330)：

```scala
val ignoreTail = vlIsVlmax && (vm =/= 0.U || vma) && !isWritePartVd
val ignoreWhole = (vm =/= 0.U || vma) && vta
val ignoreOldVd = vlBusyTable.io.read(i).resp &&
  vlIsNonZero && !isDependOldVd && (ignoreTail || ignoreWhole)
```

命中后同文件第 330 行使 old-vd 源 ready；[src/main/scala/xiangshan/backend/dispatch/NewDispatch.scala:449–450](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/dispatch/NewDispatch.scala#L449-L450) 将其 `srcType` 改成 `SrcType.no`。[src/main/scala/xiangshan/backend/issue/IssueQueue.scala:314–319](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/issue/IssueQueue.scala#L314-L319) 再将该源的数据选择初始化为 `DataSource.imm`。

固定源码 `VLEN=128`。Vsetu/VSet 的旗标计算使 e8/m1、AVL=8 得到 VL=8、VLMAX=16。因此本例 `ignoreTail=false`，TU 的 `ignoreWhole=false`，TA 的 `ignoreWhole=true`。消除还需要对应 VL 已知且非零。

此机制不删除 rename 的旧映射查询，不删除新目的物理寄存器分配。

## 3. 实际 MinimalConfig 的晚 VL 路径

[src/main/scala/xiangshan/backend/issue/EntryBundles.scala:307–326](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/issue/EntryBundles.scala#L307-L326) 在匹配的 VL 写回 wakeup 到来后再次计算同一消除条件，并更新：

```scala
srcStatusNext.srcType := Mux(ignoreOldVd, SrcType.no, srcStatus.srcType)
srcStatusNext.srcState :=
  srcStatus.srcState & !srcLoadCancel | wakeupByWB | wakeupByIQ | ignoreOldVd
```

必须绑定配置才能判断数据源选择：

- [src/main/scala/xiangshan/Parameters.scala:486–491](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/Parameters.scala#L486-L491) 的向量 load 单元是 `VLSU0/1`。
- [src/main/scala/xiangshan/Parameters.scala:508–519](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/Parameters.scala#L508-L519) 的 `iqWakeUpParams` 没有这两个 sink。
- [src/main/scala/xiangshan/backend/Backend.scala:99–102](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/Backend.scala#L99-L102) 应用配置；[src/main/scala/xiangshan/backend/exu/ExeUnitParams.scala:323–325](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/exu/ExeUnitParams.scala#L323-L325) 按 EXU 名筛选。
- [src/main/scala/xiangshan/backend/issue/IssueBlockParams.scala:240–244](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/issue/IssueBlockParams.scala#L240-L244)、[src/main/scala/xiangshan/backend/issue/IssueBlockParams.scala:258–269](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/issue/IssueBlockParams.scala#L258-L269) 因而给两向量 load IQ 得到 `hasIQWakeUp=false`。
- [src/main/scala/top/Configs.scala:67–242](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/top/Configs.scala#L67-L242) 的 MinimalConfig 不覆写该配置。

因此实际选用 [src/main/scala/xiangshan/backend/issue/EntryBundles.scala:346–351](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/issue/EntryBundles.scala#L346-L351)：

```scala
MuxCase(srcStatus.dataSources.value, Seq(
  ignoreOldVd                      -> DataSource.imm,
  wakeupByIQ                       -> DataSource.bypass,
  srcStatus.dataSources.readBypass -> DataSource.reg,
))
```

**早先对第 337–344 行 memory-with-IQ-wakeup 分支的保守提示不适用于此配置。** 该分支不是本 MinimalConfig 的 elaboration 路径，不能把它写成 T17 缺陷或剩余阻碍。

## 4. RF 请求终点与尾部合并

[src/main/scala/xiangshan/backend/datapath/DataPath.scala:136–148](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/datapath/DataPath.scala#L136-L148) 对向量 RF 仲裁输入设置：

```scala
arbInSeq(srcIdx).valid :=
  inRFReadReqSeq(srcIdx).valid &&
  allDataSources(iqIdx)(exuIdx)(srcIdx).readReg
```

固定提交的 [src/main/scala/xiangshan/backend/datapath/DataSource.scala:5–10](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/datapath/DataSource.scala#L5-L10) 定义 `readReg=value(3)`；第 46 行 `imm=0b0100`。因此 old-vd 改为 imm 后不发该源 RF 读请求。早、晚两条依赖消除路径都达到此状态。

以下是固定提交支撑证据，尚未独立绑定归档物理文件：[src/main/scala/xiangshan/backend/datapath/VldMergeUnit.scala:25–39](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/datapath/VldMergeUnit.scala#L25-L39) 将 vta 送入 Mgu，[src/main/scala/xiangshan/backend/fu/vector/ByteMaskTailGen.scala:74–79](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/fu/vector/ByteMaskTailGen.scala#L74-L79) 产生尾部 agnostic mask，[src/main/scala/xiangshan/backend/fu/vector/Mgu.scala:89–93](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/fu/vector/Mgu.scala#L89-L93) 对 agnostic 字节写全 1。本例正常完成的 load 低 8 字节来自内存，高 8 字节为 `0xff`。split/merge 路径仍存在。

## 5. 限制与可证伪边界

- VL 未知或为零、vstart 非零、indexed/fault-only-first 等 `isDependOldVd` 情况，不满足本消除前提。
- 对 `vm=0,vma=0` 的掩码未扰动情形不能套用本例；本候选须保持无掩码。
- 任何后续有效消费 agnostic 高字节的操作都会破坏软件前提；实际固定代码的全 1 尾部不能替代任意合法尾部的非干扰证明。
- 原 old-vd 已 ready、地址/VL/活动字节加载更慢、issue/内存资源约束等，都可能使最终收益为零。
- 本审查不证明指令/uop 数、访存字节数、load 固定时延、merge 阶段数或物理寄存器分配减少。
- 已有 custom ENQUEUE/ACCEPT/RESPONSE 日志不能直接统计普通 load 的 `ignoreOldVd` 事件；退休间隙不得视作因果周期份额。
- 不将此静态硬件前提升级成运行正确性、性能或完整应用资格。

## 源码身份

“实际 pins”仅对主线程明确确认的 11 项为“已匹配”。全部 SHA256 与 Git blob SHA1 均由本审查从固定提交内容复算，后者匹配工具返回的 blob ID。

| 文件 | 实际 pins | SHA256 | Git blob SHA1 |
|---|---|---|---|
| `src/main/scala/xiangshan/backend/decode/DecodeUnitComp.scala` | 已匹配 | `fd94a3008053b6bdf54da23adb5a7bced34bd6a74be42a5322c3b13f7be4b618` | `9e0d142476fe09958ba949aacc1076ed3f6bdd51` |
| `src/main/scala/xiangshan/backend/dispatch/NewDispatch.scala` | 已匹配 | `aaae74122031c4c091f566b9e73a83c5e6e249a58d7f305a3551d0d0ae73ac36` | `c3842b62e31f7a34a36179b7514070ed90e2a9d1` |
| `src/main/scala/xiangshan/backend/issue/EntryBundles.scala` | 已匹配 | `6e825d2d085f144cff72d498c1482a48314134915ffa4ba242b8b5516c3f27a8` | `af64892bf18f9dc6c5992b7922a4b8a697a488e7` |
| `src/main/scala/xiangshan/backend/issue/IssueQueue.scala` | 已匹配 | `d20799fa417b89ede9e5573a313e91217064fe30da139a45637c01f995260ae7` | `6e33e89ac8b2f32c7b1031924348bfb08129702a` |
| `src/main/scala/xiangshan/backend/datapath/DataPath.scala` | 已匹配 | `838eefec28b52827de0f0f0be6dbf33726e9e69518711138054cdf670aacac8f` | `b7cb67ee20cdff03ec1313337ae5c9c5af83aee4` |
| `src/main/scala/xiangshan/Parameters.scala` | 已匹配 | `4ce4019b34a71bbc62c467c4209993e36ad63c29212c56f4bdf5e60faf2db907` | `0abf4a0c5fb3a0f498cc4ba33c5f2bd143190886` |
| `src/main/scala/top/Configs.scala` | 已匹配 | `febd1212adf7b3c7069f378c0f54373e40ade36ee902e0d1cf63503c300d6fd2` | `125bbfe28b7d6f94c5008d69b675a18313f97e1b` |
| `src/main/scala/xiangshan/backend/Backend.scala` | 已匹配 | `346c2677150a5a64e8e865b9ec3929dcfbdcfb43697c04b468e1bccc2bd812d7` | `d301285fded394606ca04608384e0bd360cf2809` |
| `src/main/scala/xiangshan/backend/exu/ExeUnitParams.scala` | 已匹配 | `e0f58b000c93ef969634b783ed0e7ffdb11634dc1c90518eb15c9fd92d308c8c` | `dad2bf93bba26cd8fdc2a5463610a57ba0a5561e` |
| `src/main/scala/xiangshan/backend/issue/IssueBlockParams.scala` | 已匹配 | `c41af5d79c2dbb225f58361859d57d1637bde756d247d3af0323a073fffa1bcc` | `6ccd9546f3e4a43b835a68e0405678685eca9526` |
| `src/main/scala/xiangshan/backend/decode/DecodeUnit.scala` | 已匹配 | `4da8dc343ac8d0afc557270655b2cdad52ea645149ad87835aa9c5776a284134` | `a0bcda5a1b737b189f8fdafa232350ea822826a3` |
| `src/main/scala/xiangshan/backend/decode/VecDecoder.scala` | 固定提交证据，未另核对 | `2ae12df34733075ab01fb012cb3a889ca36bb1cdde5e53ce72c9460e784cb3df` | `8a2aac15aef278dae3d7d4f93521b2b2a0579690` |
| `src/main/scala/xiangshan/backend/datapath/DataSource.scala` | 固定提交证据，未另核对 | `bf8aee12abbb7c98b013190168832bb3e611875abcfb0043c9cb191b4c7b8745` | `b72a56ba6302d377cf52880ced8702c4af476665` |
| `src/main/scala/xiangshan/backend/fu/Vsetu.scala` | 固定提交证据，未另核对 | `65f9b7b8a022342e0c71664f622ddd91b503acb8695cdde53499e45f12c584aa` | `232aaad54919c37ba6c4333b89cefecaa1248622` |
| `src/main/scala/xiangshan/backend/fu/wrapper/VSet.scala` | 固定提交证据，未另核对 | `033ef52ff4061d365ac95fce95ab715b1a87586b1a78ac136b3d2df9d1c48d0f` | `7be2ed4cdf347939444493dd9ae2d182541f8fcc` |
| `src/main/scala/xiangshan/backend/datapath/VldMergeUnit.scala` | 固定提交证据，未另核对 | `3f53b9c9a9d173e38e62ee78202e25736622bc09445eac3bdfefb37b0b784a13` | `40fc0cee5787a5ac39f3a8737d52cc4d4bead81f` |
| `src/main/scala/xiangshan/backend/fu/vector/Mgu.scala` | 固定提交证据，未另核对 | `fce24fd96869d2c6df7b4bdcff2669db0de0d53647ef46f38b80e18d7c41bdcc` | `37e7b829eaa478ed3c38a431ce207c37230d324c` |
| `src/main/scala/xiangshan/backend/fu/vector/ByteMaskTailGen.scala` | 固定提交证据，未另核对 | `d70f22913c2c5e80ae4659ba4efae06cce4810a91acd4f021d2679f98e44bb05` | `31e5cbbec0817bb6621b161a53d96bb857881499` |
