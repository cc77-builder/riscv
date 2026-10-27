# acc8 有界目标验证结果

状态：**TARGET_FUNCTIONAL_AND_COST_DIAGNOSTIC_PASS**；真实负控、正常恢复、独立重放及原文／隔离新源审计全部闭合。执行2026-10-26 06:29:32～07:35:17+08，归档审计完成于07:40:16。此合同专门验证新包装的正确性与成本，未设置公平预热及共同锚点，`performance_qualified=false`，不由周期差选核。

## 实际程序与边界

同一ELF包含原包装与acc8包装、原pack及全部六个冻结整数叶。旧包装各做vdot/RVV4的x0；acc8两路各做x0→x1→x0→x2；共10次完整288×288/GS32 Q和一次pack。全部调用共用同一packed W，逐行g0→g8严格执行signed转换、乘Ws、乘Xs、再加sum。

每个正常进程实际完成2,880个输出逐位比较、80个末组完整128位槽、6个判定破坏／恢复控制、输入与输出guard、context/向量CSR/FRM检查；pack后及末尾核对全部82,944字节。模型与实际ELF限定其余输入只读和完整读写足迹。没有另跑旧v2的大计划或把旧中断批当作PASS。

目标冻结源码为`8fa52a3def10bcce9bfae7a0bc874f3bbdbcb0ad`；build-02记录构建前HEAD及88项源SHA，运行前后逐项核对与已提交源一致。构建与路径检查保留原／新包装、pack、六叶完整机器字节；四项目标ELF指针／顺序／数据／golden负例全部拒绝。

## 完整观察

以下为真实CSR差值。计时器沿用既有协议；实际CSR `instret` 比静态marker路径少5条，差异已由逐退休路径闭合，不能把不同窗口口径混用。重放逐项相同，仅验证可复现，不增加样本量。

| 窗口 | 包装／方法 | 数据 | cycles | instret |
|---:|---|---:|---:|---:|
| 0 | pack | x0 | 308,734 | 430,220 |
| 1 | original / vdot | x0 | 122,917 | 92,219 |
| 2 | original / RVV4 | x0 | 109,549 | 75,371 |
| 3 | acc8 / vdot | x0 | 92,138 | 72,865 |
| 4 | acc8 / RVV4 | x0 | 85,785 | 56,017 |
| 5 | acc8 / vdot | x1 | 89,263 | 72,865 |
| 6 | acc8 / RVV4 | x1 | 85,467 | 56,017 |
| 7 | acc8 / vdot | x0 | 88,879 | 72,865 |
| 8 | acc8 / RVV4 | x0 | 84,809 | 56,017 |
| 9 | acc8 / vdot | x2 | 88,801 | 72,865 |
| 10 | acc8 / RVV4 | x2 | 84,956 | 56,017 |

两路acc8分别把实际退休指令92,219→72,865、75,371→56,017，**均减少19,354条**，与第一步实际ELF静态预测一致。固定顺序中的调用历史不同，尤其旧包装各只有一次、acc8复用多次；本表不证明公平周期收益或某种方法优于全部RVV。pack的308,734 cycles属于本BIN的一次独立观察，不能与其他合同／镜像的Q周期相加冒称实测端到端成本。

## 目标执行与闭合

| 进程 | PID | 结果 | 实际区间（+08） |
|---|---:|---|---|
| negative | 1336 | EXPECTED_VDOT_HIGHBIT_REJECTION | 06:29:32～06:29:40 |
| recovery | 1346 | SPLIT_DIFFTEST_COUNTER_PATH_PASS | 06:29:40～07:02:25 |
| replay | 3368 | SPLIT_DIFFTEST_COUNTER_PATH_PASS | 07:02:25～07:35:15 |

负控使用链接原NEMU的既有高位故障转接，在首条独立probe的实际PC `0x80001d04`、指令`0x0388000b`注入vd0 bit100，DiffTest预期退出1，9,713 guest cycles。它没有修改原NEMU或硬件。两个正常进程均HIT GOOD TRAP，2,421,026 guest cycles、3,408,780 retired；各有51,841条O2_COMMIT、44 COUNTER_ENQUEUE和44 CSR_SAMPLE。完整十Q路径、四CSR值、退休／O2协议及输入身份均通过。

正常／重放validation JSON逐字SHA相同：`7587c9a242b9bacfab781062c423929815f89cbfdb19e7c2d0485737b29f0522`。两个stderr原文也相同，SHA `80fd50420b37aaba3077a1a60fce2ca122f7560784e2523385c488c6cad03df2`；stdout包含不同宿主耗时，未声称其全部字节相同。

## 身份与证据

- ELF：`b169979ed8c4b27b3dcd45e64b5c8c8455be701f990035a66bb454bf8081ec9f`。
- BIN：`64724626a9d5f4fd4953ddef4620cd0e8f90380451d6f4671345cd688caf0536`。
- 固定T17 EMU：`ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`。
- 正常NEMU：`8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`。
- 主归档：`evidence/target-v1/archive/payload.zip`，SHA `460cda46b955ece108ec1e8c100646efcbe212e70a9f7bad8f51c219d8d23e08`；153成员、484,251,933原始字节、35,746,587压缩字节。
- 成员清单、原文复算在`archive/archive-manifest.json`和`archive/original-audit.json`；隔离复算在`fresh-source-audit/`；辅助命令、四ELF负例及首次构建准备失败在`support.zip`。

隔离审计从归档恢复88项源闭包，并补入固定审计器和19个原始历史Git对象，保持原git-show身份检查。新的Python进程重算全部原文，在依赖探针中拒绝访问原检出、构建／运行、EMU、AM、参考与flash目录。结果与原文审计相同。探针约束Python文件访问和显式子进程路径，**不是OS级沙箱**；离线审计不重新验证外部实物，实物身份由原运行前后检查承担。新增EMU为0。

首次构建准备因本模块归档适配路径不存在而失败，未启动EMU；原stderr与命令已保留。修复只在团队新增适配层，随后build-02、四项ELF负例、全部目标进程与两次原文审计通过，没有覆盖失败或改旧判定标准。

## 使用与复算

可复用的acc8源码与第一步说明见[上级结果](../RESULT.md)，实际target构建保留可链接对象。选择入口仍显式指定；本合同不切换R5默认。新完整Q融合的公平比较使用[独立合同](../../fused/target/CONTRACT.md)，不会继承本合同的运行或性能资格。

在已准备依赖的原生Linux检出内，使用不存在、位于仓库外的输出路径：

```sh
MODULE=team/optimizations/o2/r2-config-reuse/caller/runq-q288/acc8/target
python3 "$MODULE/run.py" --action build --output "$OUT/build"
python3 "$MODULE/run.py" --action elf-controls --build "$OUT/build" --output "$OUT/elf-controls"
python3 "$MODULE/run.py" --action run --build "$OUT/build" \
  --operation-id "$OPERATION_ID" --output "$OUT/campaign"
python3 "$MODULE/archive.py" --action pack --build "$OUT/build" \
  --run "$OUT/campaign" --output "$OUT/archive"
python3 "$MODULE/archive.py" --action audit-snapshot \
  --archive "$MODULE/evidence/target-v1/archive" --output "$OUT/fresh-audit"
```

`OUT`和`OPERATION_ID`由当次调用者设定；新运行先遵守协调Issue的资源与输入保护。最后一条可直接复算已交付归档，无需新增EMU；原物理环境路径是否仍可执行应另行核验。
