"""Sequential local verification then parent PPA; never starts fullcore."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
WORK=Path("/home/riscv/riscv-lab/o2-c1-owner-20261025")
ROOT=WORK/"repo"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.datetime.now().astimezone().isoformat()
def save(p,x):
    tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(json.dumps(x,indent=2)+"\n");tmp.replace(p)
def main():
    assert not (WORK/"campaign.json").exists()
    files={}
    def track(repo):
        for name in subprocess.check_output(["git","ls-files","-z"],cwd=repo).split(b"\0"):
            if not name:continue
            p=repo/name.decode()
            if p.is_file(): files[str(p)]=sha(p)
        for line in subprocess.check_output(["git","ls-tree","HEAD"],cwd=repo,text=True).splitlines():
            if line.startswith("160000"):
                name=line.split("\t")[1];sub=repo/name
                assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=sub,text=True).strip()==line.split()[2]
                assert not subprocess.check_output(["git","status","--porcelain=v1"],cwd=sub,text=True).strip(),str(sub)
                track(sub)
    track(ROOT)
    files[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    tools=Path("/home/riscv/riscv-lab/o4-cost-20261020")
    ident=json.loads((tools/"tools/executable-identities.json").read_text())
    for n,x in ident.items():
        path=tools/"tools/root/usr/bin"/n
        assert sha(path)==x["sha256"]
        files[str(path)]=x["sha256"];files.update(x["shared_library_sha256"])
    files[str(tools/"library/NangateOpenCellLibrary_typical.lib")]=sha(tools/"library/NangateOpenCellLibrary_typical.lib")
    save(WORK/"inputs.json",files)
    def unchanged():
        for path,h in files.items():assert sha(Path(path))==h,path
    unchanged()
    state=dict(status="running",started=stamp(),steps=[],candidate_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip())
    save(WORK/"campaign.json",state)
    commands=[
      ("parent-host",["python3","-B","-m","unittest","discover","-s","team/optimizations/o2/parent","-v"]),
      ("fu-host",["python3","-B","-m","unittest","discover","-s","team/optimizations/o2","-p","test_negative_fu.py","-v"]),
      ("fu",["python3","-B","team/optimizations/o2/run_rtl.py","fu",str(WORK/"fu-01")]),
      ("parent",["python3","-B","team/optimizations/o2/run_rtl.py","parent",str(WORK/"parent-01")]),
      ("parent-replay",["python3","-B","team/optimizations/o2/parent/check_trace.py","--log",str(WORK/"parent-01/result.log"),"--output",str(WORK/"parent-replay.json")]),
      ("parent-generate",["python3","-B","team/optimizations/o4/elaborate.py","o2","parent",str(WORK/"parent-cost-01")]),
      ("parent-map",["python3","-B","team/optimizations/o4/synthesize.py",str(WORK/"parent-cost-01"),str(WORK/"parent-map-01"),"--work",str(tools)]),
      ("parent-sta",["python3","-B","team/optimizations/o4/timing.py",str(WORK/"parent-map-01"),str(WORK/"parent-sta-01"),"--work",str(tools)])]
    try:
        for label,cmd in commands:
            unchanged()
            x=dict(label=label,command=cmd,cwd=str(ROOT),started=stamp(),status="running")
            state["steps"].append(x);save(WORK/"campaign.json",state)
            print("START",label,flush=True)
            with (WORK/(label+".log")).open("xb") as f:
                process=subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONUNBUFFERED="1",JAVA_OPTS="-Xmx12G -Xss16m",BUILD_JOBS="2"))
                x["pid"]=process.pid;save(WORK/"campaign.json",state)
                rc=process.wait()
            x.update(exit_code=rc,finished=stamp(),status="passed" if rc==0 else "failed")
            save(WORK/"campaign.json",state)
            assert rc==0,label+" failed; inspect preserved log"
            unchanged()
            print("PASS",label,flush=True)
        state.update(status="LOCAL_AND_STANDARD_PPA_COMPLETE_AWAIT_SCREEN",finished=stamp())
        save(WORK/"campaign.json",state)
    except BaseException as e:
        state.update(status="failed",error=repr(e),finished=stamp());save(WORK/"campaign.json",state);raise
if __name__=="__main__":main()
