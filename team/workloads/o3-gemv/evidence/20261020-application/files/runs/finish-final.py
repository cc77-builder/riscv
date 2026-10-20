"""Complete the already-authorized O3 campaign delivery, local only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import shutil
import subprocess
import time

R=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
W=Path("/home/riscv/riscv-lab/o3-gemv-20261019")
D=Path("/home/riscv/riscv-lab/o3-gemv-final-delivery-20261020")
V=Path("/mnt/d/yanyi/riscv大赛/doc/O3应用测试_20261019")
PREFIX="team/workloads/o3-gemv/evidence/20261020-application"
A=R/PREFIX
D.mkdir(exist_ok=False)
STATE=dict(status="WAITING_FOR_MEASUREMENTS",started_utc=datetime.now(timezone.utc).isoformat(),github_pushed=False,stages=[])
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");t.replace(p)
def state():save(D/"state.json",STATE)
def git(*args):return subprocess.check_output(["git",*args],cwd=R)
def require(ok,msg):
    if not ok:raise ValueError(msg)
def command(name,cmd):
    row=dict(name=name,command=cmd,cwd=str(R),started_utc=now(),status="RUNNING")
    STATE["stages"].append(row);STATE["status"]=name;state()
    with (D/(name+".stdout.log")).open("xb") as a,(D/(name+".stderr.log")).open("xb") as b:
        rc=subprocess.run(cmd,cwd=R,stdout=a,stderr=b).returncode
    row.update(exit_code=rc,finished_utc=now(),status="PASS" if rc==0 else "FAILED");state()
    require(rc==0,"command failed "+name)
state()
try:
    while True:
        try:launch=json.loads((W/"recovery-launch-state.json").read_text())
        except json.JSONDecodeError:time.sleep(2);continue
        progress=json.loads((W/"campaign-02/state.json").read_text())
        save(V/"当前进度.json",progress)
        if launch["status"]=="EXITED":break
        time.sleep(15)
    require(launch["exit_code"]==0,"measurement campaign failed; preserve raw evidence, do not rerun automatically")
    require(progress["status"]=="O3_PAIRED_APPLICATION_CAMPAIGN_PASS","campaign not accepted")
    require(git("branch","--show-current").decode().strip()=="local/o3-gemv-20261019","branch changed during campaign")
    require(not git("status","--porcelain").strip(),"repository has additional edits; stop before packaging/commit")
    command("linux-recheck",["python3","-B","team/workloads/o3-gemv/results.py","--campaign",str(W/"campaign-02"),"--output",str(W/"results-03")])
    verification=json.loads((W/"results-03/verification.json").read_text())
    require(verification["status"]=="O3_RAW_EVIDENCE_RECHECK_PASS","strict audit")
    require((verification["jobs"],verification["windows"],verification["measured_windows"])==(56,1280,768),"audit cardinality")
    entry=R/"team/workloads/o3-gemv/README.md"
    entry.write_text("""# O3 INT8 GEMV应用评估

真实O1/O2应用测量及Linux原始日志重审完成，Windows交付复算另见delivery回执；本地保存未push，正式T16报告后置。

四尺寸、三数据集、core/endtoend、basic/reuse、vdot/RVV；56项合格EMU作业（46项原通过复用、10项恢复补跑，另2项中断尝试保留），1280校验窗口，768正式性能窗口，4项代表重放逐seq一致。全部规定尺寸和有利/不利结果保留。

[合同](CONTRACT.md) · [封存结果与证据](evidence/20261020-application/README.md)

core包含所有A/x加载、乘法/归约、累加及输出寄存器形成，endtoend再包括kernel初始配置和结果存储；测试框架和VS启用在窗外。K=13的vdot标量尾部成本计入；RVV使用最多16项宽向量及动态尾部，不能称为已证明全局最优。

硬件O1/O2使用G4相同429硬件文件/21236依赖及固定EMU；未重构建、未改ISA/NEMU/旧基准。原测量execute冻结7a642b6，构建软件5fdeba3；恢复编排99f04b9、后处理恢复审核8aab2ed、顺序修复8b6163b；不同提交角色分别记录，文档提交不是重构建。

    python3 -B -m unittest discover -s team/workloads/o3-gemv -p 'test_*.py' -v
    python3 -B team/workloads/o3-gemv/build.py --output /absolute/new/images
    python3 -B team/workloads/o3-gemv/campaign.py --images /absolute/completed/images --output /absolute/new/campaign
    python3 -B team/workloads/o3-gemv/results.py --campaign /absolute/completed/campaign --output /absolute/new/results

