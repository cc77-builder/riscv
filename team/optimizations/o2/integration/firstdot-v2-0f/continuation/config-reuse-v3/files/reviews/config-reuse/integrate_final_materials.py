"""Copy verified nondefault sources and compact evidence; never commit/push."""
from pathlib import Path
import json,hashlib,shutil,subprocess
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026")
M=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
D=W/"reviews/config-reuse";O=W/"config-reuse-clean02-02"
L=M/"team/optimizations/o2/integration/firstdot-v2-0f"
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
def main():
    final=read(D/"final-result-01/record.json")
    assert len(read(M/"team/docs/version-data-ledger.json")["records"])==24
    assert read(O/"audit-02.json")["status"]=="PROBE_LOCAL_RAW_AUDIT_PASS"
    assert final["production_RTL_changed"] is False and final["stable_default_changed"] is False
    plan=read(D/"main-integration-plan-01.json")
    manifest=read(D/"adapter-v3/import-manifest.json")
    assert len(plan["new_nondefault_software_files"])==26
    before=subprocess.check_output(["git","diff","HEAD","--","src"],cwd=M)
    assert not before
    for row in manifest["already_present_dependencies"]:
        p=M/row["path"];assert p.is_file() and sha(p)==row["sha256"] and p.stat().st_size==row["bytes"]
    for row in plan["new_nondefault_software_files"]:
        src=W/"clean-02/checkout/source"/row["path"];target=M/row["path"]
        assert str(target)==row["target"] and not target.exists()
        raw=src.read_bytes();assert len(raw)==row["bytes"] and hashlib.sha256(raw).hexdigest()==row["sha256"]
    for row in plan["new_nondefault_software_files"]:
        src=W/"clean-02/checkout/source"/row["path"];target=M/row["path"]
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
        assert sha(target)==row["sha256"]
    dst=L/"continuation/config-reuse-v3";assert not dst.exists();dst.mkdir()
    selected=set()
    for name in ["adapter-v2","adapter-v3","audit-scope-fix-v1"]:
        selected.update(p for p in (D/name).iterdir() if p.is_file())
    for name in ["run_image_scope_retry_v3.py","ROOT_REVIEW.image-scope-v3-01.json","pipeline-state-01.json",
      "ROOT_REVIEW.clean02-20261027-01.json","main-integration-plan-01.json","archive_probe_v3.py",
      "finalize_probe_record.py","integrate_final_materials.py","IMAGE_SCOPE_FIX.md"]:
        selected.add(D/name)
    for pattern in ["adapter-v3-tests-01.command.*","adapter-v3-tests-02.command.*","audit-scope-tests-01.command.*"]:
        selected.update(D.glob(pattern))
    for name in ["record.json","RESULT.md","append-verification.json"]:selected.add(D/"final-result-01"/name)
    for root in [W/"config-reuse-clean02-01",O]:
        # Compact root/command proofs and per-process raw UART/derived metadata.
        selected.update(p for p in root.iterdir() if p.is_file() and p.suffix==".json")
        for rel in ["run-01/state.json","run-01/results.json","run-01/runtime-inputs.json",
         "run-01/configuration.json","run-01/hardware-profile.json","build-01/images.json",
         "build-01/pairs.json","build-01/state.json","build-01/probe-build.json","build-01/baseline-current.json"]:
            if (root/rel).is_file():selected.add(root/rel)
        for p in (root/"run-01/runs").glob("*/*"):
            if p.is_file() and (p.name=="stdout.log" or p.suffix==".json"):selected.add(p)
    for pattern in ["config-reuse-clean02-pipeline-01.command.*","config-reuse-v3-pipeline-01.command.*","config-reuse-audit-fix-01.command.*"]:
        selected.update(W.glob(pattern))
    archive=W/"reviews/config-reuse-final-archive-01"
    selected.update([archive/"manifest.json",archive/"verification.json"])
    rows=[]
    for src in sorted(selected):
        assert not src.is_symlink()
        target=dst/"files"/src.relative_to(W);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(src.read_bytes());assert sha(target)==sha(src)
        rows.append(dict(original=str(src),stored=str(target.relative_to(dst)),bytes=src.stat().st_size,sha256=sha(src)))
    save(dst/"source-snapshot.json",dict(status="SOURCE_AND_COMPACT_EVIDENCE_BYTE_SNAPSHOT_PASS",files=rows,
      source_import=manifest,imported_main_files=26,dependencies_unchanged=39,
      omitted_large_raw_bytes_location=str(archive),portable_reproduction=False,production_RTL_changed=False))
    shutil.copyfile(D/"final-result-01/RESULT.md",dst/"RESULT.md")
    (dst/"README.md").write_text("# 当前硬件配置复用筛选：V3\n\n"+
      "结论见[RESULT.md](RESULT.md)。26个r2-config-reuse文件按fcf4a11原字节引入，39个原有依赖核对不变；该目录原有RESULT/README中的身份与成绩属于上游历史，不能当成本机0f成绩。当前资格只以此处V3结果和版本档案第24条为准。\n\n"+
      "上游候选和冻结检查器未修改；V3仅修复测试适配器中的对照BIN角色绑定。旧V2失败和61项主机验证一并保留。合同快照开头的准备期草稿/未执行说明也保留，实际执行由ROOT_REVIEW和最终state证明；当前结论以本目录RESULT为准。源码及紧凑运行证据在files/，source-snapshot.json逐项校验。完整stderr、构建字节和原始封存仍在本地config-reuse-final-archive-01，按manifest可找到；档案不独立替代外部物理输入。\n\n"+
      "脚本的绝对路径和哈希是该固定实验的真实执行身份；这里是来源快照，不是修改路径即可用于任意仓库的通用入口。当前生产RTL/default未改变，没有整分支merge或GitHub推送。\n")
    assert subprocess.check_output(["git","diff","HEAD","--","src"],cwd=M)==before
    save(D/"main-integration-receipt-01.json",dict(status="NONDEFAULT_26_FILES_AND_COMPACT_EVIDENCE_INTEGRATED",
      upstream=manifest["upstream_ref"],new_source_files=26,dependencies_unchanged=39,snapshot_files=len(rows),
      snapshot_bytes=sum(x["bytes"] for x in rows),snapshot_sha256=sha(dst/"source-snapshot.json"),
      production_RTL_unchanged=True,default_changed=False,git_commit_created=False,github_pushed=False,
      finished=datetime.now(timezone.utc).isoformat()))
    print("MAIN_NONDEFAULT_SOURCE_AND_EVIDENCE_INTEGRATION_PASS",len(rows))
if __name__=="__main__":main()
