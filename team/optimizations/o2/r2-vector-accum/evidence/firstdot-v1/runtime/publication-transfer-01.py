from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,sys
payload=json.loads(r'''{"source_pins":{"firstdot_candidate.py":"79c1c808ac7e46560ed470028fb50487b31da478e43d9f1d83d770f089cc285d","firstdot_gate.py":"fc11387899bab8b2d1ecfa074edfb52e939c15869032b4457043acf288564b3b","firstdot_experiment.py":"90ade1455659db25c4b3fabe3f79f75cb65f84f340ba3d8c62c4b6422e49b560","firstdot_evidence.py":"8277ed69207c7d513b65a9b567ae15a09a8a735d728a775097f3af6adb703377","firstdot_c_api.py":"073d6dab0e6c172ea295392a34e39091950ba373f6f1280ac5f53881b532a6e7","firstdot_c_evidence.py":"e943b2b7495c0ddf92a81d08f996e82048f99b0d8e406ce9993b4d05556b461e","firstdot_library.py":"352feda875d9403a59c5824e8e315a561e7ac695cf57971d85a1669ff9246a8a","test_firstdot.py":"c9c70bea1f6151f6fe0c4d94aa1d413d54b3ec1af5e16502e61f235eb1522c0b","test_firstdot_evidence.py":"06197893745fcf3d56c0af2626e08088e988806630b8350861a9eb2c466e44b2","test_firstdot_c_api.py":"efeb26c1f70d484c08b06496472562fb6717c2a2a84b307c503efc84cbdd6a67","FIRSTDOT_CONTRACT.md":"39ef1299ab576867a8bc0edadb2ae6e728e11b4d75e395df5270be1a1c698e45","FIRSTDOT_C_CONTRACT.md":"e0d960c85094ce1c2c6c1c39fdef2f09d690847c8137eea49ee0668b70ad32e8","FIRSTDOT_README.md":"9a36ada73895a1e8cc609e706acf508e809dbf93f4dc00cee426e4b0297a6962"},"documents":[{"relative":"team/optimizations/o2/r2-vector-accum/FIRSTDOT_RESULT.md","sha256":"32f6970d256daf270523c2ad60e2cbead1191fb62769b4d4eaaff94260bdef48"},{"relative":"team/docs/development-route-current.md","sha256":"ab8b864d9d6b6a5396479fdb8a80ef2b777c9fe57a4aaa972a17de35499c4446"},{"relative":"team/optimizations/o2/r2-vector-accum/README.md","sha256":"a69aa6518251950fe9bd94025d489998a2802f7043cbc845b139e5c21507519b"},{"relative":"开发计分板.md","sha256":"ab9b1134965a8e1aee4509a4d137069f3c5bf3fa1fcf77b19519b477bc4826e3"}],"document_receipts":[{"operation_id":"1bcd341bbd2162e3d9e297ccd2678ca0.5e887c7c9d0036d5b458bbb8f9c45abc","status":"succeeded","items":[{"after_sha256":"32f6970d256daf270523c2ad60e2cbead1191fb62769b4d4eaaff94260bdef48","applied":"true","bytes_written":16523,"index":0,"operation":"write_text","path":"D:\\Projects\\competitions\\2026-10-CIE-RISCV-XiangShan\\working-firstdot-20261024-1458\\team\\optimizations\\o2\\r2-vector-accum\\FIRSTDOT_RESULT.md","status":"succeeded"}]},{"operation_id":"1bcd341bbd2162e3d9e297ccd2678ca0.432085c803fdd160f2e58892dddfcc95","status":"succeeded","items":[{"after_sha256":"ab8b864d9d6b6a5396479fdb8a80ef2b777c9fe57a4aaa972a17de35499c4446","applied":"true","before_sha256":"729b7295a1417b4c91e4a234616fca0a5abb066b448e082f802fa0a872651ee4","bytes_written":22303,"index":0,"operation":"write_text","path":"D:\\Projects\\competitions\\2026-10-CIE-RISCV-XiangShan\\working-firstdot-20261024-1458\\team\\docs\\development-route-current.md","status":"succeeded"}]},{"operation_id":"1bcd341bbd2162e3d9e297ccd2678ca0.b36149ad089b60431128898e90b08eec","status":"succeeded","items":[{"after_sha256":"a69aa6518251950fe9bd94025d489998a2802f7043cbc845b139e5c21507519b","applied":"true","before_sha256":"085227fbe308a25907b3e8563a751ca758f583c2dd68bbc9ed5f8e843d5b520b","bytes_written":14420,"index":0,"operation":"write_text","path":"D:\\Projects\\competitions\\2026-10-CIE-RISCV-XiangShan\\working-firstdot-20261024-1458\\team\\optimizations\\o2\\r2-vector-accum\\README.md","status":"succeeded"}]},{"operation_id":"1bcd341bbd2162e3d9e297ccd2678ca0.41e479f328aaba95fd76cbcf44299d0f","status":"succeeded","items":[{"after_sha256":"ab9b1134965a8e1aee4509a4d137069f3c5bf3fa1fcf77b19519b477bc4826e3","applied":"true","before_sha256":"4421e826742e048d228261d6f26b4b9359dc7832565beb7b55bb990341694ab6","bytes_written":28016,"index":0,"operation":"write_text","path":"D:\\Projects\\competitions\\2026-10-CIE-RISCV-XiangShan\\working-firstdot-20261024-1458\\开发计分板.md","status":"succeeded"}]}],"snapshot_receipt":{"operation_id":"1bcd341bbd2162e3d9e297ccd2678ca0.e90519fd63309bc81d3b1e12dc591eb7","status":"succeeded","started_at":"2026-10-24T08:53:51.9450117Z","updated_at":"2026-10-24T08:54:37.1834866Z","script_sha256":"d6fe839b0c68e79d044b75c90505039938574e09728a4c100dd8549768ffefe1","execution_sha256":"bf784f816d9f38a8302ffd3d08371fb639d2eab8114de559d792bcd942671eba","result":{"exit_code":0,"cleanup_complete":true,"duration_ms":45189}}}''')
root=Path("/home/lizufan/riscv-lab/r2s1-firstdot-20261024-1458")
repo=root/"source"
win=Path("/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/working-firstdot-20261024-1458")
rel=Path("team/optimizations/o2/r2-vector-accum")
mod=repo/rel; ev=mod/"evidence/firstdot-v1"
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write("\n")
def copy_new(src,dst):
    assert src.is_file() and not src.is_symlink() and not dst.exists(),str(dst)
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    assert sha(src)==sha(dst)
    return dict(source=str(src),destination=str(dst),sha256=sha(src),bytes=src.stat().st_size)
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()=="137b44befb041439a018a1079577cc000df1ee03"
for name,digest in payload["source_pins"].items():
    assert sha(mod/name)==sha(win/rel/name)==digest,name
