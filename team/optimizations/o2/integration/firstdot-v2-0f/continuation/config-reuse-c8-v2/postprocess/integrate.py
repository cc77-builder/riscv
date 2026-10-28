from pathlib import Path
import json,hashlib,shutil,subprocess
from datetime import datetime,timezone,timedelta
W=Path("/home/riscv/riscv-lab/software-import-20261026");HERE=Path(__file__).resolve().parent
MAIN=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
OUT=W/"config-reuse-c8-02";PRE=W/"reviews/config-reuse/c8-preflight-02"
LEAF=Path("team/optimizations/o2/integration/firstdot-v2-0f")
DEST=MAIN/LEAF/"continuation/config-reuse-c8-v2"
WIN=Path("/mnt/d/yanyi/riscv大赛/doc/firstdotV2选择性集成_20261026")
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
def git(*a):return subprocess.check_output(["git",*a],cwd=MAIN,text=True).strip()
assert git("rev-parse","HEAD")=="c823a8786e052c6e26f6915563c42b6d730dd8e3"
assert git("branch","--show-current")=="local/zjhwork-integration-20261024"
assert not git("diff","HEAD","--","src")
assert read(PRE/"pipeline.command.json")["exit_code"]==0
record=read(HERE/"record.json")
assert record["status"]=="ORDINARY_C_FUNCTIONAL_AND_RAW_AUDIT_PASS"
lp=MAIN/"team/docs/version-data-ledger.json";mp=lp.with_suffix(".md")
old=read(lp);before=read(HERE/"ledger-before.json");md_before=(HERE/"ledger-before.md").read_text()
assert old==before and len(old["records"])==25 and mp.read_text()==md_before
assert not DEST.exists()
DEST.mkdir(parents=True);copies=[]
def copy(src,rel):
 dst=DEST/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 assert src.is_file() and not src.is_symlink() and not dst.exists()
 shutil.copyfile(src,dst);assert sha(src)==sha(dst)
 copies.append(dict(source=str(src),destination=str(rel),sha256=sha(src),bytes=src.stat().st_size))
for name in ["RESULT.md","record.json"]:copy(HERE/name,Path(name))
for version in ["c8-v1","c8-v2"]:
 for src in sorted((PRE.parent/version).iterdir()):
  if src.is_file():copy(src,Path("tools")/version/src.name)
for src in sorted(HERE.glob("*.py")):copy(src,Path("postprocess")/src.name)
for n in ["context.json","review.json","host-tests-01.command.json","host-tests-01.command.stdout.log",
 "host-tests-01.command.stderr.log","pipeline.command.json","pipeline.command.stdout.log","pipeline.command.stderr.log"]:
 copy(PRE/n,Path("evidence/preflight")/n)
for n in ["state.json","audit-01.json","identity-before.json","outer-inputs.json"]:
 copy(OUT/n,Path("evidence")/n)
copy(HERE/"physical-after.json",Path("evidence/physical-after.json"))
for base,names in {
 "build-01":["build.json","elf-validation.json","current-matrix-anchor.json"],
 "run-01":["state.json","results.json","runtime-inputs.json","configuration.json","hardware-profile.json",
 "monotonic-records.json","current-c-qualification.json"]
}.items():
 for n in names:copy(OUT/base/n,Path("evidence")/base/n)
for d in sorted((OUT/"run-01/runs").iterdir()):
 for n in ["result.json","validation.json","observation.json","negative.json","stdout.log"]:
  if (d/n).is_file():copy(d/n,Path("evidence/runs")/d.name/n)
 if (d/"stderr.log").stat().st_size<=32768:copy(d/"stderr.log",Path("evidence/runs")/d.name/"stderr.log")
for src in sorted((OUT/"qualified-public").iterdir()):
 if src.is_file():copy(src,Path("public")/src.name)
for n in ["state.json","run-01/state.json"]:
 copy(W/"config-reuse-c8-01"/n,Path("evidence/preserved-failure")/n)
for n in ["pipeline.command.json","pipeline.command.stderr.log"]:
 copy(PRE.with_name("c8-preflight-01")/n,Path("evidence/preserved-failure")/n)
