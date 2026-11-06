# dot16 独立原型成本：原始证据归档

本目录补齐 [原型结果第 4 节](../RESULT.md#4-同条件综合与时序) 的原始文件，方便脱离本机路径复核。原计算发生于 **2026-11-05 UTC**；本次 **2026-11-06 UTC** 只读复核并归档，没有新综合、STA、构建或 guest 运行。原报告、源码、运行目录和失败证据均保持原样。

## 比较范围

原计算比较 `Dot16Prototype(8,false)`、`Dot16Prototype(16,false)` 和 `Dot16Prototype(16,true)`。三个对象均包含 P/R 两槽寄存器、32 位 tag 和简化弹性控制；外部提供 kill 决策。它们不是生产 VDot FU、父执行单元或整核。共同条件和代码见 [Dot16.scala](../Dot16.scala)、[cost.py](../cost.py) 及归档中的原 `manifest.json`。

| 指标 | baseline8 | direct16 | split16 |
| --- | ---: | ---: | ---: |
| 单元面积（Liberty area 单位） | 7173.222 | 13850.886 | 13867.112 |
| 映射 DFF 单元数 | 230 | 358 | 364 |
| 最差 slack（ns，原 1 ns 约束） | -0.240952 | -0.317437 | -0.409741 |

direct16 / baseline8 面积比为 1.930916。此数值只描述该独立原型及原映射流程；三个原型均未满足这组 1 ns 约束。不能据此计算当前集成 RTL 的整核面积、最高频率、功耗或应用加速比。split16 的保存结果仍显示较差的最差 slack 和略大面积；本次归档没有改变原来的方案选择。

## 文件与身份

- [raw.zip](raw.zip)：原 `dot16-cost-v5-pro2-8951c67e` 目录的全部 **56 个普通文件／41,299,036 原始字节**，包含三个实际输入 RTL、原映射网表/JSON、全部 15 份 STA 路径、约束、综合/STA 日志，以及 split16 的原始和适配网表重读记录。
- [manifest.json](manifest.json)：每个成员的原始字节数和 SHA256；ZIP 共 **2,322,141 B**，SHA256 `f82bff076ab4eb8ad8fc5bf9d4e180bd7ad9588bb16e72f0a31ab0779c11e9ed`。
- [verification.json](verification.json)：此次只读复核结果。原总 `result.json` SHA256 仍为 `12fa34225823f298aa61d972e6124019d2435ac4aea425a6297c54cd85aee0a5`。
- [original-operation.json](original-operation.json)：重新读取的原成功工具回执，operation `626659bd04cf00cf6a5fd074939373bd.5c5a36475a641149cfc5dee4a4751425`，exit 0、cleanup complete；stdout 与原结果各变体一致。
- [archive-operation.json](archive-operation.json)：此次归档的实际执行回执，operation `0844a5921b2fa4d9e47903bfc930fdee.ab12c45090f60723941e35058018ef73`，2026-11-06 14:54:31.883～14:54:34.177 UTC，exit 0、cleanup complete。

只读复核重用已冻结的 `cost_helpers.py` 解析 15 份 STA 报告，核对映射单元/DFF 计数、原 Yosys stat 面积、约束警告和记录身份；对 split16 保存的两份重读 JSON 重新比较完整模块图并验证原图摘要。**未重新执行 Yosys 或 OpenSTA，也未重新加载库计算面积。** 库身份仍由原 manifest 固定，库本体不在此包中。

所有 ZIP 成员均已解压读取并逐 SHA 校验，原目录在归档前后逐文件一致。本目录的局部 Git 属性保留归档和记录的原始字节。工具回执时钟和原 WSL 运行器时钟分别保留在 verification 中，不拼接成新的运行区间。

## 工程接续

此目录接续同账号 WORK6670578319 / UPDATE6670959414，仅补充已完成成本筛选的可追溯性。生产 FU/整核 PPA、当前 Q288 与完整 forward 的资格继续以各自合同及真实运行结果判断，本次归档不新增资格，也不是正在进行的 Q/PQ 运行的前置条件。
