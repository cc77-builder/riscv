# R5 稳定入口验证证据

操作 `20261024-LiZufan001-r5-stable-1221`；范围与使用入口见 [STABLE.md](../../STABLE.md)。最终结论来自 [verify-03/result.json](verify-03/result.json)；所有目录均为独立输出，未覆盖先前结果。

| 目录 | 实际结果与用途 |
| --- | --- |
| `verify-03/` | 最终清单与验证器实际 GNU 构建；全库对象等于 C02，三种配置/八个别名的 caller/link 对象相等，七种错误配置被拒绝 |
| `prior-attempts/verify-01/` | 初版有限检查 PASS；随后只读审查发现复合表达式可能绕过宏检查，因此不作为最终配置边界验收 |
| `prior-attempts/verify-02/` | 宏长度与优先级修正后实际 PASS；随后补强库资格关联，最终增加全对象字节比较，不仅比较 `.text` 和符号诊断 |
| `prior-attempts/verify-01-sources/`、`verify-02-sources/` | 各轮实际头文件、验证器及 manifest 原字节；公共汇编/原头文件/Makefile 在这些轮次中保持相同身份 |
| `snapshot-transfer*.json` | Windows 发布工作区至 Linux 原生逐文件快照的源、目的、12 个文件 SHA；这是覆盖明确输入的快照，不是另一个 Git 完整检出 |
| `host-*.json`、`verify-*.stdout.log`、`verify-*.stderr.log` | 实际宿主执行回执与验证器原输出；命令级 stdout/stderr/退出码保留在各 verify 目录 |

整库对象强门禁覆盖 ELF 节成员、符号、重定位、属性和全部字节，避免局部 `.text` 相同仍可能出现链接差异的证明缺口。三种模式的完整对象比较没有删节、改写或规范化差异。所有新增执行仅为主机 GNU 编译/链接/检查，新增 EMU/NEMU 均为 0。

最终源码、清单、输出与 Git stage-0 普通文件的字节绑定由 `publication-check.json` 记录；该文件本身在提交前另行核对。归档与运行定位保留真实路径，仅作为复核线索，不把个人绝对路径写入公共使用命令。Windows 回执时钟与 WSL 程序时钟分别保留，不跨时钟源相减计算耗时。
