from pathlib import Path
import json,hashlib,subprocess,ast
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026");HERE=Path(__file__).resolve().parent
MAIN=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
DEST=MAIN/"team/optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-c8-v2"
WIN=Path("/mnt/d/yanyi/riscv大赛/doc/firstdotV2选择性集成_20261026")
OUT=W/"config-reuse-c8-02"
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
old=read(HERE/"ledger-before.json");new=read(MAIN/"team/docs/version-data-ledger.json")
assert len(old["records"])==25 and len(new["records"])==26 and old["records"]==new["records"][:-1]
for key,value in old.items():
 if key not in ["records","last_append_at","last_append_note"]:assert new[key]==value,key
record=read(HERE/"record.json");assert new["records"][-1]==record==read(DEST/"record.json")
assert (HERE/"ledger-before.md").read_text() in (MAIN/"team/docs/version-data-ledger.md").read_text()
snap=read(DEST/"source-snapshot.json")
for r in snap["files"]:
 assert sha(DEST/r["destination"])==r["sha256"]==sha(Path(r["source"])),r["destination"]
for name in ["gemv.S","gemv.h","main.c","cases.h","manifest.json","Makefile"]:
 assert (DEST/"public"/name).read_bytes()==(OUT/"build-01/source"/name).read_bytes()
for src,name in [(DEST/"RESULT.md","8x32配置复用_普通C调用验证.md"),(DEST/"record.json","8x32配置复用_普通C调用数据.json"),
 (MAIN/"team/docs/version-data-ledger.json","各版本运行数据档案.json"),(MAIN/"team/docs/version-data-ledger.md","各版本运行数据档案.md")]:
 assert sha(src)==sha(WIN/name),name
for p in DEST.rglob("*.py"):ast.parse(p.read_text(),filename=str(p))
assert subprocess.check_output(["git","diff","HEAD","--","src"],cwd=MAIN)==b""
check=subprocess.run(["git","diff","--check"],cwd=MAIN,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
assert read(OUT/"state.json")["status"]=="CURRENT_CONFIG_REUSE_8X32_C_QUALIFIED"
assert read(HERE/"physical-after.json")["matches_before"] is True
assert record["metrics"]["target"]["normal_calls"]==24 and record["metrics"]["whole_fixture"]["normal_calls"]==96
assert record["verification"]["new_cycles"]=="NOT_TESTED"
for p in Path("/proc").iterdir():
 if not p.name.isdigit():continue
 try:args=(p/"cmdline").read_bytes().split(b"\0")
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 assert not (args and args[0].endswith(b"/build/emu") and any(str(OUT).encode() in a for a in args)),p
qa=dict(status="FINAL_LOCAL_C8_MATERIALS_QA_PASS",created=datetime.now(timezone.utc).isoformat(),
 records=26,prior25_records_unchanged=True,other_ledger_keys_unchanged=True,old_markdown_body_preserved=True,
 compact_files=len(snap["files"]),compact_bytes=sum(r["bytes"] for r in snap["files"]),windows_mirrors=4,
 public_matches_executed_source=True,src_diff_empty=True,git_diff_check=True,no_active_campaign_emu=True,
 new_emu_runs=0,github_uploaded=False,default_changed=False)
save(HERE/"final-qa.json",qa)
save(DEST/"final-qa.json",qa)
handoff=W/"handoff-state.json";v=read(handoff)
v["latest_c8_20261027"]=dict(status="COMPLETED_LOCAL_NO_UPLOAD",output=str(OUT),
 receipt=str(W/"reviews/config-reuse/c8-preflight-02/pipeline.command.json"),final_qa=str(HERE/"final-qa.json"),
 results=str(DEST/"RESULT.md"),record_id=record["record_id"],next="Review8x32 reuse-vdot stable entry scope; other shapes retain prior decisions",
 production_hardware="0f",default_changed=False,updated=qa["created"])
save(handoff,v)
print(json.dumps(qa,ensure_ascii=False))
