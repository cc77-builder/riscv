# acc8 第一阶段结果：共同消费者开销静态筛选通过

结论：**`ACC8_STATIC_SCREEN_PASS`**。这是本机逐位数值、真实GNU编译及完整ELF路径的结果；新增EMU为0，目标周期、完整目标DiffTest和应用性能仍未验证。稳定firstdot V2、原Q288包装、六个整数叶和官方程序未因本候选改变。

合同：[r2-s3-runq-q288-acc8-screen-v1](CONTRACT.md)。研究动机与下一阶段条件见[研究方案](../RESEARCH.md)。本次完整检查实际执行于2026-10-26 05:26:58～05:27:30（UTC+08:00），此前05:23的单对象探索只确认驻留机制；输出目录中的0528是标识，不当作实际开始时间。

## 1. 实际修改与身份

将原 `sums[8]` 展开为8个显式FP32累加器，每行仍按group0…8进行signed转换、乘Ws、乘Xs、加自身累加器。仅独立行交错。pack、结构体、指针约束、ABI、编译参数、324次opaque叶调用、原始尺度布局及六个叶体均保持；不使用FMA、fast-math、LTO、自动向量化、预乘尺度或跨组重新结合。

实际GNU在`fs0`…`fs7`保存八个和；完整调用仅入口/出口各8次FP保存/恢复。八组host检查的288个输出均逐位通过；不能由此代替目标执行。

| 对象 | SHA-256 |
| --- | --- |
| 原Q288源 | `05955ce611f180c6cdef3becf74be47b5246f06c85931640f1c6ad33746bada0` |
| acc8源 | `f0c557cb837ac05ff713b0eaadb7949b3ba623ae54fe1c02aedcd4220f5bf8d1` |
| 原完整ELF | `7f2c3d6de93f979cc252379a8fe2147e0d7ff121b0a38151f4604ee832884f26` |
| acc8完整ELF | `8fcb7bb4fda1ce7dcc2cf4c41f83bfed3733cee363df2cf2a3d760a737103888` |
| acc8 BIN | `ee19bba14a0b28967581473d444fa362eb874fef522f796a166f8b279d8d2ce9` |
| 复用整数库参考对象 | `f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3` |

构建时HEAD为`ff873a0e043fcebea0617d08b452d92c64804650`，acc8当时是未提交候选；该SHA不是acc8提交身份。实际80个源/依赖由[build.json](evidence/screen-v1/build.json)逐文件哈希与源码快照绑定，打包时再次与工作树核对。最终承载提交由Git历史定位，不重写原始构建记录。host正样本、独立GNU源和当前候选C逐字节相同。

## 2. 六种完整Q路径的静态结果

下面包含测量窗内16条公共定时器指令、整个q288_full入口/出口和324次完整整数叶。两个ELF中pack与各完整叶机器码逐字节相同；操作数/尺度地址、所有叶参数和算术次数均校验。计数来自完整ELF控制/地址路径解释器，不是实际退休计数。

| 叶方法 | 原指令数 | acc8指令数 | 减少 |
| --- | ---: | ---: | ---: |
| vdot | 92,224 | 72,870 | 20.9859% |
| RVV0 | 124,948 | 105,594 | 15.4896% |
| RVV1 | 99,028 | 79,674 | 19.5440% |
| RVV2 | 93,844 | 74,490 | 20.6236% |
| RVV3 | 75,700 | 56,346 | 25.5667% |
| RVV4 | 75,376 | 56,022 | 25.6766% |

六种路径均少19,354条架构指令，全部超过合同事前5%静态筛选门槛；这不是官方评分门槛或性能优选。RVV4拥有更少静态指令，也不能据此选其为目标最快方法。

| 共同包装指标 | 原包装 | acc8 |
| --- | ---: | ---: |
| q288_full自身指令 | 39,072 | 19,718 |
| 完整路径条件分支 | 3,240 | 360 |
| FP栈读次数 | 2,881 | 8 |
| FP栈写次数 | 2,593 | 8 |
| FP栈读写逻辑字节 | 21,904 B | 128 B |
| 代码大小 | 408 B | 576 B |
| 窗内额外栈深度 | 192 B | 192 B |
| signed转换/FP乘/FP加 | 2,592 / 5,184 / 2,592 | 相同 |
| 完整整数叶调用 | 324 | 324 |

FP栈字节是指令地址访问量，不是DRAM或cache事务。profile中的`load/store`包含`fload/fstore`，不能把父类和子类相加。192 B从计时窗入口SP向下统计；timer在窗外已分配的48 B不包含在此数中，不称为完整应用最大栈。代码增加168 B与潜在I-cache代价必须由后续目标执行判断。原始全部访问类别、opcode、各函数计数和每行地址证据见[comparison.json](evidence/screen-v1/comparison.json)。

## 3. 实际验证与负控

