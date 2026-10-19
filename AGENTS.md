# James_Hotten latest O1 integration scope

Current task: integrate latest zjhwork cd866d52d into James_Hotten 724fbb12f.
Use the latest event observer by default; VDOT_O1_TRACE_PROFILE=frames explicitly
selects the existing atomic-frame/FTQ/CSR observer. Never emit both protocols.
Retain clock-cancellation and all four acceptance/provenance gate repairs.
Imported historical results retain their source bindings; merged RTL needs fresh
validation. Main is excluded and O1 stays off. Current integration record:
team/docs/o1-latest-integration-20261019.md. Statements below describe prior work.

Integration validation: 606 host tests, 35 compiled option cases, three frame
parent modes/four faults, two latest parent modes/seven faults and event-enabled
parent execution pass. Source and archive identity receipts are preserved in
team/evidence/o1-latest-integration-20261019. No new full-core run or merged-source
performance claim. This merge remains local; main and remote refs are unchanged.

The current user authorizes committing and pushing the completed observation
work to James_Hotten, then synchronizing other branches and reviewing all work
for correctness, acceptance vulnerabilities, optimization and performance.
Main is outside this publication scope; O1 remains off by default.
The zjhwork c3c417a26 FU evidence and stricter negative gate are integrated;
that branch's historical publication instructions do not replace this scope.

The current request starts optimization on James_Hotten after branch integration
and review of correctness, acceptance security and performance evidence.
The previous VFEX1 cleanup/main synchronization finished at e9c70db38;
its publication record is team/docs/vfex4-main-sync-20261017.md.
Integration review: team/docs/james-o1-integration-20261018.md.
Current observation work and evidence: team/docs/o1-complete-20261018.md.
Earlier schema-1 observation evidence: team/docs/o1-trace-20261018.md.
Parent clock optimization and earlier evidence: team/docs/o1-parent-20261018.md.
O0 matrix history: team/docs/o0-progress-20261018.md.
The historical O0 matrix runner deliberately pins the d3706f0b8 II4 baseline;
its runs do not imply integrated-source or T14 hardware coverage. The separate
O1 extended runner binds the current patched source, EMU and observer profile.
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
The new source-bound O1 EMU passes hello/vadd, control, 117 unique matrix cases
(124 executions), real bit100 DiffTest injection and same-image normal recovery.
The O2 companion preserves schema 1 and adds FTQ identity and CSR ownership,
sampling and per-commit-slot windows. Control records 2157 VDot commits, 384
handoffs and 329 FTQ wraps; calibration/batch validate 25 windows and 100 CSR
samples. All 13 actual launches meet expectations (12 exit 0, one injected exit 1).
72 host tests and 15 real-log corruption checks pass. Current O1 original/lean
software-plan runs and full same-source performance A/B remain separate work.
The observation checkpoint fb1e7bdc8 is pushed to James_Hotten. Both remotes
were fetched again; all ten actual remote branch tips are already included.
The four gate defects from team/docs/o1-publication-review-20261018.md are
repaired; closure and limits: team/docs/o1-gate-fixes-20261018.md. Aggregate
host checks pass (504), with 13 archived CPU logs rechecked, 24 FTQ mutations,
15 prior corruption checks and 8 real parent binary replays. No new CPU run
or performance claim is made. This publication includes the reviewed repairs; production
RTL and historical evidence bytes are unchanged. O1 remains off by default.
Preserve archive bytes, source bindings, failure records and fail-closed checks.
Do not fabricate teammate approval, STA/PPA, performance, virtualization or
official ISA acceptance. Reports follow engineering completion and version freeze.
