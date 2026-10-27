"""Ten full-Q target observations using unchanged old/acc8 wrapper sources."""
from pathlib import Path
import importlib.util
import json
import re
import shutil

HERE = Path(__file__).resolve().parent
Q = HERE.parents[1]
REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/acc8/target')
spec = importlib.util.spec_from_file_location('acc8_target_fixture', Q/'generate.py')
parent = importlib.util.module_from_spec(spec); spec.loader.exec_module(parent)
CONTRACT = 'r2-s3-runq-q288-acc8-target-v1'
MAX_CYCLES = 12000000
FILES = parent.FILES + ('q288_baseline.c',)
ORDER = (0, 1, 2, 3, 2, 3, 2, 3, 2, 3)
DATASETS = (0, 0, 0, 0, 1, 1, 0, 0, 2, 2)
METHODS = (0, 5, 0, 5)
WRAPPERS = ('q288_baseline_full', 'q288_baseline_full', 'q288_full', 'q288_full')
PINNED = {
    Q/'q288.c': '05955ce611f180c6cdef3becf74be47b5246f06c85931640f1c6ad33746bada0',
    HERE.parent/'q288.c': 'f0c557cb837ac05ff713b0eaadb7949b3ba623ae54fe1c02aedcd4220f5bf8d1',
}


def generate(repo, out):
    for path, pin in PINNED.items():
        parent.split.need(parent.digest(path.read_bytes()) == pin, 'unchanged wrapper source')
    out = Path(out)
    manifest = parent.generate(repo, out)
    shutil.copyfile(HERE.parent/'q288.c', out/'q288.c')
    (out/'q288_baseline.c').write_text(
        '#define q288_pack q288_baseline_pack\n#define q288_full q288_baseline_full\n' +
        (Q/'q288.c').read_text())
    shutil.copyfile(HERE/'main.c', out/'main.c')
    make = (out/'Makefile').read_text()
    parent.split.need(make.count('main.c q288.c oracle.c') == 1, 'base separate C units')
    (out/'Makefile').write_text(make.replace('main.c q288.c oracle.c',
                                            'main.c q288.c q288_baseline.c oracle.c'))
    rows = [dict(id=i, kind='Q', algorithm=METHODS[i],
                 method='vdot' if METHODS[i] == 0 else 'rvv',
                 variant='original' if i < 2 else 'acc8',
                 scenario='acc8-target-cost-observation', n=1,
                 dots=10368 if METHODS[i] == 0 else 0,
                 leaf=parent.NEW[METHODS[i]], wrapper=WRAPPERS[i]) for i in range(4)]
    rows.append(dict(id=4, kind='pack', algorithm=-1, method='pack', variant='shared',
                     scenario='acc8-target-pack', n=1, dots=0, leaf=None, wrapper='q288_pack'))
    plan = [dict(index=4, phase='setup', repeat=0, dataset=0, block=-1, role='pack')]
    for i, (arm, dataset) in enumerate(zip(ORDER, DATASETS)):
        plan.append(dict(index=arm, phase='measured', repeat=i, dataset=dataset,
                         block=0, role='functional_cost_observation'))
    header = (out/'data.h').read_text()
    header = header.replace('#define Q_CONTRACT "'+parent.CONTRACT+'"',
                            '#define Q_CONTRACT "'+CONTRACT+'"')
    parent.split.need(header.count('#define Q_WINDOWS 17') == 1, 'base window constant')
    header = header.replace('#define Q_WINDOWS 17', '#define Q_WINDOWS 11\n#define Q_CALLS 10')
    header, count = re.subn(r'static const unsigned q_order\[16\].*?\n};',
        'static const unsigned q_order[10] __attribute__((aligned(16),used)) = {'+
        ','.join(map(str, ORDER))+'};', header, flags=re.S)
    parent.split.need(count == 1, 'base order array')
    header, count = re.subn(r'static const int32_t q_group_dots\[2592\].*?\n};\n',
                           '', header, flags=re.S)
    parent.split.need(count == 1, 'retire unused separate integer sweep fixture')
    header += ('extern void q288_baseline_full(struct q288_context *);\n'
               'typedef void (*q_wrapper)(struct q288_context *);\n'
               'q_wrapper const q_wrappers[4] = {'+','.join(WRAPPERS)+'};\n'
               'static const unsigned q_methods[4] __attribute__((aligned(16),used)) = {'+
               ','.join(map(str, METHODS))+'};\n'
               'static const unsigned q_datasets[10] __attribute__((aligned(16),used)) = {'+
               ','.join(map(str, DATASETS))+'};\n')
    (out/'data.h').write_text(header)
    manifest.update(contract=CONTRACT, rows=rows, plan=plan, functional_calls=10,
        timed_q_calls=10, warmup_calls=0, conditioning_calls=0, full_q_calls=10,
        integer_sweep_leaf_calls=0, all_leaf_calls=3240, expected_dots=51841,
        formal_method_windows=0, formal_anchor_windows=0, pack_windows=1,
        cost_observation_windows=10, max_cycles=MAX_CYCLES,
        target_scalar_oracle_calls=0, shared_functional_and_timed_calls=True,
        conditioning='none; fixed prefix/order, no equal-warm-state or fair-speedup claim',
        primary_metric='target correctness and descriptive full-Q cycle/instruction observations',
        performance_qualified=False, selected_method=None,
        wrapper_sources={str(p.relative_to(repo)): pin for p, pin in PINNED.items()},
        original_input_lifecycle=[0], acc8_input_lifecycle=[0,1,0,2],
        runtime_expected_counter_enqueues=44, runtime_expected_csr_samples=44)
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
