"""Replay B0/H1 sealed bytes, architectural counter windows, both protocols and statistics.

Does not run EMU/NEMU or repeat Linux Git/toolchain/dependency provenance.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
import types
import tempfile
import importlib.util

CORE_JOBS={"hello-vadd","negative-vdot","control","dense-batch128"}|{f"functional-{i}" for i in range(8)}
SUPPLEMENT_JOBS={"o2-diagnostic","o2-control-diagnostic"}
PARSER="team/optimizations/o2/fullcore/analyze.py"
RUNTIME_GATE="team/optimizations/o1/audit/runtime_gate.py"
NORMAL_REFERENCE="efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4"
NEGATIVE_REFERENCE="9b3aecf362b7c7ddb4f8bace355c2e0ee2cc919fd5f59eefc641db220ab40df0"

def require(ok,message):
    if not ok:
        raise ValueError(message)


def reject_fatal_output(text):
    """Reject fatal emulator/software errors even when exit=0 says GOOD TRAP.

    This O2-only gate supplements the immutable shared O1 bit100/runtime gate.
    Strip complete ANSI CSI escapes before matching, including color escapes
    inserted within words. Unknown escape sequences remain fail-closed.
    """
    plain = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    require('\x1b' not in plain and '\x9b' not in plain,
            'unsupported or truncated terminal escape')
    require(re.search(r'\b(?:CRITICAL\s+ERROR|double\s+trap|PMA\s+check\s+failed)\b',
                      plain, re.I) is None, 'O2 fatal runtime output')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def safe_relative(name):
    require(isinstance(name,str) and name and "\\" not in name and ":" not in name,
            "unsafe portable path")
    p=PurePosixPath(name)
    require(not p.is_absolute() and not PureWindowsPath(name).drive and
            ".." not in p.parts and str(p)==name and "." not in p.parts,"unsafe portable path")
    return p

class Archive:
    """Validate every stored/raw byte pair, then serve decoded logical paths."""
    def __init__(self,path):
        self.path=Path(path)
        data=(self.path/"archive-manifest.json").read_bytes()
        hash_text=(self.path/"archive-manifest.sha256").read_text(encoding="ascii")
        require(re.fullmatch(r"[0-9a-f]{64}  archive-manifest\.json\n",hash_text) is not None,
                "invalid archive manifest digest record")
        require(digest(data)==hash_text.split()[0],"archive manifest hash mismatch")
        self.manifest=json.loads(data.decode("utf-8"))
        require(self.manifest.get("version")==1 and isinstance(self.manifest.get("files"),list),
                "unsupported archive manifest")
        self.manifest_sha256=digest(data)
        self.records={}
        stored_paths=set()
        for record in self.manifest["files"]:
            stored=safe_relative(record["stored"])
            require(stored.parts[0]=="files" and len(stored.parts)>1,"stored path outside files/")
            require(str(stored) not in stored_paths,"duplicate stored archive path")
            stored_paths.add(str(stored))
            require(record["encoding"] in ("identity","gzip"),"unknown archive encoding")
            logical=str(stored.relative_to("files"))
            if record["encoding"]=="gzip":
                require(logical.endswith(".gz"),"gzip record must use .gz suffix")
                logical=logical[:-3]
            require(logical not in self.records,"duplicate decoded archive path")
            self.records[logical]=record
            self.raw(logical)
        actual=set()
        for p in (self.path/"files").rglob("*"):
            require(not p.is_symlink(),"archive contains symlink")
            if p.is_file():
                actual.add(p.relative_to(self.path).as_posix())
        require(actual==stored_paths,"missing or unexpected archive file")
        self.bytes_result=dict(files=len(stored_paths),
            raw_bytes=sum(r["raw_bytes"] for r in self.records.values()),
            stored_bytes=sum(r["stored_bytes"] for r in self.records.values()),
            archive_manifest_sha256=self.manifest_sha256)

    def raw(self,logical):
        safe_relative(logical)
        require(logical in self.records,"archive missing: "+logical)
        r=self.records[logical]
        p=self.path.joinpath(*PurePosixPath(r["stored"]).parts)
        require(p.resolve().is_relative_to(self.path.resolve()),"archive path resolves outside archive")
        require(not p.is_symlink(),"archive symlink")
        stored=p.read_bytes()
        for key in ("stored_bytes","raw_bytes"):
            require(type(r[key]) is int and r[key]>=0,"invalid byte length")
        require(len(stored)==r["stored_bytes"] and digest(stored)==r["stored_sha256"],
                "stored-byte mismatch: "+logical)
        raw=gzip.decompress(stored) if r["encoding"]=="gzip" else stored
        require(len(raw)==r["raw_bytes"] and digest(raw)==r["raw_sha256"],
                "raw-byte mismatch: "+logical)
        return raw

    def json(self,logical):
        return json.loads(self.raw(logical).decode("utf-8"))

    def tool(self,relative,expected_sha):
        safe_relative(relative)
        require(re.fullmatch(r"[0-9a-f]{64}",expected_sha) is not None,"invalid checker SHA")
        matches=[name for name,r in self.records.items()
                 if (name==relative or name.endswith("/"+relative)) and r["raw_sha256"]==expected_sha]
        require(matches,"sealed checker not found with pinned hash: "+relative)
        raw=self.raw(sorted(matches)[0])
        # The caller deliberately executes this archive's pinned checker source.
        # It is an audit of a trusted local export, not a third-party code sandbox.
        name="_o2_portable_"+expected_sha
        module=types.ModuleType(name)
        module.__file__="archive://"+matches[0]
        sys.modules[name]=module
        exec(compile(raw,module.__file__,"exec"),module.__dict__)
        return module


def source_pin(artifacts,suffix):
    values=[v for k,v in artifacts.items() if k.endswith("/"+suffix)]
    require(len(values)==1,"missing/ambiguous original checker pin: "+suffix)
    return values[0]

def load_source(root,relative,artifacts,name):
    p=root/relative
    require(p.is_file() and digest(p.read_bytes())==source_pin(artifacts,relative),"archived checker source changed")
    spec=importlib.util.spec_from_file_location(name,p)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def validate_inventory(records,modes,names):
    expected={(m,n,0) for m in modes for n in names}
    expected|={(m,"performance-d0-s02",q) for m in modes for q in (1,2)}
    actual=[(r["mode"],r["image"],r["replay"]) for r in records]
    require(len(actual)==36 and set(actual)==expected,"incorrect/duplicate paired job inventory")


def original_linux_emu_path(product_directory):
    """Path constants become WindowsPath on native replay; keep original POSIX identity."""
    return str(PurePosixPath(str(product_directory).replace(chr(92), "/")) / "emu")


def validate_runtime_binding(record,runtime,pins,artifacts,inputs,emulator_path=None):
    require(record["command"]==runtime["command"] and record["files"]==runtime["files"],"runtime binding differs")
    c=record["command"]
    require(len(c)==13 and c[0]=="timeout" and c[2:5]==["stdbuf","-o0","-e0"] and c[6]=="-i"
            and c[9]=="--ram-size=128MB" and c[11:]==["--max-cycles=2000000","--seed=1"],"runtime option contract changed")
    require(c[8].startswith("--flash=") and c[10].startswith("--diff="),"runtime input option changed")
    flash,ref=c[8].split("=",1)[1],c[10].split("=",1)[1]
    require(c[5]==(emulator_path if emulator_path is not None else pins["emu_path"]),"job/mode EMU path differs")
    image=inputs[record["image"]+"/vdot-perf.bin"]
    require(c[7]==image["original"],"runtime image path does not match frozen image identity")
    expected={c[5]:pins["emu_sha256"],c[7]:image["sha256"],
              flash:"a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994",ref:NORMAL_REFERENCE}
    require(record["files"]==expected and all(artifacts.get(k)==v for k,v in expected.items()),
            "runtime artifact identities differ")
    return ref


CORPUS_FILES={"team/models/vdot/data/directed.jsonl","team/models/vdot/data/random.jsonl"}

def load_corpus_support(archive_path,tools,revision):
    """Restore only the two Git-bound data inputs used by frozen regeneration."""
    root=Path(archive_path)
    manifest=root/"support-manifest.json";checksum=root/"support-manifest.sha256"
    require(manifest.is_file() and checksum.is_file(),"missing frozen functional corpus support")
    body=manifest.read_bytes()
    require(checksum.read_text(encoding="ascii")==digest(body)+"  support-manifest.json\n","corpus manifest hash mismatch")
    data=json.loads(body.decode("utf-8"))
    require(data.get("version")==1 and data.get("source_revision")==revision and
            set(data.get("files",{}))==CORPUS_FILES,"corpus revision or exact inventory mismatch")
    actual=set()
    for p in (root/"support").rglob("*"):
        require(not p.is_symlink(),"corpus support symlink")
        if p.is_file():actual.add(p.relative_to(root/"support").as_posix())
    require(actual==CORPUS_FILES,"extra/missing corpus support file")
    for rel,item in data["files"].items():
        safe_relative(rel)
        p=root/"support"/Path(*PurePosixPath(rel).parts)
        raw=p.read_bytes()
        require(len(raw)==item["bytes"] and digest(raw)==item["sha256"],"corpus raw-byte mismatch")
        oid=hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()
        require(oid==item["git_blob"],"corpus Git blob mismatch")
        target=tools/Path(*PurePosixPath(rel).parts)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    return dict(files=2,bytes=sum(x["bytes"] for x in data["files"].values()),
                source_revision=revision,manifest_sha256=digest(body))

def audit(path,campaign):
    archive=Archive(path)
    safe_relative(campaign);require(len(PurePosixPath(campaign).parts)==1,"campaign must be one directory")
    with tempfile.TemporaryDirectory(prefix="o1-o2-audit-") as td:
        stage=Path(td)
        # Decode only campaign, frozen input snapshots and required tools.
        prefixes=("runs/"+campaign+"/","runs/portable-inputs/")
        for logical in sorted(archive.records):
            if logical.startswith(prefixes):
                dest=stage/Path(*PurePosixPath(logical).parts)
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.raw(logical))
        run=stage/"runs"/campaign
        artifacts=json.loads((run/"artifact-pins.json").read_text(encoding="utf-8"))
        tools=run/"checker-snapshots"
        original_state=json.loads((run/"state.json").read_text(encoding="utf-8"))
        corpus=load_corpus_support(path,tools,original_state["source_commit"])
        perf=tools/"team/optimizations/o2/result-width/h1/performance"
        sys.path.insert(0,str(perf))
        # compare imports its same-directory helper; bind that helper first.
        profile=load_source(tools,"team/optimizations/o2/result-width/h1/performance/build_profile.py",artifacts,"build_profile")
        compare=load_source(tools,"team/optimizations/o2/result-width/h1/performance/compare.py",artifacts,"g4_portable_compare")
        check=load_source(tools,"team/workloads/unified-vdot/check.py",artifacts,"g4_portable_windows")
        observers={
            "b0":load_source(tools,"team/optimizations/o2/fullcore/analyze.py",artifacts,"paired_portable_b0"),
            "h1":load_source(tools,"team/optimizations/o2/fullcore/analyze.py",artifacts,"paired_portable_h1")}
        gate=load_source(tools,"team/optimizations/o1/audit/runtime_gate.py",artifacts,"g4_portable_gate")
        fatal=load_source(tools,"team/optimizations/o2/fullcore/workloads/check.py",artifacts,"g4_portable_fatal")
        result=json.loads((run/"result.json").read_text(encoding="utf-8"))
        require(result["status"]=="B0_H1_PAIRED_PERFORMANCE_PASS","unaccepted original campaign")
        records=result["runs"];validate_inventory(records,compare.MODES,compare.expected_names())
        pins={m:json.loads((run/(m+"-hardware-pins.json")).read_text(encoding="utf-8")) for m in compare.MODES}
        compare.validate_pair(pins["b0"],pins["h1"])
        build=json.loads((run/"build-profile.json").read_text(encoding="utf-8"))
        require(build["status"]=="B0_H1_BUILD_PROFILE_PASS", "unaccepted build comparison")
        expected_paths={"b0":original_linux_emu_path(profile.B0_PRODUCTS),"h1":pins["h1"]["emu_path"]}
        require(build["emulator_paths"]==expected_paths, "build execution paths changed")
        for mode in compare.MODES:
            require(digest((run/(mode+"-hardware-pins.json")).read_bytes())==profile.PIN_SHA[mode],
                    "unaccepted original build pins")
            require(pins[mode]["emu_sha256"]==profile.EMU_SHA[mode]
                    and pins[mode]["source_commit"]==profile.SOURCE_COMMITS[mode],
                    "build source/binary mismatch")
        inputs=stage/"runs/portable-inputs"
        inp=json.loads((inputs/"input-manifest.json").read_text(encoding="utf-8"))
        require(inp["status"]=="FROZEN_INPUT_SNAPSHOT_PASS" and len(inp["files"])==209,"incomplete frozen portable inputs")
        for relative,item in inp["files"].items():
            safe_relative(relative)
            require(digest((inputs/"ours"/relative).read_bytes())==item["sha256"]==artifacts[item["original"]],
                    "frozen workload snapshot changed")
        require(inp["images"]==compare.expected_names(),"portable image inventory changed")
        all_samples=[];count=0
        actual={p.parent for p in run.glob("*/*/*/result.json")}
        declared={run/r["mode"]/r["stage"]/(r["image"]+f'-r{r["replay"]}') for r in records}
        require(actual==declared,"extra/missing archived run directory")
        for record in records:
            mode,image,replay=record["mode"],record["image"],record["replay"]
            directory=run/mode/record["stage"]/(image+f"-r{replay}")
            require(json.loads((directory/"result.json").read_text())==record,"job/campaign receipt differs")
            runtime=json.loads((directory/"runtime.json").read_text())
            require(record["status"]=="PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS" and record["exit_code"]==0,
                    "unaccepted original job")
            require((directory/"exit-code.txt").read_bytes()==b"0\n","actual exit file differs")
            reference=validate_runtime_binding(record,runtime,pins[mode],artifacts,inp["files"],expected_paths[mode])
            command=record["command"]
            for name in ("stdout.log","stderr.log"):
                require(digest((directory/name).read_bytes())==record["raw_sha256"][name],"raw stream changed")
            # Match the original Linux universal-newline view.
            stdout=(directory/"stdout.log").read_text(encoding="utf-8")
            stderr=(directory/"stderr.log").read_text(encoding="utf-8")
            for text in (stdout,stderr):
                fatal.reject_fatal_output(text);gate.validate_failure_markers(text)
            compare.validate_loaded_reference(stderr+stdout,reference,gate.normalize_console)
            windows=check.verify(inputs/"ours"/image,directory,external=artifacts)
            require(windows==json.loads((directory/"window-result.json").read_text()),"architectural/counter replay differs")
            analysis=observers[mode].analyze(stderr+stdout)
            require(json.loads(json.dumps(analysis))==json.loads((directory/"observation.json").read_text()),
                    "protocol observation replay differs")
            compare.observer_gate(mode,analysis,record["expected_vdot_commits"])
            require(record["observation_counts"]==analysis["counts"],"stored protocol counts differ")
            fresh=[dict(s,mode=mode,stage=record["stage"],replay=replay,image=image,image_sha256=windows["image_sha256"]) for s in windows["samples"]]
            require(fresh==record["samples"],"stored samples differ")
            all_samples+=fresh;count+=len(fresh)
        compare.compare_replays(records)
        require(count==478 and all_samples==result["samples"],"global sample inventory differs")
        stats=compare.summarize(all_samples)
        require(stats==result["rows"],"derived statistics differ")
        deltas=compare.paired_deltas(all_samples)
        require(len(deltas)==96 and deltas==result["paired_measured_windows"],"paired window deltas differ")
        nonregression=all(s["delta_cycles"]<=0 for s in deltas)
        equal=all(s["delta_cycles"]==0 for s in deltas)
        require(nonregression==result["cycle_nonregression_pass"]
                and equal==result["exact_measured_cycle_equality"],"cycle verdict differs")
        return dict(status="ARCHIVE_B0_H1_WINDOWS_RECHECK_PASS",
                    matched_formal_pairs=96, cycle_nonregression_pass=nonregression,
                    exact_measured_cycle_equality=equal,
                    regressions=[s for s in deltas if s["delta_cycles"]>0],archive=archive.bytes_result,corpus_support=corpus,
                    jobs=36,windows=478,measured_windows=192,replay_jobs=4,rows=stats,new_emu_run=False,
                    linux_git_toolchain_dependency_provenance_rechecked=False,
                    scope="all sealed bytes, original raw/exit identities, exact architectural and calibrated counter windows, both observer protocols, replay determinism and paired statistics; no new EMU/NEMU or Linux provenance run")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--campaign",default="campaign-01")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(),"output already exists")
    data=audit(args.archive,args.campaign)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k!="rows"},indent=2))
if __name__=="__main__":main()
