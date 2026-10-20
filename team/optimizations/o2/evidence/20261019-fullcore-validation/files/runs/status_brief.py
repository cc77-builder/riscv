import json, subprocess
from pathlib import Path
root = Path(__file__).resolve().parent
s = json.loads(subprocess.check_output(["python3", "-B", str(root / "status_g3.py")], text=True))
running = [j for j in s["jobs"] if j["status"] == "RUNNING"]
completed = [{"name": j["name"], "status": j["status"]} for j in s["jobs"] if j["status"] != "RUNNING"]
print(json.dumps({"time": s["time"], "stage": s["launch"], "completed": completed, "running": running}, ensure_ascii=False))