| 层级 | 已完成结果 | 边界 |
| --- | --- | --- |
| 主机严格数值 | x0→x1→x0→x2、min-min、max-max、min-max、zero-weight共8次，全部288输出位模式、packed全字节、输入只读及guards通过 | 主机叶为独立计算shim，不是目标整数叶执行 |
| FMA差异见证 | 严格结果0，融合结果`0xa3800000`；仍禁止融合 | 防止错误使用容差或FMA语义 |
| 展开行错误负控 | 实际编译`s1=s0+a1` mutant，由独立row-major数值oracle拒绝 | 错误保持FP计数不变，说明仅数指令不足 |
| 真实GNU独立编译 | GNU11.4，rv64gv/lp64d，严格-O2；三C翻译单元/叶/定时器独立编译，源、BIN、工具、外部库身份绑定 | 实际构建，不是只生成汇编文本 |
| ELF完整路径 | 六叶身份、324次精确实参、全部Ws/Xs、packed/slot/Y范围、RNE/CSR及全宽callee-saved恢复通过 | FP/向量值为unknown，检查控制/地址/ABI，不替代数值或DiffTest |
| 五项实际ELF负控 | signed→unsigned、mul→add、错误Ws索引、panel步长256→264、fs恢复读错槽，均以具体预期错误拒绝 | mutant原word/改word/PC/ELF哈希均记录；原官方程序未改 |
| 原始封存 | 172成员、3,407,676 B原文→857,730 B ZIP，全部成员解压读回哈希相等 | 只证明字节清单/传输；不声称独立语义重放或目标运行 |

团队父`check.py`仅增加显式候选源/引擎参数，默认原路径不变。`trace.py`新增显式group尺度顺序：真实GNU先读row7再读row0…6，因此允许当前叶返回到下一叶之间八个精确地址各出现一次；跨组、漏读、重读仍拒绝，最后一组单独闭合。原默认row顺序保留，旧提交与快照不变。独立只读审查未见阻断；确认了上述访存包含关系及栈深度口径。

## 4. 证据与复现

[归档清单](evidence/screen-v1/manifest.json)、[原始ZIP](evidence/screen-v1/raw.zip)、[主机结果](evidence/screen-v1/host.json)、[ELF拒错](evidence/screen-v1/elf-rejections.json)、[最终作业回执](evidence/screen-v1/checks.json)。ZIP SHA-256：`b3fc245f9f2f5a63e6ce1e65cf984ca44c5df15910d995f6f65d7e3add247cac`。

发布前发现根目录 team/** text 规则使首次本地Git入库将ZIP的CRLF字节规范化，blob由857,730变成857,720 B。已新增模块级 *.zip binary，按未变化的原件重新入库，并从Git index读回全部172成员核对原始哈希；[字节检查回执](evidence/screen-v1/git-byte-check.json)保留前后身份。最初本地提交 a3a2151acd42f2196fa1dd39f3528a56337c7b42 是中间检查点，正确归档由后续修复提交承载；原件、清单和验证结果未改。Git bundle格式通过不能代替载荷字节检查。

ZIP包含原/新ELF与BIN、原构建记录、完整新源码快照、对象、实际命令/stdout/stderr、单对象探索、正/负host动态库及源码、逐叶路径比较和封存脚本。ELF负控在内存中施加，记录完整基准ELF和修改坐标/word/哈希，可确定性重建，不伪称保留了未落盘的mutant文件。Python缓存不属于证据载荷。

在已有依赖就绪的原生工作区运行，所有输出必须为仓库外新路径。`ACC8_OUT`父目录先建立；`verify`和`compare`的output是文件，其他动作的output为新目录。

```sh
ACC8_MODULE=team/optimizations/o2/r2-config-reuse/caller/runq-q288/acc8
python3 "$ACC8_MODULE/screen.py" --action host --output "$ACC8_OUT/host"
python3 "$ACC8_MODULE/screen.py" --action build --output "$ACC8_OUT/build"
python3 "$ACC8_MODULE/screen.py" --action verify --build "$ACC8_OUT/build" --output "$ACC8_OUT/verify.json"
python3 "$ACC8_MODULE/screen.py" --action elf --build "$ACC8_OUT/build" --output "$ACC8_OUT/elf"
python3 "$ACC8_MODULE/screen.py" --action compare --build "$ACC8_OUT/build" \
  --baseline-build "$ACC8_BASELINE_BUILD" --output "$ACC8_OUT/comparison.json"
```

`ACC8_BASELINE_BUILD`至少包含归档`baseline/vdot-perf.elf`，哈希被固定检查。候选build/verify还需要原合同规定的固定T17/AM身份和GNU工具；不声称ZIP自带全部硬件环境或新机器安装资格。父生成器仍保留其旧46-Q计划元数据，但本screen没有EMU动作，本阶段一条也未执行。

下一步只按[研究方案A](../RESEARCH.md#5-有条件的后续研究方案)另立有界目标合同；若实测收益不足、共同锚点不稳或强RVV消除优势，按预定停止条件记录，不把本静态PASS提升为默认采用。
