# O1/O2 同镜像公平性能封存证据

36项真实运行、478个窗口、192个正式性能样本及Linux原始日志重审通过。batch128平均cycles **362.5→221，降低39.03%**，O2相对自身实测RVV为 **3.068×**；其他三场景平均周期不变。至少10%的预定batch工程目标达到，没有超过2%的场景均值退化。

## 查看结果

- [完整工程结果表](files/runs/results-01/性能结果与工程记录.md)
- [逐模式统计CSV](files/runs/results-01/summary.csv)
- [O1/O2配对比较CSV](files/runs/results-01/comparison.csv)
- [全部阶段及重放样本CSV](files/runs/results-01/samples.csv.gz)
- [严格原始日志重审回执](files/runs/results-01/verification.json)
- [精简最终结果及版本](files/runs/final-summary.json)
- [本轮实际构建配置与编译器](files/runs/campaign-01/build-profile.json)
- [最终30项主机检查](files/runs/host-check-04/verification.json)
- [工程入口与复跑说明](../../performance/README.md)

正式样本每场景每模式每方法12条；first/warmup和4次代表batch重放完整保留。重放逐seq周期与退休数一致，不增加独立样本数。约定输出、非scratch寄存器、高位、CSR、哨兵和scratch_control按冻结manifest核验；不把允许破坏的scratch宣称为全部32寄存器逐位相同。

## 字节封存和来源

共646份封存文件，原始字节228903931，存储字节38725219（约38.7MB，不含manifest及入口）。[manifest](archive-manifest.json)、[manifest摘要](archive-manifest.sha256)逐项绑定原始/存储SHA与压缩方式；gzip固定mtime且往返字节一致。

[本次G4字节复核](archive-byte-recheck.json)仅证明字节保真；功能和性能结论来自G4严格重审。原[生成时字节回执](archive-check.json)及当时封装源码原样保留，其中G3字样为复用字节工具的旧说明，后续仅修正说明并重新核验字节，原始payload/manifest未改。

导出时源码提交8c6895598a14aac42bbacb8808040550416edd78。O1实际构建源码a239dac、O2构建源码b218cbc、运行工具63b95a5分别记录；文档/封装提交不视为重新构建。两模式429项硬件文件、21236项依赖相同，只有O1/O2功能选择及各自只读观察器不同，共同T13计数；实际构建命令和七类工具版本一致。

包内保存运行命令、分离原始流、真实退出码、协议与窗口审计、工具副本、16镜像及配套文件、构建/恢复日志和主机测试失败历史。大型EMU、编译对象、生成RTL及原G3备份构建不进入本包；原始WSL输出仍保留。本轮未推送GitHub，O2默认关闭，正式T16报告后置。

## Windows或Linux离线复算

用Python3.10+运行：

    python -X utf8 -B team/optimizations/o2/performance/portable.py --archive team/optimizations/o2/evidence/20261019-performance-ab --campaign campaign-01 --output /absolute/new/portable-verification.json

工具复核全部封存字节、36项原始日志/退出码、ELF机器码与完整计数窗口、两模式协议、重放和配对统计。它不新运行EMU/NEMU，也不重复Linux的Git/依赖/编译工具来源核验。Windows实际复算回执另存交付目录。

本轮结果为固定配置的RTL周期测量，没有Fmax/面积/功耗/PPA、官方排名、最终采用或人工ACK结论；G5、O3/O4/O5和T17仍待后续完成。

## 交付补充：冻结功能语料

首次Windows完整复算在功能生成器处发现封装遗漏：该原始生成器还会读取T05 directed.jsonl及random.jsonl（仅前8条用于本功能集合）。补充数据从运行工具提交63b95a5075df7f361c4bf7b51a0bba74b6c8db17逐Git blob提取，并核验当前字节相同；没有生成新测试向量，没有改写已运行的ELF、镜像、日志或原始payload/manifest。

[support-manifest](support-manifest.json)及[摘要](support-manifest.sha256)绑定两份补充文件的原始SHA-256/Git blob；portable.py还要求语料版本与原campaign的source_commit一致，再恢复到临时检查器目录。补充交付工具33项主机测试通过（原30项＋3项语料绑定检查）；运行时原30项记录保留为当时时点。首次Windows失败与修复回执保存于交付目录。完整复算请使用当前performance/portable.py，归档内旧工具快照保持原样。

Windows原生全量离线复算已通过：[成功回执](delivery/windows-portable-audit.json)、[实际命令和退出码](delivery/windows-audit-attempt-02.json)、[33项交付检查](delivery/host-corpus-fix-01/verification.json)、[首次失败记录](delivery/windows-audit-attempt-01.json)。复算覆盖全部36项作业、478个窗口、192条正式窗口及4项重放；不增加真实EMU运行数。
