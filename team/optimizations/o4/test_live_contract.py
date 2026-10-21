import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import live_contract as live
from audit import HISTORICAL_GENERATIONS, validate_pair, validate_selection
from elaborate import build_recipe


def tool_contract():
    return dict(schema=1,environment={"PATH":"/usr/bin"},lock_sha256=live.sha(Path(live.__file__).with_name("toolchain-lock.json")),library=live.expected_library(),
                tools={name:dict(path="/tools/"+name,sha256="2"*64,version="pinned",
                                 libraries={"/lib/libc.so":"3"*64})
                       for name in ("yosys","berkeley-abc","sta")})


def generation():
    native=dict(schema=2,make_args=build_recipe.MAKE_ARGS,environment_sha256="4"*64,
                mill_launch=["/bin/bash", "/bin/mill"],
                launch_metadata={".mill-version":dict(sha256="0"*64,value="0.12.3")},
                recipe_sha256="5"*64,compilers={name:dict(path="/bin/"+name,sha256="6"*64,version="pinned")
                   for name in ("cxx","cc","java","bash","mill","verilator","verilator_bin","firtool")})
    return dict(source_commit="a"*40,source_inputs_unchanged=True,
                source_inputs=dict(source_commit="a"*40,files={"src/control.scala":"7"*64},
                                   dependency_files={"dep/module.scala":"8"*64}),
                native_build_contract=native)


def paired():
    names=("o1-fu","o2-fu","o1-parent","o2-parent")
    generations={key:(key,(generation(),"9"*64)) for key in names}
    results={key:{stage:dict(tool_contract=tool_contract(),tool_contract_unchanged=True)
                  for stage in ("mapping","timing")} for key in names}
    return generations,results


