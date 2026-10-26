"""New clean current-0f outer identity around frozen 14-process T17 fullcore checks."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import current_clean_common as c
import current_clean_profile as profile
import current_clean_identity as identity_api

HERE = Path(__file__).resolve().parent
CONTRACT = "zjh-current-clean-fullcore-v1"
PASS = "CURRENT_CLEAN_FULLCORE_PASS"
ORIGINAL_CONTROLLER_SHA = "593298f4119d5a8ce8dd925ec5836c70e0d8bf4cbcf7cf0b221570ffc669f1a2"

def configure(repo, identity):
    repo = Path(repo).resolve()
    repro = repo / "team/optimizations/o2/repro"
    original = repro / "clean_fullcore.py"
    c.require(c.sha(original) == ORIGINAL_CONTROLLER_SHA, "frozen fullcore controller drift")
    identity_api.validate_identity_value(repo, identity, physical=False)
    sys.path.insert(0, str(repro))
    sys.path.insert(0, str(HERE.parent))
    # Import already-qualified combination binding, but use its private runtime
    # instances only. No mutation of an upstream source or module global occurs.
    import combination
    spec = importlib.util.spec_from_file_location("current_private_clean_fullcore", original)
    fc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = fc
    spec.loader.exec_module(fc)
    old_ce = fc.ce
    ce = types.SimpleNamespace(**vars(old_ce))
    p = types.SimpleNamespace(**vars(profile))
    p.SOURCE = identity["source_commit"]
    p.BUILDER = c.sha(HERE / "current_clean_build.py")
    p.validate_metadata = lambda pins, state, before, baseline, generated, builder_sha, baseline_sha: \
        profile.validate_metadata(pins, state, before, baseline, generated,
                                  builder_sha, baseline_sha, identity["source_commit"])
    # ce.a is private so old clean_entry.a and historical T17 profiles stay intact.
    ce.a = types.SimpleNamespace(**vars(old_ce.a))
    # fixture_identity resolves its own module-global a.frozen_f.  A namespace
    # copy alone would retain the historical reference hash inside that function.
    evidence_path = repo / "team/optimizations/o2/r2-select/entry_evidence.py"
    c.require(c.sha(evidence_path) == old_ce.FROZEN["entry_evidence.py"],
              "frozen negative-fixture evidence checker drift")
    ce.evidence = profile.module("current_private_clean_entry_evidence", evidence_path)
    ce.evidence.a = ce.a
    ce.p = p
    def install(selected_repo, selected, physical):
        identity_api.validate_identity_value(selected_repo, selected, physical=physical)
        c.require(selected == identity, "fullcore selected identity differs")
        f, m = combination.runtime(selected_repo, selected)
        prior = m.checker_files
        def checkers(checkout):
            return prior(checkout) | identity_api.adapters() | {
                str(HERE / "current_clean_fullcore.py"): c.sha(HERE / "current_clean_fullcore.py"),
                str(original): ORIGINAL_CONTROLLER_SHA}
        m.checker_files = checkers
        ce.a.frozen_f, ce.a.frozen_m = f, m
    ce.install = install
    fc.ce, fc.p = ce, p
    fc.CONTRACT, fc.PASS = CONTRACT, PASS
    # Original code remains hash-pinned above; executed identity is this binding.
    fc.__file__ = str(HERE / "current_clean_fullcore.py")
    return fc

def main(args):
    repo = args.repo.resolve()
    identity_path = args.identity.resolve() if args.identity else args.run.resolve() / "identity.json"
    value = identity_api.validate_identity(repo, identity_path, physical=False)
    fc = configure(repo, value)
    c.require(1 <= args.jobs <= 4, "CPU budget")
    if os.name == "posix":
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    if args.action == "run":
        c.require(args.operation_id, "run requires unique operation id")
        result = fc.run(repo, identity_path, args.output.resolve(), args.operation_id, args.jobs)
    else:
        c.require(args.run, "audit requires completed campaign")
        result = fc.audit(repo, args.run.resolve(), args.output.resolve())
        # Preserve the delegated raw result; the new outer receipt states scope.
        c.save(args.output.resolve() / "current-clean-audit.json",
               dict(status="CURRENT_CLEAN_FULLCORE_RAW_AUDIT_PASS", contract=CONTRACT,
                    delegated_result_sha256=c.sha(args.output.resolve() / "results.json"),
                    outer_controller_sha256=c.sha(__file__),
                    frozen_controller_sha256=ORIGINAL_CONTROLLER_SHA,
                    new_emu_runs=0, source_new_emu_runs=14, historical_t17_acceptance=False))
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
    return result

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--action", choices=("run", "audit"), required=True)
    ap.add_argument("--identity", type=Path)
    ap.add_argument("--run", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--operation-id")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    c.require(args.identity or args.run, "identity or completed run required")
    main(args)
