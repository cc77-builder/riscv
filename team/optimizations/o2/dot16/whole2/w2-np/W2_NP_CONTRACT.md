# Fixed K768 N/P geometry derivation, v1

This is a software-source and GNU machine-code qualification only. It creates
no guest, reference run, EMU build/run or production routing change.

Inputs are the frozen N Q288 source/ELF and P source used in the current
four-arm experiment, plus the existing fixed W2 layout header. All sources,
the established ELF reader/process helper, and five GNU binaries are pinned.
M=288, K=768, GS=32, VLEN=128, RV64/lp64d, RNE and enabled FS/VS are fixed.
Packing is [36][24][8][32], 221184 int8 bytes; x has768 bytes, Ws is
row-major[288][24], Xs has24 FP32 elements. The 56-byte context preserves
offsets0/8/16/24/32/40/48; spans are disjoint, floats4-byte and slots16-byte aligned.

N changes exactly three instructions; P changes seven across its guard, fast
path and complete fallback. Scale stride36->96, groups9->24, and scale footer
252->672 are the only numerical edits. Tile count36, W advance256, x advance32,
scale inner advance4 and output advance32 remain. P scans all768 x bytes for
-128 before fast/fallback dispatch; its threshold and reloads are unchanged.
Every symbol/local-label rename uses complete tokens, so prefix-overlapping
fallback labels cannot be corrupted. Exact inverse edits recover each parent.

GNU assembles/links both complete parents and candidates. The complete parent
functions must match the frozen qualified Q288 ELF and their recorded machine
SHA: N312 bytes and P1096 bytes (both P returns and the fallback included).
Independent ADDI bit-field edits produce exactly three/seven changed words;
the whole candidate function must equal this expected machine byte-for-byte.
GNU nm exact symbol address/hex size is cross-checked with the frozen ELF reader.
Disassembly is preserved for review, not used to truncate at internal labels.
No objcopy rewrites a frozen ELF.

Groups0..23 retain INT32->FP32, multiply Ws, multiply Xs, left-fold add, with no
FMA/reordering. All other instructions, FP sequence, guard/fallback, branches,
custom words, CSR and eight full128-bit output slots retain the parent's form.
Exit is vl8/e8/m1, vstart0 and vcsr7 for the fixed entry profile; arbitrary-vcsr
preservation is not claimed. No Q288 runtime PASS transfers to K768.

CPU1/nice5, one worker, total180s and30s per GNU command. TERM/INT only latch;
the controller waits in bounded0.25s safe points, reaps/kills process groups
with the existing helper and preserves all failures. Outputs must be fresh and
separate from both frozen trees. Final source/tool hashes and child closure are
checked. This evidence does not establish K768 numerical execution, application
speedup, retired-instruction counts or the human's50% optimization objective.

The existing full-forward consumer maps its K768 non-FR branch to old q768_ta.
Future N/P application integration needs explicit new K768 dispatch; changing
only the Q288 kernel selection is insufficient. Original four-arm inputs stay
frozen, with K768 still on their original FR route.
