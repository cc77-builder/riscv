# FU、父级与解码原始证据归档

本目录仅归档已完成的八次运行；没有重新构建、仿真或调用检查器。
`manifest.json` 列出 ZIP 每个成员的原路径、字节数和 SHA256；压缩后逐成员读取核验，随后复核原文件未变。
`operation-receipts.json` 保存八个原始 ChatPC 终态回执。`archive-receipt.json` 另记录本次归档作业的真实终态。

包含 FU 三次、父级两次、解码三次；两次失败分别为 FU 的 VCS 资源/缓存目录问题和解码的 classpath 预检问题。
各 run 保留原状态、命令、正/负运行日志、检查结果、源码快照、生成 RTL、来源/依赖清单及清单绑定的 DUT 可执行文件。
附带候选与当前结果文档快照；这些文档的资格仍以其各自运行时点和适用范围解释。

排除可再生成的 obj 中间文件、probe-output 编译缓存、Mill 缓存及外部 JAR/classpath 依赖实物。
精确排除计数、大小及保留原目录均见 manifest；未移动、删除或改写任何原始运行目录。
本归档不增加整核 DiffTest、应用性能或 ASIC PPA 资格。
