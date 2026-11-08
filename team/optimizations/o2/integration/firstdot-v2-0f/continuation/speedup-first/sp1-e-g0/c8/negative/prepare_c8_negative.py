"""Build host interposers and test only against a fake, non-ISA library."""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import resource
import subprocess
import sys

P = Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first')
O = P / 'sp1-e-g0/c8/negative'
OLD = P / 'sp1-cd/checker'
CONFIG = {'c8-perf': (0x80002308, 0x0388000b), 'c8-functional': (0x80000d64, 0x0388000b)}

def pin(path):
    path = path.resolve()
    return {'path':str(path), 'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def command(argv, env=None):
    index = len(list((O/'host').glob('cmd-*.json')))
    prefix = O/'host'/f'cmd-{index:02d}'
    proc = subprocess.run(argv, env=env, capture_output=True,
                          preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)))
    prefix.with_suffix('.stdout').write_bytes(proc.stdout)
    prefix.with_suffix('.stderr').write_bytes(proc.stderr)
    save(prefix.with_suffix('.json'), {'argv':argv, 'returncode':proc.returncode,
                                      'scope':'HOST_ONLY_NO_NEMU_LOADED'})
    return proc

def stub_case(group, mode):
    # Strict path restriction: loading the production interposer is forbidden.
    fake = (O/'host/stub-reference.so').resolve()
    library = (O/'host'/f'{group}-stub.so').resolve()
    assert fake.is_relative_to(O/'host') and library.is_relative_to(O/'host')
    lib = ctypes.CDLL(str(library))
    stub = ctypes.CDLL(str(fake))
    stub.stub_setup.argtypes = [ctypes.c_uint64,ctypes.c_uint32]
    stub.stub_executions.restype = ctypes.c_uint64
    lib.difftest_exec.argtypes = [ctypes.c_uint64]
    lib.difftest_regcpy.argtypes = [ctypes.c_void_p,ctypes.c_bool]
    pc, word = CONFIG[group]
    count = 1
    if mode == 'wrong_pc': pc += 4
    if mode == 'wrong_word': word ^= 1<<15
    if mode == 'wrong_vd': word ^= 1<<7
    if mode == 'count2': count = 2
    a = (ctypes.c_ubyte*1400)()
    b = (ctypes.c_ubyte*1400)()
    stub.stub_setup(pc,word)
    stub.difftest_regcpy(b,False)
    original = bytes(b)
    lib.difftest_exec(count)
    if mode == 'clear_pending': lib.difftest_regcpy(a,True)
    lib.difftest_regcpy(a,False)
    want = mode in ('exact','once','original_unmodified')
    expected = bytearray(original)
    if want: expected[800+16*0+12] ^= 0x10
    if mode == 'clear_pending': expected = bytearray(1400)
    assert bytes(a) == bytes(expected), (group,mode)
    if mode == 'once':
        lib.difftest_exec(1)
        lib.difftest_regcpy(b,False)
        assert bytes(b) == original
    if mode == 'original_unmodified':
        stub.difftest_regcpy(b,False)
        assert bytes(b) == original
    assert stub.stub_executions() == count+(mode=='once')

