"""Raw caller checks: unchanged counter/protocol checks plus bounded C paths."""
from collections import Counter
import json
from pathlib import Path
import re
import statistics
import struct

import experiment as e
import pathcheck
g=e.g
g.require(Path(e.__file__).resolve()==Path(__file__).resolve().with_name("experiment.py"), "caller experiment import")

def normal(repo,build,run,receipt):
    g.require(receipt.get("process_started") is True and receipt.get("exit_code")==0 and not receipt.get("timed_out"),"caller incomplete execution")
    manifest=e.read(build/"source/manifest.json")
    stdout,stderr=((run/n).read_text() for n in ("stdout.log","stderr.log"))
    gate=g.load("caller_failures",repo/"team/optimizations/o1/audit/runtime_gate.py")
    fatal=g.load("caller_fatal",repo/"team/optimizations/o2/fullcore/recheck.py")
    observer=g.load("caller_protocol",repo/"team/optimizations/o2/fullcore/analyze.py")
    for stream in (stdout,stderr):
        gate.validate_failure_markers(stream);fatal.reject_fatal_output(stream)
    _,uart=observer.extract_events_and_uart(stderr+stdout)
    gate.validate_failure_markers(uart);fatal.reject_fatal_output(uart)
    plain=gate.normalize_console(uart)
    counter=g.load("caller_fixed_counters",repo/"team/workloads/unified-vdot/check.py")
    elf=g.ELF((build/"vdot-perf.elf").read_bytes())
    paths={}
    for row in manifest["rows"]:
        all_paths=[pathcheck.path(elf,row["stage"],row["method"],bytes(raw))[0] for raw in manifest["inputs"]]
        g.require(all_paths[0]==all_paths[1]==all_paths[2],"caller data-dependent compiled path")
        paths[row["id"]]=all_paths[0]
    # Private module only: do not edit the frozen counter checker. It performs
    # PC/word, counter ROB identity, sampling/fence order and exact retirement.
    counter.walk=lambda compiled_path:compiled_path
    events=counter.parse_events(stderr)
    samples=counter.trace_windows(events,manifest,paths)
    # The older checker permits compressed straight-line retirement. Explicitly
    # forbid compressed branch/call/return entries in this new C scope.
    windows=[];current=None
    for r in events["RETIRE"]:
        if r["word"]==pathcheck.START:current=[]
        if current is not None:current.append(r)
        if r["word"]==pathcheck.STOP:
            windows.append(current);current=None
    for records,step in zip(windows,manifest["plan"]):
        path=paths[step["index"]];position=0
        for rec in records:
            covered=path[position:position+rec["count"]]
            if rec["count"]>1:
                g.require(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered),"control hidden in ROB compression")
            position+=rec["count"]
    expected=[f"CALLER_BEGIN contract={e.CONTRACT} windows={len(manifest['plan'])}"]
    for sample,step in zip(samples,manifest["plan"]):
        row=manifest["rows"][step["index"]]
        sample.update(dataset=step["dataset"],scope=row["scope"])
        expected.append(f"CW {sample['seq']} {sample['cycles']} {sample['instructions']}")
        if sample["seq"]==0:expected.append("CALLER_CONTROLS detected=6 expected=6")
    expected += [f"CALLER_DEMO dataset={d} verdict=0" for d in range(3)]
    expected.append(f"CALLER_END windows={len(manifest['plan'])} failures=0")
    actual=[line for line in plain.splitlines() if line.startswith(("CALLER_","CW "))]
    g.require(actual==expected and plain.count("HIT GOOD TRAP")==1,"caller raw output/counters/judges/order differ")
    analysis=observer.analyze(stderr+stdout)
    g.require(analysis["status"]=="O2_TRACE_PASS" and analysis["schema"]["slots"]==2 and
              all(analysis.get(k)==0 for k in ("pending_count","pending_div_count","unfinished_rob_count")) and
              analysis["counts"].get("COMMIT")==manifest["expected_dots"],"caller complete protocol/commit count")
    summary=[]
    for scope in e.PHASES:
        group={}
        for method in ("vdot","rvv"):
            selected=[s for s in samples if s["scope"]==scope and s["method"]==method and s["phase"]=="measured"]
            g.require(len(selected)==12 and {(s["dataset"],s["repeat"]) for s in selected}=={(d,r) for d in range(3) for r in range(2,6)},"caller measured coverage")
            vals=[s["cycles"] for s in selected]
            group[method]=dict(samples=len(vals),total=sum(vals),mean=statistics.mean(vals),minimum=min(vals),median=statistics.median(vals),maximum=max(vals),
                instructions=sorted({s["instructions"] for s in selected}),by_dataset=[dict(dataset=d,cycles=[s["cycles"] for s in selected if s["dataset"]==d]) for d in range(3)])
        control=scope in ("pack","extract")
        row=dict(scope=scope,**group,primary_metric=scope=="full",identical_code_context_control=control)
        key="context_label_difference" if control else "reduction_vdot_vs_rvv"
        row[key]=1-group["vdot"]["total"]/group["rvv"]["total"]
        summary.append(row)
    return dict(status="CALLER_DIFFTEST_COUNTER_PATH_PASS",contract=e.CONTRACT,shape=[8,32],datasets=[0,1,2],
        windows=len(samples),formal_windows=sum(s["phase"]=="measured" for s in samples),ordinary_stack_demo_calls=3,
        judge_fault_controls=6,committed_vdot=analysis["counts"]["COMMIT"],samples=samples,summary=summary,
        diagnostic_sum_is_endtoend=False,hardware_changed=False,stable_default_changed=False)
