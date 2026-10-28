from pathlib import Path
import json,hashlib,shutil,subprocess
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
HERE=Path(__file__).resolve().parent
MAIN=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
OUT=W/"config-reuse-expanded-01";FIN=HERE/"final"
LEAF=Path("team/optimizations/o2/integration/firstdot-v2-0f")
DEST=MAIN/LEAF/"continuation/config-reuse-expanded-v1"
WIN=Path("/mnt/d/yanyi/riscv大赛/doc/firstdotV2选择性集成_20261026")
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def git(*a):return subprocess.check_output(["git",*a],cwd=MAIN,text=True).strip()
assert git("rev-parse","HEAD")=="c823a8786e052c6e26f6915563c42b6d730dd8e3"
assert git("branch","--show-current")=="local/zjhwork-integration-20261024"
assert not git("diff","HEAD","--","src")
assert read(HERE/"pipeline-02.command.json")["exit_code"]==0
record=read(FIN/"record.json");assert record["execution"]["actual_started_processes"]==33
ledger_path=MAIN/"team/docs/version-data-ledger.json"
old=read(ledger_path)
assert len(old["records"])==24
assert record["record_id"] not in [x["record_id"] for x in old["records"]]
assert not DEST.exists()
assert not (FIN/"ledger-before.json").exists()
shutil.copyfile(ledger_path,FIN/"ledger-before.json")
md_path=MAIN/"team/docs/version-data-ledger.md"
shutil.copyfile(md_path,FIN/"ledger-before.md")
DEST.mkdir(parents=True)
copies=[]
def copy(src,rel):
 dst=DEST/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 assert src.is_file() and not src.is_symlink() and not dst.exists()
 shutil.copyfile(src,dst);assert sha(src)==sha(dst)
 copies.append(dict(source=str(src),destination=str(rel),sha256=sha(src),bytes=src.stat().st_size))
for name in ["RESULT.md","record.json"]:copy(FIN/name,Path(name))
for src in (HERE.parent/"expansion-v1").iterdir():
 if src.is_file():copy(src,Path("tools/expansion-v1")/src.name)
for name in ["probe.py","raw_audit.py","CONTRACT.md","import-manifest.json"]:
 copy(HERE.parent/"adapter-v3"/name,Path("tools/adapter-v3")/name)
for src in HERE.iterdir():
 if src.is_file():copy(src,Path("root-control")/src.name)
for name in ["state.json","completion.json","audit-01.json","identity-after.json",
 "build.command.json","build.command.stdout.log","build.command.stderr.log",
 "run.command.json","run.command.stdout.log","run.command.stderr.log",
 "audit.command.json","audit.command.stdout.log","audit.command.stderr.log"]:
 copy(OUT/name,Path("evidence")/name)
for base,names in {
 "build-01":["state.json","matrix-build.json","images.json","pairs.json","baseline-current.json"],
 "run-01":["state.json","results.json","run-plan.json","runtime-inputs.json","hardware-profile.json","configuration.json"]
 }.items():
 for name in names:copy(OUT/base/name,Path("evidence")/base/name)
for src in sorted((OUT/"run-01/runs").glob("*/stdout.log")):
 copy(src,Path("evidence/concise-logs")/src.parent.name/"stdout.log")
for src in sorted((OUT/"run-01/runs").glob("*/stderr.log")):
 # full O2 trace belongs in local compressed archive; keep only small stderr.
 if src.stat().st_size<=32768:copy(src,Path("evidence/concise-logs")/src.parent.name/"stderr.log")
copy(W/"reviews/config-reuse-expanded-final-archive-01/manifest.json",Path("evidence/archive-manifest.json"))
save(DEST/"source-snapshot.json",dict(status="COMPACT_SNAPSHOT_HASH_VERIFIED",files=copies))
(DEST/"README.md").write_text("# 配置复用：数据集与尺寸扩展\n\n"
 "[结果](RESULT.md) · [完整记录](record.json) · [扩展合同](tools/expansion-v1/CONTRACT.md) · [源文件映射](source-snapshot.json)\n\n"
 "本目录保存24图/33进程扩展的工具快照与精简证据。实际输入和原始日志位于记录所列WSL路径；完整trace以本地逐文件压缩归档保存，日常仓库不收构建目录或波形。\n\n"
 "tools/expansion-v1 与 tools/adapter-v3 的相对层级保留。复跑需要完整香山源码、固定 clean identity 与其物理依赖，以及新的输出路径；快照本身不是可脱离环境执行的便携工程。root-control 与 evidence 的真实命令记录原始工作目录。\n\n"
 "本次仅扩展数据集与尺寸，不自动切换默认入口，不上传GitHub。\n")
