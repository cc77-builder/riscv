import copy
import unittest
import campaign as c

def fixture():
    records=[]
    for mode in ("o1","o2"):
        for shard in range(8):
            m,k=((4,8),(8,32),(16,64),(4,13))[shard//2]
            for d in range(3):
                samples=[]
                for repeat in range(2,6):
                    for software in ("basic","reuse"):
                        for method in ("vdot","rvv"):
                            cycles=100 if method=="vdot" else (200 if software=="basic" else 150)
                            if mode=="o2" and method=="vdot":cycles=80
                            samples.append(dict(mode=mode,shard=shard,software=software,method=method,
                                                dataset=d,repeat=repeat,phase="measured",cycles=cycles,instructions=20,
                                                image_sha256=f"{shard}-{d}",m=m,k=k,seq=len(samples),scope=("core","endtoend")[shard%2]))
                records.append(dict(mode=mode,suite="performance",replay=0,samples=samples))
    return records

class CampaignTests(unittest.TestCase):
    def test_all_samples_and_best_rvv(self):
        v=c.summarize(fixture())
        self.assertEqual(len(v["rows"]),16);self.assertEqual(len(v["measured_samples"]),768)
        self.assertAlmostEqual(v["rows"][0]["o2_vdot_cycle_reduction"],0.2)
        self.assertTrue(all(x["rvv_software"]=="reuse" for x in v["best_rvv_comparison"]))
    def test_missing_sample_rejected(self):
        v=fixture();v[0]["samples"].pop()
        with self.assertRaisesRegex(ValueError,"cardinality"):c.summarize(v)
    def test_duplicate_key_rejected(self):
        v=fixture();v[0]["samples"][4]=copy.deepcopy(v[0]["samples"][0])
        with self.assertRaises(ValueError):c.summarize(v)
    def test_retirement_drift_rejected(self):
        v=fixture();v[-1]["samples"][0]["instructions"]+=1
        with self.assertRaisesRegex(ValueError,"cross-mode"):c.summarize(v)
    def test_first_and_replay_not_measured(self):
        v=fixture()
        v.append(dict(suite="performance",replay=1,samples=[dict(phase="measured",cycles=1)]))
        v[0]["samples"].append(dict(phase="first",cycles=1))
        self.assertEqual(len(c.summarize(v)["measured_samples"]),768)
