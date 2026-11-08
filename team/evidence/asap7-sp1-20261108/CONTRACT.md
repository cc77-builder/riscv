# SP1 ASAP7 full FU / VFEX4 synthesis contract

Source release: ffb52e4504244b7d833d311d0ce0589f883abaf8 (zjhwork2).
398 production files checked against SP1 source manifest; all 126 dependency modules exported from their pinned Git objects. Isolated Linux source snapshot, no production edits. Windows archive text normalized back to exact LF release bytes before verification. Fresh compilation; tool/dependency download caches reused.

Explicit O2=1, T14 fused input=1, P4 one cycle=1; O1 and all traces=0. MinimalConfig(1), common production FU interface and real VFEX4 including VDot/VIDiv/VFDiv and three clock gates. Not a full XiangShan core synthesis or a new DiffTest qualification.

ASAP7 7.5-track RVT/TT NLDM, nominal 0.7V/25C. Pinned five-library set and 1x LEF. Yosys 0.9 / ABC 1.01 / OpenSTA 2.0.17. ABC target 1000ps, BUFx2 drive, 5fF. Explicit pin-only zero-interconnect model, ideal clock, 0.05ns uncertainty/transition, 0.1ns input/output delay. STA five profiles: 1ns/5fF, .5ns/5fF, 2ns/5fF, 1ns/1fF, 1ns/20fF. Disable and read back CRPR; parent testEnable=0, retain enable setup checks, no added false paths.

Coverage acceptance: mapped types closed, canonical netlist topology invariant, exact ports, real gate binary semantics and connectivity, 1x LEF area match, all required path classes present, no unexplained dynamic unconstrained endpoints. A coverage PASS does not mean positive slack. Preserve all timing violations and failures. No numeric PPA gate relaxed to claim success.

SP1 replaces P products with P final result: do not reuse old 1352-flop count. Validate new register inventory against generated RTL and independent FU/parent mapping, retain single actual clock source.

Only ASAP7 is executed in this run. Historic Nangate45/ASAP7 results have different source/constraints and are context only. No fresh 0f/SP1 speedup, whole-core frequency, power, CTS/routing, hold/electrical/all-PVT signoff or mapped full-netlist equivalence claimed.
