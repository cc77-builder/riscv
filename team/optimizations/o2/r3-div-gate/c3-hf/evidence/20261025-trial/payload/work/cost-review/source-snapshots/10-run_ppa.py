"""C2 immutable-input PPA campaign. Never builds fullcore."""
import argparse,datetime,hashlib,json,os,subprocess
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.datetime.now().astimezone().isoformat()
def save(p,x):
    tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(json.dumps(x,indent=2)+"\n");tmp.replace(p)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--source-repo",type=Path,required=True)
    a=p.parse_args()
    root=a.repo.resolve();work=a.work.resolve();main=a.source_repo.resolve()
    work.mkdir(exist_ok=True)
    assert not (work/"campaign.json").exists(),"new attempt required"
    state=dict(status="preflight",started=stamp(),steps=[])
    save(work/"campaign.json",state)
    pins={};deps=[]
    def pin(path):
        path=path.resolve();h=sha(path);pins[str(path)]=h;return h
    def unchanged():
        for name,h in pins.items():assert sha(Path(name))==h,"changed input "+name
    try:
        head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
        assert head=="6704ce3502a7235cdb81697638c01ed23f6914f6"
        assert not subprocess.check_output(["git","status","--porcelain=v1"],cwd=root,text=True).strip()
        assert pin(root/"src/main/scala/xiangshan/backend/exu/ExeUnit.scala")=="febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6"
        state["candidate_commit"]=head;save(work/"campaign.json",state)
        def track(repo,prefix=""):
            for name in subprocess.check_output(["git","ls-files","-z"],cwd=repo).split(b"\0"):
                if name:
                    path=repo/name.decode()
                    if path.is_file():pin(path)
            for entry in subprocess.check_output(["git","ls-tree","-rz","HEAD"],cwd=repo).split(b"\0"):
                if not entry:continue
                meta,name=entry.split(b"\t",1);mode,kind,expected=meta.decode().split()
                if mode!="160000":continue
                name=name.decode();sub=repo/name
                actual=subprocess.check_output(["git","rev-parse","HEAD"],cwd=sub,text=True).strip()
                clean=subprocess.check_output(["git","status","--porcelain=v1","--untracked-files=normal"],cwd=sub,text=True)
                assert actual==expected and not clean,(sub,actual,expected,clean)
                deps.append(dict(path=prefix+name,head=actual,pin=expected,status=clean))
                track(sub,prefix+name+"/")
        track(root)
        assert len(deps)==126
        tools=Path("/home/riscv/riscv-lab/o4-cost-20261020")
        tool_id=json.loads((tools/"tools/executable-identities.json").read_text())
        pin(tools/"tools/executable-identities.json")
        for name,meta in tool_id.items():
            assert pin(tools/"tools/root/usr/bin"/name)==meta["sha256"]
            for path,h in meta["shared_library_sha256"].items():assert pin(Path(path))==h
        assert pin(tools/"library/NangateOpenCellLibrary_typical.lib")=="8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1"
        baseline_manifest=main/"team/optimizations/o2/r3-div-gate/evidence/20261025-performance-cost/manifest.json"
        assert pin(baseline_manifest)=="9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77"
        original={x["path"]:x["raw_sha256"] for x in json.loads(baseline_manifest.read_text())["files"]}
        baseline_files=0
        for folder in ["parent-cost-01","parent-map-01","parent-sta-01"]:
            for path in sorted((a.baseline/folder).rglob("*")):
                if path.is_file():
                    assert pin(path)==original["cost/"+path.relative_to(a.baseline).as_posix()],str(path)
                    baseline_files+=1
        local=Path("/home/riscv/riscv-lab/o2-c2-readyless-20261025")
        local_manifest=main/"team/optimizations/o2/r3-div-gate/c2/evidence/20261025-local/manifest.json"
        assert pin(local_manifest)=="5fe7ea1cd978cf14ef371380a51e64d942673e1c62c7ac3748698418237b1428"
        old={x["path"]:x["raw_sha256"] for x in json.loads(local_manifest.read_text())["files"]}
        for rel in ["fu-02/runner.status.json","parent-01/runner.status.json","supplement-01/runner.status.json",
                    "final-audit/audit.json","rtl-review/final-review.json","parent-replay.json","supplement-01/supplement-replay.json"]:
            assert pin(local/rel)==old["work/"+rel]
        for stage in ["fu-02","parent-01","supplement-01"]:
            assert json.loads((local/stage/"runner.status.json").read_text())["passed"]
            for name,h in json.loads((local/stage/"source.json").read_text()).items():
                path=root/name
                assert pin(path)==h,name
        assert json.loads((local/"final-audit/audit.json").read_text())["status"]=="C2_FINAL_READONLY_AUDIT_PASS"
        pin(Path(__file__))
        pin(Path(__file__).parent/"CONTRACT.md")
        save(work/"inputs.json",pins);save(work/"dependencies.json",deps)
        save(work/"preflight.json",dict(status="C2_COST_PREFLIGHT_PASS",time=stamp(),source_inputs=len(pins),
                                      dependencies=len(deps),baseline_files=baseline_files,
                                      local_evidence_sha256=sha(local_manifest),baseline_manifest_sha256=sha(baseline_manifest)))
        unchanged()
        state["status"]="running";save(work/"campaign.json",state)
        jobs=[
          ("parent-generate",["python3","-B","team/optimizations/o4/elaborate.py","o2","parent",str(work/"parent-cost-01")]),
          ("parent-map",["python3","-B","team/optimizations/o4/synthesize.py",str(work/"parent-cost-01"),str(work/"parent-map-01"),"--work",str(tools)]),
          ("parent-sta",["python3","-B","team/optimizations/o4/timing.py",str(work/"parent-map-01"),str(work/"parent-sta-01"),"--work",str(tools)])]
        for label,cmd in jobs:
            unchanged()
            rec=dict(label=label,command=cmd,cwd=str(root),started=stamp(),status="running")
            state["steps"].append(rec);save(work/"campaign.json",state)
            print("START",label,flush=True)
            with (work/(label+".log")).open("xb") as f:
                proc=subprocess.Popen(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,
                    env=dict(os.environ,PYTHONUNBUFFERED="1",JAVA_OPTS="-Xmx12G -Xss16m",BUILD_JOBS="2"))
                rec["pid"]=proc.pid;save(work/"campaign.json",state);rc=proc.wait()
            rec.update(exit_code=rc,finished=stamp(),status="passed" if rc==0 else "failed")
            save(work/"campaign.json",state)
            assert rc==0,label+" failed; original attempt retained"
            unchanged();print("PASS",label,flush=True)
        state.update(status="C2_STANDARD_PPA_COMPLETE_AWAIT_SCREEN",finished=stamp())
        save(work/"campaign.json",state)
    except BaseException as exc:
        state.update(status="failed",error=repr(exc),finished=stamp());save(work/"campaign.json",state);raise
if __name__=="__main__":main()