copy(W/"reviews/config-reuse-c8-final-archive-03/manifest.json",Path("evidence/archive-manifest.json"))
save(DEST/"source-snapshot.json",dict(status="COMPACT_C8_SNAPSHOT_HASH_VERIFIED",files=copies))
(DEST/"C_CONTRACT.md").write_text("# 当前0f硬件的普通C接口范围\n\n"
 "本地外层合同见[验证合同](tools/c8-v2/CONTRACT.md)，原内层r2-s3-config-reuse-c-application-v1的门禁保持；旧T17身份由本轮固定clean-02身份明确替代，没有转借旧资格。\n\n"
 "8×32输入为行优先INT8矩阵A（256字节）紧接INT8向量x（32字节），共288字节。输入/输出各自16字节对齐、完整且互不重叠；8行输出各16字节，共128字节，每行低4字节为INT32结果，高12字节为零。本轮实际运行环境为Nexus-AM裸机C程序；需要RV64 lp64d、VLEN128、VS已启用，vdot函数需当前自定义编码支持。向量状态/寄存器及ABI允许的调用者保存寄存器可以被覆盖。以[真实C程序](public/main.c)和[源表](public/manifest.json)为本轮已执行用法。\n\n"
 "16个函数完成公共C功能验证；只有8×32 reuse vdot沿用本轮矩阵的性能候选结论，其他形状不据此升级。未创建静态库或dispatcher，未切稳定默认；普通C程序不提供新性能样本。\n")
(DEST/"README.md").write_text("# 8×32配置复用普通C验证\n\n"
 "[结果](RESULT.md) · [完整数据](record.json) · [合同](tools/c8-v2/CONTRACT.md) · [实际公共源码](public/) · [复制哈希](source-snapshot.json)\n\n"
 "本目录包含实际已验证的gemv.S/gemv.h、普通C调用程序及48用例、工具快照和精简证据。完整O2日志、构建物与旧失败封存在本地archive，路径和SHA见record.json。材料快照依赖完整香山源码及固定物理输入，不是可单独执行的便携工程。\n\n"
 "原运行入口为record.json记载的c8-v2/c8.py --output <新的输出目录>，通过taskset限定CPU；不复用已有输出。V1失败源码保留，仅供追溯。所有已归档工具/源码和原始运行输出保持只读；新试验另设输出。\n")
old["records"].append(record);old["last_append_at"]=datetime.now(timezone.utc).isoformat()
old["last_append_note"]="Append record26: 8x32 ordinary C on current0f, prior25 unchanged; V1 failure preserved."
save(lp,old)
result=(HERE/"RESULT.md").read_text()
mp.write_text("> 最新追加：2026-10-27，第26条为8×32配置复用普通C调用验证；无新性能窗口，旧25条全部保留。详见文末第16节。\n\n"+md_before+
 "\n\n## 16. 8×32配置复用普通C调用（第26条）\n\n"+result.split("\n",1)[1].replace("\n## ","\n### "))
