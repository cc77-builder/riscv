import copy
import importlib.util
from pathlib import Path
import struct
import json
import gzip
import tempfile
import unittest
spec=importlib.util.spec_from_file_location("compare_reproduction",Path(__file__).with_name("compare_reproduction.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def result():
    records=[]
    for variant,shard,dataset in sorted(m.EXPECTED):
        for replay in ([0,1] if dataset==0 else [0]):
            samples=[]
            for seq in range(24):
                samples.append(dict(seq=seq,phase="first" if seq<4 else "warmup" if seq<8 else "measured",
                    method="vdot" if seq%2==0 else "rvv",software="basic" if seq%4<2 else "reuse",
                    repeat=seq//4,variant=variant,shard=shard,dataset=dataset,image_sha256="abc",
                    cycles=100+seq,instructions=50+seq,counter_values=[1,2,3,4],sample_ticks=[10,20,30,40]))
            records.append(dict(variant=variant,shard=shard,dataset=dataset,replay=replay,
                name=f"{variant}-{shard}-{dataset}",image_sha256="abc",status="R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS",samples=samples))
    return dict(status="CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS",contract=m.MATRIX_CONTRACT,runs=records)

class CompareTests(unittest.TestCase):
    def setUp(self):
        self.a=result();self.b=copy.deepcopy(self.a)
    def test_all_768(self):
        self.assertEqual(m.compare_windows(self.a,self.b)["compared_windows"],768)
    def test_order_does_not_hide_identity(self):
        self.b["runs"].reverse()
        for r in self.b["runs"]:r["samples"].reverse()
        m.compare_windows(self.a,self.b)
    def test_cycles_reject(self):
        self.b["runs"][0]["samples"][8]["cycles"]+=1
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_same_mean_permutation_reject(self):
        s=self.b["runs"][0]["samples"];s[8]["cycles"],s[12]["cycles"]=s[12]["cycles"],s[8]["cycles"]
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_first_window_reject(self):
        self.b["runs"][0]["samples"][0]["cycles"]+=1
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_replay_reject(self):
        self.b["runs"][1]["samples"][23]["cycles"]+=1
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_instruction_reject(self):
        self.b["runs"][0]["samples"][0]["instructions"]+=1
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_counter_reject(self):
        self.b["runs"][0]["samples"][0]["counter_values"][0]+=1
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_ticks_reject(self):
        self.b["runs"][0]["samples"][0]["sample_ticks"][0]+=1
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_missing_run_reject(self):
        self.b["runs"].pop()
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_duplicate_run_reject(self):
        self.b["runs"][1]=self.b["runs"][0]
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_duplicate_window_reject(self):
        self.b["runs"][0]["samples"][1]=self.b["runs"][0]["samples"][0]
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_cross_group_reject(self):
        self.b["runs"][0]["samples"][0]["dataset"]=2
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def test_partial_pass_reject(self):
        self.b["status"]="FIRSTDOT_PARTIAL_PASS"
        with self.assertRaises(ValueError):m.compare_windows(self.a,self.b)
    def elf(self,p,payload=b"CODE",debug=b"DEBUG"):
        data=bytearray(124)
        data[:6]=bytes.fromhex("7f454c460201")
        struct.pack_into("<HHIQQQIHHHHHH",data,16,2,243,1,0x80000000,64,0,0,64,56,1,0,0,0)
        struct.pack_into("<IIQQQQQQ",data,64,1,5,120,0x80000000,0x80000000,4,8,4)
        data[120:124]=payload
        p.write_bytes(data+debug)
    def test_debug_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a",Path(td)/"b";self.elf(a);self.elf(b,debug=b"OTHER")
            self.assertEqual(m.loads(a),m.loads(b))
    def test_load_change_detected(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a",Path(td)/"b";self.elf(a);self.elf(b,payload=b"FAIL")
            self.assertNotEqual(m.loads(a),m.loads(b))
    def test_truncated_elf_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"a";self.elf(p);p.write_bytes(p.read_bytes()[:121])
            with self.assertRaises(ValueError):m.loads(p)
    def test_empty_load_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"a";self.elf(p);data=bytearray(p.read_bytes());struct.pack_into("<I",data,64,0);p.write_bytes(data)
            with self.assertRaises(ValueError):m.loads(p)

class EvidenceTests(unittest.TestCase):
    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value))
    def audit(self,root):
        target=root/"input";target.write_text("input")
        files=[]
        for name in ("evidence-inputs.json","external-inputs.json"):
            p=root/name;self.write(p,{str(target):m.sha(target)})
            payload=root/"archive/payload"/(name+".gz");payload.parent.mkdir(parents=True,exist_ok=True)
            payload.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
            files.append(dict(logical="raw-audit/"+name,original=str(p),payload="payload/"+payload.name,
                raw_bytes=p.stat().st_size,raw_sha256=m.sha(p),stored_bytes=payload.stat().st_size,stored_sha256=m.sha(payload)))
        self.write(root/"archive/manifest.json",dict(contract=m.AUDIT_CONTRACT,files=files))
        self.write(root/"state.json",dict(status=m.AUDIT_PASS,contract=m.AUDIT_CONTRACT,original_emu_processes=36,
            formal_windows=384,c_normal_case_executions=96,archive=dict(manifest_sha256=m.sha(root/"archive/manifest.json"))))
        return target
    def test_sealed_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);target=self.audit(root);self.assertEqual(m.verify_audit(root),{str(target):m.sha(target)})
    def test_mapping_replacement_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.audit(root);self.write(root/"evidence-inputs.json",{})
            with self.assertRaises(ValueError):m.verify_audit(root)
    def test_sealed_payload_change_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.audit(root);next((root/"archive/payload").iterdir()).write_bytes(b"bad")
            with self.assertRaises(ValueError):m.verify_audit(root)
    def test_physical_input_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);target=self.audit(root);target.write_text("different")
            with self.assertRaises(ValueError):m.verify_audit(root)
    def test_manifest_replacement_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.audit(root);self.write(root/"archive/manifest.json",dict(files=[]))
            with self.assertRaises(ValueError):m.verify_audit(root)
    def c(self,root):
        build,run=root/"build",root/"run";build.mkdir();run.mkdir()
        cases=[dict(api_symbol=f"fn{i}",dataset=d,expected_hash=i*3+d) for i in range(16) for d in range(3)]
        self.write(build/"source/manifest.json",dict(cases=cases))
        (build/"vdot-perf.bin").write_bytes(b"program")
        self.write(run/"state.json",dict(status="R4_C_APPLICATION_CALLS_PASS",contract=m.C_CONTRACT,normal_case_executions=96))
        for label in ("recovery","replay"):
            validation=dict(status="R4_C_APPLICATION_DIFFTEST_PASS",case_count=48,public_functions=16,
                output_hashes=[c["expected_hash"] for c in cases],performance_measured=False)
            self.write(run/"runs"/label/"validation.json",validation)
            self.write(run/"runs"/label/"result.json",dict(status=validation["status"],validation=validation))
        return build,run,{str(p):m.sha(p) for p in root.rglob("*") if p.is_file()}
    def test_actual_96_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            b,r,a=self.c(Path(td));v=m.c_outputs(b,r,a)
            self.assertEqual(sum(len(x["output_hashes"]) for x in v["outputs"]),96)
    def test_c_unaudited_validation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            b,r,a=self.c(Path(td));a.pop(str(r/"runs/replay/validation.json"))
            with self.assertRaises(ValueError):m.c_outputs(b,r,a)
    def test_c_rehashed_wrong_output_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            b,r,a=self.c(Path(td));p=r/"runs/replay/validation.json";v=m.read(p);v["output_hashes"][0]+=1;self.write(p,v);a[str(p)]=m.sha(p)
            q=r/"runs/replay/result.json";self.write(q,dict(status=v["status"],validation=v));a[str(q)]=m.sha(q)
            with self.assertRaises(ValueError):m.c_outputs(b,r,a)

