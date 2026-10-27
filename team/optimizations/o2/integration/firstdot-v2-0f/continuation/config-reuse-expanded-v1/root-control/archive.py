from pathlib import Path
import json,hashlib,gzip,shutil
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent
OUT=W/"config-reuse-expanded-01"
ARCH=W/"reviews/config-reuse-expanded-final-archive-01"
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
assert read(HERE/"pipeline-02.command.json")["exit_code"]==0
assert read(OUT/"state.json")["status"]=="EXPANDED_MATRIX_AND_RAW_AUDIT_PASS"
assert read(OUT/"audit-01.json")["status"]=="EXPANDED_MATRIX_LOCAL_RAW_AUDIT_PASS"
assert not ARCH.exists()
inputs=set()
for root in [OUT,HERE,HERE.parent/"expansion-v1"]:
 for p in root.rglob("*"):
  if p.is_file():
   assert not p.is_symlink(),p
   inputs.add(p)
common=read(OUT/"run-01/runtime-inputs.json")
for name,digest in common.items():
 p=Path(name);assert p.is_file() and not p.is_symlink() and sha(p)==digest,name
 inputs.add(p)
# Explicit old baseline records and selected existing qualification evidence.
for rel in ["clean-02/matrix-run-01/results.json","clean-02/matrix-run-01/state.json",
 "clean-02/matrix-build-01/images.json","clean-02/full-reproduction-comparison-03.json",
 "config-reuse-clean02-02/completion-02.json","config-reuse-clean02-02/run-01/results.json"]:
 inputs.add(W/rel)
ARCH.mkdir()
(ARCH/"files").mkdir()
rows=[]
for n,p in enumerate(sorted(inputs)):
 before=sha(p);size=p.stat().st_size
 stored=ARCH/"files"/("%05d.gz"%n)
 with p.open("rb") as src,stored.open("wb") as raw,gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0) as dest:
  shutil.copyfileobj(src,dest,length=1024*1024)
 h=hashlib.sha256();count=0
 with gzip.open(stored,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b);count+=len(b)
 assert h.hexdigest()==before and count==size and sha(p)==before,p
 rows.append(dict(source=str(p),raw_sha256=before,raw_bytes=size,stored=str(stored.relative_to(ARCH)),
   stored_sha256=sha(stored),stored_bytes=stored.stat().st_size))
value=dict(status="LOCAL_EXPANDED_EVIDENCE_BYTES_ARCHIVED_AND_READBACK_PASS",
 created=datetime.now(timezone.utc).isoformat(),members=rows,count=len(rows),
 raw_bytes=sum(r["raw_bytes"] for r in rows),stored_bytes=sum(r["stored_bytes"] for r in rows),
 actual_target_processes=33,new_emu_runs=0,portable_rebuild=False,
 limit="Local evidence/raw byte archive; original raw audit depends on pinned local physical inputs. Archive readback is not independent target reproduction.")
(ARCH/"manifest.json").write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(dict(status=value["status"],members=len(rows),raw_bytes=value["raw_bytes"],
 stored_bytes=value["stored_bytes"],manifest_sha256=sha(ARCH/"manifest.json"))))
