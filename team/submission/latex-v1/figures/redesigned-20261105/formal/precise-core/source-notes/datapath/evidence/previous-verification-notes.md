# S2-02 / S2-03 矢量初稿核对说明

## 交付与集成

- `S2-02.svg`：160 mm × 149 mm，点积算术与 P/R 两槽。
- `S2-03.svg`：160 mm × 145 mm，VFEX4 派发、互斥、独立门控和共享输出。
- 所有文字均为可编辑 SVG `<text>`；寄存器、运算树、门控、连接线均为确定性矢量，无嵌入栅格图。
- 中文字体栈按顺序指定 `Microsoft YaHei, 微软雅黑, SimSun, 宋体, "Noto Sans CJK SC", sans-serif`。微软雅黑、宋体优先；Noto 作为云端预览的后备字体，Windows 最终导出使用实际安装的微软雅黑或宋体。本环节未转换文字轮廓。
- 在 160 mm 宽下，辅助文字最小 40 用户单位 = 11.3386 pt；主体 44 单位 = 12.4724 pt；图题 52 单位 = 14.7402 pt。独立运算符可以更大。请维持 160 mm 的目标宽度；再次缩小会同比缩小字体。
- 白底，主色 navy `#16324F`、blue `#146B9C`、teal `#008A8C`。蓝色实线表示数据/valid 路径，深色虚线表示 ready，青色表示时钟或随数据迁移的控制身份。
- `build_vectors.py` 为可重复生成的本地构图脚本；`manifest.json` 记录实际输出 SHA-256、尺寸、最小字号和可编辑文字节点数。
- 本轮仅在指定 scratch 子目录创建图稿和说明，未修改仓库、Git index 或 Windows 文件；未运行工程构建、仿真、EDA。仅执行 SVG 生成与 XML / 字号 / 非栅格检查。PNG/PDF 转出、实际字体渲染与最终页面目视由主端集成完成。

## 固定版本及已读来源

硬件版本为 `cc77-builder/riscv@0f12df675378556670afd0dd2153f47fcb330610`，采用该版本 O2/H1 路径。没有使用后续 CSA、perf 裁剪或 ASAP7 结果。

| 来源 | Git blob | 本图采用的事实 |
|---|---|---|
| `src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala` | `e0703191ed2b626179e36fb40eb9741cdb843151` | 两源各取低 64 位；8 路 signed INT8 乘法得到 16 位乘积；4×17→2×18→1×19 的扩宽加法树；19 位和符号扩展到 32 位，输出高 96 位清零。 |
| `src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala` | `72d23e224bbfea13245865cc5a506ac87aed877b` | L20–24 说明 E0 接收、E1 迁移、E2 最早响应；L38–51 为 P/R valid、8×16 乘积、32 位 R 数据及控制/perf 寄存器；L59–75 为 live/ready/move 和完整输出；L85–107 为合法性处理、输入捕获和旧 P 向 R 迁移。 |
| `src/main/scala/xiangshan/backend/exu/ExeUnit.scala` | `8486333c3a4e51f5c2e6feb56c66c15b847ed2c5` | L89–91 为 P/R 占用；L126–158 为 DIV hold、VDot enable 与独立 ClockGate；L164–186 为 DIV 实际占用和取消；L307–314 为许可、selected-ready 和 child-valid；L316–333 为互斥断言；L696–699 及后续输出字段为 valid OR、ready 广播与 Mux1H 选择。 |

另只读对照了已提供的 build-06 实际正文 `originals/stage2.tex`，其 Windows 原 SHA-256 为 `223aa4d0181c98a3fbcbaa1cc0c4e77784f63755241eab9b3aaeb4000bc98e48`；正文 P/R 小节约 L168–193，VFEX4 小节约 L266–292。对照原图：S2-02 PNG SHA-256 `f596bf755e99f62d8eead9724fc065b0680989cf7ba82705fbfbf0a64e222504`；S2-03 PNG SHA-256 `a9eaee69af099f1073452779540157ab34aea080fc9476fb719084d7978e4670`。

## S2-02 逐项核对与图注建议

