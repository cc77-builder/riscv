# Unified harness independent review (Jade agent)

## Executed reference validation

```bash
python3 -B repo/team/workloads/unified-vdot/reference.py --variant jade --reference variants/jade/nemu/build/riscv64-nemu-interpreter-so --output runs/jade-reference-01
```

Result: `PASS_REFERENCE_ONLY`; 10,154 generic/native alias pairs, 10,022 known-state RVV cases, 10,022 batch cases (each also checks custom batch). This exercises the original 22 directed and 10,000 random vector records, complete 128-bit destinations, declared scratch, non-destination vectors, relevant GPR preservation, and vector CSR preservation. It is NEMU functional validation only, not RTL verification or a performance result.

## Independent generation/assembly audit

Twenty case sets (four variants × smoke/functional/three performance datasets) were generated into `variants/jade/review/generated-linked-01`, assembled and linked with the common RISC-V tools, and traversed using the offline checker. All passed:

- Across variants, the same plan, input registers, full128 expected register states, stream outputs, operation counts, and case ordering are generated.
- The RVV baseline's compiled instruction words and addresses are identical across all four variants when linked at the same text base.
- Each custom measurement window contains exactly the expected number of its own native custom instruction.
- Shared stream storage is enabled in campaign builds; paired methods use the same aligned stream address.

Evidence and reviewed source hashes: `jade-harness-review.json`.

One initial audit attempt fed relocatable `.o` files to the linked-ELF checker and was rejected on alignment; the corrected audit links first, as the actual campaign does. This did not require a harness change.

## Fairness assessment

The primary common task is exactly eight signed byte products reduced to a signed32 result with the other 96 result bits cleared. The RVV baseline explicitly clears the full destination before widened reduction. Redoop implements a different native lane-accumulating ISA; its adapter zeroes accumulators, computes lane partial sums, reduces the two required lanes, clears the complete destination, and restores e8 configuration inside the measured window. Its extra work is deliberately charged to the common task; this is an adapter comparison, not a native-instruction ranking.

Measured repeats are balanced: repeat 0 is first-use, repeat 1 is warm-up, and repeats 2..5 alternate custom-first/RVV-first evenly. Inputs are fixed across implementations. Fence/counter boundaries and UART state checks are shared. The checker binds snapshots, generated data and linked ELF to receipts, verifies actual retired PCs/words and counter identities, requires fences around sampling, reconciles CSR cycles with global-clock deltas and retirement instruction counts, and requires live DiffTest plus one GOOD TRAP.

`single` includes the common barrier overhead and is not FU latency. `chain` and four-way `batch` show dependency and independent-operation behavior. `stream` includes common whole-register loads/stores. None establishes post-synthesis frequency or area.

## Finding

`campaign.py --stream-only` still filters performance shard IDs `(7,8,9)`, inherited from an older 10-shard layout. The current suite has only four performance shards `0..3`; thus this flag silently produces no images. Normal all-images build is unaffected. Suggested fix: select shard `3` (current stream case), or derive selection from the generated scenario rather than hardcoded IDs. Reported to root; this reviewer did not edit shared harness files.
