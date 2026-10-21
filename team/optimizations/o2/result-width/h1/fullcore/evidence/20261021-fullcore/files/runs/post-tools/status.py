#!/usr/bin/env python3
"""Read the H1 campaign state without starting or altering jobs."""
from pathlib import Path
import json
import re
import subprocess
from datetime import datetime, timezone

WORK = Path("/home/riscv/riscv-lab/o2-h1-fullcore-20261021")
REPO = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")

def tail(path, limit=800):
    if not path.exists():
        return ""
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - limit))
        return stream.read().decode("utf-8", errors="replace")

def main():
    state = json.loads((WORK / "campaign-state.json").read_text())
    result = {"time_utc": datetime.now(timezone.utc).isoformat(),
              "status": state["status"],
              "steps": [{"name": s["name"], "status": s["status"], "pid": s.get("pid")} for s in state["steps"]]}
    current = state["steps"][-1]["name"] if state["steps"] else None
    if current == "build":
        state_file = WORK / "build-01/build-state.json"
        result["build"] = json.loads(state_file.read_text()).get("status") if state_file.exists() else "capturing"
        result["build_log_tail"] = tail(WORK / "build-01/emu-build.log")
        result["compiled_objects"] = sum(1 for _ in (REPO / "build").rglob("*.o"))
    elif current in ("core", "supplements"):
        campaign = WORK / (current + "-01")
        result["finished_jobs"] = []
        result["active_jobs"] = []
        for p in sorted(campaign.glob("*/runtime.json")):
            final = p.with_name("result.json")
            item = json.loads((final if final.exists() else p).read_text())
            row = {k: item[k] for k in ("name", "status", "exit_code") if k in item}
            if not item.get("finished"):
                stdout = p.with_name("stdout.log")
                if stdout.exists():
                    console = stdout.read_text(errors="replace")
                    row["printed_matrix_results"] = len(re.findall(r"VDOT_PACKED id=", console))
                    row["stdout_bytes"] = stdout.stat().st_size
            result["finished_jobs" if final.exists() and item.get("finished") else "active_jobs"].append(row)
        result["run_log_tail"] = tail(WORK / (current + ".log"))
    result["heavy_processes"] = []
    ps = subprocess.check_output(["ps", "-eo", "pid,etime,pcpu,rss,comm"], text=True)
    for line in ps.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 5 and parts[4] in ("java", "firtool", "verilator_bin", "clang++", "cc1plus", "emu", "ld"):
            result["heavy_processes"].append(parts)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
