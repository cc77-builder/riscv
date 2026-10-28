"""Grant combined C qualification after matrix and independent C raw audits."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def finalize(repo, identity, matrix, matrix_run, build, run):
    repo, identity, matrix, matrix_run, build, run = [
        Path(x).resolve() for x in (repo, identity, matrix, matrix_run, build, run)]
    leaf = repo / "team/optimizations/o2/integration/firstdot-v2-0f"
    sys.path.insert(0, str(leaf))
    sys.path.insert(0, str(leaf / "audit"))
    import combination as c
    import audit_combination as audit
    import orchestration_receipt as orchestration

    out = run / "combination-c-qualification.json"
    closure_out = run / "combination-c-orchestration-proof.json"
    c.g.require(not out.exists() and not closure_out.exists(), "qualification/proof already exists")
    matrix_proof = c.matrix_qualification(identity, matrix, matrix_run)
    binding = orchestration.validate_independent_receipt(c, repo, identity, matrix, build, run)
    value = c.parent_identity(repo, identity)
    base, adaptation = audit.private_c_auditor(c, repo, value)
    raw_proof = base.audit_run(repo, build, run)
    c.g.require(binding == orchestration.validate_independent_receipt(c, repo, identity, matrix, build, run),
                "independent C receipt changed during raw audit")
    proof = dict(
        status="CURRENT_FIRSTDOT_INDEPENDENT_C_FINALIZATION_PASS",
        binding=binding, raw_c_proof=raw_proof, matrix_proof=matrix_proof,
        private_c_audit_adapter=adaptation,
        finalizer_source_sha256=c.g.sha(__file__),
        audit_source_sha256=c.g.sha(audit.__file__),
    )
    qualification = dict(
        contract=c.CONTRACT, matrix_proof=matrix_proof, hardware_identity_sha256=c.g.sha(identity),
        historical_pass_reused=False, public_functions=16, distinct_cases=48,
        normal_case_executions=96, new_emu_runs=3, status="CURRENT_FIRSTDOT_C_APPLICATION_PASS")
    # Create the evidence first; the qualification is only visible after success.
    # Both paths are new, and reruns cannot silently replace a partial attempt.
    with closure_out.open("xb") as stream:
        stream.write(audit.encoded(proof))
    with out.open("xb") as stream:
        stream.write(audit.encoded(qualification))
    return qualification


if __name__ == "__main__":
    result = finalize(*sys.argv[1:])
    print(result["status"])
