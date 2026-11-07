"""Root-authored exact source extension: four W2 sites and a typed selector.

Append to the pinned narrow-Q288 derivation. No official input is changed.
The old complete generated C/include are recovered byte-for-byte by inverse.
"""
PRE_W2_CORE = core
CONTRACT = 'r3-dot16-first-forward-w2np-v1'
W2_SYMBOLS = {'paired16': 'q768_paired16_rvv', 'dot16': 'q768_dot16_whole8_narrow'}


def core(c_raw, inc_raw):
    need(DOT16_SYMBOL == 'q288_dot16_whole8_narrow', 'fixed qualified narrow Q288')
    generated, parent_proof = PRE_W2_CORE(c_raw, inc_raw)
    old_c, old_inc = generated['consumer.c'].decode(), generated['consumer.inc'].decode()
    c, inc, c_edits, inc_edits = old_c, old_inc, [], []
    anchor = 'extern void q288_tail_vdot(struct q288_context *);\n'
    declarations = (anchor + 'extern void q288_paired16_rvv(struct q288_context *);\n'
                    'extern void q288_dot16_whole8_narrow(struct q288_context *);\n'
                    'extern void q768_paired16_rvv(struct w2_context *);\n'
                    'extern void q768_dot16_whole8_narrow(struct w2_context *);\n')
    c = change(c, anchor, declarations, c_edits)
    before = '            void (*entry)(struct w2_context*)=kernel==q288_fused_rvv4?q768_fr:q768_ta;\n'
    after = ('            void (*entry)(struct w2_context*)=\n'
             '                kernel==q288_fused_rvv4 ? q768_fr :\n'
             '                kernel==q288_paired16_rvv ? q768_paired16_rvv :\n'
             '                kernel==q288_dot16_whole8_narrow ? q768_dot16_whole8_narrow : q768_ta;\n')
    c = change(c, before, after, c_edits)
    routes = {}
    for name in ACTIVE_METHODS:
        marker = '__attribute__((noinline)) static float* consumer_' + name + '_cache('
        need(inc.count(marker) == 1, 'one complete target consumer: ' + name)
        start = inc.index(marker)
        next_start = inc.find('__attribute__((noinline)) static float*', start + len(marker))
        stop = len(inc) if next_start < 0 else next_start
        previous = inc[start:stop]
        route = 'paired16' if name.startswith('paired16') else 'dot16'
        changed = previous.replace(W2_LINE, W2_LINE.replace('route_fr(', 'route_' + route + '('))
        need(previous.count(W2_LINE) == 1 and previous.count('route_' + route + '(') == 7,
             'one W2 and seven Q288 original sites: ' + name)
        need(changed.count('route_' + route + '(') == 8 and 'route_fr(' not in changed,
             'eight statically routed sites after W2 replacement')
        inc = change(inc, previous, changed, inc_edits)
        routes[name] = dict(before_sha256=sha(previous.encode()), after_sha256=sha(changed.encode()),
                            q288_static_sites=7, w2_static_sites=1, w2_kernel=W2_SYMBOLS[route],
                            exact_complete_function_inverse=True)
    for text, old, edits in ((c, old_c, c_edits), (inc, old_inc, inc_edits)):
        inverse = text
        for before, after in reversed(edits):
            need(inverse.count(after) == 1, 'unique entire inverse source span')
            inverse = inverse.replace(after, before, 1)
        need(inverse == old, 'whole prior narrow consumer recovered')
    return {'consumer.c': c.encode(), 'consumer.inc': inc.encode()}, dict(
        parent=parent_proof, previous_c_sha256=sha(old_c.encode()),
        previous_include_sha256=sha(old_inc.encode()), c_edits=c_edits, include_edits=inc_edits,
        routes=routes, exact_prior_generated_sources_recovered=True,
        tensor_layer_offsets_context_fp_order_unchanged=True,
        main_csr_window_and_report_abi_unchanged=True,
        qualification='new source only; full application reference and target evidence required')
