# Current-source O2 G3 evidence — 2026-10-21

Final independently recomputed verdict: **O2_G3_OFFLINE_RECHECK_INCOMPLETE**.

- Hardware build: `0484f1feb25d0e8fa9fa281a643f1943eabc7bb5`; explicit `split-clang-v2`.
- EMU SHA-256: `b2b8f01324613f44f5c2ab9b1f4948f1bbe7db15457383d450608014d5c1ece9`.
- Explicit corrected gate/auditor commit: `2b6c5d6c1d29cc4a933f73853ce2ccbfc449f2fa`.
- Actual launches: 16, including two retained original supplements and two seed=1 supplements. Selected audit jobs: 14; one intentional bit100 rejection, remaining normal jobs pass. G3 complete: False; missing coverage: ['PARTIAL_KILL'].
- Original core verdict `O2_CORE_REGRESSION_FAILED` is preserved. Its sole failed job was the old gate's commit-group PC false rejection. No original log, result or launch ledger was rewritten.

Start with [selected audit](native/runs/recheck-03/result.json), [original core](native/runs/core-01/result.json), [seed=1 supplements](native/runs/supplements-02/result.json), and [deployment receipt](native/recheck-launch-03.json). Original supplements-01 and recheck-02 INCOMPLETE are retained. Seed runner commit: afe589bffc1fe98785784100187d45e953b421e9; shared core drivers remain byte-identical to the build revision.
The [derived summary](native/current-g3-summary.json) exposes exact counts and qualified coverage sources. [Build06](native/build-06/build-state.json) and attempts01–05 retain separate identities and failures.

`manifest.json` records payload hashes, sizes and original source paths. Selected prepared inputs are preserved in `native/prepared-inputs-v4.zip`; its previously verified hash is rechecked while sealing. Audit-bound inputs and evidence are rechecked before and after copies. The temporary swap cleanup receipt is included.

This is audit evidence and a selected-input archive, not a portable complete rebuild environment. EMU, all native tools and every hardware dependency are not bundled. Absolute-path strict replay still requires the prepared native workspace or a separately rebuilt contract. No new performance/PPA, independent T17 or human ACK claim. O1/O2 remain default-off in production.
