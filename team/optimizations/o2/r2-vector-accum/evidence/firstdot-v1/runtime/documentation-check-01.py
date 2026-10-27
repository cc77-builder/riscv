from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import unquote,urlsplit
import hashlib,json,re,shutil,unicodedata
repo=Path("/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/working-firstdot-20261024-1458")
native=Path("/home/lizufan/riscv-lab/r2s1-firstdot-20261024-1458/source")
module=Path("team/optimizations/o2/r2-vector-accum")
evidence=module/"evidence/firstdot-v1"
names=[module/x for x in ("FIRSTDOT_CONTRACT.md","FIRSTDOT_C_CONTRACT.md","FIRSTDOT_README.md","FIRSTDOT_RESULT.md","README.md")]
names += [Path("team/docs/development-route-current.md"),Path("开发计分板.md")]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def anchors(p):
    text=p.read_text(encoding="utf-8"); found=set(re.findall(r'<a\s+id=["\x27]([^"\x27]+)',text)); used={}
    for line in text.splitlines():
        m=re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$",line)
        if not m: continue
        h=re.sub(r"\[([^\]]+)\]\([^)]*\)",r"\1",m.group(1)).replace(chr(96),"").lower()
        h="".join(c for c in h if c in "_-" or c.isspace() or unicodedata.category(c)[0] in "LMN")
        slug=h.replace(" ","-"); n=used.get(slug,0); used[slug]=n+1
        found.add(slug+("-"+str(n) if n else ""))
    return found
rows=[]; links=[]; external=0; anchor_checks=0
for rel in names:
    p=repo/rel; data=p.read_bytes(); text=data.decode("utf-8")
    assert "@PENDING_" not in text,str(rel)
    rows.append(dict(path=rel.as_posix(),bytes=len(data),sha256=sha(p)))
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)",text):
        target=target.strip().strip("<>")
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:",target):
            external+=1; continue
        file,sep,fragment=target.partition("#")
        dst=(p.parent/unquote(file)).resolve() if file else p.resolve()
        assert dst.is_relative_to(repo.resolve()),(str(rel),target,"outside repo")
        assert dst.is_file(),(str(rel),target,"missing local file")
        if sep and fragment:
            anchor=unquote(fragment)
            assert anchor in anchors(dst),(str(rel),target,"missing anchor")
            anchor_checks+=1
        links.append(dict(document=rel.as_posix(),target=target))
score=(repo/"开发计分板.md").read_bytes().decode("utf-8")
matches=[line for line in score.split("\r\n") if line.startswith("| 20261024-LiZufan001-r2s1-firstdot-1458 / ")]
assert len(matches)==1
rest=score.replace(matches[0]+"\r\n\r\n","",1)
assert hashlib.sha256(rest.encode()).hexdigest()=="4421e826742e048d228261d6f26b4b9359dc7832565beb7b55bb990341694ab6"
intro="当前新增的首块直接初始化子项已取得独立运行资格与可选C库，见 [Firstdot结果](FIRSTDOT_RESULT.md)、[普通C使用/复算/回退](FIRSTDOT_README.md)。原R5稳定默认入口保持不变。下文继续记录原S1与冻结v2批次，不将其旧PASS转移到新候选。\n\n"
old_readme=(repo/module/"README.md").read_bytes().decode("utf-8")
assert old_readme.count(intro)==1
assert hashlib.sha256(old_readme.replace(intro,"",1).encode()).hexdigest()=="085227fbe308a25907b3e8563a751ca758f583c2dd68bbc9ed5f8e843d5b520b"
report=repo/evidence/"reports/documentation-check-01.json"
result=dict(status="FIRSTDOT_PUBLICATION_DOCUMENTS_AND_HISTORY_PASS",created=datetime.now(timezone.utc).isoformat(),checker_sha256=sha(Path(__file__)),documents=rows,local_links=len(links),anchor_checks=anchor_checks,external_links_not_requested=len([1 for _ in range(external)]),original_scoreboard_bytes_preserved=True,old_s1_readme_body_bytes_preserved=True,pending_markers=0,scope="seven publication Markdown files and local links/anchors; no new engineering regression",links=links)
with report.open("x",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write("\n")
copied=[]
for rel in (evidence/"reports/publication-check-01.json",evidence/"reports/documentation-check-01.json",evidence/"runtime/documentation-check-01.py"):
    src=repo/rel; dst=native/rel
    assert src.is_file() and not dst.exists()
    shutil.copyfile(src,dst); assert sha(src)==sha(dst)
    copied.append(dict(relative=rel.as_posix(),sha256=sha(src)))
print(json.dumps(dict(status=result["status"],documents=len(rows),local_links=len(links),anchor_checks=anchor_checks,report_sha256=sha(report),native_copies=copied),indent=2))