不要重启已完成campaign或改写旧证据。新的完整复跑必须用新目录；不以离线复算冒称T17干净构建。O4/O5/G5、默认模式采用和人工ACK仍待后续。
""",encoding="utf-8")
    for filename in ("AGENTS.md","OPTIMIZATION.md"):
        p=R/filename;old=p.read_text()
        p.write_text("""# O3应用评估：本轮自动测量及Linux严格重审完成

2026-10-19（任务开始日期），local/o3-gemv-20261019。先读team/workloads/o3-gemv/README.md及对应证据入口。56项合格作业（46项原通过复用、10项恢复补跑，另2项中断尝试保留）、1280窗口、768正式窗口及4项确定性重放通过；Windows原生复算状态另见delivery回执。不要重跑完成campaign或改密封证据。本轮本地保存未push，不自动O4/O5/G5或切换默认模式，正式T16后置。以下为历史状态。

"""+old,encoding="utf-8")
    (W/"CURRENT_TASK.md").write_text("# 测量与Linux重审已完成\n\n56项合格作业（46复用＋10补跑，另2中断保留）、1280窗口、768正式窗口通过；Windows交付后续状态在相邻o3-gemv-final-delivery-20261020，不重跑campaign。本文件为封存前时点。\n",encoding="utf-8")
    save(W/"final-summary.json",verification)
    subprocess.run(["git","add","--","AGENTS.md","OPTIMIZATION.md","team/workloads/o3-gemv/README.md"],cwd=R,check=True)
    subprocess.run(["git","diff","--cached","--check"],cwd=R,check=True)
    subprocess.run(["git","commit","-m","docs(o3): record measured application results and remaining adoption gates"],cwd=R,check=True,stdout=subprocess.PIPE)
    command("archive",["python3","-B","team/workloads/o3-gemv/archive.py","--work-root",str(W),"--output",str(A),"--campaign-name","campaign-02","--results-name","results-03","--launch-name","recovery-launch-state.json"])
    # W is sealed after export. All subsequent delivery receipts remain in D.
    A.joinpath("README.md").write_text("""# O3应用测试封存证据

O1/O2同镜像GEMV，四尺寸、三数据集、两计时口径、两软件版本及公平RVV对照。
56项合格作业（46项原通过复用、10项恢复补跑，另2项中断尝试保留）、1280校验窗口、768正式性能窗口和4项代表重放通过Linux严格重审。

- [工程结果及全部预定尺寸](files/runs/results-03/结果与工程记录.md)
- [配对比较CSV](files/runs/results-03/comparison.csv)
- [较快RVV对照](files/runs/results-03/best-rvv.csv)
- [原始日志重审](files/runs/results-03/verification.json)
- [测试合同](../../CONTRACT.md)

archive-manifest.json绑定每份原始/存储字节与压缩方式，archive-check.json只证明字节保真；功能/性能结论来自严格重审。原始失败和前期镜像均保留，编译objects排除。

