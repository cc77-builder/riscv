# Same-stage arithmetic expression screen, v3

This separately identified experiment retains all v1/v2 raw evidence and the
original production source. It uses the same fixed generation and nominal cost
receipts, complete CommonFuCostTop, library, tools and path-only relocated
mapping/STA scripts. The selected product expression is independently proved
over all eight complete outputs before synthesis.

The optional `flat19` reducer replaces the widening 17/18/19-bit intermediate
tree with one signed19 expression summing the eight signed16 input products.
For arbitrary signed16 inputs the exact sum is in [-262144,262136], which fits
signed19. The final result still sign-extends only to the low word and forces
bits127:32 to zero. A second unconstrained SAT miter compares all128 output bits
for every combination of the eight16-bit inputs, including values unreachable
from byte multiplication. Exact inverse edits recover the original reducer.

The change may allow the existing Yosys alumacc pass to combine addends. No
claimed area or timing benefit is assumed. The P products, P/R ctrl/perf,
valids, R result, clock/reset/flush and complete public IO remain untouched.
Earliest E2 response and unstalled II1 are structurally preserved; no gate,
test-enable assumption, extra stage, rounding, or approximate arithmetic is used.

Both proofs must finish successfully before mapping. Complete port identity,
all1870 functional DFFs, five path classes, constant-only setup warnings and
all input hashes are checked. The old 24017.406 point is the common comparator;
the 20000 library-area target is a soft candidate-selection budget. This is an
isolated synthesis-input screen, not a whole-core or application PASS.

CPU1/nice5/one worker remains within the existing four-core assignments. Total
budget540s, each proof120s, mapping180s, STA60s. TERM/INT only latch an interrupt;
bounded wait safe points (at most0.25s apart) enter child cleanup after Popen has
returned its process object. Further signals never raise inside cleanup. No
automatic retry or new guest is requested. The two frozen input trees cannot
contain or be contained by the new output directory. All failed and successful
artifacts remain separately identified.
