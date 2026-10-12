"""Synthetic parser unit fixtures; these are not emulator evidence."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from generate_vdot_cases import generate

spec=importlib.util.spec_from_file_location('check_vdot_run',Path(__file__).resolve().parents[1]/'scripts/check-vdot-run.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def fixture():
    lines=['VDOT_BEGIN contract=vdot-s8x8-r32-v0.1 mode=selftest']
    for name,word in checker.SELFTEST.items():
        cause=0 if name=='H00-vadd-control' else 3
        off=name=='H02-VS-off'
        csrs=[1<<63 if name=='H04-vill' else 0,0 if name=='H04-vill' else 8,
              7 if name=='H03-vstart7' else 0,3,1,7]
        csr='/'.join(hex(x) for x in csrs)
        row=dict(id=name,result='PASS',instruction=hex(word),expected_cause=hex(cause),
                 actual_cause=hex(cause),trap_count=int(bool(cause)),fault_pc='0x80000000',
                 actual_epc='0x80000000' if cause else '0x0',resume_pc='0x80000004',mtval='0x0',
                 pre_mstatus='0x0' if off else '0x600',raw_mstatus='0x0' if off else '0x600',
                 pre_vd128='0x'+32*'f',expected_vd128='0x'+32*'f',post_vd128='0x'+32*'f',
                 pre_csr=csr,post_csr=csr,capture_phase=2 if off else 1,all32_checked=1,
                 guards_ok=1,protocol_errors='0x0')
        if not cause:
            row['expected_vd128']=row['post_vd128']='0x'+16*'f'+16*'0'
        lines.append('VDOT_CASE '+' '.join(f'{k}={v}' for k,v in row.items()))
    lines.extend(['HARNESS_NEGATIVE id=N01-wrong-pc result=TRAP_PROTOCOL protocol_errors=0x2',
                  'HARNESS_NEGATIVE id=N02-wrong-high-byte result=VECTOR_CHANGED',
                  'HARNESS_SELFTEST_PASS cases=5 negative_controls=2',
                  'VDOT_SUMMARY mode=selftest contract=vdot-s8x8-r32-v0.1 planned=5 executed=5 passed=5 failed=0 unreachable=0'])
    return '\n'.join(lines)


class LogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data=Path(self.temp.name)
        generate(self.data,32,0x20261011)

    def check(self,log,mode='selftest',rc=0,**kw):
        return checker.validate(log,mode,rc,self.data,**kw)

    def test_selftest_does_not_certify_vdot_or_difftest(self):
        result=self.check(fixture())
        self.assertFalse(result['extension_pass'])
        with self.assertRaises(ValueError): self.check(fixture(),mode='full')
        with self.assertRaises(ValueError): self.check(fixture(),require_diff=True)

    def test_rejects_incomplete_duplicate_and_unreachable(self):
        log=fixture()
        for bad in (log.replace('id=H04-vill','id=H03-vstart7'),
                    log.replace('planned=5','planned=4'),log.replace('unreachable=0','unreachable=1'),
                    log.replace('HARNESS_SELFTEST_PASS','REMOVED'),
                    log.replace('result=VECTOR_CHANGED','result=PASS')):
            with self.subTest(log=bad[-90:]), self.assertRaises(ValueError): self.check(bad)

    def test_rejects_forged_pass_with_wrong_state(self):
        log=fixture()
        for bad in (log.replace('actual_cause=0x3','actual_cause=0x2',1),
                    log.replace('actual_epc=0x80000000','actual_epc=0x80000004',1),
                    log.replace('expected_cause=0x3','expected_cause=0x2',1),
                    log.replace('all32_checked=1','all32_checked=0',1),
                    log.replace('capture_phase=2','capture_phase=1',1),
                    log.replace('post_vd128=0x'+32*'f','post_vd128=0x'+32*'0',1)):
            with self.assertRaises(ValueError): self.check(bad)
        with self.assertRaises(ValueError): self.check(log,rc=124)

    def test_generated_artifact_tampering_is_rejected(self):
        (self.data/'cases.h').write_text('stale generated expectations\n')
        with self.assertRaises(ValueError): self.check(fixture())

    def test_preservation_and_selftest_values_are_checked_independently(self):
        log=fixture()
        with self.assertRaises(ValueError):
            self.check(log.replace('expected_vd128=0x'+32*'f','expected_vd128=0x'+32*'0').replace(
                'post_vd128=0x'+32*'f','post_vd128=0x'+32*'0'))
        with self.assertRaises(ValueError):
            self.check(log.replace('0x'+16*'f'+16*'0','0x'+32*'f'))


if __name__=='__main__': unittest.main()
