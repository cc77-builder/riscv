import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict

import check_extended as extended
from check_parent_negative import check
from evidence_output import require_new_output, write_new_json
from test_trace import pair, line

HERE=Path(__file__).parent
CASES={'identity':'old identity','wen':'write class','high':'full128 shared/vec/v0 result',
       'cancel':'unsolicited or canceled vdot output'}


class OutputTests(unittest.TestCase):
    def test_all_cli_outputs_reject_existing_before_reading_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'raw.log';path.write_text('ORIGINAL\n')
            missing=Path(tmp)/'missing'
            commands=[['check_trace.py',str(path),'--mode','2','--scope','fullcore'],
                      ['audit_trace_negatives.py',str(path)],
                      ['recheck_extended_run.py','--run',str(missing)],
                      ['audit_extended_negatives.py','--control',str(path),'--calibration',str(path),'--build',str(missing)]]
            for script,*args in commands:
                with self.subTest(script=script):
                    p=subprocess.run([sys.executable,'-OO','-B',str(HERE/script),*args,'--output',str(path)],capture_output=True,text=True)
                    self.assertNotEqual(p.returncode,0)
                    self.assertIn('Use a new evidence output',p.stderr)
                    self.assertEqual(path.read_text(),'ORIGINAL\n')

    def test_exclusive_write_rejects_file_created_after_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'result.json';require_new_output(path)
            path.write_text('CONCURRENT OWNER')
            with self.assertRaises(FileExistsError):write_new_json(path,dict(status='PASS'))
            self.assertEqual(path.read_text(),'CONCURRENT OWNER')

    def test_hardlink_and_symlink_aliases_cannot_replace_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);original=folder/'input';original.write_text('ORIGINAL')
            hard=folder/'hard';os.link(original,hard)
            for path in (original,hard,folder):
                with self.assertRaises(FileExistsError):require_new_output(path)
                with self.assertRaises((FileExistsError,IsADirectoryError)):write_new_json(path,{})
            if os.name!='nt':
                for name,target in [('link',original),('dangling',folder/'absent')]:
                    path=folder/name;path.symlink_to(target)
                    with self.assertRaises(FileExistsError):require_new_output(path)
                    with self.assertRaises(FileExistsError):write_new_json(path,{})
                self.assertFalse((folder/'absent').exists())
            self.assertEqual(original.read_text(),'ORIGINAL')

    def test_fresh_trace_cli_output_still_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);log=folder/'raw.log';out=folder/'new.json'
            raw='\n'.join(line(t,r) for t,r in pair())+'\n';log.write_text(raw)
            p=subprocess.run([sys.executable,'-OO','-B',str(HERE/'check_trace.py'),str(log),
                              '--mode','2','--scope','fullcore','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('PASS',json.loads(out.read_text())['status'])
            self.assertEqual(log.read_text(),raw)


class ParentNegativeTests(unittest.TestCase):
    def test_all_intended_detections(self):
        for fault,reason in CASES.items():
            self.assertEqual(check(fault,1,f'PARENT_INJECT {fault}\nVFEX4_PARENT_FAIL tick=42 {reason}\n')['fault'],fault)

    def test_unrelated_duplicate_reversed_missing_and_wrong_exits(self):
        for fault,reason in CASES.items():
            inject=f'PARENT_INJECT {fault}\n';failure=f'VFEX4_PARENT_FAIL tick=42 {reason}\n'
            for text in (inject+'VFEX4_PARENT_FAIL tick=42 bounded divider progress\n',
                         failure+inject,inject+inject+failure,inject+failure+failure,
                         inject+failure+'VFEX4_PARENT_PASS mode=2\n',inject,failure,
                         inject+failure+'unrelated runtime error\n',inject+failure.replace('42','-1')):
                with self.assertRaises(ValueError):check(fault,1,text)
            for rc in (0,2,3,127,134,-9):
                with self.assertRaises(ValueError):check(fault,rc,inject+failure)
            for other in CASES:
                if other!=fault:
                    with self.assertRaises(ValueError):check(other,1,inject+failure)

    def test_observer_records_allowed_only_before_injection(self):
        prefix='\n'.join(line(t,r) for t,r in pair() if t.startswith('O1_EXU'))+'\n'
        text='PARENT_INJECT high\nVFEX4_PARENT_FAIL tick=42 full128 shared/vec/v0 result\n'
        check('high',1,prefix+text)
        with self.assertRaises(ValueError):check('high',1,text+prefix)
        with self.assertRaises(ValueError):check('high',1,'O1_EXU bogus=1\n'+text)

    def test_real_shell_entry_invokes_strict_checker(self):
        if os.name=='nt':self.skipTest('Bash runner requires Linux')
        source=(HERE/'check-parent.sh').read_text()
        start=source.index('  python3 -B team/optimizations/o1/check_parent_negative.py')
        gate=source[start:source.index('\ndone',start)]
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'inject-high.log'
            for reason,success in [('full128 shared/vec/v0 result',True),('bounded divider progress',False)]:
                log.write_text('PARENT_INJECT high\nVFEX4_PARENT_FAIL tick=42 '+reason+'\n')
                p=subprocess.run(['bash','-c',gate],cwd=HERE.resolve().parents[2],
                                 env=dict(os.environ,rc='1',out=tmp,fault='high'),capture_output=True)
                self.assertEqual(p.returncode==0,success,p.stderr)


class FTQRedirectTests(unittest.TestCase):
    def rows(self,self_flush=1):
        rows=defaultdict(list)
        enq=dict(cycle=10,slot=0,rf=0,rv=22,ftf=0,ftv=1,fto=8)
        redirect=dict(cycle=20,rf=0,rv=22,self=self_flush,ftf=0,ftv=1,fto=8)
        rows['O2_FTQ_ENQ']=[enq];rows['O2_FTQ_REDIRECT']=[redirect]
        if not self_flush:rows['O2_FTQ_COMMIT']=[dict(enq,cycle=30)]
        base=[]
        for tag,values in rows.items():
            for row in values:
                r={k:v for k,v in row.items() if not k.startswith('ft')}
                if tag!='O2_FTQ_REDIRECT':r.update(dest=10,pc=0x80001000,word=0x0294050b)
                base.append(line(tag.replace('O2_FTQ','O1_ROB'),r))
        return base,rows

    def test_self_flush_checks_all_three_identity_fields(self):
        base,rows=self.rows()
        self.assertEqual(extended.ftq_audit(base,rows),dict(allocated=1,squashed=1))
        for field in ('ftf','ftv','fto'):
            bad=copy.deepcopy(rows);bad['O2_FTQ_REDIRECT'][0][field]^=1
            with self.assertRaisesRegex(ValueError,'self-flush target identity'):
                extended.ftq_audit(base,bad)

    def test_nonself_replay_retains_distinct_ftq_origin(self):
        base,rows=self.rows(0)
        rows['O2_FTQ_REDIRECT'][0].update(ftf=1,ftv=6,fto=3)
        self.assertEqual(extended.ftq_audit(base,rows),dict(allocated=1,committed=1))


if __name__=='__main__':unittest.main()
