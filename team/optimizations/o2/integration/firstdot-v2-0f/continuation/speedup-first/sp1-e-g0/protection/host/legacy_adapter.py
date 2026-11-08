"""Compatibility adapter for immutable old images, without claiming new runtime evidence."""
import re,hashlib
import protection as p
import legacy_workload as uart_gate

def check(text,manifest,exit_code,mode,kind,reference):
 p.need(mode in ('baseline','candidate') and kind in ('control','diagnostic','control-diagnostic'),'explicit schema/case')
 text=p.failure.normalize_console(text);p.failure.validate_failure_markers(text);uart_gate.reject_fatal_output(text)
 p.need(exit_code==0,'normal exit code')
 p.need(text.count('The first instruction of core 0 has commited. Difftest enabled.')==1,'one live DiffTest banner')
 p.need(re.findall(r'The reference model is ([^\r\n]+)',text)==[reference],'exact reference model')
 obs=p.sp1 if mode=='candidate' else p.o2
 a=obs.analyze(text);events,uart=obs.extract_events_and_uart(text)
 p.need(a['status']==('SP1_TRACE_PASS' if mode=='candidate' else 'O2_TRACE_PASS'),'complete correct schema')
 p.need(a['input_sha256']==hashlib.sha256(text.encode()).hexdigest(),'analysis raw binding')
 p.need(a['pending_count']==a['pending_div_count']==a['unfinished_rob_count']==0,'all queues/ROB drain')
 if kind=='control':
  begin='T12_BEGIN seed=0x20261014 contract=vdot-s8x8-r32-v0.1'
  summary='T12_SUMMARY groups=4 checkpoints=128 speculative_attempts=256 failures=0'
  markers=[begin]+[f'T12_GROUP_PASS id={i} checkpoints=32 bytes=16384' for i in range(4)]+[summary]
  positions=[uart_gate.marker_position(uart,x) for x in markers]
  p.need(positions==sorted(positions),'T12 canonical marker order')
  p.need(uart.count('T12_BEGIN')==1 and uart.count('T12_GROUP_PASS')==4 and uart.count('T12_SUMMARY')==1,'T12 extra markers')
  p.need(uart.count('HIT GOOD TRAP')==1 and uart.index('HIT GOOD TRAP')>positions[-1],'T12 final trap')
  expected=sum(x['vdot_count'] for x in manifest['groups'])+manifest['speculation']['expected_architectural_vdot']
  p.need(a['counts']['COMMIT']==expected,'T12 exact architectural dot count')
  p.need(all(t['illegal']==0 and t['vl']==8 for t in a['transactions']),'T12 VL/legal transactions')
  c=a['counts'];coverage=dict(accepted_younger_squashed=c.get('ACCEPTED_YOUNGER_SQUASHED',0)>0,inflight_fu_killed=c['KILL']>0,shared_vfex4_fu_kinds=len(a['vfex4_fu_counts'])>=2,shared_vfex4_backpressure=c['VFEX4_WAIT']>0,vdot_writeback_backpressure=c['STALL']>0,rob_wrap_repeated=c.get('ROB_WRAP',0)>=8,ftq_wrap_repeated=c.get('FTQ_WRAP',0)>=8)
  p.need(all(coverage.values()),'original seven control coverage obligations')
  work=dict(status='LEGACY_CONTROL_FUNCTIONAL_PASS',expected_vdot_commits=expected,checked_register_bytes=65536,legacy_coverage=coverage)
 else:
  # The unmodified UART helper knows only the legacy status spelling. It receives
  # a fresh local copy AFTER the actual SP1/O2 analyzer passed and bound raw SHA.
  # No cached analysis is accepted and the original observation status is retained.
  compatible=dict(a,status='O2_TRACE_PASS')
  work=(uart_gate.check if kind=='diagnostic' else uart_gate.check_control)(uart,manifest,exit_code,compatible)
 return dict(status='PROTECTION_LEGACY_FUNCTIONAL_PASS',kind=kind,mode=mode,observation_status=a['status'],observed_schema=a['schema'],counts=a['counts'],o2_coverage=a['o2_coverage'],vfex4_fu_counts=a['vfex4_fu_counts'],workload=work,raw_sha256=hashlib.sha256(text.encode()).hexdigest(),performance_measured=False,performance_2_percent_qualified=False,scope='full observer plus original workload gate; this function does not launch targets')
