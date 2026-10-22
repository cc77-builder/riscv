"""Check matched software build settings; never changes products or runs EMU."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[4]
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized_verilator(log,products):
    rows=[line for line in log.splitlines() if "verilator --exe " in line]
    require(len(rows)==1,"expected one real Verilator generation command")
    row=rows[0]
    require("--threads 1 " in row and "-O3 --cc" in row,"wrong simulator options")
    return row.replace(str(products),"<BUILD>")

def build_profile(o1_build,o2_build):
    o1_build,o2_build=Path(o1_build),Path(o2_build)
    b1=json.loads((o1_build/"build-state.json").read_text())
    b2=json.loads((o2_build/"build-state.json").read_text())
    require(b1["status"]=="O1_MATCHED_BUILD_PASS" and b2["status"]=="O2_FULLCORE_BUILD_PASS","build not complete")
    products={"o1":Path(b1["build_products"]),"o2":ROOT/"build"}
    dirs={"o1":o1_build,"o2":o2_build}
    files={}
    version_hashes={}
    for tool in ("java","mill","verilator","clang","make","python","firtool"):
        a,b=o1_build/(tool+"-version.log"),o2_build/(tool+"-version.log")
        require(a.read_bytes()==b.read_bytes(),"tool version differs: "+tool)
        files.update({str(a):sha(a),str(b):sha(b)})
        version_hashes[tool]=sha(a)
    commands={}
    for mode in ("o1","o2"):
        p=dirs[mode]/"emu-build.log";text=p.read_text()
        commands[mode]=normalized_verilator(text,products[mode])
        require('OPT_SLOW="-O0"' in text and "OPT_FAST=-O3" in text,"wrong C++ optimization")
        files[str(p)]=sha(p)
        for leaf in ("hardware-inputs.json","build-state.json"):
            p=dirs[mode]/leaf;files[str(p)]=sha(p)
    require(commands["o1"]==commands["o2"],"normalized Verilator/C++ settings differ")
    makefile=Path("/usr/local/share/verilator/include/verilated.mk")
    make_text=makefile.read_text()
    require(re.search(r"^CXX = clang\+\+$",make_text,re.M) is not None,"unexpected actual CXX rule")
    require('CFG_CXX_VERSION = "Ubuntu clang version 19.1.7' in make_text,"unexpected configured compiler")
    compiler=Path(subprocess.check_output(["bash","-c","source team/scripts/activate.sh\ncommand -v clang++"],cwd=ROOT,text=True).strip()).resolve()
    version=subprocess.check_output([str(compiler),"--version"],text=True)
    require("Ubuntu clang version 19.1.7" in version,"unexpected actual compiler version")
    files.update({str(makefile):sha(makefile),str(compiler):sha(compiler)})
    restore=o1_build/"original-build-restoration.json"
    require(json.loads(restore.read_text())["status"]=="ORIGINAL_O2_GENERATION_RESTORED","old G3 build not restored")
    files[str(restore)]=sha(restore)
    aux=json.loads((o1_build/"generated-auxiliary.json").read_text())
    for row in aux:
        require(sha(row["destination"])==row["sha256"],"staged O1 auxiliary changed")
        files[row["destination"]]=row["sha256"]
    return files,dict(status="MATCHED_O1_O2_BUILD_PROFILE_PASS",tool_version_sha256=version_hashes,
                      normalized_verilator_command=commands["o1"],compiler_path=str(compiler),
                      compiler_sha256=sha(compiler),compiler_version=version,
                      actual_compiler_source="same configured Verilator CXX rule, resolved activated clang++, and version",
                      common_optimization="OPT_FAST=-O3 OPT_SLOW=-O0",o1_auxiliary_files=len(aux),
                      original_o2_generation_restored=True,observer_flags_differ_by_mode=True)
