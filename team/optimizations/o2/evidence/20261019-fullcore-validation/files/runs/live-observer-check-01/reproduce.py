import sys,json,traceback,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('frozen_analyze',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
 result=module.analyze(Path(sys.argv[2]).read_text(),require_complete=False)
 print(json.dumps(result,indent=2))
except Exception:
 traceback.print_exc()
 sys.exit(1)
