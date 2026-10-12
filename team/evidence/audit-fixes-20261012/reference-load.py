import ctypes, json
from pathlib import Path
path='/home/amesotten/.cache/codex-rvinno/t08/delivered/reference/build/riscv64-nemu-interpreter-so'
library=ctypes.CDLL(path)
symbols=['difftest_init','difftest_exec','difftest_memcpy','difftest_regcpy']
for symbol in symbols: getattr(library,symbol)
result=dict(binary=path,loaded=True,exports_checked=symbols,guest_difftest_run=False)
Path('team/out/fix-nemu-reference/load-check.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
