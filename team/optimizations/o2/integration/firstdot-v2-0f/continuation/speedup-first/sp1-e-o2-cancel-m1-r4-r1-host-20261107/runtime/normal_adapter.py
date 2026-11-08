"""Read-only normal-log adapter; runtime identity/resource receipts remain separate."""
import re
from o2_cancel_selector import select, base, need

def expected_uart(contract):
    p=contract['uart_protocol']
    rows=[p['begin']]
    for c in contract['call_plan']:
        rows.append(f"OC19_CALL seq={c['seq']} phase={c['phase'] or 0} stage={c['stage']} probe={int(c['probe'])}")
        rows.append(f"OC19_PASS seq={c['seq']}")
    rows.append(p['summary'])
    return rows

def collect_normal(text,contract,exit_code,require_hit=False):
    need(exit_code==0,'normal target must exit zero')
    need(text.count('HIT GOOD TRAP')==1 and 'HIT BAD TRAP' not in text,'complete successful trap required')
    need('DIFFTEST_HIGHBIT_NEGATIVE_INJECTED' not in text and 'diff-test failed' not in text.lower(),'normal log contains failure or injection')
    _,uart=base.extract_events_and_uart(text)
    rows=re.findall(r'OC19_[^\r\n]*',uart)
    need(rows==expected_uart(contract),'complete ordered 41-call UART contract mismatch')
    result=select(text,contract,require_hit=require_hit)
    result.update(uart_calls=len(contract['call_plan']),uart_rows=len(rows),source='OFFLINE_LOG_ONLY_NEEDS_ACTUAL_EXECUTION_RECEIPTS',good_trap=True,normal_exit=exit_code)
    return result
