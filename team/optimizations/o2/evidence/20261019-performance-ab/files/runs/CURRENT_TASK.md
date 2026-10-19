# Historical execution/recovery note

The G4 run and strict Linux recheck are now complete. Read final-summary.json and results-01. The text below is the preserved execution checkpoint, not a new instruction to rerun work.

# Current task: G4 O1/O2 fair same-image performance

User explicitly authorized this turn. Complete actual 36 jobs + Linux original-log recheck + sealed evidence + Windows portable full-window/protocol/statistics recheck + engineering results. Local only, NO GitHub push, NO G5/adoption/default switching, T16 formal report deferred. No subagents per newest developer rule.

Repo /home/riscv/riscv-lab/zjhwork2-review-20261018/repo, branch local/o2-performance-20261019.
Work /home/riscv/riscv-lab/o2-performance-20261019.
Windows D:/yanyi/riscv大赛/doc/O1_O2同镜像性能对比_20261019.
Current code commit 14a1fa4 (compare/profile/results frozen at c7e887d; 63b95a5 adds portable/archive;14a1fa4 only labels G4 archive status). Build source a239dac; 30 host tests PASS at host-check-04 (latest source hashes; finalizer uses it). host-check-01's 2 failures were isolated fixture shared-dict aliasing, fixed; retained.

Matched new O1 build o1-build-01 PASS:
EMU6699225b76ceae479060741026683bb03de069c1e10a4a94e463304ba1e322d0.
O2 reused G3 build-03 pins from /home/riscv/riscv-lab/o2-fullcore-20261019/build-03, EMU ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57 at repo/build/emu.
429 source/21236 deps match. O1 uses HANDOFF1/O2_ELASTIC0/O1_TRACE1/O2_TRACE0. O2 inverse. Common fused1,T13_TRACE1,T12_TRACE0. Actual normalized Verilator cmd and all seven tool-version logs match. LLVM19 compiler observed via /proc (build-monitor.json).
1687 old G3 non-object generated files saved/restored and hashes verified; backup o1-build-01/preserved-o2-generated-build excluded from future archive. Original EMU unchanged.

Active launcher unified exec session63663 runs work/launch.py:
wait build -> compare.py --output campaign-01 -> results.py --campaign campaign-01 --output results-01.
Builder session20323 finished PASS. Monitor17655 finished.
Do not start another campaign or mutate frozen compare.py/profile.py/CONTRACT.md or shared checkers during run.
Latest known 17:56 Beijing: both calibration modes passed,2/36; functional O2/d0-s00 andO1/d0-s01 running. O1 initial smoke took24m wall due host-time variation, but all11guestcycles/instructions match historical; never use hostelapsed in speedup. See calibration-historical-sanity.json.
Status: python3 -B work/status.py (records resource-monitor snapshots). Read launch-state.json and campaign-01/state.json. Final launcher ALL_COMMANDS_FINISHED and exit0 required.

16 original frozen images ours-images-02, all208 tar entries bytechecked. Portable copies209 (incl images.json) under portable-inputs/ours with input-manifest.json, strongly bound to original artifacts.
36 runs total: 32 initial (16 each mode) +4 batch d0-s02 replay jobs; 478 full windows,192measured. Exact four scenarios single1/chain256/batch128/stream64,3datasetsx4measured. each mode measured RVV denominator, no legacy362.5/678 reused. Max2 singlethreadEMU processes, pair sequential alternating order, stage barriers smoke->functional->performance->replay. Seed1,128MB,max2mcycles,120m timeout.
Original estimates75min runtime. User commentary at most60s during ongoing work.

Code team/optimizations/o2/performance:
build_o1.py 3 safetytests; compare.py + build_profile.py (24tests total with inherited statistical/ref tests); results.py strict original-log/protocol/window recheck and CSV/工程MD; portable.py (3 extra tests) replays sealed raw logs+ELF/data exact windows+bothprotocols+stats on Windows stdlib only; archive.py uses G3 archive format and guard G4campaign/recheck/launcherPASS.
portable extracts campaign/checker-snapshots tools and portable inputs from archive; uses original Git-bound run checker sources. Does not run EMU/NEMU or Linux source/dependency/toolchain provenance again. Windows Python D:/python location/python.exe.
archive excludes products,preserved-o2-generated-build,objects,__pycache__,rtl,emu-compile; tools from Git-tracked performance dir. Includes small ELF/bin portable input snapshots and all failures/metadata. All raw/stored SHA recorded/gzip deterministic.

