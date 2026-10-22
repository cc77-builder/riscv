import unittest
import evidence_order as eo
class EvidenceOrderTests(unittest.TestCase):
    def samples(self):
        return [dict(mode="o1",shard=0,dataset=0,seq=i,cycles=100+i,instructions=20) for i in range(4)]
    def test_completion_order_does_not_change_samples(self):
        rows=self.samples();eo.require_same_measured(rows,list(reversed(rows)))
    def test_cycle_change_rejected(self):
        a=self.samples();b=self.samples();b[0]["cycles"]+=1
        with self.assertRaisesRegex(ValueError,"drift"):eo.require_same_measured(a,b)
    def test_missing_rejected(self):
        a=self.samples()
        with self.assertRaises(ValueError):eo.require_same_measured(a,a[:-1])
    def test_duplicate_rejected(self):
        a=self.samples()
        with self.assertRaisesRegex(ValueError,"duplicate"):eo.require_same_measured(a,a[:3]+[a[0]])
    def test_identity_change_rejected(self):
        a=self.samples();b=self.samples();b[0]["dataset"]=1
        with self.assertRaises(ValueError):eo.require_same_measured(a,b)
