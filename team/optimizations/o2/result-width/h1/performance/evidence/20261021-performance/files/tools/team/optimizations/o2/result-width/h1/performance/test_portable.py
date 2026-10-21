import copy
import tempfile
from pathlib import Path
import unittest
import portable

class PortableBindings(unittest.TestCase):
    def fixture(self):
        command=["timeout","120m","stdbuf","-o0","-e0","/emu","-i","/images/x/vdot-perf.bin",
                 "--flash=/flash","--ram-size=128MB","--diff=/ref","--max-cycles=2000000","--seed=1"]
        files={"/emu":"a"*64,"/images/x/vdot-perf.bin":"b"*64,
               "/flash":"a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994",
               "/ref":portable.NORMAL_REFERENCE}
        record=dict(command=command,files=files,image="x")
        return record,copy.deepcopy(record),dict(emu_path="/emu",emu_sha256="a"*64),files.copy(),{"x/vdot-perf.bin":dict(original="/images/x/vdot-perf.bin",sha256="b"*64)}

    def test_correct_binding_and_alien_image_or_reference_rejection(self):
        self.assertEqual(portable.validate_runtime_binding(*self.fixture()),"/ref")
        for change in ("image","reference","seed"):
            a,b,pins,artifacts,inputs=self.fixture()
            if change=="image":a["command"][7]="/images/other/vdot-perf.bin"
            if change=="reference":a["command"][10]="--diff=/alien"
            if change=="seed":a["command"][-1]="--seed=9"
            b=copy.deepcopy(a)
            with self.subTest(change=change),self.assertRaises(ValueError):
                portable.validate_runtime_binding(a,b,pins,artifacts,inputs)

    def test_relocated_emu_requires_explicit_identical_binary_binding(self):
        a,b,pins,artifacts,inputs=self.fixture()
        pins["emu_path"]="/original/build/emu"
        with self.assertRaises(ValueError):
            portable.validate_runtime_binding(a,b,pins,artifacts,inputs)
        self.assertEqual(portable.validate_runtime_binding(a,b,pins,artifacts,inputs,"/emu"),"/ref")
        with self.assertRaises(ValueError):
            portable.validate_runtime_binding(a,b,pins,artifacts,inputs,"/alien")
        pins["emu_sha256"]="c"*64
        with self.assertRaises(ValueError):
            portable.validate_runtime_binding(a,b,pins,artifacts,inputs,"/emu")

    def test_native_windows_path_object_preserves_original_linux_identity(self):
        from pathlib import PureWindowsPath, PurePosixPath
        value="/home/riscv/riscv-lab/preserved"
        for cls in (PureWindowsPath,PurePosixPath):
            self.assertEqual(portable.original_linux_emu_path(cls(value)),value+"/emu")

    def test_source_hash_must_match_frozen_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"team/tool.py";p.parent.mkdir();p.write_text("VALUE=1\n")
            artifacts={"/original/team/tool.py":portable.digest(p.read_bytes())}
            self.assertEqual(portable.load_source(root,"team/tool.py",artifacts,"portable_fixture").VALUE,1)
            p.write_text("VALUE=2\n")
            with self.assertRaises(ValueError):
                portable.load_source(root,"team/tool.py",artifacts,"portable_fixture_changed")

    def test_exact_inventory_rejects_duplicates_and_missing_jobs(self):
        modes=("b0","h1");names=["smoke"]+[str(i) for i in range(15)]
        names[-1]="performance-d0-s02"
        records=[dict(mode=m,image=n,replay=0) for m in modes for n in names]
        records += [dict(mode=m,image="performance-d0-s02",replay=q) for m in modes for q in (1,2)]
        portable.validate_inventory(records,modes,names)
        for bad in (records[:-1],records[:-1]+[records[0]]):
            with self.assertRaises(ValueError):portable.validate_inventory(bad,modes,names)

class CorpusSupport(unittest.TestCase):
    def fixture(self,root):
        import json,hashlib
        archive=root/"archive";archive.mkdir()
        files={}
        for i,rel in enumerate(sorted(portable.CORPUS_FILES)):
            raw=(f'{{"id":{i}}}\n').encode()
            p=archive/"support"/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            files[rel]=dict(bytes=len(raw),sha256=portable.digest(raw),
                           git_blob=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest())
        body=(json.dumps(dict(version=1,source_revision="a"*40,files=files))+"\n").encode()
        (archive/"support-manifest.json").write_bytes(body)
        (archive/"support-manifest.sha256").write_text(portable.digest(body)+"  support-manifest.json\n")
        return archive

    def test_restores_exact_functional_corpus(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);archive=self.fixture(root);tools=root/"tools"
            out=portable.load_corpus_support(archive,tools,"a"*40)
            self.assertEqual(out["files"],2)
            for rel in portable.CORPUS_FILES:
                self.assertEqual((tools/rel).read_bytes(),(archive/"support"/rel).read_bytes())

    def test_wrong_revision_or_changed_data_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);archive=self.fixture(root)
            with self.assertRaisesRegex(ValueError,"revision"):
                portable.load_corpus_support(archive,root/"tools","b"*40)
            p=archive/"support"/sorted(portable.CORPUS_FILES)[0];p.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"raw-byte"):
                portable.load_corpus_support(archive,root/"tools","a"*40)

    def test_missing_bundle_cannot_fall_back_to_local_models(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"missing frozen"):
                portable.load_corpus_support(Path(td),Path(td)/"tools","a"*40)

if __name__=="__main__":unittest.main()
