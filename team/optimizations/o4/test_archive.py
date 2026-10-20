"""Archive acceptance remains fail-closed in separate optimized Python processes."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class ArchiveAcceptance(unittest.TestCase):
    def invoke(self, script, *arguments):
        return subprocess.run([sys.executable,"-OO",str(HERE/script),*map(str,arguments)],
                              capture_output=True,text=True)

    def fixture(self, root):
        evidence=root/"archive";files=evidence/"files";files.mkdir(parents=True)
        payload=files/"raw.log";payload.write_bytes(b"x")
        entry=dict(path="raw.log",stored="raw.log",gzip=False,bytes=1,stored_bytes=1,
                   sha256=digest(b"x"),stored_sha256=digest(b"x"))
        value=dict(format=1,entries=[entry]);self.write_manifest(evidence,value)
        return evidence,value

    def write_manifest(self, evidence, value):
        (evidence/"manifest.json").write_text(json.dumps(value))

    def test_manifest_path_type_hash_and_inventory_corruption_rejected_under_oo(self):
        with tempfile.TemporaryDirectory() as temporary:
            evidence,value=self.fixture(Path(temporary))
            mutations=[lambda m:m.update(format=True),lambda m:m.update(entries=[]),
                lambda m:m["entries"][0].update(gzip=1),
                lambda m:m["entries"][0].update(bytes=True),
                lambda m:m["entries"][0].update(stored_bytes=True),
                lambda m:m["entries"][0].update(bytes=-1),
                lambda m:m["entries"][0].update(sha256="0"*64),
                lambda m:m["entries"][0].update(stored_sha256="0"*64),
                lambda m:m["entries"].append(copy.deepcopy(m["entries"][0]))]
            for key in ("path","stored"):
                for name in ("/outside","../outside","C:/outside","folder\\outside","a/../outside","a//b", "name.", "name ", "NUL", "aux.txt", "nested/COM1.txt"):
                    mutations.append(lambda m,key=key,name=name:m["entries"][0].update({key:name}))
            for index,mutate in enumerate(mutations):
                changed=copy.deepcopy(value);mutate(changed);self.write_manifest(evidence,changed)
                with self.subTest(case=index):
                    result=self.invoke("recheck.py",evidence)
                    self.assertNotEqual(result.returncode,0,result.stdout)
                    self.assertIn("ValueError",result.stderr)
            self.write_manifest(evidence,value)
            (evidence/"files/extra").write_text("unlisted")
            result=self.invoke("recheck.py",evidence)
            self.assertNotEqual(result.returncode,0);self.assertIn("unexpected archive payload",result.stderr)

    def test_duplicate_storage_and_parent_file_collision_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            evidence,value=self.fixture(Path(temporary))
            duplicate=copy.deepcopy(value["entries"][0]);duplicate["path"]="other.log"
            value["entries"].append(duplicate);self.write_manifest(evidence,value)
            result=self.invoke("recheck.py",evidence)
            self.assertIn("duplicate logical or stored",result.stderr)
            duplicate.update(path="raw.log/child",stored="raw.log/child")
            self.write_manifest(evidence,value)
            result=self.invoke("recheck.py",evidence)
            self.assertIn("conflicting restored",result.stderr)

    def test_casefold_path_collisions_rejected_before_restore(self):
        with tempfile.TemporaryDirectory() as temporary:
            evidence,value=self.fixture(Path(temporary))
            second=copy.deepcopy(value["entries"][0]);second.update(path="RAW.log",stored="RAW.log")
            value["entries"].append(second)
            (evidence/"files/RAW.log").write_bytes(b"x")
            self.write_manifest(evidence,value)
            result=self.invoke("recheck.py",evidence)
            self.assertIn("case-insensitive evidence path collision",result.stderr)

    def test_symlink_payload_and_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);evidence,value=self.fixture(root)
            outside=root/"outside";outside.write_bytes(b"x")
            payload=evidence/"files/raw.log";payload.unlink()
            try:payload.symlink_to(outside)
            except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
            result=self.invoke("recheck.py",evidence)
            self.assertIn("symlink",result.stderr)
            payload.unlink();payload.write_bytes(b"x")
            metadata=evidence/"manifest.json";copy=root/"manifest.json";copy.write_bytes(metadata.read_bytes())
            metadata.unlink();metadata.symlink_to(copy)
            self.assertIn("symlink",self.invoke("recheck.py",evidence).stderr)

    def test_valid_compressed_and_plain_bytes_restore_in_optimized_subprocess(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);evidence,value=self.fixture(root)
            raw=b"timing path\n"*100;payload=gzip.compress(raw,mtime=0)
            (evidence/"files/report.log.gz").write_bytes(payload)
            value["entries"].append(dict(path="report.log",stored="report.log.gz",gzip=True,
                bytes=len(raw),stored_bytes=len(payload),sha256=digest(raw),stored_sha256=digest(payload)))
            self.write_manifest(evidence,value)
            restored=root/"restored";restored.mkdir()
            code="import sys;sys.path.insert(0,sys.argv[1]);from archive_gate import restore;print(restore(sys.argv[2],sys.argv[3]))"
            result=subprocess.run([sys.executable,"-OO","-c",code,str(HERE),str(evidence),str(restored)],
                                   capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),"2")
            self.assertEqual((restored/"raw.log").read_bytes(),b"x")
            self.assertEqual((restored/"report.log").read_bytes(),raw)

    def test_seal_rejects_missing_incomplete_and_truthy_assessment_under_oo(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);work=root/"work";work.mkdir()
            for index,flag in enumerate((None,False,1,"true",[],{})):
                assessment=work/"assessment.json"
                if flag is not None:assessment.write_text(json.dumps(dict(audit_pass=flag)))
                output=root/f"bad-{index}"
                result=self.invoke("seal.py",work,output)
                self.assertNotEqual(result.returncode,0,result.stdout)
                self.assertIn("ValueError",result.stderr);self.assertFalse(output.exists())
            (work/"assessment.json").write_text(json.dumps(dict(audit_pass=True,selection={})))
            self.assertIn("incomplete assessment selection",self.invoke("seal.py",work,root/"partial").stderr)
            self.assertIn("outside source",self.invoke("seal.py",work,work/"nested").stderr)

    def test_pass_flag_alone_cannot_seal_fake_completed_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);work=root/"work";work.mkdir()
            selection={key:[key+"-map",key+"-sta"] for key in ("o1-fu","o2-fu","o1-parent","o2-parent")}
            for pair in selection.values():
                for name in pair:
                    directory=work/name;directory.mkdir();(directory/"placeholder").write_text("fake complete")
            (work/"assessment.json").write_text(json.dumps(dict(audit_pass=True,selection=selection)))
            result=self.invoke("seal.py",work,root/"output")
            self.assertNotEqual(result.returncode,0,result.stdout)
            self.assertNotIn("O4_SEALED_RECHECK_PASS",result.stdout)


if __name__ == "__main__":unittest.main()
