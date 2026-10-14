> 本文件是独立审查的只读展示副本。正文相对路径指向同目录审查包解压后的 `independent-review/`，原始正文保存在归档中，不代表所有源码副本直接铺在 GitHub 目录。参见 [README](README.md)。

# T12 software and acceptance independent review

**旧四片仍全部 NOT_ACCEPTED：exit124、无 T12C_END、无可认可的整核完成证据。** 本轮没有运行全核 EMU、没有重建 AM。新增证据来自原脚本调用、便携交叉编译、固定 NEMU 短参考执行；它们帮助排除部分软件解释，不能替旧全核运行盖章。

固定审查 b8272f2e8a62557437869c936b6ea9ce5fff84fe。另按真实 Git blob 读取 initial `9a4a67a92161beb9b13742bdb7af21c26a043bd9` 和 compact `36d390a6917e1d74c414b3edd876a3816d845287` 的 C/生成器。原运行回执、生成数据、反汇编已复制并散列，路径为 [evidence/old_runs](evidence/old_runs)，来源在两个 manifest；不能把不同阶段日志当作一个固定镜像的连续执行。

| 旧切片 | start/limit | 实际 exit | 完成 |
|---|---|---|---|
| 000 | 0/3 | 124 | 只有 begin/controls，无 end |
| 003 | 3/3 | 124 | 同上 |
| 006 | 6/2 | 124 | 同上 |
| 008 | 8/5 | 124 | 同上 |

initial 的 exit-code.txt 单独写0，但 run.log 只到 T12_BEGIN，没有 summary/good trap；foreground 重跑 exit124，停在第一个用例 post_csr 输出中途。不能据“文件里有0”恢复完整通过，也不能仅凭截断位置宣布硬件死锁。

**S01，确认的验收漏洞：计数器只检查正数，不检查位宽或执行量。** [check-t12-run.py](sources/baseline/team/scripts/check-t12-run.py) 30–32、99–105 与 [check_t12_compact.py](sources/baseline/team/scripts/check_t12_compact.py) 52–59 接受任意大 Python int；`cycle_end=18446744073709551617` 超过64位仍 PASS。compact 的 seq164 是16次 dot 的 complete-vdot：`cy=100,101 ir=100,101` 仍获 `T12_ARCHITECTURAL_SLICE_PASS`。固定硬件 CSRRS 的 noSpec/blockBack 设置在 DecodeUnit:213，dispatch 的 waitForward/robEmpty 约束在 NewDispatch:811 起；不应把这类明显不足的退休量当作16次循环完成的有效证据。严格的预期 instret 应从最终 ELF/执行路径计算，不能只测 `end>begin`。

**S02，确认的绑定缺口：compact digest 不覆盖性能计数。** C [main.c](sources/baseline/team/workloads/t12-perf/main.c) 83–91 和 Python 18–32 只混 seq/repeat/id、非scratch32个寄存器、post CSR、trap_count/cause、recovery CSR。将同一文本的 `cy=100,101` 换成 `cy=100,1000000000000`，保持 end digest 不变，checker 仍接受。这不证明真实 DUT 计数错误，但证明 digest 不能为加速比字段提供它宣称的“状态/order”以外的保护。应绑定四个原始 counter、计时配置和执行量，保留完整 raw log SHA。

**S03，确认的来源绑定缺口：receipt 是声明，未验证实际镜像/日志/运行工具。** compact `bind():62–74` 检查字符串字段与 `--diff` 存在，却不读取 image、EMU/reference、log 的实际字节。最小 CLI 反例使用不存在的 `/definitely/nonexistent/{emu,ref.so,image.bin}` 和64个0的 image_sha256，配一个合成完整 transcript，exit0 接受；见 [CLI 日志](logs/compact-counterexample-cli.log)。旧 full checker 的 fault PC 也仅比较文本 epc==expected_pc 且≥0x80000000；两者一起从80001000改80002000仍接受。C 的实际 fault symbol 检查较强，因此这是**独立验收缺口，不是已证明镜像执行了错误 PC**。验收入口需要可信 launcher 产物：直接散列实文件、ELF fault 符号、命令实际参数和值、日志 SHA、wait 得到的子进程退出码，而不是仅相互比较自报 JSON。无法仅靠 unsigned JSON 证明运行真实性。

