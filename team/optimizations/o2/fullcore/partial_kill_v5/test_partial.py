import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import check
import generate
import run


class DirectedTest(unittest.TestCase):
    def transcript(self):
        return ('The reference model is /reference.so\n'
                'The first instruction of core 0 has commited. Difftest enabled.\n'
                'PARTIAL_V5_BEGIN groups=1 trials=16\n'+
                ''.join(f'PARTIAL_V5_GROUP_PASS id={i} trials=16 register_bytes=8192 csr_fields=5\n' for i in range(1))+
                'PARTIAL_V5_SUMMARY groups=1 trials=16 register_bytes=8192 failures=0\n'
                'HIT GOOD TRAP\nSeed=1 Guest cycle spent: 123\n')

    def evaluate(self,text=None,manifest=None,windows=None):
        manifest=generate.corpus()[1] if manifest is None else manifest
        # Isolate the UART gate; real strict traces have their own regression and
        # are mandatory in the real runner. This fixture cannot qualify hardware.
        diagnosis={'counts':{'COMMIT':generate.corpus()[1]['expected_vdot_commits']},'windows':windows or []}
        raw=(self.transcript() if text is None else text).encode()
        with patch.object(check.diagnose_kills,'diagnose',return_value=diagnosis), \
             patch.object(check.diagnose_kills.analyze,'extract_events_and_uart',return_value=([],raw.decode())), \
             patch.object(check,'validate_layout',return_value=({'partial_old':256,'partial_young':272},{256:11,260:11,272:11})):
            return check.check(raw,0,manifest,'/reference.so','','')

    def test_functional_pass_does_not_close_missing_coverage(self):
        result=self.evaluate()
        self.assertTrue(result['architectural_pass']);self.assertFalse(result['target_covered'])
        self.assertFalse(result['campaign_acceptance'])

    def test_missing_duplicate_and_reordered_markers_rejected(self):
        text=self.transcript();row='PARTIAL_V5_GROUP_PASS id=0 trials=16 register_bytes=8192 csr_fields=5\n'
        for bad in (text.replace(row,''),text.replace(row,row+row),text.replace('id=0','id=1')):
            with self.assertRaises(ValueError):self.evaluate(bad)

    def test_wrong_manifest_and_reference_or_seed_rejected(self):
        manifest=copy.deepcopy(generate.corpus()[1]);manifest['expected_vdot_commits']-=1
        with self.assertRaises(ValueError):self.evaluate(manifest=manifest)
        for old,new in (('/reference.so','/wrong.so'),('Seed=1','Seed=2'),('HIT GOOD TRAP','HIT BAD TRAP')):
            with self.assertRaises(ValueError):self.evaluate(self.transcript().replace(old,new))

    def test_partial_requires_real_survivor_and_cancelled_victim(self):
        row=dict(classification='partial_kill',survivor_committed=True,victim_committed=False,
                 killp=1,p={'pc':'0x110'},r={'pc':'0x100'})
        self.assertTrue(self.evaluate(windows=[row])['target_covered'])
        for key,value in (('survivor_committed',False),('victim_committed',True)):
            with self.assertRaises(ValueError):self.evaluate(windows=[dict(row,**{key:value})])

    def test_unrelated_partial_is_not_the_shared_producer_target(self):
        row=dict(classification='partial_kill',survivor_committed=True,victim_committed=False,
                 killp=1,p={'pc':'0x110'},r={'pc':'0x110'})
        self.assertFalse(self.evaluate(windows=[row])['target_covered'])

    def test_full_width_goldens_include_sibling_result_and_both_branch_paths(self):
        initial,trials,expected=generate.inputs_and_expected()
        divided=initial[19][:]
        divided[:8]=[a//b if b else 255 for a,b in zip(initial[8][:8],initial[9][:8])]
        signed=lambda x:x if x<128 else x-256
        total=sum(signed(a)*signed(b) for a,b in zip(divided[:8],initial[9][:8])) & 0xffffffff
        dot=list(total.to_bytes(4,'little'))+[0]*12
        total2=sum(signed(a)*signed(b) for a,b in zip(dot[:8],initial[9][:8])) & 0xffffffff
        dot2=list(total2.to_bytes(4,'little'))+[0]*12
        low=signed(divided[0]) & ((1<<64)-1)
        self.assertEqual({t==low for t in trials},{True,False})
        for trial,registers in zip(trials,expected):
            want=[r[:] for r in initial]
            want[19]=divided[:];want[17]=dot[:];want[18]=dot2[:];want[16]=dot2[:]
            if trial==low:
                for r in range(20,28):want[r]=dot2[:]
            self.assertEqual(registers,want)

    def test_compiled_dependency_and_branch_target_are_required(self):
        symbols='\n'.join(f'{address:x} T {name}' for name,address in
                         [('partial_0',0x100),('partial_div',0x100),('partial_producer',0x104),('partial_sibling',0x108),
                          ('partial_old',0x10c),('partial_extract',0x110),('partial_branch',0x114),('partial_young',0x118),('partial_0_end',0x13c)])
        lines=['100: 8284a9d7 vdivu.vv v19,v8,v9',
               f'104: {generate.model.word(17,19,9):08x} .word',
               f'108: {generate.model.word(18,17,9):08x} .word',
               f'10c: {generate.model.word(16,17,9):08x} .word',
               '110: 433023d7 vmv.x.s t2,v19','114: 03c39263 bne t2,t3,138 <skip>']
        lines += [f'{0x118+4*i:x}: {generate.model.word(reg,17,9):08x} .word' for i,reg in enumerate(range(20,28))]
        disassembly='\n'.join(lines)+'\n'
        check.validate_layout(symbols,disassembly)
        for bad in (disassembly.replace('v19,v8,v9','v18,v8,v9'),
                    disassembly.replace('t2,v19','t2,v18'),disassembly.replace('03c39263','01c39263'),
                    disassembly.replace(f'{generate.model.word(18,17,9):08x}',f'{generate.model.word(18,19,9):08x}'),
                    disassembly.replace('03c39263','03c38263'),
                    disassembly.replace(f'{generate.model.word(16,17,9):08x}',f'{generate.model.word(16,8,9):08x}')):
            with self.assertRaises(ValueError):check.validate_layout(symbols,bad)

    def test_producer_cancellation_does_not_qualify_as_younger_victim(self):
        row=dict(classification='partial_kill',survivor_committed=True,victim_committed=False,
                 killp=1,p={'pc':'0x104'},r={'pc':'0x100'})
        self.assertFalse(self.evaluate(windows=[row])['target_covered'])

    def test_fresh_outputs_only_and_canonical_lf_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'new';generate.emit(out)
            files,manifest=generate.corpus()
            for name,text in files.items():self.assertEqual((out/name).read_bytes(),text.encode())
            with self.assertRaises(FileExistsError):generate.emit(out)
            with self.assertRaises(ValueError):run.check_output(out,[Path(temp)/'input'])
            with self.assertRaises(ValueError):run.check_output(Path(temp)/'inside',[Path(temp)])


if __name__=='__main__':unittest.main()
