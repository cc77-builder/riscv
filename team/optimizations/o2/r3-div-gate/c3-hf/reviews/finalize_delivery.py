from pathlib import Path
import json,shutil,hashlib,datetime
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
m=r/"team/optimizations/o2/r3-div-gate/c3-hf"
d=Path("/mnt/d/yanyi/riscv大赛/doc/C3-HF_最小范围试验_20261025")
ledger=json.loads((r/"team/docs/version-data-ledger.json").read_text())
assert len(ledger["records"])==21 and ledger["records"][-1]["record_id"]=="C3-HF-20261025-01"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pairs=[]
for p in sorted(m.rglob("*")):
 if p.is_file() and not {"evidence","__pycache__"}.intersection(p.relative_to(m).parts):
  pairs.append((p,p.relative_to(r).as_posix()))
for name in ["team/docs/version-data-ledger.md","team/docs/version-data-ledger.json","team/docs/version-data-ledger-sources.json","team/docs/development-route-current.md","开发计分板.md"]:
 pairs.append((r/name,name))
rows=[]
for p,name in pairs:
 q=d/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 a=sha(p);assert sha(q)==a,name
 rows.append(dict(path=name,sha256=a,bytes=p.stat().st_size))
readme="""# C3-HF 最小范围试验（2026-10-25）

结论：局部功能通过，成本筛选拒绝，不采用；保留 O2＋H1＋DIV 取消关钟修复 0f12df6。

- [完整试验结果](team/optimizations/o2/r3-div-gate/c3-hf/RESULT.md)
- [统一版本数据档案（新增第21条）](team/docs/version-data-ledger.md)
- [当前开发路线](team/docs/development-route-current.md)
- [本轮冻结合同](team/optimizations/o2/r3-div-gate/c3-hf/CONTRACT.md)
- [封存清单](team/optimizations/o2/r3-div-gate/c3-hf/evidence/20261025-trial/manifest.json)
- [Linux/Windows字节完整性回执](team/optimizations/o2/r3-div-gate/c3-hf/reviews/cross-platform-check.json)

只修改 FP DIV/SQRT 保持位的置位条件。22组定向及10000组随机的完整128位验证、真实父级和补充监测通过。目标FP保持位D端1.930584→0.557445ns，但面积+0.184115%超过+0.1%上限，45项路径有25项超限。因此没有进入全核或同镜像周期验证；没有新的加速比、功耗或整核Fmax结论。

本目录是本地材料副本，未上传GitHub。主线源码和EMU保持原身份，实验候选77d0a12只保存在独立工作区及补丁。下一步回到稳定集成与T17干净复现，不继续扩大本轮门控改法。

原始工程：/home/riscv/riscv-lab/zjhwork2-review-20261018/repo
本次工作区：/home/riscv/riscv-lab/o2-c3-hf-20261025

此副本只包含本轮材料及台账，台账里指向其他历史阶段的链接请到完整工程中查看。1131份载荷已无损封存，跨平台校验只验证字节完整性，不等同于再次运行硬件或EDA。
"""
(d/"README.md").write_text(readme)
rows.append(dict(path="README.md",sha256=sha(d/"README.md"),bytes=(d/"README.md").stat().st_size))
e=d/"team/optimizations/o2/r3-div-gate/c3-hf/evidence/20261025-trial/manifest.json"
assert sha(e)=="d59cb0ebaec8209a8683ce3b3f97fafabc4daedbd50e0a2e0f36caf948d3ce31"
manifest=dict(status="C3_HF_DELIVERY_FILES_COPIED",time=datetime.datetime.now().astimezone().isoformat(),files=rows,archive_manifest=dict(path=e.relative_to(d).as_posix(),sha256=sha(e)),archive_payload_files=1131)
(d/"delivery-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
(d/"delivery-state.json").write_text(json.dumps(dict(status="C3_HF_DELIVERY_COMPLETE_AWAIT_NATIVE_DOCUMENT_CHECK",files=len(rows),source=str(r),manifest="delivery-manifest.json"),indent=2)+"\n")
print(json.dumps(dict(status=manifest["status"],documents=len(rows),output=str(d)),ensure_ascii=False))
