# T10/T11 全核首批验收证据

本目录保存 **实际执行** 的117唯一用例、8片全核日志、精确异常/完整状态比较和vdot bit100负控。完整技术结论和未测边界见[验收报告](../../docs/t10-t11-acceptance-20261013.md)。`execution-acceptance.json`记录第一次严格复算的结果；后续加强验收器后的最终结果见`final-archive-recheck.json`。历史结果文件不被冒充为新运行。

- `parent/`：母用例48定向+32固定随机+37异常；生成器来自3baa，模型未改。
- `matrix/data-*`：1bd6生成的8个分片，精确并集不删改期望，D00仅作为每片合法对照重复。
- `matrix/run-*/evidence/run.log.gz`：gzip无损原始全核日志；解压SHA见archive-manifest。
- `matrix/build-*`与每片provenance：编译输入、实际运行镜像/EMU/reference/flash及配置摘要。ELF、binary、obj_dir、生成SV不进入Git；当时运行前对实际字节已核验，归档重算核对完整冻结来源回执，不声称从摘要重建了二进制。
- `matrix/negative-*`：真实vdot差分负控，包含注入器源码、正常基础reference与同镜像恢复来源。
- `components/`：先前已经来源绑定的decode/datapath/FU、全核构建、NEMU参考API、hello/vadd证据；层次分开，不把API数量当全核数量。
- `review/`：非原作者的只读审查及主审逐项处理记录；不伪造另一次独立批准。
- `acceptance-pins.json`：显式外部输入的被测source/母用例source/EMU/reference/flash/corpus计划。不是从分片相互一致反推可信。

从仓库根无需重新仿真即可复核归档：

```bash
python3 -B team/scripts/check-vdot-shards.py \
  --parent-data team/evidence/t10-t11-fullcore-20261013/parent \
  --runs team/evidence/t10-t11-fullcore-20261013/matrix --repo . \
  --expected-source 1bd6f1d9c9485695876ff37a77fbb175a5125983 \
  --expected-parent-source 3baa4112996eae0f6cb58c85ca393bb81a94a8c0 \
  --expected-emu 43fd7b094a3fb8676395dc97ca08443fb2d2d37d1dbfea0d7b9078c67087718f \
  --expected-reference e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae \
  --expected-flash a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994 \
  --expected-plan c6fec6194bbca496d0b4a128f866e7a1f4d1187d356c7d224f53e6eef699cfd1 \
  --expected-unique-cases 117
python3 -B -m unittest discover -s team/tests -p 'test_*.py' -v
bash team/scripts/check-vdot-model.sh
```

检查器要求每片七个自检、三个负控、D00前置及完整case序列、唯一实际exit0、summary之后GOOD TRAP、严格来源/镜像/配置/数据链、实际bit100差分事件与同镜像正常恢复。删除记录、拼接旧运行、统一换错SHA、仅留PASS标记等反例必须被拒绝。故障注入只证明比较链路能检出该错误，不是全部RTL故障覆盖率。

`archive-manifest.json`列最初收集的356个文件和原始解压摘要，后加文档/审查/最终回执由最终提交本身追溯；不将它误解成签名或对所有后添文件的完整目录签名。原始大日志仍在本机，不向仓库提交生成二进制。

最终主机验收：70项全部通过；原数学模型另35项及5文件一致性。最后使用补丁1.1.0的reference重跑hello/vadd三组24lane、GOOD TRAP，见`components/final-reference-hello-vadd`。

本目录`.gitattributes`禁止换行转换，并仅对原始证据关闭空白风格检查；源码/当前文档仍执行差异检查。gzip和原日志字节以实际摘要为准，不为消除空白告警修改原始证据。