class ContinuationTests(unittest.TestCase):
    def resumed_matrix(self):
        value=result()
        value.update(status=m.RESUMED_MATRIX_PASS,contract=m.RESUMED_MATRIX_CONTRACT,
            underlying_contract=m.MATRIX_CONTRACT,historical_pass_reused=False,
            continuation=dict(new_emu_runs=21,inherited_started=13,inherited_qualified_processes=12,
                interrupted_runs=1,total_processes_started=34,qualified_processes=33))
        return value
    def resumed_audit(self,root):
        helper=EvidenceTests();target=helper.audit(root)
        manifest=m.read(root/"archive/manifest.json")
        manifest["contract"]=m.RESUMED_AUDIT_CONTRACT
        helper.write(root/"archive/manifest.json",manifest)
        state=m.read(root/"state.json")
        state.pop("original_emu_processes")
        state.update(status=m.RESUMED_AUDIT_PASS,contract=m.RESUMED_AUDIT_CONTRACT,
            qualified_processes=36,actual_launched_processes=38,interrupted_processes=2,
            continuation_new_emu_processes=23,inherited_launched_processes=15,
            new_emu_runs=0,new_nemu_runs=0,interrupted_results_counted_as_pass=False,
            archive=dict(manifest_sha256=m.sha(root/"archive/manifest.json")))
        helper.write(root/"state.json",state)
        return target
    def resumed_c(self,root):
        helper=EvidenceTests();b,r,a=helper.c(root)
        neg=root/"prior/runs/negative"
        helper.write(neg/"result.json",dict(status="EXPECTED_VDOT_HIGHBIT_REJECTION",negative=True))
        state=m.read(r/"state.json")
        state.update(status=m.RESUMED_C_PASS,contract=m.RESUMED_C_CONTRACT,
            new_emu_runs=2,total_launched_processes=4,interrupted_processes=1,logical_completed_processes=3,
            distinct_cases=48,public_functions=16,expected_negative_runs=1,normal_runs=2,
            performance_measured=False,record_locations={"negative":str(neg),"recovery":str(r/"runs/recovery"),
                "replay":str(r/"runs/replay")})
        helper.write(r/"state.json",state)
        a.update({str(p):m.sha(p) for p in root.rglob("*") if p.is_file()})
        return b,r,a
    def test_resumed_current_768_windows(self):
        self.assertEqual(m.compare_windows(self.resumed_matrix(),result())["compared_windows"],768)
    def test_resumed_clean_matrix_rejected(self):
        with self.assertRaises(ValueError):m.compare_windows(result(),self.resumed_matrix())
    def test_resumed_matrix_wrong_counts_rejected(self):
        for key in self.resumed_matrix()["continuation"]:
            with self.subTest(key=key):
                a=self.resumed_matrix();a["continuation"][key]+=1
                with self.assertRaises(ValueError):m.compare_windows(a,result())
    def test_resumed_matrix_boolean_count_rejected(self):
        a=self.resumed_matrix();a["continuation"]["interrupted_runs"]=True
        with self.assertRaises(ValueError):m.compare_windows(a,result())
    def test_resumed_matrix_wrong_contract_rejected(self):
        for key in ("contract","underlying_contract"):
            with self.subTest(key=key):
                a=self.resumed_matrix();a[key]="unknown-contract"
                with self.assertRaises(ValueError):m.compare_windows(a,result())
    def test_resumed_matrix_still_compares_counters(self):
        a=self.resumed_matrix();a["runs"][0]["samples"][0]["counter_values"][0]+=1
        with self.assertRaises(ValueError):m.compare_windows(a,result())
    def test_resumed_current_audit_seals(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);target=self.resumed_audit(root)
            self.assertEqual(m.verify_audit(root,allow_resumed=True),{str(target):m.sha(target)})
    def test_resumed_clean_audit_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.resumed_audit(root)
            with self.assertRaises(ValueError):m.verify_audit(root)
    def test_resumed_audit_wrong_counts_rejected(self):
        keys=("qualified_processes","actual_launched_processes","interrupted_processes",
              "continuation_new_emu_processes","inherited_launched_processes","new_emu_runs","new_nemu_runs")
        for key in keys:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td:
                root=Path(td);self.resumed_audit(root);s=m.read(root/"state.json");s[key]+=1
                EvidenceTests().write(root/"state.json",s)
                with self.assertRaises(ValueError):m.verify_audit(root,allow_resumed=True)
    def test_resumed_audit_wrong_contract_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.resumed_audit(root);s=m.read(root/"state.json");s["contract"]=m.AUDIT_CONTRACT
            EvidenceTests().write(root/"state.json",s)
            with self.assertRaises(ValueError):m.verify_audit(root,allow_resumed=True)
    def test_resumed_audit_cannot_count_interrupted_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.resumed_audit(root);s=m.read(root/"state.json");s["interrupted_results_counted_as_pass"]=True
            EvidenceTests().write(root/"state.json",s)
            with self.assertRaises(ValueError):m.verify_audit(root,allow_resumed=True)
    def test_resumed_archive_cannot_relabel_old_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.resumed_audit(root);v=m.read(root/"archive/manifest.json");v["contract"]=m.AUDIT_CONTRACT
            EvidenceTests().write(root/"archive/manifest.json",v)
            s=m.read(root/"state.json");s["archive"]["manifest_sha256"]=m.sha(root/"archive/manifest.json")
            EvidenceTests().write(root/"state.json",s)
            with self.assertRaises(ValueError):m.verify_audit(root,allow_resumed=True)
    def test_resumed_current_c_actual96(self):
        with tempfile.TemporaryDirectory() as td:
            b,r,a=self.resumed_c(Path(td));v=m.c_outputs(b,r,a,allow_resumed=True)
            self.assertEqual(sum(len(x["output_hashes"]) for x in v["outputs"]),96)
    def test_resumed_clean_c_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            b,r,a=self.resumed_c(Path(td))
            with self.assertRaises(ValueError):m.c_outputs(b,r,a)
    def test_resumed_c_wrong_counts_rejected(self):
        keys=("new_emu_runs","total_launched_processes","interrupted_processes","logical_completed_processes",
              "normal_case_executions","distinct_cases","public_functions","expected_negative_runs","normal_runs")
        for key in keys:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td:
                b,r,a=self.resumed_c(Path(td));p=r/"state.json";v=m.read(p);v[key]+=1
                EvidenceTests().write(p,v);a[str(p)]=m.sha(p)
                with self.assertRaises(ValueError):m.c_outputs(b,r,a,allow_resumed=True)
    def test_resumed_c_wrong_contract_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            b,r,a=self.resumed_c(Path(td));p=r/"state.json";v=m.read(p);v["contract"]=m.C_CONTRACT
            EvidenceTests().write(p,v);a[str(p)]=m.sha(p)
            with self.assertRaises(ValueError):m.c_outputs(b,r,a,allow_resumed=True)
    def test_resumed_c_negative_must_be_audited(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);b,r,a=self.resumed_c(root);a.pop(str(root/"prior/runs/negative/result.json"))
            with self.assertRaises(ValueError):m.c_outputs(b,r,a,allow_resumed=True)
    def test_resumed_c_normal_location_cannot_move(self):
        with tempfile.TemporaryDirectory() as td:
            b,r,a=self.resumed_c(Path(td));p=r/"state.json";v=m.read(p);v["record_locations"]["replay"]="/tmp/fake"
            EvidenceTests().write(p,v);a[str(p)]=m.sha(p)
            with self.assertRaises(ValueError):m.c_outputs(b,r,a,allow_resumed=True)





