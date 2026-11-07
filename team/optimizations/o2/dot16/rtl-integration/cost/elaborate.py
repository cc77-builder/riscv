#!/usr/bin/env python3
"""Generate two full-IO FU cost inputs with an existing read-only classpath.

Reproduce the previously tested feature1 RTL before compiling the unchanged O4
cost generator. No Mill invocation, resident write, functional PASS, or mapping.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = 'dot16-production-fu-cost-generation-v2'
GENERATOR_SHA = 'de06a6f46d19d6d4a42cbcff19f081e7423747578951c9b341d50076a913e97b'
SOURCE_SHA = '80637d38348fbecd928f6442fd0c69fab763a918ac8da8642a5a3667dacdc9c2'
OLD_CP_SHA = 'ab6aaa12cb8b9508d1a1bf994d63561a08f2112ea6d9d48b30ac7916fc1dfdde'
HELPERS = {
    'process_helper.py': ('team/optimizations/o2/dot16/rtl-integration/run_fu.py',
                          'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'),
    'classpath_helper.py': ('team/optimizations/o2/dot16/rtl-integration/decode/run.py',
                            '0214e9a220b905156c9818342832a9226e3b7bfcce2a8f5340f0b659f7c68b7c'),
}
CACHE_JSON = {
    'runClasspath.json': '225e392471d4fe3b162f3b2a40e25d3e9c3d84dfafd3f5d287efff6bb7aadf25',
    'scalaCompilerClasspath.json': '366e7637594a2156008a282e6136df2a7359b3db61471e241dde3a8a79496cba',
    'allScalacOptions.json': '2630309dd4ea5bbb5018926f156fdbbbe4179663d3a0554fe288935be5bad734',
}
ORIGINAL_RTL = {
    'VDotElastic.sv': 'c15778eb5c7089af40422b7002fde00d552dd7274b88cecb5f132d15e984ed1e',
    'VDotElasticFuTestTop.sv': '47235cf3f7f7b80f62037c03fbddfc76d1f79ebc7cdb2652b6fe9441390510b9',
    'VDotProducts.sv': '0c1e566dd820f80382c64b98a74882ff400e5cb63cd511bcd19831759597178a',
    'VDotReduce.sv': 'ed09c5ac8ca7a0a910ac8d51000ef1de8f01dadca4bec544467d1678ebeaaf85',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def main(a):
    os.sched_setaffinity(0, {a.cpu})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    deadline = time.monotonic() + a.budget_seconds
    repo, evidence, out = a.repo.resolve(), a.fu_root.resolve(), a.output.resolve()
    need(a.cpu in range(4) and 30 <= a.budget_seconds <= 900, 'finite four-core budget')
    need(a.output.is_absolute() and Path(os.path.abspath(a.output)) == out and not out.exists(), 'fresh real output')
    need(not out.is_relative_to(repo) and not repo.is_relative_to(out), 'output separate from resident')
    need(not out.is_relative_to(evidence) and not evidence.is_relative_to(out), 'preserve old evidence')
    cache = repo/'out/dot16-fu-20261106-pro2'
    source = evidence/'flag1-01/campaign/source.json'
    old_cp = evidence/'decode-flag0-02/classpath-before.json'
    generator = repo/'team/optimizations/o4/GenerateVDotCost.scala'
    need(sha(source) == SOURCE_SHA and sha(old_cp) == OLD_CP_SHA and sha(generator) == GENERATOR_SHA,
         'reviewed source, classpath evidence and unchanged O4 generator')
    old_status = json.loads((evidence/'flag1-01/status.json').read_bytes())
    need(old_status.get('qualification') == 'DOT16_FU_FEATURE_1_PASS' and old_status.get('passed') is True
         and old_status.get('process_group_absent') is True, 'applicable original FU receipt')
    here = Path(__file__).resolve().parent
    pins = {str(p): sha(p) for p in (Path(__file__).resolve(), here/'GENERATION_CONTRACT.md', source,
                                   old_cp, generator, evidence/'flag1-01/status.json')}
    for rel, expected in HELPERS.values():
        need(sha(repo/rel) == expected, 'fixed helper ' + rel)
        pins[str(repo/rel)] = expected
    for name, expected in CACHE_JSON.items():
        p = cache/'vdotElasticFu'/name
        need(sha(p) == expected, 'observed immutable cached recipe ' + name)
        pins[str(p)] = expected
    for rel, expected in json.loads(source.read_bytes()).items():
        need(sha(repo/rel) == expected, 'production source differs from FU evidence: ' + rel)
        pins[str(repo/rel)] = expected
    for name, expected in ORIGINAL_RTL.items():
        p = evidence/'flag1-01/campaign/rtl'/name
        need(sha(p) == expected, 'original tested generated RTL')
        pins[str(p)] = expected
    java = Path('/home/lizufan/.local/share/graalvm-jdk-21.0.12/bin/java')
    firtool = Path('/home/lizufan/riscv-tools/firtool-1.62.1/bin/firtool')
    yosys = Path('/usr/bin/yosys')
    need(sha(yosys) == 'dab84e88b53146fe22d675a142de32b1e545ee9b7fe1054238f6220245b24c8d', 'fixed parser')
    for tool in (java, firtool, yosys):
        pins[str(tool)] = sha(tool)

    out.mkdir(parents=True)
    snap = out/'source-snapshot'
    snap.mkdir()
    for source_path, target in [(Path(__file__), 'elaborate.py'), (here/'GENERATION_CONTRACT.md', 'GENERATION_CONTRACT.md'),
                                (generator, 'GenerateVDotCost.scala'), (source, 'original-source.json'),
                                (old_cp, 'old-classpath.json')]:
        shutil.copyfile(source_path, snap/target)
        need(sha(snap/target) == pins[str(source_path.resolve())], 'source snapshot')
    for name, (rel, expected) in HELPERS.items():
        shutil.copyfile(repo/rel, snap/name)
        need(sha(snap/name) == expected, 'helper snapshot')
    util = module(snap/'process_helper.py', 'fu_cost_process_helper')
    cp_util = module(snap/'classpath_helper.py', 'fu_cost_classpath_helper')
    status = dict(contract=CONTRACT, status='RUNNING', started=util.stamp(), commands=[],
                  top='CommonFuCostTop', cpu_affinity=[a.cpu], nice=5, budget_seconds=a.budget_seconds,
                  existing_cache_read_only=True, mill_invoked=False, resident_modified=False,
                  functional_qualified=False, synthesis_complete=False, sta_complete=False,
                  original_rtl_reproduced_byte_exact=False, generated=[])
    snapshots = {str(p): sha(p) for p in snap.iterdir() if p.is_file()}
    env = os.environ.copy()
    for key in ('JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'JAVA_OPTS'):
        env.pop(key, None)
    tmp = out/'tmp'
    tmp.mkdir()
    flags = dict(VDOT_DOT16='1', VDOT_O2_ELASTIC='1', VDOT_T14_FUSED_INPUT='1',
                 VDOT_O1_HANDOFF='0', VDOT_T12_TRACE='0', VDOT_T13_TRACE='0', VDOT_O1_TRACE='0', VDOT_O2_TRACE='0')
    env.update(flags, CHISEL_FIRTOOL_PATH=str(firtool.parent), TMPDIR=str(tmp), LANG='C', LC_ALL='C',
               JAVA_HOME=str(java.parent.parent), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    java_base = [str(java), '-Xmx4G', '-Xss8m', '-XX:ActiveProcessorCount=1', '-XX:+UseSerialGC',
                 '-XX:-UsePerfData', '-Djava.io.tmpdir='+str(tmp)]
    cp_before = None
    all_paths = None

    def command(label, argv):
        remaining = deadline-time.monotonic()
        need(remaining > 1, 'total deadline exhausted before ' + label)
        rec = dict(label=label, argv=list(map(str, argv)), started=util.stamp(),
                   budget_seconds=min(300, remaining), feature=env['VDOT_DOT16'], exit_code=None)
        status['commands'].append(rec)
        proc = None
        try:
            with (out/(label+'.log')).open('wb') as log:
                proc = subprocess.Popen(rec['argv'], cwd=out, env=env, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                rec['pid'] = proc.pid
                save(out/'result.json', status)
                rec['exit_code'] = proc.wait(timeout=rec['budget_seconds'])
            need(rec['exit_code'] == 0, label+' failed')
            need(not util.group_exists(proc.pid), label+' left children')
        finally:
            if proc is not None:
                if util.group_exists(proc.pid):
                    rec['cleanup_complete'] = util.stop_group(proc)
                rec['reaped'] = proc.poll() is not None
                rec['group_absent'] = not util.group_exists(proc.pid)
            rec['finished'] = util.stamp()
            save(out/'result.json', status)

    try:
        values = {n: json.loads((cache/'vdotElasticFu'/n).read_bytes())['value'] for n in CACHE_JSON}
        run_paths = cp_util.parse_classpath(json.dumps(values['runClasspath.json']))
        compiler_paths = cp_util.parse_classpath(json.dumps(values['scalaCompilerClasspath.json']))
        old_records = json.loads(old_cp.read_bytes())
        old_paths = [p['path'] for p in old_records]
        need(cp_util.classpath_identity(old_paths, repo) == old_records, 'cached classes/resources differ from original decode evidence')
        # The FU module adds two explicitly absent optional resource roots and
        # its own classes to the already-pinned production runtime classpath.
        optional = [str(repo/'vdotElasticFu'/n) for n in ('compile-resources', 'src/main/resources')]
        fu_classes = str(cache/'vdotElasticFu/compile.dest/classes')
        need(set(run_paths)-set(old_paths) == set(optional+[fu_classes]), 'closed FU classpath additions')
        need(all(not Path(p).exists() and not Path(p).is_symlink() for p in optional), 'original empty FU resource slots')
        options = values['allScalacOptions.json']
        plugins = [s.split(':', 1)[1] for s in options if s.startswith('-Xplugin:')]
        need(len(plugins) == 1 and all(isinstance(s, str) for s in options), 'single observed compiler plugin')
        all_paths = list(dict.fromkeys(old_paths+[fu_classes]+compiler_paths+plugins))
        cp_before = cp_util.classpath_identity(all_paths, repo)
        save(out/'classpath-before.json', cp_before)
        save(out/'inputs.json', dict(originals=pins, snapshots=snapshots, run_paths=run_paths,
                                    compiler_paths=compiler_paths, scalac_options=options,
                                    absent_optional_resources=optional, flags=flags,
                                    java_base=java_base, firtool_path=str(firtool)))
        command('java-version', [java, '-version'])
        command('firtool-version', [firtool, '--version'])
        command('reproduce-original-feature1', java_base+['-cp', ':'.join(run_paths),
                'team.vdot.GenerateVDotElasticFu', str(out/'original-replay')])
        need({p.name: sha(p) for p in (out/'original-replay').glob('*.sv')} == ORIGINAL_RTL,
             'cache failed to reproduce all four previously tested SV files exactly')
        status['original_rtl_reproduced_byte_exact'] = True
        classes = out/'cost-classes'
        classes.mkdir()
        command('compile-cost-generator', java_base+['-cp', ':'.join(compiler_paths), 'scala.tools.nsc.Main',
                '-classpath', ':'.join(old_paths), '-d', str(classes), *options, str(snap/'GenerateVDotCost.scala')])
        for feature in (0, 1):
            env['VDOT_DOT16'] = str(feature)
            rtl = out/('feature'+str(feature))/'rtl'
            command('generate-feature'+str(feature), java_base+['-cp', str(classes)+':'+':'.join(old_paths),
                    'team.vdot.GenerateVDotCost', 'fu', str(rtl)])
            files = sorted(rtl.glob('*.sv'))
            need({p.name for p in files} == {'CommonFuCostTop.sv', 'VDotElastic.sv', 'VDotProducts.sv', 'VDotReduce.sv'},
                 'closed generated full-IO cost RTL set')
            need(all(b'// ----- 8< ----- FILE "' not in p.read_bytes() for p in files), 'no virtual RTL files')
            ys = out/('parse-feature'+str(feature)+'.ys')
            ys.write_text('\n'.join(['read_verilog -sv -DSYNTHESIS '+str(p) for p in files]+
                          ['hierarchy -check -top CommonFuCostTop', 'check -assert'])+'\n')
            command('parse-feature'+str(feature), [yosys, '-T', '-s', ys])
            status['generated'].append(dict(feature=feature, flags={**flags, 'VDOT_DOT16': str(feature)},
                files=[dict(path=str(p.relative_to(out)), bytes=p.stat().st_size, sha256=sha(p)) for p in files]))
        need(cp_util.classpath_identity(all_paths, repo) == cp_before, 'classpath mutated during generation')
        need(all(sha(Path(p)) == h for p, h in pins.items()), 'original input changed')
        need(all(sha(Path(p)) == h for p, h in snapshots.items()), 'snapshot input changed')
        need(all(not Path(p).exists() and not Path(p).is_symlink() for p in optional), 'optional resources changed')
        need(time.monotonic() < deadline, 'total deadline exhausted during final identity')
        status.update(status='TWO_COST_INPUTS_GENERATED_AND_PARSED', input_identity_unchanged=True)
    except Exception as exc:
        status.update(status='FAILED', error=type(exc).__name__+': '+str(exc))
        raise
    finally:
        status['finished'] = util.stamp()
        save(out/'result.json', status)
        print(json.dumps({k: status.get(k) for k in ('status', 'error', 'original_rtl_reproduced_byte_exact',
                                                   'input_identity_unchanged', 'functional_qualified')}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--fu-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cpu', type=int, choices=range(4), default=1)
    p.add_argument('--budget-seconds', type=int, default=900)
    main(p.parse_args())
