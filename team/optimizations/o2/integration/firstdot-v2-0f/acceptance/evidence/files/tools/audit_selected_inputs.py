"""Read-only final selection qualification, preserving historical execution identities."""
import hashlib, importlib.util, json, subprocess
from pathlib import Path
R=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
W=Path("/home/riscv/riscv-lab/software-import-20261026")
A=R/"team/optimizations/o2/integration/firstdot-v2-0f/acceptance"
O=W/"r5-g5-acceptance-01/selected-inputs-02"
assert not O.exists()
O.mkdir()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
rel=R/"team/optimizations/o2/integration/firstdot-v2-0f/package/c8/relink"
spec=importlib.util.spec_from_file_location("r5_c8_integrate",rel/"integrate.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tools,identity,closure,summary=m.verify_inputs(R,W/"clean-02/identity/current.json",
 W/"config-reuse-expanded-01",W/"config-reuse-c8-02",W/"c8-package-01",O/"qualification")
manifest=read(rel/"source-evidence-manifest.json")
for name,item in manifest.items():
 assert sha(rel/name)==item["sha256"] and (rel/name).stat().st_size==item["bytes"],name
parser=m.load("r5_elf_parser",R/"team/optimizations/o2/r2-safe-tail/linked_gate.py")
old=W/"config-reuse-c8-02/build-01"
new=W/"c8-relink-01/integrated"
comparison=m.compare_images(parser,(old/"vdot-perf.elf").read_bytes(),(new/"vdot-perf.elf").read_bytes(),
 (old/"vdot-perf.bin").read_bytes(),(new/"vdot-perf.bin").read_bytes(),read(old/"source/manifest.json"))
save("final-image-equivalence.json",comparison)
# Bind the whole current production source inventory to selected 0f and clean source.
entries=subprocess.check_output(["git","ls-tree","-r","0f12df675378556670afd0dd2153f47fcb330610","--","src"],cwd=R,text=True).splitlines()
names=[];gitlinks={}
for entry in entries:
 meta,name=entry.split("\t",1)
 mode,kind,oid=meta.split()
 if kind=="blob":names.append(name)
 elif kind=="commit":
  gitlinks[name]=oid
  for root in (R,W/"clean-02/checkout/source"):
   actual=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root/name,text=True).strip()
   assert actual==oid,(name,actual,oid)
 else:raise AssertionError(kind)
save("production-gitlinks.json",gitlinks)
source_pins={}
for name in names:
 frozen=subprocess.check_output(["git","show","0f12df675378556670afd0dd2153f47fcb330610:"+name],cwd=R)
 digest=hashlib.sha256(frozen).hexdigest()
 assert sha(R/name)==sha(W/"clean-02/checkout/source"/name)==digest,name
 source_pins[name]=digest
save("production-source-pins.json",source_pins)
record=read(R/"team/docs/version-data-ledger.json")["records"]
save("selected-history-records.json",[record[i-1] for i in (9,14,22,23,25,26,27,28)])
result=dict(status="R5_SELECTED_INPUTS_AND_C8_EQUIVALENCE_PASS",protected_inputs=len(closure),
 production_files=len(source_pins),production_matches_selected_0f_and_clean=True,
 prior_relink_manifest_files=len(manifest),final_image_equal=True,
 bin_sha256=comparison["bin_sha256"],bin_bytes=comparison["bin_bytes"],
 reused_matrix_processes=33,reused_c_processes=3,new_emu_runs=0,new_performance="NOT_TESTED",
 new_ppa="NOT_TESTED",qualification=summary)
save("results.json",result)
print(json.dumps({k:v for k,v in result.items() if k!="qualification"}))
