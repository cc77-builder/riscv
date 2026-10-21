"""Cross-platform archive-byte and O2 trace replay, using only Python's stdlib.

This does not execute EMU/NEMU, rebuild hardware, revalidate Linux Git/input
provenance, repeat every architectural workload check, or measure G4 performance.
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

def tool_pin(preflight,suffix):
    matches=[v for k,v in preflight.get("driver_files",{}).items() if k.endswith("/"+suffix)]
    require(len(matches)==1,"missing or ambiguous checker pin: "+suffix)
    return matches[0]

def text_view(raw):
    # The live drivers used Path.read_text(), i.e. universal-newline decoding.
    # Match that view while preserving independent raw stream SHA checks.
    return io.TextIOWrapper(io.BytesIO(raw),encoding="utf-8",newline=None).read()

def campaign_inputs(archive,campaign):
    require(len(safe_relative(campaign).parts)==1,"campaign must be a single directory name")
    prefix="runs/"+campaign
    preflight=archive.json(prefix+"/preflight.json")
    pin_raw=archive.raw(prefix+"/hardware-pins.json")
    pins=json.loads(pin_raw)
    require(preflight["hardware_pins_sha256"]==digest(pin_raw),"campaign hardware pins changed")
    require(preflight["emu_sha256"]==pins["emu_sha256"],"campaign EMU identity mismatch")
    parser=archive.tool(PARSER,tool_pin(preflight,PARSER))
    gate=archive.tool(RUNTIME_GATE,tool_pin(preflight,RUNTIME_GATE))
    return preflight,pins,parser,gate

def audit_job(archive,campaign,name,preflight,pins,parser,gate):
    prefix="runs/"+campaign+"/"+name
    record=archive.json(prefix+"/result.json")
    require(record.get("name")==name,"job identity mismatch")
    raw_logs={key:archive.raw(prefix+"/"+key) for key in ("stdout.log","stderr.log","run.log")}
    require(record.get("raw_logs_sha256")=={key:digest(raw) for key,raw in raw_logs.items()},
            "job raw stream receipt mismatch: "+name)
    require(raw_logs["run.log"]==raw_logs["stderr.log"]+raw_logs["stdout.log"],
            "derived transcript is not exact stderr + stdout: "+name)
    rc_raw=archive.raw(prefix+"/exit-code.txt")
    require(re.fullmatch(rb"-?[0-9]+\n",rc_raw) is not None,"malformed exit-code file")
    rc=int(rc_raw)
    require(type(record.get("exit_code")) is int and record["exit_code"]==rc,"exit-code receipt mismatch")
    command=record.get("command")
    require(isinstance(command,list) and len(command)==12 and
            command[:1]==["timeout"] and command[2:5]==["stdbuf","-o0","-e0"] and command[6]=="-i" and
            command[8].startswith("--flash=") and command[9]=="--ram-size=128MB" and
            command[10].startswith("--diff=") and command[11]=="--max-cycles=5000000",
            "unexpected emulator command")
    reference=command[10].split("=",1)[1]
    expected_ref=NEGATIVE_REFERENCE if name=="negative-vdot" else NORMAL_REFERENCE
    require(record["files"].get(reference)==expected_ref and
            preflight.get("input_files",{}).get(reference)==expected_ref,"reference identity receipt mismatch")
    require(record["files"].get(command[5])==pins["emu_sha256"],"job EMU identity mismatch")
    text=text_view(raw_logs["run.log"])
    reject_fatal_output(text)
    normalized=gate.normalize_console(text)
    require("The first instruction of core 0 has commited. Difftest enabled." in text,
            "missing real DiffTest runtime banner")
    loaded=re.findall(r"The reference model is ([^\r\n]+)",normalized)
    require([v.strip() for v in loaded]==[reference],"loaded reference differs from command")
    negative=name=="negative-vdot"
    if negative:
        gate.validate_negative(text,rc)
    else:
        require(rc==0,"normal job nonzero exit code")
        gate.validate_failure_markers(text)
        require(normalized.count("HIT GOOD TRAP")==1,"normal job missing unique GOOD TRAP")
    observation=parser.analyze(text,require_complete=not negative)
    wanted="O2_PARTIAL_TRACE_AUDIT" if negative else "O2_TRACE_PASS"
    require(observation["status"]==wanted,"wrong trace scope")
    # JSON normalization preserves the exact persisted schema for keys/histograms.
    canonical=json.loads(json.dumps(observation))
    require(archive.json(prefix+"/observation.json")==canonical,"cached observation differs from raw replay")
    require(record.get("observation_status")==wanted and
            record.get("observation_counts")==observation["counts"],"job trace verdict differs from replay")
    if not negative:
        require(observation["pending_count"]==0 and observation["pending_div_count"]==0 and
                observation["unfinished_rob_count"]==0,"normal job did not drain")
    return dict(name=name,recorded_job_status=record.get("status"),exit_code=rc,
                observation_status=wanted,counts=observation["counts"],
                raw_sha256=digest(raw_logs["run.log"]),text_view_sha256=digest(text.encode()),
                input_sha256=observation["input_sha256"],
                negative_scope="intentional bit100 rejection; partial trace only" if negative else None)

def audit(archive_path,core_campaign,supplement_campaign):
    require(core_campaign!=supplement_campaign,"core and supplement campaign must differ")
    archive=Archive(archive_path)
    records=[]
    identities=[]
    for campaign,expected in ((core_campaign,CORE_JOBS),(supplement_campaign,SUPPLEMENT_JOBS)):
        preflight,pins,parser,gate=campaign_inputs(archive,campaign)
        identities.append((pins,tool_pin(preflight,PARSER),tool_pin(preflight,RUNTIME_GATE)))
        result=archive.json("runs/"+campaign+"/result.json")
        require(isinstance(result.get("runs"),list) and len(result["runs"])==len(expected) and
                {r.get("name") for r in result["runs"]}==expected,"campaign job inventory mismatch")
        names={name.split("/")[2] for name in archive.records
               if name.startswith("runs/"+campaign+"/") and name.endswith("/result.json")
               and len(name.split("/"))==4}
        require(names==expected,"extra or missing sealed job result")
        for name in sorted(expected):
            record=archive.json("runs/"+campaign+"/"+name+"/result.json")
            require([r for r in result["runs"] if r.get("name")==name]==[record],
                    "campaign and job receipts disagree")
            records.append(audit_job(archive,campaign,name,preflight,pins,parser,gate))
    require(identities[0]==identities[1],"campaigns used different hardware or trace checkers")
    return dict(status="ARCHIVE_BYTES_AND_TRACE_AUDIT",archive=archive.bytes_result,
                core_campaign=core_campaign,supplement_campaign=supplement_campaign,
                jobs=len(records),complete_traces=sum(r["observation_status"]=="O2_TRACE_PASS" for r in records),
                partial_negative_traces=sum(r["observation_status"]=="O2_PARTIAL_TRACE_AUDIT" for r in records),
                emu_sha256=identities[0][0]["emu_sha256"],runs=records,new_emu_run=False,
                new_nemu_run=False,linux_git_and_input_provenance_rechecked=False,
                architectural_workload_checks_repeated=False,performance_measured=False,
                scope="All archived stored/raw bytes, original exit/log identities, normal failure gates, bit100 negative chain, and exact O2 trace replay only")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--core-campaign",required=True)
    parser.add_argument("--supplement-campaign",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(),"output already exists")
    result=audit(args.archive,args.core_campaign,args.supplement_campaign)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="runs"},indent=2))

if __name__=="__main__":
    main()
