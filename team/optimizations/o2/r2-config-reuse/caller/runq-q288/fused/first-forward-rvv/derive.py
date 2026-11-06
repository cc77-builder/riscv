"""Bounded source derivation for one FR/GS32/paired16 first-forward image.

Only team sources are derived. The original consumer, API, kernels, reference
and official build inputs stay read-only. Each clone reverses to the same FR
template; the harness reverses to the actual frozen norm first-token source.
"""
import hashlib

CONTRACT = 'r2-s3-first-forward-rvv-v1'
MAGIC = 0x5232465752565631
METHODS = {'fr': 3, 'gs32': 0x47533332, 'paired16': 0x50313631}
PARENTS = {
    'consumer.c': '0510a0279b7a72692f0deb29eb70dd6f57f0d4b94a8b4f08cf766bc9f110f22e',
    'consumer.inc': '028ee77b1fede4a8803b86302eaf705a7f62e7d5eb527da8586bc412f5fe8be0',
}
MAIN_SHA = '4537a39c9b07bd4d2e61f6b7e48aae7f241b7905abd18fb198402fce356976ad'
ENTRY_SHA = '7db6047a7dfea8a4a1cd98ba95b2845c03405d4fc8aee638463e241da6290531'
W2_LINE = '        route_fr(s->xb, &s->hq, w->w2 + l, hidden_dim, dim);\n'
BEGIN = 'CONSUMER_BEGIN token=1 position=0'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def change(text, before, after, records):
    need(text.count(before) == 1 and before != after, 'unique source edit: ' + before[:70])
    need(after not in text, 'new source span absent before derivation')
    records.append((before, after))
    return text.replace(before, after)


def core(c_raw, inc_raw):
    need(sha(c_raw) == PARENTS['consumer.c'] and sha(inc_raw) == PARENTS['consumer.inc'],
         'actual frozen norm/W2 C and include')
    old_c, old_inc = c_raw.decode(), inc_raw.decode()
    first = '__attribute__((noinline)) static float* consumer_fr_cache('
    last = '__attribute__((noinline)) static float* consumer_ta_cache('
    need(old_inc.count(first) == old_inc.count(last) == 1, 'one complete FR-cache template')
    template = old_inc[old_inc.index(first):old_inc.index(last)]
    need(template.count('route_fr(') == 8 and template.count(W2_LINE) == 1,
         'seven K288 static routes and the single original W2 route')
    clones, routes, public, proof = [], [], [], {}
    for name in ('gs32', 'paired16'):
        clone = ''.join(line if line == W2_LINE else line.replace('route_fr(', f'route_{name}(')
                        for line in template.splitlines(keepends=True))
        clone = clone.replace('consumer_fr_cache(', f'consumer_{name}_cache(')
        need(clone.count(f'route_{name}(') == 7 and clone.count('route_fr(') == 1
             and clone.count(W2_LINE) == 1, 'bounded route replacement: ' + name)
        need(clone.replace(f'consumer_{name}_cache(', 'consumer_fr_cache(')
             .replace(f'route_{name}(', 'route_fr(') == template, 'exact complete clone reversal')
        clones.append(clone)
        routes.append(f'''extern void q288_{name}_rvv(struct q288_context *);
static void route_{name}(float *out,QuantizedTensor *x,QuantizedTensor *w,int n,int d) {{
    route_matmul(out,x,w,n,d,q288_{name}_rvv);
}}
''')
        public.append(f'''
__attribute__((noinline)) float *r2_w2_{name}_forward(struct r2_consumer_state *state,
                                                   int token,int position) {{
    if(!initialized || !state || token<0 || token>=32000 || position<0 || position>=256)return NULL;
    Transformer t={{0}};t.config=(Config){{288,768,6,6,6,32000,256}};t.weights=model;bind_state(&t.state,state);
    return consumer_{name}_cache(&t,token,position);
}}
''')
        proof[name] = dict(template_sha256=sha(template.encode()), clone_sha256=sha(clone.encode()),
                           exact_reverse=True, k288_static_routes=7, retained_w2_fr_routes=1)
    marker = '#define STAGE_QUANTIZE quantize\n'
    need(old_c.count(marker) == 1, 'one private route insertion point')
    added = ''.join(routes)
    suffix = ''.join(public)
    c = old_c.replace(marker, added + marker) + suffix
    inc = old_inc + '\n' + '\n'.join(clones)
    need(c[:-len(suffix)].replace(added, '') == old_c and inc.startswith(old_inc),
         'old API, globals, init/reset and original functions unchanged')
    return {'consumer.c': c.encode(), 'consumer.inc': inc.encode()}, {
        'parent_sources': PARENTS, 'clones': proof, 'original_c_exact_reverse': True,
        'original_include_prefix_preserved': True, 'shared_initialization_and_model_globals': True,
        'old_enum_0_to_4_and_method_5_domain_unchanged': True,
    }


