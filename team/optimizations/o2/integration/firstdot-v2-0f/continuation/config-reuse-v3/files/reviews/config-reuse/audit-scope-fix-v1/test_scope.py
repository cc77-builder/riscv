import importlib.util,json,sys,unittest
from pathlib import Path
W=Path("/home/riscv/riscv-lab/software-import-20261026")
D=W/"reviews/config-reuse"
sys.path.insert(0,str(D/"adapter-v3"))
import probe
sp=importlib.util.spec_from_file_location("fixed_audit_test",Path(__file__).with_name("raw_audit_fixed.py"))
audit=importlib.util.module_from_spec(sp);sp.loader.exec_module(audit)
class Scope(unittest.TestCase):
    def instance(self):
        return probe.Probe(W/"clean-02/checkout/source",W/"clean-02/identity/current.json",
                          W/"clean-02/matrix-build-01",W/"clean-02/matrix-run-01")
    def test_actual_complete_campaign_passes_unchanged_physical_identity(self):
        p=self.instance()
        result=audit.audit_probe(p,W/"config-reuse-clean02-02/build-01",W/"config-reuse-clean02-02/run-01")
        self.assertEqual(result["status"],"PROBE_LOCAL_RAW_AUDIT_PASS")
        self.assertEqual(result["normal_all_windows"],96)
        self.assertEqual(result["new_emu_runs"],0)
    def test_changed_final_physical_identity_still_rejected(self):
        p=self.instance();original=p.physical;calls=[0]
        def changed():
            value=original();calls[0]+=1
            if calls[0]>=2:
                value=(value[0],value[1],dict(value[2],deliberate_identity_fault=True))
            return value
        p.physical=changed
        with self.assertRaisesRegex(ValueError,"physical clean identity changed"):
            audit.audit_probe(p,W/"config-reuse-clean02-02/build-01",W/"config-reuse-clean02-02/run-01")
if __name__=="__main__":unittest.main()
