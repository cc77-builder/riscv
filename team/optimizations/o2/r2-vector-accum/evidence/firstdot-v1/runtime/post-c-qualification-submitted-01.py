from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,shutil,subprocess,sys
r=Path("/home/lizufan/riscv-lab/r2s1-firstdot-20261024-1458"); repo=r/"source"; mod=repo/"team/optimizations/o2/r2-vector-accum"
identity=Path("/home/lizufan/riscv-lab/t17-clean-20261024-0854/identity-02.json")
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open("x") as f: json.dump(v,f,indent=2); f.write("\n")
state=read(r/"c-run-01/state.json"); qual=read(r/"c-run-01/firstdot-qualification.json")
assert state["status"]=="R4_C_APPLICATION_CALLS_PASS" and state["active_pid"] is None and state["new_emu_runs"]==3 and state.get("finished")
assert qual["status"]=="FIRSTDOT_C_APPLICATION_CALLS_PASS"
ps=subprocess.check_output(["ps","-eo","pid,ppid,comm,pcpu,pmem"],text=True)
heavy=[x for x in ps.splitlines()[1:] if len(x.split())>2 and x.split()[2] in {"emu","cc1","cc1plus","verilator","verilator_bin","mill","java","make","ninja"}]
save(r/"resource-after-c-01.json",dict(created=now(),affinity=sorted(os.sched_getaffinity(0)),processes=ps,heavy=heavy,state=state))
assert not heavy and len(os.sched_getaffinity(0))<=4
readme_source=Path("/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/working-firstdot-20261024-1458/team/optimizations/o2/r2-vector-accum/FIRSTDOT_README.md"); readme_target=mod/"FIRSTDOT_README.md"
assert sha(readme_source)=="9a36ada73895a1e8cc609e706acf508e809dbf93f4dc00cee426e4b0297a6962"
assert sha(readme_target)=="62a759107fa40ff45086fc9c6644639b0b0dd9d24143b17d738e25b1781873e6"
with (r/"pre-usage-FIRSTDOT_README.md").open("xb") as f: f.write(readme_target.read_bytes())
readme_target.write_bytes(readme_source.read_bytes())
assert sha(readme_target)==sha(readme_source)
save(r/"source-transfer-07.json",dict(created=now(),scope="README only after C execution completed",source=str(readme_source),destination=str(readme_target),sha256=sha(readme_target)))
def command(label,argv,folder=r):
    out=folder/(label+".stdout.log"); err=folder/(label+".stderr.log"); driver=folder/(label+"-driver.json")
    assert not driver.exists()
    started=now()
    with out.open("xb") as so,err.open("xb") as se: result=subprocess.run(list(map(str,argv)),cwd=repo,stdout=so,stderr=se)
    receipt=dict(argv=list(map(str,argv)),cwd=str(repo),started=started,finished=now(),exit_code=result.returncode,stdout=str(out),stderr=str(err))
    save(driver,receipt)
    print(json.dumps(dict(label=label,**receipt,tail=out.read_text()[-2200:],errors=err.read_text()[-2200:])),flush=True)
    if result.returncode: sys.exit(result.returncode)
    return receipt
def run(label,script,args):
    return command(label,["taskset","-c","0-3","python3","-B",script,*args])
