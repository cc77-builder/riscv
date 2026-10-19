# 第一笔真实 VDOT 的全核观察检查

这是运行中的部分轨迹诊断，不是完整 G3 验收。原始 stdout/stderr 均只读复制，保存 SHA/字节长度/读前后文件状态；没有修改运行中的工具或日志，没有启动 EMU。使用 Git 提交 e2d9c06 的检查器副本。截取时保留完整行，并丢弃最新全局周期全部记录，避免半拍事件。

functional-1 第一笔：ENQUEUE312745 → ACCEPT312749 → MOVE312750 → RESPONSE312751 → COMMIT312754。seq=0、ROB0:4、pdest124；接受到响应2拍。低8字节源1均为0，数学结果完整128位为0（高96位也为0）。高源lane包含a5，未参与结果。vpu完整字段跨ACCEPT/MOVE/RESPONSE一致，perf字段此笔全零且保持一致；这笔不能单独证明非零perf多事务身份区分。

negative-vdot 第一笔：ENQUEUE311080 → ACCEPT311084 → MOVE311085 → RESPONSE311086 → COMMIT311094。该任务刻意注入NEMU结果错误，本检查只核对硬件观察记录；负控成功与具体不匹配位由正式runner另行验证。若安全前缀舍弃了最后COMMIT，则 partial 不要求其终结。

各任务安全前缀的分析结果、完整计数、首笔身份和原始字段见 diagnostic.json 与子目录 analysis.json / first-transaction.json。全部结果都保留 partial 状态；尚不能据此宣称两槽覆盖、整个矩阵、全核回归或最终 G3 完成。
