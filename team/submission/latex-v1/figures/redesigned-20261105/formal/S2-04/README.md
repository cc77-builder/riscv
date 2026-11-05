# S2-04 基础验证层级与覆盖范围

本图是独立单张工程层级图，原生 **160 × 126 mm**。源 SVG 正常字重，字号由画布比例确定为 **11.622–11.906 pt**；SVG 保留可编辑文字。排版 PDF 直接使用 Inkscape `--export-text-to-path` 导出，字体数和可提取文字均为零，避免已确认的 Noto CFF/ToUnicode 数字映射问题；准确文字请使用 SVG 和正文图注。

## 核心表达

四层框线表示 VDot 相关硬件的实现包含关系：整核含真实 VFEX4 父级、父级含 VDot FU、FU 含算术逻辑。各层的实际测试和原证据独立记账，**不表示测试输入集合逐层全包含，不表示所有层同时执行一次测试，更不合并为一次新的 PASS**。图面积没有定量覆盖率含义，未展开其他整核模块或完整 DIV/SQRT 结构。

独立整数模型位于设计之外，用于完整 128 位算术期望；NEMU 是另一个架构参考角色，位于整核差分对照侧。两个中性比较节点各接一份实际状态与一份相应参考值，没有预设相等或通过。

算术插图保留 8 路乘积及 4→2→1 组合归约，只标识局部算术范围，不表示流水级数、时钟周期或新的测试。128 位结果条按高 96 位/低 32 位的 3:1 比例绘制，算术结果仅进入低 32 位 S，高 96 位为零。虚线是观察／对照关系，穿过范围框不表示物理设计中的连接或一条串联测试流水线。

## 分层观测与证据边界

| 范围 | 可观察内容 | 必须保留的限制 |
| --- | --- | --- |
| 独立整数模型 | signed8 乘积求和、结果字段布局和确定性期望 | 主机模型检查不授 RTL 资格。 |
| 算术 RTL | 实际乘法、足宽归约、完整 128 位结果 | 此层不含 ready/valid、ROB、flush。报告的 22 定向＋10000 随机及 10 月 12 日统计保留原批次身份，不改写为本轮新运行。 |
| VDot FU | 接收／响应、反压保持、ROB/pdest/控制身份、flush/reset、异常及写使能 | 数据正确不替代身份与协议正确；R5 复用原 0f 记录。 |
| 真实 VFEX4 父级 | 父子握手、VDot/DIV 派发互斥、共享输出、实际门控释放 | 不扩大成所有 DIV/SQRT 动态角落的穷尽覆盖；检查器／日志变异与 RTL 故障注入分开。 |
| 整核差分 | 实际指令路径、架构状态、寄存器别名、非法配置／异常和提交后的参考比较 | 117 个不同用例与 124 次执行分开；R5 是 13 项复用＋1 项新诊断的组合，不是 fresh 14，也不倒推出所有 FU 角落已被整核重跑。 |

## 冻结来源

sources.json 保存完整路径、URL、Git blob、SHA256 和复制处理。五项均已按 Git blob 核验；对旧缓存多出的一个末尾 LF，仅在本图的新规范副本中去掉，旧缓存未改动。

- 报告：`e2c2e8d5fa9a92c5d99c3c3e3f5399d60a115c63` 的 `team/submission/latex-v1/sections/stage2.tex`，blob `0dad912d653582cdb873209cd0208bc9b8e62eed`。重点为功能验证表、S2-04 图注、控制与分层验证说明。
- 验收索引：`eca41d7cd959f5f3c4f240e382919c492d1ccb96` 的 `team/optimizations/o2/integration/firstdot-v2-0f/acceptance/acceptance-matrix.json`，blob `e0b0184822ada0ba733d1df8c6fb6e096df4b09d`。按 `model`、`fu-parent`、`fullcore` 的不同状态与限制使用；本轮没有重新打开或运行全部原始审计载荷。
- 实现：`0f12df675378556670afd0dd2153f47fcb330610` 的 VDotDatapath.scala、VDotElastic.scala、ExeUnit.scala。图中实现关系与可观测字段由实际源码支持，历史 PASS 不自动转授任何新候选。

## 建议图注

嵌套框表示 VDot 相关实现范围由算术 RTL 扩展到 FU、真实 VFEX4 父级和整核；各层分别核验并保留原证据。独立整数模型用于完整 128 位算术对照，NEMU 用于整核对应架构状态比较。实现包含不表示测试集合全包含，也不合并为一次新的 PASS。

## 复现

```text
python build_s204.py
inkscape S2-04-validation-layers.svg --export-type=pdf --export-text-to-path --export-filename=S2-04-validation-layers.pdf
pdftoppm -png -r 220 -singlefile S2-04-validation-layers.pdf S2-04-validation-layers
```

render-log.json 保存实际导出命令，render-qa.json 保存本次页面尺寸、路径文字状态、源码字号与文件摘要。技术/图面审查与人工审美最终选用分别记录。本轮没有工程构建、RTL 仿真、新性能实验、报告工作树、Git index 或 Issue 写入。
