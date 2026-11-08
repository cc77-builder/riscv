"""Focused B4 C48 delta controls. Pure Python/history only, fail first."""
from pathlib import Path
import copy, hashlib, json, re, time, traceback
import adapter as a
import fixtures
HERE = Path(__file__).resolve().parent
TESTS = []

def check(name, fn, reject=False):
    start = time.monotonic()
    try:
        value = fn()
    except (ValueError, AssertionError) as error:
        if not reject:
            raise
        value = {'expected_rejection': str(error)}
    else:
        if reject:
            raise AssertionError('missing rejection: ' + name)
    TESTS.append(dict(name=name, status='PASS', expected_rejection=reject, wall_seconds=time.monotonic()-start))
    print('PASS', name, flush=True)
    return value

def call(text, negative=False, mode='candidate', reference=a.FAKE_REFERENCE, scope='HOST_FIXTURE', code=None):
    return (a.negative if negative else a.collect)(text,a.CASE_ID,mode,reference,(1 if negative else 0) if code is None else code,'b4-host-fixture',scope)

def mutate_one(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old,new)

def main():
    start = time.monotonic()
    out = HERE / 'attempt-01'
    out.mkdir(exist_ok=False)
    try:
        for pin in json.loads((HERE/'SOURCE_FREEZE.json').read_text())['files']:
            a.check_pin(pin)
        check('exact_source_image_and_linked_48call_numeric_model',lambda:a.native.validate_static(a.CASE))
        desc=check('canonical_descriptor_and_no_target_authorization',lambda:a.descriptor())
        a.need(desc['case_id']=='original-c8-c48' and desc['coverage']['calls']==48 and desc['coverage']['custom_commits']==1008,'descriptor coverage')
        text=fixtures.normal();negative=fixtures.negative();negative_load=fixtures.negative(True)
        good=check('full_candidate_host_1008_and_48_calls',lambda:call(text))
        hist,h=fixtures.history(1)
        historical=check('complete_unmodified_historical_o2_log_only',lambda:call(hist,mode='baseline',reference=h['normal_reference_path'],scope='HISTORICAL_LOG'))
        a.need(historical['guest_cycles']==871326 and historical['target_run_qualified'] is False,'historical qualification boundary')
        check('exact_current_group_C48_bit100_host',lambda:call(negative,negative=True))
        check('preceding_exact_C48_vle8_group_host',lambda:call(negative_load,negative=True))
        check('missing_48th_call_rejected',lambda:call(text.replace('R4C_CASE seq=47','BROKEN seq=47')),True)
        check('changed_output_hash_rejected',lambda:call(text.replace('R4C_CASE seq=47 hash=','R4C_CASE seq=47 hash=1')),True)
        bad=re.sub(r'(SP1_RESPONSE[^\n]*?data=)(0x[0-9a-f]+)',lambda m:m[1]+hex(int(m[2],16)^(1<<100)),text,count=1)
        check('full128_high100_result_rejected',lambda:call(bad),True)
        check('frozen_ELF_custom_PC_rejected',lambda:call(text.replace('pc=0x80000d64','pc=0x80000d60')),True)
        check('wrong_image_banner_rejected',lambda:call(text.replace('The image is ','The image is /wrong/')),True)
        check('wrong_reference_rejected',lambda:call(text,reference=a.FAKE_REFERENCE+'wrong'),True)
        check('unsupported_scope_rejected',lambda:call(text,scope='HOST_FIXTURE_NOT_TARGET'),True)
        check('historical_ref_not_current_qualification',lambda:call(hist,mode='baseline',reference=h['normal_reference_path'],scope='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT'),True)
        check('missing_guest_count_rejected',lambda:call(text.replace('Guest cycle spent:','Guest missing:')),True)
        check('negative_exit0_rejected',lambda:call(negative,negative=True,code=0),True)
        check('wrong_injection_PC_rejected',lambda:call(negative.replace('vd=0 pc=0x80000d64 instruction=','vd=0 pc=0x80000d68 instruction='),negative=True),True)
        check('wrong_injection_vd_rejected',lambda:call(negative.replace('bit=100 vd=0 pc=','bit=100 vd=1 pc='),negative=True),True)
        check('wrong_load_ELF_footprint_rejected',lambda:call(negative_load.replace('inst 020f8987','inst 020f8007'),negative=True),True)
        check('group_head_mismatch_rejected',lambda:call(negative_load.replace('v0_high different at pc = 0x0080000d60','v0_high different at pc = 0x0080000d64'),negative=True),True)
        check('wrong_final_reference_low32_rejected',lambda:call(mutate_one(negative,'v0 : 0x0000000000000000_0000000000007ec2','v0 : 0x0000000000000000_0000000000007ec3'),negative=True),True)
        check('CSR_vstart_context_rejected',lambda:call(negative.replace('vstart: 0x0000000000000000','vstart: 0x0000000000000001'),negative=True),True)
        check('unknown_vector_footprint_rejected',lambda:a.c48_vector_destination(0x020f8007),True)
        check('actual_observed_functional_replay',lambda:a.compare(good,copy.deepcopy(good),True))
        b=copy.deepcopy(good);del b['application_uart_sha256']
        check('absent_UART_None_cannot_pass',lambda:a.compare(b,b,True),True)
        b=copy.deepcopy(good);b['guest_cycles']+=1
        check('same_hardware_guest_replay_mismatch',lambda:a.compare(good,b,True),True)
        b=copy.deepcopy(good);b['mode']='baseline';b['guest_cycles']+=1
        check('cross_hardware_guest_difference_not_new_gate',lambda:a.compare(b,good))
        receipt=dict(status='PASS_C48_HOST_ADAPTER',controls=len(TESTS),tests=TESTS,wall_seconds=time.monotonic()-start,
                     history={'guest_cycles':historical['guest_cycles'],'calls':historical['calls'],'custom_commits':historical['custom_commits']},
                     source_freeze_sha256=hashlib.sha256((HERE/'SOURCE_FREEZE.json').read_bytes()).hexdigest(),
                     target_runs=0,native_library_loads=0,builds=0,launch_enabled=False,target_admission='HOLD_PENDING_NEW_CALIBRATION_CONTRACT_AND_USER_AUTHORIZATION')
        for pin in json.loads((HERE/'SOURCE_FREEZE.json').read_text())['files']:a.check_pin(pin)
        (out/'RESULT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
        print('PASS_C48_HOST_ADAPTER',len(TESTS),flush=True)
    except BaseException as error:
        receipt=dict(status='FAIL_C48_HOST_ADAPTER',controls_completed=len(TESTS),tests=TESTS,error=repr(error),traceback=traceback.format_exc(),target_runs=0,native_library_loads=0,launch_enabled=False)
        (out/'RESULT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
        raise

if __name__=='__main__':main()
