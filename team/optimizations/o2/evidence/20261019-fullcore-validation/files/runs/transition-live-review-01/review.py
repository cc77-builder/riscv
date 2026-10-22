from pathlib import Path
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import re
import struct
import subprocess

WORK = Path("/home/riscv/riscv-lab/o2-fullcore-20261019")
REPO = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
CAMPAIGN = WORK / "supplements-02"
JOB = CAMPAIGN / "o2-diagnostic"
BUILD = WORK / "diagnostic-build-03"
OUT = WORK / "transition-live-review-01"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


result = json.loads((JOB / "result.json").read_text())
need(result["status"] == "O2_SUPPLEMENT_PASS" and result["exit_code"] == 0,
     "completed qualified diagnostic required; prefixes are not accepted")
need((JOB / "exit-code.txt").read_bytes() == b"0\n", "raw exit code mismatch")
for name, expected in result["raw_logs_sha256"].items():
    need(sha(JOB/name) == expected, "raw log drift: "+name)
need((JOB/"run.log").read_bytes() == (JOB/"stderr.log").read_bytes()+(JOB/"stdout.log").read_bytes(),
     "derived run.log differs from separate raw streams")
for name, expected in result["files"].items():
    need(sha(Path(name)) == expected, "runtime artifact drift: "+name)

preflight = json.loads((CAMPAIGN/"preflight.json").read_text())
tool_bindings = {}
for original, expected in preflight["driver_files"].items():
    rel = Path(original).relative_to(REPO)
    frozen = CAMPAIGN/"tools"/rel
    need(sha(frozen) == expected, "frozen tool drift: "+str(rel))
    blob = subprocess.check_output(["git","-C",str(REPO),"show",preflight["tool_source_commit"]+":"+str(rel)])
    need(hashlib.sha256(blob).hexdigest() == expected, "tool Git blob mismatch: "+str(rel))
    tool_bindings[str(rel)] = expected
a = load_module("transition_review_analyze", CAMPAIGN/"tools/team/optimizations/o2/fullcore/analyze.py")
checker = load_module("transition_review_workload", CAMPAIGN/"tools/team/optimizations/o2/fullcore/workloads/check.py")
manifest = checker.verify_build(BUILD)
receipt = json.loads((BUILD/"build.json").read_text())
need(json.loads((JOB/"build-receipt.json").read_text()) == receipt, "job build receipt differs")
source_bindings = {}
for rel, expected in receipt["source_sha256"].items():
    file = BUILD/rel
    need(sha(file) == expected, "build source drift")
    repo_rel = "team/optimizations/o2/fullcore/workloads/" + file.name
    blob = subprocess.check_output(["git","-C",str(REPO),"show",receipt["source_commit"]+":"+repo_rel])
    need(hashlib.sha256(blob).hexdigest() == expected, "build source Git blob mismatch: "+repo_rel)
    source_bindings[repo_rel] = expected

text = (JOB/"stderr.log").read_text()+(JOB/"stdout.log").read_text()
analysis = a.analyze(text, require_complete=True)
events, uart = a.extract_events_and_uart(text)
functional = checker.check(uart, manifest, 0, analysis)
need(analysis["counts"] == result["observation_counts"], "recomputed counts differ from final receipt")
need(analysis["status"] == "O2_TRACE_PASS" and functional["status"] == "O2_DIAGNOSTIC_PASS", "complete audits failed")
need(analysis["counts"]["COMMIT"] == analysis["counts"]["RESPONSE"] == 1158, "vdot conservation failed")
need(analysis["counts"]["DIV_RESPONSE"] == 12 and analysis["counts"]["DIV_KILL"] == 0, "DIV completion failed")
need(not any(analysis[k] for k in ["pending_count","pending_div_count","unfinished_rob_count"]), "not drained")

by_kind = {}
for cycle, _, kind, fields in events:
    by_kind.setdefault(kind, []).append(fields)
parents = sorted(by_kind["VFEX4_ACCEPT"], key=lambda f:(f["cycle"],f["seq"]))
need(len(parents) == 1170 and [p["seq"] for p in parents] == list(range(1170)), "unexpected parent acceptance inventory")
enqueues = by_kind["ENQUEUE"]


def enqueue_for(accept):
    found = [e for e in enqueues if e["rob"] == accept["rob"] and e["cycle"] <= accept["cycle"]]
    need(bool(found), "missing preceding dynamic vdot PC")
    return max(found, key=lambda e:e["cycle"])


