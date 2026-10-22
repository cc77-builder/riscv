"""Independently replay T12 sequences and verify every complete checkpoint."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

generator=load('t12_generator','team/workloads/vdot-regression/generate.py')
independent=load('t12_independent','team/tests/vdot_model.py')

def array(header,name):
    literal=re.search(r'\b'+name+r'(?:\[\d+\])+\s*=\s*(\{.*\});',header)[1]
    return json.loads(literal.replace('{','[').replace('}',']'))

class T12CorpusTests(unittest.TestCase):
    def test_all_register_checkpoints_with_independent_dot_oracle(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            out=Path(temporary);generator.emit(out)
            manifest=json.loads((out/'manifest.json').read_text());header=(out/'sequences.h').read_text()
            dots=0
            for group in manifest['groups']:
                n=group['id'];regs=array(header,f'input{n}');expected=array(header,f'expected{n}')
                checkpoints=dict(zip(group['checkpoints_after_operations'],expected))
                self.assertEqual(len(checkpoints),32)
                for step,op in enumerate(group['operations'],1):
                    kind=op['op']
                    if kind=='vdot':
                        a=int.from_bytes(bytes(regs[op['vs1']]),'little');b=int.from_bytes(bytes(regs[op['vs2']]),'little')
                        regs[op['vd']]=list(independent.result128(a,b).to_bytes(16,'little'));dots+=1
                    elif kind=='vadd':
                        regs[op['vd']][:8]=[(a+b)%256 for a,b in zip(regs[op['a']][:8],regs[op['b']][:8])]
                    elif kind=='vdivu':
                        regs[op['vd']][:8]=[a//b if b else 255 for a,b in zip(regs[op['a']][:8],regs[op['b']][:8])]
                    elif kind=='fdiv-s-vfmv': regs[28]=[0,0,96,64]*4
                    else: self.fail(kind)
                    if step in checkpoints:self.assertEqual(regs,checkpoints[step],(n,step))
            self.assertEqual(dots,2048)
    def test_deterministic_generation(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root=Path(temporary);generator.emit(root/'a');generator.emit(root/'b')
            for p in (root/'a').iterdir():self.assertEqual(p.read_bytes(),(root/'b'/p.name).read_bytes())
    def test_speculative_expected_complete_128_bits(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            out=Path(temporary);generator.emit(out);header=(out/'sequences.h').read_text()
            src=array(header,'spec_input');expected=array(header,'spec_expected')
            raw=re.search(r'spec_trials\[256\]\[3\] = (.*);',header)[1]
            raw=re.sub(r'UINT64_C\((\d+)\)',r'\1',raw)
            trials=json.loads(raw.replace('{','[').replace('}',']'))
            result=list(independent.result128(int.from_bytes(bytes(src[0]),'little'),int.from_bytes(bytes(src[1]),'little')).to_bytes(16,'little'))
            self.assertEqual(len(expected),256)
            for i,(n,d,q) in enumerate(trials):self.assertEqual(expected[i],result if n//d==q else src[2])

if __name__=='__main__':unittest.main()
