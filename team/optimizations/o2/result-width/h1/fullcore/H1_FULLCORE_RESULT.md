# H1 全核构建与 NEMU 差分回归结果

2026-10-21：**新 H1 全核构建、14 项作业与严格离线重审通过。** 本轮是功能与协同验证，未运行公平性能 A/B。

硬件提交：8b5024fcbd96986871cc40ce8c9fb71a67c495eb。新 EMU SHA256：e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747。

MinimalConfig、单核/单线程EMU、O2与O2/T13观察开启；两编译线程、12G JVM。观察器保持原协议，从公开128位结果整值比较，不修改黄金数据或NEMU语义。生成RTL证实R槽32位保存、输出高96位零。

- 13项正常完整作业通过，1项bit100故障参考库按预期被DiffTest拒绝；同镜像恢复正常库通过。
- 原矩阵117个唯一用例（80合法/37异常），8分片执行124次；hello/vadd、F2v、dense和两个补充诊断均通过。
- 正常程序共5378条vdot提交；95项主机检查通过。完整128位、身份/perf、反压、取消与正常排空按原门禁验证。

| 全核O2覆盖 | 实际计数 |
| --- | ---: |
| MULTI_INFLIGHT | 2829 |
| TRIPLE_OVERLAP | 2133 |
| FULL_STALL | 13 |
| KILL_P | 37 |
| KILL_R | 29 |
| PARTIAL_KILL | 1 |

严格重审从原始stdout/stderr、真实退出码、已固定Git blob、硬件pins、输入来源重新复算；不是只检查成功字符串。核对429份硬件源和21236份依赖文件。

已有局部面积收益仍为FU约2.334%、完整父级约0.137%，此前ready负载退化与1ns未收敛限制保持。全核正确性通过不改变该物理时序结论；没有本轮新加速比、运行期全核reset、功耗或真实工艺Fmax证据。

当前repo/build/emu已是H1；B0原构建完整保存在/home/riscv/riscv-lab/o2-b0-build-before-h1-20261021，R0锁继续绑定B0。下一步为同镜像B0/H1周期不退化检查，R4独立成员复现/最终采用仍待完成。没有推送GitHub，自动审查不代替队友ACK。

原始证据根：/home/riscv/riscv-lab/o2-h1-fullcore-20261021。核心证据为campaign-state、build-01、core-01、supplements-01、recheck-01及final-validation.json。

可复现命令见[合同](CONTRACT.md)、launch.py与归档；已完成campaign不可重复启动。新运行应使用新目录。归档入口[evidence/20261021-fullcore/archive-manifest.json](evidence/20261021-fullcore/archive-manifest.json)；归档字节/便携轨迹复核不等于重新运行EMU，也不代替Linux来源核验。
