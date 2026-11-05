# S1-01 开发环境与协同验证框架

本候选为单张正式工程结构图。原生尺寸 **160 × 120 mm**；正文实测最小 **11.622 pt**，DiffTest 标注约 11.906 pt。SVG 可编辑，PDF 字体已嵌入，PNG 为实际 PDF 的 220 dpi 渲染。技术审查与人工审美认可分别记录，当前尚无人工最终选用结论。

## 图意与边界

- 历史范围是 **2026-10-09 阶段一 hello/vadd**。Windows 外框表示宿主，WSL2 Ubuntu 内框表示构建和仿真环境及原生文件系统，不表示机器网络或操作系统进程拓扑。
- 四条构建路径分别为香山 Scala/Chisel → RTL → EMU、AM 程序 → ELF → 程序 BIN、独立 boot-flash.S → 启动 flash、NEMU 源码 → 参考库。编译器和完整命令为简化而未逐项画入。
- 程序 BIN、启动 flash、NEMU 参考库是不同文件。“共同输入”的集合节点表示 BIN 与 flash 两项同时作为运行输入，不表示文件合并或同一二进制。历史启动 flash 为 12 字节；程序 BIN 并非这份 flash。
- EMU 和动态参考库分别被执行侧使用，`--diff` 表示运行中加载所指定参考库；DUT/REF 框为功能角色，不宣称两套独立可执行进程。
- 实线表示构建依赖，虚线表示运行使用或架构状态流。DiffTest 接收一份 DUT 对应提交状态与一份参考状态；不表示内部周期锁步、FU 响应即退休或一次运行已经 PASS。
- 未把 environment.md 中来自 **2026-10-24 R4** 的 Windows 原生 Git／发布职责填入 10 月 9 日历史图，也未混入最终 0f 组合身份。未画波形输出，避免将 FST 误接为 DiffTest 单独产物。

## 建议图注

阶段一（2026-10-09）历史开发环境及构建、运行关系。构建和仿真位于 Windows 宿主承载的 WSL2 Ubuntu 原生文件系统；程序 BIN、共同启动 flash 和 NEMU 动态参考库是不同输入。模型框表示功能角色，DiffTest 比较对应的架构状态。实线为构建依赖，虚线为运行使用关系；本图不表示物理拓扑、内部周期同步或新的验证通过结果。

## 冻结来源

前五项固定在 `cc77-builder/riscv` 提交 `eca41d7cd959f5f3c4f240e382919c492d1ccb96`；报告对应 James_Hotten 提交 `e2c2e8d5fa9a92c5d99c3c3e3f5399d60a115c63`。完整 URL、Git blob、SHA256 与本地映射见 sources.json；六项均已按 Git blob 算法核验原始 UTF-8 字节。

| 来源 | 直接支持的图示内容 |
| --- | --- |
| team/docs/environment.md | L5：10 月 9 日 Windows/WSL2 Ubuntu 环境；L34–44：历史版本锁；L50–64：工具链。L13–20 的 Git 发布分工属于后期实践，未纳入图内。 |
| team/docs/stage1.md | L5、21–31：EMU/参考库/工作负载、共同启动 flash、参考库加载；L61：架构状态比较；历史 hello/vadd 范围。 |
| team/scripts/stage1.sh | L18–31：参考库与 EMU 构建；L34–49：程序、ELF/BIN 与独立启动镜像；L52–64：实际 `-i`、`--flash`、`--diff` 使用。 |
| team/workloads/hello-vadd/boot-flash.S | 独立启动汇编源码，保留原三条指令，不在图中杜撰指令。 |
| team/evidence/stage1-20261009/hello-vadd-summary.log | 实际加载的程序 BIN、参考库和 flash，以及启用 DiffTest 的历史记录；未将日志 PASS 变为新图的运行结果。 |
| team/submission/latex-v1/sections/stage1.tex | 环境原生目录说明；“部署任务的依赖关系”与“程序装载、启动与串口输出”小节解释工具链与 ELF/BIN 的不同用途。使用已验证的规范 e2 字节，不把额外换行缓存或后期草稿冒充该版本。 |

## 复现与检查

`build_s101.py` 生成 SVG、结构清单，并从 source-api.json 恢复冻结来源及验证 Git blob。图形渲染仅调用本地文档工具：

```text
python build_s101.py
inkscape S1-01-environment.svg --export-type=pdf --export-filename=S1-01-environment.pdf
pdftoppm -png -r 220 -singlefile S1-01-environment.pdf S1-01-environment
```

render-log.json 保存本次实际渲染命令和返回状态；render-qa.json 保存字体、页面边界及文件摘要。图中无外链图片、虚构日志、波形或成功标记。本轮没有运行任何工程构建、仿真或新性能实验，没有写报告工作树、Git index 或 Issue。
