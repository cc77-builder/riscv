"""Generate, build and inspect source-bound O3 application images."""
import argparse
import hashlib
import importlib.util
import json
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import generate as gen

ROOT = gen.ROOT
HERE = Path(__file__).resolve().parent
AM = Path("/home/riscv/riscv-lab/t13-performance-20261015/deps/nexus-am")

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, v):
    Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def now():
    return datetime.now(timezone.utc).isoformat()
def load(name, p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def build(root, suite, dataset, shard):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    gen.generate(root/"data",suite,dataset,shard,8)
    (root/"source").mkdir()
    paths=[*HERE.glob("*.py"),HERE/"main.c",HERE/"Makefile",HERE/"fixed-layout.ld",HERE/"CONTRACT.md",
           ROOT/"team/workloads/unified-vdot/generate.py",ROOT/"team/workloads/unified-vdot/check.py"]
    software={}
    for path in paths:
        software[path.relative_to(ROOT).as_posix()]=sha(path)
        target=root/"source"/path.name if path.parent==HERE else root/"source"/"renderer"/path.name
        target.parent.mkdir(exist_ok=True);shutil.copy2(path,target)
    command=["bash","-c","source team/scripts/activate.sh\nexport AM_HOME="+shlex.quote(str(AM))+
             "\nmake -C team/workloads/o3-gemv ARCH=riscv64-xs MARCH=rv64gcv T13_DATA="+shlex.quote(str(root/"data"))+
             " T13_OBJ_ROOT="+shlex.quote(str(root/"objects"))+" BINARY="+shlex.quote(str(root/"vdot-perf"))+" -j1"]
    value=dict(source=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
               command=command,started=now(),software=software,
               am_revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=AM,text=True).strip())
    with (root/"stdout.log").open("wb") as a,(root/"stderr.log").open("wb") as b:
        value["exit_code"]=subprocess.run(command,cwd=ROOT,stdout=a,stderr=b).returncode
    value["finished"]=now()
    save(root/"build.json",value)
    if value["exit_code"]:raise ValueError("build failed: "+str(root))
    value["artifacts"]={name:sha(root/name) for name in ("vdot-perf.elf","vdot-perf.bin")}
    value["artifacts"]["manifest.json"]=sha(root/"data/manifest.json")
    save(root/"build.json",value)
    c=load("o3_original_elf_checker",ROOT/"team/workloads/unified-vdot/check.py")
    manifest=json.loads((root/"data/manifest.json").read_text())
    c.verify_generation(root,manifest);c.check_compiled_cases(root/"vdot-perf.elf",manifest)
    kernels=c.elf_kernels(root/"vdot-perf.elf")
    counts=[]
    for index,row in enumerate(manifest["rows"]):
        walked=c.walk(kernels[index])
        custom=sum(w&manifest["custom_mask"]==manifest["custom_match"] for _,w in walked)
        if custom!=(row["dots"] if row["method"]=="vdot" else 0):raise ValueError("ELF dot count")
        counts.append(dict(id=row["id"],machine_instructions=len(walked),custom_instructions=custom))
    save(root/"elf-audit.json",dict(status="O3_COMPILED_INPUT_OUTPUT_AND_EXACT_WINDOW_PASS",kernels=counts))
    return dict(name=root.name,path=str(root),suite=suite,dataset=dataset,shard=shard,m=manifest["m"],k=manifest["k"],scope=manifest["scope"])

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    images=[]
    for suite,dataset,shard in [("smoke",0,s) for s in (0,7)]+[("performance",d,s) for d in range(3) for s in range(8)]:
        name=f"{suite}-d{dataset}-s{shard:02d}"
        images.append(build(a.output/name,suite,dataset,shard));print(name,"O3_BUILD_PASS",flush=True)
    save(a.output/"images.json",dict(images=images,count=len(images)))
