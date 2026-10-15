# T12 zufan 离线整合复核证据

结论和完整来源见[整合报告](../../docs/t12-zufan-integration-20261014.md)，机器摘要见[summary.json](summary.json)。本次新增DUT运行0；107项Python、35项模型、C judge普通/UBSan、固定NEMU短参考与既有original190/lean199工件复核均通过。生产代码保持最终受测版本，硬件候选没有启用。

两类失败没有删除或改成PASS：e5d继承压缩包的SHA失败已通过恢复原清单匹配字节解决；Windows来源`.git/index`原始字节变化仍保留严格exit1。后一项未影响1145个索引条目、原文件、refs或未跟踪工件，变更执行者未观察。原工作区8372个文件内容全部一致，详见归档内`original-trees-complete-audit.json`和`windows-index-investigation.json`。

`integration-checks.tar.gz`是小型文本回执包：实际argv/cwd/起止时间/exit/日志、各来源完整SHA和parents、merge逐blob结果、全部63窗口复核、归档修复前后hash、源码/依赖/原树检查、实际检查脚本，以及原1ba交付FINAL的只读副本。`ARCHIVE_MANIFEST.json`绑定所有成员。未重复打包镜像、工具、生成向量或大的原始日志；黄金来源复核输出与既有`../t12-r2-20261014/preflight/reference-verification.json.gz`解压字节相同，仅记录其hash和命令。

先在本目录执行 `sha256sum -c SHA256SUMS`，再按`archive.json`核对压缩包及内部清单。只向全新目录解压。回执中的绝对路径是实际运行位置，迁移时须核同依赖hash；不能把解压检查当重新跑过DUT。原始本机证据在`publish-zufan/evidence`，完整原树指纹在其中`source-snapshot-before.json`；包内记录其hash及检查结果。

本机可按新输出路径重新执行两套严格工件审计（从候选repo根运行，须保留原runs与固定资产）：

```bash
python3 -B team/scripts/verify_t12_evidence.py --repo . --runs /home/lizufan/chatpc-workspaces/xiangshan-t12-20261014-r2/runs/matrix-190 --expected-source a4fea8f69f8c2c58f986858481257d3424a903f0 --complete --output /tmp/t12-integration-original-recheck.json
python3 -B team/scripts/verify_t12_evidence.py --repo . --runs /home/lizufan/chatpc-workspaces/xiangshan-t12-20261014-r2/runs/matrix-199-lean --expected-source 8af7b21857ba2c65dbc4d835f7b2152cd6684875 --complete --output /tmp/t12-integration-lean-recheck.json
```

归档固定于本次验收/来源审计完成时点。随后本地文档提交、最终Git blob/干净状态、祖先与bundle复核回执在`publish-zufan/FINAL.json`及同级evidence中，避免在提交内循环自填自身SHA。没有联网、push、队友ACK或新RTL/STA/PPA声明。
