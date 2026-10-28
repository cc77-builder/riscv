"""Synthetic temporary fixtures for archive/receipt gates; no simulator qualification."""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
sys.dont_write_bytecode = True
import current_clean_archive as a

REPO = None
CLEAN_ADAPTER = None

class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins = a.read(a.HERE / "runtime-source-lock.json")
        core = types.SimpleNamespace(__file__=str(CLEAN_ADAPTER / "current_clean_fullcore.py"),
            p=types.SimpleNamespace(read=a.read, require=a.require, sha=a.sha), g=types.SimpleNamespace(),
            ce=types.SimpleNamespace(), PASS=a.PASS, CORE=a.CORE, SUPPLEMENTS=a.SUPPLEMENTS)
        cls.e = a.receipt_tools(REPO, core)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-receipt-unit-")
        self.run = Path(self.temp.name)
        start = datetime(2026, 10, 26, tzinfo=timezone.utc)
        # Explicit parentheses avoid fixture operator-precedence ambiguity.
        order = ["hello-vadd", "negative-vdot", "functional-0"] + sorted(
            (a.CORE | a.SUPPLEMENTS) - {"hello-vadd", "negative-vdot", "functional-0"})
        rows = []
        for number, name in enumerate(order):
            directory = self.run / "runs" / name; directory.mkdir(parents=True)
            negative = name == "negative-vdot"
            raw = {"stdout.log": b"SYNTHETIC UNIT TEST RECEIPT ONLY\n", "stderr.log": b""}
            raw["run.log"] = raw["stderr.log"] + raw["stdout.log"]
            for filename, body in raw.items(): (directory / filename).write_bytes(body)
            command = ["timeout", "120m", "stdbuf", "-o0", "-e0", "/not-executed/emu", "-i",
                       "/synthetic/same-image.bin" if name in ("negative-vdot", "functional-0") else "/synthetic/" + name,
                       "--flash=/synthetic/flash", "--ram-size=128MB",
                       "--diff=/synthetic/" + ("negative" if negative else "normal"), "--max-cycles=5000000"]
            row = dict(name=name, started=(start + timedelta(seconds=number * 2)).isoformat(),
                finished=(start + timedelta(seconds=number * 2 + 1)).isoformat(), command=command, files={},
                negative_target="vdot" if negative else None, cwd=str(directory / "cwd"), auxiliary_files={},
                environment_overrides={"XS_NEGATIVE_VECTOR_TARGET": "vdot" if negative else None},
                process_started=True, pid=1000 + number, pid_kind="synthetic-only", actual_new_execution=True,
                performance_measured=False, exit_code=1 if negative else 0, timed_out=False,
                terminated_returncode=None, raw_logs_sha256={n: a.digest(v) for n,v in raw.items()},
                status="SYNTHETIC_FIXTURE_NOT_A_WORKLOAD_VERDICT")
            a.save(directory / "runtime.json", row); a.save(directory / "result.json", row)
            (directory / "exit-code.txt").write_text(str(row["exit_code"]) + "\n")
            rows.append(row)
        a.save(self.run / "completed-runs.json", sorted(rows,key=lambda r:r["name"]))
        a.save(self.run / "state.json", dict(status=a.PASS, controller_sha256=self.e.CONTROLLER,
            new_emu_runs=14, new_emu_launch_attempts=14, active={}, jobs=1, cpu_affinity=[0],
            started=start.isoformat(), finished=(start + timedelta(seconds=30)).isoformat()))

    def tearDown(self): self.temp.cleanup()
    def check(self): return a.process_receipts(self.run,self.e)
    def mutate(self, name, fn, runtime=True):
        path=self.run/"runs"/name/"result.json"; row=a.read(path);fn(row);a.save(path,row)
        if runtime:
            path=self.run/"runs"/name/"runtime.json";row=a.read(path);fn(row);a.save(path,row)

    def test_selected_runtime_source_lock_matches_real_files(self):
        for name, digest in self.pins["sources"].items():
            self.assertEqual(a.sha(CLEAN_ADAPTER / name), digest)

    def test_consistent_receipt_fixture_only(self):
        result=self.check()
        self.assertEqual(result["new_emu_runs"],0)
        self.assertTrue(result["negative_recovery_same_image"])
    def test_boolean_process_count_rejected(self):
        p=self.run/"state.json";x=a.read(p);x["new_emu_runs"]=True;a.save(p,x)
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_affinity_rejected(self):
        p=self.run/"state.json";x=a.read(p);x["cpu_affinity"]=[0,0];a.save(p,x)
        with self.assertRaises(ValueError):self.check()
    def test_live_process_rejected(self):
        p=self.run/"state.json";x=a.read(p);x["active"]={"x":100};a.save(p,x)
        with self.assertRaises(ValueError):self.check()
    def test_spawn_pid_disagreement_rejected(self):
        self.mutate("control",lambda x:x.update(pid=9999),runtime=False)
        with self.assertRaises(ValueError):self.check()
    def test_timeout_rejected(self):
        self.mutate("control",lambda x:x.update(timed_out=True))
        with self.assertRaises(ValueError):self.check()
    def test_actual_exit_receipt_rejected(self):
        (self.run/"runs/control/exit-code.txt").write_text("1\n")
        with self.assertRaises(ValueError):self.check()
    def test_negative_exit_zero_rejected(self):
        self.mutate("negative-vdot",lambda x:x.update(exit_code=0))
        (self.run/"runs/negative-vdot/exit-code.txt").write_text("0\n")
        with self.assertRaises(ValueError):self.check()
    def test_log_hash_mutation_rejected(self):
        (self.run/"runs/control/stdout.log").write_bytes(b"tampered")
        with self.assertRaises(ValueError):self.check()
    def test_derived_log_order_rejected(self):
        d=self.run/"runs/control";(d/"stderr.log").write_bytes(b"err")
        (d/"run.log").write_bytes((d/"stdout.log").read_bytes()+b"err")
        self.mutate("control",lambda x:x.update(raw_logs_sha256={
            n:a.sha(d/n) for n in ("stdout.log","stderr.log","run.log")}))
        with self.assertRaises(ValueError):self.check()
    def test_missing_job_rejected(self):
        shutil.rmtree(self.run/"runs/control")
        with self.assertRaises(ValueError):self.check()
    def test_negative_recovery_image_mismatch(self):
        self.mutate("functional-0",lambda x:x["command"].__setitem__(7,"/wrong/image"))
        with self.assertRaises(ValueError):self.check()
    def test_negative_recovery_same_pid_rejected(self):
        neg=a.read(self.run/"runs/negative-vdot/result.json")["pid"]
        self.mutate("functional-0",lambda x:x.update(pid=neg))
        with self.assertRaises(ValueError):self.check()
    def test_completed_index_missing_rejected(self):
        p=self.run/"completed-runs.json";v=a.read(p);a.save(p,v[:-1])
        with self.assertRaises(ValueError):self.check()
    def test_symlink_log_rejected(self):
        d=self.run/"runs/control";(d/"stdout.log").unlink();(d/"stdout.log").symlink_to(d/"run.log")
        with self.assertRaises(ValueError):self.check()
    def test_injection_environment_rejected(self):
        self.mutate("control",lambda x:x.update(environment_overrides={"XS_NEGATIVE_VECTOR_TARGET":"vdot"}))
        with self.assertRaises(ValueError):self.check()

class ArchiveBytesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="synthetic-archive-unit-")
        self.base=Path(self.temp.name);self.source=self.base/"source.txt"
        self.source.write_bytes(b"archive fixture only\n"*1000)
        self.archive=self.base/"archive"
        self.reader=a.portable(REPO)
        writer=a.Writer(self.archive,self.reader)
        writer.add(self.source,"inputs/source.txt","unit-test-fixture")
        self.sealed=writer.finish({"fixture_only":True})
    def tearDown(self):self.temp.cleanup()
    def test_roundtrip_and_no_semantic_claim(self):
        self.assertEqual(self.sealed.raw("inputs/source.txt"),self.source.read_bytes())
        self.assertTrue(self.sealed.json("evidence-map.json")["fixture_only"])
    def test_payload_mutation_rejected(self):
        p=self.archive/self.sealed.records["inputs/source.txt"]["stored"]
        p.write_bytes(p.read_bytes()+b"x")
        with self.assertRaises(ValueError):self.reader.Archive(self.archive)
    def test_manifest_hash_mutation_rejected(self):
        p=self.archive/"archive-manifest.json";p.write_bytes(p.read_bytes()+b" ")
        with self.assertRaises(ValueError):self.reader.Archive(self.archive)
    def test_unexpected_payload_rejected(self):
        (self.archive/"files/extra").write_bytes(b"x")
        with self.assertRaises(ValueError):self.reader.Archive(self.archive)
    def test_missing_payload_rejected(self):
        (self.archive/self.sealed.records["inputs/source.txt"]["stored"]).unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):self.reader.Archive(self.archive)
    def test_unsafe_logical_rejected(self):
        other=self.base/"other"
        writer=a.Writer(other,self.reader)
        with self.assertRaises(ValueError):writer.add(self.source,"../escape","fixture")
    def test_duplicate_original_is_deduplicated_with_roles(self):
        other=self.base/"other";writer=a.Writer(other,self.reader)
        writer.add(self.source,"one","one");writer.add(self.source,"two","two")
        sealed=writer.finish({"fixture_only":True})
        self.assertEqual(len(sealed.records),2)
        self.assertEqual(set(sealed.json("evidence-map.json")["roles"]),{"one","two"})
    def test_input_changed_during_seal_rejected(self):
        other=self.base/"other";writer=a.Writer(other,self.reader)
        writer.add(self.source,"one","one");self.source.write_bytes(b"different")
        with self.assertRaises(ValueError):writer.add(self.source,"two","two")
    def test_output_overlap_rejected(self):
        with self.assertRaises(ValueError):a.outside(self.base/"new",[self.base])
    def test_pinned_source_link_archives_regular_payload_and_metadata(self):
        source_root=self.base/"hardware";source_root.mkdir()
        target=source_root/"target.h";target.write_bytes(b"source contents")
        link=source_root/"link.h";link.symlink_to("target.h")
        metadata=a.pinned_source_link(link,source_root,a.sha(link))
        writer=a.Writer(self.base/"links",self.reader)
        writer.add(link,"hardware-source/link.h","hardware-source",source_link=metadata)
        sealed=writer.finish({"fixture_only":True,"source_links":{str(link):metadata}})
        self.assertEqual(sealed.raw("hardware-source/link.h"),target.read_bytes())
        stored=writer.output/sealed.records["hardware-source/link.h"]["stored"]
        self.assertFalse(stored.is_symlink())
        self.assertEqual(sealed.records["hardware-source/link.h"]["original"],str(link))
    def test_source_link_escape_rejected(self):
        source_root=self.base/"hardware";source_root.mkdir()
        link=source_root/"link.h";link.symlink_to(self.source)
        with self.assertRaises(ValueError):a.pinned_source_link(link,source_root,a.sha(link))
    def test_source_link_content_drift_rejected(self):
        source_root=self.base/"hardware";source_root.mkdir()
        target=source_root/"target.h";target.write_bytes(b"source contents")
        link=source_root/"link.h";link.symlink_to("target.h")
        with self.assertRaises(ValueError):a.pinned_source_link(link,source_root,"a"*64)

    def test_bytes_only_does_not_accept_fixture_as_real_archive(self):
        with self.assertRaises((KeyError,ValueError)):a.open_archive(REPO,self.archive)

