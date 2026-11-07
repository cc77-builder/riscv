# Real inline signed8 source candidate: local qualification v3

The only production-source candidate is team-owned VDotDatapath.scala:
add a pure combinational VDotSignedByteProduct inline implementation and
connect each existing Products lane to its signed8-by-signed8/signed16 result.
Keep all128-bit input interfaces, eight16-bit products, lane order and ignored
upper64 input bits. No clock/reset/state, approximate arithmetic, synthesis-only
replacement, extra latency, clock gate, or protocol change is introduced.
The enclosing FU retains its existing clock/reset/flush, earliest E2 response
and unstalled II1 contract; actual inherited FU tests remain necessary.

The original resident source and complete cached classpath are read-only.
Use the completed common generation's pinned recipe and original source/class
identities, compiling only the candidate source and unchanged cost generator
into one fresh complete class directory. Put that entire directory (including
anonymous Bundle classes) first for both FU and cost generation. Do not copy a
subset of class files or treat old cached Products as the new candidate.
Four new elaborations cover cost/FU with feature0/1. Each has five real design SV files,
the exact generated comment-only extern_modules.sv, its complete filelist.f,
and its actual inline-resource manifest. The external stub must equal the
original generated macro header plus only the named external-module comment. Verify eight inline instances, identical
arithmetic across all four consumers and byte-identical enclosing wrapper,
reducer and top against each applicable original generated input.

An unconstrained miter compares all eight complete16-bit outputs of the actual
old Products and actual new Products plus the emitted inline definition.
Read and flatten the real inline module; an uninterpreted blackbox is forbidden.
All new FU simulations and mapping consume those exact generated files.
The existing complete 10022-vector FU tests, dot16 extra coverage and four
negative checker controls run on both feature settings. No test/checker source,
expected inventory or official program is changed.

For each feature, use its existing complete CommonFuCostTop mapping/STA template.
The only template differences are inverse-checked paths and explicitly reading
the fifth real arithmetic module. Keep the same library, tools, period, IO
constraints and path classes. All cells must map to real library cells; check
complete port identity, original1742/1870 DFFs, independent cell-area sums,
all five paths and original constant-only setup warning checks.
Feature0 and feature1 both use the new arithmetic for a fair incremental-cost
comparison. The previous direct-expression screen's area is not assumed to
transfer to this different generated hierarchy.

CPU1/nice5, one worker; Java ActiveProcessorCount1/SerialGC, Verilator/make j1.
Bind installed Verilator share resources; set its real share/verilator root.
Use /usr/bin:/bin PATH and explicit /usr/bin/make plus command-line make
CXX/LINK=/usr/local/bin/clang++ (actual LLVM19, fixed SHA), AR=/usr/bin/ar; clear inherited make override files.
Total1200s including preflight and final audit; compile/build commands at most300s,
each elaboration180s, SAT120s, mapping240s, STA60s and each FU run60s.
Signals only latch and are acted on at bounded0.25s waits after Popen returns;
cleanup uses the existing process-group helper, without async signal exceptions.
Fresh outputs are outside the repository, original cost/FU roots and source
directory. Source snapshots, all failures, real generated inputs, commands,
tool identities, process closures and before/after input hashes are retained.

Success is local generated-arithmetic equivalence, existing FU functional
qualification and independently measured nominal FU synthesis/STA results.
It grants no new parent/fullcore/application/performance qualification.
The original four-arm guest, resident RTL/cache and deployed/default behavior
are unchanged. Production adoption, any future EMU and the 20000 area preference
or50% application objective must be reported against their actual evidence.

Attempt local-01 stopped after successful compilation and first elaboration:
the v1 controller incorrectly expected exactly five SV files, excluding the
actual comment-only extern_modules.sv. It performed no SAT/FU/mapping and
acquired no qualification. Preserve it unchanged. This v2 corrects only that
manifest expectation, binds and checks both file lists, and requires the exact
comment-only stub; it does not suppress generated content or weaken proof.

Attempt local-02 completed all four elaborations and the actual flattened SAT
proof, then failed before C++ compilation: installed Verilator's Clang-only
flags are incompatible with g++. Preserve it unchanged. V3 uses the actual
installed Clang19 executable with explicit --compiler clang and command-line
CXX/LINK selection. No test, RTL, proof or synthesis algorithm changes.
