import unittest
import recovery_check as rc
def fixture():
    old=[["o1",f"old-{i}",0] for i in range(46)]
    new=[["o2",f"new-{i}",0] for i in range(10)]
    proof=dict(imported_keys=old,pending_keys=new,imported_accepted_jobs=46,pending_jobs=10,incomplete_attempts=[{},{}],started_utc="2026-10-20T10:00:00+00:00")
    records=[dict(mode=m,image=i,replay=r,started_utc="2026-10-20T10:00:01+00:00") for m,i,r in old+new]
    return proof,records
class RecoveryBindingTests(unittest.TestCase):
    def test_valid_partition(self):
        proof,records=fixture();old,new,_=rc.partition(proof,records)
        self.assertEqual((len(old),len(new)),(46,10))
    def test_overlap_rejected(self):
        proof,records=fixture();proof["pending_keys"][0]=proof["imported_keys"][0]
        with self.assertRaises(ValueError):rc.partition(proof,records)
    def test_incomplete_record_not_hidden_as_new(self):
        proof,records=fixture();records[-1]["started_utc"]="2026-10-19T10:00:00+00:00"
        with self.assertRaisesRegex(ValueError,"incorrectly reused"):rc.partition(proof,records)
    def test_duplicates_rejected(self):
        proof,records=fixture();records[-1]=records[-2].copy()
        with self.assertRaises(ValueError):rc.partition(proof,records)
