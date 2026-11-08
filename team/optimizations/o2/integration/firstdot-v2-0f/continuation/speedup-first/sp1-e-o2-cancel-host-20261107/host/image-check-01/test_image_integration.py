import json, importlib.util, struct, unittest
from pathlib import Path
from o2_cancel_fixtures import Fixture
from normal_adapter import collect_normal, expected_uart
from o2_cancel_selector import select
N=Path(__file__).resolve().parent.parent
C=json.loads((N/'host/PC_CONTRACT.json').read_text())
M=json.loads((N/'software/manifest.json').read_text())
p=N/'build-review/audit.py'
spec=importlib.util.spec_from_file_location('o2_cancel_object_audit',p);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)

class RealInputsFixture(Fixture):
    def request(self,rob,**kwargs):
        return super().request(rob,vs1=M['vs1_low64'],vs2=M['vs2_low64'],**kwargs)

def emit_call(f,seq,c):
    num=seq*3
    ptr=lambda k:f'{((num+k)//48)%2}:{(num+k)%48}'
    rows=[v for v in C['pc_roles'].values() if v['stage']==c['stage'] and v['phase']==c['phase']]
    rows.sort(key=lambda x:x['pc'])
    def enter(rob,row):
        f.enqueue(rob,pdest=5+row['vd'],vd=row['vd'])
        f.entries[rob]['pc']=row['pc']
        f.rows[-1]=f.rows[-1].split(' pc=')[0]+f" pc={hex(row['pc'])} ftq=0:1 word={hex(row['word'])}"
    enter(ptr(0),rows[0])
    if c['stage']=='prelude':f.tick(ptr(0));f.drain();return
    enter(ptr(2),rows[1]);f.tick(ptr(0));f.tick(ptr(2),ready=0 if c['stage']=='S0' or c['probe'] else 1)
    if c['probe']:f.tick(ready=1,flush=(ptr(1),0))
    f.drain()

def full_fixture():
    f=RealInputsFixture()
    for c in C['call_plan']:emit_call(f,c['seq'],c)
    return f.text()+'\n'.join(expected_uart(C))+'\nHIT GOOD TRAP\n'

class Integration(unittest.TestCase):
    def test_actual_image_full_pc_and_call_contract(self):
        r=collect_normal(full_fixture(),C,0,require_hit=True)
        self.assertEqual((r['custom_commits'],r['uart_calls']),(77,41))
        self.assertEqual(len(r['witnesses']['S0']),4);self.assertEqual(len(r['witnesses']['S1']),4)
        self.assertFalse(r['target_run_qualified'])
    def test_protocol_missing_duplicate_failure_and_wrong_exit(self):
        t=full_fixture()
        for bad in [t.replace('OC19_PASS seq=20\n',''),t.replace('OC19_PASS seq=20\n','OC19_PASS seq=20\nOC19_PASS seq=20\n'),t.replace('OC19_SUMMARY calls=41','OC19_SUMMARY calls=40'),t.replace('OC19_PASS seq=20','OC19_FAIL seq=20 error=2'),t.replace('HIT GOOD TRAP','HIT BAD TRAP')]:
            with self.assertRaises(ValueError):collect_normal(bad,C,0)
        with self.assertRaises(ValueError):collect_normal(t,C,1)
    def test_actual_object_abi_positive_and_callee_save_call_rejection(self):
        elf=Path(M['images']['elf']['path']).read_bytes()
        for f in M['functions']:
            raw=obj.elf_bytes(elf,f['start_pc'],f['end_pc']-f['start_pc'])
            words=list(struct.unpack('<'+'I'*(len(raw)//4),raw))
            self.assertEqual(obj.audit_kernel_words(words)['protected_writes'],0)
            badwords=[(1<<20)|(rd<<7)|0x13 for rd in [1,2,3,4,8,9,18,27]]+[(0x78<<25)|(5<<15)|(8<<7)|0x53,0xef,0xffffffff]
            for bad in badwords:
                corrupted=list(words);corrupted[0]=bad
                with self.assertRaises(ValueError):obj.audit_kernel_words(corrupted)
    def test_software_expected_bytes_independent_math(self):
        data=bytes.fromhex(M['input_bytes']);signed=lambda x:x-256 if x>127 else x
        result=sum(signed(data[i])*signed(data[16+i]) for i in range(8))&0xffffffff
        self.assertEqual((result.to_bytes(4,'little')+bytes(12)).hex(),M['expected_dot128'])
        self.assertEqual(len(M['expected_retired_pc_sequence']),77)

if __name__=='__main__':unittest.main(verbosity=2)
