# James_Hotten O0/O1 integration scope

The current user authorizes merging fetched branch progress into James_Hotten
and pushing James_Hotten only, then completing FTQ/counter observations and the
O1 matrix/DiffTest negative control. Main is outside this publication scope.
The zjhwork c3c417a26 FU evidence and stricter negative gate are integrated;
that branch's historical publication instructions do not replace this scope.

The current request starts optimization on James_Hotten after branch integration
and review of correctness, acceptance security and performance evidence.
The previous VFEX1 cleanup/main synchronization finished at e9c70db38;
its publication record is team/docs/vfex4-main-sync-20261017.md.
Integration review: team/docs/james-o1-integration-20261018.md.
Current observation work and evidence: team/docs/o1-trace-20261018.md.
Parent clock optimization and earlier evidence: team/docs/o1-parent-20261018.md.
O0 matrix history: team/docs/o0-progress-20261018.md.
The matrix runner deliberately pins the existing d3706f0b8 II4 baseline;
new matrix execution does not imply integrated-source or T14 hardware coverage.
The retired implementation is recoverable from Git, not a second working-tree
implementation. Recovery and active test entries: team/docs/retired-vfex1.md.
Prior full-core validation in team/docs/james-fullcore-20261016.md executed against
d3706f0b8; it is not a new run of the integrated source. Historical instructions
under team/docs/history describe earlier tasks and do not override current scope.

Production uses VFEX4/VDot with NEMU 1.1.0. T14 input-product fusion is opt-in
(VDOT_T14_FUSED_INPUT=1); the default remains E3 response / II4.
T15 is a standalone parameter experiment, not a full-core SEW16 ISA change.
O0 diagnostics are incomplete. O1 has an opt-in RTL candidate, not accepted
hardware; VDOT_O1_HANDOFF remains off by default and requires T14 when enabled.
Three FU and real VFEX4 parent modes have simulation evidence. The parent uses
production dividers and clock gates; canceled-owner clock holds are cleared in
all three VFEX4 modes. O1 parent II2 is measured; full-core O1 acceptance remains pending.
Clock pulse reductions are simulation activity, not measured power or STA/PPA.
The frozen T12/T13 observers cannot validate O1 overlapping transactions.
VDOT_O1_TRACE is a separate default-off schema. Atomic ungated EXU frames and
ROB events are checked with the explicit one-cycle redirect delay. Three real
parent modes, trace-off RTL byte equivalence, and log corruption checks pass.
The new O1 EMU passes hello/vadd, control and frozen batch128 observations:
control commits 2157 VDots with 384 handoffs; batch commits 768 with 719 handoffs.
Schema 1 omits FTQ wrap; its protocol pass is not complete T12/T13 acceptance.
Preserve archive bytes, source bindings, failure records and fail-closed checks.
Do not fabricate teammate approval, STA/PPA, performance, virtualization or
official ISA acceptance. Reports follow engineering completion and version freeze.
