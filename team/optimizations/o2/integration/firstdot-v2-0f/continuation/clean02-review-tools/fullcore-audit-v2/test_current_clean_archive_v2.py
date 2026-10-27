"""Focused host tests for new exact-case archive closure; never launches EMU."""
import ast
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode = True
import current_clean_archive_v2 as a

class CapacityArchiveTests(unittest.TestCase):
    def setUp(self):
        self.fixed = a.capacity_evidence()
        self.info = dict(contract=a.CONTRACT, campaign=str(a.SELECTED_RUN),
            source_root=str(a.SELECTED_REPO), clean_adapter=str(a.SELECTED_REPO / a.CLEAN_REL),
            capacity_source_sha256=a.CAPACITY_SOURCE_SHA, capacity_case_sha256=a.CAPACITY_CASE_SHA,
            source_result_sha256=self.fixed[str(a.SELECTED_RUN / "results.json")],
            identity_sha256=self.fixed[str(a.SELECTED_RUN / "identity.json")], **a.limited_flags())
        self.roles = {"capacity-evidence": dict(self.fixed)}
    def check(self):
        a.validate_capacity_archive(self.info, self.roles)
    def test_exact_closed_resource_evidence_accepts(self):
        self.check()
    def test_v1_contract_rejected(self):
        self.info["contract"]="zjh-current-clean-fullcore-archive-v1"
        with self.assertRaises(ValueError): self.check()
    def test_other_campaign_rejected(self):
        self.info["campaign"]=str(a.SELECTED_RUN)+"-other"
        with self.assertRaises(ValueError): self.check()
    def test_other_source_root_rejected(self):
        self.info["source_root"]="/some/other/checkout"
        with self.assertRaises(ValueError): self.check()
    def test_wall_clock_pass_claim_rejected(self):
        self.info["wall_clock_capacity"]="PASS"
        with self.assertRaises(ValueError): self.check()
    def test_unrecorded_os_measurement_claim_rejected(self):
        self.info["os_monotonic_capacity_measured"]=True
        with self.assertRaises(ValueError): self.check()
    def test_unknown_cause_cannot_be_claimed_known(self):
        self.info["clock_cause"]="NTP"
        with self.assertRaises(ValueError): self.check()
    def test_capacity_four_rejected(self):
        self.info["source_bound_max_workers"]=4
        with self.assertRaises(ValueError): self.check()
    def test_exception_tolerance_change_rejected(self):
        self.info["exact_anomaly_microseconds"]=80120
        with self.assertRaises(ValueError): self.check()
    def test_identity_substitution_rejected(self):
        self.info["identity_sha256"]="0"*64
        with self.assertRaises(ValueError): self.check()
    def test_source_result_substitution_rejected(self):
        self.info["source_result_sha256"]="0"*64
        with self.assertRaises(ValueError): self.check()
    def test_case_hash_substitution_rejected(self):
        self.info["capacity_case_sha256"]="0"*64
        with self.assertRaises(ValueError): self.check()
    def test_omitted_v1_failure_evidence_rejected(self):
        key=next(k for k in self.fixed if "fullcore-physical-01.command.stderr.log" in k)
        del self.roles["capacity-evidence"][key]
        with self.assertRaises(ValueError): self.check()
    def test_extra_capacity_evidence_rejected(self):
        self.roles["capacity-evidence"]["/not/an/input"]="0"*64
        with self.assertRaises(ValueError): self.check()
    def test_capacity_evidence_digest_substitution_rejected(self):
        key=next(iter(self.fixed))
        self.roles["capacity-evidence"][key]="0"*64
        with self.assertRaises(ValueError): self.check()

class UnchangedGateTests(unittest.TestCase):
    def test_raw_log_receipt_checks_unchanged_before_return(self):
        original=a.SELECTED_REPO / "team/optimizations/o2/integration/firstdot-v2-0f/clean-audit/current_clean_archive.py"
        old=ast.parse(original.read_text()); new=ast.parse(Path(a.__file__).read_text())
        def func(tree,name):return next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
        # All raw/exit/env/recovery predicates before the labelled return stay equal.
        self.assertEqual(ast.dump(ast.Module(body=func(old,"process_receipts").body[:-1],type_ignores=[])),
                         ast.dump(ast.Module(body=func(new,"process_receipts").body[:-1],type_ignores=[])))
        for name in ("outside","files_under","portable","pinned_source_link","live_match"):
            self.assertEqual(ast.dump(func(old,name)),ast.dump(func(new,name)))

if __name__=="__main__":unittest.main()
