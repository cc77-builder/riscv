"""Strict v5 functional/retirement gate; partial coverage is a separate result."""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_suite as suite
import diagnose_kills
import run_supplements
generate=suite.load_module('partial_v5_generate',Path(__file__).with_name('generate.py'))
workload=suite.load_module('partial_uart_check',Path(__file__).resolve().parents[1]/'workloads/check.py')


def validate_layout(symbols, disassembly):
    table={p[2]:int(p[0],16) for line in symbols.splitlines() if len(p:=line.split())==3}
    labels=['partial_div','partial_producer','partial_sibling','partial_old','partial_extract','partial_branch','partial_young']
    suite.require(all(x in table for x in labels+['partial_0','partial_0_end']), 'missing dependency symbol')
    base=table[labels[0]]
    suite.require([table[x]-base for x in labels]==[0,4,8,12,16,20,24], 'dependency instruction layout differs')
    rows={int(m[1],16):(int(m[2],16),m[3].strip()) for m in
          re.finditer(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+([^\n]+)',disassembly,re.M)}
    for label,word in [('partial_div',0x8284a9d7),('partial_extract',0x433023d7)]:
        suite.require(table[label] in rows and rows[table[label]][0]==word,
                      'compiled dependency encoding differs: '+label)
    for label,pattern in [('partial_div',r'vdivu\.vv\s+v19,\s*v8,\s*v9'),
                          ('partial_extract',r'vmv\.x\.s\s+t2,\s*v19'),
                          ('partial_branch',r'bne\s+t2,\s*t3,\s*[0-9a-f]+(?:\s+.*)?')]:
        suite.require(table[label] in rows and re.fullmatch(pattern,rows[table[label]][1]) is not None,
                      'compiled dependency differs: '+label)
    # The branch must skip exactly eight speculative VDOTs, not a subset.
    branch=rows[table['partial_branch']][0]
    offset=((branch>>31)<<12)|(((branch>>7)&1)<<11)|(((branch>>25)&63)<<5)|(((branch>>8)&15)<<1)
    if offset & 4096:offset-=8192
    suite.require(branch&0x01fff07f==0x01c39063 and table['partial_branch']+offset==table['partial_young']+32,
                  'branch target does not skip the whole younger block')
    sites={table['partial_producer']:generate.model.word(17,19,9),
           table['partial_sibling']:generate.model.word(18,17,9),
           table['partial_old']:generate.model.word(16,17,9)}
    sites.update({table['partial_young']+4*i:generate.model.word(reg,17,9) for i,reg in enumerate(range(20,28))})
    actual={pc:word for pc,(word,_) in rows.items() if table['partial_0']<=pc<table['partial_0_end'] and word&127==11}
    suite.require(actual==sites,'compiled VDOT PCs/operands differ')
    return table,sites


def check(raw,exit_code,manifest,reference,symbols,disassembly):
    suite.require(type(exit_code) is int and exit_code==0,'nonzero/invalid emulator exit')
    suite.require(manifest==generate.corpus()[1],'not the canonical dependency-admission v5 corpus')
    table,sites=validate_layout(symbols,disassembly)
    text=raw.decode('utf-8')
    workload.reject_fatal_output(text)
    suite.validate_failure_markers(text)
    suite.validate_runtime(text,reference)
    run_supplements.validate_seed_log(text,1)
    diagnosis=diagnose_kills.diagnose(raw)
    events,uart=diagnose_kills.analyze.extract_events_and_uart(text)
    for _,_,kind,fields in events:
        if kind=='ENQUEUE':
            suite.require(sites.get(fields['pc'])==fields['word'],'trace PC/word differs from compiled corpus')
    uart=uart.replace('\r\n','\n')
    suite.require('PARTIAL_V5_FAIL' not in uart,'directed software failure')
    markers=['PARTIAL_V5_BEGIN groups=1 trials=16']
    markers += [f'PARTIAL_V5_GROUP_PASS id={i} trials=16 register_bytes=8192 csr_fields=5' for i in range(1)]
    markers += ['PARTIAL_V5_SUMMARY groups=1 trials=16 register_bytes=8192 failures=0']
    actual=re.findall(r'^PARTIAL_V5_[^\r\n]*',uart,re.M)
    suite.require(actual==markers,'missing/reordered/extra directed marker')
    for marker in markers:workload.marker_position(uart,marker)
    suite.require(uart.count('HIT GOOD TRAP')==1 and uart.index('HIT GOOD TRAP')>uart.index(markers[-1]),'missing final good trap')
    suite.require(diagnosis['counts'].get('COMMIT')==manifest['expected_vdot_commits'],'retirement count differs')
    partial=[w for w in diagnosis['windows'] if w['classification']=='partial_kill']
    for window in partial:
        suite.require(window['survivor_committed'] and not window['victim_committed'],
                      'partial window lacks survivor retirement/victim cancellation')
    target=[]
    for window in partial:
        survivor=window['r' if window['killp'] else 'p']
        victim=window['p' if window['killp'] else 'r']
        young_pcs={table['partial_young']+4*i for i in range(8)}
        if int(survivor['pc'],16)==table['partial_old'] and int(victim['pc'],16) in young_pcs:
            target.append(window)
    return dict(status='PARTIAL_V5_TARGET_PASS' if target else 'PARTIAL_V5_FUNCTIONAL_PASS_COVERAGE_MISSING',
                architectural_pass=True,target_covered=bool(target),partial_windows=len(partial),target_windows=len(target),
                checked_register_bytes=8192,counts=diagnosis['counts'],diagnosis=diagnosis,
                campaign_acceptance=False,performance_measured=False)