Windows原生复算和实际退出码保存delivery/；复算不新跑EMU，也不重复Linux的工具/依赖来源审核。O4/O5/G5、Fmax/PPA、最终模式和人工ACK仍未完成，本轮不push，正式T16后置。
""",encoding="utf-8")
    shutil.copytree(A,V/"evidence/20261020-application")
    shutil.copytree(R/"team/workloads/o3-gemv",V/"software",dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__","evidence"))
    shutil.copytree(W/"results-03",V/"results")
    windows_root="D:\\yanyi\\riscv大赛\\doc\\O3应用测试_20261019"
    cmd=["/mnt/d/python location/python.exe","-X","utf8","-B",windows_root+"\\software\\portable.py",
         "--archive",windows_root+"\\evidence\\20261020-application",
         "--output",windows_root+"\\windows-portable-audit.json"]
    command("windows-native-recheck",cmd)
    native=json.loads((V/"windows-portable-audit.json").read_text(encoding="utf-8"))
    require(native["status"]=="O3_NATIVE_OFFLINE_RECHECK_PASS" and native["platform"]=="win32","native audit missing")
    proof=A/"delivery";proof.mkdir()
    for name in ("windows-native-recheck.stdout.log","windows-native-recheck.stderr.log"):
        shutil.copy2(D/name,proof/name)
    shutil.copy2(V/"windows-portable-audit.json",proof/"windows-portable-audit.json")
    save(proof/"command-and-exit.json",STATE["stages"][-1])
    attr=R/".gitattributes";s=attr.read_text();rule=PREFIX+"/** -text -whitespace"
    if rule not in s:attr.write_text(s.rstrip()+"\n"+rule+"\n")
    require(not git("diff","--cached","--name-only").strip(),"unexpected staged changes")
    subprocess.run(["git","add","-f","--",PREFIX],cwd=R,check=True)
    subprocess.run(["git","add","--",".gitattributes"],cwd=R,check=True)
    subprocess.run(["git","diff","--cached","--check"],cwd=R,check=True)
    paths=sorted(p for p in A.rglob("*") if p.is_file())
    names=[p.relative_to(R).as_posix() for p in paths]
    raw=subprocess.check_output(["git","cat-file","--batch"],cwd=R,input="".join(":"+p+"\n" for p in names).encode())
    offset=0;digests={}
    for p,name in zip(paths,names):
        end=raw.index(b"\n",offset);header=raw[offset:end].split();require(header[1]==b"blob","Git blob type")
        size=int(header[2]);data=raw[end+1:end+1+size];require(data==p.read_bytes(),"Git changed evidence bytes "+name)
        digests[name]=hashlib.sha256(data).hexdigest();offset=end+size+2
    require(offset==len(raw),"Git batch parse")
    save(D/"git-blob-verification.json",dict(status="O3_ALL_STAGED_EVIDENCE_BYTES_PASS",files=len(paths),blob_sha256=digests))
    subprocess.run(["git","commit","-m","test(o3): seal paired GEMV application evidence and native replay"],cwd=R,check=True,stdout=subprocess.PIPE)
    commit=git("rev-parse","HEAD").decode().strip();require(not git("status","--porcelain").strip(),"working tree not clean")
    save(D/"git-delivery.json",dict(status="LOCAL_O3_COMMIT_COMPLETE",commit=commit,branch="local/o3-gemv-20261019",
                                   working_tree_clean=True,github_pushed=False))
    shutil.copytree(A,V/"evidence/20261020-application",dirs_exist_ok=True)
    shutil.copytree(D,V/"Git交付",dirs_exist_ok=True)
    shutil.copy2(R/"team/workloads/o3-gemv/README.md",V/"software/README.md")
    table=(W/"results-03/结果与工程记录.md").read_text()
    V.joinpath("README.md").write_text("# O3应用测试完成\n\n真实测量、Linux原始日志严格重审、Windows原生全量离线复算均通过；本地保存，未推送GitHub。\n\n"
        +"[全部结果及解释](results/结果与工程记录.md) · [配对CSV](results/comparison.csv) · [较快RVV对照](results/best-rvv.csv)\n\n"
        +"[Windows复算](windows-portable-audit.json) · [证据入口](evidence/20261020-application/README.md) · [本地提交](Git交付/git-delivery.json)\n\n"
        +"本地分支local/o3-gemv-20261019，提交"+commit+"。O4/O5/G5及最终采用仍待后续，正式T16报告继续后置。\n\n"+table,encoding="utf-8")
    STATE.update(status="O3_MEASURE_AUDIT_ARCHIVE_NATIVE_AND_LOCAL_DELIVERY_COMPLETE",finished_utc=now(),commit=commit,
                 jobs=56,windows=1280,measured_windows=768,replay_jobs=4)
    state();save(V/"delivery-complete.json",STATE);save(V/"Git交付/final-state.json",STATE)
    print(json.dumps(STATE,ensure_ascii=False),flush=True)
except Exception as exc:
    STATE.update(status="FAILED",error=repr(exc),finished_utc=now());state()
    save(V/"交付状态.json",STATE)
    print(json.dumps(STATE,ensure_ascii=False),flush=True)
    raise