1. 图中的 `a0…a7`、`b0…b7` 分别是两源的 `bits[8i+7:8i]`，以 signed INT8 解释。两源高 64 位均不参与乘法。
2. 八个 16 位乘积进入 P 槽，随后经过 4 个 17 位、2 个 18 位、1 个 19 位加法节点；图形中的层级计数与位宽都直接来自源码。
3. 19 位和先符号扩展为 32 位，再进入 R 数据寄存器。输出按 `Cat(0.U(96.W), R.data)` 组成 128 位，图中没有将整个 128 位输出符号扩展。
4. P/R 横带代表内部两个槽。控制及 perf 身份沿旁侧路径在同一次 P→R 迁移中同步更新，不是另一个独立执行单元或额外流水级。图中省略 valid 状态机细节。
5. 最早 2 拍响应、II=1 仅描述无阻塞、允许接收且无取消时的行为，来自该路径的 E0/E1/E2 关系；不表示框架固定延迟声明。
6. 本图聚焦合法算术路径，非法输入处理移入图注：非法输入的 R 数据置 0，目的写使能关闭，同时保留异常信息。不要将图解读为非法输入仍向目的寄存器提交正常算术和。

**可直接采用的图注：**

> 图 S2-02　0f 版本的 VDot 点积算术与 P/R 两槽。每个源只取低 64 位，按 8 个有符号字节相乘；乘积在 P 槽寄存后，经扩宽平衡树求和，符号扩展到 32 位并进入 R 槽，输出高 96 位固定为 0。控制、异常与 perf 身份随数据同步迁移。图示为合法算术路径；非法输入将结果置 0 并关闭目的写使能。无阻塞、允许接收且无取消时，E0 接收的事务最早在 E2 响应，启动间隔为 1 拍。

## S2-03 逐项核对与图注建议

1. 左侧是 `fuType` 选路与占用许可，不是仲裁器，也未增加请求队列或优先级。
2. `allow = !divOccupied && (newIsVDot || !vdotOccupied) && !flush.valid && !reset`。VDot 占用期间仍可接收 VDot，DIV 与 VDot 不能交叉占用。
3. `selectedReady = Mux1H(selected, child.in.ready)`；`parent.in.ready = allow && selectedReady`。不能将其改为所有子单元 ready 的 AND，也不能写成只看 VDot 的 ready。
4. `child(i).in.valid = parent.in.valid && allow && selected(i)`。valid 不以 ready 为前提；图中的蓝色请求路径同时代表相应输入数据与有效信号，完整握手表达式留在本说明及图注。
5. VDot、VIDiv、VFDivSqrt 分别有 CG。VDot 的门控使能为 `pValid || rValid || in.fire || reset`；DIV 依赖 hold 等实际控制条件。图内的 `en` 仅是独立使能端口标签，不将三个使能画成同一信号。
6. DIV 的有效占用包含 `divBusy || divOutValid || !divReady`，完成或取消后仍需等物理输出释放及实际 ready 恢复；图不画“取消立即切换”的捷径。
7. 共享输出是 `out.valid = OR(valid_i)`，有效输出至多一路；输出数据及控制/perf 按 `Mux1H` 选择。`out.ready` 直接广播到三个 FU，不经选择门控。
8. VFDivSqrt 只表示父级静态结构，图内明确标注“静态结构”。本图不声称该单元已覆盖动态执行实验。
9. 蓝色数据线路在与 ready 或时钟线交叉处使用白色间隙，且没有连接点，表示跨越；只有时钟分支和 ready 广播上的圆点表示真实分支连接。

**可直接采用的图注：**

> 图 S2-03　0f 版本的 VFEX4 父级结构。输入由 fuType 选择功能单元，并受 DIV/VDot 占用许可约束；ready 取被选中单元的 ready 与许可相与，子单元 valid 由请求 valid、许可和选择信号共同产生。三个功能单元分别使用独立门控时钟。共享输出在至多一路有效的前提下通过 Mux1H 选择数据、控制与身份，out.ready 广播至所有单元。VDot 占用期间可以继续接收 VDot；DIV 完成或取消后，切换还需等待其实际输出与 ready 状态释放。VFDivSqrt 在此仅展示静态接线。

## 已完成的文件级检查与尚待主端检查

生成脚本检查 XML 可解析、最小字号不低于 40 用户单位、没有嵌入图片或 foreignObject，并输出文件哈希。以上是构图完整性检查，不是 RTL 或动态功能验证。主端仍需在实际 Windows 字体环境下检查两图的宋体/微软雅黑解析、连线遮挡和 160 mm 页面放置；这些不改变本图引用的硬件证据。
