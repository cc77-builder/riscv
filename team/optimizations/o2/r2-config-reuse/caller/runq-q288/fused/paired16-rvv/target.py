"""Build one P/GS32/TA/FR image with one untimed full-s8 fallback case.

Only generated copies are adapted. The mature generators, guest judge for the
three existing datasets, official code, and immutable AM libraries stay intact.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import struct
import subprocess
import sys
import time

import generate
import screen

need, sha = generate.need, generate.sha
REL = generate.REL
CONTRACT = 'r2-s3-runq-paired16-rvv-target-v1'
ORDER = (3, 0, 1, 2, 3, 3, 2, 1, 0, 3)
WRAPPERS = (generate.NAME, 'q288_gs32_rvv', 'q288_tail_vdot', 'q288_fused_rvv4')
METHODS = (5, 5, 0, 5)
FUNCTIONAL_ORDER = (0, 1, 2, 3, 0, 1, 2, 3)
FUNCTIONAL_DATASETS = (1, 1, 1, 1, 2, 2, 2, 2)
FULLMIN_DATASET = 3
FULLMIN_OUTPUT_SHA = '66c4c3af41f5c15c3228ce31c1bfc1be67e438e566d1def9499e6daa6b96e525'
GUARD = 0xd15ea5e5cafebabe
GS32_PINS = {
    'generate.py':'216571084e75823a67a86d72627a8c6e9ca304e23a7f640720f83ad6dac1793f',
    'screen.py':'2ae9f3a57d505c71747f445050f7473818556555b45b106ba497261f41779dca',
    'target.py':'63138043a80cc39f3fecad9284e246f247367c2b6a79491d63053c4e8be7e59f',
    'check_target.py':'0b0a44f57e0f8e100341daa4821ca20289d97d16581806346af1373cc03e2539',
    'run_target.py':'a679f3baef057ec946b5d21ff87eb9c1c6d691ea63398b951f82658c3a688528',
}
BASE_SOURCE_PINS = {
    "team/optimizations/o1/audit/runtime_gate.py": "80315b278f4dc0168edd33657a07ae648b20f0279fa57a69f35b0f983fa42ea1",
    "team/optimizations/o2/fullcore/analyze.py": "27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496",
    "team/optimizations/o2/fullcore/recheck.py": "8cebe76129f86747cdddf87f93f54d4379a8606dd3c1a20d55008361f2f95140",
    "team/optimizations/o2/r2-config-reuse/caller/caller.h": "8f8ebbdfc64f506549b8fcb91700fc80dd91b1fd0a5be64aaed504ebcfa0c38e",
    "team/optimizations/o2/r2-config-reuse/caller/hoisted/caller.c": "141d1789e5cf8e55ba5463e1ed246868bc94bdeee3daf9006f6f0e134fb6e75b",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/acc8/q288.c": "f0c557cb837ac05ff713b0eaadb7949b3ba623ae54fe1c02aedcd4220f5bf8d1",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/generate.py": "b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/gs32-rvv/check_target.py": "0b0a44f57e0f8e100341daa4821ca20289d97d16581806346af1373cc03e2539",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/gs32-rvv/generate.py": "216571084e75823a67a86d72627a8c6e9ca304e23a7f640720f83ad6dac1793f",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/gs32-rvv/run_target.py": "a679f3baef057ec946b5d21ff87eb9c1c6d691ea63398b951f82658c3a688528",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/gs32-rvv/screen.py": "2ae9f3a57d505c71747f445050f7473818556555b45b106ba497261f41779dca",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/gs32-rvv/target.py": "63138043a80cc39f3fecad9284e246f247367c2b6a79491d63053c4e8be7e59f",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/model.py": "703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/candidate.py": "2b487c60b53e25dbc04eba4c2eac4bd175e1573837863194de463d6a27df2399",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/screen.py": "8537f85027ccc9164229c10a400a7d996d42c6711d30dc869835e5eb71a88fd9",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/tail/candidate.py": "3a75e09640fdf789c11cf8a9050cd716ca3fde12732cb500f3f123adb0b50697",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/tail/target/generate.py": "8369f553aaf642cb2de84ca40506e04f67b5458c6c3992f4d540dc5af7c1c9b5",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/tail/target/main.c": "39b1e2910d6e01ee0894895425f588fa9b6a85853d6b3fb32e866719f61c5390",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/target/generate.py": "410137991477f8f77ec5ca918e4067697f20a10daf3f48ea3e1fc1eb6c165618",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/target/main.c": "39b1e2910d6e01ee0894895425f588fa9b6a85853d6b3fb32e866719f61c5390",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/screen.py": "39bfbe63942d15ad5bee4e32e08153c2edf56cc8ce2058f74c199550f16cf5ae",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/generate.py": "e9d5771c267b3544a5b37d239cf82ab047bd1fa32eff0e2e1f634a21fabc753c",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/main.c": "06b0ebb89e27cc21182234e8a87d4869ceab6602c01757e5e2e0e600995d7ca5",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/generate.py": "e2862fb802754c473a0c9cb8a949b30ed55eaee647aae9ef7e1d566168122987",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/main.c": "af3fd9eeebe75add408e9cb1582ee699a4a4ca781d58d8b15d1bead18df03a0e",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/oracle.c": "6e72ed5b4e6b4ea804d34212e9e84d9001207eea076a26a8a835f2a1c29f9dec",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/q288.c": "05955ce611f180c6cdef3becf74be47b5246f06c85931640f1c6ad33746bada0",
    "team/optimizations/o2/r2-config-reuse/caller/runq-q288/q288.h": "f8e4df00dba860487c168f6990edbf2dc8814291b825d30762c7ecad61821cc2",
    "team/optimizations/o2/r2-config-reuse/caller/split/generate.py": "2d4d5b28433b7b28c12ffd3629f170d661fe9663f68bc5b821045c67d2fb849d",
    "team/optimizations/o2/r2-config-reuse/caller/split/split.h": "94ccdc8e6212c0c0d7ef0e8795c8edcdc9a02e173802bea18965bbce5e01e222",
    "team/optimizations/o2/r2-config-reuse/public/gemv.S": "9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2",
    "team/optimizations/o2/r2-safe-tail/machine_model.py": "8fb2ac208d8db9083464fb839c06b46ec365234d72b819822563830dad90171e",
    "team/optimizations/o2/r2-select/evidence/entry-v1/files/builds/build-probe-01/images/performance-s0-d0-s03/data/gemv.S.gz": "c88ea52fc5c724437a4058407ab859f2653f1305f3d2f383b5058cfc86ce99ea",
    "team/optimizations/o2/r2-select/evidence/entry-v1/files/builds/build-probe-01/images/performance-s0-d0-s03/gemv-reference.o.gz": "d7fe24c540ff89b629690b86690d5c5d61ed59c1407550fa96e9862c6360f0fd",
    "team/optimizations/o2/r2-vector-accum/evidence/firstdot-v1/library/member-extract/stdout.log": "b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af",
    "team/optimizations/o2/r2-vector-accum/firstdot/public/gemv.S": "1e1aa8ca665559efa6acab2648f4614c6121422aaf400d78c192e6accad5da47",
    "team/workloads/unified-vdot/check.py": "084bebc22e2f4665e5c7a7797e5cd2a6c73220719b4cf228ce3075ae2446bc66"
}
FUNCTION_PINS = {
    'q288_fused_rvv4':'66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab',
    'q288_tail_vdot':'b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3',
}


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def gs32_modules(repo):
    """Load unchanged helpers with their own ordinary import bindings.

    This operation is serial only. No worker that launches an EMU invokes it.
    Restoring import aliases does not alter the source modules or their gates.
    """
    saved = {name:sys.modules.get(name) for name in
             ('generate', 'screen', 'target', 'check_target', 'run_target')}
    modules = {}
    try:
        for name in saved:
            path = repo/REL/'gs32-rvv'/(name+'.py')
            need(sha(path.read_bytes()) == GS32_PINS[name+'.py'], 'fixed GS32 helper '+name)
            spec = importlib.util.spec_from_file_location('paired16_gs32_'+name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            modules[name] = module
    finally:
        for name, value in saved.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return modules


def fullmin_fixture(model, helpers, qgen):
    fixture = screen.constant_case(qgen.fixtures(), -128, -128)
    golden = helpers.python_golden(fixture, 0)
    need(sha(struct.pack('<288I', *golden)) == FULLMIN_OUTPUT_SHA,
         'fullmin equals the independently screened C/Python case')
    return fixture, golden


def replace_once(text, before, after):
    need(text.count(before) == 1, 'one generated replacement: '+before[:100])
    return text.replace(before, after)


def replace_array(header, name, size, values):
    pattern = r'static const unsigned '+name+r'\['+str(size)+r'\][^;]*;'
    replacement = ('static const unsigned '+name+'['+str(len(values))+'] '
                   '__attribute__((aligned(16),used)) = {'+','.join(map(str, values))+'};')
    header, count = re.subn(pattern, lambda _:replacement, header)
    need(count == 1, 'one generated array '+name)
    return header


def function_fragment(source, first, following):
    start = source.index(first)
    stop = source.index(following, start)
    return source[start:stop]


def adapt_main(original):
    # Preserve the mature judge, guards, prepare, and five fault controls for
    # the original datasets byte for byte in the new generated C source.
    guard = function_fragment(original, 'static unsigned guards(void)', 'static void prepare(')
    judge = function_fragment(original, '__attribute__((noinline,noclone)) static unsigned judge(',
                              'static unsigned controls(')
    min_guard = replace_once(guard, 'guards(void)', 'min_guards(void)')
    min_guard = replace_once(min_guard, 'const volatile struct guarded_packed *p=&q_packed;',
                            'const volatile struct guarded_packed *p=&q_min_packed;\n'
                            '    const volatile struct paired_guarded_x *x=&q_min_x;')
    min_guard = replace_once(min_guard, 'p->tail[i]!=guard ||',
                            'p->tail[i]!=guard || x->head[i]!=guard || x->tail[i]!=guard ||')
    min_judge = replace_once(judge, 'judge(unsigned d,unsigned kind) {',
                            'min_judge(void) {\n    const unsigned d=0,kind=5;')
    for before, after in (('if(guards())', 'if(min_guards())'),
                          ('q_golden[d][r]', 'q_min_golden[r]'),
                          ('dot(d,280+r,8)', '524288'),
                          ('q_context.packed!=q_packed.value', 'q_context.packed!=q_min_packed.value'),
                          ('q_context.x!=q_inputs[d]', 'q_context.x!=q_min_x.value')):
        min_judge = replace_once(min_judge, before, after)
    text = replace_once(original, 'int main(void) {', min_guard+min_judge+'int main(void) {')
    text = replace_once(text, 'for(unsigned i=0;i<6;++i) {', 'for(unsigned i=0;i<8;++i) {')
    extra = '''    prepare(0,5);
    q_context.packed=q_min_packed.value;q_context.x=q_min_x.value;
    q_wrappers[0](&q_context);
    unsigned min_verdict=min_judge();
    if(min_verdict) return fail("fullmin",min_verdict);
    record(0,0,3);
    text("Q_MIN checked=1 outputs=288 slots=8\\n");
'''
    measured_loop = ('    for(unsigned i=0;i<Q_WINDOWS;++i) {\n'
                     '        unsigned arm=q_order[i],kind=q_methods[arm];')
    text = replace_once(text, measured_loop, extra+measured_loop)
    for before, after in ((' windows=8\\n', ' windows=10\\n'),
        ('Q_FUNCTIONAL calls=22 controls=5 outputs=6336 warm=8 extra=6',
         'Q_FUNCTIONAL calls=29 controls=5 outputs=8352 warm=10 extra=9'),
        ('Q_END windows=8 full_calls=22 leaf_calls=0 inline_calls=22 probe_dots=1 failures=0',
         'Q_END windows=10 full_calls=29 leaf_calls=0 inline_calls=29 probe_dots=1 failures=0')):
        text = replace_once(text, before, after)
    text = replace_once(text, 'static const uint64_t guard=',
                        '_Static_assert(offsetof(struct paired_guarded_x,value)==16 &&\n'
                        '               offsetof(struct paired_guarded_x,tail)==304,"fullmin X guards");\n'
                        'static const uint64_t guard=')
    need(text.count(guard) == text.count(judge) == 1, 'original guards and judge preserved')
    for first, following in (('static void prepare(', '__attribute__((noinline,noclone)) static unsigned judge('),
                             ('static unsigned controls(', 'static void record(')):
        need(function_fragment(original, first, following) in text, 'original prepare/fault controls preserved')
    return text, dict(original_main_sha256=sha(original.encode()),
        retained_guard_sha256=sha(guard.encode()),retained_judge_sha256=sha(judge.encode()),
        fullmin_guard_sha256=sha(min_guard.encode()),fullmin_judge_sha256=sha(min_judge.encode()))


def produce(repo, out):
    for relative,pin in BASE_SOURCE_PINS.items():
        need(sha((repo/relative).read_bytes())==pin,'fixed thin source input '+relative)
    modules = gs32_modules(repo)
    base, base_check = modules['target'], modules['check_target']
    manifest = base.produce(repo, out)
    model, qgen, _ = base_check.support(repo)
    _, helpers = screen.support(repo)
    fixture, golden = fullmin_fixture(model, helpers, qgen)
    header = (out/'data.h').read_text()
    for before, after in (('#define Q_CONTRACT "'+base.CONTRACT+'"', '#define Q_CONTRACT "'+CONTRACT+'"'),
                           ('#define Q_WINDOWS 8', '#define Q_WINDOWS 10'),
                           ('#define Q_TOTAL_CALLS 22', '#define Q_TOTAL_CALLS 29')):
        header = replace_once(header, before, after)
    for name, size, values in (('q_order',8,ORDER),('q_methods',3,METHODS),
        ('q_functional_order',6,FUNCTIONAL_ORDER),('q_functional_datasets',6,FUNCTIONAL_DATASETS)):
        header = replace_array(header,name,size,values)
    header, count = re.subn(r'q_wrapper const q_wrappers\[3\][^;]*;',
                           lambda _:'q_wrapper const q_wrappers[4] = {'+','.join(WRAPPERS)+'};',header)
    need(count == 1, 'one four-arm wrapper table')
    header = replace_once(header, 'typedef void (*q_wrapper)(struct q288_context *);',
                          'extern void '+generate.NAME+'(struct q288_context *);\n'
                          'typedef void (*q_wrapper)(struct q288_context *);')
    guards = '{UINT64_C(0xd15ea5e5cafebabe),UINT64_C(0xd15ea5e5cafebabe)}'
    header += ('const struct guarded_packed q_min_packed __attribute__((aligned(16),used)) = {\n'
               +guards+', {\n'+(','.join(['-128']*32)+',\n')*2592+'}, '+guards+'};\n')
    header += ('struct paired_guarded_x { uint64_t head[2]; int8_t value[288]; uint64_t tail[2]; };\n'
               'const struct paired_guarded_x q_min_x __attribute__((aligned(16),used)) = {\n'
               +guards+', {\n'+(','.join(['-128']*32)+',\n')*9+'}, '+guards+'};\n')
    header += ('const uint32_t q_min_golden[288] __attribute__((aligned(16),used)) = {\n'
               +''.join(','.join('UINT32_C(0x%08x)'%x for x in golden[i:i+8])+',\n'
                        for i in range(0,288,8))+'};\n')
    (out/'data.h').write_text(header)
    parent, public = generate.load_parent(repo)
    assembly = (out/'fused.S').read_text()
    need(generate.NAME not in assembly, 'paired candidate absent before append')
    (out/'fused.S').write_text(assembly+generate.function(parent,public))
    main, source_certificate = adapt_main((out/'main.c').read_text())
    (out/'main.c').write_text(main)
    rows = [dict(id=i,kind='Q',algorithm=METHODS[i],method='vdot' if i==2 else 'rvv',
        variant=('paired16','gs32-v2','tail-agnostic','fused')[i],
        label=('paired16-rvv','gs32-rvv','tail-vdot','fused-rvv4')[i],
        scenario='self-warmed-prepacked-full-Q',n=1,dots=10368 if i==2 else 0,
        leaf=qgen.NEW[METHODS[i]],wrapper=WRAPPERS[i]) for i in range(4)]
    calls = [dict(stage=0,arm=a,dataset=d) for a,d in zip(FUNCTIONAL_ORDER,FUNCTIONAL_DATASETS)]
    calls.append(dict(stage=0,arm=0,dataset=FULLMIN_DATASET))
    for arm in ORDER:
        calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    need(len(calls)==29 and sum(rows[c['arm']]['dots'] for c in calls)+1==62209,
         '29 full Q calls and unchanged 62209 custom instructions')
    plan = [dict(index=arm,phase='measured',repeat=i//5,dataset=0,block=i//5,
                 role='anchor_start_method' if i%5==0 else 'anchor_end' if i%5==4 else 'method')
            for i,arm in enumerate(ORDER)]
    manifest.update(contract=CONTRACT,rows=rows,plan=plan,call_plan=calls,
        functional_calls=29,explicit_functional_calls=9,timed_q_calls=10,warmup_calls=10,
        full_q_calls=29,integer_core_executions=29*324,expected_dots=62209,
        formal_method_windows=10,formal_anchor_windows=4,method_anchor_overlap_windows=4,
        functional_order=list(FUNCTIONAL_ORDER)+( [0] ),
        functional_datasets=list(FUNCTIONAL_DATASETS)+( [FULLMIN_DATASET] ),
        count_expected_counter_enqueues=40,count_expected_csr_samples=40,
        fp_element_operations=dict(convert=29*2592,mul=29*5184,add=29*2592),
        statistics='two reversed P/G/TA observations and all four FR anchors; replay is not a new sample',
        selection_scope='guarded paired16 versus screened GS32v2 and unchanged TA/FR in this ELF',
        structural_hypothesis='pair exact s8 products in s16 under runtime guard; reduce widening reductions',
        fullmin=dict(dataset=FULLMIN_DATASET,arm=0,performance_sample=False,weight=-128,input=-128,
                     group_dot=524288,scale_dataset=0,output_sha256=FULLMIN_OUTPUT_SHA),
        guest_source_certificate=source_certificate,
        changed_candidate_function_words=None,candidate_instruction_count_change=None,
        target_runtime_qualified=False,performance_qualified=False)
    save(out/'manifest.json',manifest)
    inputs = json.loads((out/'producer-inputs.json').read_text())
    for relative,pin in BASE_SOURCE_PINS.items():
        # Keep the original decoded-payload pins for the named gzip inputs.
        inputs.setdefault(str(repo/relative),pin)
    for name,pin in GS32_PINS.items():
        inputs[str(repo/REL/'gs32-rvv'/name)] = pin
    own = Path(__file__).resolve().parent
    for name in ('generate.py','screen.py','target.py','TARGET_CONTRACT.md'):
        path = own/name
        inputs[str(path)] = sha(path.read_bytes())
    save(out/'producer-inputs.json',inputs)
    return manifest


def command(argv, out, label):
    start = time.monotonic()
    process = subprocess.run([str(x) for x in argv],cwd=out,capture_output=True,timeout=120)
    (out/(label+'.stdout.log')).write_bytes(process.stdout)
    (out/(label+'.stderr.log')).write_bytes(process.stderr)
    record = dict(argv=[str(x) for x in argv],returncode=process.returncode,
        elapsed_seconds=time.monotonic()-start,stdout_sha256=sha(process.stdout),stderr_sha256=sha(process.stderr))
    save(out/(label+'.json'),record)
    need(process.returncode==0,'command failed '+label+': '+process.stderr.decode(errors='replace'))
    return record


def build(repo, am, out):
    need(not out.exists() and not out.is_relative_to(repo),'fresh isolated target build')
    base = gs32_modules(repo)['target']
    for name,pin in base.LIB_PINS.items():
        need(sha((am/name).read_bytes())==pin,'immutable AM input '+name)
    out.mkdir(parents=True)
    produce(repo,out/'source')
    source,objects = out/'source',out/'objects'
    objects.mkdir()
    cc,ld,objcopy = (shutil.which(t) for t in ('riscv64-linux-gnu-gcc','riscv64-linux-gnu-ld','riscv64-linux-gnu-objcopy'))
    need(all((cc,ld,objcopy)),'GNU target tools available')
    common=[cc,'-fno-pic','-march=rv64gv','-mcmodel=medany','-mabi=lp64d','-mno-relax','-I'+str(source)]
    cflags=['-std=gnu11','-ffreestanding','-fno-tree-vectorize','-fno-tree-slp-vectorize',
        '-fno-tree-loop-distribute-patterns','-fno-ipa-cp','-fno-ipa-icf','-fno-optimize-sibling-calls',
        '-fno-lto','-ffp-contract=off','-fno-fast-math','-static','-O2','-Wall','-Werror',
        '-fno-asynchronous-unwind-tables','-fno-builtin','-fno-stack-protector','-Wno-main']
    units=('main.c','q288.c','oracle.c','timers.S','kernels.S','fused.S')
    records=[]
    for name in units:
        records.append(command(common+(cflags if name.endswith('.c') else ['-O0'])+
            ['-c',source/name,'-o',objects/(Path(name).stem+'.o')],out,'compile-'+Path(name).stem))
    records.append(command([ld,'-melf64lriscv','-L',am/'am/src/nemu/ldscript',
        '-T',am/'am/src/nemu/isa/riscv/boot/loader64.ld','--undefined=q288_full','--gc-sections',
        '-o',out/'paired16-target.elf','--start-group',*[objects/(Path(n).stem+'.o') for n in units],
        am/'am/build/am-riscv64-xs.a',am/'libs/klib/build/klib-riscv64-xs.a','--end-group'],out,'link'))
    records.append(command([objcopy,'-S','--set-section-flags','.bss=alloc,contents','-O','binary',
        out/'paired16-target.elf',out/'paired16-target.bin'],out,'objcopy'))
    for name,pin in base.LIB_PINS.items():
        need(sha((am/name).read_bytes())==pin,'AM input unchanged after link '+name)
    result=dict(contract=CONTRACT,status='PAIRED16_TARGET_BUILD_COMPLETE',commands=records,
        elf_sha256=sha((out/'paired16-target.elf').read_bytes()),
        bin_sha256=sha((out/'paired16-target.bin').read_bytes()),compile_workers=1,
        tools={str(Path(t).resolve()):sha(Path(t).read_bytes()) for t in (cc,ld,objcopy)},
        immutable_am_inputs={str(am/n):pin for n,pin in base.LIB_PINS.items()},
        target_runtime_qualified=False,performance_qualified=False)
    save(out/'build.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--am-home',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    sys.dont_write_bytecode=True
    result=build(args.repo.resolve(),args.am_home.resolve(),args.output.resolve())
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','immutable_am_inputs')},indent=2))
