import hashlib
import itertools
import json
from pathlib import Path
import struct
import tempfile
import unittest
from dataclasses import replace

from vdot_model import MASK, NotVdot, VectorState, decode, dot_s8, encode, execute, result128
from generate_vdot_cases import DIRECTED, directed_cases, exception_cases, generate, jsonl, packed, random_cases


class ModelTests(unittest.TestCase):
    def test_documented_examples_and_precision(self):
        for name,a,b,total in DIRECTED:
            with self.subTest(name=name):
                self.assertEqual(dot_s8(a,b),total)
                self.assertEqual(result128(packed(a),packed(b)),total & 0xFFFFFFFF)
        self.assertEqual(result128(packed([-128]*8),packed([-128]*8)),131072)
        self.assertEqual(result128(packed([-1]*8),packed([1]*8)),0xFFFFFFF8)

    def test_all_single_lane_products(self):
        for a,b in itertools.product(range(-128,128),repeat=2):
            self.assertEqual(dot_s8([a]+[0]*7,[b]+[0]*7),a*b)

    def test_encoding_fields_and_rejections(self):
        for vd,vs1,vs2 in itertools.product(range(32),repeat=3):
            self.assertEqual(decode(encode(vd,vs1,vs2)),(vd,vs1,vs2))
        self.assertEqual(encode(10,9,8),0x0284850B)
        for bit in range(32):
            if MASK & (1<<bit):
                with self.assertRaises(NotVdot): decode(encode(10,8,9) ^ (1<<bit))
        for regs in ((32,0,0),(-1,0,0),(0,0,1.5)):
            with self.assertRaises(ValueError): encode(*regs)

    def test_random_independent_struct_oracle(self):
        for c in random_cases(10000):
            a,b = [int(c[k],16) for k in ('src1_128','src2_128')]
            # struct decoding and direct arithmetic are independent of model byte conversion.
            total = sum(x*y for x,y in zip(struct.unpack('<8b',a.to_bytes(16,'little')[:8]),
                                          struct.unpack('<8b',b.to_bytes(16,'little')[:8])))
            actual = result128(a,b)
            self.assertEqual(actual,total & 0xFFFFFFFF)
            self.assertEqual(actual >> 32,0)
            self.assertEqual(result128(b,a),actual)
            self.assertEqual(result128(a ^ (((1<<64)-1)<<64),b),actual)
            self.assertTrue(-130048 <= total <= 131072)

    def test_aliases_policies_and_preserved_state(self):
        for c in directed_cases():
            regs = list(range(32))
            regs[c['vd']] = int(c['old_vd_128'],16)
            regs[c['vs1']],regs[c['vs2']] = int(c['src1_128'],16),int(c['src2_128'],16)
            before = VectorState(regs=tuple(regs),**c['config'])
            out = execute(int(c['instruction'],16),before)
            self.assertIsNone(out.cause)
            expected = list(before.regs)
            expected[c['vd']] = int(c['expected_128'],16)
            self.assertEqual(out.state,replace(before,regs=tuple(expected),pc=before.pc+4,vs=3))

    def test_illegal_is_atomic_and_explained(self):
        base = VectorState(regs=tuple((1<<128)-i-1 for i in range(32)),vxrm=3,vxsat=1)
        variations = [(dict(vs=0),'VS_OFF'),(dict(vtype=8),'SEW'),(dict(vtype=1),'LMUL'),
                      (dict(vtype=7),'LMUL'),(dict(vtype=1<<63,vl=0),'VILL'),
                      (dict(vtype=0x100),'RESERVED_VTYPE')]
        variations += [(dict(vl=vl),'VL') for vl in (0,1,7,9,16)]
        variations += [(dict(vstart=v),'VSTART') for v in (1,7)]
        for fields,reason in variations:
            state = replace(base,**fields)
            for vd,vs1,vs2 in ((10,8,9),(8,8,9),(9,8,9),(0,0,0),(31,31,31)):
                out = execute(encode(vd,vs1,vs2),state)
                self.assertIs(out.state,state)
                self.assertEqual((out.cause,out.fault_pc),(2,state.pc))
                self.assertIn(reason,out.reasons)
        with self.assertRaises(NotVdot): execute(0x00000013,base)
        with self.assertRaises(ValueError): VectorState(vlen=256)

    def test_data_is_reproducible_and_fixture_current(self):
        self.assertEqual(Path(__file__).with_name('data').joinpath('vdot-directed.jsonl').read_bytes(),
                         jsonl(directed_cases()))
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            m = generate(Path(a),100,0x20261011)
            generate(Path(b),100,0x20261011)
            for name in ('cases.jsonl','cases.h','manifest.json','word-sites.S','stubs.h','exceptions.json'):
                self.assertEqual((Path(a)/name).read_bytes(),(Path(b)/name).read_bytes())
            self.assertEqual(hashlib.sha256((Path(a)/'cases.jsonl').read_bytes()).hexdigest(),m['cases_sha256'])
            self.assertEqual(m['total'],len(directed_cases())+100)
        self.assertEqual(len({c['id'] for c in directed_cases()}),len(directed_cases()))

    def test_exception_corpus_does_not_confuse_encoding_and_state(self):
        cases=exception_cases()
        self.assertEqual(len(cases),35)
        self.assertEqual(len({c['id'] for c in cases}),35)
        for c in cases:
            if c['model_class']=='not-vdot':
                self.assertEqual(c['word'] & 0x7F,0x0B)
                with self.assertRaises(NotVdot): decode(c['word'])
            else:
                type_value=1<<63 if c['vtype']==0x100 else c['vtype']
                state=VectorState(vtype=type_value,vl=0 if type_value>>63 else c['vl'],
                                  vstart=c['vstart'],vs=0 if c['vs_off'] else 1,
                                  vxrm=c['vxrm'],vxsat=c['vxsat'])
                self.assertEqual(execute(c['word'],state).cause,2)


if __name__ == '__main__':
    unittest.main()
