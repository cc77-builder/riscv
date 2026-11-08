"""Exact C48 neighboring-PC delta. Frozen base adapter and its files unchanged."""
from pathlib import Path
import importlib.util, sys
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('b4_c48_exact_pc_base', HERE.parent / 'adapter.py')
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)
need, check_pin, native = base.need, base.check_pin, base.native
CONTRACT, CASE, CASE_ID = base.CONTRACT, base.CASE, base.CASE_ID
FAKE_REFERENCE, SCOPES = base.FAKE_REFERENCE, base.SCOPES
descriptor, collect, compare = base.descriptor, base.collect, base.compare

def negative(text, case_id, mode, reference, exit_code, run_id, scope='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT'):
    result = base.negative(text, case_id, mode, reference, exit_code, run_id, scope)
    symbols, read = native.windows.elf_data(Path(CASE['artifacts']['elf']['path']))
    start, _ = symbols['config_reuse_gemv_8x32_reuse_vdot']
    stop = int(CASE['negative_binding']['pc'], 0)
    pairs = {(pc, int.from_bytes(read(pc, 4), 'little')) for pc in range(start, stop, 4)
             if int.from_bytes(read(pc, 4), 'little') & 0x7f == 0x07}
    words = {word for _, word in pairs}
    need(len(pairs) == len(words) == 8, 'exact eight neighboring PC/word pairs')
    for row in result['fault']['current_group']['instructions']:
        if row['word'] in words:
            need((row['pc'], row['word']) in pairs, 'C48 unit-stride load must match exact frozen neighboring PC and full word')
    result['c48_load_footprint_scope'] = 'eight exact neighboring PC/full-word pairs under original e8,m1/VL8 group context'
    return result
