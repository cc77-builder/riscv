# P/PQ 首次完整消费者：固定输入参考结果

## 结论与适用范围

新组合取得 `FIRST_FORWARD_PSQ_REFERENCE_CAMPAIGN_PASS`：3个新的原版NEMU进程，PQ负控按指定字节被拒绝，P/PQ两个正常完整消费者通过。最终ELF已核实两臂各自的量化调用与矩阵路由。没有新增目标EMU，`performance_qualified=false`，稳定默认与原P的 `HOLD_CONTEXT_VARIATION` 保留。

本结论限固定合成D288/H768/L6/GS32模型、token=1、position=0，在共同规定prepare之后的首次完整forward。计数包含方法读取、分派和完整forward中的激活量化；不包含模型生成、打包、启动和初始化。它不能替代持续生成、全部输入或含打包端到端性能结果。

| 本次新同ELF正常臂 | forward instret | 整个参考退休量 | 窗口外退休量 | 完整state |
|---|---:|---:|---:|---|
| P，保留原量化 | 5,175,368 | 8,868,762 | 3,693,394 | PASS，3,691,424B |
| PQ，替换激活量化 | 4,784,311 | 8,477,705 | 3,693,394 | PASS，3,691,424B |

本次窗口减少 **391,057条退休指令，约7.55612%**。实际公式是 `report[18]-report[17]`；四字段依次为c0、i0、i1、c1，已直接核对生成main及原始64位report。NEMU的cycle差值分别为5,175,374和4,784,317，不是香山周期，不据此报告应用加速比。两正常臂窗口外退休量相同，但本实验未直接计数快路命中比例，命中率仍未知。

最初团队即时消息曾误用 `report[19]-report[17]`，使两臂各多3条；原始数据没有改变，差值391,057不变，以上为回读后的更正值。旧GQ的4,828,794/4,437,727已交叉核对，原发布数字正确。

## 实现与公平比较

新合同为 `r2-s3-first-forward-psq-v1`，P私有标签0x50313631，PQ标签0x50535131，MAGIC 0x5232505351563031；不改既有公开枚举。同一个77,118,304B镜像的两个正常参考，只在offset73,424,408的4B方法选择字内有差异，实际变化字节为73,424,409和73,424,410；其余字节逐一相同。

以原P cached函数为完整模板，仅克隆函数名、五处量化调用与公开薄入口。七处K288 GEMV仍调用原P，W2矩阵乘仍走原FR；**W2之前的hq量化改为Q属于本次预期变化**。原P、G、FR、FP32累加顺序、模型、库与官方程序不改。模板完整逆向恢复、旧C移除新增后逐字恢复、旧include前缀保留；main是可逆扩展，不宣称字节未变。

最终ELF检查已通过：

- 原 `consumer_paired16_cache` 的五处量化调用仍到 `quantize`，新 `consumer_paired16_quantize_cache` 的五处到 `r2_quantize_gs32_rvv`。
- PQ七个K288调用真实绑定 `q288_paired16_rvv`；唯一W2仍通过原选择器绑定FR。P原保护分支及fallback保持。
- Q为原有限参考合格的完整248B函数；除offset24/28/240/244四个外部重定位word外，实际机器字相同。共享GS为0x8498bb3c，scalar fallback为0x80003a6c，Q入口为0x80008e00。
- 原quantize、fabs、round及其浮点常量身份相同；dispatcher、公开入口、新clone的真实调用链和七个消费者的21个norm静态调用均检查。
- 原五份base源、八份量化输入、官方AM、libm和参考SO按既有身份约束使用；prepare/build/reference各在独立Python进程执行。

Q沿用既有ABI、舍入及FCSR合同，不满足快路域时恢复入口环境并整调用回退。源码静态路径对应19次n288和6次n768量化；这不是动态命中统计，也不作为性能百分比的替代。

## 实际运行与终态

新参考在2026-11-06 UTC 12:35:01–12:35:10执行；CPU affinity固定为1。每个原参考限制100M API、600秒内部、630秒所有者，整个批次2100秒绝对截止，没有扩展或追加运行。

| 用例 | PID | 退出码 | 原比较器结论 |
|---|---:|---:|---|
| PQ指定输出负控 | 486 | 2 | 在state byte152476发现唯一最低位翻转，按预期拒绝 |
| P正常 | 490 | 0 | 完整state、两侧guards、模型/gold、TLS/errno、FCSR、trap通过 |
| PQ正常 | 491 | 0 | 同上 |

三个PID不同，均 `direct_child_reaped=true`、`process_group_absent_after_exit=true`，最终 `active_pid=null`。两正常guarded-state SHA相同：

