from pathlib import Path
import hashlib
import importlib.util
import json

BASE = Path(__file__).resolve().parent.parent
model_path = BASE / "references/shishui/vdot/vdot_model.py"
spec = importlib.util.spec_from_file_location("shishui_public_model", model_path)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
results = []
for name in ["directed", "random"]:
    path = BASE / f"repo/team/models/vdot/data/{name}.jsonl"
    count = 0
    for line in path.read_text().splitlines():
        item = json.loads(line)
        actual = model.vdot_vv(int(item["vs1"], 16), int(item["vs2"], 16))
        expected = int(item["expected_vd"], 16)
        assert actual == expected, (item["id"], hex(actual), hex(expected))
        count += 1
    results.append({"dataset": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "passed": count})
print(json.dumps({"status": "PASS", "scope": "Python public mathematical model only; not RTL/DiffTest", "datasets": results}, indent=2))