Still to do after actual run:
- If failure inspect and fix minimally, preserve failed attempt. No silent reruns/omissions.
- If >2% regression investigate actual traces before adoption claim; 10% batch target uses newly measured O1, not history.
- results-01 verification must OFFLINE_O1_O2_PAIRED_RECHECK_PASS; result table, CSV raw samples, ratio of sums.
- Update README/AGENTS/OPTIMIZATION/O2README engineering status and versions, no formal report. Commit docs/source locally before export; source/artifact checks kept immutable.
- Add narrow .gitattributes prefix team/optimizations/o2/evidence/20261019-performance-ab/** -text -whitespace BEFORE staging archive to protect binary ELF/gzip.
- Seal work with archive.py --work-root WORK --output repo/team/optimizations/o2/evidence/20261019-performance-ab, output must fresh/outside work.
- Ensure no process continues writing work before seal (launcher/monitor complete; last status snapshot then stop).
- Archive README human index after create, then Windows copy; copy portable.py to Windows full source folder or standalone.
- Run Windows portable.py --archive ARCHIVE --campaign campaign-01 --output new windows-portable-audit.json. Should ARCHIVE_O1_O2_WINDOWS_RECHECK_PASS. Architecture counter windows replay uses extracted16inputs, rawlogs36, original frozen checkers from snapshots; exact cached compare.
- Verify every staged Git blob for entire new evidence prefix SHA equals source bytes and archive storedSHA (git cat-file --batch efficient). Local commit only, clean status.
- Final receipts outside sealed work (e.g /home/riscv/riscv-lab/o2-performance-delivery-20261019), copy Git/window receipts + final results to Windows entry. Open README/result in app if helpful.
- Final user gets concise4scene table O1/O2 cycles, reduction, O2relativeRVV + targetassessment, localcommit/noPush, Windowsfile link. No new PPA/officialrank or finaladoption claim.

## Latest checkpoint 2026-10-19 19:06 Asia/Shanghai
Campaign still RUNNING/performance,24/36 done, no failures. O2 dataset2 single9/12 andO1 dataset1 stream10/12 active.
Dataset0 all four pairs completed: single71 both (RVV85.25),chain1857 both (RVV5440.5),batch O1=362.5 O2=221 (RVV678 both),stream1127.5 both (RVV1133).
Dataset1 single andbatch pairs same asdataset0; chain also1857 both. Thus batch8/12 formal samples show39.03448% reduction,3.067873xrelativeRVV. Still provisional untilall36 andstrictreplay.
paired_progress.py prints completed-dataset provisional means only. partial-batch-preview-01.json andWindows阶段预览_仅首数据集.json bindfirstdataset originalresult/rawSHA; neveruseasfinalsamplesextra.
ROOTHEAD9ff9395 only adds narrow .gitattributes forG4evidence/** -text -whitespace; runtimecommit63b95a5 unchanged,sourcecompare/profile/results c7e887d.
Finalhostreceipt host-check-04/verification.json=30PASS withlatest source hashes; finish_docs.pyuses04 andrequiresallpySHAsunchanged. archive.py statusnow O1_O2_PERFORMANCE_ARCHIVE_BYTES_PASS.
finish_docs.py guarded finalizer prepared inWORK,runonlyafterlauncherALL_COMMANDS_FINISHED &results01PASS; updatesrootAGENTS/OPTIMIZATION/O2README/performanceREADME andfinal-summary.json. Itclarifiesallowed scratchregisterscope.
Windows compatibility-preflight-01 nativePython3.13 passedexact11O1calibrationcounter/ELF/protocolwindows,receiptcopiedWORK/windows-compatibility-01; NOTfullG4pass.
WORK/reused-o2-build saves16reusedO2buildreceipts matchedbyteforbyteagainstsealedG3manifest. WORK/o1-generated-auxiliary-source saves10stagedcompilerauxiliaryinputs. Botharearchivable.
Nextfinishall24performance+4replay ->Linuxresults ->guardedfinaldocs/localcommit ->archivefreshrepo/team/optimizations/o2/evidence/20261019-performance-ab ->Windowscopy/nativeportable.pyfull36recheck ->Gitblobexact-byteverification/localcommit ->finalWindowsREADME/results.
Do notpushGitHub,changeISA/NEMU/inputs/default,runG5,orstartnewcampaignjustbecausecurrenttakeslong.

Latest checkpoint 2026-10-19T19:24:58.646631+08:00:31/36 completed;performance stageonlyO1dataset2streamactive. Batchall3datasets/12formalcustom/RVV samplesmeasured:O1mean362.5(range360..364),O2mean221(all221),bothRVV678,reduction39.03448%,O2speedup3.067873x. See batch-complete-checkpoint.json (stillnotwholeG4PASS). Othercompletedscene/data pairsallunchanged. Needfinishlaststream+4replays thenactualLinuxresults/Windowsfullportable/pack/commit asalreadyinplan.
