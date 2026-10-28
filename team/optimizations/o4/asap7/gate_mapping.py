"""Bind generated ClockGate behavior to the selected Liberty state table."""
import hashlib
import itertools
import re

def mapping(platform, library, original, output):
    cell, clock, enable, q = ('CLKGATETST_X1', 'CK', 'E', 'GCK') if platform == 'nangate45' else ('ICGx1_ASAP7_75t_R', 'CLK', 'ENA', 'GCLK')
    if not re.search(r'if\s*\(!CK\).*?EN\s*=\s*TE\s*\|\s*E', original, re.S) or not re.search(r'assign\s+Q\s*=\s*CK\s*&\s*EN', original):
        raise ValueError('unrecognized generated ClockGate semantics')
    match = re.search(r'\bcell\s*\(\s*'+cell+r'\s*\)\s*\{', library)
    if not match: raise ValueError('missing clock gate')
    end = match.end(); depth = 1
    while depth:
        depth += (library[end] == '{') - (library[end] == '}'); end += 1
    body = library[match.start():end]
    tab = re.search(r'statetable\s*\("'+clock+' '+enable+r' SE",\s*"IQ"\).*?table\s*:\s*"([^"]+)"',body,re.S)
    if not tab: raise ValueError('missing clock gate state table')
    rows = [tuple(x.strip() for x in row.split(':')) for row in tab[1].replace('\\','').split(',')]
    function = re.search(r'pin\s*\('+q+r'\).*?state_function\s*:\s*"([^"]+)"',body,re.S)[1]
    if function.replace(' ','').strip('()') not in ['IQ&'+clock,clock+'&IQ']: raise ValueError('gate output differs')
    transitions = []
    for ck,e,te,old in itertools.product([0,1],repeat=4):
        hits = [nxt for pins,prior,nxt in rows if (prior=='-' or (prior=='H')==bool(old)) and all(p=='-' or (p=='H')==bool(v) for p,v in zip(pins.split(),[ck,e,te]))]
        if len(hits)!=1: raise ValueError('ambiguous gate transition')
        actual = old if hits[0]=='N' else int(hits[0]=='H')
        expected = old if ck else e|te
        if actual!=expected: raise ValueError('gate state differs')
        transitions.append([ck,e,te,old,actual,ck&actual])
    output.write_text(f'module ClockGate(input TE, E, CK, output Q);\n  {cell} impl(.{clock}(CK), .{enable}(E), .SE(TE), .{q}(Q));\nendmodule\n')
    return {'cell':cell,'clock_pin':clock,'enable_pin':enable,'output_pin':q,'transitions':transitions,'state_function':function,'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'mapping_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'scope':'all 16 binary state transitions; not analog timing or full formal equivalence'}
