"""Diagnostic raw reparse only; does not grant old process runtime qualification."""
from pathlib import Path
import json,shutil,tempfile,sys
import probe
W=Path("/home/riscv/riscv-lab/software-import-20261026")
R=W/"clean-02/checkout/source"
old=W/"config-reuse-clean02-01/run-01/runs/recovery-config-reuse"
p=probe.Probe(R,W/"clean-02/identity/current.json",W/"clean-02/matrix-build-01",W/"clean-02/matrix-run-01")
f,m=p.runtime()
with tempfile.TemporaryDirectory() as tmp:
    out=Path(tmp)
    for name in ["stdout.log","stderr.log","result.json"]:shutil.copyfile(old/name,out/name)
    r=probe.read(out/"result.json");build=Path(r["path"]);actual=str(build/"vdot-perf.bin")
    if sys.argv[1]!="original":
        common=dict(r["files"]);loaded=common.pop(actual)
        r["files"]=probe.process_inputs(common)|{actual:"0"*64 if sys.argv[1]=="wrong" else loaded}
        probe.save(out/"result.json",r)
    windows,observation=f.verify_runtime(R,build,out)
    print(json.dumps(windows))
