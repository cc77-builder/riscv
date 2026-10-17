"""Minimal valid three-event redirect/enqueue lifecycle from the captured trace."""
import importlib.util
from pathlib import Path
root=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016/source-9a5c75274233d410')
spec=importlib.util.spec_from_file_location('control',root/'team/scripts/check-vdot-regression.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
text='''The reference model is /fixture/ref.so
The first instruction of core 0 has commited. Difftest enabled.
T12_ENQUEUE cycle=321330 rob=1:16 pc=0x80010800 ftq=1:4 word=0x02940a0b
T12_REDIRECT cycle=321330 rob=0:27 ftq=0:5
T12_ENQUEUE cycle=321358 rob=1:16 pc=0x80010800 ftq=1:4 word=0x02940a0b
T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1
T12_GROUP_PASS id=0 checkpoints=32 bytes=16384
T12_GROUP_PASS id=1 checkpoints=32 bytes=16384
T12_GROUP_PASS id=2 checkpoints=32 bytes=16384
T12_GROUP_PASS id=3 checkpoints=32 bytes=16384
T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0
HIT GOOD TRAP
'''
# This minimized synthetic trace does not claim full coverage or DUT execution.
result=m.check(text,{'groups':[],'speculation':{'expected_architectural_vdot':0}},0)
if result['status']!='T12_COVERAGE_INCOMPLETE':raise RuntimeError('minimal trace must not claim full coverage')
print('MINIMAL_REDIRECT_LIFECYCLE_PASS_WITH_INCOMPLETE_COVERAGE')
