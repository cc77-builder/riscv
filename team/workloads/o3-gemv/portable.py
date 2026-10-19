"""Native offline O3 replay: archive bytes, math/state/counters/protocol/statistics."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

def require(ok,msg):
    if not ok:raise ValueError(msg)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(archive,output):
    archive=Path(archive)
    manifest=json.loads((archive/"archive-manifest.json").read_text(encoding="utf-8"))
    require(sha(archive/"archive-manifest.json")==(archive/"archive-manifest.sha256").read_text().split()[0],"manifest digest")
    originals=set();stored_names=set()
    with tempfile.TemporaryDirectory(prefix="o3-offline-") as temp:
        work=Path(temp)/"work";checkout=Path(temp)/"checkout";work.mkdir();checkout.mkdir()
        for rec in manifest["files"]:
            rel=PurePosixPath(rec["stored"])
            require(not rel.is_absolute() and ".." not in rel.parts and rel.as_posix() not in stored_names,"archive path")
            stored_names.add(rel.as_posix())
            stored=(archive/Path(*rel.parts)).read_bytes()
            require(len(stored)==rec["stored_bytes"] and hashlib.sha256(stored).hexdigest()==rec["stored_sha256"],"stored hash")
            require(rec["encoding"] in ("gzip","identity"),"encoding")
            raw=gzip.decompress(stored) if rec["encoding"]=="gzip" else stored
            require(len(raw)==rec["raw_bytes"] and hashlib.sha256(raw).hexdigest()==rec["raw_sha256"],"raw hash")
            prefix=manifest["work_root"]+"/"
            if rec["original"].startswith(prefix):
                name=PurePosixPath(rec["original"][len(prefix):])
                require(not name.is_absolute() and ".." not in name.parts and name.as_posix() not in originals,"original path")
                originals.add(name.as_posix());target=work/Path(*name.parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        require({p.relative_to(archive).as_posix() for p in (archive/"files").rglob("*") if p.is_file()}==stored_names,"unexpected archive files")
        campaign=work/"campaign-01"
        pins=json.loads((campaign/"artifact-pins.json").read_text(encoding="utf-8"))
        state=json.loads((campaign/"state.json").read_text(encoding="utf-8"))
        require(state["status"]=="O3_PAIRED_APPLICATION_CAMPAIGN_PASS","incomplete campaign")
        source=campaign/"source"
        for path in source.rglob("*"):
            if not path.is_file():continue
            rel=path.relative_to(source)
            key=next((k for k in pins if k.endswith("/"+rel.as_posix())),None)
            require(key is not None and sha(path)==pins[key],"source pin "+rel.as_posix())
            target=checkout/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        sys.path.insert(0,str(checkout/"team/workloads/o3-gemv"))
        c=load("o3_portable_runtime_campaign",checkout/"team/workloads/o3-gemv/campaign.py")
        gate=c.load("o3_portable_runtime_gate",checkout/"team/optimizations/o1/audit/runtime_gate.py")
        fatal=c.load("o3_portable_fatal",checkout/"team/optimizations/o2/fullcore/workloads/check.py")
        obs={m:c.load("o3_portable_observer_"+m,checkout/("team/optimizations/"+m+"/fullcore/analyze.py")) for m in ("o1","o2")}
        aggregate=json.loads((campaign/"result.json").read_text(encoding="utf-8"))
        indexed={(r["mode"],r["image"],r["replay"]):r for r in aggregate["runs"]}
        require(len(indexed)==56,"aggregate run count")
        paths=sorted([*campaign.glob("o1/*/result.json"),*campaign.glob("o2/*/result.json")])
        require(len(paths)==56,"raw run inventory")
        records=[];windows=0
        for path in paths:
            directory=path.parent;r=json.loads(path.read_text(encoding="utf-8"))
            require(r==indexed[(r["mode"],r["image"],r["replay"])],"aggregate/disk record")
            require(r["status"]=="O3_IMAGE_DIFFTEST_STATE_WINDOWS_AND_PROTOCOL_PASS" and r["exit_code"]==0,"failed run")
            require((directory/"exit-code.txt").read_text()=="0\n","actual exit receipt")
            runtime=json.loads((directory/"runtime.json").read_text(encoding="utf-8"))
            for key in ("mode","image","suite","shard","dataset","build","replay","command","cwd","started_utc","files"):
                require(runtime[key]==r[key],"runtime identity "+key)
            prefix=manifest["work_root"]+"/";require(r["build"].startswith(prefix),"foreign build")
            build=work/Path(*PurePosixPath(r["build"][len(prefix):]).parts)
            m=json.loads((build/"data/manifest.json").read_text(encoding="utf-8"))
            stdout=(directory/"stdout.log").read_text(encoding="utf-8");stderr=(directory/"stderr.log").read_text(encoding="utf-8")
            for stream in (stdout,stderr):fatal.reject_fatal_output(stream);gate.validate_failure_markers(stream)
            refs=[s.strip() for s in re.findall(r"The reference model is ([^\r\n]+)",gate.normalize_console(stderr+stdout))]
            reference=[k for k in r["files"] if k.endswith("/riscv64-nemu-interpreter-so")]
            require(refs==reference and len(refs)==1,"reference identity")
            result=c.check.verify(build,directory,external=pins)
            analysis=obs[r["mode"]].analyze(stderr+stdout)
            c.g4.observer_gate(r["mode"],analysis,c.g4.expected_commits(m))
            require(result==json.loads((directory/"windows.json").read_text(encoding="utf-8")),"saved windows")
            require(analysis==json.loads((directory/"observation.json").read_text(encoding="utf-8")),"saved protocol")
            samples=[]
            for item,entry in zip(result["samples"],m["plan"]):
                row=m["rows"][entry["index"]]
                samples.append(dict(item,mode=r["mode"],shard=r["shard"],software=row["software"],m=row["m"],k=row["k"],
                                    scope=row["scope"],image_sha256=sha(build/"vdot-perf.bin")))
            require(samples==r["samples"],"saved samples");records.append(r);windows+=len(samples)
        for mode in ("o1","o2"):
            rows=[r for r in records if r["mode"]==mode and r["image"]=="performance-d0-s05"]
            require(len(rows)==3 and {r["replay"] for r in rows}=={0,1,2},"replay inventory")
            base=next(r for r in rows if r["replay"]==0)
            for row in rows:
                require([(s["seq"],s["cycles"],s["instructions"]) for s in row["samples"]]==[(s["seq"],s["cycles"],s["instructions"]) for s in base["samples"]],"replay")
        stats=c.summarize(records)
        sealed=json.loads((work/"results-01/verification.json").read_text(encoding="utf-8"))
        require(sealed["status"]=="O3_RAW_EVIDENCE_RECHECK_PASS","Linux audit status")
        for key in ("rows","best_rvv_comparison"):
            require(stats[key]==aggregate[key]==sealed[key],"recomputed statistics "+key)
        require(windows==1280 and len(stats["measured_samples"])==768,"window count")
        result=dict(status="O3_NATIVE_OFFLINE_RECHECK_PASS",platform=sys.platform,jobs=56,windows=windows,
                    measured_windows=768,replay_jobs=4,archive_files=len(stored_names),archive_manifest_sha256=sha(archive/"archive-manifest.json"),
                    rows=stats["rows"],best_rvv_comparison=stats["best_rvv_comparison"],new_emu_run=False,
                    linux_git_compiler_dependency_provenance_rechecked=False,
                    scope="sealed raw bytes, source/image regeneration, full application/state gates, exact ELF/counter windows, both protocols, replay and statistics; no new EMU or Linux provenance run")
    with Path(output).open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
    print(json.dumps({k:result[k] for k in ("status","platform","jobs","windows","measured_windows")}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--archive",required=True,type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();audit(a.archive,a.output)