public=mod/"firstdot/public"
assert sha(public/"gemv.S")=="1e1aa8ca665559efa6acab2648f4614c6121422aaf400d78c192e6accad5da47"
assert sha(public/"gemv.h")=="8ff3e08d098f000962beeaf898730939ee83bd4ea8eaf9be1c03c80f93c9db83"
doccopies=[]
for d in payload["documents"]:
    relative=Path(d["relative"]); src=win/relative; dst=repo/relative
    assert sha(src)==d["sha256"]
    if dst.exists(): copy_new(dst,ev/"runtime/pre-publication-docs"/relative)
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    assert sha(dst)==d["sha256"]
    doccopies.append(dict(relative=relative.as_posix(),sha256=sha(dst),bytes=dst.stat().st_size))
save(ev/"runtime/publication-document-transfers.json",dict(status="FIRSTDOT_FINAL_DOCUMENTS_WINDOWS_TO_NATIVE_MATCH",created=now(),files=doccopies,file_operation_receipts=payload["document_receipts"]))
save(ev/"runtime/snapshot-detached-03-tool-receipt.json",payload["snapshot_receipt"])
copy_new(Path(__file__),ev/"runtime/publication-transfer-01.py")
states={}
for name in ("run-probe-01","run-extension-01","c-run-01"):
    s=read(root/name/"state.json")
    assert s.get("active_pid") is None and s.get("active_result") is None and s.get("finished"),name
    states[name]={k:s.get(k) for k in ("status","started","finished","active_pid","active_result","new_emu_runs")}
