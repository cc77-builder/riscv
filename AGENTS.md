# James_Hotten O0/O1 integration scope

The current request integrates branch updates into James_Hotten and reviews
correctness, acceptance security and performance evidence.
The previous VFEX1 cleanup/main synchronization finished at e9c70db38;
its publication record is team/docs/vfex4-main-sync-20261017.md.
Current work and evidence scope: team/docs/james-o1-integration-20261018.md.
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
Three FU modes have real simulation evidence; parent EXU/full-core O1 is pending.
The frozen T12/T13 observers cannot validate O1 overlapping transactions.
Preserve archive bytes, source bindings, failure records and fail-closed checks.
Do not fabricate teammate approval, STA/PPA, performance, virtualization or
official ISA acceptance. Reports follow engineering completion and version freeze.