def main(raw):
    need(sha(raw) == MAIN_SHA, 'actual frozen first-token target main')
    text, edits = raw.decode(), []
    declarations = '''extern float *r2_w2_gs32_forward(struct r2_consumer_state *,int,int);
extern float *r2_w2_paired16_forward(struct r2_consumer_state *,int,int);
'''
    dispatch = '''/* Method load, validation and dispatch are entirely inside the measured call. */
__attribute__((noinline,noclone)) static float *first_forward_dispatch(void) {
    method=target_control[0];
    switch(method) {
        case 3u: return r2_w2_forward(&target_state,R2_FR_CACHE,1,0);
        case 0x47533332u: return r2_w2_gs32_forward(&target_state,1,0);
        case 0x50313631u: return r2_w2_paired16_forward(&target_state,1,0);
        default: reject(88,0);
    }
}
'''
    pairs = [
        ('/* Full forward measurement; all validation/UART are outside the pure call. */',
         '/* First full forward: method load and dispatch are included; validation/UART are outside. */'),
        ('#include "consumer_w2.h"', '#include "consumer_w2.h"\n' + declarations),
        ('/* FR_CACHE/TA_CACHE, actual application negative, UART enabled. */',
         '/* Private experiment selector, application negative, UART; old public enum is unchanged. */'),
        ('={4,0,1};', '={3,0,1};'),
        ('0x52324e5447543031', '0x5232465752565631'),
        ('int team_forward_main(void) {', dispatch + 'int team_forward_main(void) {'),
        ('    method=target_control[0];negative=target_control[1];uart=target_control[2];',
         '    negative=target_control[1];uart=target_control[2];'),
        ('target_report[1]=1;target_report[2]=method;target_report[3]=1;',
         'target_report[1]=1;target_report[2]=0;target_report[3]=1;'),
        ('check((method==R2_FR_CACHE || method==R2_TA_CACHE) && negative<=1 && uart<=1,82);',
         'check(negative<=1 && uart<=1,82);'),
        ('    if(uart)printf("CONSUMER_BEGIN method=%u token=1 position=0 negative=%u\\n",method,negative);',
         '    if(uart)printf("CONSUMER_BEGIN token=1 position=0\\n");'),
        ('    float *logits=r2_w2_forward(&target_state,(enum r2_consumer_method)method,1,0);',
         '    __asm__ volatile(".global first_forward_call_begin\\nfirst_forward_call_begin:":::"memory");\n'
         '    float *logits=first_forward_dispatch();\n'
         '    __asm__ volatile(".global first_forward_call_end\\nfirst_forward_call_end:":::"memory");'),
        ('    target_report[16]=c0;', '    target_report[2]=method;target_report[16]=c0;'),
    ]
    for before, after in pairs:
        text = change(text, before, after, edits)
    restored = text
    for before, after in reversed(edits):
        need(restored.count(after) == 1, 'unique inverse main span')
        restored = restored.replace(after, before)
    need(restored.encode() == raw, 'entire original norm first-token wrapper recovered')
    need('state_empty' not in text, 'no correctness-only state scans')
    return text.encode(), dict(parent_main_sha256=MAIN_SHA, exact_inverse=True, edits=edits,
        fixed_begin=BEGIN, selector_load_and_dispatch_inside_window=True,
        method_report_after_four_reads=True, no_prestate_scan=True, exact_flags_guard=1)


def entry(raw):
    need(sha(raw) == ENTRY_SHA and raw.count(b'.word 0x0000006b') == 1, 'original entry bytes')
    changed = raw.replace(b'.word 0x0000006b', b'.word 0x0005006b')
    need(changed.replace(b'.word 0x0005006b', b'.word 0x0000006b') == raw, 'entry exact inverse')
    return changed
