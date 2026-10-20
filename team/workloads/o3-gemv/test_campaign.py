import copy
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import json
import gzip
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


def live_pair():
    common=dict(files={"src/a":"1"},dependency_files={"dep/a":"2"},config="MinimalConfig",
                NUM_CORES=1,EMU_THREADS=1,JVM_XMX="12G",BUILD_JOBS=2,source_commit="a"*40,
                native_build_contract=dict(schema=1,make_args=list(c.g4.build_recipe.MAKE_ARGS),
                    environment_sha256="a"*64,recipe_sha256="b"*64,
                    compilers={role:dict(path="/tools/"+role,sha256="c"*64,version="v1")
                               for role in ("cxx","cc","java","mill","verilator","firtool")}),
                VDOT_T14_FUSED_INPUT="1",VDOT_T12_TRACE="0",VDOT_T13_TRACE="1")
    return dict(o1=dict(copy.deepcopy(common),VDOT_O1_HANDOFF="1",VDOT_O2_ELASTIC="0",VDOT_O1_TRACE="1",VDOT_O2_TRACE="0",VDOT_O1_TRACE_PROFILE="events"),
                o2=dict(copy.deepcopy(common),VDOT_O1_HANDOFF="0",VDOT_O2_ELASTIC="1",VDOT_O1_TRACE="0",VDOT_O2_TRACE="1"))


class LiveInputTests(unittest.TestCase):
    def test_current_pair_requires_real_inventory_verifier(self):
        pins=live_pair()
        with patch.object(c.subprocess,"check_output",return_value="a"*40),patch.object(c.g4.live_inputs,"verify") as gate:
            c.verify_live(pins,"a"*40)
            gate.assert_called_once_with(c.ROOT,pins["o2"])
            gate.side_effect=ValueError("inventory drift")
            with self.assertRaisesRegex(ValueError,"inventory drift"):c.verify_live(pins,"a"*40)

    def test_changed_head_or_stale_build_rejected(self):
        for head,source in (("b"*40,"a"*40),("b"*40,"b"*40)):
            with self.subTest(head=head,source=source),patch.object(c.subprocess,"check_output",return_value=head),patch.object(c.g4.live_inputs,"verify") as gate:
                with self.assertRaises(ValueError):c.verify_live(live_pair(),source)
                gate.assert_not_called()

    def test_missing_native_contract_is_not_historical_fallback(self):
        pins=live_pair();pins["o1"].pop("native_build_contract")
        with patch.object(c.subprocess,"check_output",return_value="a"*40):
            with self.assertRaisesRegex(ValueError,"native build contract"):c.verify_live(pins,"a"*40)

    def calibration_fixture(self,root):
        # Copy actual frozen metadata only; this helper does not execute or
        # promote historical evidence to a current-source calibration.
        original=c.ROOT/"team/optimizations/o2/evidence/20261019-performance-ab/files/runs/campaign-01"
        def read(name):
            p=original/name
            return json.loads(p.read_bytes() if p.exists() else gzip.decompress(p.with_name(p.name+".gz").read_bytes()))
        state=read("state.json");(root/"state.json").write_text(json.dumps(state))
        pins={}
        for mode in ("o1","o2"):
            pins[mode]=read(mode+"-hardware-pins.json")
            (root/(mode+"-hardware-pins.json")).write_text(json.dumps(pins[mode]))
            target=root/mode/"smoke/smoke-d0-s00-r0/result.json";target.parent.mkdir(parents=True)
            target.write_text(json.dumps(read(mode+"/smoke/smoke-d0-s00-r0/result.json")))
        return pins,state["source_commit"]

    def test_calibration_exact_recorded_identity_metadata(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);pins,source=self.calibration_fixture(root)
            files,records=c.calibration_bindings(root,pins,source)
            self.assertEqual(len(files),5);self.assertEqual([x[0] for x in records],["o1","o2"])

    def test_calibration_stale_source_wrong_emu_and_partial_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);pins,source=self.calibration_fixture(root)
            with self.assertRaisesRegex(ValueError,"source mismatch"):c.calibration_bindings(root,pins,"f"*40)
            path=root/"o1/smoke/smoke-d0-s00-r0/result.json";original=json.loads(path.read_text())
            for mutate in (lambda r:r.update(status="RUNNING"),lambda r:r.update(exit_code=True),
                           lambda r:r["files"].update({pins["o1"]["emu_path"]:"f"*64})):
                row=copy.deepcopy(original);mutate(row);path.write_text(json.dumps(row))
                with self.assertRaises(ValueError):c.calibration_bindings(root,pins,source)
