"""Explicit synthetic HOST fixtures plus unmodified frozen historical bytes."""
from pathlib import Path
import importlib.util, re, sys
import adapter as a
sys.modules['analyze'] = a.native.sp1
spec = importlib.util.spec_from_file_location('b4_c48_original_synthetic_fixture', Path(a.CONTRACT['native_adapter']['path']).parent / 'frozen_host/fixtures.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)

def history(index):
    h = a.CASE['history_budget_facts'][index]
    raw = {key:a.check_pin(h[key]).decode() for key in ('stdout', 'stderr')}
    return raw['stdout'] + '\n' + raw['stderr'], h

def set_first(fixture, rob):
    fixture.entries[rob]['pc'] = 0x80000d64
    fixture.rows[-1] = re.sub(r'pc=0x[0-9a-f]+', 'pc=0x80000d64', fixture.rows[-1])
    fixture.rows[-1] = re.sub(r'word=0x[0-9a-f]+', 'word=0x0388000b', fixture.rows[-1])

def normal():
    fixture = f.Fixture()
    for i in range(1008):
        rob = f'{(i // 48) % 2}:{i % 48}'
        fixture.enqueue(rob, pdest=1, vd=0)
        set_first(fixture, rob)
        fixture.tick(rob)
        fixture.drain()
    m = a.native.case_manifest(a.CASE)
    text = 'HOST_SYNTHETIC_C48_CHECKER_ONLY_NOT_TARGET\n'
    text += 'The image is ' + a.CASE['artifacts']['bin']['path'] + '\n'
    text += 'The reference model is ' + a.FAKE_REFERENCE + '\n'
    text += 'The first instruction of core 0 has commited. Difftest enabled.\n'
    text += f"R4C_BEGIN cases=48 contract={m['contract']}\nR4C_CONTROLS detected=5 expected=5\n"
    text += ''.join(f"R4C_CASE seq={i} hash={c['expected_hash']}\n" for i,c in enumerate(m['cases']))
    text += 'R4C_END executed=48 failures=0\nHIT GOOD TRAP\nGuest cycle spent: 871326\n'
    return text + fixture.text()

def negative(include_load=False):
    h = a.CASE['history_budget_facts'][0]
    stdout = a.check_pin(h['stdout']).decode()
    stderr = a.check_pin(h['stderr']).decode()
    operands = re.search(r'O2_ACCEPT[^\n]*seq=\s*0 [^\n]*vs1=(0x[0-9a-f]+) vs2=(0x[0-9a-f]+)', stderr)
    assert operands is not None
    vs1,vs2 = [int(x,16) for x in operands.groups()]
    class FixedOperands(f.Fixture):
        def request(self, rob, illegal=0, vl=8, **kwargs):
            return super().request(rob, illegal, vl, vs1=vs1, vs2=vs2)
    fixture = FixedOperands()
    fixture.enqueue('1:3', pdest=1, vd=0)
    set_first(fixture, '1:3')
    fixture.tick('1:3');fixture.drain()
    assert a.native.sp1.dot_result(vs1,vs2) == 0x7ec2
    stdout = re.sub(r'The image is [^\r\n]+', 'The image is ' + a.CASE['artifacts']['bin']['path'], stdout)
    stdout = re.sub(r'The reference model is [^\r\n]+', 'The reference model is ' + a.FAKE_REFERENCE, stdout)
    if include_load:
        for old,new in [('commit group [10]: pc 0080000d64 cmtcnt 1 <--','commit group [10]: pc 0080000d60 cmtcnt 2 <--'),
                        ('the first commit instr pc of DUT is 0x0000000080000d64','the first commit instr pc of DUT is 0x0000000080000d60'),
                        ('the first commit instr pc of REF is 0x0000000080000d64','the first commit instr pc of REF is 0x0000000080000d60'),
                        ('v0_high different at pc = 0x0080000d64','v0_high different at pc = 0x0080000d60')]:
            assert stdout.count(old) == 1, old
            stdout = stdout.replace(old,new)
    return 'HOST_SYNTHETIC_C48_CURRENT_GROUP_NOT_TARGET\n' + stdout + '\n' + fixture.text() + 'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=0 pc=0x80000d64 instruction=0x0388000b\n'
