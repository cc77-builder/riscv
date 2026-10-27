from pathlib import Path
import json,hashlib,subprocess,ast,re
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent;FIN=HERE/"final"
MAIN=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
DEST=MAIN/"team/optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-expanded-v1"
WIN=Path("/mnt/d/yanyi/riscv大赛/doc/firstdotV2选择性集成_20261026")
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ledger=read(MAIN/"team/docs/version-data-ledger.json")
assert len(ledger["records"])==25 and ledger["records"][:-1]==read(FIN/"ledger-before.json")["records"]
assert ledger["records"][-1]==read(FIN/"record.json")==read(DEST/"record.json")
assert (FIN/"ledger-before.md").read_text() in (MAIN/"team/docs/version-data-ledger.md").read_text()
snap=read(DEST/"source-snapshot.json")
for row in snap["files"]:
 assert sha(DEST/row["destination"])==row["sha256"]==sha(Path(row["source"])),row
for path in (DEST/"tools/expansion-v1").glob("*.py"):ast.parse(path.read_text())
for label,dest in [("各版本运行数据档案.json",MAIN/"team/docs/version-data-ledger.json"),
 ("各版本运行数据档案.md",MAIN/"team/docs/version-data-ledger.md"),
 ("配置复用_数据集与尺寸扩展结果.md",DEST/"RESULT.md"),
 ("配置复用_数据集与尺寸扩展数据.json",DEST/"record.json")]:
 assert sha(WIN/label)==sha(dest),label
for link in re.findall(r"\]\(([^)]+)\)",(DEST/"README.md").read_text()):
 assert (DEST/link).is_file(),link
assert not subprocess.check_output(["git","diff","HEAD","--","src"],cwd=MAIN,text=True).strip()
diffcheck=subprocess.run(["git","diff","--check"],cwd=MAIN,text=True,capture_output=True)
assert diffcheck.returncode==0,diffcheck.stdout+diffcheck.stderr
live=[]
for p in Path("/proc").iterdir():
 if p.name.isdigit():
  try:
   if (p/"exe").resolve().name=="emu" and b"/config-reuse-expanded-01/" in (p/"cmdline").read_bytes():live.append(p.name)
  except (OSError,RuntimeError):pass
assert not live,live
result=dict(status="FINAL_LOCAL_EXPANSION_MATERIALS_QA_PASS",record_count=25,
 previous_24_json_records_unchanged=True,previous_markdown_body_preserved=True,
 compact_files_verified=len(snap["files"]),windows_mirrors_verified=4,production_src_diff_empty=True,
 active_emu_pids=live,github_uploaded=False,finished=datetime.now(timezone.utc).isoformat())
q=FIN/"final-qa.json";assert not q.exists();q.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
handoff=W/"handoff-state.json";d=read(handoff)
d["latest_expansion_20261027"].update(status="COMPLETED_LOCAL_NO_UPLOAD",
 record_id=ledger["records"][-1]["record_id"],decisions={k:v["decision"] for k,v in ledger["records"][-1]["performance"].items()},
 result=str(DEST/"RESULT.md"),record=str(DEST/"record.json"),qa=str(q),
 next_step="Review per-shape selection, then qualify ordinary public C application path; no default switch yet.")
handoff.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result))
