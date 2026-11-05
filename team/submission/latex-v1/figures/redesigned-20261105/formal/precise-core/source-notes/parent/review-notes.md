# S2-03 暖白版核对说明

## 文件与版式

`S2-03.svg` 为 160 × 145 mm 可编辑纯矢量，`build_vector.py` 可在本目录重建；`sources.json` 是纯数据来源清单，记录固定提交、源码 blob、逐项行号、图中短标签映射、尺寸、字号与输出 SHA-256。

图中没有完整总标题或版本大字。背景为近白 `#F6F3EE`，石墨 `#242424`，轻填色 `#E8E3DC`，时钟及独立门控采用橙红 `#CE4B32`。160 mm 宽时全部辅助字不低于 11.3386 pt，主体 12.4724 pt。SVG 的字体栈依次使用微软雅黑、宋体、Noto Sans CJK SC 及通用 sans-serif；本次交付 PDF 实际嵌入 Noto Sans CJK SC 的常规和粗体字体。若在 Windows 重新导出并发生字体替换，需要重新目视检查。

145 mm 高用于容纳必要的准入条件、selected-ready 选择、三列 FU、独立时钟门控及共享输出，没有通过缩小字体挤压公式。最终报告分页由主 Pro 在整稿中确认。

## 精确来源与本地缓存

源码为 `cc77-builder/riscv@0f12df675378556670afd0dd2153f47fcb330610` 的 `src/main/scala/xiangshan/backend/exu/ExeUnit.scala`，目标 Git blob 为 `8486333c3a4e51f5c2e6feb56c66c15b847ed2c5`。

配置前提是 `VDotO2.enabled=true` 且 `EnableClockGate=true`。O2 分支限制在包含这三个功能单元的 VFEX4；关闭 O2 或门控时不能直接把本图作为对应配置的结构说明（L67–78、L95）。这不是当前分支默认配置或新仿真结果的声明。

已实际读取 `evidence/0f-ExeUnit.scala`。本地缓存比原 Git blob 多一个末尾 LF；只在内存中去掉这一字节后精确匹配目标 blob。没有改写缓存。原始缓存 SHA-256 为 `2067403aa9f5806123efe4c448a1bb59721bff5bc9d7bf30659aa41880ac3ff4`，原始缓存 Git blob 为 `9264328af9fc3cade1f54f04e19d19f7f80e7755`。

## 图中网络与技术核对

- 三列按视觉顺序放置 VDot、VIDiv、VFDivSqrt。V/I/F 是图中网络标签，不声称这些列对应 `funcUnits` 的 0/1/2 下标。
- `fuSel` 是源码 `selected` 的图示短名，来自 `VecInit(acceptCond(io.in.bits))`（L305）。`selectedReady` 明确通过 Mux1H 从对应子 FU 的 `in.ready` 中选取（L310），父级 ready 再与 `allowInput` 相与（L311）。没有将所有子 FU ready 直接 AND 后作为输入 ready。
- 需要区分：`divReady` 确实是两个 DIV 子单元 ready 的 AND（L173），它用于 `divOccupied`；这个内部定义没有替代 `selectedReady`。
- 输入 bits 采用上方真实广播干线（L313）。局部 `vV/vI/vF` 分别表示对应子 FU 的输入 valid，按 `in.valid && allowInput && selected(i)` 产生（L314）；valid 不以 ready 为前提。
- 顶部 `rV/rI/rF` 与各列顶端的同名虚线端口是同一网络，分别来自对应子 FU 的 `in.ready`。用命名网络避免将三个 ready 画成合流或一条共享数据信号。
- `VDot忙 = pValid || rValid`（L89–91）；`DIV忙 = divBusy || divOutValid || !divReady`（L166–186）。图内条件允许 VDot 占用时继续接收 VDot，阻止 DIV 与 VDot 交叉占用。DIV 完成或取消后必须等实际输出释放、ready 恢复，不能视为立即切换。
- 每列 CG 是独立实例，`enV/enI/enF` 也分别是独立使能。三个 `clk` 标签表示同一父级时钟；橙色线路只在每列局部门控区域内行进，没有穿入功能数据分支。VDot 使能为 `pValid || rValid || in.fire || reset`（L146–150）；DIV hold 的匹配取消与清除逻辑见 L126–143。
- 下方 Mux1H 表示共享输出数据、控制与身份按对应有效路选择（L699–714、L737）；`out.valid = OR(valid_i)`（L696），有效路最多一路（L332–333）。它不是新增仲裁器。
- 底部虚线是 `out.ready` 的真实广播（L697）。竖向回传线路在下方数据收集线交叉处留有背景色间隙；无圆点处不连接，圆点才表示真实广播分支。
- VFDivSqrt 仅展示静态结构，未声称动态测试覆盖。

## 可用图注

> O2 弹性路径与时钟门控启用时，VFEX4 的互斥派发、独立时钟门控与共享输出。输入数据广播到三个功能单元，valid 由输入有效、占用许可和对应选择位共同限定；父级 ready 取被选中单元的 ready 并与许可相与。VDot 的 P/R 占用允许继续接收 VDot，DIV 与 VDot 之间则需完成占用交接。各单元分别门控时钟，输出在至多一路有效的前提下经 Mux1H 选择，out.ready 广播至各单元。图中的 V/I/F 为网络短标签；VFDivSqrt 仅表示静态接线。

## 自检范围

已执行本图生成、固定源码身份核对、SVG XML 解析、最小字号与非栅格检查，没有工程构建、功能测试或仿真。全部写入仅限本目录。根端已实际执行 Inkscape→PDF→PNG，核实 PDF 为 160×145 mm，最小字号 11.3386 pt，字体已嵌入，全部文字包围盒位于页面内。首稿 fuSel 标签压到梯形斜边的问题仅通过移动该标签修正；原稿及失败目视证据保留在 `pre-label-fix/`。

## 本批 B 版统一

从已接受并修正 fuSel 标签位置的暖白 v2 独立复制，仅统一背景为 `#F6F3EE`。生成器保留 `VDotO2.enabled=true`、`EnableClockGate=true` 的适用前提；布局、40 用户单位最小字号、数据关系、标签位置与源码身份均沿用已接受版本。
