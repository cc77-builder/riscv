import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from oracle import Parameters, BASELINE, EXTENSION, pack, result, exact_sum, lanes
import generate


class ParameterOracleTests(unittest.TestCase):
    def test_hand_computed_extremes(self):
        p=EXTENSION
        self.assertEqual(p.limits,(-8589672448,8589934592))
        self.assertEqual(p.required_bits,35)
        self.assertEqual(exact_sum(pack([-32768]*8,p),pack([-32768]*8,p),p),8589934592)
        self.assertEqual(exact_sum(pack([-32768]*8,p),pack([32767]*8,p),p),-8589672448)
        self.assertEqual(result(pack([-32768]*8,p),pack([-32768]*8,p),p),0x200000000)

    def test_negative_field_and_upper_zero(self):
        actual=result(pack([-1]*8,EXTENSION),pack([1]*8,EXTENSION),EXTENSION)
        self.assertEqual(actual,0xfffffffffffffff8)
        self.assertEqual(actual>>64,0)

    def test_baseline_width(self):
        self.assertEqual(BASELINE.required_bits,19)
        self.assertEqual(BASELINE.limits,(-130048,131072))

    def test_reject_insufficient_result_fields(self):
        for bits in (0,16,32,33,34,129):
            with self.subTest(bits=bits),self.assertRaises(ValueError): Parameters(16,8,bits)

    def test_reject_bad_parameter_shapes(self):
        for args in [(8,0,32),(8,3,32),(8,32,32),(16,16,64),(7,8,32),(True,8,32),(8,8,32,64)]:
            with self.subTest(args=args),self.assertRaises(ValueError):Parameters(*args)

    def test_reject_bad_sources_and_lanes(self):
        for value in (-1,2**128,True,1.0):
            with self.subTest(value=value),self.assertRaises(ValueError):result(value,0,EXTENSION)
        for values in ([0]*7,[0]*9,[32768]*8,[-32769]*8,[True]*8):
            with self.subTest(values=values),self.assertRaises(ValueError):pack(values,EXTENSION)
        with self.assertRaises(ValueError):pack([0]*8,EXTENSION,1)

    def test_order_and_upper_half(self):
        p=EXTENSION
        self.assertEqual(lanes(0x00080007000600050004000300020001,p),tuple(range(1,9)))
        a=pack([0,0,0,0,1,2,3,4],p)
        self.assertEqual(result(a,a,p),30)
        a8=pack(range(8),BASELINE)
        self.assertEqual(result(a8,a8,BASELINE),result(a8|(0xffffffffffffffff<<64),a8,BASELINE))

    def test_corpus_against_independent_shift_decode(self):
        groups,_=generate.corpus()
        for name,rows in groups.items():
            p=generate.PROFILES[name];mask=(1<<p.element_bits)-1
            for row in rows:
                sums=0
                for i in range(p.pairs):
                    a=(int(row['vs1'],16)>>(p.element_bits*i))&mask
                    b=(int(row['vs2'],16)>>(p.element_bits*i))&mask
                    if a&(1<<(p.element_bits-1)):a-=1<<p.element_bits
                    if b&(1<<(p.element_bits-1)):b-=1<<p.element_bits
                    sums+=a*b
                self.assertEqual(sums,row['expected_sum'])
                self.assertEqual(sums&((1<<p.result_bits)-1),int(row['expected_vd'],16))
                self.assertEqual(exact_sum(int(row['vs2'],16),int(row['vs1'],16),p),sums)

    def test_boundary_detects_narrow_and_unsigned_mutants(self):
        p=EXTENSION;a=pack([-32768]*8,p);b=pack([32767]*8,p)
        correct=exact_sum(a,a,p)
        self.assertNotEqual(correct,correct&0xffffffff)
        narrowed=correct&((1<<34)-1)
        if narrowed&(1<<33):narrowed-=1<<34
        self.assertNotEqual(correct,narrowed)
        self.assertNotEqual(exact_sum(a,b,p),8*32768*32767)

    def test_generation_is_deterministic_and_tamper_rejected(self):
        first=generate.files();self.assertEqual(first,generate.files())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,data in first.items():(root/name).write_bytes(data)
            generate.check(root)
            (root/'s16x8.tsv').write_bytes(first['s16x8.tsv'][:-1])
            with self.assertRaises(ValueError):generate.check(root)

    def test_manifest_names_are_portable(self):
        _, originals = generate.corpus()
        self.assertEqual(set(originals), {
            "team/models/vdot/data/directed.jsonl",
            "team/models/vdot/data/random.jsonl",
        })
