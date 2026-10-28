"""Complete the unchanged RMSNorm v1 experiment under a separate resource budget.

Only the host deadline and total guest-cycle ceiling change. All workload,
negative control, ordering, numerical gates and performance rules remain v1.
The failed original campaign is never resumed or overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import signal
import sys

HERE = Path(__file__).resolve().parent
BASE_RUN_SHA256 = "77fe20c798bcd5025810f5e7f97efa171935fc37fc43fff39e44d6dd6293bb53"
BASE_CONTRACT_SHA256 = "7123410cbd1485999dfa4ec8922ddd136f417a2054019a51adfa02b3eb5ab86e"
RESOURCE_CONTRACT = "r2-s3-rmsnorm-output-v1-budget2"
GUEST_CYCLES = 6_000_000
HOST_SECONDS = 7_200


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_base():
    if sha(HERE / "run.py") != BASE_RUN_SHA256:
        raise ValueError("the original v1 runner bytes must be preserved")
    if sha(HERE / "CONTRACT.md") != BASE_CONTRACT_SHA256:
        raise ValueError("the original v1 contract bytes must be preserved")
    spec = importlib.util.spec_from_file_location("norm_budget_base", HERE / "run.py")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base.need((base.MAX_CYCLES, base.TIMEOUT) == (4_000_000, 3_600),
              "expected original resource ceilings")
    # These are the original runner's documented resource constants. They are
    # shared by launch and validation, so the two cannot use different ceilings.
    base.MAX_CYCLES = GUEST_CYCLES
    base.TIMEOUT = HOST_SECONDS
    return base


def run(args):
    base = load_base()
    output = args.output.resolve()
    profile_path = output.with_name(output.name + ".resource-contract.json")
    base.need(not output.exists() and not profile_path.exists(), "fresh budget2 output")
    profile = dict(
        resource_contract=RESOURCE_CONTRACT,
        validation_contract=base.b.CONTRACT,
        operation_id=args.operation_id,
        created_at=base.b.old.h.now(),
        original_runner_sha256=BASE_RUN_SHA256,
        original_contract_sha256=BASE_CONTRACT_SHA256,
        resource_contract_sha256=sha(HERE / "BUDGET-CONTRACT.md"),
        entry_sha256=sha(__file__),
        entry_path=str(Path(__file__).resolve()),
        resource_contract_path=str(HERE / "BUDGET-CONTRACT.md"),
        original_limits=dict(guest_cycles=4_000_000, host_seconds=3_600),
        limits=dict(guest_cycles=GUEST_CYCLES, host_seconds=HOST_SECONDS,
                    raw_file_bytes=512 * 1024 * 1024, concurrent_emu=args.cpu_count),
        arguments={k: str(getattr(args, k).resolve()) for k in ("identity", "build", "reference", "output")},
        workload_changed=False,
        runtime_log_profile_changed=False,
        numerical_or_performance_rules_changed=False,
        old_failed_campaign_reclassified=False,
        command=[sys.executable, *sys.argv],
    )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(profile_path, profile)
    profile_sha256 = sha(profile_path)
    try:
        result = base.run(args.identity.resolve(), args.build.resolve(), args.reference.resolve(),
                          output, args.cpu_count, args.operation_id)
        return result
    finally:
        base.need(sha(profile_path) == profile_sha256, "initial resource receipt unchanged")
        base.need(sha(HERE / "run.py") == BASE_RUN_SHA256, "original runner unchanged")
        base.need(sha(HERE / "CONTRACT.md") == BASE_CONTRACT_SHA256, "original contract unchanged")
        base.need(sha(__file__) == profile["entry_sha256"] and
                  sha(HERE / "BUDGET-CONTRACT.md") == profile["resource_contract_sha256"],
                  "resource profile source unchanged")
        if output.exists():
            base.save(output / "resource-contract.json", profile)
            state_path = output / "state.json"
            if state_path.exists():
                state = base.read(state_path)
                state.update(resource_contract=RESOURCE_CONTRACT,
                             validation_contract=base.b.CONTRACT,
                             resource_contract_sha256=profile_sha256)
                base.save(state_path, state)


if __name__ == "__main__":
    def interrupted(signum, frame):
        raise InterruptedError("norm budget2 signal " + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("identity", "build", "reference", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--cpu-count", type=int, choices=(1, 2), default=2)
    parser.add_argument("--operation-id", required=True)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({k: result[k] for k in
                      ("status", "started", "finished", "new_emu_runs", "performance_qualified")}, indent=2))
