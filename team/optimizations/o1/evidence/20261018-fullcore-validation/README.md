# O1 fullcore validation evidence

This archive preserves the completed campaign and its strict offline recheck. The verification verdict comes from the [final recheck](files/runs/o1-fullcore-recheck-01/result.json). Packaging itself runs no emulator and does not create a new validation result.

| Job | Strict offline result |
| --- | --- |
| hello-vadd | HELLO_VADD_PASS |
| negative-vdot | EXPECTED_VDOT_HIGHBIT_REJECTION |
| functional-0 | VDOT_MATRIX_SHARD_PASS |
| functional-1 | VDOT_MATRIX_SHARD_PASS |
| functional-2 | VDOT_MATRIX_SHARD_PASS |
| functional-3 | VDOT_MATRIX_SHARD_PASS |
| functional-4 | VDOT_MATRIX_SHARD_PASS |
| functional-5 | VDOT_MATRIX_SHARD_PASS |
| functional-6 | VDOT_MATRIX_SHARD_PASS |
| functional-7 | VDOT_MATRIX_SHARD_PASS |
| control | O1_CONTROL_REGRESSION_PASS |
| dense-batch128 | O1_DENSE_HANDOFF_AND_WINDOWS_PASS |

- Original failed/aborted attempts, partial probes and the original gate defect remain verbatim.
- Only the final complete recheck establishes the whole-suite verdict; partial audits do not.
- Negative DiffTest intentionally exits 1; its trace remains a partial audit.
- Dense workload windows validate handoff and window integrity, not an A/B speedup claim.
- Derived run.log is stderr followed by stdout; it is not cross-stream chronological evidence.
- External integration patches are historical drafts; inclusion does not imply application.
- Final host checks and review are included as supplied; their own receipts retain their scope.

Every source path, original-byte SHA, stored-byte SHA and size is recorded in file-map.json. All .log/.stdout/.stderr files and text files at least 256 KiB use gzip with mtime=0; gzip is verified by decompression. Existing gzip files retain their original compressed bytes. excluded.json records excluded build products, binaries, objects, waveforms and caches. Original evidence files are not modified.