class BoundArchiveFixtureTests(unittest.TestCase):
    """Structurally complete byte package with non-verdict synthetic campaign."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="synthetic-bound-bytes-unit-")
        self.base=Path(self.temp.name);self.run=self.base/"run";self.run.mkdir()
        self.audit=self.base/"audit";self.audit.mkdir()
        self.source=self.base/"direct.txt";self.source.write_bytes(b"synthetic direct")
        self.support=self.base/"support.txt";self.support.write_bytes(b"synthetic support")
        self.emu=self.base/"hardware/build/emu";self.emu.parent.mkdir(parents=True);self.emu.write_bytes(b"NOT AN EMULATOR")
        self.value=dict(configuration={"hardware_source":str(self.emu.parents[1])},
            hardware_profile={"emu_sha256":a.sha(self.emu)},
            support_files={str(self.support):a.sha(self.support)},fixture_only=True)
        a.save(self.run/"identity.json",self.value)
        a.save(self.run/"runtime-inputs.json",{str(self.source):a.sha(self.source),str(self.emu):a.sha(self.emu)})
        a.save(self.run/"results.json",{"synthetic_bytes_fixture":True,"runtime_verdict":None})
        (self.audit/"fixture.txt").write_text("no semantic audit executed")
        self.writer=a.Writer(self.base/"archive",a.portable(REPO))
        for role,root in (("campaign",self.run),("physical-audit",self.audit)):
            for name,path in a.files_under(root).items():self.writer.add(path,role+"/"+name,role)
        self.writer.add(self.source,"inputs/direct","runtime-input")
        self.writer.add(self.support,"support/provenance","support-input")
        clean=CLEAN_ADAPTER
        auditors=[Path(a.__file__).resolve(),a.HERE/"runtime-source-lock.json",REPO/a.PORTABLE,REPO/a.RECEIPT_TOOL]
        auditors += [clean/n for n in a.read(a.HERE/"runtime-source-lock.json")["sources"]]
        for n,path in enumerate(auditors):self.writer.add(path,f"auditors/{n}/"+path.name,"auditor-source")
        self.info=dict(contract=a.CONTRACT,source_root=str(REPO),clean_adapter=str(clean),campaign=str(self.run),
            physical_audit=str(self.audit),external_inputs={str(self.emu):a.sha(self.emu)},source_scope="direct",
            audit_source_sha256=a.sha(a.__file__),source_lock_sha256=a.sha(a.HERE/"runtime-source-lock.json"),
            auditor_path=str(Path(a.__file__).resolve()),source_lock_path=str(a.HERE/"runtime-source-lock.json"),
            controller_sha256=a.sha(clean/"current_clean_fullcore.py"),
            source_result_sha256=a.sha(self.run/"results.json"),identity_sha256=a.sha(self.run/"identity.json"),
            semantic_audit_requires_physical_originals=True,fixture_only=True)
    def tearDown(self):self.temp.cleanup()
    def test_bytes_pass_explicitly_has_no_semantic_qualification(self):
        self.writer.finish(self.info)
        result=a.bytes_only(REPO,self.base/"archive")
        self.assertFalse(result["raw_semantic_audit_executed"])
        self.assertFalse(result["physical_originals_revalidated"])
        self.assertEqual(result["new_emu_runs"],0)
    def test_missing_auditor_closure_rejected(self):
        key=next(iter(self.writer.roles["auditor-source"]))
        del self.writer.roles["auditor-source"][key]
        self.writer.finish(self.info)
        with self.assertRaises(ValueError):a.open_archive(REPO,self.base/"archive")
    def test_runtime_external_set_change_rejected(self):
        self.info["external_inputs"]={}
        self.writer.finish(self.info)
        with self.assertRaises(ValueError):a.open_archive(REPO,self.base/"archive")
    def test_physical_original_changed_rejected(self):
        self.writer.finish(self.info)
        _,info,combined=a.open_archive(REPO,self.base/"archive")
        self.source.write_bytes(b"tamper")
        with self.assertRaises(ValueError):a.live_match(info,combined)
    def test_physical_campaign_addition_rejected(self):
        self.writer.finish(self.info)
        _,info,combined=a.open_archive(REPO,self.base/"archive")
        (self.run/"unexpected").write_bytes(b"new")
        with self.assertRaises(ValueError):a.live_match(info,combined)

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--clean-adapter",type=Path)
    args,rest=ap.parse_known_args();REPO=args.repo.resolve()
    CLEAN_ADAPTER=args.clean_adapter.resolve() if args.clean_adapter else REPO/a.CLEAN_REL
    unittest.main(argv=[__file__]+rest)
