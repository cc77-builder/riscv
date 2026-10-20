"""Current O3 adapter against frozen real image/log bytes; no EMU launch."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("o3_active_integration_checker",HERE/"check.py")
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
ARCHIVE=HERE/"evidence/20261020-application"


def extract(prefix, target):
    manifest=json.loads((ARCHIVE/"archive-manifest.json").read_text(encoding="utf-8"))
    prefix="files/runs/"+prefix+"/"
    for entry in manifest["files"]:
        if entry["stored"].startswith(prefix):
            raw=(ARCHIVE/entry["stored"]).read_bytes()
            if entry["encoding"]=="gzip":raw=gzip.decompress(raw)
            if hashlib.sha256(raw).hexdigest()!=entry["raw_sha256"]:raise ValueError("frozen fixture drift")
            name=entry["stored"][len(prefix):]
            if entry["encoding"]=="gzip":name=name[:-3]
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)


class IntegrationTests(unittest.TestCase):
    def test_all_frozen_images_regenerate_with_current_adapter(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);extract("images-02",root)
            images=sorted(p for p in root.iterdir() if p.is_dir())
            self.assertEqual(len(images),26)
            for image in images:
                with self.subTest(image=image.name):
                    manifest=json.loads((image/"data/manifest.json").read_text())
                    checker.verify_generation(image,manifest)
                    checker.base.verify_build_record(image)
                    checker.base.check_compiled_cases(image/"vdot-perf.elf",manifest)

    def test_real_smoke_transcript_with_strict_current_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);build=root/"image";run=root/"run"
            extract("images-02/smoke-d0-s00",build)
            extract("campaign-02/o1/smoke-d0-s00-r0",run)
            # Historical records stay frozen. Only this temporary fixture adds
            # explicit current-run topology metadata, and the old record fails.
            with self.assertRaisesRegex(ValueError,"core/thread"):
                checker.verify(build,run,external={})
            receipt=json.loads((run/"result.json").read_text())
            receipt.update(single_core=True,emu_threads=1)
            (run/"result.json").write_text(json.dumps(receipt))
            result=checker.verify(build,run,external=receipt["files"])
            self.assertEqual(result["status"],"PASS")
            self.assertEqual(result["samples"],json.loads((run/"windows.json").read_text())["samples"])

    def test_unreviewed_generator_cannot_authorize_itself(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);extract("images-02/smoke-d0-s00",root)
            source=root/"source/generate.py";source.write_bytes(source.read_bytes()+b"\nraise RuntimeError('untrusted execution')\n")
            record=json.loads((root/"build.json").read_text())
            record["software"]["team/workloads/o3-gemv/generate.py"]=checker.base.sha(source)
            (root/"build.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,"unreviewed O3 generator"):
                checker.verify_generation(root,json.loads((root/"data/manifest.json").read_text()))

    def test_exact_wrapper_and_overriding_flags(self):
        command=['timeout','120m','stdbuf','-o0','-e0','/emu','-i','/image','--flash=/flash',
                 '--diff=/reference','--ram-size=128MB','--max-cycles=2000000','--seed=1']
        self.assertEqual(checker.runtime_roles(command)['emu'],'/emu')
        for suffix in (['--diff=/other'],['--no-diff'],['--seed=2']):
            with self.subTest(suffix=suffix),self.assertRaises(ValueError):checker.runtime_roles(command+suffix)
        command[3]='-oL'
        with self.assertRaises(ValueError):checker.runtime_roles(command)
