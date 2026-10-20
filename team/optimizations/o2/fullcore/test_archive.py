"""Exercise the actual archive CLI in a separate optimized Python process."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ARCHIVE = Path(__file__).with_name("archive.py")


def digest(data):
    return hashlib.sha256(data).hexdigest()


class OptimizedArchiveTests(unittest.TestCase):
    def write_manifest(self, output, manifest):
        data = (json.dumps(manifest)+"\n").encode()
        (output/"archive-manifest.json").write_bytes(data)
        (output/"archive-manifest.sha256").write_text(digest(data)+"  archive-manifest.json\n")

    def fixture(self, output):
        payload=output/"files/runs/raw.log";payload.parent.mkdir(parents=True);payload.write_bytes(b"x")
        record=dict(stored="files/runs/raw.log",encoding="identity",raw_bytes=1,stored_bytes=1,
                    raw_sha256=digest(b"x"),stored_sha256=digest(b"x"))
        manifest=dict(version=1,files=[record]);self.write_manifest(output,manifest)
        return manifest

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable,"-OO",str(ARCHIVE),*map(str,arguments)],
                              capture_output=True,text=True)

    def test_optimized_verifier_rejects_path_hash_type_and_inventory_forgery(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/"archive";output.mkdir();manifest=self.fixture(output)
            self.assertEqual(self.run_cli("--output",output,"--verify-only").returncode,0)
            mutations=[lambda m:m.update(version=True),lambda m:m.update(files=[]),
                       lambda m:m["files"][0].update(stored_bytes=True),
                       lambda m:m["files"][0].update(raw_bytes=-1),
                       lambda m:m["files"][0].update(encoding="unknown"),
                       lambda m:m["files"][0].update(raw_sha256="f"*64),
                       lambda m:m["files"][0].update(stored_sha256="f"*64),
                       lambda m:m["files"].append(copy.deepcopy(m["files"][0]))]
            for name in ("/outside", "files/../outside", "files\\outside", "C:/outside", "files//runs/raw.log"):
                mutations.append(lambda m,name=name:m["files"][0].update(stored=name))
            for index,mutation in enumerate(mutations):
                bad=copy.deepcopy(manifest);mutation(bad);self.write_manifest(output,bad)
                with self.subTest(case=index):
                    result=self.run_cli("--output",output,"--verify-only")
                    self.assertNotEqual(result.returncode,0,result.stdout)
                    self.assertIn("ValueError",result.stderr)
            self.write_manifest(output,manifest)
            (output/"files/runs/extra.log").write_bytes(b"extra")
            self.assertNotEqual(self.run_cli("--output",output,"--verify-only").returncode,0)
            (output/"archive-manifest.sha256").write_text("0"*64+"  archive-manifest.json\n")
            self.assertNotEqual(self.run_cli("--output",output,"--verify-only").returncode,0)

    def test_export_preserves_shared_gate_source_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);work=root/"work";work.mkdir()
            (work/"raw.log").write_text("preserved bytes")
            if ARCHIVE.parent.name == "performance":
                for name,body in (("campaign-01/result.json",dict(status="O1_O2_PAIRED_PERFORMANCE_PASS",new_emu_jobs=36)),
                    ("results-01/verification.json",dict(status="OFFLINE_O1_O2_PAIRED_RECHECK_PASS",original_evidence_unchanged=True)),
                    ("launch-state.json",dict(status="ALL_COMMANDS_FINISHED",stages=[dict(exit_code=0)]))):
                    path=work/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(body))
            output=root/"archive"
            result=self.run_cli("--output",output,"--work-root",work)
            self.assertEqual(result.returncode,0,result.stderr)
            names={r["stored"] for r in json.loads((output/"archive-manifest.json").read_text())["files"]}
            for name in ("team/optimizations/o1/build_inputs.py", "team/optimizations/o1/build_recipe.py",
                         "team/optimizations/o2/fullcore/live_inputs.py", "team/optimizations/o2/fullcore/archive_gate.py",
                         "team/scripts/prepare-core-baseline.py"):
                self.assertIn("files/tools/"+name,names)
            self.assertEqual(self.run_cli("--output",output,"--verify-only").returncode,0)

    def test_missing_metadata_and_nonexistent_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            result=self.run_cli("--output",root/"missing","--verify-only")
            self.assertNotEqual(result.returncode,0);self.assertIn("ValueError",result.stderr)
            result=self.run_cli("--output",root/"output","--work-root",root/"missing")
            self.assertNotEqual(result.returncode,0);self.assertFalse((root/"output").exists())


if __name__ == "__main__":unittest.main()
