# Fixed-weight 8×32 stream consumer — v1

Identity: `r2-s3-fixed-weight-8x32-v1`. Source base:
`3d56e84aca5cc63bf235f6fbcf76ce8079c9581c`. This contract is fixed before the first
build/run. It is a bounded engineering example, not an existing LLM application.

## Question and implementation

Does the optional split-input interface remain useful when A is fixed throughout
one complete stream? The former caller copied A (256 bytes) on every invocation.
Here `fixed_packed` copies A once per measured stream, copies only each new
32-byte x, calls the unchanged packed leaf, and extracts eight INT32 results.
`fixed_split` directly reads the same A and each x and performs the same extraction.
Both capture context fields once and use one indirect leaf call per step. No
allocation, persistent cache, cross-call invalidation, new shape, or RTL change.

The API is GNU C11, RV64/lp64d, VLEN128, VS enabled. A is row-major signed INT8
8×32. X is N consecutive signed INT8 vectors of length 32. A/X permit arbitrary
byte alignment. Y contains N×8 INT32 values with natural alignment. Slots contain
N×8 complete 128-bit results and start at a 16-byte boundary. The packed buffer
has 288 bytes. All five buffers and the 64-byte context are valid and mutually
disjoint for the call. A, X, count, and function pointers remain stable. The
valid and qualified counts are exactly N=1 and N=4. Other counts, including zero,
are outside this contract; the public maximum 4 is a capacity bound. No argument
checking is performed. Each slot has the exact signed sum in low32 and zero high96.
Vector registers/configuration are clobbered; return VL=8,VTYPE=0,VSTART=0,VCSR=7.
Clocks/reset/FU interfaces are unchanged: fixed T17 O2+H1 hardware, first response
2 cycles and unstalled II=1 under its existing contract; no new hardware/PPA claim.

## Fair comparison and decision fixed in advance

One new BIN contains both interfaces and all six unchanged arithmetic variants:
S3 reuse vdot, S0 basic/reuse RVV, S3 basic RVV, firstdot reuse RVV, S3 reuse RVV.
Use the same frozen GNU compiler/options, AM, T17 EMU, normal NEMU and flash.
All official programs and old inputs/receipts remain unchanged.

The whole timer window includes wrapper/context loads, the one-time A preparation
on packed, all N steps, loop/index control, x copies, indirect calls, full slot
writes, and tight INT32 extraction. Caller-owned context construction and input,
golden, guard preparation are outside for both. There is no per-step conditioning,
UART, timer or oracle inside a stream. Each complete stream gets the same RVV
conditioning beforehand. Samples are printed only after the entire plan.

N=4 is primary; N=1 is the setup control. Report measured total and total/N as
including initialization. Do not infer steady-state time from subtraction or
from adding separately measured components. No N=16 expansion in this contract.

Each N uses three existing O3 datasets, six repeats (first, warmup, then four
formal), alternating all 12 methods forward/backward, with the same split-vdot
stream before/after each group. There are 504 windows, 288 formal method windows
and 48 formal anchors in total. Each N/method has 12 formal observations. The x
sequence differs by step through a documented deterministic signed-byte transform;
functional data additionally cover extremes and zeros. Exact inputs and plan are
generated into the manifest and independently checked in the ELF.

For each N separately: each same-algorithm split/packed pair qualifies if total
formal cycles decrease at least 5% and no dataset regresses over 1%. All six must
qualify to recommend the interface for that N. Algorithm selection independently
requires the shared anchors to vary no more than 1% in each dataset and vdot to
beat the lowest-total split RVV by at least 0.5% in all dataset×order cells.
Use integer cross-products at thresholds. Otherwise report STOP_INTERFACE,
HOLD_CONTEXT_VARIATION or KEEP_RVV_EXPLICIT as appropriate; no post-hoc threshold
changes. Report all N and all RVV variants. R5 default and prior hoisted HOLD stay.

## Verification and finite resources

1. Exact old leaf bytes, all-word split relocation certificates, executable/BIN
   equality, source regeneration and actual GNU command/option binding.
2. Bounded real-ELF scalar path execution: one wrapper, N leaves, balanced calls,
   A copied exactly once only for packed, x copied exactly 32N bytes, complete
   A/x vector footprints, N×128 slot and N×32 Y writes, no split packed access.
   No unknown vector result may control an address or branch.
3. Both wrappers, all six algorithms, seven datasets, two misaligned/disjoint
   input layouts, N=4: 168 functional streams. Every measured N=1/4 stream is
   also fully checked. Retain every step's slots/Y, check all bytes including
   unused tails, input/guard/context integrity and returned CSRs. Eight live
   judge fault controls include a nonfinal high96 fault and a CSR fault.
4. New BIN: real vd0 bit100 DiffTest negative, normal recovery, independent normal
   replay. First functional call is split/vdot so its exact first custom PC is
   fixed. Full UART, RETIRE paths, CSR counter/ROB identities, O2 protocol and
   all custom commits must agree. Expected total is derived from the manifest:
   functional vdot steps plus measured vdot steps; conditioning is RVV only.
5. Meaningful host fault controls and raw-evidence mutations check the new
   lifecycle/output/trace boundaries. Host results never substitute for ISA runs.
6. Archive complete commands/source manifests and raw successful/failed logs;
   independently unpack/recompute. Build/link an explicit optional C library
   and verify its wrapper/leaf machine bytes against the qualified ELF.

Overall CPU budget is four. Performance EMUs run serially with isolated cwd and
read-only frozen inputs. One campaign of three EMUs, each capped at 8,000,000
simulated cycles and 7200 host seconds; at most one justified revision after a
specific failure, with a new source/build identity and original failure retained.
The larger cycle budget covers twice the old window count, N=4 sequence work and
full intermediate-output checks. Budget exhaustion never grants performance
qualification. STOP/HOLD is a valid decision, not a reason to extend the matrix.
