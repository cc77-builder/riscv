"""Affected exact-PC delta controls only; original suite stays preserved."""
from pathlib import Path
import hashlib, importlib.util, json, sys, time, traceback
HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    assert Path(m.__file__).resolve()==path.resolve()
    return m

a=load('b4_c48_exact_pc_current',HERE/'adapter.py')
sys.modules['b4_c48_host_r1_adapter']=a
f=load('b4_c48_exact_pc_fixture',HERE.parent/'host-r1/fixtures.py')
TESTS=[]
def check(name,fn,reject=False):
    try:fn()
    except ValueError as error:
        if not reject:raise
        diagnostic=str(error)
    else:
        if reject:raise AssertionError('missing rejection '+name)
        diagnostic=None
    TESTS.append(dict(name=name,status='PASS',diagnostic=diagnostic));print('PASS',name,flush=True)

def invoke(text):return a.negative(text,a.CASE_ID,'candidate',a.FAKE_REFERENCE,1,'b4-exact-pc-host','HOST_FIXTURE')
def main():
    start=time.monotonic();out=HERE/'attempt-01';out.mkdir(exist_ok=False)
    try:
        for pin in json.loads((HERE/'SOURCE_FREEZE.json').read_text())['files']:a.check_pin(pin)
        check('unchanged_normal_descriptor_compare_function_identity',lambda:a.need(a.collect is a.base.collect and a.compare is a.base.compare and a.descriptor is a.base.descriptor,'base functions identical'))
        check('original_first_custom_negative_still_valid',lambda:invoke(f.negative()))
        text=f.negative(True)
        check('exact_neighbor_load_group_valid',lambda:invoke(text))
        meta=json.loads((HERE/'FIXTURE_METADATA.json').read_text());other=int(meta['different_real_ELF_pc'],0)
        bad=text.replace('commit group [10]: pc 0080000d60 cmtcnt 2 <--',f'commit group [10]: pc {other:010x} cmtcnt 2 <--')
        bad=bad.replace('the first commit instr pc of DUT is 0x0000000080000d60',f'the first commit instr pc of DUT is {other:#018x}')
        bad=bad.replace('the first commit instr pc of REF is 0x0000000080000d60',f'the first commit instr pc of REF is {other:#018x}')
        bad=bad.replace('[18] commit pc 0000000080000d60 inst 020f8987',f'[18] commit pc {other:016x} inst 020f8987')
        bad=bad.replace('v0_high different at pc = 0x0080000d60',f'v0_high different at pc = {other:#x}')
        assert bad!=text
        # The inherited full-word/ELF gate accepts this synthetic alternate site;
        # the new neighborhood-PC gate must reject it. Neither is target evidence.
        check('baseline_word_only_gap_exercised_host_only',lambda:a.base.negative(bad,a.CASE_ID,'candidate',a.FAKE_REFERENCE,1,'b4-old-gap-host','HOST_FIXTURE'))
        check('alternate_real_ELF_site_same_word_rejected',lambda:invoke(bad),True)
        check('wrong_neighbor_instruction_still_rejected',lambda:invoke(text.replace('inst 020f8987','inst 020f8007')),True)
        result=dict(status='PASS_C48_EXACT_PC_DELTA',executed_controls=len(TESTS),tests=TESTS,wall_seconds=time.monotonic()-start,target_runs=0,native_loads=0,old27_controls_reused_with_normal_function_identity=True,source_freeze_sha256=hashlib.sha256((HERE/'SOURCE_FREEZE.json').read_bytes()).hexdigest())
        (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    except BaseException as error:
        (out/'RESULT.json').write_text(json.dumps(dict(status='FAIL_C48_EXACT_PC_DELTA',tests=TESTS,error=repr(error),traceback=traceback.format_exc(),target_runs=0),indent=2)+'\n');raise
if __name__=='__main__':main()
