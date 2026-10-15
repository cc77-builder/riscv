"""Corpus partition tests; sharding never changes numeric expectations."""
import hashlib,json,tempfile,unittest
from collections import Counter
from pathlib import Path
from generate_vdot_cases import generate

class ShardTests(unittest.TestCase):
    def test_all_shards_exactly_cover_parent_and_keep_legal_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);parent=root/'parent';m=generate(parent,32,0x20261011)
            legal=[json.loads(x) for x in (parent/'cases.jsonl').read_text().splitlines()][:m['smoke_count']]
            exc=json.loads((parent/'exceptions.json').read_text())
            wanted={x['id']:x for x in legal+exc}
            plan=hashlib.sha256(json.dumps(dict(legal=legal,exceptions=exc),sort_keys=True,separators=(',',':')).encode()).hexdigest()
            observed=Counter()
            for i in range(4):
                folder=root/str(i);sub=generate(folder,32,0x20261011,32,'legacy',i,4)
                cases=[json.loads(x) for x in (folder/'cases.jsonl').read_text().splitlines()]
                exceptions=json.loads((folder/'exceptions.json').read_text())
                self.assertEqual(cases[0],legal[0]);self.assertTrue(exceptions)
                self.assertEqual(sub['shard']['parent_plan_sha256'],plan)
                self.assertEqual(len(cases),sub['smoke_count'])
                self.assertEqual(len(cases)+len(exceptions),30)
                for x in cases+exceptions:self.assertEqual(x,wanted[x['id']]);observed[x['id']]+=1
                dispatch=(folder/'stubs.h').read_text()
                for x in exceptions:self.assertIn('case 0x%08xU:'%x['word'],dispatch)
                for name,digest in sub['artifacts_sha256'].items():self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),digest)
            self.assertEqual(set(observed),set(wanted))
            self.assertEqual(len(observed),117)
            self.assertEqual(observed['D00'],4)
            self.assertTrue(all(n==1 for key,n in observed.items() if key!='D00'))
    def test_invalid_partition_parameters_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            for index,count in ((0,0),(4,4),(-1,4),(0,38)):
                with self.subTest(index=index,count=count),self.assertRaises(ValueError):
                    generate(Path(temp)/str(index),32,0x20261011,32,'legacy',index,count)
    def test_default_partition_preserves_normal_corpus(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);a=generate(p/'a',32,0x20261011);b=generate(p/'b',32,0x20261011,32,'legacy',0,1)
            self.assertEqual(a,b);self.assertNotIn('shard',a)
            self.assertEqual(a['smoke_count'],80);self.assertEqual(a['exception_count'],37)
if __name__=='__main__':unittest.main()
