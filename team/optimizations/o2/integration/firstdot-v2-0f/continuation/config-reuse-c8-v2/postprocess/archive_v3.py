from pathlib import Path
import json,hashlib,gzip,shutil,os
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent
OUT=W/"config-reuse-c8-02"
ARCH=W/"reviews/config-reuse-c8-final-archive-03"
PRE=W/"reviews/config-reuse/c8-preflight-02"
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
assert read(PRE/"pipeline.command.json")["exit_code"]==0
assert read(OUT/"state.json")["status"]=="CURRENT_CONFIG_REUSE_8X32_C_QUALIFIED"
assert read(OUT/"audit-01.json")["status"]=="CURRENT_CONFIG_REUSE_C_RAW_AUDIT_PASS"
assert not ARCH.exists()
inputs=set();aliases=[]
allowed_links={v["path"]:v["sha256"] for v in read(OUT/"build-01/build.json")["toolchain"].values()}
for root in [OUT,W/"config-reuse-c8-01",PRE,PRE.with_name("c8-preflight-01"),PRE.with_name("c8-v1"),PRE.with_name("c8-v2")]:
 for p in root.rglob("*"):
  if p.is_file():
   assert not p.is_symlink(),p
   inputs.add(p)
for name in ["outer-inputs.json","run-01/runtime-inputs.json"]:
 for path,digest in read(OUT/name).items():
  p=Path(path);assert p.is_file() and sha(p)==digest,path
  if p.is_symlink():
   assert path in allowed_links and allowed_links[path]==digest,("unapproved symlink input",path)
   resolved=p.resolve(strict=True)
   assert resolved.is_file() and not resolved.is_symlink() and sha(resolved)==digest,path
   row=dict(input_path=path,link_text=os.readlink(p),resolved_path=str(resolved),sha256=digest)
   if row not in aliases:aliases.append(row)
   inputs.add(resolved)
  else:inputs.add(p)
for p in HERE.glob("*.py"):inputs.add(p)
inputs.add(HERE/"physical-after.json")
ARCH.mkdir();(ARCH/"files").mkdir()
rows=[]
for n,p in enumerate(sorted(inputs)):
 digest=sha(p);size=p.stat().st_size;stored=ARCH/"files"/("%05d.gz"%n)
 with p.open("rb") as src,stored.open("wb") as raw,gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0) as dest:
  shutil.copyfileobj(src,dest,length=1024*1024)
 h=hashlib.sha256();count=0
 with gzip.open(stored,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b);count+=len(b)
 assert h.hexdigest()==digest and count==size and sha(p)==digest,p
 rows.append(dict(source=str(p),raw_sha256=digest,raw_bytes=size,stored=str(stored.relative_to(ARCH)),
  stored_sha256=sha(stored),stored_bytes=stored.stat().st_size))
for row in aliases:
 p=Path(row["input_path"])
 assert p.is_symlink() and os.readlink(p)==row["link_text"] and str(p.resolve())==row["resolved_path"] and sha(p)==row["sha256"]
value=dict(toolchain_symlink_aliases=aliases,status="LOCAL_C8_EVIDENCE_BYTES_ARCHIVED_AND_READBACK_PASS",created=datetime.now(timezone.utc).isoformat(),
 members=rows,count=len(rows),raw_bytes=sum(r["raw_bytes"] for r in rows),stored_bytes=sum(r["stored_bytes"] for r in rows),
 actual_target_processes=3,new_emu_runs=0,portable_rebuild=False,
 preserved_failure="V1 wrapper argument mismatch before EMU; source/build/receipt preserved",
 limit="Byte readback only; raw audit and reproduction need pinned local physical inputs. No independent new target or portable rebuild claim.")
save(ARCH/"manifest.json",value)
print(json.dumps({k:value[k] for k in ["status","count","raw_bytes","stored_bytes"]}|{"manifest_sha256":sha(ARCH/"manifest.json")}))
