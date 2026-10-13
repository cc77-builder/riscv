# dev集成验证记录

2026-10-13（北京时间）。dev由c1ef31d81快进到James_Hotten的a978b3b8f；随后只添加进度/集成文档与本目录。来源5个提交保留，main与James_Hotten没有改动。

| 记录 | 含义 |
| --- | --- |
| [merge-verification.json](merge-verification.json) | 快进后的完整树与来源一致；既有8归档431项摘要、最终硬件源码/向量绑定通过 |
| [model-tests.txt](model-tests.txt) | 本次dev实际运行23个Python方法，退出0 |
| [judge-tests.txt](judge-tests.txt) | 本次dev实际编译并运行生产C判定器，25项通过 |
| [vdot-source-verification.txt](vdot-source-verification.txt) / [baseline-source-verification.txt](baseline-source-verification.txt) | 当前编译来源与原软件验收的source.sha256一致 |

实际命令为python3 -m unittest discover -s team/tests -p 'test_*.py' -v；gcc -std=c11 -Wall -Wextra -Werror -Iteam/workloads/vdot-exceptions team/workloads/vdot-exceptions/judge.c team/tests/test_exception_judge.c -o team/out/dev-merge-20261013/judge-test后执行；软件来源以sha256sum -c核对原audit-fixes归档的两个build/source.sha256。原生可执行文件留team/out。

本次没有重跑NEMU/QEMU/RTL重型仿真。原1341/1304/12022项运行仅按不变源码、输入和历史证据继承，不能称作dev当天新运行，也不因此关闭全核或成员验收。当前合入范围及待办见 [集成说明](../../docs/dev-integration-20261013.md)。

archive.sha256保存本目录原始字节，.gitattributes防止换行转换。