`027e4200fcbbd6453806591c355b616df27acbd219d4008d24893ac685bd814a`

完整正常比较为3,691,424B，不仅比较logits；FCSR为1，errno保留12345，五份模型及独立gold未改变。负控继续调用同一完整比较器，不放宽判定标准。

### 保留的外层收尾失败

Windows原operation `f6b0298dc0ef3f02061010e3c71e5c82.b5c1c5f46b67ebcb730d0e5cf507105b` 返回exit1、cleanup_complete=true。原因是一次性外层driver把真实成功常量 `FIRST_FORWARD_PSQ_REFERENCE_CAMPAIGN_PASS` 错写为缺少 `CAMPAIGN` 的字符串。prepare、build、reference三个独立Python stage本身全部exit0；错误发生在全部guest结束后的状态解释阶段。

原失败batch-state及脚本、日志原样保留，不改为PASS。该driver随后尚未执行的清理检查还使用了wrapper字段名 `reaped/group_absent`，而原参考回执字段是 `direct_child_reaped/process_group_absent_after_exit`；只读回读采用真实schema核对。

独立只读operation `f6b0298dc0ef3f02061010e3c71e5c82.cbdc41a46bde6df3a947e05a90c7f32e` 重新调用原参考 `validate` 审核三份既有raw，核414项输入SHA、原验证JSON、镜像差异和进程组，exit0、cleanup_complete=true。**这次没有重新运行guest、编译或修改验证器。** 因此外层脚本失败与实际参考资格分别报告。

## 交付与证据

本目录四份可执行派生源为 `prepare.py`、`derive_extension.py`、`inspect_quantize.py` 和[合同](CONTRACT.md)。结构化结论与完整身份见[REFERENCE.json](REFERENCE.json)。

[紧凑证据包](evidence/p-pq-consumer-reference-01.zip)包含源快照、controller、构建与参考元数据、三个完整guarded-state、独立gold、寄存器/CSR、失败脚本和原始回执；344个ZIP成员均已CRC及SHA256回读。包为5,870,479B：

`5e35395c107c4a5cb9fc8c76fa9f5d951a1c6b9b024ad61184a92264a17aabf2`

原始5目录共351文件、781,081,272B。包内收录327份原始文件，另24份大镜像/模型/raw保持在原路径，完整大小和SHA在[manifest.json](evidence/manifest.json)。本包是紧凑审查包，仍依赖冻结父输入，不声明脱离这些输入即可独立复现。无原始文件删除。

关键身份：

| 对象 | SHA256 |
|---|---|
| 新ELF | `c4c541678e4b844d75a1e9f1bdbc4357eae267b88d5cd516ad8a6d4ea051d3df` |
| 新BIN | `76f67cb7fe8b0cca96a8dd8b20e5fae2b1432a96759717b81fed67bba0efd0d6` |
| 构建结果 | `4aba7b5151d35e69021f650253cec63a72a5482c83ef1fe202637b0e14062750` |
| 原参考state | `fd8944829f1491a5b055159c163ad3cdc739857afdddfaa4ae4c2c0346596a93` |
| 原参考results | `505408482b195f9db318490ccb44035d85783d70d5073b1b766261bfc6ac683c` |
| 只读回读summary | `4868bea30ffeb38c62ab092ccc99e30e1f55ae60ea2b11029fff2a65e0868499` |

本机原始根位于 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/quantize-gs32-20261106-pro3/` 下的 `paired-consumer-{source,controller,build,reference,batch}-01`。Windows同名runs根的 `paired-consumer-reference-01-export` 和 `paired-consumer-evidence-01` 提供回读和归档副本。

## 复现与回退

按[合同](CONTRACT.md)取得清单中全部冻结输入，选新的隔离输出，在CPU1和新批准预算下依次用**三个独立进程**执行：

```text
python3 -B prepare.py --base <pinned-base-five> --config <config.json> --quantize <attempt-02> --output <new-controller>
python3 -B <new-controller>/build.py --output <new-build>
python3 -B <new-controller>/reference.py --build <new-build> --adapter <original-adapter> --identity <identity.json> --output <new-reference>
```

运行前应重新核资源和输入身份，不把本次批次预算当作重复运行授权。无需复用存在状态名错误的一次性外层driver；可按原stage CLI并读取其真实退出码和campaign状态。

回退只需继续选择同镜像中的原P，或保留此前已交付版本。PQ没有替换稳定默认，没有修改官方程序、共享运行输入或旧实验。下一步若获独立预算，可对本次P/PQ同ELF做目标周期观察；尚无香山cycle结果，不合并旧P窗口与本次指令节省估算加速。