bounds = receipt["compiled_cases"]
begin, end = [int(bounds[9][k], 16) for k in ("begin", "end")]
type_of_fu = {1 << 35:"VDOT",1 << 22:"VIDiv",1 << 26:"VFDiv"}
transition_dot_accepts = [p for p in parents if p["fu"] == (1 << 35) and begin <= enqueue_for(p)["pc"] < end]
need(len(transition_dot_accepts) == 6, "expected six live transition vdots")
first_seq = min(p["seq"] for p in transition_dot_accepts)
need(first_seq == 1152, "first nine fixed-work cases did not delimit transition sequence")
live = [p for p in parents if p["seq"] >= first_seq]
need(len(live) == 18, "transition region does not have exactly 18 actual acceptances")
types = [type_of_fu[p["fu"]] for p in live]
type_counts = Counter(types)
need(type_counts == Counter({"VDOT":6,"VIDiv":6,"VFDiv":6}), "real accepted type inventory differs")
pairs = Counter(left+"->"+right for left,right in zip(types,types[1:]))
want_pairs = {left+"->"+right for left in type_of_fu.values() for right in type_of_fu.values()}
need(set(pairs) == want_pairs, "actual adjacent acceptance sequence misses a pair")

def kind_from_word(word):
    if word & 0xfe00707f == 0x0200000b:
        return "VDOT"
    if word & 0x7f == 0x57 and word >> 26 == 0x20:
        return {2:"VIDiv",1:"VFDiv"}.get((word >> 12) & 7)
    return None


