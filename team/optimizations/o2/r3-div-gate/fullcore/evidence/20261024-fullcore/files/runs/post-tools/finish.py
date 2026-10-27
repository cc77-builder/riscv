#!/usr/bin/env python3
"""Seal only a completed R3 DIV-gate full-core campaign; no Git/network writes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, shutil, subprocess, time

REPO = Path(__file__).resolve().parents[5]
WORK = REPO.parents[1] / "o2-r3-div-gate-fullcore-20261024"
ENTRY = Path(__file__).resolve().parent
DELIVERY = REPO.parents[1] / "o2-r3-div-gate-fullcore-delivery-20261024"
ARCHIVE = ENTRY / "evidence/20261024-fullcore"
WINDOWS = Path("/mnt/d/yanyi/riscv大赛/doc/R3_DIV关钟修复全核回归_20261024")
SOURCE = "0f12df675378556670afd0dd2153f47fcb330610"
OLD_EMU = "e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def need(ok, message):
    if not ok: raise ValueError(message)
def save(p, value):
    p = Path(p); t = p.with_suffix(p.suffix + ".tmp")
    t.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    t.replace(p)
def run(name, cmd):
    started = now()
    with (DELIVERY / (name + ".stdout.log")).open("xb") as out, (DELIVERY / (name + ".stderr.log")).open("xb") as err:
        rc = subprocess.run(cmd, cwd=REPO, stdout=out, stderr=err).returncode
    save(DELIVERY / (name + ".command.json"), dict(command=cmd, started=started, finished=now(), exit_code=rc))
    need(rc == 0, name + " failed")

def main():
    DELIVERY.mkdir(exist_ok=False)
    state = dict(status="WAITING", started=now(), pid=os.getpid())
    statefile = DELIVERY / "finish-state.json"
    save(statefile, state)
    try:
        while True:
            campaign = read(WORK / "campaign-state.json")
            if campaign["status"] == "passed": break
            need(campaign["status"] == "running", "campaign failed; inspect original evidence")
            time.sleep(15)
        state["status"] = "CHECKING"; save(statefile, state)
        need(campaign.get("candidate_source_unchanged") is True, "source completion missing")
        need(len(campaign["steps"]) == 7 and all(x["status"] == "passed" and x["exit_code"] == 0 for x in campaign["steps"]), "incomplete campaign")
        core = read(WORK / "core-01/result.json")
        supp = read(WORK / "supplements-01/result.json")
        audit = read(WORK / "recheck-01/result.json")
        pins = read(WORK / "build-01/hardware-inputs.json")
        need(audit["status"] == "O2_G3_OFFLINE_RECHECK_PASS" and audit["whole_suite_pass"] and audit["g3_complete"], "strict recheck failed")
        need(audit["normal_reference_recovery"] and audit["original_evidence_unchanged"], "recovery/evidence failed")
        need(audit["missing_jobs"] == [] and audit["missing_components"] == [], "missing jobs")
        need(pins["source_commit"] == SOURCE and pins["emu_sha256"] != OLD_EMU and sha(REPO / "build/emu") == pins["emu_sha256"], "new hardware identity failed")
        for rel, digest in read(WORK / "identity.json")["files"].items():
            need(sha(REPO / rel) == digest, "candidate source drift: " + rel)
        rows = core["runs"] + supp["runs"]
        normal = [x for x in rows if x["name"] != "negative-vdot"]
        negative = [x for x in rows if x["name"] == "negative-vdot"]
        need(len(rows) == len({x["name"] for x in rows}) == 14 and len(normal) == 13 and len(negative) == 1, "wrong inventory")
        need(negative[0]["status"] == "EXPECTED_VDOT_HIGHBIT_REJECTION" and negative[0]["exit_code"] != 0, "negative failure missing")
        need(all(x["exit_code"] == 0 and x["observation_status"] == "O2_TRACE_PASS" for x in normal), "normal trace failed")
        tests = 0
        for name, count in (("host-fullcore.log", 94), ("host-workloads.log", 16)):
            text = (WORK / name).read_text()
            need(re.search(r"Ran " + str(count) + r" tests in", text) and text.rstrip().endswith("OK"), "host check failed")
            tests += count
        rtl = REPO / "build/rtl/VDotElastic.sv"
        text = rtl.read_text()
        need(re.search(r"reg\s+\[31:0\]\s+rPacket_res_data\s*;", text), "missing H1 result32")
        need(re.search(r"assign\s+io_out_bits_res_data\s*=\s*\{96'h0,\s*rPacket_res_data\};", text), "missing full128 output")
        generated = read(WORK / "build-01/generated-artifacts.json")
        need(any(x["path"] == "build/rtl/VDotElastic.sv" and x["sha256"] == sha(rtl) for x in generated), "generated RTL unbound")
        coverage = {k: sum(x["count"] for x in v) for k,v in audit["suite_coverage"]["sources"].items()}
        need(audit["suite_coverage"]["complete"] and len(coverage) == 6 and all(coverage.values()), "coverage incomplete")
        summary = dict(status="R3_DIV_GATE_FULLCORE_PASS", finished=now(), source_commit=SOURCE,
            emu_sha256=pins["emu_sha256"], normal_jobs=13, expected_negative_jobs=1,
            normal_vdot_commits=sum(x["observation_counts"].get("COMMIT",0) for x in normal),
            matrix_unique=core["matrix_unique"], matrix_executed=core["matrix_executed"],
            host_tests=tests, coverage=coverage, normal_reference_recovery=True,
            hardware_sources_git_verified=audit["hardware_source_git_blobs_verified"],
            dependency_files_verified=audit["dependency_files_verified"],
            normal_reference_sha256="efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4",
            negative_reference_sha256="9b3aecf362b7c7ddb4f8bace355c2e0ee2cc919fd5f59eefc641db220ab40df0",
            h1_storage_bits=32, public_result_bits=128, new_performance_ab=False,
            new_ppa=False, github_push=False, human_ack=False)
        save(WORK / "final-validation.json", summary)
        shutil.copyfile(rtl, WORK / "source/VDotElastic.generated.sv")
        tools = WORK / "post-tools"; tools.mkdir()
        for p in ENTRY.glob("*.py"): shutil.copyfile(p, tools / p.name)
        note = "# R3 DIV取消关钟修复：全核构建与NEMU差分结果\n\n"
        note += "本轮完成新EMU构建、14项实际全核作业和严格原文复算。源码为O2＋H1＋DIV取消关钟修复。\n\n"
        note += "本地硬件提交：" + SOURCE + "；EMU SHA256：" + pins["emu_sha256"] + "。\n\n"
        note += "- 13项正常差分通过，1项bit100负控被DiffTest按预期拒绝，随后同镜像正常库恢复通过。\n"
        note += "- 117唯一功能/异常case，8分片执行124次；正常提交" + str(summary["normal_vdot_commits"]) + "条vdot。\n"
        note += "- hello/vadd、控制、dense及两项补充诊断通过；110项主机测试通过。\n"
        note += "- 严格复算核对" + str(summary["hardware_sources_git_verified"]) + "份硬件源码和" + str(summary["dependency_files_verified"]) + "份依赖；完整128位结果和O2控制检查保持。\n\n"
        note += "| O2覆盖 | 次数 |\n| --- | ---: |\n"
        for k,v in coverage.items(): note += "| " + k + " | " + str(v) + " |\n"
        note += "\n配置为MinimalConfig/单核/单线程EMU，O2及T14融合开启、O1关闭，O2/T13观察开启。NEMU/镜像/观察器和判据沿用固定合同。\n\n"
        note += "本轮只证明整核正确性与差分链路；取消后零多余时钟脉冲证据仍来自前轮真实父级严格检查。未做新公平周期A/B、综合STA、功耗测量或运行期全核reset，不代签人工验收。\n\n"
        note += "旧H1 build保存在/home/riscv/riscv-lab/o2-h1-build-before-r3-div-gate-20261024。当前build/emu是修复版。下一步以同镜像进行修复前后周期不退化检查，再做同约束成本/STA。\n\n"
        note += "仅本地提交，无GitHub推送。原始工作根：" + str(WORK) + "。\n\n"
        note += "查看[合同](CONTRACT.md)、[封存清单](evidence/20261024-fullcore/archive-manifest.json)；原始命令、退出码、日志及生成物哈希随证据保存。\n"
        (ENTRY / "RESULT.md").write_text(note)
        (WORK / "RESULT.md").write_text(note)
        state["status"] = "ARCHIVING"; save(statefile,state)
        run("archive", ["python3","-B",str(ENTRY / "archive_local.py"),"--work-root",str(WORK),"--output",str(ARCHIVE)])
        run("portable-linux", ["python3","-B","team/optimizations/o2/fullcore/portable.py","--archive",str(ARCHIVE),"--core-campaign","core-01","--supplement-campaign","supplements-01","--output",str(DELIVERY / "portable-linux.json")])
        reviews = ENTRY / "reviews"; reviews.mkdir()
        for p in DELIVERY.iterdir():
            if p.is_file() and p.name != "finish-state.json": shutil.copyfile(p,reviews / p.name)
        shutil.copytree(ENTRY, WINDOWS / "fullcore")
        records = {}
        for p in ENTRY.rglob("*"):
            if p.is_file():
                rel=p.relative_to(ENTRY); target=WINDOWS / "fullcore" / rel
                need(p.read_bytes()==target.read_bytes(),"Windows copy differs: "+str(rel))
                records[str(rel)]=dict(sha256=sha(p),bytes=p.stat().st_size)
        save(WINDOWS / "delivery-manifest.json",dict(status="R3_FULLCORE_WINDOWS_COPY_PASS",files=records,time=now()))
        (WINDOWS / "README.md").write_text("# R3 DIV关钟修复全核回归\n\n见[结果](fullcore/RESULT.md)。本地验证，不上传GitHub。\n")
        state.update(status="R3_FULLCORE_DELIVERY_READY",finished=now(),emu_sha256=pins["emu_sha256"],portable_linux_pass=True,windows_copy_pass=True)
    except BaseException as e:
        state.update(status="FAILED",error=repr(e),finished=now())
        raise
    finally:
        save(statefile,state)

if __name__ == "__main__": main()
