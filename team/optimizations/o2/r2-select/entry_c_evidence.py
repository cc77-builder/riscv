"""Portable ordinary-C evidence, anchored to the complete R4 performance matrix."""
from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path, PurePosixPath
import tempfile

import entry_c_api as c

g,a,CONTRACT=c.g,c.a,c.CONTRACT
EXTRA={str(g.ENTRY/n) for n in ("entry_c_evidence.py","test_entry_c_api.py","ENTRY_CONTRACT.md","C_API_CONTRACT.md")}
EXTRA.update(str(g.ENTRY/"public"/n) for n in ("gemv.S","gemv.h"))


def archive_modules(repo):
    import entry_evidence as evidence
    portable,_,_=evidence.modules(repo)
    c.source_files(repo)
    g.require(Path(__file__).resolve()==repo/g.ENTRY/"entry_c_evidence.py","C evidence from another checkout")
    return evidence,portable


def pack(repo,build,run,output,matrix):
    """A small C evidence archive anchored to the complete performance archive."""
    g.require(os.name=="posix","C physical sealing needs Linux")
    e,portable=archive_modules(repo)
    proof=c.audit_run(repo,build,run)
    for name in ("gemv.S","gemv.h"):
        g.require((repo/g.ENTRY/"public"/name).read_bytes()==(build/"source"/name).read_bytes(),
                  "published public source differs from the real C build")
    base=portable.Archive(matrix)
    e.byte_check(repo,matrix)
    g.require(base.manifest["qualification_scope"]=="matrix","C evidence needs the complete matrix anchor")
    g.require(not output.exists() and all(not output.is_relative_to(p) for p in (build,run,matrix)),
              "C archive overlaps inputs or exists")
    output.mkdir(parents=True,exist_ok=False)
    entries,originals=[],{}
    def add(raw,logical,original):
        g.require(original not in originals,"duplicate C archive input")
        encoded,stored,encoding=raw,Path("files")/logical,"identity"
        if len(raw)>1024:
            zipped=gzip.compress(raw,compresslevel=9,mtime=0)
            if len(zipped)+64<len(raw): encoded,stored,encoding=zipped,stored.with_name(stored.name+".gz"),"gzip"
        target=output/stored
        g.require(not target.exists(),"duplicate C archive path")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(encoded)
        entries.append(dict(original=original,stored=stored.as_posix(),encoding=encoding,
                            raw_bytes=len(raw),raw_sha256=e.digest(raw),stored_bytes=len(encoded),stored_sha256=e.digest(encoded)))
        originals[original]=logical
    for prefix,root in (("build",build),("run",run)):
        for path in sorted(root.rglob("*")):
            if not path.is_file(): continue
            rel=path.relative_to(root)
            if set(rel.parts)&{"objects","__pycache__"}: continue
            if "cwd" in rel.parts and not (path.name in a.frozen_m.AUX and path.parent.name=="build"): continue
            g.require(not path.is_symlink(),"symlink in C evidence")
            add(path.read_bytes(),prefix+"/"+rel.as_posix(),str(path))
    inputs=a.read(run/"runtime-inputs.json")
    for path in (run/"runs").glob("*/result.json"):
        for name,sha in a.read(path)["files"].items(): e.include(inputs,name,sha)
    for name in sorted(set(inputs)|{str(repo/rel) for rel in EXTRA}):
        path=Path(name)
        if path.is_relative_to(repo) and name not in originals:
            add(path.read_bytes(),"tools/"+path.relative_to(repo).as_posix(),name)
    base_originals={r["original"]:logical for logical,r in base.records.items()}
    base_seal=base.json("sealed-inputs.json")
    sealed={}
    for path,sha in sorted(inputs.items()):
        if path in originals:
            source,logical="self",originals[path]
        elif path in base_originals:
            source,logical="matrix",base_originals[path]
            g.require(e.digest(base.raw(logical))==sha,"C/matrix payload mismatch")
        else:
            source,logical="external",None
            g.require(base_seal.get(path)==dict(sha256=sha,logical=None),"unknown C external input")
        sealed[path]=dict(sha256=sha,archive=source,logical=logical)
    a.frozen_m.verify_files(inputs)
    add(e.json_bytes(sealed),"sealed-inputs.json","generated:sealed-inputs")
    meta=dict(version=1,contract=CONTRACT,created_utc=a.frozen_f.now(),source_root=str(repo),build_root=str(build),run_root=str(run),
              matrix_manifest_sha256=g.sha(matrix/"archive-manifest.json"),files=entries,
              scope="ordinary C functional calls only; common hardware provenance anchored to the R4 matrix archive")
    raw=e.json_bytes(meta)
    (output/"archive-manifest.json").write_bytes(raw)
    (output/"archive-manifest.sha256").write_text(e.digest(raw)+"  archive-manifest.json\n")
    checked=portable.Archive(output)
    result=dict(status="R4_C_APPLICATION_ARCHIVE_BYTES_PASS",**checked.bytes_result)
    g.save(output/"archive-check.json",result)
    return dict(**proof,archive=result)


