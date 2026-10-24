"""Strict v2 functional/retirement gate; partial coverage is a separate result."""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_suite as suite
import diagnose_kills
import run_supplements
generate=suite.load_module('partial_v2_generate',Path(__file__).with_name('generate.py'))
workload=suite.load_module('partial_uart_check',Path(__file__).resolve().parents[1]/'workloads/check.py')


def check(raw,exit_code,manifest,reference):
    suite.require(type(exit_code) is int and exit_code==0,'nonzero/invalid emulator exit')
    suite.require(manifest==generate.corpus()[1],'not the canonical directed v2 corpus')
    text=raw.decode('utf-8')
    workload.reject_fatal_output(text)
    suite.validate_failure_markers(text)
    suite.validate_runtime(text,reference)
    run_supplements.validate_seed_log(text,1)
    diagnosis=diagnose_kills.diagnose(raw)
    _,uart=diagnose_kills.analyze.extract_events_and_uart(text)
    uart=uart.replace('\r\n','\n')
    suite.require('PARTIAL_V2_FAIL' not in uart,'directed software failure')
    markers=['PARTIAL_V2_BEGIN groups=8 trials=128']
    markers += [f'PARTIAL_V2_GROUP_PASS id={i} trials=16 register_bytes=8192 csr_fields=5' for i in range(8)]
    markers += ['PARTIAL_V2_SUMMARY groups=8 trials=128 register_bytes=65536 failures=0']
    actual=re.findall(r'^PARTIAL_V2_[^\r\n]*',uart,re.M)
    suite.require(actual==markers,'missing/reordered/extra directed marker')
    for marker in markers:workload.marker_position(uart,marker)
    suite.require(uart.count('HIT GOOD TRAP')==1 and uart.index('HIT GOOD TRAP')>uart.index(markers[-1]),'missing final good trap')
    suite.require(diagnosis['counts'].get('COMMIT')==manifest['expected_vdot_commits'],'retirement count differs')
    partial=[w for w in diagnosis['windows'] if w['classification']=='partial_kill']
    for window in partial:
        suite.require(window['survivor_committed'] and not window['victim_committed'],
                      'partial window lacks survivor retirement/victim cancellation')
    return dict(status='PARTIAL_V2_TARGET_PASS' if partial else 'PARTIAL_V2_FUNCTIONAL_PASS_COVERAGE_MISSING',
                architectural_pass=True,target_covered=bool(partial),partial_windows=len(partial),
                checked_register_bytes=65536,counts=diagnosis['counts'],diagnosis=diagnosis,
                campaign_acceptance=False,performance_measured=False)
