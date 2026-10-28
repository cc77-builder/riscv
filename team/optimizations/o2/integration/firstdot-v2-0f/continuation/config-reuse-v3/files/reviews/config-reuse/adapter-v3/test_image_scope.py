"""Image-role regression tests; no EMU. Includes unchanged real parser."""
from pathlib import Path
import copy,importlib.util,json,shutil,tempfile,unittest
import probe
W=Path("/home/riscv/riscv-lab/software-import-20261026")
REPO=W/"clean-02/checkout/source"
OLD=W/"config-reuse-clean02-01/run-01/runs/recovery-config-reuse"

class Scope(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)/"comparison"/"vdot-perf.bin"
        self.base.parent.mkdir();self.base.write_bytes(b"comparison")
        self.common={str(self.base):probe.sha(self.base),"/arbitrary/source.py":"abc"}
    def test_only_comparison_key_removed_other_inputs_unchanged(self):
        original=dict(self.common)
        self.assertEqual(probe.process_inputs(self.common),{"/arbitrary/source.py":"abc"})
        self.assertEqual(self.common,original)
    def test_missing_baseline_rejected(self):
        with self.assertRaisesRegex(ValueError,"exactly one"):probe.process_inputs({})
    def test_multiple_comparisons_rejected(self):
        with self.assertRaisesRegex(ValueError,"exactly one"):
            probe.process_inputs(self.common|{"/other/vdot-perf.bin":"abc"})
    def test_tampered_baseline_rejected(self):
        self.base.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"comparison BIN changed"):probe.process_inputs(self.common)
    def test_missing_baseline_bytes_rejected(self):
        self.base.unlink()
        with self.assertRaisesRegex(ValueError,"comparison BIN changed"):probe.process_inputs(self.common)
    def test_symlink_baseline_rejected(self):
        real=self.base.with_name("original");self.base.rename(real);self.base.symlink_to(real)
        with self.assertRaisesRegex(ValueError,"comparison BIN changed"):probe.process_inputs(self.common)
    def diagnostic(self,wrong=False,original=False):
        # Isolate upstream canonical module names from historical-root tests.
        import subprocess,sys
        mode="original" if original else "wrong" if wrong else "scoped"
        p=subprocess.run([sys.executable,"-B",str(Path(__file__).with_name("diagnostic_image_scope.py")),mode],
                         capture_output=True,text=True)
        if p.returncode:raise ValueError(p.stderr)
        return json.loads(p.stdout),None
    def test_original_two_bin_receipt_reproduces_failure(self):
        with self.assertRaisesRegex(ValueError,"loaded image mismatch"):self.diagnostic(original=True)
    def test_scoped_receipt_rechecks_all_24_real_windows(self):
        windows,observation=self.diagnostic()
        self.assertEqual(len(windows["samples"]),24)
    def test_wrong_loaded_image_still_rejected(self):
        with self.assertRaisesRegex(ValueError,"loaded image mismatch"):self.diagnostic(wrong=True)
if __name__=="__main__":unittest.main()