locations=dict(
    status="FIRSTDOT_ENGINEERING_QUALIFIED_PUBLICATION_TRACKED_IN_ISSUE",
    operation_id="20261024-LiZufan001-r2s1-firstdot-1458",
    actor="@LiZufan001 / Agent",
    started_utc="2026-10-24T06:57:51+00:00",
    created_utc=now(),
    primary_windows_entry=r"D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\working-zufan-full-20261022",
    primary_entry_initial_head="ff58e519091f273c4bc177f5e82cfbbfaf102cc5",
    primary_entry_not_modified=True,
    windows_worktree=r"D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\working-firstdot-20261024-1458",
    windows_branch="work/r2s1-firstdot-20261024-1458",
    source_base="137b44befb041439a018a1079577cc000df1ee03",
    native_root=str(root),native_source=str(repo),
    detached_root="/home/lizufan/riscv-lab/r2s1-firstdot-detached-20261024-1458",
    detached_snapshot="runtime/detached-source-snapshot.json",
    detached_scope="source-only base checkout with hash-verified uncommitted candidate delta; no hardlinks/alternates, root build or out; Python access guard is not an OS sandbox",
    frozen_source_sha256=payload["source_pins"],
    hardware=dict(source="34bae6d4acceac939f958199dae53c14bc1f6183",identity_sha256="4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb",emu_sha256="ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f",normal_reference_sha256="8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9",physical_root="/home/lizufan/riscv-lab/t17-clean-20261024-0854",rtl_changed=False,new_synthesis=False),
    native_builds=[str(root/n) for n in ("build-probe-01","build-8x32-rest-01","build-other-shapes-01","c-build-01")],
    native_runs={name:dict(path=str(root/name),state=s) for name,s in states.items()},
    execution=dict(total_emu=36,normal_emu=34,expected_negative_emu=2,performance_emu=33,c_emu=3,formal_images=24,measured_windows=384,replay_processes=8,replay_window_pairs=192,c_distinct_cases=48,c_normal_case_executions=96,maximum_cpu_budget=4,affinity="0-3",performance_emu_serial=True,active_run_pids=[]),
    native_archive_map={"probe-archive":str(root/"probe-archive-01"),"matrix-archive":str(root/"matrix-archive-01"),"c-archive":str(root/"c-archive-01"),"library":str(root/"library-01"),"usage-check":str(root/"usage-check-02")},
    manifest_sha256={"probe":"3d2381aad71671b03ecb5ac3250db093df3b7bbf1ca987a1c23f98073d6d5f91","matrix":"0c8d3159c91aa3c934c7bfb7f2640906844246e812c0b5bfc556cdfb86d0d3b4","c":"47859f1c12d5311ef554803c6976c8699ebafc164e2bdd876cfd0c6a6f2a2ec1"},
    attempts=dict(selected_receipts="runtime/selected-tool-receipts.json",detached_final_receipt="runtime/snapshot-detached-03-tool-receipt.json",prior_sources="prior-attempts",notes=["Post-C driver completed C export/archive/audit/library/host rejection checks before README regex failed due to cross-shell backtick expansion; only remaining example work ran in usage-check-02.","Snapshot attempt01 failed before WSL start due to command line length; attempt02 copied a malformed script but did not execute its body; attempt03 completed after local syntax validation.","Immutable archives, all successful EMU runs, and qualified library builds were not repeated."]),
    publication=dict(target="cc77-builder/riscv:zufan",expected_remote_before_integration="137b44befb041439a018a1079577cc000df1ee03",actual_commit_and_window="https://github.com/cc77-builder/riscv/issues/2",check="reports/publication-check-01.json",report_self_excluded_from_own_inventory=True,report_staged_identity_verification="required before commit; native index report self excluded and checked separately"),
    boundaries=dict(stable_r5_changed=False,full_application_performance_measured=False,asic_ppa_measured=False,new_machine_installation=False,human_ack=False,whole_competition_acceptance=False),
    next_optional="R2-S3: prove repeated vector configuration removal and vstart/normal-completion state, optimize RVV equally, then screen 8x32/d0 before expanding."
)
save(ev/"runtime/locations.json",locations)
save(ev/"runtime/independent-review-01.json",dict(status="NO_BLOCKING_FINDINGS",created=now(),reviewer="cloud /root/independent_review, read-only Agent review, not human ACK",result_sha256="32f6970d256daf270523c2ad60e2cbead1191fb62769b4d4eaaff94260bdef48",readme_sha256=payload["source_pins"]["FIRSTDOT_README.md"],scope=["core and C adapter review","performance and evidence boundaries","final result counts and ordinary C negative PC","library object bytes and weak/strong undefined-symbol distinction","detached base plus explicit delta boundary","publication checker sole scoreboard CRLF normalization"],new_pc_operations=0,new_tests=0))
copied=[]
for sub in ("firstdot","evidence/firstdot-v1"):
    src=mod/sub; dst=win/rel/sub
    assert src.is_dir() and not dst.exists(),str(dst)
    dst.mkdir(parents=True)
    for p in sorted(src.rglob("*")):
        assert not p.is_symlink()
        if p.is_file(): copied.append(copy_new(p,dst/p.relative_to(src)))
    source_names={p.relative_to(src).as_posix() for p in src.rglob("*") if p.is_file()}
    dest_names={p.relative_to(dst).as_posix() for p in dst.rglob("*") if p.is_file()}
    assert source_names==dest_names
report=dict(status="FIRSTDOT_NATIVE_TO_WINDOWS_PUBLICATION_BYTES_PASS",created=now(),source=str(repo),destination=str(win),already_equal_source_files=payload["source_pins"],documents=doccopies,files=len(copied),bytes=sum(x["bytes"] for x in copied),entries=copied,own_receipt_excluded_from_inventory=True)
save(ev/"reports/publication-transfer-01.json",report)
copy_new(ev/"reports/publication-transfer-01.json",win/rel/"evidence/firstdot-v1/reports/publication-transfer-01.json")
print(json.dumps(dict(status=report["status"],files=report["files"],bytes=report["bytes"],report_sha256=sha(ev/"reports/publication-transfer-01.json"),states=states),indent=2),flush=True)
