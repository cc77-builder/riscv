"""Reject semantic mutations of the actual C application's linked artifacts."""
import copy
import os
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

import entry_c_api as c

g,a=c.g,c.a


class ActualCBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value=os.environ.get("R4_C_API_BUILD")
        if not value:
            raise RuntimeError("R4_C_API_BUILD must name the actual GNU/AM build")
        cls.build=Path(value)
        cls.validation=c.verify_build(g.ROOT,cls.build)

    def mutate_symbol(self,symbol,transform,message):
        with tempfile.TemporaryDirectory(prefix="r4-c-linked-reject-") as temp:
            build=Path(temp)/"build"
            shutil.copytree(self.build,build,ignore=shutil.ignore_patterns("objects"))
            elf_path=build/"vdot-perf.elf"
            raw=bytearray(elf_path.read_bytes())
            elf=g.ELF(raw)
            address=elf.symbols[symbol][0]
            section=next(s for s in elf.sections if s[1]!=8 and s[2]&2 and s[3]<=address<s[3]+s[5])
            offset=section[4]+address-section[3]
            transform(raw,offset,elf)
            elf_path.write_bytes(raw)
            (build/"vdot-perf.bin").write_bytes(g.ELF(raw).binary())
            receipt=a.read(build/"build.json")
            for name in ("vdot-perf.elf","vdot-perf.bin"):
                receipt["artifacts"][name]=g.sha(build/name)
            g.save(build/"build.json",receipt)
            with self.assertRaisesRegex(ValueError,message):
                c.verify_build(g.ROOT,build)

    def test_actual_c_linked_public_functions(self):
        self.assertEqual(self.validation["cases"],48)
        self.assertEqual(self.validation["public_functions"],16)
        self.assertEqual(self.validation["expected_dots"],1008)
        self.assertTrue(all(r["semantics"]["trials"]==9 for r in self.validation["functions"]))

    def test_rehashed_wrong_function_pointer_is_rejected(self):
        def change(raw,offset,elf):
            manifest=a.read(self.build/"source/manifest.json")
            target=elf.symbols[manifest["cases"][1]["api_symbol"]][0]
            raw[offset:offset+8]=struct.pack("<Q",target)
        self.mutate_symbol("r4_c_cases",change,"linked call table differs")

    def test_rehashed_wrong_linked_input_is_rejected(self):
        name=next(iter(a.read(self.build/"source/manifest.json")["inputs"]))
        def change(raw,offset,elf): raw[offset]^=1
        self.mutate_symbol(name,change,"actual input bytes")

    def test_missing_required_tool_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="r4-c-build-reject-") as temp:
            build=Path(temp)/"build"
            shutil.copytree(self.build,build,ignore=shutil.ignore_patterns("objects"))
            receipt=a.read(build/"build.json")
            receipt["toolchain"].pop("objcopy")
            g.save(build/"build.json",receipt)
            with self.assertRaisesRegex(ValueError,"toolchain inventory"):
                c.verify_build(g.ROOT,build)

    def test_c_source_guard_cannot_be_removed(self):
        with tempfile.TemporaryDirectory(prefix="r4-c-guard-reject-") as temp:
            build=Path(temp)/"build"
            shutil.copytree(self.build,build,ignore=shutil.ignore_patterns("objects"))
            main=build/"source/main.c"
            main.write_text(main.read_text().replace("if(detected!=5 || judge(c)) return 2;","/* omitted */"))
            with self.assertRaisesRegex(ValueError,"source regeneration: main.c"):
                c.verify_build(g.ROOT,build)


class Recovery(unittest.TestCase):
    def test_new_contract_recovery_and_identity_boundaries(self):
        negative=dict(status=a.frozen_m.NEGATIVE_PASS,negative=True,image_sha256="1"*64,name="r4-c-api-s1",
                      pid=101,reference="negative.so",finished="2026-10-23T20:00:01+00:00")
        normal=dict(status="R4_C_APPLICATION_DIFFTEST_PASS",negative=False,image_sha256="1"*64,name="r4-c-api-s1",
                    pid=102,reference="normal.so",started="2026-10-23T20:00:02+00:00")
        c.validate_recovery(negative,normal)
        for change in ({"status":a.frozen_m.NORMAL_PASS},{"pid":101},{"image_sha256":"2"*64},
                       {"reference":"negative.so"},{"started":"2026-10-23T20:00:00+00:00"}):
            with self.subTest(change=change):
                changed=dict(normal,**change)
                with self.assertRaises(ValueError): c.validate_recovery(negative,changed)


class Console(unittest.TestCase):
    SCHEMA = "O2_SCHEMA version=1 clock=global latency=2 slots=2 rob_size=48 ftq_size=8 vlen=128 vpu_width=195 perf_width=577\n"
    SAMPLE = "T13_CSR_SAMPLE cycle=1 addr=0xc00 data=0x0 wen=0\n"

    def test_observer_insertion_preserves_uart_characters(self):
        observer=g.load("r4_c_console_test",g.ROOT/"team/optimizations/o2/fullcore/analyze.py")
        expected="R4C_CASE seq=0 hash=0123456789abcdef\nHIT GOOD TRAP\n"
        for cut in (2,23,44):
            with self.subTest(cut=cut):
                _,uart=observer.extract_events_and_uart(self.SCHEMA+expected[:cut]+self.SAMPLE+expected[cut:])
                self.assertEqual(uart,expected)

    def test_interrupted_failure_markers_are_still_rejected(self):
        with tempfile.TemporaryDirectory(prefix="r4-c-uart-reject-") as temp:
            run=Path(temp)
            (run/"stderr.log").write_text("")
            for marker in ("HIT BAD TRAP","DIFFTEST FAIL","CRITICAL ERROR"):
                with self.subTest(marker=marker):
                    text=self.SCHEMA+marker[:2]+self.SAMPLE+marker[2:]+"\nHIT GOOD TRAP\n"
                    (run/"stdout.log").write_text(text)
                    with self.assertRaisesRegex(ValueError,"runtime failure marker|O2 fatal runtime output"):
                        c.normal_check(g.ROOT,run/"unused-build",run,dict(process_started=True,exit_code=0))


if __name__=="__main__":
    unittest.main()
