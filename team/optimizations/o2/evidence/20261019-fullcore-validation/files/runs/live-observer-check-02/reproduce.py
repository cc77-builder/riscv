import sys,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('frozen',sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
print(json.dumps(m.analyze(Path(sys.argv[2]).read_text(),require_complete=sys.argv[3]=='complete'),indent=2))