route=MAIN/"team/docs/development-route-current.md";text=route.read_text()
a=text.index("> 2026-10-27 本地zjhwork接续：");b=text.index("\n\n更新：",a)
prefix="> 2026-10-27 本地zjhwork接续：当前0f＋firstdot组合与干净复现、配置复用4尺寸×3数据集矩阵已完成；8×32普通公共C调用现已通过。新3进程覆盖16函数/48用例/96正常调用，其中8×32为4函数/12用例/24调用；目标bit100拒错、同BIN恢复、重放和原文审计通过。\n"
prefix+="> 当前选择：8×32配置复用reuse vdot保留性能及普通C候选资格；1.095238×来自此前完整调用矩阵，本C程序无新周期数。4×8、16×64仍须只读归因未改RVV控制窗差异；4×13保留较优RVV。默认未切换、生产RTL保持0f、未上传。\n"
prefix+="> 下一步：评审8×32稳定入口的使用范围及所需新路径验证；其他尺寸按上述证据分别处理。见[C调用结果](../optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-c8-v2/RESULT.md)及[版本档案](version-data-ledger.md)第26条；旧失败与历史墙钟限制保留。\n"
prefix+="> 下文旧R4/T17及6d2身份保留为历史基线，不替代当前0f；队友其他Q应用包不在本轮引入范围。"
route.write_text(text[:a]+prefix+text[b:])
receipt=read(PRE/"pipeline.command.json")
board=MAIN/"开发计分板.md"
board.write_text(board.read_text()+"\n\n## 2026-10-27 8×32配置复用普通C调用\n\n"
 "- 执行者：@cc77-builder / Agent；操作ID：zjhwork-config-reuse-8x32-c-20261027-01（V2独立输出）。\n"
 "- 工作区段：从V1主机检查"+read(PRE.with_name("c8-preflight-01")/"host-tests-01.command.json")["started"]+
 "至本轮留档"+datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))).isoformat()+
 "；成功流水线"+receipt["started"]+"至"+receipt["finished"]+"。含自动验证和等待，不计为成员人工投入。\n"
 "- 成果：8×32四API/三数据集12例、两轮24调用；保留完整16函数48例/96调用。全128位、标量参考、边界/CSR、O2及NEMU通过；bit100负控命中8×32实际PC0x80000d64，同BIN恢复与重放通过。20项主机检查及原文审计完成。\n"
 "- 失败保留：V1的spawn包装器位置参数缺陷在EMU前中止，0新目标。V2只修复env/timeout透传；不修改内层冻结门禁或RTL。\n"
 "- 证据：[结果]("+str(LEAF/"continuation/config-reuse-c8-v2/RESULT.md")+")、[版本档案](team/docs/version-data-ledger.md)第26条。c823a软件＋0f硬件；输入/构建/镜像及3个真实PID见JSON。原始根software-import-20261026/config-reuse-c8-02。\n"
 "- 接续：8×32普通C候选已闭合；下一步评审稳定入口范围。4×8/16×64控制差异仍待只读归因，4×13保留RVV。无新性能/PPA，默认不变、无生产RTL改动、未上传GitHub。\n")
p=MAIN/LEAF/"RESULT.md"
p.write_text(p.read_text()+"\n\n## 8×32普通C调用补齐\n\n"
 "配置复用的普通C路径已完成新3进程验证，详见[结果](continuation/config-reuse-c8-v2/RESULT.md)。16函数/48用例/96调用通过，其中8×32为4函数/12例/24调用；目标高位拒错与重放通过。上一轮1.095238×仍为独立性能矩阵数据，本次未新测周期；默认和RTL未改，未上传。\n")
p=MAIN/"team/README.md";p.write_text(p.read_text()+"\n- [8×32配置复用普通C调用](optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-c8-v2/RESULT.md)：真实调用、全宽差分与重放；数据档案第26条。\n")
for src,name in [(DEST/"RESULT.md","8x32配置复用_普通C调用验证.md"),(DEST/"record.json","8x32配置复用_普通C调用数据.json"),
 (lp,"各版本运行数据档案.json"),(mp,"各版本运行数据档案.md")]:shutil.copyfile(src,WIN/name)
(WIN/"当前进度.md").write_text("# 当前进度\n\n8×32配置复用普通C调用验证完成：3个新进程，8×32为12例/24调用；完整夹具48例/96调用通过。当前硬件仍为O2＋H1＋DIV取消保持修复（0f）。\n\n"
 "见[验证结果](8x32配置复用_普通C调用验证.md)及[数据](8x32配置复用_普通C调用数据.json)。1.095238×是上一轮完整调用矩阵数据，本轮无新周期数。4×8/16×64仍待控制差异归因，4×13保留RVV。\n\n"
 "下一步评审8×32稳定入口范围；默认未切换、RTL未修改、未上传GitHub。\n")
save(HERE/"integration-receipt.json",dict(status="LOCAL_C8_SNAPSHOT_AND_RECORD26_APPENDED",destination=str(DEST),
 copied_files=len(copies),ledger_records=26,old_records_preserved=True,old_markdown_preserved=md_before in mp.read_text(),
 src_diff_empty=not git("diff","HEAD","--","src"),github_uploaded=False,created=datetime.now(timezone.utc).isoformat()))
print("LOCAL_C8_SNAPSHOT_AND_RECORD26_APPENDED")
