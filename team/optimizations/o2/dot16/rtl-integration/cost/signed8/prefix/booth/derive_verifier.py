#!/usr/bin/env python3
"""Keep the strict existing parser/FA proof and replace only its input arithmetic."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent/'prefix-pgroup-candidate-01/controller/verify_csa.py'
EXPECTED = 'e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de'

PROOF = r'''
def prove(raw):
    declarations, assignments = Parser(raw.decode('ascii')).module()
    roots, controls, cells, weights, levels, dependencies = set(), set(), {}, {}, {}, {}
    bit = lambda n, i: ('bit', n, i)
    leaf = lambda n: ('leaf', n)
    unary = lambda a: ('~', a)
    both = lambda a, b: ('&', a, b)
    either = lambda a, b: ('|', a, b)
    exclusive = lambda a, b: ('^', a, b)
    for lane in range(8):
        for group in range(4):
            low = leaf(ZERO) if group == 0 else bit('vs2', 8*lane+2*group-1)
            mid = bit('vs2', 8*lane+2*group)
            high = bit('vs2', 8*lane+2*group+1)
            one, two, neg = [f'{kind}_{lane}_{group}' for kind in ('one','two','neg')]
            expected = {
                one: exclusive(low,mid),
                two: either(both(both(unary(high),mid),low), both(both(high,unary(mid)),unary(low))),
                neg: high,
            }
            for name, expression in expected.items():
                need(assignments.get(name) == expression, 'exact Booth control expression: '+name)
                controls.add(name); dependencies[name] = set(); levels[name] = -2
            # The neg signal is also one arithmetic correction token. Its use by
            # PP Boolean expressions is not a second weighted arithmetic token.
            roots.add(neg); weights[neg] = 2*group
            for i in range(9):
                name = f'pp_{lane}_{group}_{i}'
                a = bit('vs1', 8*lane+min(i,7))
                twice_a = leaf(ZERO) if i == 0 else bit('vs1', 8*lane+i-1)
                q = exclusive(either(both(leaf(one),a),both(leaf(two),twice_a)),leaf(neg))
                expected = unary(q) if i == 8 else q
                need(assignments.get(name) == expected, 'exact Booth row bit/lane/sign: '+name)
                roots.add(name); weights[name] = 2*group+i; levels[name] = -1
                dependencies[name] = {one,two,neg}
    for name in declarations - roots - controls:
        match = CELL.fullmatch(name)
        need(match is not None, 'unrecognized internal wire: '+name)
        kind, level, column, number = match.groups()
        key = int(level), int(column), int(number)
        need(key[1] < 20, 'compressor source column outside the 20-bit heap')
        cells.setdefault(key,{})[kind] = name; levels[name] = key[0]
    need(declarations == roots | controls | {n for pair in cells.values() for n in pair.values()},
         'complete closed recoder/PP/compressor declaration coverage')

    def evaluate_input(node, values, a, b):
        if node[0] == 'bit':
            return ((a if node[1] == 'vs1' else b) >> node[2]) & 1
        if node[0] == 'leaf':
            return 0 if node[1] == ZERO else 1 if node[1] == ONE else values[node[1]]
        left = evaluate_input(node[1],values,a,b)
        if node[0] == '~': return left ^ 1
        right = evaluate_input(node[2],values,a,b)
        return {'&':left & right, '^':left ^ right, '|':left | right}[node[0]]

    # Every lane was bound above to the same exact equations with a disjoint
    # byte-index substitution. For each group, enumerate all relevant actual
    # multiplier bits and all 256 values of its multiplicand. Group0 fixes b[-1]=0.
    recode_cases = 0
    for group in range(4):
        triples = range(0,8,2) if group == 0 else range(8)
        for a_bits in range(256):
            a_signed = a_bits if a_bits < 128 else a_bits-256
            for triple in triples:
                b_bits = triple >> 1 if group == 0 else triple << (2*group-1)
                values = {}
                for kind in ('one','two','neg'):
                    name = f'{kind}_0_{group}'
                    values[name] = evaluate_input(assignments[name],values,a_bits,b_bits)
                row = sum(evaluate_input(assignments[f'pp_0_{group}_{i}'],values,a_bits,b_bits) << i
                          for i in range(9))
                neg = values[f'neg_0_{group}']
                digit = (values[f'one_0_{group}'] + 2*values[f'two_0_{group}'])*(1-2*neg)
                need(row+neg == a_signed*digit+256, 'actual 9-bit recode plus independent carry identity')
                recode_cases += 1
    decomposition_cases = 0
    for b in range(256):
        digits = []
        for group in range(4):
            low = 0 if group == 0 else (b >> (2*group-1)) & 1
            mid, high = (b >> (2*group)) & 1, (b >> (2*group+1)) & 1
            digit = low + mid - 2*high
            digits.append(digit)
        need(sum(d << (2*g) for g,d in enumerate(digits)) == (b if b < 128 else b-256),
             'full signed-byte radix4 decomposition including top sign group')
        # This expression is independently checked against each actual recode's
        # one/two/neg equations for the eight possible triples below.
        decomposition_cases += 1
    for low,mid,high in itertools.product((0,1),repeat=3):
        one = low ^ mid
        two = ((1-high)&mid&low) | (high&(1-mid)&(1-low))
        need((one+2*two)*(1-2*high) == low+mid-2*high,'Booth digit truth table')

    inputs, kinds = {}, Counter()
    for key,pair in cells.items():
        need(set(pair)=={'s','c'},'unpaired compressor: '+str(key))
        s,c = assignments[pair['s']],assignments[pair['c']]
        terms = xor_inputs(s)
        need(len(terms) in (2,3) and len(set(terms))==len(terms),'FA/HA distinct arithmetic slots')
        need(boolean_leaves(c)==set(terms),'compressor Boolean input mismatch')
        for bits in itertools.product((0,1),repeat=len(terms)):
            values = dict(zip(terms,bits))
            need(sum(bits)==evaluate(s,values)+2*evaluate(c,values),'FA/HA full truth table')
        inputs[key]=terms; kinds['FA' if len(terms)==3 else 'HA']+=1
        for name in pair.values(): dependencies[name]=set(terms)-{ONE}
    dag_check(dependencies)
    uses,constants = Counter(),Counter()
    for key in sorted(cells):
        level,column,_ = key
        for term in inputs[key]:
            if term == ONE: constants[column]+=1
            else:
                need(term in weights and levels[term]<level,'only earlier arithmetic inputs: '+term)
                need(weights[term]==column,'compressor arithmetic weight: '+term)
                uses[term]+=1
        weights[cells[key]['s']]=column; weights[cells[key]['c']]=column+1
    rows={}
    for name in ('row0','row1'):
        concat=assignments[name]
        need(concat[0]=='concat' and len(concat)==21,'explicit complete 20-bit output concat')
        rows[name]=[]
        for column,expression in zip(range(19,-1,-1),concat[1:]):
            need(expression[0]=='leaf','output must be scalar arithmetic atom')
            term=expression[1];rows[name].append(term)
            if term==ZERO:continue
            if term==ONE:constants[column]+=1
            else:
                need(term in weights and weights[term]==column,'final output arithmetic weight')
                uses[term]+=1
    expected_constants=Counter({18:1,16:1,14:1,12:1,11:1})
    need(constants==expected_constants,'exact fixed Booth heap bias correction tokens')
    dropped=[]
    arithmetic_names=roots | {n for pair in cells.values() for n in pair.values()}
    for name in sorted(arithmetic_names):
        if uses[name]==0 and name.startswith('c_') and weights[name]>=20:dropped.append(name)
        else:need(uses[name]==1,f'exactly one weighted destination: {name} got {uses[name]}')
    per_lane_bias=256*sum(1<<(2*g) for g in range(4))
    correction=sum(count*(1<<column) for column,count in constants.items())
    need(per_lane_bias==21760 and 8*per_lane_bias+correction==1<<19,'complete bias identity')
    minimum,maximum=8*(-128*127),8*(-128*-128)
    need(-(1<<18)<=minimum<=maximum<(1<<18),'dot8 signed19 range')
    need(-(1<<19)<=2*minimum<=2*maximum<(1<<19),'dot16 signed20 range')
    return dict(status='BOOTH_CSA_STRUCTURAL_EQUIVALENCE_PASS',all_inputs_equivalent=True,
        combinational_identity_proved=True,parsed_entire_module=True,module='VDotCarrySaveRows',
        proof_domain='All 2^128 binary operand assignments by exact recode truth tables, signed-byte decomposition and weighted FA/HA conservation. No X/Z claim.',
        scalar_wires=len(declarations),booth_partial_product_bits=288,independent_neg_tokens=32,
        recode_controls=96,actual_recode_cases=recode_cases,signed_byte_decomposition_cases=decomposition_cases,
        full_adders=kinds['FA'],half_adders=kinds['HA'],local_boolean_cases=8*kinds['FA']+4*kinds['HA'],
        layers=sorted({key[0] for key in cells}),all_internal_nodes_acyclic=True,only_earlier_layer_inputs=True,
        arithmetic_destinations='Each recoded pp/neg/s/c weighted token used once; only carry of weight>=20 may be discarded modulo 2^20.',
        discarded_carries=dropped,correction_tokens_by_bit={str(k):constants[k] for k in sorted(constants)},
        per_lane_complement_bias=per_lane_bias,total_correction=correction,
        heap_identity='(row0+row1) mod 2^20 = (signed_dot8+2^19) mod 2^20',
        result_identity='signed19(low19(row0+row1))=signed_dot8; two biased halves sum modulo2^20 to signed_dot16',
        disabled_high_half_sum=1<<19,exact_signed_dot8_range=[minimum,maximum],
        rows_msb_to_lsb=rows,wrapper_binding_verified=False,sequential_fu_qualified=False,
        real_parent_qualified=False,full_core_qualified=False,application_qualified=False,performance_qualified=False,
        mapped_equivalence_proved=False,
        required_external_binding=['Actual SV SHA and one/two instance count.',
            'Operand byte halves, full20 P saves for feature1 or low19 saves for feature0.',
            'Dot8 disabled high half encodes 2^19, saved on acceptance.',
            'Unsigned R19/R20 modular prefix and unchanged architectural sign/zero extension.'])

'''


def main():
    raw=OLD.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==EXPECTED
    text=raw.decode()
    first=text[:text.index('def prove(raw):')]
    first=first.replace('scalar\npartial products, paired FA/HA equations, and two explicit 19-bit concatenations.',
        'scalar\nBooth recodes, paired FA/HA equations, and two explicit 20-bit concatenations.')
    first=first.replace("PP = re.compile(r'pp_([0-7])_([0-7])_([0-7])\\Z')\n",'')
    first=first.replace('output wire [18:0] row0, output wire [18:0] row1','output wire [19:0] row0, output wire [19:0] row1')
    tail=text[text.index('def main():'):]
    tail=tail.replace('CSA_STRUCTURAL_EQUIVALENCE_REJECTED','BOOTH_CSA_STRUCTURAL_EQUIVALENCE_REJECTED')
    result=first+PROOF+tail
    out=ROOT/'controller';out.mkdir(exist_ok=True)
    (out/'verify_booth.py').write_bytes(result.encode())
    print(json.dumps(dict(bytes=len(result.encode()),sha256=hashlib.sha256(result.encode()).hexdigest(),
        base_verifier_sha256=EXPECTED,scope='Strict parser and local Boolean FA/HA helpers retained; all Booth arithmetic separately proved.')))


if __name__=='__main__': main()
