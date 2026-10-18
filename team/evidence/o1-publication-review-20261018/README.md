# Publication and review evidence

Reviewed commit: `fb1e7bdc8e3f70f08764a62eb9d31ba0025c0e93`, diff base `e9c70db384ca71c494ef197aba598ed4bc08fa9b`. [Findings and scope](../../docs/o1-publication-review-20261018.md).

This is review evidence, not a repaired release or another CPU campaign. Four P2 gate defects remain open (three Standards, one Spec). The production RTL and previously sealed artifacts were not changed by this review. O1 remains disabled by default.

- `branches.json`: two successful fetches and ancestry counts for ten actual remote branches; none has unmerged commits. The initial Windows Schannel failure and successful command-scoped OpenSSL retry are disclosed.
- `remote-confirmed.json`: successful final Windows/OpenSSL remote query. Only the requested James_Hotten checkpoint was published; main remains unchanged. `remote-readback.json` preserves a preceding WSL query terminated after it stalled; that failed attempt is not treated as confirmation.
- `tests.json` and seven `.log` files: actual commands, exit codes, log hashes and counts for 487 successful host checks under Python 3.12, `-OO -B`. These checks did not detect the new reproductions.
- `standards-repro/`: actual reproduction receipts and helpers. The output-clobber case copies the real campaign before altering a log; the parent fault-reason case supplies a deliberately wrong synthetic error to the exact shell gate; the dependency case uses an isolated Git fixture with the real pinned yunsuan dependency. No project dependencies or frozen originals are altered. Initial temporary attempts were repeated in persistent project-cache directories; these are the saved repeated receipts.
- `publication-spec-ftq-redirect.*`: on eight real matrix transcripts, changing a self-flush FTQ index is still accepted. The additional self=0 control example illustrates unused fields but is not the defect's identity-equality oracle.
- `throughput.json` and `o1-review-throughput.py`: authenticated O1 batch raw-log analysis, accepted-request gaps and exact response-edge frames. Six windows, 762 adjacent pairs, 719 two-cycle pairs, 43 delayed pairs. This is zero new CPU executions and does not establish same-source T14/O1 speedup.
- `reviewed-inputs.json`: hashes of the source/checkers used by the audit at the fixed commit. Reproduction requires that checkout and the previously archived inputs; helpers retain the actual local cache paths used.
- `published-evidence-check.json`: all 19 files in the published O1 complete evidence inventory remain unchanged.
- `files.json`: SHA256 and byte size inventory of this review directory except the inventory itself.

Reproduction helpers are audit tools, not replacement acceptance gates. They deliberately construct invalid inputs and report that current gates accept them. Existing true hardware results remain bounded by their original source/profile/trace checks; the findings describe what reusable tools currently fail to reject. The next action is to repair these gates with targeted negative tests and recheck frozen inputs into new output directories.
