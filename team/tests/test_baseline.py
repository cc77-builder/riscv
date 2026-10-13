"""Scratch allocation invariants and evidence rejection checks (not emulator evidence)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from generate_baseline import generate_baseline, scratch_registers

spec = importlib.util.spec_from_file_location('check_baseline_run', Path(__file__).resolve().parents[1]/'scripts/check-baseline-run.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class BaselineTests(unittest.TestCase):
    def test_scratch_all_register_combinations(self):
        for vd in range(32):
            for vs1 in range(32):
                for vs2 in range(32):
                    p, high, zero, reduced = scratch_registers(vd,vs1,vs2)
                    self.assertEqual(p % 2, 0)
                    self.assertEqual(high, p+1)
                    self.assertEqual(len({p,high,zero,reduced}), 4)
                    self.assertFalse({p,high,zero,reduced} & {vd,vs1,vs2,0})
                    self.assertTrue(all(0 <= r < 32 for r in (p,high,zero,reduced)))

    def test_incomplete_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            data = Path(d)
            generate_baseline(data,0,0)
            text = ('BASELINE_BEGIN contract=vdot-s8x8-r32-v0.1 baseline=rvv-vdot-s8x8-r32-v1\n'
                    'BASELINE_CONTROLS_PASS high96=detected preserved_register=detected csr=detected declared_scratch=allowed\n'
                    'BASELINE_SUMMARY contract=vdot-s8x8-r32-v0.1 baseline=rvv-vdot-s8x8-r32-v1 planned=48 executed=48 passed=48 failed=0\n')
            with self.assertRaisesRegex(ValueError, 'case IDs'):
                checker.validate(text,0,data)

    def test_full_log_rejects_wrong_state_masks_and_boundaries(self):
        with tempfile.TemporaryDirectory() as d:
            data=Path(d)
            baseline=generate_baseline(data,0,0)
            cases=[json.loads(line) for line in (data/'cases.jsonl').read_text().splitlines()]
            lines=['BASELINE_BEGIN contract=vdot-s8x8-r32-v0.1 baseline=rvv-vdot-s8x8-r32-v1',
                   'BASELINE_CONTROLS_PASS high96=detected preserved_register=detected csr=detected declared_scratch=allowed']
            for case in cases:
                c=case['config'];scratch=baseline['scratch_by_word'][case['instruction']]
                csr='/'.join(hex(v) for v in (c['vtype'],8,0,c['vxrm'],c['vxsat'],c['vxrm']*2+c['vxsat']))
                row=dict(id=case['id'],result='PASS',instruction=case['instruction'],scratch_mask=hex(sum(1<<v for v in scratch)),
                         pre_csr=csr,post_csr=csr,expected_vd128='0x'+case['expected_128'],post_vd128='0x'+case['expected_128'],
                         pre_mstatus=hex(c['vs']<<9),raw_mstatus='0x600',trap_count=0,protocol_errors='0x0',requested_vs=c['vs'],
                         pre32_checked=1,all32_except_scratch_checked=1,guards_ok=1,begin_pc='0x80000000',end_pc='0x80000034')
                lines.append('BASELINE_CASE '+' '.join(f'{k}={v}' for k,v in row.items()))
            n=len(cases)
            lines.append(f'BASELINE_SUMMARY contract=vdot-s8x8-r32-v0.1 baseline=rvv-vdot-s8x8-r32-v1 planned={n} executed={n} passed={n} failed=0')
            log='\n'.join(lines)
            self.assertEqual(checker.validate(log,0,data)['executed'],304)
            variants=[log.replace('post_vd128=0x'+32*'0','post_vd128=0x1',1),
                      log.replace('scratch_mask=0x1e','scratch_mask=0x0',1),
                      log.replace('pre_csr=0x0/0x8','pre_csr=0x0/0x7',1),
                      log.replace('raw_mstatus=0x600','raw_mstatus=0x200',1),
                      log.replace('pre32_checked=1','pre32_checked=0',1),
                      log.replace('end_pc=0x80000034','end_pc=0x80000030',1),
                      log.replace(f'planned={n}',f'planned={n-1}',1),log+'\n'+lines[2]]
            for bad in variants:
                with self.assertRaises(ValueError): checker.validate(bad,0,data)
            with self.assertRaises(ValueError): checker.validate(log,1,data)
            (data/'baseline-sites.S').write_text('tampered')
            with self.assertRaises(ValueError): checker.validate(log,0,data)

    def test_runtime_layouts_and_csr_cross_cover_multiple_paths(self):
        with tempfile.TemporaryDirectory() as d:
            result=generate_baseline(Path(d),1000,1000)
            data=json.loads((Path(d)/'manifest.json').read_text())
            self.assertEqual(result['planned'],1304)
            self.assertGreater(result['scratch_layout_count'],1)
            self.assertEqual(data['coverage']['operand_registers'],list(range(32)))
            self.assertEqual(data['coverage']['initial_vs'],[1,2,3])
            self.assertEqual(data['coverage']['policy_vxrm_vxsat_vs_count'],96)


if __name__ == '__main__':
    unittest.main()
