"""Finite checks for the frozen prefix candidate in a newly generated real parent.

Only expression whitespace is compacted for closed arithmetic port matching.
No real RTL is rewritten, and there is no whole-RTL or sequential formal claim.
"""
import hashlib
import re


def need(ok, message):
    if not ok:
        raise ValueError(message)


def compact(value):
    return re.sub(r'\s+', '', value)


def assignments(text):
    return [(name, compact(expression)) for name, expression in
            re.findall(r'(?m)^\s*(\w+)\s*<=\s*(.*?);', text, re.S)]


def module_header(text):
    matches = re.findall(r'(?ms)^module VDotElastic\(.*?^\);', text)
    need(len(matches) == 1, 'one complete VDotElastic module interface')
    return matches[0]


def closed_ports(body, count):
    pairs = re.findall(r'\.(\w+)\s*\(([^()]*)\)', body)
    rest = re.sub(r'\.(\w+)\s*\(([^()]*)\)', '', body)
    need(not rest.replace(',', '').strip() and len(pairs) == count
         and len(dict(pairs)) == count, 'complete unique arithmetic instance ports')
    return {key: compact(value) for key, value in pairs}


def verify_dot16_mode(text):
    # Both declaration forms are present in existing generated RTL: module-level
    # wire in the cost boundary, automatic logic in the original parent block.
    declarations = re.findall(r'\b(?:wire|automatic\s+logic)\s+isDot16\s*=\s*(.*?);', text, re.S)
    writes = re.findall(r'\bisDot16\s*(?:<=|=(?!=))\s*(.*?);', text, re.S)
    expected = ["io_in_bits_ctrl_fuOpType==9'h1"]
    need([compact(value) for value in declarations] == expected
         and [compact(value) for value in writes] == expected,
         'unique dot16 predicate is the original fuOpType comparison')
    return expected[0]


def verify_data_binding(text, feature):
    need(feature in (0, 1), 'fixed feature0/feature1 only')
    width = 20 if feature else 19
    mode = verify_dot16_mode(text) if feature else None
    matches = re.findall(r'\bVDotCarrySaveRows\s+(\w+)\s*\((.*?)\);', text, re.S)
    instances = dict(matches)
    expected = {'products', 'highProducts'} if feature else {'products'}
    need(len(matches) == len(expected) and set(instances) == expected,
         'actual one/two unique CSA instances')
    for name, body in instances.items():
        hi, lo = (127, 64) if name == 'highProducts' else (63, 0)
        need(closed_ports(body, 4) == {
            'vs1': f'io_in_bits_data_src_0[{hi}:{lo}]',
            'vs2': f'io_in_bits_data_src_1[{hi}:{lo}]',
            'row0': f'_{name}_row0', 'row1': f'_{name}_row1'},
            'exact input halves and CSA row wires')
    need(not re.search(r'\b(?:VDotProducts|VDotReduce|VDotSignedByteProduct)\s+\w+\s*\(', text),
         'obsolete arithmetic instances are absent')
    pnames = [f'pRows_{half}_{row}' for half in range(2 if feature else 1) for row in range(2)]
    declarations = re.findall(r'\breg\s+\[(\d+):0\]\s+(pRows_\d+_\d+)\s*;', text)
    need(declarations == [('18', name) for name in pnames], 'complete 19-bit saved rows')
    need(re.findall(r'\breg\s+\[(\d+):0\]\s+rPacket_res_data\s*;', text) == [str(width-1)],
         'exact 19/20-bit R data register')
    need(not re.search(r'\bpProducts_\d+\b', text), 'old saved products are absent')
    updates = assignments(text)
    for half in range(2 if feature else 1):
        for row in range(2):
            name = f'pRows_{half}_{row}'
            expected_value = f"isDot16?_highProducts_row{row}:19'h0" if half else f'_products_row{row}'
            need([value for key, value in updates if key == name] == [expected_value],
                 'exact accepted P row and dot8 high-half zero')
    matches = re.findall(r'\b(VDotPrefixFinish\d+)\s+(\w+)\s*\((.*?)\);', text, re.S)
    need(len(matches) == 1 and matches[0][:2] == (f'VDotPrefixFinish{width}', 'prefixSum'),
         'one matching prefixSum instance')
    ports = closed_ports(matches[0][2], len(pnames)+1)
    expected_ports = {'result': '_prefixSum_result'}
    for index, name in enumerate(pnames):
        expected_ports[f'rows_{index}'] = '{'+name+'[18],'+name+'}' if feature else name
    need(ports == expected_ports, 'ordered saved rows with required sign extension')
    need(re.findall(r'\bwire\s+\[(\d+):0\]\s+_prefixSum_result\s*;', text) == [str(width-1)],
         'exact prefix result width')
    need([value for key, value in updates if key == 'rPacket_res_data'] ==
         [f"pCtrl_exceptionVec_2?{width}'h0:_prefixSum_result"],
         'exact illegal-zero or prefix-result R write')
    outputs = re.findall(r'\bassign\s+io_out_bits_res_data\s*=\s*(.*?);', text, re.S)
    need(len(outputs) == 1, 'single architectural output expression')
    output = compact(outputs[0])
    match = re.fullmatch(r"\{96'h0,([A-Za-z_][A-Za-z_0-9]*),rPacket_res_data\}", output)
    need(match is not None, 'zero high96 plus one explicit sign extension and saved R')
    sign_wire = match[1]
    sign_rows = re.findall(r'\bwire\s+\[(\d+):0\]\s+'+re.escape(sign_wire)+r'\s*=\s*(.*?);', text, re.S)
    sign_width = 32-width
    need([(size, compact(value)) for size, value in sign_rows] ==
         [(str(sign_width-1), '{'+str(sign_width)+'{rPacket_res_data['+str(width-1)+']}}')],
         'sign-extension wire repeats exactly the saved R sign bit')
    return dict(feature=feature, result_width=width, csa_instances=sorted(instances),
                p_row_registers=pnames, prefix_module=f'VDotPrefixFinish{width}',
                prefix_ports=ports, sign_extension_wire=sign_wire,
                sign_extension_bits=sign_width, architectural_output=output,
                dot16_predicate=mode,
                data_bindings_verified=True)


