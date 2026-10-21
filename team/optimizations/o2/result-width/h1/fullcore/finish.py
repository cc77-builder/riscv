#!/usr/bin/env python3
"""Finish local H1 full-core evidence only after the unchanged G3 gates pass."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone

REPO = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
WORK = Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021")
DELIVERY = Path("/home/riscv/riscv-lab/o2-h1-fullcore-delivery-20261021")
ENTRY = REPO / "team/optimizations/o2/result-width/h1/fullcore"
ARCHIVE = ENTRY / "evidence/20261021-fullcore"
WINDOWS = Path("/mnt/d/yanyi/riscv大赛/doc/H1全核回归_20261021")
SOURCE = "8b5024fcbd96986871cc40ce8c9fb71a67c495eb"
B0_SHA = "ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57"
R0_SHA = "8bc49ced46926b4015b900185bd657bee13bb606a27fc6482d4f169c1766c29e"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def need(ok, message):
    if not ok:
        raise ValueError(message)

def stamp():
    return datetime.now(timezone.utc).isoformat()

def save(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temp.replace(path)

def run(name, command):
    with (DELIVERY / (name + ".stdout.log")).open("xb") as out, (DELIVERY / (name + ".stderr.log")).open("xb") as err:
        start = stamp()
        p = subprocess.run(command, cwd=REPO, stdout=out, stderr=err)
    save(DELIVERY / (name + ".command.json"), {"command": command, "started": start, "finished": stamp(), "exit_code": p.returncode})
    need(p.returncode == 0, name + " failed; inspect retained logs")

def main():
    state = {"status": "waiting_for_campaign", "pid": os.getpid(), "started": stamp()}
    state_file = DELIVERY / "finish-state.json"
    save(state_file, state)
    try:
        while True:
            campaign = read(WORK / "campaign-state.json")
            if campaign["status"] == "passed":
                break
            need(campaign["status"] == "running", "campaign did not pass")
            time.sleep(15)
        state["status"] = "validating"
        save(state_file, state)
        need(campaign.get("source_and_r0_lock_unchanged") is True, "missing frozen-source completion")
        need(len(campaign["steps"]) == 7 and all(s["status"] == "passed" and s["exit_code"] == 0 for s in campaign["steps"]), "incomplete steps")
        core = read(WORK / "core-01/result.json")
        supp = read(WORK / "supplements-01/result.json")
        check = read(WORK / "recheck-01/result.json")
        pins = read(WORK / "build-01/hardware-inputs.json")
        need(check["status"] == "O2_G3_OFFLINE_RECHECK_PASS" and check["g3_complete"] and check["whole_suite_pass"], "strict full-suite gate incomplete")
        need(check["normal_reference_recovery"] and check["original_evidence_unchanged"], "recovery or stable evidence missing")
        need(check["missing_jobs"] == [] and check["missing_components"] == [], "missing required inventory")
        need(pins["source_commit"] == SOURCE and pins["emu_sha256"] != B0_SHA, "wrong H1 hardware identity")
        need(sha(REPO / "build/emu") == pins["emu_sha256"], "new EMU drift")
        need(sha(REPO / "team/optimizations/o2/repro/baseline-lock.json") == R0_SHA, "old R0 lock changed")
        rows = core["runs"] + supp["runs"]
        need(len(rows) == 14 and len({r["name"] for r in rows}) == 14, "expected 14 unique jobs")
        negative = [r for r in rows if r["name"] == "negative-vdot"]
        normal = [r for r in rows if r["name"] != "negative-vdot"]
        need(len(negative) == 1 and negative[0]["status"] == "EXPECTED_VDOT_HIGHBIT_REJECTION" and negative[0]["exit_code"] != 0, "bit100 gate missing")
        need(all(r["exit_code"] == 0 and r["observation_status"] == "O2_TRACE_PASS" for r in normal), "normal run did not fully pass")
        for name, count in [("host-fullcore.log", 79), ("host-workloads.log", 16)]:
            body = (WORK / name).read_text()
            need(re.search(r"Ran " + str(count) + r" tests in", body) and body.rstrip().endswith("OK"), "host suite not passed")
        rtl = REPO / "build/rtl/VDotElastic.sv"
        text = rtl.read_text()
        need(re.search(r"reg\s+\[31:0\]\s+rPacket_res_data\s*;", text), "generated RTL does not store low32")
        need(re.search(r"assign\s+io_out_bits_res_data\s*=\s*\{96'h0,\s*rPacket_res_data\};", text), "generated public result not full128")
        generated = read(WORK / "build-01/generated-artifacts.json")
        match = [x for x in generated if x["path"] == str(rtl.relative_to(REPO))]
        need(len(match) == 1 and match[0]["sha256"] == sha(rtl), "generated RTL binding missing")
        coverage = {k: sum(x["count"] for x in v) for k, v in check["suite_coverage"]["sources"].items()}
        need(check["suite_coverage"]["complete"] and len(coverage) == 6 and all(x > 0 for x in coverage.values()), "O2 coverage incomplete")
        commits = sum(r["observation_counts"].get("COMMIT", 0) for r in normal)
        summary = {
            "status": "H1_FULLCORE_VALIDATION_PASS", "finished": stamp(), "source_commit": SOURCE,
            "emu_sha256": pins["emu_sha256"], "normal_reference_sha256": "efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4",
            "normal_jobs": len(normal), "expected_negative_jobs": len(negative), "normal_vdot_commits": commits,
            "matrix_unique": core["matrix_unique"], "matrix_executed": core["matrix_executed"],
            "host_tests": 95, "coverage": coverage, "generated_vdot_rtl_sha256": sha(rtl),
            "h1_local_data_storage_bits": 32, "public_result_bits": 128,
            "core_pass": core["status"], "supplements_pass": supp["status"], "recheck_pass": check["status"],
            "hardware_sources_git_verified": check["hardware_source_git_blobs_verified"],
            "dependency_files_verified": check["dependency_files_verified"],
            "new_performance_ab": False, "runtime_fullcore_reset_tested": False, "human_ack": False,
            "r0_b0_lock_sha256": R0_SHA,
            "input_receipts": {str(p.relative_to(WORK)): sha(p) for p in [
                WORK / "campaign-state.json", WORK / "source-freeze.json", WORK / "build-01/hardware-inputs.json",
                WORK / "core-01/result.json", WORK / "supplements-01/result.json", WORK / "recheck-01/result.json"]}}
        save(WORK / "final-validation.json", summary)
        (WORK / "source/VDotElastic.generated.sv").write_bytes(rtl.read_bytes())
        source_dir = WORK / "post-tools"
        source_dir.mkdir()
        for p in ENTRY.glob("*.py"):
            shutil.copyfile(p, source_dir / p.name)
        note = "# H1 全核构建与 NEMU 差分回归结果\n\n"
        note += "2026-10-21：**新 H1 全核构建、14 项作业与严格离线重审通过。** 本轮是功能与协同验证，未运行公平性能 A/B。\n\n"
        note += "硬件提交：" + SOURCE + "。新 EMU SHA256：" + pins["emu_sha256"] + "。\n\n"
        note += "MinimalConfig、单核/单线程EMU、O2与O2/T13观察开启；两编译线程、12G JVM。观察器保持原协议，从公开128位结果整值比较，不修改黄金数据或NEMU语义。生成RTL证实R槽32位保存、输出高96位零。\n\n"
        note += "- 13项正常完整作业通过，1项bit100故障参考库按预期被DiffTest拒绝；同镜像恢复正常库通过。\n"
        note += "- 原矩阵117个唯一用例（80合法/37异常），8分片执行124次；hello/vadd、F2v、dense和两个补充诊断均通过。\n"
        note += "- 正常程序共" + str(commits) + "条vdot提交；95项主机检查通过。完整128位、身份/perf、反压、取消与正常排空按原门禁验证。\n\n"
        note += "| 全核O2覆盖 | 实际计数 |\n| --- | ---: |\n"
        for key, value in coverage.items():
            note += "| " + key + " | " + str(value) + " |\n"
        note += "\n严格重审从原始stdout/stderr、真实退出码、已固定Git blob、硬件pins、输入来源重新复算；不是只检查成功字符串。核对" + str(check["hardware_source_git_blobs_verified"]) + "份硬件源和" + str(check["dependency_files_verified"]) + "份依赖文件。\n\n"
        note += "已有局部面积收益仍为FU约2.334%、完整父级约0.137%，此前ready负载退化与1ns未收敛限制保持。全核正确性通过不改变该物理时序结论；没有本轮新加速比、运行期全核reset、功耗或真实工艺Fmax证据。\n\n"
        note += "当前repo/build/emu已是H1；B0原构建完整保存在/home/riscv/riscv-lab/o2-b0-build-before-h1-20261021，R0锁继续绑定B0。下一步为同镜像B0/H1周期不退化检查，R4独立成员复现/最终采用仍待完成。没有推送GitHub，自动审查不代替队友ACK。\n\n"
        note += "原始证据根：/home/riscv/riscv-lab/o2-h1-fullcore-20261021。核心证据为campaign-state、build-01、core-01、supplements-01、recheck-01及final-validation.json。\n\n"
        note += "可复现命令见[合同](CONTRACT.md)、launch.py与归档；已完成campaign不可重复启动。新运行应使用新目录。归档入口[evidence/20261021-fullcore/archive-manifest.json](evidence/20261021-fullcore/archive-manifest.json)；归档字节/便携轨迹复核不等于重新运行EMU，也不代替Linux来源核验。\n"
        (ENTRY / "H1_FULLCORE_RESULT.md").write_text(note)
        (WORK / "H1_FULLCORE_RESULT.md").write_text(note)
        state["status"] = "archiving"
        save(state_file, state)
        run("archive", ["python3", "-B", "team/optimizations/o2/fullcore/archive.py", "--work-root", str(WORK), "--output", str(ARCHIVE)])
        run("portable-linux", ["python3", "-B", "team/optimizations/o2/fullcore/portable.py", "--archive", str(ARCHIVE), "--core-campaign", "core-01", "--supplement-campaign", "supplements-01", "--output", str(DELIVERY / "portable-linux.json")])
        state["status"] = "copying_windows"
        save(state_file, state)
        shutil.copytree(ENTRY, WINDOWS / "fullcore", dirs_exist_ok=True)
        records = {}
        for p in sorted(ENTRY.rglob("*")):
            if p.is_file():
                rel = p.relative_to(ENTRY)
                target = WINDOWS / "fullcore" / rel
                need(p.read_bytes() == target.read_bytes(), "Windows copy differs: " + str(rel))
                records[str(rel)] = {"sha256": sha(p), "bytes": p.stat().st_size}
        save(WINDOWS / "delivery-manifest.json", {"status": "H1_FULLCORE_WINDOWS_COPY_PASS", "files": records, "source": str(ENTRY), "time": stamp()})
        (WINDOWS / "README.md").write_text("# H1 全核回归已完成\n\n见[完整结果](fullcore/H1_FULLCORE_RESULT.md)。新EMU、14项作业、NEMU差分及严格离线重审通过；没有新性能A/B或GitHub推送。Linux便携归档/轨迹审计通过，Windows逐文件复制字节核对通过；原始运行保持在WSL。\n")
        shutil.copyfile(DELIVERY / "portable-linux.json", WINDOWS / "portable-linux.json")
        state.update(status="H1_FULLCORE_DELIVERY_READY", finished=stamp(),
                     result=str(ENTRY / "H1_FULLCORE_RESULT.md"), emu_sha256=pins["emu_sha256"],
                     portable_linux_pass=True, windows_copy_pass=True)
        print(state["status"], flush=True)
    except BaseException as error:
        state.update(status="FAILED", error=repr(error), finished=stamp())
        print("H1_FULLCORE_FINISH_FAILED", repr(error), flush=True)
        raise
    finally:
        save(state_file, state)

if __name__ == "__main__":
    main()