def audit_archive(repo,archive,matrix):
    e,portable=archive_modules(repo)
    saved,base=portable.Archive(archive),portable.Archive(matrix)
    meta=saved.manifest
    g.require(meta["contract"]==CONTRACT and meta["matrix_manifest_sha256"]==g.sha(matrix/"archive-manifest.json"),
              "C archive contract/matrix anchor")
    matrix_proof=e.audit(repo,matrix)
    g.require(matrix_proof["qualification_scope"]=="matrix","C archive requires full matrix qualification")
    g.require(a.read(archive/"archive-check.json")==dict(status="R4_C_APPLICATION_ARCHIVE_BYTES_PASS",**saved.bytes_result),
              "C archive cached byte verdict")
    original_paths=set()
    for logical,record in saved.records.items():
        parts=PurePosixPath(logical).parts
        root={"build":meta["build_root"],"run":meta["run_root"],"tools":meta["source_root"]}.get(parts[0])
        expected=str(PurePosixPath(root)/PurePosixPath(*parts[1:])) if root else "generated:sealed-inputs" if logical=="sealed-inputs.json" else None
        g.require(record["original"]==expected and expected not in original_paths,"C archive original mapping")
        original_paths.add(expected)
        if parts[0]=="tools":
            g.require(e.digest(saved.raw(logical))==g.sha(repo/PurePosixPath(*parts[1:])),"C archive tool changed")
    for rel in EXTRA:
        logical="tools/"+rel
        g.require(logical in saved.records and e.digest(saved.raw(logical))==g.sha(repo/rel),"missing/changed C evidence tool or contract")
    for name in ("gemv.S","gemv.h"):
        g.require((repo/g.ENTRY/"public"/name).read_bytes()==saved.raw("build/source/"+name),
                  "published public source differs from archived C build")
    sealed=saved.json("sealed-inputs.json")
    base_seal=base.json("sealed-inputs.json")
    for path,value in sealed.items():
        if value["archive"] in ("self","matrix"):
            source=saved if value["archive"]=="self" else base
            logical=value["logical"]
            g.require(logical in source.records and source.records[logical]["original"]==path and
                      e.digest(source.raw(logical))==value["sha256"],"C sealed input payload mismatch")
        else:
            g.require(value["archive"]=="external" and value["logical"] is None and
                      base_seal.get(path)==dict(sha256=value["sha256"],logical=None),"C unarchived input")
    profile=saved.json("run/hardware-profile.json")
    base_profile=base.json("campaigns/"+next(iter(base.manifest["campaigns"]))+"/hardware-profile.json")
    g.require(profile=={k:v for k,v in base_profile.items() if k!="software_contract"},"C/matrix hardware profile differs")
    cfg=saved.json("run/configuration.json")
    g.require(cfg["source_root"]==meta["source_root"] and cfg["canonical_build"]==meta["build_root"] and
              cfg["run_root"]==meta["run_root"],"C archive configuration roots")
    e.fixture_identity(saved,"run/negative-fixture",saved.json("run/negative-fixture/fixture.json"),cfg,a.frozen_m)
    with tempfile.TemporaryDirectory(prefix="r4-c-archive-") as temp:
        out=Path(temp)
        for logical in saved.records:
            if logical.startswith(("build/","run/")):
                target=out/logical
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(saved.raw(logical))
        proof=c.audit_run(repo,out/"build",out/"run",external={p:v["sha256"] for p,v in sealed.items()})
    return dict(**{k:v for k,v in proof.items() if k!="status"},status="R4_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS",
                archive=saved.bytes_result,matrix_manifest_sha256=meta["matrix_manifest_sha256"],
                matrix_status=matrix_proof["status"])


def index_check(repo,archive):
    e,portable=archive_modules(repo)
    saved=portable.Archive(archive)
    g.require(saved.manifest["contract"]==CONTRACT and a.read(archive/"archive-check.json")==
              dict(status="R4_C_APPLICATION_ARCHIVE_BYTES_PASS",**saved.bytes_result),"C archive byte identity")
    result=e.index_bytes(repo,archive)
    result["status"]="R4_C_APPLICATION_ARCHIVE_COMPLETE_GIT_INDEX_PASS"
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--action",choices=("pack","audit","index"),required=True)
    p.add_argument("--build",type=Path)
    p.add_argument("--run",type=Path)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--matrix",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    repo,archive=args.repo.resolve(),args.archive.resolve()
    if args.action=="pack":
        g.require(args.build is not None and args.run is not None and args.matrix is not None,"C pack needs build/run/matrix")
        result=pack(repo,args.build.resolve(),args.run.resolve(),archive,args.matrix.resolve())
    else:
        g.require(args.output is not None and not args.output.exists() and all(not args.output.resolve().is_relative_to(p.resolve())
                  for p in (args.build,args.run,args.archive,args.matrix) if p is not None),"C audit output must be new/outside inputs")
        if args.action=="audit":
            g.require(args.matrix is not None,"C audit needs matrix anchor")
            result=audit_archive(repo,archive,args.matrix.resolve())
        else:
            result=index_check(repo,archive)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        g.save(args.output,result)
    print(json.dumps(result,indent=2))