base=["--repo",repo,"--identity",identity,"--matrix",r/"matrix-archive-01"]
run("c-export-01",mod/"firstdot_c_api.py",[*base,"--action","export","--build",r/"c-build-01","--run",r/"c-run-01","--output",r/"qualified-public-01"])
dest=mod/"firstdot/public"; assert not dest.exists()
shutil.copytree(r/"qualified-public-01",dest)
copied={p.name:sha(p) for p in (r/"qualified-public-01").iterdir()}
assert copied=={p.name:sha(p) for p in dest.iterdir()}
save(r/"public-transfer-01.json",dict(created=now(),source=str(r/"qualified-public-01"),destination=str(dest),files=copied,identical=True))
run("c-pack-01",mod/"firstdot_c_evidence.py",[*base,"--action","pack","--build",r/"c-build-01","--run",r/"c-run-01","--archive",r/"c-archive-01"])
run("c-audit-01",mod/"firstdot_c_evidence.py",[*base,"--action","audit","--archive",r/"c-archive-01","--output",r/"c-audit-01.json"])
run("library-build-01",mod/"firstdot_library.py",[*base,"--action","build","--c-archive",r/"c-archive-01","--build",r/"c-build-01","--run",r/"c-run-01","--output",r/"library-01"])
run("c-library-host-01",mod/"test_firstdot_c_api.py",["--repo",repo,"--identity",identity,"--library",r/"library-01","--output",r/"c-library-host-01.json"])
usage=r/"usage-check-01"; usage.mkdir()
text=(mod/"FIRSTDOT_README.md").read_text()
blocks=re.findall(r"```c\n(.*?)\n```",text,re.S)
assert len(blocks)==2 and "void gemv8(" in blocks[1]
(usage/"app.c").write_text(blocks[1]+"\n")
receipt=read(r/"c-build-01/build.json"); compiler=receipt["toolchain"]["gcc"]; linker=receipt["toolchain"]["ld"]
assert sha(Path(compiler["path"]))==compiler["sha256"] and sha(Path(linker["path"]))==linker["sha256"]
commands=[]
commands.append(command("source-rebuild",[compiler["path"],"-march=rv64gcv","-mabi=lp64d","-mno-relax","-c",dest/"gemv.S","-o",usage/"rebuilt-gemv.o"],usage))
assert (usage/"rebuilt-gemv.o").read_bytes()==(r/"library-01/gemv.o").read_bytes()
commands.append(command("example-compile",[compiler["path"],"-std=c11","-march=rv64gcv","-mabi=lp64d","-mno-relax","-ffreestanding","-O2","-I"+str(dest),"-c",usage/"app.c","-o",usage/"app.o"],usage))
commands.append(command("example-link",[linker["path"],"-r","--no-relax",usage/"app.o",r/"library-01/libfirstdot_gemv.a","-o",usage/"app-firstdot.o"],usage))
sys.path.insert(0,str(mod))
import firstdot_gate as g
linked=g.ELF((usage/"app-firstdot.o").read_bytes()); original=g.ELF((r/"library-01/gemv.o").read_bytes())
names=read(r/"library-01/library.json")["public_symbols"]
undefined=[n for n,v in linked.symbols.items() if n and v[2]==0]
assert not undefined and linked.symbols["gemv8"][1]>0
assert all(linked.symbol_data(n)==original.symbol_data(n) for n in names)
report=dict(status="FIRSTDOT_README_EXAMPLE_COMPILE_LINK_AND_SOURCE_REBUILD_PASS",created=now(),readme_sha256=sha(mod/"FIRSTDOT_README.md"),
example_source_sha256=sha(usage/"app.c"),qualified_object_sha256=sha(usage/"rebuilt-gemv.o"),public_functions=16,linked_leaves_identical=True,
undefined_symbols=undefined,commands=commands,new_emu_runs=0,example_executed=False,performance_measured=False,
artifacts={p.name:sha(p) for p in usage.iterdir() if p.is_file()})
save(usage/"report.json",report)
print(json.dumps(report),flush=True)
summary=dict(c_state=state,qualification={k:v for k,v in qual.items() if k!="matrix_anchor"},c_audit=read(r/"c-audit-01.json"),
library=read(r/"library-01/library-check.json"),host=read(r/"c-library-host-01.json"),negative=read(r/"c-run-01/runs/negative/result.json")["negative_details"],
hashes={n:sha(r/n) for n in ("c-audit-01.json","c-archive-01/archive-manifest.json","library-01/library.json","library-01/library-check.json","c-library-host-01.json","usage-check-01/report.json")})
save(r/"c-final-summary-01.json",summary)
print(json.dumps(summary),flush=True)
