# R3 DIV取消关钟修复：全核构建与NEMU差分结果

本轮完成新EMU构建、14项实际全核作业和严格原文复算。源码为O2＋H1＋DIV取消关钟修复。

本地硬件提交：0f12df675378556670afd0dd2153f47fcb330610；EMU SHA256：2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。

- 13项正常差分通过，1项bit100负控被DiffTest按预期拒绝，随后同镜像正常库恢复通过。
- 117唯一功能/异常case，8分片执行124次；正常提交5378条vdot。
- hello/vadd、控制、dense及两项补充诊断通过；110项主机测试通过。
- 严格复算核对429份硬件源码和21236份依赖；完整128位结果和O2控制检查保持。

| O2覆盖 | 次数 |
| --- | ---: |
| MULTI_INFLIGHT | 2829 |
| TRIPLE_OVERLAP | 2133 |
| FULL_STALL | 13 |
| KILL_P | 37 |
| KILL_R | 29 |
| PARTIAL_KILL | 1 |

配置为MinimalConfig/单核/单线程EMU，O2及T14融合开启、O1关闭，O2/T13观察开启。NEMU/镜像/观察器和判据沿用固定合同。

本轮只证明整核正确性与差分链路；取消后零多余时钟脉冲证据仍来自前轮真实父级严格检查。未做新公平周期A/B、综合STA、功耗测量或运行期全核reset，不代签人工验收。

旧H1 build保存在/home/riscv/riscv-lab/o2-h1-build-before-r3-div-gate-20261024。当前build/emu是修复版。下一步以同镜像进行修复前后周期不退化检查，再做同约束成本/STA。

仅本地提交，无GitHub推送。原始工作根：/home/riscv/riscv-lab/o2-r3-div-gate-fullcore-20261024。

查看[合同](CONTRACT.md)、[封存清单](evidence/20261024-fullcore/archive-manifest.json)；原始命令、退出码、日志及生成物哈希随证据保存。
