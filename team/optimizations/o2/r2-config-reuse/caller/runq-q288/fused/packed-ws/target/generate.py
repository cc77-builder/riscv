"""One frozen four-entry, twelve-window packed-scale comparison image."""
from pathlib import Path
import importlib.util
import json
import re
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
Q = HERE.parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
previous = load('ws_target_previous_generator', Q/'fused/phased/tail/target/generate.py')
candidate = load('ws_target_candidate', HERE.parent/'generate.py')
parent = previous.parent
need = parent.split.need
CONTRACT = 'r2-s3-runq-q288-packed-ws-target-v1'
MAX_CYCLES = 12000000
FILES = previous.FILES + ('q288_ws.h', 'pack.c')
METHODS = (5, 0, 5, 0)
WRAPPERS = ('q288_fused_rvv4', 'q288_tail_vdot', 'q288_ws_rvv4', 'q288_ws_vdot')
LABELS = ('FR', 'TA', 'PFR', 'PTA')
ORDER = (0, 2, 1, 3, 2, 0, 0, 2, 3, 1, 2, 0)
FUNCTIONAL_ORDER = (0, 1, 2, 3, 0, 1, 2, 3)
FUNCTIONAL_DATASETS = (1, 1, 1, 1, 2, 2, 2, 2)
GUARD = previous.GUARD


def generate(repo, out):
    repo, out = Path(repo).resolve(), Path(out).resolve()
    manifest = previous.generate(repo, out)
    shutil.copyfile(HERE/'main.c', out/'main.c')
    for name in ('q288_ws.h', 'pack.c'):
        shutil.copyfile(HERE.parent/name, out/name)
    with tempfile.TemporaryDirectory(prefix='packed-ws-target-producer-') as temporary:
        generated = Path(temporary)/'generated'
        candidate.generate(repo, generated)
        shutil.copyfile(generated/'q288-ws.S', out/'fused.S')
    make = (out/'Makefile').read_text()
    old = 'main.c q288.c oracle.c timers.S kernels.S fused.S'
    need(make.count(old) == 1, 'fixed existing target translation units')
    (out/'Makefile').write_text(make.replace(old, old+' pack.c'))
    header = (out/'data.h').read_text()
    for before, after in (('#define Q_CONTRACT "'+previous.CONTRACT+'"', '#define Q_CONTRACT "'+CONTRACT+'"'),
                          ('#define Q_WINDOWS 8', '#define Q_WINDOWS 12'),
                          ('#define Q_TOTAL_CALLS 22', '#define Q_TOTAL_CALLS 32')):
        need(header.count(before) == 1, 'unique target contract field')
        header = header.replace(before, after)
    for name, old_size, values in (('q_order',8,ORDER), ('q_methods',3,METHODS),
                                  ('q_functional_order',6,FUNCTIONAL_ORDER),
                                  ('q_functional_datasets',6,FUNCTIONAL_DATASETS)):
        pattern = r'static const unsigned '+name+r'\['+str(old_size)+r'\][^;]*;'
        replacement = 'static const unsigned '+name+'['+str(len(values))+'] __attribute__((aligned(16),used)) = {'+','.join(map(str,values))+'};'
        header, count = re.subn(pattern, lambda _: replacement, header)
        need(count == 1, 'unique original array '+name)
    marker = 'typedef void (*q_wrapper)(struct q288_context *);\n'
    need(header.count(marker) == 1, 'remove original single-ABI wrapper type')
    header = header.replace(marker, '')
    header, count = re.subn(r'q_wrapper const q_wrappers\[3\][^;]*;',
        'const uintptr_t q_entry_addresses[4] __attribute__((aligned(16),used)) = {'+
        ','.join('(uintptr_t)'+n for n in WRAPPERS)+'};', header)
    need(count == 1, 'replace original function-pointer table with raw timer entry addresses')
    need('q_wrapper' not in header, 'no incompatible old wrapper casts')
    (out/'data.h').write_text(header)
    variants = ('fused', 'tail-agnostic', 'packed-ws-rvv4', 'packed-ws-vdot')
    rows = [dict(id=i,kind='Q',algorithm=METHODS[i],method='vdot' if i in (1,3) else 'rvv',
                 variant=variants[i],label=LABELS[i],scenario='self-warmed-prepacked-full-Q',
                 n=1,dots=10368 if i in (1,3) else 0,leaf=parent.NEW[METHODS[i]],wrapper=WRAPPERS[i],
                 context_bytes=56 if i<2 else 48,scale_layout='row-major' if i<2 else 'tile-group-lane')
            for i in range(4)]
    plan = [dict(index=arm,phase='measured',repeat=i//6,dataset=0,block=i//6,
                 role=('FR-anchor-start' if i%6==0 else 'FR-anchor-end') if arm==0 else
                      'PFR-anchor' if arm==2 else 'method') for i,arm in enumerate(ORDER)]
    calls = [dict(stage=0,arm=a,dataset=d) for a,d in zip(FUNCTIONAL_ORDER,FUNCTIONAL_DATASETS)]
    for arm in ORDER:
        calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    need(ORDER[6:] == tuple(reversed(ORDER[:6])), 'strict reverse-order second block')
    need(len(calls) == 32 and sum(rows[c['arm']]['dots'] for c in calls)+1 == 124417,
         'derived complete-call and custom counts')
    manifest.update(contract=CONTRACT,rows=rows,plan=plan,call_plan=calls,
        functional_calls=32,explicit_functional_calls=8,timed_q_calls=12,warmup_calls=12,
        conditioning_calls=0,full_q_calls=32,integer_sweep_leaf_calls=0,all_leaf_calls=0,
        integer_core_executions=10368,expected_dots=124417,formal_method_windows=12,
        formal_anchor_windows=8,method_anchor_overlap_windows=8,pack_windows=0,max_cycles=MAX_CYCLES,
        target_scalar_oracle_calls=0,prepacked_constant_input=False,weight_prepacked_constant_input=True,
        pack_executed=True,weight_pack_executed=False,scale_pack_executed=True,scale_pack_calls=1,
        scale_pack_words=2592,scale_pack_controls=3,scale_pack_timed=False,judge_fault_controls=10,
        functional_order=list(FUNCTIONAL_ORDER),functional_datasets=list(FUNCTIONAL_DATASETS),
        conditioning='one same-method full Q before each measured window; common prepare before both calls',
        primary_metric='complete 288-output Q with prepacked weights and prepacked scales where applicable',
        statistics='two reverse-order TA/PTA observations; four FR and four PFR anchors; replay adds no sample',
        selection_scope='TA/PTA and both named FR/PFR controls; every observation retained',
        anchor_threshold_ratio=[101,100],separation_threshold_ratio=[199,200],
        count_expected_counter_enqueues=48,count_expected_csr_samples=48,
        fp_element_operations=dict(convert=82944,mul=165888,add=82944),
        changed_candidate_function_words=3,candidate_functions_changed=2,candidate_instruction_count_change=0,
        structural_hypothesis='replace strided weight scales with equivalent contiguous scale groups',
        scale_storage_bytes=10368,extra_scale_storage_bytes=10368,packing_cost_measured=False,
        selected_method=None,hardware_changed=False,stable_default_changed=False,
        includes_quantization=False,actual_model_checkpoint=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
