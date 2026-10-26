"""Actual frozen receipt test plus isolated in-memory rejection checks; no EMU."""
from pathlib import Path
import copy
import importlib.util
import json
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
RUN = WORK / "combination-resume-01"
spec = importlib.util.spec_from_file_location("chronology", HERE/"chronology.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.locations=c.read(RUN/"run-locations.json")
        cls.labels=list(cls.locations)
        cls.records=[c.read(Path(cls.locations[n])/"result.json") for n in cls.labels]
        cls.proof, cls.inputs=c.verify(None,REPO,RUN,cls.labels,cls.records,cls.locations)
        (HERE/"chronology-proof.json").write_text(json.dumps(cls.proof,indent=2)+"\n")
        (HERE/"chronology-inputs.json").write_text(json.dumps(cls.inputs,indent=2)+"\n")
        cls.digests={**cls.inputs}
    def invoke(self, labels=None, records=None, locations=None):
        original=c.sha
        # Unit fault injection uses the already physically checked immutable map.
        def cached(p):
            key=str(p)
            return self.digests[key] if key in self.digests else original(p)
        with patch.object(c,"sha",side_effect=cached):
            return c.verify(None,REPO,RUN,self.labels if labels is None else labels,
                self.records if records is None else records,
                self.locations if locations is None else locations)
    def test_actual_limited_proof(self):
        self.assertEqual(self.proof["wall_clock_chronology"],"FAIL")
        self.assertEqual(self.proof["causal_serial_order"],"PASS")
        self.assertEqual(self.proof["anomalies"][0]["backward_microseconds"],543481)
    def test_reorder_rejected(self):
        labels=self.labels.copy();labels[3],labels[4]=labels[4],labels[3]
        with self.assertRaises(ValueError):self.invoke(labels=labels)
    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError):self.invoke(records=self.records[:-1])
    def test_changed_anomaly_time_rejected(self):
        records=copy.deepcopy(self.records);records[3]["finished"]="2026-10-26T07:07:55.796378+00:00"
        with self.assertRaises(ValueError):self.invoke(records=records)
    def test_changed_pid_rejected(self):
        records=copy.deepcopy(self.records);records[4]["pid"]+=1
        with self.assertRaises(ValueError):self.invoke(records=records)
    def test_changed_cwd_rejected(self):
        records=copy.deepcopy(self.records);records[4]["cwd"]="/different/cwd"
        with self.assertRaises(ValueError):self.invoke(records=records)
    def test_other_reversal_rejected(self):
        records=copy.deepcopy(self.records);records[5]["started"]=records[4]["started"]
        with self.assertRaises(ValueError):self.invoke(records=records)
    def test_nonzero_exit_rejected(self):
        records=copy.deepcopy(self.records);records[4]["exit_code"]=1
        with self.assertRaises(ValueError):self.invoke(records=records)
    def test_frozen_source_hash_rejected(self):
        original=c.sha
        source=str(REPO/next(iter(c.SOURCES)))
        with patch.object(c,"sha",side_effect=lambda p: "0"*64 if str(p)==source else original(p)):
            with self.assertRaises(ValueError):c.verify(None,REPO,RUN,self.labels,self.records,self.locations)
    def test_receipt_hash_rejected(self):
        original=c.sha
        target=str(WORK/"combination-run-01.command.stdout.log")
        with patch.object(c,"sha",side_effect=lambda p:"0"*64 if str(p)==target else original(p)):
            with self.assertRaises(ValueError):c.verify(None,REPO,RUN,self.labels,self.records,self.locations)

if __name__ == "__main__":
    unittest.main(verbosity=2)
