# James_Hotten integration scope

The current request authorizes removing the retired VFEX1 implementation,
updating James_Hotten and synchronizing main, including both remote branches.
Preserve main's unique historical integration evidence through an ordinary merge.
Current cleanup/publication record: team/docs/vfex4-main-sync-20261017.md.
The retired implementation is recoverable from Git, not a second working-tree
implementation. Recovery and active test entries: team/docs/retired-vfex1.md.
Prior full-core validation in team/docs/james-fullcore-20261016.md executed against
d3706f0b8; it is not a new run of the integrated source. Historical instructions
under team/docs/history describe earlier tasks and do not override current scope.

Production uses VFEX4/VDot with NEMU 1.1.0. T14 input-product fusion is opt-in
(VDOT_T14_FUSED_INPUT=1); the default remains E3 response / II4.
T15 is a standalone parameter experiment, not a full-core SEW16 ISA change.
O0 diagnostics are incomplete; O1 is a contract, not implemented RTL.
Preserve archive bytes, source bindings, failure records and fail-closed checks.
Do not fabricate teammate approval, STA/PPA, performance, virtualization or
official ISA acceptance. Reports follow engineering completion and version freeze.
