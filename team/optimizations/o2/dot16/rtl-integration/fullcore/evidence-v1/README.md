# 整核验证原始证据 v1

这是五次既有操作的归档：image-01、build-01、native-01、native-02、smoke-01。最终六例合法整核 DiffTest 结果见 [RESULT.md](../RESULT.md)；归档不新增验证资格。

| 文件 | 用途 |
| --- | --- |
| raw.zip | 144 个原始成员，包含两次失败及成功运行、源码快照和绑定的运行时产物 |
| manifest.json | 每个成员的原路径、大小、完整 SHA256，以及运行状态和归档身份 |
| operation-receipts.json | 五次实际 ChatPC 操作的完整终态回执 |
| archive-operation-receipt.json | 本次归档自身的独立终态回执 |
| pack_evidence.py | 实际使用的只归档入口，未调用构建或测试 |

归档 SHA256：`dc2929eb9399b7274ec7111a87b5ac00f7a9aecc89bbbf6c3cab31d95e60449c`。压缩大小 23182665 字节，原始成员合计 89127207 字节。每个归档成员都经解压流式 SHA/大小检查，原文件随后再次核 SHA；Windows 与 WSL 输出一致。

包内 `records/<运行名>/` 保留原记录、完整日志及源码快照；`delivery/` 保存生产 patch、源码清单与本轮入口；`runtime/` 保存绑定的 EMU、reference 和必要接口文件。重复路径只收录一份，成员映射以 manifest 为准。

生成 C++、RTL、对象、PCH 与缓存未全部复制；它们继续保留在原构建位置，2,014 个生成文件的完整身份位于包内 `records/pre-native-freeze.json`。工具/JAR/动态库依赖的身份记录保留，除绑定运行时文件外未复制所有安装载荷。因此该包用于结果审计及原环境复现，不声称是可直接在任意机器运行的独立发行包。

`pack_evidence.py` 的源执行位置和 Windows 目标反映实际本机操作；全部生成文件和原失败目录未被修改，未重跑六例。脚本中的“新目录不存在”保护是为了保留旧记录；若重新归档，应使用新目录并核对输入身份。