disassembly = (BUILD/"o2-diag.txt").read_text()
static = []
elf = (BUILD/"o2-diag.elf").read_bytes()
header = struct.unpack_from("<16sHHIQQQIHHHHHH",elf)
need(header[0][:6] == b"\x7fELF\x02\x01", "unexpected ELF format")
segments = [struct.unpack_from("<IIQQQQQQ",elf,header[5]+i*header[9]) for i in range(header[10])]
image = (BUILD/"o2-diag.bin").read_bytes()
for match in re.finditer(r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s",disassembly,re.M):
    pc, word = int(match[1],16), int(match[2],16)
    kind = kind_from_word(word)
    if begin <= pc < end and kind is not None:
        loads = [s for s in segments if s[0] == 1 and s[3] <= pc and pc+4 <= s[3]+s[5]]
        need(len(loads) == 1, "static instruction not in unique ELF LOAD")
        s = loads[0]
        need(int.from_bytes(elf[s[2]+pc-s[3]:s[2]+pc-s[3]+4],"little") == word, "disassembly/ELF mismatch")
        offset = pc - 0x80000000
        need(0 <= offset <= len(image)-4 and int.from_bytes(image[offset:offset+4],"little") == word,
             "static instruction differs from actual raw image")
        static.append(dict(pc=hex(pc),word=hex(word),kind=kind))
need(len(static) == 18 and Counter(r["kind"] for r in static) == type_counts, "static binary inventory differs")
need([r["kind"] for r in static] == types, "real accepted type order differs from binary type order")
need([{"vdot":"VDOT","vidiv":"VIDiv","vfdiv":"VFDiv"}[op["op"]] for op in manifest["cases"][9]["ops"]] == types,
     "manifest and actual accepted types differ")

rows = []
for index, parent in enumerate(live):
    kind = type_of_fu[parent["fu"]]
    row = dict(index=index, kind=kind, accept_cycle=parent["cycle"], seq=parent["seq"],
               rob=parent["rob"], physical_destination=parent["pdest"],
               fu=hex(parent["fu"]), static_instruction=static[index],
               static_to_dynamic_assignment="ordinal/type correspondence only; DIV PC is not observed")
    if kind == "VDOT":
        enq = enqueue_for(parent)
        need(enq["pc"] == int(static[index]["pc"],16) and enq["word"] == int(static[index]["word"],16), "vdot live PC/word mismatch")
        child = [f for f in by_kind["ACCEPT"] if f["seq"] == parent["seq"]]
        responses = [f for f in by_kind["RESPONSE"] if f["seq"] == parent["seq"]]
        commits = [f for f in by_kind["COMMIT"] if f["rob"] == parent["rob"] and f["pc"] == enq["pc"] and f["cycle"] > parent["cycle"]]
        need(len(child)==len(responses)==len(commits)==1 and child[0]["vl"]==8 and child[0]["illegal"]==0,
             "vdot config/response/commit missing or duplicate")
        response = responses[0]
        need(response["data"] == a.dot_result(child[0]["vs1"],child[0]["vs2"]), "full128 dot mismatch")
        row.update(dynamic_pc=hex(enq["pc"]),dynamic_word=hex(enq["word"]),
                   static_to_dynamic_assignment="direct ENQUEUE/ACCEPT/COMMIT binding",
                   response_cycle=response["cycle"],commit_cycle=commits[0]["cycle"],
                   data128=f"0x{response['data']:032x}",vl=8,illegal=0)
    else:
        child = [f for f in by_kind["DIV_ACCEPT"] if f["seq"] == parent["seq"]]
        finished = [f for f in by_kind["DIV_OUTPUT"] if f["seq"] == parent["seq"] and f["ready"]==1 and f["cancelled"]==0]
        need(len(child)==len(finished)==1, "DIV accept/completion not unique")
        for f in (child[0],finished[0]):
            need(all(f[k] == parent[k] for k in ("seq","rob","pdest","fu")), "DIV metadata mismatch")
        row.update(dynamic_pc=None,dynamic_word=None,response_cycle=finished[0]["cycle"],
                   cancelled=0,ready=1,
                   architectural_completion_evidence="complete DiffTest/workload 32x128 + seven-CSR PASS; no separate DIV COMMIT PC event")
    rows.append(row)

case_stats = []
response_by_seq = {f["seq"]:f for f in by_kind["RESPONSE"]}
for index in range(9):
    lo,hi = [int(bounds[index][k],16) for k in ("begin","end")]
    selected = [p for p in parents if p["fu"] == (1 << 35) and lo <= enqueue_for(p)["pc"] < hi]
    need(len(selected)==128, "fixed-work case dynamic acceptance count differs")
    gaps = Counter(b["cycle"]-a0["cycle"] for a0,b in zip(selected,selected[1:]))
    latency = Counter(response_by_seq[p["seq"]]["cycle"]-p["cycle"] for p in selected)
    case_stats.append(dict(id=manifest["cases"][index]["id"],acceptances=128,
        accept_gap_histogram=dict(sorted(gaps.items())),response_latency_histogram=dict(sorted(latency.items())),
        one_cycle_accept_gaps=gaps.get(1,0),two_cycle_responses=latency.get(2,0),
        scope="actual full-core protocol observation only; not a speedup or fair performance comparison"))
need(any(s["one_cycle_accept_gaps"] for s in case_stats[:6]), "no actual independent one-cycle acceptance witness")
need(any(s["two_cycle_responses"] for s in case_stats[:6]), "no actual two-cycle response witness")

source_pc_limit = "No per-DIV dynamic PC/word is recorded by this hardware observer; T13_RETIRE is absent. Static DIV rows are ordinal/type correspondence, not direct dynamic PC proof."
bindings = {str(p):sha(p) for p in [
    JOB/"result.json",JOB/"stdout.log",JOB/"stderr.log",JOB/"exit-code.txt",BUILD/"build.json",
    BUILD/"data/manifest.json",BUILD/"o2-diag.bin",BUILD/"o2-diag.elf",BUILD/"o2-diag.txt",
    CAMPAIGN/"preflight.json",CAMPAIGN/"hardware-pins.json"]}
audit = dict(
    status="O2_TRANSITION_LIVE_REVIEW_PASS",
    reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    scope="Completed new diagnostic only; byte identities, original-checker full replay and independent actual acceptance order",
    no_emu_launched=True,no_frozen_tools_modified=True,performance_measured=False,
    hardware_source_commit=result["build_source_commit"],workload_source_commit=receipt["source_commit"],
    tool_source_commit=preflight["tool_source_commit"],bindings=bindings,
    workload_source_sha256=source_bindings,tool_sha256=tool_bindings,
    recomputed_status=analysis["status"],recomputed_functional_status=functional["status"],
    full_run_counts=analysis["counts"],pending_count=analysis["pending_count"],
    pending_div_count=analysis["pending_div_count"],unfinished_rob_count=analysis["unfinished_rob_count"],
    actual_accept_types=types,type_counts=dict(type_counts),actual_adjacent_pair_counts=dict(sorted(pairs.items())),
    transitions=rows,fixed_work_protocol_observations=case_stats,
    t13_retire_records=len(re.findall(r"T13_RETIRE ",text)),limitations=[source_pc_limit],
    functional_marker="O2_DIAG_CASE_PASS seq=9 id=vfex4-all-pairs dots=6 register_bytes=512 csr_fields=7",
    summary_marker="O2_DIAG_SUMMARY cases=10 dots=1158 failures=0")
(OUT/"review.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n")
table = "\n".join(
    f"| {r['seq']} | {r['accept_cycle']} | {r['kind']} | {r['rob']} | {r.get('dynamic_pc') or '未记录'} | {r['static_instruction']['pc']} / {r['static_instruction']['word']} | {r['response_cycle']} |"
    for r in rows)
pair_table = "\n".join(f"| {pair} | {count} |" for pair,count in sorted(pairs.items()))
stats_table = "\n".join(f"| {s['id']} | 128 | {s['one_cycle_accept_gaps']} | {s['two_cycle_responses']} |" for s in case_stats)
readme = f"""# 修复后 VFEX4 转换用例的真实接受顺序复核

结论：O2_TRANSITION_LIVE_REVIEW_PASS。新 diagnostic-build-03 的完整运行已结束，原始退出码为 0；使用本轮封存的分析器和检查器从完整 stdout/stderr 重新验证通过，并独立统计真实 VFEX4_ACCEPT 顺序。没有启动 EMU，没有修改冻结工具。

实际转换段为 seq1152…1169，共18次接受；VDOT、VIDiv、VFDiv 各6次。按真实接受顺序得到的17个相邻边覆盖全部9种有序类型组合。该结论来自动态事件，而非只读取汇编排列。

## 身份与完整通过证据

- 作业：{JOB}
- 硬件源码提交：{result['build_source_commit']}
- 工作负载源码提交：{receipt['source_commit']}
- 检查工具提交：{preflight['tool_source_commit']}
- 新镜像 SHA256：{sha(BUILD/'o2-diag.bin')}
- generate.py SHA256：{source_bindings['team/optimizations/o2/fullcore/workloads/generate.py']}
- main.c SHA256：{source_bindings['team/optimizations/o2/fullcore/workloads/main.c']}
- stderr SHA256：{sha(JOB/'stderr.log')}
- stdout SHA256：{sha(JOB/'stdout.log')}

核对了 raw rc、原始流 SHA、run.log 的逐字节拼接、实际 EMU/参考库/flash/镜像身份、原 build receipt 的全部源码/生成物/镜像/AM 库 SHA。构建源码与工具源码均逐项绑定其记录提交的 Git blob。实际18条指令字还与 ELF LOAD 字节和 raw bin 对照。

全程序重新计算得到1158次 VDOT 接受、响应及提交，12次 DIV 正常完成，DIV取消0；VDOT、DIV、ROB均已排空。第十病例精确输出：

    {audit['functional_marker']}
    {audit['summary_marker']}

该病例软件检查全部32×128位向量寄存器及7项CSR，检查逻辑与黄金值由绑定的源码/manifest确认。全部10病例完整通过，共5120寄存器字节；这些是软件检查与DiffTest证据，不声称每个CSR值都单独打印在O2轨迹中。

## 动态顺序及身份

| seq | 接受周期 | 实际FU类型 | ROB | 直接观测的动态PC | 静态ELF PC / word | 响应周期 |
| --- | --- | --- | --- | --- | --- | --- |
{table}

六条VDOT使用ENQUEUE的PC/word和ACCEPT、RESPONSE、COMMIT直接关联，全部VL8、illegal=0，完整128位结果重新计算一致。12条DIV使用真实父/子接受及正常输出的fu/seq/rob/pdest绑定，均唯一正常完成。

**动态DIV PC限制：** 现有DIV事件没有PC/word，且本诊断未开启T13退休窗口（T13_RETIRE共0条）。因此表中的DIV静态PC仅是二进制顺序及类型对应，不能当作逐条动态PC直接观测。九种相邻类型覆盖仍由实际VFEX4接受顺序独立成立，不依赖这个静态对应假设。

## 真实相邻类型组合

| 组合 | 实际相邻出现次数 |
| --- | --- |
{pair_table}

## 固定工作量病例中的协议观察

仅统计各病例内部相邻VDOT接受，排除跨病例间隔。下面说明真实整核能出现1拍接受间隔和2拍响应，不等同于应用加速比或公平O1/O2性能结果。

| 病例 | 实际接受数 | 内部1拍接受间隔次数 | 2拍响应次数 |
| --- | --- | --- | --- |
{stats_table}

review.json 保存完整事件绑定、直方图和SHA。review.py 为本次只读复核脚本；它只重算已有完整日志，不执行仿真器。失败旧批次仍保留，本审计仅声明修复后新诊断的结果，不替代整套G3合并验收。
"""
(OUT/"README.md").write_text(readme,encoding="utf-8",newline="\n")
print(json.dumps(dict(status=audit["status"],type_counts=dict(type_counts),
    pair_counts=dict(sorted(pairs.items())),rows=len(rows),commit_count=analysis["counts"]["COMMIT"],
    independent_one_cycle_gaps=sum(s["one_cycle_accept_gaps"] for s in case_stats[:6]),
    independent_two_cycle_responses=sum(s["two_cycle_responses"] for s in case_stats[:6]),
    README_sha256=sha(OUT/"README.md"),review_json_sha256=sha(OUT/"review.json")),ensure_ascii=False))
