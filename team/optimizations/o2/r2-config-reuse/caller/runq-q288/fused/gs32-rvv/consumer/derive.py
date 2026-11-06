"""Derive the separate GS32 entry from the actual frozen norm/W2 C sources.

The existing four consumer functions, old API and upstream source are never
edited. The one new clone changes seven K288 routes; its unique W2 call stays
byte-for-byte the original FR call. This is a fixed-model private route.
"""
from pathlib import Path
import hashlib
import json

PARENTS = {
    'consumer.c': '0510a0279b7a72692f0deb29eb70dd6f57f0d4b94a8b4f08cf766bc9f110f22e',
    'consumer.inc': '028ee77b1fede4a8803b86302eaf705a7f62e7d5eb527da8586bc412f5fe8be0',
    'main.c': '43a4950b754676e0105b26095be3a904ea361a2c5dc97fbdfe721de18caf4544',
}
ENTRY = 'r2_w2_gs32_forward'
ENTRY_TAG = 0x47533332
CONTRACT = 'r2-s3-forward-consumer-gs32-v1'
W2_LINE = '        route_fr(s->xb, &s->hq, w->w2 + l, hidden_dim, dim);\n'
ROUTE = '''extern void q288_gs32_rvv(struct q288_context *);
/* Private K288 route: the new clone leaves its sole K768 call on route_fr. */
static void route_gs32(float *out,QuantizedTensor *x,QuantizedTensor *w,int n,int d) {
    route_matmul(out,x,w,n,d,q288_gs32_rvv);
}
'''
PUBLIC = '''
__attribute__((noinline)) float *r2_w2_gs32_forward(struct r2_consumer_state *state,
                                                   int token,int position) {
    if(!initialized || !state || token<0 || token>=32000 || position<0 || position>=256)return NULL;
    Transformer t={0};t.config=(Config){288,768,6,6,6,32000,256};t.weights=model;bind_state(&t.state,state);
    return consumer_gs32_cache(&t,token,position);
}
'''
ZERO_CHECK = '''static void state_empty(unsigned code) {
    const unsigned char *p=(const unsigned char *)&consumer_state;
    for(size_t i=0;i<sizeof(consumer_state);++i)check(p[i]==0,code);
}
'''
BEFORE_INIT = '''    check(r2_w2_gs32_forward(&consumer_state,0,0)==NULL,87);
    state_empty(87);
'''
AFTER_INIT = '''    check(r2_w2_gs32_forward(NULL,1,0)==NULL,88);
    check(r2_w2_gs32_forward(&consumer_state,-1,0)==NULL,88);
    check(r2_w2_gs32_forward(&consumer_state,32000,0)==NULL,88);
    check(r2_w2_gs32_forward(&consumer_state,1,-1)==NULL,88);
    check(r2_w2_gs32_forward(&consumer_state,1,256)==NULL,88);
    check(r2_w2_forward(&consumer_state,(enum r2_consumer_method)5,1,0)==NULL,89);
    state_empty(89);
'''


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def replace_once(text, before, after):
    need(text.count(before) == 1 and after not in text,
         'one exact source change: ' + before[:70])
    return text.replace(before, after)