class LimitedChronologyTests(unittest.TestCase):
    # Fixture reuses physical pinned evidence; no target programs execute.
    actual = Path("/home/riscv/riscv-lab/software-import-20261026")
    def fixture(self,root):
        helper=EvidenceTests();ContinuationTests().resumed_audit(root)
        proof=dict(contract=m.CHRONOLOGY_CONTRACT,wall_clock_chronology="FAIL",causal_serial_order="PASS",
            clock_cause="UNCONFIRMED",ordering="frozen_controller_dispatch_sequence",
            monotonic_timestamps_recorded=False,timestamp_values_modified=False,records_reordered=False,
            new_emu_runs=0,anomalies=[dict(m.KNOWN_ANOMALY)])
        repo=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
        source=repo/"team/optimizations/o2/integration/firstdot-v2-0f/combination.py"
        receipt=self.actual/"combination-run-01.command.stdout.log"
        proof.update(source_files={str(source):m.sha(source)},receipt_files={str(receipt):m.sha(receipt)})
        inputs=dict(proof["source_files"],**proof["receipt_files"])
        for label in ("formal-performance-s1-d0-s01","formal-performance-s1-d1-s01"):
            file=self.actual/"combination-run-01/runs"/label/"result.json";inputs[str(file)]=m.sha(file)
        state=m.read(root/"state.json")
        state.update(status=m.LIMITED_AUDIT_PASS,contract=m.LIMITED_AUDIT_CONTRACT,
            functional_validation="PASS",target_cycle_validation="PASS",wall_clock_chronology="FAIL",causal_serial_order="PASS")
        helper.write(root/"external-inputs.json",inputs)
        helper.write(root/"chronology-proof.json",proof)
        helper.write(root/"state.json",state)
        self.reseal(root)
        return root
    def reseal(self,root):
        helper=EvidenceTests();files=[]
        for name in ("evidence-inputs.json","external-inputs.json","chronology-proof.json"):
            file=root/name;payload=root/"archive/payload"/(name+".gz")
            payload.write_bytes(gzip.compress(file.read_bytes(),mtime=0))
            files.append(dict(logical="raw-audit/"+name,original=str(file),payload="payload/"+payload.name,
                raw_sha256=m.sha(file),raw_bytes=file.stat().st_size,
                stored_sha256=m.sha(payload),stored_bytes=payload.stat().st_size))
        helper.write(root/"archive/manifest.json",dict(contract=m.LIMITED_AUDIT_CONTRACT,files=files))
        state=m.read(root/"state.json");state["archive"]["manifest_sha256"]=m.sha(root/"archive/manifest.json")
        state["chronology_proof_sha256"]=m.sha(root/"chronology-proof.json")
        helper.write(root/"state.json",state)
    def mutate_proof(self,root,fn):
        value=m.read(root/"chronology-proof.json");fn(value);EvidenceTests().write(root/"chronology-proof.json",value)
        self.reseal(root)
    def reject(self,root):
        with self.assertRaises(ValueError):m.verify_audit(root,allow_resumed=True)
    def test_limited_current_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));self.assertTrue(m.verify_audit(root,allow_resumed=True))
    def test_limited_clean_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td))
            with self.assertRaises(ValueError):m.verify_audit(root)
    def test_cannot_claim_wall_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));s=m.read(root/"state.json");s["wall_clock_chronology"]="PASS"
            EvidenceTests().write(root/"state.json",s);self.reject(root)
    def test_cannot_claim_clock_cause(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));self.mutate_proof(root,lambda p:p.update(clock_cause="PROVEN_WSL_SYNC"));self.reject(root)
    def test_cannot_claim_monotonic_timestamps(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));self.mutate_proof(root,lambda p:p.update(monotonic_timestamps_recorded=True));self.reject(root)
    def test_exact_anomaly_required(self):
        for key in m.KNOWN_ANOMALY:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td:
                root=self.fixture(Path(td))
                self.mutate_proof(root,lambda p:p["anomalies"][0].update({key:0 if key=="backward_microseconds" else "changed"}))
                self.reject(root)
    def test_cannot_add_anomaly(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));self.mutate_proof(root,lambda p:p["anomalies"].append(dict(m.KNOWN_ANOMALY)));self.reject(root)
    def test_cannot_detach_source_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));self.mutate_proof(root,lambda p:p.update(source_files={"/tmp/fake":"0"*64}));self.reject(root)
    def test_cannot_detach_anomalous_record(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));p=root/"external-inputs.json";values=m.read(p)
            values={k:v for k,v in values.items() if v!=m.KNOWN_ANOMALY["before_record_sha256"]}
            EvidenceTests().write(p,values);self.reseal(root);self.reject(root)
    def test_cannot_detach_proof_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));(root/"archive/payload/chronology-proof.json.gz").write_bytes(b"invalid");self.reject(root)
    def test_cannot_modify_or_reorder(self):
        for key in ("timestamp_values_modified","records_reordered"):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td:
                root=self.fixture(Path(td));self.mutate_proof(root,lambda p:p.update({key:True}));self.reject(root)

if __name__=="__main__":unittest.main()