class LiveContracts(unittest.TestCase):
    def test_capture_nonempty_ldd_inventory_survives_json_roundtrip(self):
        # Execute capture's real loop and hashing with independently assembled
        # binaries/shared library; only native probe output is simulated.
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);binary=work/"tools/root/usr/bin";binary.mkdir(parents=True)
            shared=work/"libsample.so";shared.write_bytes(b"shared library fixture")
            for name in ("yosys","berkeley-abc","sta"):(binary/name).write_bytes(name.encode())
            outputs=[]
            for name in ("yosys","berkeley-abc","sta"):
                outputs += [f"libsample.so => {shared.as_posix()} (0x1234)\n",name+" pinned version\n"]
            # ldd uses absolute POSIX paths. On Windows supply the same real
            # library via a rooted slash spelling accepted by Path.resolve.
            if shared.drive:
                outputs=[value.replace(shared.as_posix(),"/"+shared.as_posix()) if "=>" in value else value for value in outputs]
            original_resolve=Path.resolve
            def resolve(path,*args,**kwargs):
                text=str(path).replace("\\","/")
                if shared.drive and text.startswith("/"+shared.drive+"/"):
                    path=Path(text[1:])
                return original_resolve(path,*args,**kwargs)
            with patch.object(live,"library_inventory",return_value=live.expected_library()),patch.object(live.subprocess,"check_output",side_effect=outputs) as probe,patch.object(Path,"resolve",resolve):
                contract=live.capture(work)
            restored=json.loads(json.dumps(contract))
            self.assertEqual(restored["library"],live.expected_library())
            for name,tool in restored["tools"].items():
                self.assertEqual(tool["sha256"],live.sha(binary/name))
                self.assertEqual(tool["libraries"],{str(shared.resolve()):live.sha(shared)})
                self.assertEqual(tool["version"],name+" pinned version\n")
            self.assertEqual(probe.call_count,6)

    def test_current_pair_requires_same_complete_sources_and_tools(self):
        g,r=paired()
        self.assertEqual(validate_pair(g,r),"current-source-and-tool-contracts")
        for mutate in (
            lambda x:x["source_inputs"]["files"].update({"src/control.scala":"b"*64}),
            lambda x:x["source_inputs"]["dependency_files"].update({"dep/module.scala":"b"*64}),
            lambda x:x["source_inputs"].update(source_commit="b"*40),
            lambda x:x["native_build_contract"]["compilers"]["java"].update(sha256="b"*64),
            lambda x:x.pop("source_inputs"),
            lambda x:x.update(source_inputs_unchanged=False)):
            bad=copy.deepcopy(g);mutate(bad["o2-parent"][1][0])
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):validate_pair(bad,r)

    def test_mapping_and_sta_tool_drift_or_missing_contract_rejected(self):
        g,r=paired()
        for mutate in (
            lambda x:x["tool_contract"]["tools"]["sta"].update(sha256="b"*64),
            lambda x:x["tool_contract"]["tools"]["yosys"]["libraries"].update({"/lib/libc.so":"b"*64}),
            lambda x:x["tool_contract"]["environment"].update(PATH="/different"),
            lambda x:x.pop("tool_contract"),
            lambda x:x.update(tool_contract_unchanged=False)):
            bad=copy.deepcopy(r);mutate(bad["o2-parent"]["timing"])
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):validate_pair(g,bad)

    def test_historical_only_exact_original_receipts_without_new_contracts(self):
        g={name:(name,({},digest)) for name,digest in HISTORICAL_GENERATIONS.items()}
        r={name:{"mapping":{},"timing":{}} for name in g}
        self.assertEqual(validate_pair(g,r),"historical-20261020-replay")
        bad=copy.deepcopy(g);name=next(iter(bad));bad[name]=(name,({},"0"*64))
        with self.assertRaises(ValueError):validate_pair(bad,r)
        r[next(iter(r))]["mapping"]["tool_contract"]=tool_contract()
        with self.assertRaisesRegex(ValueError,"mixed"):validate_pair(g,r)

    def test_changed_executable_is_rejected_before_version_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);binary=work/"tools/root/usr/bin";binary.mkdir(parents=True)
            library=work/"lib.so";library.write_bytes(b"original library")
            contract=tool_contract()
            for name,tool in contract["tools"].items():
                path=binary/name;path.write_bytes(b"original binary")
                tool.update(path=str(path.resolve()),sha256=live.sha(path),libraries={str(library):live.sha(library)})
            (work/"tools/contract.json").write_text(json.dumps(contract))
            # validate's Linux path policy is orthogonal to this Windows-capable
            # byte mutation test; all execution and comparison code remains real.
            with patch.object(live,"validate"),patch.object(live,"library_inventory",return_value=contract["library"]),patch.object(live,"capture",return_value=contract) as probe:
                self.assertEqual(live.verify(work),contract)
                probe.reset_mock();(binary/"yosys").write_bytes(b"replacement")
                with self.assertRaisesRegex(ValueError,"executable changed"):live.verify(work)
                probe.assert_not_called()
                (binary/"yosys").write_bytes(b"original binary")
                library.write_bytes(b"replacement library")
                with self.assertRaisesRegex(ValueError,"shared library changed"):live.verify(work)
                probe.assert_not_called()

    def test_preparation_contract_replacement_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);(work/"tools").mkdir()
            contract=tool_contract();(work/"tools/contract.json").write_text(json.dumps(contract))
            bad=copy.deepcopy(contract);bad["lock_sha256"]="b"*64
            with self.assertRaisesRegex(ValueError,"preparation contract changed"):live.verify(work,bad)

    def test_library_mutation_rejected_before_any_tool_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);(work/"library").mkdir();lib=work/"library/reference.lib";lib.write_bytes(b"fixed reference")
            lock={"library":{"files":[dict(file="reference.lib",sha256=live.sha(lib),url="pinned")]}}
            with patch.object(live,"load_lock",return_value=lock),patch.object(live.subprocess,"check_output") as probe:
                self.assertEqual(live.library_inventory(work),{"reference.lib":live.sha(lib)})
                lib.write_bytes(b"different cell areas")
                with self.assertRaisesRegex(ValueError,"reference library/source changed"):live.capture(work)
                probe.assert_not_called()

    def test_each_stage_receipt_must_bind_the_summary_tool_contract(self):
        contract=tool_contract();receipt=dict(tool_contract=contract,tool_contract_unchanged=True,exit_code=0)
        live.stage_receipt(contract,receipt)
        for mutate in (lambda x:x.pop("tool_contract"),lambda x:x.update(tool_contract_unchanged=False),
                       lambda x:x.update(exit_code=False),lambda x:x.update(exit_code=1),
                       lambda x:x["tool_contract"]["tools"]["sta"].update(sha256="b"*64)):
            bad=copy.deepcopy(receipt);mutate(bad)
            with self.assertRaises(ValueError):live.stage_receipt(contract,bad)

    def test_successful_mapping_process_cannot_hide_postrun_tool_drift(self):
        import synthesize
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);g=work/"generation";g.mkdir();(g/"rtl").mkdir()
            (g/"result.json").write_text(json.dumps(dict(exit_code=0,source_inputs={"captured":True},
                source_inputs_unchanged=True,boundary="fu",mode="o2")))
            (work/"library").mkdir();(work/"library/NangateOpenCellLibrary_typical.lib").write_text("library fixture")
            output=work/"map"
            args=["synthesize.py",str(g),str(output),"--work",str(work)]
            with patch("sys.argv",args),patch.object(live,"verify",side_effect=[tool_contract(),ValueError("tool changed")]),patch.object(synthesize.subprocess,"run",return_value=SimpleNamespace(returncode=0)):
                with self.assertRaises(SystemExit) as caught:synthesize.main()
            self.assertEqual(caught.exception.code,1)
            receipt=json.loads((output/"run.json").read_text())
            self.assertFalse(receipt["tool_contract_unchanged"])
            self.assertEqual(receipt["tool_exit_code"],0)
            self.assertEqual(receipt["exit_code"],1)
            self.assertFalse((output/"summary.json").exists())

    def test_selection_supports_fresh_names_but_rejects_aliases_and_escapes(self):
        selection={key:[key+"-new-map",key+"-new-sta"] for key in paired()[0]}
        self.assertEqual(validate_selection(selection),selection)
        for value in ("../escape","C:/escape","nested/map",selection["o1-fu"][1]):
            bad=copy.deepcopy(selection);bad["o1-fu"][0]=value
            with self.assertRaises(ValueError):validate_selection(bad)


if __name__=="__main__":unittest.main()
