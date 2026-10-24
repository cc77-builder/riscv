"""Assemble the bounded C pointer-hoisting candidate over frozen caller v2.

The existing team-owned engine is reused in this process; none of its files,
official code, public leaves, old builds or old evidence is modified.
"""
import argparse
from pathlib import Path
import shutil
import sys
import json
import os

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import experiment as e
g=e.g
CONTRACT="r2-s3-caller-hoisted-8x32-v1"
BASE_PINS={
    "caller.h": "8f8ebbdfc64f506549b8fcb91700fc80dd91b1fd0a5be64aaed504ebcfa0c38e",
    "caller.c": "0e4908e7ff7be9d59d7185e4d1461cf24297ebcd98aacee36958fe674b9183c4",
    "demo.c": "771cb2234851986e6e7f5258a208bc0f681240c22d4266dabbdc83ddcca02b66",
    "main.c": "c17575ae7370f0d440c20edd1e0dc74652bf40f1ea55be8ced1bf4db86cb989e",
    "experiment.py": "e692f4db50b1db0acf69f7d8ca8e38817ff3282d3b8ebcbdd5361c7720e8740a",
    "pathcheck.py": "87e11075f1d84946277cf4d24914944ec9793cfffcc2bfab5a2cc8592c44f1b8",
    "check.py": "e801e82e1fb56c48f567621dd846a3bab77d40aa99a4e7ed6d8aec74fb50f956",
    "CONTRACT.md": "2e0d1e7f95e870bdd5bae2cbcb3b74d93261cc907565aa94ba0a9eda5c38cf07"
}
REL=e.REL/"hoisted"
OWN=("candidate.py","caller.c","CONTRACT.md")
AUX_PINS={"evidence.py": "575ea12d71fb355a4cd08a96d9ecfd578a65de8327589e2273e1292eadfb1901", "selftest.py": "9cc03b5cd20b5b229554fbec80887dbc8db3638a392000cf3370ddb3f439aede"}

def install():
    g.require(e.CONTRACT=="r2-s3-caller-8x32-v2" and HERE==e.ROOT/REL,"candidate/base module identity")
    for name,sha in BASE_PINS.items():
        g.require(g.sha(e.HERE/name)==sha,"frozen original caller changed: "+name)
    for name,sha in AUX_PINS.items():
        g.require(g.sha(e.HERE/name)==sha,"candidate auxiliary gate changed: "+name)
    source_files,generate=e.sources,e.generate
    def sources(repo):
        found=source_files(repo)
        found.update({str(REL/name):g.sha(HERE/name) for name in OWN})
        found.update({str(e.REL/name):sha for name,sha in AUX_PINS.items()})
        return found
    def candidate_generate(repo,out):
        manifest=generate(repo,out)
        shutil.copyfile(HERE/"caller.c",out/"caller.c")
        manifest.update(caller_variant="hoisted-pointers",baseline_contract="r2-s3-caller-8x32-v2",
                        baseline_caller_sha256=BASE_PINS["caller.c"],candidate_caller_sha256=g.sha(HERE/"caller.c"),
                        context_disjoint_from_write_regions=True,pointer_capture_inside_full=True)
        g.save(out/"manifest.json",manifest)
        return manifest
    e.CONTRACT,e.sources,e.generate=CONTRACT,sources,candidate_generate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--identity",type=Path)
    p.add_argument("--action",choices=("build","run","verify-build","selftest","audit","pack","audit-archive"),required=True)
    p.add_argument("--build",type=Path);p.add_argument("--run",type=Path);p.add_argument("--archive",type=Path)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--operation-id")
    args=p.parse_args();repo=args.repo.resolve();out=args.output.resolve()
    g.require(repo==e.ROOT and not out.exists(),"candidate selected checkout and new output required")
    identity=(args.identity or repo/e.parent.REPRO/"evidence/clean-reproduction-v1/reports/identity-02.json").resolve()
    cfg=e.parent.parent_identity(repo,identity)["configuration"]
    roots=[repo,identity.parent]+[cfg[k] for k in ("am_home","hardware_source","build_record")]
    roots += [p.resolve() for p in (args.build,args.run,args.archive) if p]
    e.parent.outside_inputs(out,roots)
    if os.name=="posix":os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
    install()
    if args.action=="build": result=e.build(repo,identity,out)
    elif args.action=="run":
        g.require(args.build and args.operation_id,"candidate run needs build and operation")
        result=e.run(repo,identity,args.build.resolve(),out,args.operation_id)
    elif args.action=="verify-build":
        g.require(args.build is not None,"candidate verification needs build")
        result=e.verification(repo,args.build.resolve());g.save(out,result)
    elif args.action=="selftest":
        g.require(args.build is not None,"candidate selftest needs build")
        t=g.load("hoisted_selftest",e.HERE/"selftest.py")
        result=t.run(args.build.resolve(),args.run.resolve() if args.run else None);g.save(out,result)
    else:
        evidence=g.load("hoisted_evidence",e.HERE/"evidence.py")
        if args.action=="audit-archive":
            g.require(args.archive is not None,"candidate archive required")
            result=evidence.audit_archive(args.archive.resolve());g.save(out,result)
        else:
            g.require(args.build and args.run,"candidate evidence needs build and run")
            if args.action=="pack":result=evidence.pack(args.build.resolve(),args.run.resolve(),out)
            else:result=evidence.audit(args.build.resolve(),args.run.resolve());g.save(out,result)
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()

