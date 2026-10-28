from pathlib import Path
import json,importlib.util,hashlib
from datetime import datetime,timezone
W=Path("/home/riscv/riscv-lab/software-import-20261026");HERE=Path(__file__).resolve().parent
OUT=W/"config-reuse-c8-02";p=W/"reviews/config-reuse/c8-v2/c8.py"
spec=importlib.util.spec_from_file_location("c8_final_readonly",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.read(OUT/"state.json")["status"]==m.PASS
ex=m.CurrentC();actual=ex.physical()
assert json.loads(json.dumps(actual))==m.read(OUT/"identity-before.json")
m.verify(m.read(OUT/"outer-inputs.json"))
value=dict(status="C8_FINAL_PHYSICAL_IDENTITY_PASS",matches_before=True,created=datetime.now(timezone.utc).isoformat(),
 identity_before_sha256=m.sha(OUT/"identity-before.json"),outer_inputs_sha256=m.sha(OUT/"outer-inputs.json"),
 physical_profile=actual[0],physical_files=actual[1],third_identity_keys=list(actual[2]),new_emu_runs=0)
assert not (HERE/"physical-after.json").exists()
m.save(HERE/"physical-after.json",value)
print("C8_FINAL_PHYSICAL_IDENTITY_PASS")
