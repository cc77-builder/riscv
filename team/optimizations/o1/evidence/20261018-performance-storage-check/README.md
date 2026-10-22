# T14/O1 性能证据的 Git 存储核验

本次先为密封目录设置专属 -text -whitespace 属性，禁止换行转换。379个暂存Git blob均与工作区逐字节一致，373个映射载荷的解压字节与原输入一致；核验结果见 [verification.json](verification.json)。没有修改密封归档，也没有执行新EMU。