def main():
    O.mkdir(exist_ok=True)
    (O/'host').mkdir(exist_ok=True)
    assert not (O/'RESULT.json').exists()
    reference = json.loads((P/'sp1-e-g0/COMMON_CONTRACT.json').read_text())['runtime']['normal_reference']
    assert pin(Path(reference['path'])) == reference
    cases = json.loads((P/'sp1-e-g0/c8/CASES.json').read_text())['cases']
    original = (OLD/'chain-bit100.c').read_text()
    for group,(pc,word) in CONFIG.items():
        matching = [c for c in cases if c['kind'] == ('performance' if group == 'c8-perf' else 'functional')]
        assert matching and all(c['negative_binding']=={'pc':hex(pc),'word':hex(word),'vd':0,'bit':100,'injection_count':1} for c in matching)
        text = original.replace('0x8000114c',f'0x{pc:08x}').replace('0x0295050b',f'0x{word:08x}').replace('TARGET_VD 10u','TARGET_VD 0u').replace('bit=100 vd=10','bit=100 vd=0')
        (O/f'{group}-bit100.c').write_text(text)
    (O/'stub-reference.c').write_bytes((OLD/'stub-reference.c').read_bytes())
    (O/'prepare_c8_negative.py').write_bytes(Path(__file__).read_bytes())
    save(O/'SOURCE_FREEZE.json', {'sources':[pin(q) for q in sorted(O.glob('*')) if q.suffix in ('.py','.c')],
                                 'template':pin(OLD/'chain-bit100.c'), 'normal_reference':reference,
                                 'loads_only_fake_library':True})
    fake = O/'host/stub-reference.so'
    proc=command(['/usr/bin/gcc','-shared','-fPIC','-O2',str(O/'stub-reference.c'),'-o',str(fake)])
    assert proc.returncode==0,proc.stderr
    products={}
    for group in CONFIG:
        products[group]={}
        for kind,ref in [('stub',str(fake)),('production',reference['path'])]:
            out=O/'host'/f'{group}-stub.so' if kind=='stub' else O/f'{group}-negative-reference.so'
            argv=['/usr/bin/gcc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',
                  f'-DREF_SO="{ref}"',str(O/f'{group}-bit100.c'),'-Wl,--no-as-needed',ref,'-ldl','-o',str(out)]
            proc=command(argv)
            assert proc.returncode==0,proc.stderr
            products[group][kind]=pin(out)
        proc=command(['/usr/bin/readelf','-d',products[group]['production']['path']])
        assert proc.returncode==0 and reference['path'].encode() in proc.stdout
    tests=[]
    modes=['exact','once','original_unmodified','wrong_pc','wrong_word','wrong_vd','count2','clear_pending']
    for group in CONFIG:
        for mode in modes+['env_missing','env_wrong']:
            env=dict(os.environ)
            env.pop('SP1_CHAIN_BIT100',None)
            if mode!='env_missing':env['SP1_CHAIN_BIT100']='0' if mode=='env_wrong' else '1'
            proc=command(['/usr/bin/python3','-B',str(O/'prepare_c8_negative.py'),'stub',group,mode],env)
            if mode.startswith('env_'):
                assert proc.returncode!=0 and b'NEGATIVE_FIXTURE_SETUP_FAIL' in proc.stderr
            else:
                assert proc.returncode==0,(group,mode,proc.stderr)
                assert proc.stderr.count(b'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED')==int(mode in ('exact','once','original_unmodified'))
                if mode in ('exact','once','original_unmodified'):
                    pc,word=CONFIG[group]
                    assert f'pc=0x{pc:08x} instruction=0x{word:08x}'.encode() in proc.stderr
            tests.append({'group':group,'case':mode,'status':'PASS','scope':'FAKE_HOST_ABI_ONLY'})
    for q in json.loads((O/'SOURCE_FREEZE.json').read_text())['sources']:
        assert pin(Path(q['path']))==q
    assert pin(Path(reference['path']))==reference
    result={'status':'HOST_NEGATIVE_FIXTURES_PASS','scope':'Compile production wrappers, load fake variants only; no NEMU/EMU execution or loading',
            'products':products, 'tests':tests, 'host_checks':len(tests),
            'normal_reference':reference, 'new_NEMU_builds':0, 'new_target_executions':0,
            'production_wrappers_loaded':False,
            'bindings':{k:{'pc':pc,'word':word,'vd':0,'bit':100,'count':1,'environment':{'SP1_CHAIN_BIT100':'1'}} for k,(pc,word) in CONFIG.items()},
            'target_qualification':'NOT_TESTED, fresh exact target rejection mandatory in each future campaign'}
    save(O/'RESULT.json',result)
    (O/'RESULT.md').write_text('# C8 bit100 host fixtures\n\nHOST PASS: 20 fake-library ABI controls. Two production wrappers were compiled and statically inspected, never loaded. Both C8 PC bindings are distinct from the chain wrapper. No NEMU/EMU run; actual target rejection remains NOT_TESTED.\n')
    save(O/'MANIFEST.json',{'files':[pin(q) for q in sorted(O.rglob('*')) if q.is_file()]})
    print('HOST_NEGATIVE_FIXTURES_PASS',len(tests))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='stub':stub_case(sys.argv[2],sys.argv[3])
    else:main()
