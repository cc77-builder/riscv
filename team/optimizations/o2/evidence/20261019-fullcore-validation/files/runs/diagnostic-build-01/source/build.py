"""Build a fresh external O2 diagnostic image with complete source receipts."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import generate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not args.output.is_absolute() or out.is_relative_to(ROOT):
        raise ValueError("output must be an absolute fresh directory outside checkout")
    out.mkdir(parents=True,exist_ok=False)
    manifest = generate.generate(out/"data")
    (out/"source").mkdir()
    for path in sorted(HERE.glob("*")):
        if path.is_file():
            shutil.copyfile(path,out/"source"/path.name)
    # Workload sources compile from the snapshot, so subsequent edits cannot
    # alter this image's receipt. nexus-am remains the pinned external runtime.
    cmd = ["make","-C",str(out/"source"),"ARCH=riscv64-xs","MARCH=rv64gcv",
           "O2_DATA="+str(out/"data"),"O2_OBJ_ROOT="+str(out/"objects"),
           "BINARY="+str(out/"o2-diag"),"-j2"]
    command = "source "+shlex.quote(str(ROOT/"team/scripts/activate.sh"))+"\n"+shlex.join(cmd)+"\n"
    (out/"build-command.sh").write_text(command)
    started = datetime.now().astimezone().isoformat()
    with (out/"build.log").open("wb") as log:
        rc=subprocess.run(["bash","-lc",command],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
    (out/"exit-code.txt").write_text(str(rc)+"\n")
    if rc:
        raise RuntimeError(f"build failed {rc}; see {out}/build.log")
    disassembly=(out/"o2-diag.txt").read_text()
    symbol_lines={m[2]:int(m[1],16) for m in re.finditer(r"^([0-9a-f]+) <([^>]+)>:$",disassembly,re.M)}
    instructions=[(int(m[1],16),int(m[2],16)) for m in re.finditer(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s",disassembly,re.M)]
    checked=[]
    for i,case in enumerate(manifest["cases"]):
        begin,end=symbol_lines[f"o2_diag_{i}_begin"],symbol_lines[f"o2_diag_{i}_end"]
        observed=[word for pc,word in instructions if begin<=pc<end and word&0x7f==0x0b]
        expected=[generate.word(op["d"],op["a"],op["b"]) for op in case["ops"] if op["op"]=="vdot"]
        if observed!=expected:
            raise ValueError("compiled vdot sequence differs: "+case["id"])
        checked.append(dict(id=case["id"],begin=hex(begin),end=hex(end),vdot_count=len(observed)))
    am=Path(os.environ.get("HOME","/home/riscv"))/"riscv-lab/xs-env/nexus-am"
    libs=[am/"am/build/am-riscv64-xs.a",am/"libs/klib/build/klib-riscv64-xs.a"]
    receipt=dict(schema=1,status="O2_DIAGNOSTIC_BUILD_PASS",started=started,
                 finished=datetime.now().astimezone().isoformat(),exit_code=rc,
                 source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                 command=cmd,source_sha256={str(x.relative_to(out)):sha(x) for x in (out/"source").glob("*") if x.is_file()},
                 generated_sha256={str(x.relative_to(out)):sha(x) for x in (out/"data").glob("*") if x.is_file()},
                 images_sha256={name:sha(out/name) for name in ["o2-diag.elf","o2-diag.bin","o2-diag.txt"]},
                 am_libraries_sha256={str(x):sha(x) for x in libs},
                 nexus_am_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=am,text=True).strip(),
                 toolchain=subprocess.check_output(["riscv64-linux-gnu-gcc","--version"],text=True).splitlines()[0],
                 compiled_cases=checked,performance_measured=False)
    (out/"build.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(dict(status=receipt["status"],image=str(out/"o2-diag.bin"),
                         expected_vdot_commits=manifest["expected_vdot_commits"])))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