def verify_parent_wrapper(actual_bytes, original_bytes, feature):
    actual, original = actual_bytes.decode('utf-8'), original_bytes.decode('utf-8')
    record = verify_data_binding(actual, feature)
    old_header, new_header = module_header(original), module_header(actual)
    need(new_header == old_header, 'original real-parent wrapper interface is byte-exact')
    before, after = assignments(original), assignments(actual)
    def data_or_shadow(name):
        return (name.startswith('pProducts_') or name.startswith('pRows_')
                or name in ('rPacket_res_data', 'heldResponse'))
    non_data_before = [(key, value) for key, value in before if not data_or_shadow(key)]
    non_data_after = [(key, value) for key, value in after if not data_or_shadow(key)]
    need(non_data_after == non_data_before, 'ordered non-data sequential updates unchanged')
    old_output = re.findall(r'\bassign\s+io_out_bits_res_data\s*=\s*(.*?);', original, re.S)
    need([compact(value) for value in old_output] == ["{96'h0,rPacket_res_data}"],
         'fixed original R32 architectural output')
    old_held = [value for key, value in before if key == 'heldResponse']
    new_held = [value for key, value in after if key == 'heldResponse']
    marker = "96'h0,rPacket_res_data,"
    need(len(old_held) == len(new_held) == 1 and old_held[0].count(marker) == 1,
         'single complete original and new stalled-response shadow update')
    expected = old_held[0].replace(marker, "96'h0,"+record['sign_extension_wire']+",rPacket_res_data,", 1)
    need(new_held[0] == expected,
         'shadow update differs only by the independently bound R sign extension')
    shadow_decl = lambda value: re.findall(r'\breg\s+\[(\d+):0\]\s+heldResponse\s*;', value)
    need(shadow_decl(actual) == shadow_decl(original) == ['940'],
         'same complete 941-bit stalled-response shadow')
    record.update(original_wrapper_sha256=hashlib.sha256(original_bytes).hexdigest(),
                  actual_wrapper_sha256=hashlib.sha256(actual_bytes).hexdigest(),
                  interface_byte_exact=True,
                  non_data_sequential_updates_equal=True,
                  non_data_assignment_count=len(non_data_before),
                  stalled_shadow_only_sign_extension_changed=True,
                  comparison_scope='interfaces, ordered update expressions and closed data bindings; not sequential formal equivalence',
                  real_rtl_modified=False)
    return record
