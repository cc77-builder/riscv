"""Append D/DQ to the already derived P/PQ source, preserving every old byte.

This is appended by prepare.py after the fixed paired-consumer extension.
The kernel placeholder is replaced only by an explicit, pinned selection.
"""
PRE_DOT16_CORE = core
PRE_DOT16_MAIN = main
CONTRACT = 'r3-dot16-first-forward-v1'
MAGIC = 0x5233443136465731
DOT16_SYMBOL = '__SELECTED_DOT16_SYMBOL__'
METHODS = {**METHODS, 'dot16': 0x44313631, 'dot16_quantize': 0x44313651}
ACTIVE_METHODS = ('paired16', 'paired16_quantize', 'dot16', 'dot16_quantize')


def core(c_raw, inc_raw):
    need(DOT16_SYMBOL in ('q288_dot16_vdot', 'q288_dot16_whole2'),
         'explicit selected complete dot16 kernel')
    generated, parent_proof = PRE_DOT16_CORE(c_raw, inc_raw)
    old_c = generated['consumer.c'].decode()
    old_inc = generated['consumer.inc'].decode()
    pq_begin = '__attribute__((noinline)) static float* consumer_paired16_quantize_cache('
    need(old_inc.count(pq_begin) == 1, 'one final complete PQ template')
    pq_template = old_inc[old_inc.index(pq_begin):]
    need(pq_template.count('__attribute__((noinline)) static float*') == 1,
         'PQ remains the final complete cached function')
    template = pq_template.replace('consumer_paired16_quantize_cache(', 'consumer_paired16_cache(')
    template = template.replace('r2_quantize_gs32_rvv(', 'STAGE_QUANTIZE(')
    need(old_inc.count(template) == 1 and sha(template.encode()) == parent_proof['template_sha256'],
         'recover the actual complete P template, without changing the PQ derivation order')
    need(template.count('route_paired16(') == 7 and template.count('route_fr(') == 1
         and template.count(W2_LINE) == 1 and template.count('STAGE_QUANTIZE(') == 5,
         'same seven K288 routes, FR W2 route and five quantize sites')
    public_pq_begin = '__attribute__((noinline)) float *r2_w2_paired16_quantize_forward('
    need(old_c.count(public_pq_begin) == 1, 'one final PQ public entry')
    pq_public = old_c[old_c.index(public_pq_begin):]
    need(pq_public.count('__attribute__((noinline)) float *') == 1,
         'PQ remains the final complete public entry')
    public_template = pq_public.replace('r2_w2_paired16_quantize_forward(', 'r2_w2_paired16_forward(')
    public_template = public_template.replace('consumer_paired16_quantize_cache(', 'consumer_paired16_cache(')
    need(old_c.count(public_template) == 1, 'actual complete P public template')
    clones, entries, proofs = [], [], {}
    for name, optimized in (('dot16', False), ('dot16_quantize', True)):
        clone = template.replace('consumer_paired16_cache(', 'consumer_' + name + '_cache(')
        clone = clone.replace('route_paired16(', 'route_dot16(')
        if optimized:
            clone = clone.replace('STAGE_QUANTIZE(', 'r2_quantize_gs32_rvv(')
        inverse = clone.replace('consumer_' + name + '_cache(', 'consumer_paired16_cache(')
        inverse = inverse.replace('route_dot16(', 'route_paired16(')
        if optimized:
            inverse = inverse.replace('r2_quantize_gs32_rvv(', 'STAGE_QUANTIZE(')
        need(inverse == template and clone.count(W2_LINE) == 1 and clone.count('route_dot16(') == 7,
             'complete clone reverses to P and retains the exact FR W2 route')
        wanted = 'r2_quantize_gs32_rvv(' if optimized else 'STAGE_QUANTIZE('
        need(clone.count(wanted) == 5, 'five unchanged-position quantize sites')
        entry = public_template.replace('r2_w2_paired16_forward(', 'r2_w2_' + name + '_forward(')
        entry = entry.replace('consumer_paired16_cache(', 'consumer_' + name + '_cache(')
        need(entry.replace('r2_w2_' + name + '_forward(', 'r2_w2_paired16_forward(')
             .replace('consumer_' + name + '_cache(', 'consumer_paired16_cache(') == public_template,
             'whole public entry inverse')
        clones.append(clone)
        entries.append(entry)
        proofs[name] = dict(template_sha256=sha(template.encode()), clone_sha256=sha(clone.encode()),
                            public_sha256=sha(entry.encode()), complete_inverse=True,
                            k288_static_sites=7, retained_w2_fr_sites=1, quantize_static_sites=5,
                            quantize_symbol='r2_quantize_gs32_rvv' if optimized else 'quantize',
                            dot16_symbol=DOT16_SYMBOL)
    added = f'''extern void {DOT16_SYMBOL}(struct q288_context *);
static void route_dot16(float *out,QuantizedTensor *x,QuantizedTensor *w,int n,int d) {{
    route_matmul(out,x,w,n,d,{DOT16_SYMBOL});
}}
'''
    marker = '#define STAGE_QUANTIZE quantize\n'
    need(old_c.count(marker) == 1 and 'static void route_dot16(' not in old_c,
         'one existing macro and no prior dot16 route')
    suffix = '\n' + '\n'.join(entries)
    changed_c = old_c.replace(marker, added + marker) + suffix
    changed_inc = old_inc + '\n' + '\n'.join(clones)
    need(changed_c[:-len(suffix)].replace(added, '', 1) == old_c
         and changed_inc.startswith(old_inc), 'entire previous P/PQ sources retained')
    return {'consumer.c': changed_c.encode(), 'consumer.inc': changed_inc.encode()}, dict(
        parent=parent_proof, previous_c_sha256=sha(old_c.encode()),
        previous_include_sha256=sha(old_inc.encode()), clones=proofs,
        old_c_exact_inverse=True, old_include_prefix_preserved=True,
        shared_model_and_initialization=True, selected_dot16_symbol=DOT16_SYMBOL)


