from pathlib import Path
import json,sys
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p))
import portable
a=json.loads((p/"artifact-pins.json").read_text(encoding="utf-8"))
tools=p/"checker-snapshots";perf=tools/"team/optimizations/o2/performance";sys.path.insert(0,str(perf))
portable.load_source(tools,"team/optimizations/o2/performance/build_profile.py",a,"build_profile")
compare=portable.load_source(tools,"team/optimizations/o2/performance/compare.py",a,"windows_compare")
check=portable.load_source(tools,"team/workloads/unified-vdot/check.py",a,"windows_counter_check")
observer=portable.load_source(tools,"team/optimizations/o1/fullcore/analyze.py",a,"windows_o1_protocol")
run=p/"o1/smoke/smoke-d0-s00-r0"
record=json.loads((run/"result.json").read_text(encoding="utf-8"));runtime=json.loads((run/"runtime.json").read_text(encoding="utf-8"))
pins=json.loads((p/"o1-hardware-pins.json").read_text(encoding="utf-8"));inp=json.loads((p/"input-manifest.json").read_text(encoding="utf-8"))
portable.validate_runtime_binding(record,runtime,pins,a,inp["files"])
windows=check.verify(p/"input",run,external=a)
assert windows==json.loads((run/"window-result.json").read_text(encoding="utf-8"))
analysis=observer.analyze((run/"stderr.log").read_text(encoding="utf-8")+(run/"stdout.log").read_text(encoding="utf-8"))
compare.observer_gate("o1",analysis,record["expected_vdot_commits"])
assert json.loads(json.dumps(analysis))==json.loads((run/"observation.json").read_text(encoding="utf-8"))
data=dict(status="WINDOWS_G4_TOOL_COMPATIBILITY_PASS",windows=len(windows["samples"]),scope="completed O1 calibration only; not full G4",new_emu_run=False)
(p/"verification.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
print(json.dumps(data))
