#!/usr/bin/env python3
"""Validate the already-qualified prefix overlay in the existing real parent.

This controller never updates the resident source/cache and never builds an EMU.
It compiles only the unchanged parent harness, preserves all existing checkers,
and consumes the complete candidate class directory from the completed prefix local-01.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = 'dot16-prefix-real-parent-v1'
LOCAL_CONTRACT = 'dot16-csa-prefix-local-v1'
LOCAL_INPUTS_SHA = '1afacb22c143705355ffed93b62824b2a02153e799b003bcc7f92dba1b10c219'
OVERLAY_SHA = 'f36dd44ef66c0058a73839bfeaacd321cc6ac7d41144c622c38371948375c4bf'
GEN_INPUTS_SHA = 'ec29dc8725cf3a1c04ea684e2753debc1a9b2a04d37b4adadcdfe96f85ec20d8'
CP_SHA = 'd9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902'
CANDIDATE_SHA = '1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb'
WRAPPER_SHA = '912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92'
LOCAL_RESULT_SHA = 'a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0'
BINDING_SHA = 'eefefaea3ab263b2be754a076dd5d07465bf3392699e217df017da7435921dc7'
VECTORS_SHA = '901a7be30e62b81bcd3df55b20538a5ba9c879ba9c7c34f28b8c0421d8e6a327'
CSA_RTL_SHA = '68227036423ff34235b275546dc7d2341fb5e890857e1b9098f4bc070f9545f6'
PREFIX_RTL_SHA = {0: '8cbaa598a2d7887b31b616b36894a4769b3e60de627f31972d34840f7c712f3d',
                  1: '3ce276e8ea48a36ebbb77e6251d1607c39cc6e7a7b988a38e5cb9a563f4afe5a'}
PARENT_STATUS = {
    0: '21eaa2a213d2812d8b86df3d7ac9c0944cf6ef6396d1e1858ff0cbf8c817fc88',
    1: '028559bf5ea081daeeb1441eb4cbd9420fb7a9eadf0e9442f4f34c0cfbc50b09',
}
PARENT_GENERATED = {
    0: 'be932495cd15c13a4d467cf6d4dc92256f72f93043c22c85bc6311af8d3d1403',
    1: '69484df7cc9f4992f2fd32a84290d1a79f65fbdd2707669ef03d97c560c512b4',
}
PARENT_INPUTS = {
    'team/optimizations/o2/dot16/rtl-integration/parent/run.py': '8a8eee12389133d9f9a9f9e1b5729e40e4193cc2a6bb7ba5a122989e6596ffe8',
    'team/optimizations/o2/dot16/rtl-integration/parent/derive_test.py': 'b6733d205f1b46f5500837f27c99e60ca74f6fed680e4bcf600e547daa7f1375',
    'team/optimizations/o2/dot16/rtl-integration/parent/extra_cases.cpp.inc': '8769f41b4083b746085eadf25464f377b27b091d9b09729b7b6f6feca324c752',
    'team/optimizations/o2/dot16/rtl-integration/parent/check_coverage.py': '0a7a9b31df768235c0ca1c98aaa477bef58172b615ade9c5cf23d71088905bd1',
    'team/optimizations/o2/dot16/rtl-integration/parent/CONTRACT.md': '07ed215e2f1be7a48d80f7c94a05fa2e6e836231d19f00ed017c87f09c1edd9f',
    'team/optimizations/o2/dot16/rtl-integration/run_fu.py': 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3',
    'team/optimizations/o2/dot16/rtl-integration/source-manifest.json': 'fd556a8c498ab4a3928ecd1cae46f4ac7af4fa8b319d3741d31713f5c2fdba89',
    'team/optimizations/o2/dot16/rtl-integration/candidate.patch': '5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416',
    'team/optimizations/o2/run_rtl.py': '125cd5a308fa0253c7bd0dbc6d9ea7593afea6e7a118e3b544bfd1dab0fd7922',
    'team/optimizations/o2/parent/GenerateVDotElasticParent.scala': '73b21658b8a91cbceadce3689a7e4853c96d64088934d4b3094c5c112c248bf4',
    'team/optimizations/o2/parent/parent_test.cpp': 'c691558f7c53433b212efe0c81d902abdfab7128257143cb329366c7032e952f',
    'team/optimizations/o2/parent/check_negative.py': '8ef1103242c88c09a106c212a22bae10f30798e0c7ac41ba58ce49b953b5ef74',
    'team/optimizations/o2/parent/test_negative.py': '073515026e62fffa382c04cf7e4f16ac73ccc9a0df9d00478c8a170789392c0e',
    'team/optimizations/o2/parent/check_trace.py': 'cc0a2b74aa2f40a1fad93dc4d6e92cef6fb946f88e895a0f394cba14e394e2c1',
    'team/optimizations/o2/parent/test_trace.py': '87fcce2dd79f5d4c757ea8a8f93852dee3a785f94af710838303bf01a089aecf',
    'team/optimizations/o4/perf/audit.py': '780f8daa1801fa378d3fa097029e2ddc393d9e906cf4f8a64e27023854326abe',
}
FAULTS = ('identity', 'rob', 'high', 'metadata', 'wen', 'stall', 'route', 'double',
          'clock', 'occupancy', 'kill_p', 'kill_r', 'survivor', 'duplicate',
          'missing', 'reset', 'perf_input', 'perf_swap', 'perf_parent', 'perf_cross')
PARENT_REL = Path('team/optimizations/o2/parent')
EXTENSION_REL = Path('team/optimizations/o2/dot16/rtl-integration/parent')
TOP = 'VDotElasticParentTestTop'
LOG_OBJECT_MESSAGES = (
    (b'xiangshan.backend.fu.wrapper.VFDivSqrt', b'Vfdiv OpType not supported'),
    (b'xiangshan.backend.exu.ExeUnitImp', b'fuOutValidOH %b should be one-hot)\\n'),
    (b'xiangshan.backend.fu.wrapper.VIDiv', b'Vfdiv OpType not supported'),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def compare_log_object_labels(actual, reference):
    """Allow labels and permutations of exactly three complete independent prints.

    Only the observed four-line blocks are recognized. Their conditions, file
    descriptors, format strings, arguments and whitespace remain byte-exact.
    Comparison is in memory; actual RTL and diagnostics are never rewritten.
    """
    fields = ((b'x1_bore', b"64'h0"),
              (b'x1_bore_2', b"64'h0, x2_bore"),
              (b'x1_bore_1', b"64'h0"))
    labels, old_spans, new_spans = [], [], []
    old_blocks, new_blocks = {}, {}
    for (classname, message), (condition, arguments) in zip(LOG_OBJECT_MESSAGES, fields):
        head = (b'      if ((`PRINTF_COND_) & ' + condition + b' & ~reset)\n'
                b"        $fwrite(32'h80000002,\n"
                b'                "[ERROR][time=%d] ' + classname + b'@')
        tail = b': ' + message + b'",\n                ' + arguments + b');\n'
        pattern = re.compile(rb'(?m)^' + re.escape(head) + rb'([0-9a-f]{1,8})' + re.escape(tail))
        old_matches = list(pattern.finditer(reference))
        new_matches = list(pattern.finditer(actual))
        need(len(old_matches) == 1 and len(new_matches) == 1,
             'one exact old/new complete error block for ' + classname.decode('ascii'))
        old_match, new_match = old_matches[0], new_matches[0]
        def normalized(match):
            raw = match.group(0)
            left, right = match.start(1) - match.start(), match.end(1) - match.start()
            return raw[:left] + b'OBJECT_LABEL' + raw[right:]
        old_blocks[classname], new_blocks[classname] = normalized(old_match), normalized(new_match)
        need(new_blocks[classname] == old_blocks[classname],
             'complete same-class error block equal after only its object label')
        old_spans.append((old_match.start(), old_match.end(), classname))
        new_spans.append((new_match.start(), new_match.end(), classname))
        labels.append(dict(class_name=classname.decode('ascii'),
                           old_label=old_match.group(1).decode('ascii'),
                           new_label=new_match.group(1).decode('ascii'),
                           old_block_sha256=hashlib.sha256(old_match.group(0)).hexdigest(),
                           new_block_sha256=hashlib.sha256(new_match.group(0)).hexdigest(),
                           comparison_block_sha256=hashlib.sha256(old_blocks[classname]).hexdigest()))
    old_spans.sort(); new_spans.sort()
    for side, spans in (('old', old_spans), ('new', new_spans)):
        need(len(spans) == 3 and all(a[1] == b[0] for a, b in zip(spans, spans[1:])),
             'exactly three contiguous complete error blocks in ' + side)
    old_begin, old_end = old_spans[0][0], old_spans[-1][1]
    new_begin, new_end = new_spans[0][0], new_spans[-1][1]
    old_prefix, old_suffix = reference[:old_begin], reference[old_end:]
    new_prefix, new_suffix = actual[:new_begin], actual[new_end:]
    need(new_prefix == old_prefix and new_suffix == old_suffix,
         'LogPerfEndpoint prefix/suffix outside the three-block region stay byte-exact')
    old_order = [classname for _, _, classname in old_spans]
    new_order = [classname for _, _, classname in new_spans]
    normalized_old = old_prefix + b''.join(old_blocks[name] for name in old_order) + old_suffix
    normalized_new = new_prefix + b''.join(new_blocks[name] for name in old_order) + new_suffix
    need(normalized_new == normalized_old,
         'LogPerfEndpoint differs only in three object labels and complete block permutation')
    return dict(kind='diagnostic_error_object_labels_and_three_block_order', labels=labels,
                old_sha256=hashlib.sha256(reference).hexdigest(), old_bytes=len(reference),
                new_sha256=hashlib.sha256(actual).hexdigest(), new_bytes=len(actual),
                comparison_sha256=hashlib.sha256(normalized_new).hexdigest(),
                changed_labels=sum(row['old_label'] != row['new_label'] for row in labels),
                old_order=[name.decode('ascii') for name in old_order],
                new_order=[name.decode('ascii') for name in new_order],
                old_region=[old_begin, old_end], new_region=[new_begin, new_end],
                prefix_sha256=hashlib.sha256(old_prefix).hexdigest(),
                suffix_sha256=hashlib.sha256(old_suffix).hexdigest(),
                block_order_changed=new_order != old_order,
                simultaneous_error_log_order_may_differ=new_order != old_order,
                complete_same_class_blocks_equal_after_labels=True,
                outside_region_bytes_equal=True, real_rtl_modified=False,
                diagnostic_text_byte_exact=actual == reference)


def run(a):
    deadline = time.monotonic() + a.budget_seconds
    need(a.cpu == 1 and 120 <= a.budget_seconds <= 1200, 'CPU1 and at most1200 seconds')
    os.sched_setaffinity(0, {1})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    repo, cost, parents, local, out = [p.resolve() for p in
                                     (a.repo, a.cost_root, a.parent_root, a.local_root, a.output)]
    here = Path(__file__).resolve().parent
    need(a.output.is_absolute() and Path(os.path.abspath(a.output)) == out and not out.exists(),
         'fresh absolute output without symlink parents')
    for path in (repo, cost, parents, local, here):
        need(path.is_dir() and out != path and not out.is_relative_to(path)
             and not path.is_relative_to(out), 'separate existing input/output trees')
    need(a.local_result_sha256 == LOCAL_RESULT_SHA,
         'reviewed exact completed prefix result SHA required')
    out.mkdir(parents=True)
    result = dict(contract=CONTRACT, status='PREFLIGHT', started=stamp(), commands=[],
                  cpu_affinity=[1], nice=os.getpriority(os.PRIO_PROCESS, 0),
                  budget_seconds=a.budget_seconds, parent_results=[],
                  parent_qualified=False, fullcore_qualified=False,
                  application_performance_qualified=False, cost_qualified=False,
                  core_cost_qualified=False, performance_measured=False,
                  resident_modified=False, original_cache_modified=False,
                  production_default_changed=False, new_core_builds=0, new_core_runs=0)
    save(out/'result.json', result)
    pending = [None]
    def interrupt(signum, _frame):
        if pending[0] is None:
            pending[0] = signum
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    def check():
        if pending[0] is not None:
            raise InterruptedError('received signal ' + str(pending[0]))
        need(time.monotonic() < deadline, 'total wall budget exhausted')
    pins, snapshots, generated_pins, link_targets = {}, {}, {}, {}
    def pin(path, expected=None):
        check()
        path = Path(path)
        need(path.is_absolute() and path.is_file(), 'real absolute input ' + str(path))
        actual = sha(path)
        need(expected is None or actual == expected, 'fixed input ' + str(path))
        key = str(path)
        need(key not in pins or pins[key] == actual, 'consistent input identity')
        pins[key] = actual
        link_targets[key] = str(path.resolve())
        return path
    def snapshot(source, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        need(not target.exists(), 'fresh snapshot target')
        target.write_bytes(Path(source).read_bytes())
        need(sha(target) == pins[str(source)], 'exact snapshot ' + str(target))
        snapshots[str(target)] = sha(target)
        return target
    util = None
    try:
        pin(Path(__file__).resolve())
        pin(here/'PARENT_CONTRACT.md')
        pin(local/'result.json', a.local_result_sha256)
        pin(local/'inputs.json', LOCAL_INPUTS_SHA)
        pin(local/'overlay-classes.json', OVERLAY_SHA)
        upstream = json.loads((local/'result.json').read_bytes())
        need(upstream['contract'] == LOCAL_CONTRACT and
             upstream['status'] == 'PREFIX_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE',
             'applicable completed prefix local-01')
        need(all(upstream.get(k) is True for k in ('arithmetic_equivalent', 'fu_qualified',
             'inputs_unchanged', 'generated_inputs_unchanged', 'original_classpath_unchanged',
             'all_children_reaped')) and upstream['candidate_source_sha256'] == CANDIDATE_SHA
             and upstream['candidate_wrapper_sha256'] == WRAPPER_SHA,
             'complete upstream source/wrapper/arithmetic/FU identity')
        need(len(upstream['prefix_miters']) == 2 and
             {(x['feature'], x['width'], x['row_count']) for x in upstream['prefix_miters']}
             == {(0, 19, 2), (1, 20, 4)} and all(x['status'] == 'PASS'
             and x['solver_equivalence_proved'] is True for x in upstream['prefix_miters']),
             'both actual prefix modular-sum proofs completed')
        need(len(upstream['fu_results']) == 2 and
             {x['feature'] for x in upstream['fu_results']} == {0, 1}
             and all(x['passed'] is True for x in upstream['fu_results']),
             'both original prefix FU campaigns completed')
        local_inputs = json.loads((local/'inputs.json').read_bytes())
        for path, digest in {**local_inputs['originals'], **local_inputs['snapshots']}.items():
            pin(path, digest)
        gen = cost/'generation-01'
        pin(gen/'inputs.json', GEN_INPUTS_SHA)
        pin(gen/'classpath-before.json', CP_SHA)
        cfg = json.loads((gen/'inputs.json').read_bytes())
        old_cp = json.loads((gen/'classpath-before.json').read_bytes())
        overlay = local/'overlay-classes'
        overlay_pins = json.loads((local/'overlay-classes.json').read_bytes())
        need(overlay.is_dir() and len(overlay_pins) == 23, 'complete23 prefix overlay classes')
        def overlay_identity():
            return {str(p): sha(p) for p in sorted(overlay.rglob('*')) if p.is_file()}
        need(all(Path(p).is_relative_to(overlay) for p in overlay_pins)
             and overlay_identity() == overlay_pins, 'exact complete verified overlay, including anonymous classes')
        for path, digest in overlay_pins.items():
            pin(path, digest)
        pin(local/'source-snapshot/VDotDatapath.scala', CANDIDATE_SHA)
        pin(local/'source-snapshot/VDotElastic.scala', WRAPPER_SHA)
        reference_rtl = {}
        for feature in (0, 1):
            rows = [x for x in upstream['generated'] if x['feature'] == feature and x['kind'] == 'cost']
            need(len(rows) == 1, 'one completed local cost generation per feature')
            root = local/f'cost-feature{feature}/rtl'
            names = {Path(x['path']).name for x in rows[0]['files']}
            need(names == {'CommonFuCostTop.sv', 'VDotElastic.sv', 'VDotCarrySaveRows.sv',
                          f'VDotPrefixFinish{20 if feature else 19}.sv', 'extern_modules.sv'},
                 'exact frozen prefix local generation closure')
            for record in rows[0]['files']:
                path = local/record['path']
                need(path.resolve().is_relative_to(root), 'local reference remains inside its RTL root')
                pin(path, record['sha256'])
                need(path.stat().st_size == record['bytes'], 'local reference byte count')
            pin(root/'VDotCarrySaveRows.sv', CSA_RTL_SHA)
            pin(root/f'VDotPrefixFinish{20 if feature else 19}.sv', PREFIX_RTL_SHA[feature])
            reference_rtl[feature] = root
        vectors = pin(local/'source-snapshot/vectors.tsv', VECTORS_SHA)
        local_helper = pin(local/'source-snapshot/process_helper.py',
                           'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3')
        cp_helper = pin(local/'source-snapshot/classpath_helper.py',
                        '0214e9a220b905156c9818342832a9226e3b7bfcce2a8f5340f0b659f7c68b7c')
        snap = out/'source-snapshot'
        tree = snap/'tree'
        util = load_module(snapshot(local_helper, snap/'process_helper.py'), 'prefix_parent_process')
        cp_util = load_module(snapshot(cp_helper, snap/'classpath_helper.py'), 'prefix_parent_classpath')
        snapshot(Path(__file__).resolve(), snap/'prefix_parent.py')
        snapshot(here/'PARENT_CONTRACT.md', snap/'PARENT_CONTRACT.md')
        binding_path = pin(here/'parent_binding.py', BINDING_SHA)
        binding = load_module(snapshot(binding_path, snap/'parent_binding.py'), 'prefix_parent_binding')
        vectors = snapshot(vectors, snap/'vectors.tsv')
        cp_paths = [item['path'] for item in old_cp]
        need(cp_util.classpath_identity(cp_paths, repo) == old_cp, 'unchanged complete base classpath')
        need(all(not Path(p).exists() and not Path(p).is_symlink()
                 for p in cfg['absent_optional_resources']), 'original optional resources remain absent')
        save(out/'classpath-before.json', old_cp)
        expected_inputs = {str(repo/rel): digest for rel, digest in PARENT_INPUTS.items()}
        baselines = {}
        for feature in (0, 1):
            old = parents/f'parent-flag{feature}-01'
            status_path = pin(old/'status.json', PARENT_STATUS[feature])
            status = json.loads(status_path.read_bytes())
            need(status['passed'] is True and status['parent_qualified'] is True
                 and status['qualification'] == f'DOT16_PARENT_FEATURE_{feature}_PASS'
                 and status['process_group_absent'] is True, 'completed original parent receipt')
            old_inputs = pin(old/'inputs.json')
            need(json.loads(old_inputs.read_bytes()) == expected_inputs, 'exact original parent source map')
            for rel, digest in PARENT_INPUTS.items():
                source = pin(old/'source-snapshot'/Path(rel).name, digest)
                if feature == 0:
                    snapshot(source, tree/rel)
                else:
                    need(source.read_bytes() == (tree/rel).read_bytes(), 'same parent sources for both features')
            pin(old/'source-snapshot/dot16_parent_test.cpp')
            pin(old/'campaign/vectors.tsv', VECTORS_SHA)
            manifest = pin(old/'campaign/generated-files.json', PARENT_GENERATED[feature])
            recorded = json.loads(manifest.read_bytes())
            old_files = []
            for record in recorded:
                path = old/'campaign'/record['path']
                need(path.resolve().is_relative_to(old/'campaign/rtl'), 'parent generated manifest remains in its RTL tree')
                pin(path, record['sha256'])
                need(path.stat().st_size == record['bytes'], 'original generated byte count')
                if path.suffix in ('.sv', '.v'):
                    old_files.append(path)
            old_rtl = old/'campaign/rtl'
            actual = {p.resolve() for pattern in ('*.sv', '*.v') for p in old_rtl.rglob(pattern)}
            need(set(p.resolve() for p in old_files) == actual and old_files,
                 'complete original parent RTL inventory')
            need(all((old_rtl/name).is_file() for name in (TOP+'.sv', 'ClockGate.sv',
                 'VDotProducts.sv', 'VDotElastic.sv', 'IterBlockI8Nr4.sv')),
                 'original real parent, clock gate, VDot and DIV')
            baselines[feature] = dict(root=old, rtl=old_rtl, files=old_files)
        # The audit's ROOT=parents[4] finds the unchanged check_trace under tree/.
        checker_dir = tree/PARENT_REL
        extension_dir = tree/EXTENSION_REL
        negative = load_module(checker_dir/'check_negative.py', 'prefix_parent_negative_interface')
        need(tuple(negative.FAULTS) == FAULTS, 'unchanged complete20 negative controls')
        deriver = load_module(extension_dir/'derive_test.py', 'prefix_parent_original_deriver')
        verilator_root = Path('/home/lizufan/riscv-tools/verilator-5.052')
        verilator = pin(verilator_root/'bin/verilator',
                        '098b09b11ba7d3e904ae13d924a9e8dac8ced5c9d7c9beff3b9d36119a417581')
        pin(verilator_root/'bin/verilator_bin',
            '44e1e7e32a8f3005a2fc6323b040c871d43e9884b30fa801b10d06c342513b84')
        support_root = verilator_root/'share/verilator'
        support_files = sorted(p for p in support_root.rglob('*') if p.is_file())
        need(support_files and (support_root/'include/verilated.mk').is_file(), 'actual installed Verilator support')
        support_identity = {str(p): sha(p) for p in support_files}
        for path, digest in support_identity.items():
            expected = local_inputs['originals'].get(path,
                       local_inputs['originals'].get(str(Path(path).resolve())))
            need(expected == digest, 'same prefix-local Verilator support')
            pin(path, digest)
        for tool in ('/usr/bin/make', '/usr/bin/ar', '/usr/local/bin/clang++'):
            expected = local_inputs['originals'].get(tool)
            if expected is None:
                expected = local_inputs['originals'].get(str(Path(tool).resolve()))
            need(expected is not None, 'tool already bound by prefix-local: ' + tool)
            pin(tool, expected)
        pin(sys.executable)
        tmp = out/'tmp'
        tmp.mkdir()
        env = {**os.environ, **cfg['flags'], 'LANG': 'C', 'LC_ALL': 'C',
               'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
               'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': str(tmp),
               'CHISEL_FIRTOOL_PATH': str(Path(cfg['firtool_path']).parent),
               'VERILATOR_ROOT': str(support_root), 'MAKEFLAGS': '-j1',
               'PATH': '/usr/bin:/bin', 'MAKE': '/usr/bin/make',
               'CXX': '/usr/local/bin/clang++', 'LINK': '/usr/local/bin/clang++', 'AR': '/usr/bin/ar'}
        for key in ('JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'JAVA_OPTS',
                    'MAKEFILES', 'MFLAGS', 'MAKEOVERRIDES', 'PYTHONPATH', 'PYTHONSAFEPATH'):
            env.pop(key, None)
        java_base = [x if not x.startswith('-Djava.io.tmpdir=') else '-Djava.io.tmpdir='+str(tmp)
                     for x in cfg['java_base']]
        save(out/'inputs.json', dict(originals=pins, snapshots=snapshots,
             local_result_sha256=a.local_result_sha256, local_inputs_sha256=LOCAL_INPUTS_SHA,
             candidate_overlay_manifest_sha256=OVERLAY_SHA, recipe_sha256=GEN_INPUTS_SHA))
        result.update(status='RUNNING', upstream_prefix_local=str(local),
                      upstream_result_sha256=a.local_result_sha256, candidate_source_sha256=CANDIDATE_SHA,
                      candidate_wrapper_sha256=WRAPPER_SHA,
                      upstream_multiplication_miter_status=upstream['independent_miter']['status'])
        save(out/'result.json', result)

        def command(label, argv, limit=120, expected=0):
            check()
            record = dict(label=label, argv=list(map(str, argv)), started=stamp(),
                          feature=env['VDOT_DOT16'], expected_exit=expected,
                          budget_seconds=min(limit, deadline-time.monotonic()))
            result['commands'].append(record)
            proc = None
            log = out/(label+'.log')
            try:
                with log.open('wb') as stream:
                    proc = subprocess.Popen(record['argv'], cwd=out, env=env,
                        stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                    record['pid'] = proc.pid
                    save(out/'result.json', result)
                    until = time.monotonic()+record['budget_seconds']
                    while True:
                        check()
                        left = until-time.monotonic()
                        if left <= 0:
                            raise subprocess.TimeoutExpired(record['argv'], record['budget_seconds'])
                        try:
                            record['exit_code'] = proc.wait(timeout=min(.25, left))
                            break
                        except subprocess.TimeoutExpired:
                            continue
                need(expected is None or record['exit_code'] == expected, label+' exit mismatch')
                need(not util.group_exists(proc.pid), label+' left child processes')
            finally:
                if proc is not None:
                    try:
                        if util.group_exists(proc.pid):
                            record['cleanup_complete'] = util.stop_group(proc)
                    finally:
                        record['reaped'] = proc.poll() is not None
                        record['group_absent'] = not util.group_exists(proc.pid)
                record['finished'] = stamp()
                save(out/'result.json', result)
            return log, record['exit_code']

        # These two fixed test modules have no feature-dependent hardware input.
        command('original-checker-tests', [sys.executable, '-B', '-m', 'unittest', 'discover',
                '-s', checker_dir, '-p', 'test_*.py', '-v'], 120)
        classes = out/'parent-harness-classes'
        classes.mkdir()
        compile_cp = ':'.join([str(overlay), *cfg['run_paths']])
        command('compile-parent-harness', java_base+['-cp', ':'.join(cfg['compiler_paths']),
            'scala.tools.nsc.Main', '-classpath', compile_cp, '-d', classes,
            *cfg['scalac_options'], checker_dir/'GenerateVDotElasticParent.scala'], 300)
        harness_pins = {str(p): sha(p) for p in sorted(classes.rglob('*')) if p.is_file()}
        need((classes/'team/vdot/GenerateVDotElasticParent.class').is_file()
             and (classes/'team/vdot/VDotElasticParentTestTop.class').is_file()
             and harness_pins and all(Path(p).is_relative_to(classes/'team/vdot') for p in harness_pins),
             'only unchanged parent harness classes were newly compiled')
        generated_pins.update(harness_pins)
        save(out/'parent-harness-classes.json', harness_pins)
        runtime_cp = ':'.join([str(overlay), str(classes), *cfg['run_paths']])
        save(out/'runtime-classpath.json', dict(candidate_overlay_first=str(overlay),
             parent_harness_second=str(classes), base=cfg['run_paths']))
        for feature in (0, 1):
            check()
            env['VDOT_DOT16'] = str(feature)
            folder = out/f'feature{feature}'
            folder.mkdir()
            rtl = folder/'rtl'
            cpp = folder/'dot16_parent_test.cpp'
            derivation = deriver.derive(checker_dir/'parent_test.cpp',
                extension_dir/'extra_cases.cpp.inc', cpp, feature)
            old = baselines[feature]
            need(cpp.read_bytes() == (old['root']/'source-snapshot/dot16_parent_test.cpp').read_bytes(),
                 'byte-exact original derived parent C++')
            generated_pins[str(cpp)] = sha(cpp)
            save(folder/'test-derivation.json', derivation)
            command(f'generate-parent-{feature}', java_base+['-cp', runtime_cp,
                    'team.vdot.GenerateVDotElasticParent', rtl], 180)
            files = sorted({p.resolve() for pattern in ('*.sv', '*.v') for p in rtl.rglob(pattern)})
            need(files and all(p.is_relative_to(rtl) and b'// ----- 8< ----- FILE "' not in p.read_bytes()
                               for p in files), 'real complete parent RTL files')
            old_names = {p.relative_to(old['rtl']).as_posix() for p in old['files']}
            new_names = {p.relative_to(rtl).as_posix() for p in files}
            removed_modules = {'VDotProducts.sv', 'VDotReduce.sv'}
            new_modules = {'VDotCarrySaveRows.sv', f'VDotPrefixFinish{20 if feature else 19}.sv'}
            need(removed_modules <= old_names and not new_modules & old_names,
                 'original parent arithmetic closure matches the declared replacement')
            need(new_names == (old_names-removed_modules) | new_modules,
                 'real parent closure replaces only Products/Reduce with CSA/prefix')
            boundary_records = []
            for name in sorted(old_names-removed_modules):
                new_path, old_path = rtl/name, old['rtl']/name
                if name == 'VDotElastic.sv':
                    record = binding.verify_parent_wrapper(new_path.read_bytes(), old_path.read_bytes(), feature)
                    record.update(file=name, reference_file=str(old_path))
                    boundary_records.append(record)
                elif name == 'LogPerfEndpoint.sv':
                    record = compare_log_object_labels(new_path.read_bytes(), old_path.read_bytes())
                    record.update(file=name, reference_file=str(old_path))
                    boundary_records.append(record)
                elif name == 'extern_modules.sv':
                    raw = new_path.read_bytes()
                    for module_name in ('VDotCarrySaveRows', f'VDotPrefixFinish{20 if feature else 19}'):
                        marker = ('// external module '+module_name+'\n\n').encode()
                        need(raw.count(marker) == 1, 'one exact new external module comment')
                        raw = raw.replace(marker, b'', 1)
                    need(raw == old_path.read_bytes(), 'all existing external comments byte-exact')
                else:
                    need(new_path.read_bytes() == old_path.read_bytes(), 'unchanged parent/clock/DIV boundary '+name)
            for name in sorted(new_modules):
                actual_path, reference_path = rtl/name, reference_rtl[feature]/name
                need(actual_path.read_bytes() == reference_path.read_bytes(), 'same proved arithmetic RTL '+name)
                boundary_records.append(dict(file=name, actual_sha256=sha(actual_path),
                    reference_file=str(reference_path), reference_sha256=sha(reference_path), byte_exact=True))
            boundary_report = folder/'generation-boundary.json'
            save(boundary_report, dict(contract=CONTRACT, feature=feature,
                 comparisons=boundary_records, real_rtl_modified=False,
                 removed_modules=sorted(removed_modules), new_modules=sorted(new_modules),
                 changed_existing_modules=['VDotElastic.sv', 'LogPerfEndpoint.sv', 'extern_modules.sv'],
                 all_other_retained_sv_v_byte_exact=True))
            generated_pins[str(boundary_report)] = sha(boundary_report)
            def list_paths(path, root):
                return [(Path(t) if Path(t).is_absolute() else root/t).resolve()
                        for t in shlex.split(path.read_text(), comments=True)]
            old_resource = old['rtl']/'firrtl_black_box_resource_files.f'
            new_resource = rtl/'firrtl_black_box_resource_files.f'
            resource_names = {p.relative_to(old['rtl']).as_posix()
                              for p in list_paths(old_resource, old['rtl'])}
            resources = list_paths(new_resource, rtl)
            need('ClockGate.sv' in resource_names and len(resources) == len(set(resources))
                 and {p.relative_to(rtl).as_posix() for p in resources}
                 == resource_names | new_modules and set(resources).issubset(files),
                 'complete unchanged real ClockGate resources plus CSA/prefix')
            filelist = rtl/'filelist.f'
            listed = list_paths(filelist, rtl)
            need(len(listed) == len(files) and set(listed) == set(files), 'complete actual parent filelist')
            for path in files+[new_resource, filelist]:
                generated_pins[str(path)] = sha(path)
            save(folder/'generated-files.json', [dict(path=str(p.relative_to(folder)),
                 bytes=p.stat().st_size, sha256=sha(p)) for p in files+[new_resource, filelist]])
            # Exact existing run_rtl.py allowance for unchanged production DIV.
            expression = '_GEN[{1\'h0, io_pre_w[8]} + 2\'h1] + {io_pre_w[7:0], io_pre_w_low[7]};'
            positions = [n+1 for n, line in enumerate((rtl/'IterBlockI8Nr4.sv').read_text().splitlines())
                         if line.strip() == expression]
            need(len(positions) == 1 and positions[0] in (37, 46), 'existing exact DIV width waiver')
            waiver = folder/'divider-width.vlt'
            waiver.write_text('`verilator_config\nlint_off -rule WIDTHEXPAND -file "*/IterBlockI8Nr4.sv" -lines '
                              +str(positions[0])+'\n')
            generated_pins[str(waiver)] = sha(waiver)
            stem = f'parent-{feature}'
            command(stem+'-lint', [verilator, '--lint-only', '--assert', '--top-module', TOP,
                    waiver, *files], 120)
            obj = folder/'obj'
            command(stem+'-build', [verilator, '--cc', '--exe', '--build', '--assert',
                    '--top-module', TOP, '--Mdir', obj, '--compiler', 'clang', '-j', '1',
                    '-MAKEFLAGS', 'CXX=/usr/local/bin/clang++ LINK=/usr/local/bin/clang++ AR=/usr/bin/ar',
                    '-CFLAGS', '-std=c++17 -O2', waiver, *files, cpp], 300)
            binary = obj/('V'+TOP)
            generated_pins[str(binary)] = sha(binary)
            metadata = folder/'metadata.log'
            positive, _ = command(stem+'-positive', [binary, vectors, '-', metadata], 90)
            generated_pins[str(positive)] = sha(positive)
            generated_pins[str(metadata)] = sha(metadata)
            command(stem+'-positive-replay', [sys.executable, '-B', checker_dir/'check_negative.py',
                    '--positive', '--return-code', '0', '--log', positive], 60)
            audit = folder/'metadata-audit.json'
            command(stem+'-metadata-replay', [sys.executable, '-B', tree/'team/optimizations/o4/perf/audit.py',
                    '--control', positive, '--metadata', metadata, '--output', audit], 60)
            coverage = folder/'additional-coverage.json'
            command(stem+'-coverage', [sys.executable, '-B', extension_dir/'check_coverage.py',
                    '--result-log', positive, '--metadata-log', metadata, '--feature', str(feature),
                    '--output', coverage], 60)
            report = json.loads(coverage.read_bytes())
            need(report['status'] == f'DOT16_PARENT_FEATURE_{feature}_COVERAGE_PASS', 'original coverage completion')
            for fault in FAULTS:
                log, rc = command(stem+'-inject-'+fault, [binary, vectors, fault], 60, expected=None)
                command(stem+'-check-'+fault, [sys.executable, '-B', checker_dir/'check_negative.py',
                        '--fault', fault, '--return-code', str(rc), '--log', log], 30)
                generated_pins[str(log)] = sha(log)
            generated_pins[str(audit)] = sha(audit)
            generated_pins[str(coverage)] = sha(coverage)
            result['parent_results'].append(dict(feature=feature, checks_completed=True,
                 binary_sha256=sha(binary), faults=list(FAULTS),
                 coverage={k: v for k, v in report.items() if k != 'cases'},
                 real_clock_gate_unchanged=True,
                 other_parent_rtl_byte_exact_except_recorded=True,
                 generation_boundary_report=str(boundary_report),
                 generation_boundary_report_sha256=sha(boundary_report)))
            save(out/'result.json', result)
        check()
        for path, digest in {**pins, **snapshots, **generated_pins}.items():
            check()
            need(sha(path) == digest, 'final unchanged input/artifact '+path)
        need(all(str(Path(p).resolve()) == target for p, target in link_targets.items()), 'input link targets unchanged')
        need(overlay_identity() == overlay_pins, 'complete original candidate overlay unchanged')
        need(cp_util.classpath_identity(cp_paths, repo) == old_cp, 'complete original base classpath unchanged')
        need({str(p): sha(p) for p in sorted(support_root.rglob('*')) if p.is_file()} == support_identity,
             'complete Verilator support tree unchanged')
        need(all(not Path(p).exists() and not Path(p).is_symlink()
                 for p in cfg['absent_optional_resources']), 'optional resources stayed absent')
        need(all(row.get('reaped') is True and row.get('group_absent') is True for row in result['commands']),
             'all children reaped and process groups absent')
        check()
        save(out/'final-artifact-pins.json', generated_pins)
        result.update(status='PREFIX_REAL_PARENT_PASS', parent_qualified=True,
                      inputs_unchanged=True, generated_inputs_unchanged=True,
                      original_classpath_unchanged=True, original_overlay_unchanged=True,
                      all_children_reaped=True)
    except BaseException as exc:
        result.update(status='FAILED', error=repr(exc), parent_qualified=False)
        raise
    finally:
        result['finished'] = stamp()
        save(out/'result.json', result)
        if pins:
            save(out/'observed-input-pins.json', dict(files=pins, resolved_targets=link_targets))
    print(json.dumps({k: v for k, v in result.items() if k not in ('commands', 'parent_results')}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'cost-root', 'parent-root', 'local-root', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--local-result-sha256', required=True)
    parser.add_argument('--cpu', type=int, choices=(1,), default=1)
    parser.add_argument('--budget-seconds', type=int, default=1200)
    run(parser.parse_args())