def main(raw):
    original, parent_proof = PRE_DOT16_MAIN(raw)
    text, edits = original.decode(), []
    pairs = [
        ('extern float *r2_w2_paired16_quantize_forward(struct r2_consumer_state *,int,int);\n',
         'extern float *r2_w2_paired16_quantize_forward(struct r2_consumer_state *,int,int);\n'
         'extern float *r2_w2_dot16_forward(struct r2_consumer_state *,int,int);\n'
         'extern float *r2_w2_dot16_quantize_forward(struct r2_consumer_state *,int,int);\n'),
        ('        case 0x50535131u: return r2_w2_paired16_quantize_forward(&target_state,1,0);\n',
         '        case 0x50535131u: return r2_w2_paired16_quantize_forward(&target_state,1,0);\n'
         '        case 0x44313631u: return r2_w2_dot16_forward(&target_state,1,0);\n'
         '        case 0x44313651u: return r2_w2_dot16_quantize_forward(&target_state,1,0);\n'),
        ('0x5232505351563031', '0x5233443136465731')]
    for before, after in pairs:
        text = change(text, before, after, edits)
    inverse = text
    for before, after in reversed(edits):
        need(inverse.count(after) == 1, 'unique inverse D/DQ main span')
        inverse = inverse.replace(after, before, 1)
    need(inverse.encode() == original, 'whole previous P/PQ main recovered')
    return text.encode(), dict(parent=parent_proof, exact_inverse=True, edits=edits,
        active_methods={name: METHODS[name] for name in ACTIVE_METHODS},
        selector_load_and_dispatch_inside_window=True, exact_flags_guard=1,
        all_four_csr_reads_and_fences_unchanged=True, no_new_in_window_probe=True)
