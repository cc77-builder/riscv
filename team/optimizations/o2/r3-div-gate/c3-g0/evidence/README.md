# C3-G0 评审证据

本目录保存只读审查、固定历史来源摘取与新纯 Python 控制抽象检查。没有 C3 RTL、网表或新的硬件实测。

candidate-review/command-01.json 保存原实际命令、时间和退出码；control_variants.py 以绝对路径和 SHA 固定导入原 c2-g0/system_model.py，执行需要原 WSL 项目。root-review/g0-system_model.py.txt 是该导入模型的逐字节留档。此目录不声称为脱离源码仓即可执行的完整仿真包。

candidate-review 与 value-review 内各自 manifest 保持原样；本目录 manifest 进一步封存全部载荷。既有 C1/C2 原始大网表仍在原封存位置，本轮只保存审查所需的选取材料和身份，不重跑旧综合。root-review/before-* 为本轮修改文档之前的快照，旧19条版本记录必须保持。

来源不一致的初次失败与使用既有历史文档解决的回执均保留。Agent 审查不代签人工复核。
