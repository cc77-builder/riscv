from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,shutil,subprocess,sys
r=Path("/home/lizufan/riscv-lab/r2s1-firstdot-20261024-1458"); repo=r/"source"; mod=repo/"team/optimizations/o2/r2-vector-accum"; dest=mod/"firstdot/public"
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open("x") as f: json.dump(v,f,indent=2); f.write("\n")
state=read(r/"c-run-01/state.json"); qual=read(r/"c-run-01/firstdot-qualification.json")
assert state["status"]=="R4_C_APPLICATION_CALLS_PASS" and state["active_pid"] is None
assert read(r/"library-01/library-check.json")["linked_c_entry_relocations"]==16
assert len(read(r/"c-library-host-01.json")["library"]["rehashed_corruptions"])==4
save(r/"usage-check-01-failure.json",dict(status="TRANSPORT_FAILURE_BEFORE_EXAMPLE_COMMANDS",original_receipt="1bcd341bbd2162e3d9e297ccd2678ca0.eb497a588ed874664b05e9b115184271",exit_code=1,library_and_host_checks_completed=True,example_commands_started=False,reason="Literal Markdown backticks in the WSL python -c payload were interpreted by the shell; regex assertion failed. Qualified C export/archive/library unchanged.",repair="Use a base64 transport envelope and a new usage-check-02 directory; no EMU or library rebuild."))
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
usage=r/"usage-check-02"; usage.mkdir()
text=(mod/"FIRSTDOT_README.md").read_text()
fence=chr(96)*3
blocks=re.findall(fence+"c\\n(.*?)\\n"+fence,text,re.S)
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
hashes={n:sha(r/n) for n in ("c-audit-01.json","c-archive-01/archive-manifest.json","library-01/library.json","library-01/library-check.json","c-library-host-01.json","usage-check-02/report.json")})
save(r/"c-final-summary-01.json",summary)
print(json.dumps(summary),flush=True)
