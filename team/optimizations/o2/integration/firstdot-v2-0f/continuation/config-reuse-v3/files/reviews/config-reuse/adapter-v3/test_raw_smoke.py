"""Existing firstdot logs only: no config-reuse target execution."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys,tempfile,unittest
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPO=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
CAMPAIGN=Path("/home/riscv/riscv-lab/software-import-20261026/combination-run-01")
sys.path.insert(0,str(HERE))
import raw_audit as audit
sys.path.insert(0,str(REPO/"team/optimizations/o2/integration/firstdot-v2-0f"))
import combination
F,M=combination.runtime(REPO,combination.read(CAMPAIGN/"parent-identity.json"))
G=combination.g
CFG=combination.read(CAMPAIGN/"configuration.json")
COMMON=combination.read(CAMPAIGN/"runtime-inputs.json")
# V3 also verifies one comparison BIN at outer scope; the process map still
# matches the unchanged historical raw receipt after scoped selection.
comparison=Path(combination.read(CAMPAIGN/"runs/recovery-firstdot-8x32/result.json")["path"])/"vdot-perf.bin"
COMMON[str(comparison)]=audit.sha(comparison)


class ExistingFirstdotRaw(unittest.TestCase):
    def copy(self,negative=False):
        label="negative-firstdot-8x32" if negative else "recovery-firstdot-8x32"
        source=CAMPAIGN/"runs"/label
        temp=tempfile.TemporaryDirectory(prefix="config-raw-test-")
        self.addCleanup(temp.cleanup)
        target=Path(temp.name)/"run";target.mkdir()
        for name in ("result.json","stdout.log","stderr.log","windows.json","observation.json","negative.json"):
            if (source/name).exists():shutil.copyfile(source/name,target/name)
        record=combination.read(target/"result.json")
        image={k:record[k] for k in ("suite","shard","dataset","variant","name","path","image_sha256")}
        return source,target,image

    def verify(self,source,target,image,negative=False):
        fixture=combination.read(CAMPAIGN/"negative-fixture/fixture.json") if negative else None
        return audit.record_audit(REPO,G,F,M,CFG,image,target,COMMON,combination.CONTRACT,
                                  negative=negative,fixture=fixture,expected_cwd=source/"cwd")

    def change(self,target,file,key,value):
        row=combination.read(target/file);row[key]=value;G.save(target/file,row)

    def private_copy(self):
        source,target,image=self.copy()
        private=target/"cwd/build";private.mkdir(parents=True)
        for name in M.AUX:
            shutil.copyfile(source/"cwd/build"/name,private/name)
        record=combination.read(target/"result.json")
        old=str(source/"cwd");new=str(target/"cwd")
        record["cwd"]=new
        record["files"]={new+key[len(old):] if key.startswith(old+"/") else key:value
                         for key,value in record["files"].items()}
        G.save(target/"result.json",record)
        return target,image

    def test_actual_private_aux_copy_accepted(self):
        target,image=self.private_copy()
        value=self.verify(target,target,image)
        self.assertEqual(value["audit"]["windows"],24)

    def test_real_private_aux_tamper_rejected(self):
        target,image=self.private_copy()
        (target/"cwd/build"/next(iter(M.AUX))).write_bytes(b"tampered")
        with self.assertRaises(ValueError):self.verify(target,target,image)

    def test_real_private_aux_missing_rejected(self):
        target,image=self.private_copy()
        (target/"cwd/build"/next(iter(M.AUX))).unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):self.verify(target,target,image)

    def test_actual_firstdot_normal_raw24(self):
        source,target,image=self.copy()
        value=self.verify(source,target,image)
        self.assertEqual(value["audit"]["windows"],24)
        self.assertEqual(value["audit"]["new_emu_runs"],0)

    def test_actual_firstdot_negative_raw(self):
        source,target,image=self.copy(True)
        value=self.verify(source,target,image,True)
        self.assertTrue(value["audit"]["negative"])

    def test_cached_sample_cycle_rejected(self):
        source,target,image=self.copy()
        row=combination.read(target/"result.json");row["samples"][0]["cycles"]+=1;G.save(target/"result.json",row)
        with self.assertRaisesRegex(ValueError,"cached samples"):self.verify(source,target,image)

    def test_cached_window_cycle_rejected(self):
        source,target,image=self.copy()
        row=combination.read(target/"windows.json");row["samples"][0]["cycles"]+=1;G.save(target/"windows.json",row)
        with self.assertRaisesRegex(ValueError,"cached windows"):self.verify(source,target,image)

    def test_cached_o2_rejected(self):
        source,target,image=self.copy()
        row=combination.read(target/"observation.json");row["counts"]["COMMIT"]+=1;G.save(target/"observation.json",row)
        with self.assertRaisesRegex(ValueError,"cached O2"):self.verify(source,target,image)

    def test_nonzero_normal_exit_rejected(self):
        source,target,image=self.copy();self.change(target,"result.json","exit_code",1)
        with self.assertRaisesRegex(ValueError,"normal exit"):self.verify(source,target,image)

    def test_wrong_seed_rejected(self):
        source,target,image=self.copy()
        row=combination.read(target/"result.json");row["command"][-1]="--seed=2";G.save(target/"result.json",row)
        with self.assertRaisesRegex(ValueError,"command"):self.verify(source,target,image)

    def test_missing_input_binding_rejected(self):
        source,target,image=self.copy()
        row=combination.read(target/"result.json");row["files"].pop(next(iter(row["files"])));G.save(target/"result.json",row)
        with self.assertRaisesRegex(ValueError,"inventory"):self.verify(source,target,image)

    def test_wrong_destination_rejected(self):
        source,target,image=self.copy();self.change(target,"result.json","cwd","/tmp/unrelated")
        with self.assertRaisesRegex(ValueError,"destination"):self.verify(source,target,image)

    def test_timeout_rejected(self):
        source,target,image=self.copy();self.change(target,"result.json","timed_out",True)
        with self.assertRaisesRegex(ValueError,"incomplete"):self.verify(source,target,image)

    def test_truncated_raw_rehashed_still_rejected(self):
        source,target,image=self.copy()
        raw=(target/"stdout.log").read_bytes();(target/"stdout.log").write_bytes(raw[:len(raw)//2])
        row=combination.read(target/"result.json");row["raw_sha256"]["stdout.log"]=G.sha(target/"stdout.log")
        G.save(target/"result.json",row)
        with self.assertRaises(ValueError):self.verify(source,target,image)

    def test_false_negative_detail_rejected(self):
        source,target,image=self.copy(True)
        row=combination.read(target/"result.json");row["negative_details"]["bit"]=99;G.save(target/"result.json",row)
        with self.assertRaisesRegex(ValueError,"cached negative"):self.verify(source,target,image,True)

    def test_missing_raw_hash_rejected(self):
        source,target,image=self.copy()
        self.change(target,"result.json","raw_sha256",{})
        with self.assertRaisesRegex(ValueError,"digest"):self.verify(source,target,image)

    def test_bool_exit_rejected(self):
        source,target,image=self.copy();self.change(target,"result.json","exit_code",False)
        with self.assertRaisesRegex(ValueError,"incomplete"):self.verify(source,target,image)


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit("new result output required")
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExistingFirstdotRaw))
    report=dict(status="EXISTING_FIRSTDOT_RAW_AUDIT_TESTS_PASS" if result.wasSuccessful() else "FAIL",
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),
        new_emu_runs=0,config_reuse_executed=False,clean_runtime_qualification=False,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with args.output.open("x") as f:json.dump(report,f,indent=2);f.write("\n")
    if not result.wasSuccessful():raise SystemExit(1)
