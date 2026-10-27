"""Host-only mutations of portable byte/trace receipts; never emulator tests."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import portable
import analyze

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def encoded(value):
    return (json.dumps(value,indent=2)+"\n").encode()

def empty_trace():
    return ("O2_SCHEMA version=1 clock=global latency=2 slots=2 rob_size=48 ftq_size=8 vlen=128 vpu_width=195 perf_width=577\n"
            "O2_STATE cycle=1 pvalid=0 pseq=0 prob=0:0 ppdest=0 rvalid=0 rseq=0 rrob=0:0 rpdest=0 occupancy=0 invalid=0 inready=0 vready=1 outvalid=0 outready=1 move=0 killp=0 killr=0 divactive=0 divseq=0 divoccupied=0 busy=0\n")

def fixture():
    files={}
    parser=(HERE/"analyze.py").read_bytes()
    gate=(ROOT/portable.RUNTIME_GATE).read_bytes()
    files["tools/"+portable.PARSER]=parser
    files["tools/"+portable.RUNTIME_GATE]=gate
    pins={"emu_sha256":"e"*64,"source_commit":"a"*40}
    pin_raw=encoded(pins)
    drivers={"/checkout/"+portable.PARSER:portable.digest(parser),
             "/checkout/"+portable.RUNTIME_GATE:portable.digest(gate)}
    for campaign,names in [("core",portable.CORE_JOBS),("supplements",portable.SUPPLEMENT_JOBS)]:
        preflight=dict(hardware_pins_sha256=portable.digest(pin_raw),emu_sha256="e"*64,
                       driver_files=drivers,input_files={"/normal.so":portable.NORMAL_REFERENCE,
                                                       "/negative.so":portable.NEGATIVE_REFERENCE})
        files["runs/"+campaign+"/preflight.json"]=encoded(preflight)
        files["runs/"+campaign+"/hardware-pins.json"]=pin_raw
        records=[]
        for name in sorted(names):
            negative=name=="negative-vdot"
            reference="/negative.so" if negative else "/normal.so"
            text="The reference model is "+reference+"\nThe first instruction of core 0 has commited. Difftest enabled.\n"+empty_trace()
            if negative:
                text+=("DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=10 pc=0x80000000 instruction=0x0294050b\n"
                       "v10_high different at pc = 0x80000000, right= 0x1000000000, wrong = 0x0\n"
                       "Core 0: ABORT at pc = 0x80000004\n")
            else:
                text+="HIT GOOD TRAP\n"
            # Exercise universal newline semantics while preserving raw stream hashes.
            stdout=text.replace("\n","\r\n").encode()
            stderr=b""
            raw=stderr+stdout
            obs=analyze.analyze(portable.text_view(raw),require_complete=not negative)
            prefix="runs/"+campaign+"/"+name
            command=["timeout","120m","stdbuf","-o0","-e0","/emu","-i","/image",
                     "--flash=/flash","--ram-size=128MB","--diff="+reference,"--max-cycles=5000000"]
            record=dict(name=name,status="SYNTHETIC_HOST_FIXTURE",command=command,
                        files={"/emu":"e"*64,reference:portable.NEGATIVE_REFERENCE if negative else portable.NORMAL_REFERENCE},
                        exit_code=1 if negative else 0,
                        raw_logs_sha256={k:portable.digest(v) for k,v in {"stdout.log":stdout,"stderr.log":stderr,"run.log":raw}.items()},
                        observation_status=obs["status"],observation_counts=obs["counts"])
            for key,value in {"stdout.log":stdout,"stderr.log":stderr,"run.log":raw,
                              "exit-code.txt":b"1\n" if negative else b"0\n",
                              "observation.json":encoded(obs),"result.json":encoded(record)}.items():
                files[prefix+"/"+key]=value
            records.append(record)
        files["runs/"+campaign+"/result.json"]=encoded(dict(runs=records))
    return files

def seal(root,files):
    root.mkdir()
    records=[]
    for i,(logical,raw) in enumerate(sorted(files.items())):
        compressed=i%2==0
        stored=gzip.compress(raw,mtime=0) if compressed else raw
        relative="files/"+logical+(".gz" if compressed else "")
        path=root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(stored)
        records.append(dict(original="/fixture/"+logical,stored=relative,
                            encoding="gzip" if compressed else "identity",
                            raw_bytes=len(raw),raw_sha256=portable.digest(raw),
                            stored_bytes=len(stored),stored_sha256=portable.digest(stored)))
    manifest=encoded(dict(version=1,files=records))
    (root/"archive-manifest.json").write_bytes(manifest)
    (root/"archive-manifest.sha256").write_text(portable.digest(manifest)+"  archive-manifest.json\n")
    return root

class PortableTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.files=fixture()

    def tearDown(self):
        self.temp.cleanup()

    def audit(self,files=None):
        archive=seal(self.root/"archive",self.files if files is None else files)
        return portable.audit(archive,"core","supplements")

    def test_all_fourteen_trace_scopes_and_crlf(self):
        result=self.audit()
        self.assertEqual(result["status"],"ARCHIVE_BYTES_AND_TRACE_AUDIT")
        self.assertEqual((result["jobs"],result["complete_traces"],result["partial_negative_traces"]),(14,13,1))
        self.assertFalse(result["new_emu_run"])
        self.assertFalse(result["architectural_workload_checks_repeated"])

    def test_stored_byte_mutation_rejected(self):
        archive=seal(self.root/"archive",self.files)
        target=next((archive/"files").rglob("*.gz"))
        target.write_bytes(target.read_bytes()+b"x")
        with self.assertRaisesRegex(ValueError,"stored-byte"):
            portable.Archive(archive)

    def test_manifest_raw_digest_mutation_rejected(self):
        archive=seal(self.root/"archive",self.files)
        manifest=json.loads((archive/"archive-manifest.json").read_text())
        manifest["files"][0]["raw_sha256"]="0"*64
        raw=encoded(manifest)
        (archive/"archive-manifest.json").write_bytes(raw)
        (archive/"archive-manifest.sha256").write_text(portable.digest(raw)+"  archive-manifest.json\n")
        with self.assertRaisesRegex(ValueError,"raw-byte"):
            portable.Archive(archive)

    def test_unsafe_windows_and_posix_paths_rejected(self):
        for name in ["../bad","/bad","C:/bad","C:bad","a\\b","files//x","files/./x"]:
            with self.subTest(name=name),self.assertRaises(ValueError):
                portable.safe_relative(name)

    def test_unexpected_file_rejected(self):
        archive=seal(self.root/"archive",self.files)
        (archive/"files/extra").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError,"unexpected"):
            portable.Archive(archive)

    def test_resealed_log_fails_original_receipt(self):
        self.files["runs/core/hello-vadd/run.log"]+=b"changed\n"
        with self.assertRaisesRegex(ValueError,"stream receipt"):
            self.audit()

    def test_cached_observation_count_mutation_rejected(self):
        key="runs/core/hello-vadd/observation.json"
        value=json.loads(self.files[key])
        value["counts"]["ACCEPT"]=1
        self.files[key]=encoded(value)
        with self.assertRaisesRegex(ValueError,"cached observation"):
            self.audit()

    def test_wrong_parser_pin_rejected(self):
        key="runs/core/preflight.json"
        value=json.loads(self.files[key])
        value["driver_files"]["/checkout/"+portable.PARSER]="0"*64
        self.files[key]=encoded(value)
        with self.assertRaisesRegex(ValueError,"checker not found"):
            self.audit()

    def test_missing_job_inventory_rejected(self):
        key="runs/core/result.json"
        value=json.loads(self.files[key])
        value["runs"].pop()
        self.files[key]=encoded(value)
        with self.assertRaisesRegex(ValueError,"inventory"):
            self.audit()

    def test_negative_wrong_exit_rejected(self):
        self.files["runs/core/negative-vdot/exit-code.txt"]=b"0\n"
        with self.assertRaisesRegex(ValueError,"exit-code"):
            self.audit()

    def test_gzip_and_identity_logical_collision_rejected(self):
        archive=seal(self.root/"archive",self.files)
        value=json.loads((archive/"archive-manifest.json").read_text())
        original=value["files"][0]
        if original["encoding"]=="gzip":
            duplicate=dict(original,stored=original["stored"][:-3],encoding="identity",
                           stored_bytes=original["raw_bytes"],stored_sha256=original["raw_sha256"])
            path=archive/duplicate["stored"]
            path.write_bytes(gzip.decompress((archive/original["stored"]).read_bytes()))
            value["files"].append(duplicate)
            raw=encoded(value)
            (archive/"archive-manifest.json").write_bytes(raw)
            (archive/"archive-manifest.sha256").write_text(portable.digest(raw)+"  archive-manifest.json\n")
            with self.assertRaisesRegex(ValueError,"duplicate decoded"):
                portable.Archive(archive)

if __name__=="__main__":
    unittest.main()
