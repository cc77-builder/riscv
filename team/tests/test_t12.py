"""T12 host checks and deliberately synthetic checker counterexamples."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from generate_t12 import generate, corpus, dot, general, batched, word

spec=importlib.util.spec_from_file_location('t12_checker',Path(__file__).resolve().parents[1]/'scripts/check-t12-run.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)

def fixture(data):
    m=json.loads((data/'manifest.json').read_text())
    rows={r['id']:r for r in json.loads((data/'cases.json').read_text())}
    lines=['Difftest enabled','T12_BEGIN contract=vdot-s8x8-r32-v0.1','T12_CONTROLS high96=1 preserved=1 csr=1']
    for entry in m['schedule']:
        r=rows[entry['id']];fault=r['fault_vl'] is not None;perf=r['kind']=='perf'
        cs=lambda v:'/'.join(hex(x) for x in v)
        dest='/'.join(f'{int.from_bytes(bytes.fromhex(r["expected"][i]),"little"):032x}' for i in range(10,14))
        kv=dict(id=r['id'],repeat=entry['repeat'],result='PASS',verdict=0,scratch=hex(sum(1<<i for i in r['scratch'])),
                pre32_checked=1,vectors_checked=1,csr_checked=1,guards=1,traps=int(fault),cause=2 if fault else 0,
                epc='0x80001000' if fault else '0x0',expected_pc='0x80001000' if fault else '0x0',tval='0x0',
                pre_csr=cs([0,8,0,3,1,7]),post_csr=cs([0,r['fault_vl'] if fault else 8,0,3,1,7]),
                recovered_csr=cs([0,8,0,3,1,7] if fault else [0]*6),recovered_status='0x600' if fault else '0x0',dests=dest,
                cycle_begin=100 if perf else 0,cycle_end=(200 if r['method']=='vdot' else 300) if perf else 0,
                instret_begin=100 if perf else 0,instret_end=100+checker.expected_instret(r) if perf else 0)
        lines += ['T12_CASE '+' '.join(f'{k}={v}' for k,v in kv.items())]
    lines += [f'T12_SUMMARY executed={len(m["schedule"])} failed=0','HIT GOOD TRAP']
    return '\n'.join(lines)

class T12Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.data=Path(self.tmp.name)/'data';generate(self.data)
        self.log=fixture(self.data)
    def tearDown(self):self.tmp.cleanup()
    def reject(self,log,code=0):
        with self.assertRaises(ValueError):checker.validate(log,code,self.data)
    def test_complete_synthetic_log_only(self):
        r=checker.validate(self.log,0,self.data)
        self.assertEqual(r['executed'],190);self.assertFalse(r['microarchitectural_observed'])
        self.assertEqual(len(r['metrics']),27)
    def test_missing_case(self):
        self.reject('\n'.join(x for x in self.log.splitlines() if not x.startswith('T12_CASE id=raw-alias ')))
    def test_failure_exit(self):self.reject(self.log,1)
    def test_missing_terminal_success(self):self.reject(self.log.replace('HIT GOOD TRAP',''))
    def test_wrong_fullwidth(self):
        line=next(x for x in self.log.splitlines() if x.startswith('T12_CASE '))
        row=checker.fields(line,'T12_CASE');v=row['dests'].split('/');v[0]='1'+v[0][1:]
        self.reject(self.log.replace('dests='+row['dests'],'dests='+'/'.join(v),1))
    def test_nonpositive_perf(self):self.reject(self.log.replace('cycle_end=200','cycle_end=100',1))
    def test_pair_count_mismatch(self):
        path=self.data/'cases.json';rows=json.loads(path.read_text())
        next(r for r in rows if r['id']=='perf-complete-rvv')['dots']+=1
        path.write_text(json.dumps(rows))
        mp=self.data/'manifest.json';m=json.loads(mp.read_text());m['files']['cases.json']=checker.digest(path);mp.write_text(json.dumps(m))
        self.reject(self.log)
    def test_pair_input_mismatch(self):
        path=self.data/'cases.json';rows=json.loads(path.read_text())
        next(r for r in rows if r['id']=='perf-complete-rvv')['before'][8]='00'*16
        path.write_text(json.dumps(rows))
        mp=self.data/'manifest.json';m=json.loads(mp.read_text());m['files']['cases.json']=checker.digest(path);mp.write_text(json.dumps(m))
        self.reject(self.log)
    def test_source_binary_mismatch(self):
        source='a'*40
        b=dict(source=source,arch='riscv64-xs',kind='t12',image='b'*64,manifest='c'*64)
        r=dict(source=source,parent=checker.PARENT,emu=checker.EMU,reference=checker.REFERENCE,flash=checker.FLASH,
               image='b'*64,manifest='c'*64,difftest=True,ram='128MB',pid=123,exit_code=0,
               started_at='2026-10-14T00:00:00+08:00',finished_at='2026-10-14T00:01:00+08:00')
        checker.validate_binding(source,b,r)
        for field,value in [('source','d'*40),('image','d'*64),('flash','d'*64),('exit_code',1),('difftest',False)]:
            bad=dict(r);bad[field]=value
            with self.assertRaises(ValueError):checker.validate_binding(source,b,bad)
    def test_csr_failure(self):self.reject(self.log.replace('post_csr=0x0/0x8','post_csr=0x0/0x7',1))
    def test_exception_recovery_failure(self):self.reject(self.log.replace('recovered_csr=0x0/0x8','recovered_csr=0x0/0x7',1))
    def test_changed_generated_assembly(self):
        (self.data/'t12-sites.S').write_text('changed');self.reject(self.log)
    def test_duplicate_case_and_completion(self):
        self.reject(self.log+'\n'+next(x for x in self.log.splitlines() if x.startswith('T12_CASE ')))
        self.reject(self.log+'\nHIT GOOD TRAP')
    def test_boundary_fullwidth_and_ignored_tail(self):
        self.assertEqual(int.from_bytes(dot(bytes([128]*16),bytes([128]*16)),'little'),131072)
        self.assertEqual(int.from_bytes(dot(bytes([128]*16),bytes([127]*16)),'little'),(-130048)&0xffffffff)
        for x in range(256):
            for y in range(256):
                a=bytes([x])+bytes(7)+bytes([255]*8);b=bytes([y])+bytes(7)+bytes([0xa5]*8)
                expected=int.from_bytes(bytes([x]),'little',signed=True)*int.from_bytes(bytes([y]),'little',signed=True)
                out=dot(a,b)
                self.assertEqual(int.from_bytes(out[:4],'little',signed=True),expected)
                self.assertEqual(out[4:],bytes(12))
    def test_generator_determinism_and_direct_adjacency(self):
        other=Path(self.tmp.name)/'other';generate(other)
        for p in self.data.iterdir():self.assertEqual(p.read_bytes(),(other/p.name).read_bytes())
        asm=(self.data/'t12-sites.S').read_text()
        self.assertIn('vsetvl zero, t1, t2\n  .word',asm)
        self.assertNotIn('printf',asm)
        self.assertEqual(sum(r['fault_vl'] is not None for r in corpus()),5)
    def test_lean_preserves_original_pairs_and_adds_dependency_window(self):
        original=corpus();lean=corpus('lean',True)
        self.assertEqual(len(lean),len(original)+3)
        for a,b in zip(original,lean):
            for key in ('id','before','expected','dots','fault_vl'):
                self.assertEqual(a[key],b[key])
        self.assertEqual((len(general(lean=True)),len(general(known=True,lean=True)),len(batched(lean=True))),(7,5,14))
        seq=general(lean=True)
        self.assertLess(next(i for i,s in enumerate(seq) if 'vwmul' in s),next(i for i,s in enumerate(seq) if 'vmv.v.i' in s))
        self.assertIn('  vsetivli zero, 8, e16, m1, tu, mu',seq)
        self.assertIn('  vwredsum.vs v10, v2, v10',seq)
        chain=next(r for r in lean if r['id']=='perf-dependency-chain-rvv')
        self.assertEqual(chain['dots'],64)
        self.assertIn('  vwmul.vv v2, v10, v9',chain['body'])
        self.assertEqual(chain['scratch'],[2,3])
    def test_scratch_collision_rejected(self):
        for args in (dict(a=2,lean=True),dict(vd=3,lean=True),dict(a=4),dict(b=5),dict(vd=32,lean=True)):
            with self.assertRaises(ValueError):general(**args)
    def test_optimized_baseline_not_narrow(self):
        for seq in (general(),general(known=True),batched()):
            self.assertTrue(any('vwmul.vv' in s for s in seq));self.assertTrue(any('vwredsum.vs' in s for s in seq))
            self.assertFalse(any('vredsum.vs ' in s for s in seq))
        self.assertLess(len(general(known=True)),len(general()))
        self.assertEqual(word(10,8,9),0x0294050b)

if __name__=='__main__':unittest.main()