def derive(source):
    original = {name: (source / name).read_bytes() for name in PARENTS}
    for name, raw in original.items():
        need(sha(raw) == PARENTS[name], 'actual compiled parent source: ' + name)
    old_inc = original['consumer.inc'].decode()
    start = '__attribute__((noinline)) static float* consumer_fr_cache('
    stop = '__attribute__((noinline)) static float* consumer_ta_cache('
    need(old_inc.count(start) == old_inc.count(stop) == 1, 'unique complete cached FR template')
    template = old_inc[old_inc.index(start):old_inc.index(stop)]
    need(template.count('route_fr(') == 8 and template.count(W2_LINE) == 1,
         'seven K288 calls and exactly one retained K768 call')
    clone = ''.join(line if line == W2_LINE else line.replace('route_fr(', 'route_gs32(')
                    for line in template.splitlines(keepends=True))
    clone = clone.replace('consumer_fr_cache(', 'consumer_gs32_cache(')
    need(clone.count('route_gs32(') == 7 and clone.count('route_fr(') == 1
         and clone.count(W2_LINE) == 1, 'new route scope excludes W2')
    need(clone.replace('consumer_gs32_cache(', 'consumer_fr_cache(')
         .replace('route_gs32(', 'route_fr(') == template, 'whole clone reverses to original template')
    inc = old_inc + '\n' + clone
    need(inc[:len(old_inc)] == old_inc, 'all four original functions preserved')

    old_c = original['consumer.c'].decode()
    header = '#include "consumer_w2.h"'
    marker = '#define STAGE_QUANTIZE quantize\n'
    c = replace_once(old_c, header, header + '\n#include "consumer_gs32.h"')
    c = replace_once(c, marker, ROUTE + marker) + PUBLIC
    restored = c[:-len(PUBLIC)].replace(ROUTE, '').replace(
        header + '\n#include "consumer_gs32.h"', header)
    need(restored == old_c, 'complete old model/init/reset/route/API byte-text preserved')

    main = original['main.c'].decode()
    changes = [
        (header, header + '\n#include "consumer_gs32.h"'),
        ('/* method, consecutive positions, application negative, save selected states */',
         '/* independent entry tag, three positions, output negative, snapshots */'),
        ('={4,3,0,1};', '={0x47533332u,3,0,1};'),
        ('unsigned method=consumer_control[0]', 'unsigned entry=consumer_control[0]'),
        ('consumer_report[2]=method;', 'consumer_report[2]=entry;'),
        ('check(method<=4 && positions>=1 && positions<=256 && negative<=1 && snapshots<=1,82);',
         'check(entry==0x47533332u && positions==3 && negative<=1 && snapshots==1,82);'),
        ('static void tls_check(void) {', ZERO_CHECK + 'static void tls_check(void) {'),
        ('    check(r2_w2_init(fixture_weights,fixture_weights_end-fixture_weights,',
         BEFORE_INIT + '    check(r2_w2_init(fixture_weights,fixture_weights_end-fixture_weights,'),
        ('    /* The complete raw image contains zero-filled state, verified from ELF.',
         AFTER_INIT + '    /* The complete raw image contains zero-filled state, verified from ELF.'),
        ('        float *logits=r2_w2_forward(&consumer_state,(enum r2_consumer_method)method,token,(int)p);',
         '        __asm__ volatile(".global gs32_forward_call_begin\\ngs32_forward_call_begin:":::"memory");\n'
         '        float *logits=r2_w2_gs32_forward(&consumer_state,token,(int)p);\n'
         '        __asm__ volatile(".global gs32_forward_call_end\\ngs32_forward_call_end:":::"memory");'),
    ]
    for before, after in changes:
        main = replace_once(main, before, after)
    restored_main = main
    for before, after in reversed(changes):
        need(restored_main.count(after) == 1, 'unique reverse harness edit')
        restored_main = restored_main.replace(after, before)
    need(restored_main.encode() == original['main.c'], 'exact original harness reverse')
    generated = {'consumer.c': c, 'consumer.inc': inc, 'main.c': main}
    for name, text in generated.items():
        (source / name).write_text(text)
    return dict(contract=CONTRACT, entry=ENTRY, entry_tag=ENTRY_TAG,
        parent_source_sha256=PARENTS,
        generated_source_sha256={name: sha(text.encode()) for name, text in generated.items()},
        original_four_consumers_preserved=True, complete_old_c_reverse=True,
        exact_clone_reverse=True, k288_static_call_sites=7, unchanged_k768_static_call_sites=1,
        existing_enum_0_to_4_unchanged=True, method_5_still_invalid=True,
        old_harness_exact_reverse=True, guest_guard_source_added=True,
        performance_qualified=False)
