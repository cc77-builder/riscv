"""Count retired PCs in the reference instret window without changing guest code."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import importlib.util
import json
import os
import re
import resource
import shutil
import signal
import struct

HERE = Path(__file__).resolve().parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

ref = load('profile_first_token_reference', HERE / 'reference.py')
e = load('profile_evidence_helpers', HERE.parent / 'evidence.py')
b, c, old = ref.b, ref.c, ref.old
need, read, save, sha = e.need, e.read, e.save, e.sha
CONTRACT = 'r2-s3-first-token-reference-pc-profile-v1'
PARENT_SOURCE = '6ea9a43ddfa4420f00c7e62f101035e1e7fbf85610e607c4d7762b96c803bd2b'


def functions(build, record):
    elf = c.base.f.g.ELF((build / (b.PREFIX + '.elf')).read_bytes()); spans = {}
    for line in (build / 'metadata.stdout.log').read_text().splitlines():
        match = re.fullmatch(r'\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+|0x[0-9a-fA-F]+)\s+FUNC\s+\S+\s+\S+\s+(\S+)\s+(\S+)\s*', line)
        if not match or match[3] == 'UND': continue
        start, size, name = int(match[1], 16), int(match[2], 0), match[4]
        if not size: continue
        need(name in elf.symbols and tuple(elf.symbols[name][:2]) == (start, size), 'actual ELF symbol equals pinned readelf record')
        need(start % 2 == 0 and size > 0 and size % 2 == 0, 'aligned nonempty function extent')
        spans.setdefault((start, start + size), set()).add(name)
    ordered = [(a, z, sorted(names)) for (a, z), names in sorted(spans.items())]
    need(ordered and all(left[1] <= right[0] for left, right in zip(ordered, ordered[1:])), 'nonoverlapping function extents; exact aliases combined')
    sites = [int(row['pc'], 16) for row in record['counter_sites']]
    need([row['csr'] for row in record['counter_sites']] == ['0xc00', '0xc02', '0xc02', '0xc00'], 'fixed four-CSR order')
    words = [struct.unpack('<I', elf.read(pc, 4))[0] for pc in sites]
    need(all(word & 0x000fffff == (((word >> 7 & 31) << 7) | 0x2073) and word >> 20 == int(row['csr'], 16)
             for word, row in zip(words, record['counter_sites'])), 'actual CSRRS read with zero source and declared CSR')
    base, end = min(a for a, _, _ in ordered), max(z for _, z, _ in ordered)
    need(base >= 0x80000000 and 0 < end - base <= 16 * 1024 * 1024, 'bounded complete text function span')
    return elf, ordered, dict(base=base, end=end, counter_pcs=sites, counter_rd=[word >> 7 & 31 for word in words])


def derive(source, layout):
    need(hashlib.sha256(source).hexdigest() == PARENT_SOURCE, 'exact team-owned parent adapter source')
    snippet = r'''
/* Team-owned host-only observer. No NEMU API or guest state is written here. */
static const uint64_t profile_pcs[4] = { @PCS@ };
static const unsigned profile_rds[4] = { @RDS@ };
static uint64_t profile_counts[@SLOTS@], profile_values[4], profile_before[4];
static unsigned profile_seen;
static bool profile_active;
static void profile_record(uint64_t pc,uint64_t before,uint64_t after,const riscv64_CPU_state *cpu) {
    require(after>=before && after-before<=1,"single-step retirement increment");
    for(unsigned k=0;k<4;++k) if(pc==profile_pcs[k]) {
        require(profile_seen==k && after-before==1,"each four-CSR instruction retires once in order");
        profile_values[k]=cpu->gpr[profile_rds[k]]._64;profile_before[k]=before;++profile_seen;
        if(k==1)profile_active=true;
        if(k==2)profile_active=false;
    }
    if(profile_active) {
        require(after-before==1 && pc>=UINT64_C(@BASE@) && pc<UINT64_C(@END@) && !(pc&1),"complete retired PC inside declared window span");
        ++profile_counts[(pc-UINT64_C(@BASE@))/2];
    }
}
static void profile_save(const char *directory) {
    require(profile_seen==4 && !profile_active,"one complete instret window");
    FILE *pcs=create(directory,"retired-pcs.tsv");uint64_t total=0;
    for(uint64_t k=0;k<@SLOTS@;++k) if(profile_counts[k]) {
        total+=profile_counts[k];
        require(fprintf(pcs,"0x%llx\t%llu\n",(unsigned long long)(UINT64_C(@BASE@)+k*2),(unsigned long long)profile_counts[k])>0,"complete PC histogram row");
    }
    require(fclose(pcs)==0,"PC histogram close");
    require(profile_before[2]>=profile_before[1] && profile_values[2]>=profile_values[1] &&
        total==profile_before[2]-profile_before[1] && total==profile_values[2]-profile_values[1],"retirement conservation equals actual instret delta");
    FILE *out=create(directory,"pc-profile.json");
    fprintf(out,"{\"format\":\"retired-pc-profile-v1\",\"window_retired\":%llu,\"counter_values\":[",(unsigned long long)total);
    for(unsigned k=0;k<4;++k)fprintf(out,"%s%llu",k?",":"",(unsigned long long)profile_values[k]);
    fprintf(out,"],\"before_retired\":[");
    for(unsigned k=0;k<4;++k)fprintf(out,"%s%llu",k?",":"",(unsigned long long)profile_before[k]);
    fprintf(out,"],\"include_start_instret\":true,\"include_end_instret\":false,\"xiangshan_cycles_measured\":false}\n");
    require(fclose(out)==0,"profile receipt close");
}
'''
    for key, value in {'PCS': ','.join('UINT64_C(%d)' % pc for pc in layout['counter_pcs']),
                       'RDS': ','.join(map(str, layout['counter_rd'])), 'SLOTS': str((layout['end'] - layout['base'] + 1) // 2),
                       'BASE': str(layout['base']), 'END': str(layout['end'])}.items(): snippet = snippet.replace('@' + key + '@', value)
    changes = [
        ('int main(int argc,char **argv) {', snippet + '\nint main(int argc,char **argv) {'),
        ('uint64_t before_pc=current.pc;', 'uint64_t before_pc=current.pc;uint64_t profile_previous=last_retired;'),
        ('uint64_t count=retired();idle=count==last_retired?idle+1:0;last_retired=count;',
         'uint64_t count=retired();idle=count==last_retired?idle+1:0;last_retired=count;\n        profile_record(before_pc,profile_previous,count,&current);'),
        ('    printf("REFERENCE_ADAPTER_DONE', '    profile_save(argv[3]);\n    printf("REFERENCE_ADAPTER_DONE'),
    ]
    text = source.decode()
    for before, after in changes:
        need(text.count(before) == 1, 'one finite observer insertion'); text = text.replace(before, after)
    inverse = text
    for before, after in reversed(changes):
        need(inverse.count(after) == 1, 'one inverse observer insertion'); inverse = inverse.replace(after, before)
    need(inverse.encode() == source, 'entire parent adapter exactly recoverable')
    return text.encode()


def analyze(build, baseline, dest, record, receipt):
    actual = ref.validate(build, dest, record, receipt, receipt['method'], False)
    need(actual == read(baseline / 'validation.json'), 'complete existing raw reference qualification reproduced')
    binaries = {p.name for p in baseline.glob('*.bin')}
    need(binaries == {p.name for p in dest.glob('*.bin')} and all(sha(dest / name) == sha(baseline / name) for name in binaries),
         'every whole guest image, memory dump, initial/final register and CSR byte equals qualified baseline')
    profile = read(dest / 'pc-profile.json'); report = struct.unpack('<64Q', (dest / 'report.bin').read_bytes())
    need(profile['format'] == 'retired-pc-profile-v1' and profile['counter_values'] == list(report[16:20]) and
         profile['window_retired'] == report[18] - report[17] == profile['before_retired'][2] - profile['before_retired'][1] and
         profile['include_start_instret'] is True and profile['include_end_instret'] is False and
         profile['xiangshan_cycles_measured'] is False, 'exact original four values and retirement conservation')
    elf, spans, layout = functions(build, record); per_pc = {}; grouped = Counter(); unmapped = Counter()
    for line in (dest / 'retired-pcs.tsv').read_text().splitlines():
        match = re.fullmatch(r'(0x[0-9a-f]+)\t([1-9][0-9]*)', line); need(match is not None, 'canonical positive PC histogram')
        pc, count = int(match[1], 16), int(match[2]); need(pc not in per_pc and pc % 2 == 0, 'unique aligned retired PC')
        need(layout['base'] <= pc < layout['end'], 'retired PC within declared code span')
        per_pc[pc] = count; candidates = [(a, z, tuple(names)) for a, z, names in spans if a <= pc < z]
        need(len(candidates) <= 1, 'no double assignment across function extents')
        if candidates: grouped[candidates[0]] += count
        else: unmapped[hex(pc)] += count
        low = struct.unpack('<H', elf.read(pc, 2))[0]; elf.read(pc, 4 if low & 3 == 3 else 2)
    total = sum(per_pc.values()); need(total == profile['window_retired'] > 0 and sum(grouped.values()) + sum(unmapped.values()) == total,
                                   'complete PC and function conservation')
    rows = [dict(start=hex(a), end=hex(z), names=list(names), retired=count, fraction=count / total)
            for (a, z, names), count in sorted(grouped.items(), key=lambda pair: (-pair[1], pair[0]))]
    return dict(status='REFERENCE_PC_PROFILE_PASS', method=receipt['method'], window_retired=total,
        counter_values=profile['counter_values'], unique_retired_pcs=len(per_pc), functions=rows, unmapped=dict(unmapped),
        all_guest_binary_files_equal=sorted(binaries), raw_profile_sha256={name: sha(dest / name) for name in ('retired-pcs.tsv', 'pc-profile.json')},
        count_boundary='includes initial instret instruction, excludes final instret; includes actual fences and dispatch within that interval',
        xiangshan_cycles_measured=False, performance_qualified=False)


def compiler_command(argv, compiler, adapter, source, output, nemu):
    command = [str(compiler), *argv[1:]]
    need(command.count('-MF') == command.count('-o') == command.count(str(adapter / 'reference_runner.c')) == 1,
         'exact original output/source arguments')
    command[command.index('-MF') + 1] = str(output / 'runner.d'); command[command.index('-o') + 1] = str(output / 'reference-profiler')
    command[command.index(str(adapter / 'reference_runner.c'))] = str(source / 'reference_runner.c')
    include = [i for i, arg in enumerate(command) if arg.startswith('-I')]
    need([command[i] for i in include] == ['-I' + str(nemu / sub) for sub in ('include', 'src/isa/riscv64/include')], 'exact two joined original fixed header roots')
    for i, sub in zip(include, ('include', 'src/isa/riscv64/include')): command[i] = '-I' + str(source / 'headers' / sub)
    return command


def run(args):
    build, reference, adapter, identity, output = (getattr(args, key).resolve() for key in ('build', 'reference', 'adapter', 'identity', 'output'))
    need(not output.exists() and not any(output.is_relative_to(p) for p in (b.REPO, build, reference, adapter, identity.parent)), 'fresh isolated diagnostic output')
    record, files, physical, checker = ref.inputs(build, adapter, identity)
    base_state, base_result = e.closed(reference), read(reference / 'results.json')
    need(base_state['contract'] == base_result['contract'] == b.CONTRACT and
         base_state['status'] == base_result['status'] == b.REFERENCE_PASS and
         base_state['reference_runs'] == base_result['reference_runs'] == 4 and
         len(base_state['records']) == 4 and base_result['records'] == base_state['records'], 'actual closed final four-case reference qualification')
    previous = read(reference / 'runtime-inputs.json')
    need(all(files.get(path) == value for path, value in previous.items()), 'same actual baseline shared inputs')
    for path in (Path(__file__).resolve(), HERE / 'PROFILE.md'): c.pin(files, path)
    for path in reference.rglob('*'):
        if path.is_file(): c.pin(files, path)
    parent = read(adapter / 'build.json')
    need(parent['status'] == 'REFERENCE_ADAPTER_BUILD_PASS' and sha(adapter / 'reference_runner.c') == PARENT_SOURCE == parent['artifacts']['reference_runner.c'], 'exact qualified team adapter')
    need(sha(adapter / 'compile.command.json') == parent['artifacts']['compile.command.json'], 'actual qualified parent compile command')
    parent_inputs = read(adapter / 'inputs.json')['files']
    need(sha(adapter / 'inputs.json') == parent['inputs_sha256'], 'original adapter input registry')
    for name in ('build.json', 'inputs.json', 'compile.command.json'): c.pin(files, adapter / name)
    for path, value in parent_inputs.items(): need(sha(path) == value, 'unchanged original adapter source/header/config/compiler')
    _, _, layout = functions(build, record)
    output.mkdir(parents=True)
    state = dict(contract=CONTRACT, status='PREPARING', started=c.base.f.h.now(), active_pid=None, records=[], reference_runs=0,
                 new_emu_runs=0, performance_qualified=False, original_build=str(build), original_reference=str(reference),
                 original_profile=str(output), original_adapter=str(adapter), configuration=physical['configuration'])
    persist = lambda: save(output / 'state.json', state); persist()
    try:
        _, hard = resource.getrlimit(resource.RLIMIT_FSIZE); need(hard == resource.RLIM_INFINITY or hard >= 128 * 1024 * 1024, '128MiB output allowance')
        resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024 * 1024, hard)); checks = {}
        source = output / 'source'; source.mkdir()
        (source / 'parent-adapter').mkdir()
        for name in ('build.json', 'inputs.json', 'compile.command.json'): shutil.copyfile(adapter / name, source / 'parent-adapter' / name)
        shutil.copyfile(adapter / 'reference_runner.c', source / 'parent-reference_runner.c')
        shutil.copytree(adapter / 'headers', source / 'headers')
        nemu = Path(physical['configuration']['reference']).resolve().parents[1]
        header_pins = {Path(path).resolve().relative_to(nemu).as_posix(): value for path, value in parent_inputs.items()
                       if Path(path).suffix == '.h' and Path(path).resolve().is_relative_to(nemu)}
        need(header_pins and {p.relative_to(source / 'headers').as_posix() for p in (source / 'headers').rglob('*') if p.is_file()} == set(header_pins), 'exact parent header snapshot membership')
        for rel, value in header_pins.items(): need(sha(source / 'headers' / rel) == value, 'actual compile headers equal original qualified inputs')
        derived = derive((adapter / 'reference_runner.c').read_bytes(), layout); (source / 'reference_runner.c').write_bytes(derived)
        save(source / 'derivation.json', dict(parent_sha256=PARENT_SOURCE, derived_sha256=sha(source / 'reference_runner.c'), exact_inverse=True, layout=layout))
        command = read(adapter / 'compile.command.json')['argv']; compiler = Path(shutil.which(command[0])).resolve()
        need(parent_inputs[str(compiler)] == sha(compiler), 'same native compiler as the qualified adapter')
        command = compiler_command(command, compiler, adapter, source, output, nemu)
        save(output / 'compile.command.json', command)
        compile_rec = dict(command=command, cwd=str(output), status='RUNNING', started=c.base.f.h.now(), process_started=False,
                           exit_code=None, cpu_affinity=sorted(os.sched_getaffinity(0)), external_timeout_seconds=60)
        state['compiler'] = compile_rec
        def compile_progress():
            state['active_pid'] = compile_rec.get('pid') if not compile_rec.get('process_group_absent_after_exit') else None
            save(output / 'compile-result.json', compile_rec); persist()
        compile_progress()
        try:
            with (output / 'compile.stdout.log').open('wb') as stdout, (output / 'compile.stderr.log').open('wb') as stderr:
                old.previous.spawn(command, output, stdout, stderr, compile_rec, compile_progress, dict(os.environ), 60)
            need(compile_rec['exit_code'] == 0 and compile_rec.get('direct_child_reaped') and compile_rec.get('process_group_absent_after_exit') and
                 not compile_rec.get('residual_process_group'), 'actual native observer build and complete compiler group closure')
            compile_rec['status'] = 'PROFILE_ADAPTER_BUILD_PASS'
        except BaseException as error: compile_rec.update(status='FAILED', error=repr(error)); raise
        finally: compile_rec['finished'] = c.base.f.h.now(); compile_progress()
        c.pin(files, compiler)
        for path in [output / 'reference-profiler', output / 'compile.command.json', output / 'compile-result.json', output / 'runner.d', *source.rglob('*')]:
            if path.is_file(): c.pin(files, path)
        dependencies = (output / 'runner.d').read_text().replace('\\\n', ' ').split(':', 1)[1].split()
        for path in dependencies: c.pin(files, Path(path))
        save(output / 'runtime-inputs.json', files)
        e.closure(output, b.REPO, output / 'closure', [build, Path(record['norm_build'])])
        state['status'] = 'RUNNING'; persist()
        for label, method in (('fr', 3), ('ta', 4)):
            dest = output / label; dest.mkdir(); raw, control = ref.image(build, record, method, False, 0)
            (dest / 'image.bin').write_bytes(raw); save(dest / 'image-control.json', control); del raw
            casefiles = dict(files); c.pin(casefiles, dest / 'image.bin'); c.pin(casefiles, dest / 'image-control.json')
            save(dest / 'runtime-inputs.json', casefiles); checker.verify_files(casefiles)
            argv = [str(output / 'reference-profiler'), physical['configuration']['reference'], str(dest / 'image.bin'), str(dest), 'builtin',
                    '100000000', '600', str(build / 'dump-plan.txt'), '1']
            rec = dict(contract=CONTRACT, name=label, method=method, negative=False, status='RUNNING', command=argv, cwd=str(dest),
                started=c.base.f.h.now(), process_started=False, exit_code=None, cpu_affinity=sorted(os.sched_getaffinity(0)))
            state['records'].append(rec); state['reference_runs'] += 1
            def progress():
                state['active_pid'] = rec.get('pid') if not rec.get('process_group_absent_after_exit') else None
                save(dest / 'result.json', rec); persist()
            progress()
            try:
                with (dest / 'stdout.log').open('wb') as stdout, (dest / 'stderr.log').open('wb') as stderr:
                    old.previous.spawn(argv, dest, stdout, stderr, rec, progress, dict(os.environ), 630)
                actual = analyze(build, reference / label, dest, record, rec); save(dest / 'analysis.json', actual)
                checker.verify_files(casefiles); rec.update(status=actual['status'], analysis_sha256=sha(dest / 'analysis.json')); checks[label] = actual
            except BaseException as error: rec.update(status='FAILED', error=repr(error)); raise
            finally: rec['finished'] = c.base.f.h.now(); progress()
        checker.verify_files(files); state['status'] = 'FIRST_TOKEN_REFERENCE_PROFILE_PASS'
        save(output / 'results.json', dict(contract=CONTRACT, status=state['status'], checks=checks, reference_runs=2, new_emu_runs=0,
            performance_qualified=False, source_sha256=sha(__file__), reference_validator_sha256=sha(HERE / 'reference.py')))
    except BaseException as error: state.update(status='FAILED', error=repr(error)); raise
    finally:
        state['reference_runs'] = sum(row.get('process_started') is True for row in state['records'])
        state['finished'] = c.base.f.h.now(); persist()
    return state


def recheck(args):
    build, reference, profile, output = (getattr(args, key).resolve() for key in ('build', 'reference', 'profile', 'output'))
    need(not output.exists() and not any(output.is_relative_to(p) for p in (build, reference, profile)), 'fresh offline profile output')
    state, summary = e.closed(profile), read(profile / 'results.json')
    need(state['contract'] == summary['contract'] == CONTRACT and state['status'] == summary['status'] == 'FIRST_TOKEN_REFERENCE_PROFILE_PASS' and
         state['reference_runs'] == summary['reference_runs'] == 2 and len(state['records']) == 2, 'closed exact actual profile campaign')
    compile_rec = read(profile / 'compile-result.json')
    need(state['compiler'] == compile_rec and compile_rec['status'] == 'PROFILE_ADAPTER_BUILD_PASS' and compile_rec['exit_code'] == 0 and
         compile_rec.get('direct_child_reaped') and compile_rec.get('process_group_absent_after_exit') and not compile_rec.get('residual_process_group') and
         type(compile_rec['pid']) is int and compile_rec['pid'] > 0 and compile_rec['process_group'] == compile_rec['pid'], 'actual compiler group completely closed')
    runtime, info = read(profile / 'runtime-inputs.json'), read(profile / 'closure/pins.json')
    parent_dir = profile / 'source/parent-adapter'; original_adapter = Path(state['original_adapter'])
    for name in ('build.json', 'inputs.json', 'compile.command.json'):
        need(runtime[str(original_adapter / name)] == sha(parent_dir / name), 'same actual parent adapter metadata')
    parent, parent_inputs = read(parent_dir / 'build.json'), read(parent_dir / 'inputs.json')['files']
    need(parent['inputs_sha256'] == sha(parent_dir / 'inputs.json') and parent['artifacts']['compile.command.json'] == sha(parent_dir / 'compile.command.json'), 'bound original parent compile registry')
    old_profile = Path(state['original_profile']); old_nemu = Path(state['configuration']['reference']).parents[1]
    actual_command = read(profile / 'compile.command.json'); compiler = Path(actual_command[0])
    need(parent_inputs[str(compiler)] == runtime[str(compiler)] and
         actual_command == compiler_command(read(parent_dir / 'compile.command.json')['argv'], compiler, original_adapter, old_profile / 'source', old_profile, old_nemu) and
         compile_rec['command'] == actual_command and compile_rec['cwd'] == str(old_profile) and compile_rec['external_timeout_seconds'] == 60,
         'exact original compiler and finite argv transformation; no offline physical path reads')
    header_pins = {Path(os.path.normpath(path)).relative_to(old_nemu).as_posix(): value for path, value in parent_inputs.items()
                   if Path(path).suffix == '.h' and Path(os.path.normpath(path)).is_relative_to(old_nemu)}
    need(header_pins and {p.relative_to(profile / 'source/headers').as_posix() for p in (profile / 'source/headers').rglob('*') if p.is_file()} == set(header_pins), 'exact recovered original compile header membership')
    for rel, value in header_pins.items(): need(sha(profile / 'source/headers' / rel) == value, 'same qualified header source bytes')
    original_repo = Path(info['original_repo']); source = profile / 'closure/repo'
    expected = {Path(path).relative_to(original_repo).as_posix(): value for path, value in runtime.items() if Path(path).is_relative_to(original_repo)}
    need(info['files'] == expected and info['runtime_inputs_sha256'] == sha(profile / 'runtime-inputs.json') and not info['supplemental_pins'], 'exact historical source closure')
    for rel, value in expected.items(): need(sha(source / rel) == value, 'all frozen profile source bytes')
    need(b.REPO == source and Path(__file__).resolve().is_relative_to(source), 'execute this profile rechecker from its historical closure')
    e.imports(ref, source, info, profile)
    need(sha(__file__) == expected[Path(__file__).resolve().relative_to(source).as_posix()], 'same historical profile observer and analyzer')
    roots = [(Path(state['original_build']), build), (Path(state['original_reference']), reference), (Path(state['original_profile']), profile)]
    for path, value in runtime.items():
        for oldroot, newroot in roots:
            if Path(path).is_relative_to(oldroot):
                need(sha(newroot / Path(path).relative_to(oldroot)) == value, 'every preserved historically consumed byte'); break
    record = read(build / 'result.json'); _, _, layout = functions(build, record)
    need(derive((profile / 'source/parent-reference_runner.c').read_bytes(), layout) == (profile / 'source/reference_runner.c').read_bytes(), 'exact entire host-only observer derivation')
    before = e.inventory(profile); checks = {}; records = {row['name']: row for row in state['records']}
    need(set(records) == {'fr', 'ta'} and len({row['pid'] for row in records.values()}) == 2, 'two independent historical reference processes')
    for label, method in (('fr', 3), ('ta', 4)):
        dest = profile / label; rec = read(dest / 'result.json'); olddest = Path(state['original_profile']) / label
        need(rec == records[label] and rec['status'] == 'REFERENCE_PC_PROFILE_PASS' and rec['method'] == method and rec['negative'] is False and rec.get('finished'), 'same complete historical case receipt')
        need(type(rec['pid']) is int and rec['pid'] > 0 and rec['process_group'] == rec['pid'], 'actual positive PID and its same owned process group')
        need(rec['cwd'] == str(olddest) and rec['command'] == [str(Path(state['original_profile']) / 'reference-profiler'), state['configuration']['reference'],
            str(olddest / 'image.bin'), str(olddest), 'builtin', '100000000', '600', str(Path(state['original_build']) / 'dump-plan.txt'), '1'], 'exact bounded historical profiler invocation')
        need(read(dest / 'runtime-inputs.json') == {**runtime, str(olddest / 'image.bin'): sha(dest / 'image.bin'), str(olddest / 'image-control.json'): sha(dest / 'image-control.json')}, 'exact per-case inputs')
        actual = analyze(build, reference / label, dest, record, rec)
        need(actual == read(dest / 'analysis.json') == read(profile / 'results.json')['checks'][label] and rec['analysis_sha256'] == sha(dest / 'analysis.json'), 'raw histogram, guest dumps and derived analysis agree')
        checks[label] = dict(window_retired=actual['window_retired'], functions=actual['functions'], unmapped=actual['unmapped'])
    need(e.inventory(profile) == before, 'all original profile evidence unchanged after offline check')
    output.mkdir(parents=True); result = dict(status='FROZEN_REFERENCE_PROFILE_RECHECK_PASS', checks=checks, new_reference_runs=0, new_emu_runs=0, performance_qualified=False)
    save(output / 'result.json', result); return result


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('reference profile signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for action, names in (('run', ('build', 'reference', 'adapter', 'identity', 'output')), ('recheck', ('build', 'reference', 'profile', 'output'))):
        command = sub.add_parser(action)
        for name in names: command.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(); os.sched_setaffinity(0, [min(os.sched_getaffinity(0))]); result = run(args) if args.action == 'run' else recheck(args)
    print(json.dumps({key: result[key] for key in ('status', 'reference_runs', 'new_emu_runs', 'performance_qualified') if key in result}, indent=2))
