# O1 密封证据的 Git 字节保存检查

原仓库的 `team/** text eol=lf` 规则将本次 30 个 gzip 文件的暂存字节作了换行转换；工作区原文件和密封归档均未改变。问题在提交前发现，修复前清单见 [before.json](before.json)。

根目录 .gitattributes 为本次密封归档增加精确范围的 `-text -whitespace`：保留压缩数据和原始补丁/源码摘录的全部字节，不对证据施加源码排版规则。重新暂存后，430 个归档文件的 Git blob 与工作区逐字节一致，425 个映射载荷的解压摘要与原始输入一致；见 [verification.json](verification.json)。

本检查只证明 Git 存储完整性，不启动 EMU、不更改密封证据、不产生新性能或硬件验证结论。
