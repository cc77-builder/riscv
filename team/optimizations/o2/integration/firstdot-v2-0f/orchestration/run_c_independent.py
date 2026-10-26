from pathlib import Path
import sys,json,hashlib,os
repo=Path(sys.argv[1]).resolve()
identity=Path(sys.argv[2]).resolve()
matrix=Path(sys.argv[3]).resolve()
build=Path(sys.argv[4]).resolve()
output=Path(sys.argv[5]).resolve()
sys.path.insert(0,str(repo/"team/optimizations/o2/integration/firstdot-v2-0f"))
import combination as c
own_sha=c.g.sha(__file__)
os.sched_setaffinity(0,[sorted(os.sched_getaffinity(0))[1]])
value=c.parent_identity(repo,identity)
c.outside_inputs(output,[repo,identity.parent,matrix,build,value["configuration"]["am_home"]])
anchor=c.library_anchor(repo,build,matrix)
c.g.require(anchor==c.read(build/"matrix-anchor.json"),"C matrix object drift")
c.g.require(c.read(build/"combination-c-build.json")["adapter_files"]==c.adapter_files(),"C adapter drift")
base=c.c_adapter(repo,value)
result=base.run(repo,value["configuration"],build,output,"20261026-cc77-builder-firstdot-independent-c")
c.g.require(c.g.sha(__file__)==own_sha,"orchestration source drift")
c.g.save(output/"independent-c-orchestration.json",dict(
 contract=c.CONTRACT, hardware_identity_sha256=c.g.sha(identity),
 source_sha256=own_sha, source_file=str(Path(__file__).resolve()),
 matrix_images_sha256=c.g.sha(matrix/"images.json"), source_result=result,
 scope="independent ordinary C correctness; matrix qualification remains pending",
 combination_qualified=False, performance_measured=False))
print("ORDINARY_C_DONE_MATRIX_QUALIFICATION_PENDING",flush=True)