**S04，确认的终态覆盖漏洞：循环次数可被大量缩短而结果不变。** `generate_t12.py:87–99,123–144` 中 div-mix 32轮与1轮、branch 128轮与1轮、wrap1024轮与只执行 v10/v11/v12/v13 各一次、complete-vdot16轮与1轮，均有相同最终可观察向量状态。compact 的整个 case 只混一次最终状态，不能区分这些执行。现有 loop-label/source 字符串测试不是动态覆盖。应计入与迭代次数有关的标量签名或保留经过核验的退休/PC trace；取消、共享 FU 竞争、ROB/FTQ 环绕仍需真实 RTL 事件，参考执行没有这些微架构事件。

**S05，确认的异常可观察性缺口，非已证实 RTL bug。** 非法用例目标是 v16，随后合法 recovery 写 v10；trap handler [harness.S](sources/baseline/team/workloads/vdot-exceptions/harness.S) 199–202 只采 CSR，返回 resume，完整 VR 是在 `vdot_observe:124–132` 才保存。C `verify():48–57` 用最终 after 与期望比较，并将 view.post 换为 pre 交给 inherited judge。最小反例：非法指令瞬间错误改写非目的 v10，随后合法 recovery 正确覆盖 v10；所有现有最终检查与 digest 都看不到这个错误。

已将**固定 C verify/judge 真正交叉编译并在 NEMU 执行**：正常 verdict0；持久 v16 错误 verdict7；被 recovery 擦除的 v10 错误 verdict0；recovery VL改7 verdict20，见 [软件结果](validation/software/results.json)。这是针对判定器的故障注入，不伪装成真实硬件产生了错误。真实完整逐步 DiffTest 可能另行捕获该错误；这里只证明 C 终态检查与 digest 不能独立证明 fault 时无部分更新，不能据此断言已绕过真实 DiffTest。最小改善是恢复前增加合法配置下完整32寄存器的 trap-time snapshot，并将 CSR 原值保存在切配置之前；为非法目标无写与非目的保持分别比对。该捕获本身需处理 vstart/VS-Off，不能为了方便在 fault CSR 捕获前改变状态。

**未确认格式化或无限循环 bug。** initial 和 baseline 中 hex 都是有符号 `int i=60; i>=0; i-=4`，16轮停止；decimal 是至多20次除10及至多20次反向输出，buf[21] 足够。真实交叉编译检查0、1、9、10、99、100、2³²−1、2⁶³、2⁶⁴−1 的 decimal 与 hex，18项输出正确、均有限返回。禁止凭 `%10` 或 `i-=4` 就声称已定位 timeout。

compact 的 C FNV-1a 与 Python `<Q` 小端序列在 seq0、seq8 实际运行匹配（`eaa9321b8aaab53a`、`a8c54d1e61b7dbf9`）；struct vector_csrs 是六个 uint64、48字节，未发现该结构 padding/端序误配。原 case ID 的 `do...while(*id++)` 包含一个 NUL，Python 也混入一个 NUL；scratch 都混16字节零。**已验证没有这几类 digest 实现错误，不代表计数器或所有证据已被 digest 覆盖。**

本轮还直接编译原 `generate_t12.py` 生成的 sites、原 harness.S、原 C main/verify/digest 和 judge，以小 wrapper 调用13个原 stress case，在固定 NEMU 参考中全部 return0；五个非法 VL 都经真实 trap handler/recovery。测得 custom 指令尝试数依次为1、4、3、4、64、256、128、3072、2、2、2、2、2，最终13例摘要 `2e51e6e6b71a5ebd` 与 checker 相同。第一例含三次负控检查共45,128条参考指令，后续简单 case 也约19,500条；吞吐/日志/自检成本值得在真 EMU 上定位。**这些是本探针的参考指令计数，不是旧镜像的全核周期或已证明 timeout 原因。** [13例结果](validation/software/real-t12-results.json)、[日志](logs/small-t12-reference.log)。

仍正确的保护也已实测：真实 exit124 与缺 end 都被 compact checker 拒绝；禁止修补成“允许 timeout”。C 对初始32寄存器、non-scratch完整终态、guard、CSR、trap count/cause、fault符号、tval0和recovery状态有实际检查。main.c 中禁写错误和恒定返回PASS并不是目前发现的问题；高96/preserved/CSR 负控也确实运行。所有合成反例的文件名都带 SYNTHETIC，不能拿它们作为比赛或整核运行证据。

复现入口为 [checker_counterexamples.py](scripts/checker_counterexamples.py)、[software_reference.py](scripts/software_reference.py)、[t12_small_reference.py](scripts/t12_small_reference.py)。每条工具命令与 exit 在 logs/*.command.json。下一次主实现定位 timeout 时，最小有效证据是一个切片中最近退休 PC/retired count、UART/heartbeat 边界以及实际子进程退出原因；没有这些，不能在“硬件死锁”和“仿真成本”间下定论。
