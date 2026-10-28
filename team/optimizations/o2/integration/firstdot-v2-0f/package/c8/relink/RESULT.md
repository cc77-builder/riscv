# C8 软件包接回普通 C 程序：最终镜像等价结果

**PASS：C8 软件包已真实接入原普通 C 夹具，最终可执行内容完全等价。** 依照事先约定，复用第26条同镜像的功能、NEMU/O2、bit100拒错、恢复与重放证据；本轮无需新增全核仿真。

执行者 @cc77-builder / Agent；操作ID 20261027-cc77-builder-c8-relink。生产RTL保持0f，旧四尺寸默认不变；未提交或上传GitHub。

## 接入内容

- 原主程序只把底层头的包含改为 `selected_gemv_c8.h`。
- 8×32 reuse vdot/RVV × 三数据集，共6个函数表项改用 `xs_c8_gemv_8x32` / `xs_c8_gemv_8x32_rvv`。其余42项、数据、期望值、顺序和校验不变，没有重新生成测试向量。
- 真正从 `libxs_gemv_c8.a(gemv.o)` 链入完整合格对象；SDK程序源目录没有gemv.S，对象目录没有绕过库的gemv.o。GNU依赖文件和link map确认实际包含SDK头、实际抽取库成员。
- 在全新输出中分别构建原源码复制对照和SDK接入程序，保留原AM/klib和链接次序；只有输出路径和记录链接来源的选项不同。

源码见 [source](source/)，重建和完整核验见 [README](README.md)。

## 三方等价结果

比较对象：原已通过全核的C8镜像 → 本轮原源码复制对照 → 本轮SDK接入版。

| 项目 | 结果 |
| --- | --- |
| 完整BIN | 三者全字节一致，均31,440字节 |
| BIN SHA256 | 56805506eb98b68269c73a3645d8f75dff73b697e30dec5f93ccc4716089ad34 |
| 入口 | 均0x80000000；ABI flags及ISA属性一致 |
| PT_LOAD | 同地址、权限、对齐及完整内容；file30,024B，memory31,440B，零填充1,416B |
| 装载节 | 所有SHF_ALLOC节的位置、大小、权限、对齐及内容一致，包括BSS |
| 函数 | 16个公共函数及启动/主程序等5个函数的地址、大小和机器码一致 |
| 测试表与数据 | 48条64字节调用记录与原计划逐项匹配；12组输入数组地址及内容一致 |
| GNU链接 | 无未解析符号；map与实际子命令证明使用SDK库成员 |
| 完整ELF原字节 | 不同；差异仅在.debug_info、.debug_line、.debug_line_str |
| 独立GNU复核 | 分别objcopy --strip-debug后，三份完整ELF全字节一致 |
| 去调试ELF SHA256 | 7e26e295fb020a63334026f768ed4825372266465b4e6008973de966fefc04ab |

调试节保存源文件/头文件路径及行号等信息，构建目录与头文件发生变化会改变这些记录。保留原ELF，没有通过删除调试信息来掩盖装载差异：主检查器已先完整比较装载内容和计划，去调试检查是独立补充证据。

原ELF SHA256：02159c7ef78cb31eb24cf706bf2974eadea313710563f235f2b11a7bb922de56。  
复制对照ELF SHA256：cfad14278ee4a3590de9bcbe7589b808fd91959156cef93ba92a78a90db0d99b。  
SDK接入ELF SHA256：f0ddf1167c961101e70f58cfd012ae788d2965324ad057aa4ade5af1de5bc42e。

## 检查器拒错与输入保护

7项负控全部被拒绝：实际ELF代码字节改坏、调用表改坏、启动入口改变、BSS大小改变、ISA属性改变、输入计划改变，以及真实GNU链接错误空库。另有只改调试字节的正控，确认不会将纯调试变化判为行为改变。错误镜像只用于主机检查，没有送入全核。

627项完整输入与封存运行证据绑定当前0f、EMU/NEMU及GNU工具。原33个矩阵进程和3个C进程的审计关系及全部封存输出树保持；本轮没有重复解析相同原始日志或伪造新PASS。当前操作保存了真实新GNU构建和最终镜像等价证据。

成功流水线：2026-10-27T21:59:40.771873+08:00 至 2026-10-27T21:59:43.182911+08:00，exit0。两次GNU构建，8份主流水线命令回执，另3份去调试GNU检查回执。流程首次通过，负控和原始文件全部保留。

## 已完成与未新增的结论

当前C8包已从“对象/可重定位链接合格”推进到“接回原可运行C程序、完整镜像等价”。原16函数、48例/两轮96正常调用（8×32占12例/24调用）的功能资格可明确复用；不是本轮重新执行这些调用。

新增EMU/NEMU/全核运行均为0。当前验证的是原测试夹具的包化接入，不是新的实际应用或LLM推理。没有新的周期、面积、STA或功耗测量。原273 cycles与1.095238×属于第25条性能矩阵，不是本C程序新测数据。

最小软件包接入闭环已完成。后续选择具体应用后再固定新的输入/调用路径/最终镜像合同；需要新性能结论时使用同路径firstdot/RVV及必要的集成前对照。另可继续4×8、16×64控制差异只读归因；4×13保留RVV。生产RTL和旧默认均不因本次接入改变。

## 证据

- [完整数据记录](record.json)，统一版本档案第28条：C8-RELINK-DIVFIX0F-CLEAN02-20261027-01。
- [比较与负控结果](evidence/report.json)、[实际接入link map](evidence/integrated/link.map)、[GNU独立复核](evidence/postcheck/result.json)。
- [原图/新图比较](evidence/integrated/equivalence.json)、[输入身份](evidence/qualification/report.json)、[执行回执](evidence/pipeline.command.json)。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-relink-01。
- 完整本地归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-relink-final-archive-01。
- 软件基点c823a8786e052c6e26f6915563c42b6d730dd8e3；硬件0f12df675378556670afd0dd2153f47fcb330610。当前状态为本地未提交材料，不能把基点SHA当作已包含本次修改的提交。