old["records"].append(record)
old["last_append_at"]=datetime.now(timezone.utc).isoformat()
old["last_append_note"]="Append record 25: four-shape, three-dataset config-reuse matrix; prior 24 records unchanged."
save(ledger_path,old)
assert read(ledger_path)["records"][:-1]==read(FIN/"ledger-before.json")["records"]
result_text=(FIN/"RESULT.md").read_text()
append="\n\n## 15. 配置复用四尺寸、三数据集扩展（第25条）\n\n"+result_text.split("\n",1)[1].replace("\n## ","\n### ")
md_old=(FIN/"ledger-before.md").read_text()
md_path.write_text("> 最新追加：2026-10-27，第25条为4尺寸×3数据集的新配置复用矩阵；第24条仍是历史8×32/d0探针，全部旧数据保留。详见文末第15节。\n\n"+md_old+append)
# Existing navigation: only update this round's current routing prefix.
route=MAIN/"team/docs/development-route-current.md"
rt=route.read_text()
start=rt.index("> 2026-10-27 本地zjhwork接续：")
end=rt.index("\n\n更新：",start)
summary="；".join(s+"="+d["decision"] for s,d in record["performance"].items())
new="> 2026-10-27 本地zjhwork接续：选择性引入、当前0f软硬件组合与干净复现已完成。配置复用4尺寸×3数据集扩展完成24图/33进程，384正式窗、192重放对与288 firstdot对照窗已原文复核；逐尺寸判定："+summary+"。\n"
new+="> 下一步：按逐尺寸证据保留候选范围，补配置复用的普通公共C调用验证；通过后再评审稳定入口。默认未切换，生产RTL保持0f，未上传。\n"
new+="> 本轮数据见[扩展结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-expanded-v1/RESULT.md)与[版本档案](version-data-ledger.md)第25条。历史全核墙钟限制保留；新轮次独立采用单调包络容量检查。\n"
new+="> 下文旧R4/T17及6d2身份保留为历史基线，不替代当前0f身份；队友其他Q应用包不在本轮引入范围。"
route.write_text(rt[:start]+new+rt[end:])
board=MAIN/"开发计分板.md"
board.write_text(board.read_text()+"\n\n## 2026-10-27 配置复用数据集与尺寸扩展\n\n"
 "- 执行者：@cc77-builder / Agent；操作ID：zjhwork-config-reuse-expanded-20261027-01。\n"
 "- 命令执行区间："+read(HERE/"pipeline-02.command.json")["started"]+" 至 "+read(HERE/"pipeline-02.command.json")["finished"]+"；主机执行与等待不计为成员人工投入。\n"
 "- 工作包：R2-S3配置复用的当前0f硬件扩展；24新图、33新进程；92主机测试、GNU、full128/NEMU、O2观察器和原文复核完成。\n"
 "- 结果："+summary+"。保留全部逐数据集、控制和非主项结果，不汇总成单一总加速比。\n"
 "- 身份：源码c823a8786e052c6e26f6915563c42b6d730dd8e3；硬件0f12df675378556670afd0dd2153f47fcb330610；详见[扩展结果]("+str(LEAF/"continuation/config-reuse-expanded-v1/RESULT.md")+"), [版本档案](team/docs/version-data-ledger.md)第25条。\n"
 "- 接续：审阅逐尺寸结论后验证普通公共C调用路径；默认未切换、RTL未改、未上传。首次启动因新增测试撞上源码冻结被拒，0构建/0目标进程；失败回执与主机JSON键类型修复历史均保留。\n")
result=MAIN/LEAF/"RESULT.md"
result.write_text(result.read_text()+"\n\n## 配置复用范围扩展\n\n"
 "4尺寸×3数据集扩展已完成，详见[本轮结果](continuation/config-reuse-expanded-v1/RESULT.md)。"
 "24新图、33新进程；逐尺寸判定："+summary+"。默认未切换，下一步补普通公共C调用路径验证。\n")
readme=MAIN/"team/README.md"
readme.write_text(readme.read_text()+"\n- [配置复用四尺寸、三数据集扩展](optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-expanded-v1/RESULT.md)：完整实测与逐尺寸采用判断，版本档案第25条。\n")
WIN.mkdir(parents=True,exist_ok=True)
for src,name in [(DEST/"RESULT.md","配置复用_数据集与尺寸扩展结果.md"),(DEST/"record.json","配置复用_数据集与尺寸扩展数据.json"),
 (ledger_path,"各版本运行数据档案.json"),(md_path,"各版本运行数据档案.md")]:
 shutil.copyfile(src,WIN/name)
progress=WIN/"当前进度.md"
progress.write_text("# 当前进度\n\n数据集与尺寸扩展已完成，当前硬件仍为O2 + H1 + DIV取消保持修复（0f）。\n\n"
 +summary+"。\n\n详见[扩展结果](配置复用_数据集与尺寸扩展结果.md)与[完整数据](配置复用_数据集与尺寸扩展数据.json)。\n\n"
 "下一步为普通公共C调用路径验证；默认入口未切换，RTL未修改，未上传GitHub。\n")
save(FIN/"integration-receipt.json",dict(status="LOCAL_SNAPSHOT_AND_RECORD25_APPENDED",
 destination=str(DEST),copied_files=len(copies),ledger_records=25,old_records_preserved=True,
 old_markdown_body_preserved=md_old in md_path.read_text(),src_diff_empty=not git("diff","HEAD","--","src"),
 github_uploaded=False,created=datetime.now(timezone.utc).isoformat()))
print("LOCAL_SNAPSHOT_AND_RECORD25_APPENDED")
