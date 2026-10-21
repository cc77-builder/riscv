import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import copy
import build_o1 as build

class PreservationTests(unittest.TestCase):
    def fixture(self,base):
        root=base/"build";root.mkdir()
        (root/"emu").write_bytes(b"original executable")
        (root/"constantin.cpp").write_bytes(b"old auxiliary")
        (root/"rtl").mkdir();(root/"rtl/SimTop.sv").write_bytes(b"old rtl")
        saved=base/"saved";pins=build.preserve_generated(root,saved)
        return root,saved,pins

    def test_old_generation_restored_and_new_auxiliary_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);root,saved,pins=self.fixture(b)
            (root/"constantin.cpp").write_bytes(b"new auxiliary")
            (root/"extra.txt").write_bytes(b"new fixed path")
            alterations=build.restore_generated(root,saved,pins,b/"changed")
            self.assertEqual((root/"constantin.cpp").read_bytes(),b"old auxiliary")
            self.assertEqual((root/"rtl/SimTop.sv").read_bytes(),b"old rtl")
            self.assertEqual((root/"emu").read_bytes(),b"original executable")
            self.assertFalse((root/"extra.txt").exists())
            self.assertEqual((b/"changed/extra.txt.removed-from-original").read_bytes(),b"new fixed path")
            self.assertEqual(len(alterations),2)

    def test_unexpected_new_rtl_not_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);root,saved,pins=self.fixture(b)
            unexpected=root/"rtl/unexpected.sv";unexpected.write_bytes(b"unexpected")
            with self.assertRaisesRegex(ValueError,"unexpected new"):
                build.restore_generated(root,saved,pins,b/"changed")
            self.assertEqual(unexpected.read_bytes(),b"unexpected")

    def test_corrupted_preserved_file_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp);root,saved,pins=self.fixture(b)
            (saved/"constantin.cpp").write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError,"preserved source changed"):
                build.restore_generated(root,saved,pins,b/"changed")

class CurrentReferenceTests(unittest.TestCase):
    def test_reference_requires_complete_success_identity_and_contract(self):
        from test_compare import pins as pair_pins
        _, pins = pair_pins()
        pins.update(emu_sha256="e"*64, emu_path=str(build.ROOT/"build/emu"))
        state = dict(status="O2_FULLCORE_BUILD_PASS",build_exit_code=0,
                     source_commit=pins["source_commit"],emu_sha256=pins["emu_sha256"])
        def validate(p, st):
            return build.validate_reference(p, st, pins["files"], pins["dependency_files"],
                                            pins["native_build_contract"], pins["emu_sha256"])
        with patch.object(build, "git", return_value=(pins["source_commit"]+"\n").encode()):
            validate(pins, state)
            for field, value in (("build_exit_code",False),("status","BUILDING"),("emu_sha256","f"*64)):
                bad=copy.deepcopy(state);bad[field]=value
                with self.assertRaises(ValueError):validate(pins,bad)
            for field, value in (("files",{}),("NUM_CORES",True),("native_build_contract",None),
                                 ("emu_path","/alien/emu")):
                bad=copy.deepcopy(pins);bad[field]=value
                with self.assertRaises(ValueError):validate(bad,state)


class NativeProfileTests(unittest.TestCase):
    def test_actual_receipts_invocation_and_native_tool_drift(self):
        import json
        import build_profile
        from test_compare import pins as pair_pins
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = pair_pins()[0]["native_build_contract"]
            for role, tool in contract["compilers"].items():
                path=root/role;path.write_bytes(role.encode())
                tool.update(path=str(path),sha256=build.sha(path))
            contract["mill_launch"]=[contract["compilers"]["sh"]["path"],contract["compilers"]["mill"]["path"]]
            directories=[]
            for mode,status in (("o1","O1_MATCHED_BUILD_PASS"),("o2","O2_FULLCORE_BUILD_PASS")):
                directory=root/mode;directory.mkdir();directories.append(directory)
                products=directory/"products";products.mkdir()
                emu=products/"emu";emu.write_bytes(mode.encode())
                pins=dict(native_build_contract=contract,source_commit="a"*40,
                          emu_sha256=build.sha(emu),emu_path=str(emu))
                state=dict(status=status,build_exit_code=0,source_commit="a"*40,
                           emu_sha256=build.sha(emu),build_products=str(products))
                for leaf,body in (("hardware-inputs.json",pins),("build-state.json",state),
                                  ("original-build-restoration.json",dict(status="ORIGINAL_O2_GENERATION_RESTORED")),
                                  ("generated-auxiliary.json",[])):
                    (directory/leaf).write_text(json.dumps(body))
                command=build.build_recipe.make_command(contract, products if mode=="o1" else None)
                (directory/"build-command.sh").write_text(command)
                (directory/"emu-build.log").write_text("verilator --exe --threads 1 -O3 --cc x\n")
            self.assertEqual(build_profile.build_profile(*directories)[1]["status"],"MATCHED_O1_O2_BUILD_PROFILE_PASS")
            command=directories[0]/"build-command.sh";original=command.read_text()
            command.write_text(original.replace("OPT_FAST=-O3","OPT_FAST=-O0"))
            with self.assertRaisesRegex(ValueError,"invocation differs"):
                build_profile.build_profile(*directories)
            command.write_text(original)
            (root/"cc").write_bytes(b"compiler replaced")
            with self.assertRaisesRegex(ValueError,"native tool changed"):
                build_profile.build_profile(*directories)


if __name__=="__main__":unittest.main()
