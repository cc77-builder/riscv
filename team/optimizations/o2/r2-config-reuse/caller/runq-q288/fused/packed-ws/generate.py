"""Generate two explicit packed-scale entry points from pinned team sources.

The first candidate changes exactly three machine words per complete function.
Keeping the unused stride setup and a zero tile increment preserves function
sizes, branch displacements and architectural instruction counts for screening.
No existing source, authoritative program or frozen experiment is modified.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import tempfile

REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/packed-ws')
Q = REL.parent.parent
CONTRACT = 'r2-s3-runq-q288-packed-ws-screen-v1'
PINS = {
    'team/optimizations/o2/r2-config-reuse/public/gemv.S': '9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2',
    (Q/'fused/generate.py').as_posix(): 'b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b',
    (Q/'fused/phased/candidate.py').as_posix(): '2b487c60b53e25dbc04eba4c2eac4bd175e1573837863194de463d6a27df2399',
    (Q/'fused/phased/tail/candidate.py').as_posix(): '3a75e09640fdf789c11cf8a9050cd716ca3fde12732cb500f3f123adb0b50697',
}
FUNCTIONS = {'q288_tail_vdot': 'q288_ws_vdot', 'q288_fused_rvv4': 'q288_ws_rvv4'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate(body, before, after):
    replacements = {
        '  vlse32.v v12, (a4), t3\n': '  vle32.v v12, (a4)\n',
        '  addi a4, a4, 4\n': '  addi a4, a4, 32\n',
        '  addi a4, a4, 252\n': '  addi a4, a4, 0\n',
    }
    for old, new in replacements.items():
        need(body.count(old) == 1, 'unique bounded scale instruction: '+old.strip())
        body = body.replace(old, new)
    need(body.count('  li t3, 36\n') == 1, 'preserve unused setup for equal instruction count')
    body = body.replace(before, after)
    # Local labels must also be distinct when all baselines coexist in one ELF.
    label = 'tail' if before == 'q288_tail_vdot' else 'rvv4'
    body = body.replace('.Ltile_'+label, '.Ltile_ws_'+label)
    body = body.replace('.Lgroup_'+label, '.Lgroup_ws_'+label)
    return body


def generate(repo, output):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    need(not output.exists() and not output.is_relative_to(repo), 'fresh output outside the repository')
    for relative, expected in PINS.items():
        need(sha((repo/relative).read_bytes()) == expected, 'frozen source: '+relative)
    tail = load('ws_fixed_tail_generator', repo/Q/'fused/phased/tail/candidate.py')
    fused = load('ws_fixed_fused_generator', repo/Q/'fused/generate.py')
    public = (repo/'team/optimizations/o2/r2-config-reuse/public/gemv.S').read_text()
    with tempfile.TemporaryDirectory(prefix='q288-ws-fixed-') as temp:
        original = Path(temp)/'tail'
        tail.generate(repo, original)
        old = (original/'tail.S').read_text()
    marker = '.balign 64\n.global q288_tail_vdot\n'
    need(old.count(marker) == 1, 'one original TA function')
    ta_body = old[old.index(marker):]
    fr_body = fused.function(public, 'rvv4')
    assembly = old + fr_body
    assembly += candidate(ta_body, 'q288_tail_vdot', 'q288_ws_vdot')
    assembly += candidate(fr_body, 'q288_fused_rvv4', 'q288_ws_rvv4')
    output.mkdir(parents=True)
    (output/'q288-ws.S').write_text(assembly, encoding='utf-8')
    result = dict(contract=CONTRACT, source_sha256=sha(assembly.encode()), source_pins=PINS,
                  functions=FUNCTIONS, candidate_machine_words_changed_per_function=3,
                  source_scale_bytes=10368, packed_scale_bytes=10368, extra_scale_storage_bytes=10368,
                  old_abi_changed=False, hardware_changed=False, target_runtime_qualified=False,
                  performance_qualified=False)
    (output/'generation.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.repo, args.output), indent=2))
