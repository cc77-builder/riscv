"""Derive the optional W2 consumer; reverse every change to its fixed parent."""
from pathlib import Path
import hashlib,json

CONTRACT='r2-s3-forward-consumer-w2-v1'
PARENTS={'consumer.c':'f1d944367614fda5df4317355315b456afc8ff3ff53779ff021fb87d04940d4c','main.c':'398d20b1abc193ffdf92a31afa9deb59ea7483cec04a4c2804994d3058102c19'}
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()

def generate(parent,output):
    output.mkdir(parents=True,exist_ok=True);records={}
    for name in ('consumer.c','main.c'):
        original=(parent/name).read_text();need(sha(original.encode())==PARENTS[name],'fixed pure consumer parent '+name)
        changes=[]
        def replace(before,after,count=1):
            nonlocal text
            need(text.count(before)==count,'exact substitution site '+before[:60])
            text=text.replace(before,after);changes.append((before,after,count))
        text=original
        replace('#include "consumer.h"','#include "consumer.h"\n#include "consumer_w2.h"')
        for api in ('init','reset','forward'):
            token='r2_consumer_'+api
            if token in text:replace(token,'r2_w2_'+api,text.count(token))
        if name=='consumer.c':
            replace('#include "q288.h"','#include "q288.h"\n#include "w2.h"')
            replace('static const int8_t *packed_model;','static const int8_t *packed_model,*w2_packed_model;')
            replace('const void *tail_scales,size_t tail_scale_bytes) {','const void *tail_scales,size_t tail_scale_bytes,\n                     const void *w2_packed,size_t w2_packed_bytes) {')
            replace('if(!weights || !embedding || !packed || !tail_scales ||','if(!weights || !embedding || !packed || !tail_scales || !w2_packed ||\n       w2_packed_bytes!=R2_W2_PACKED_BYTES || (uintptr_t)w2_packed%16 ||')
            replace('packed_model=packed; tail_model=tail_scales;','packed_model=packed; w2_packed_model=w2_packed; tail_model=tail_scales;')
            replace("/* Both paths have exactly the same routing and tail handling. W2's K768\n * remains the original scalar left fold. Only the complete Q kernel differs.\n */", "/* Both methods share routing. Fixed six-layer W2 uses the matching K768\n * kernel; unknown shapes/tensors retain the original scalar fallback. */")
            old='    if(n!=288) {matmul(out,x,w,n,d);return;}'
            new='''    if(n==768 && d==288) {
        for(unsigned layer=0;layer<6;++layer)if(w==&arrays[5][layer]) {
            struct w2_slot work[8] __attribute__((aligned(16)));
            struct w2_context c={w2_packed_model+(size_t)layer*221184,
                x->q,w->s,x->s,out,work,0};
            void (*entry)(struct w2_context*)=kernel==q288_fused_rvv4?q768_fr:q768_ta;
            entry(&c);return;
        }
    }
'''+old
            replace(old,new)
        else:
            replace('.word 0x0000006b','.word 0x0005006b')
            replace('extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[];',
                    'extern unsigned char fixture_packed[],fixture_packed_end[],fixture_tail_scales[],fixture_tail_scales_end[];\nextern unsigned char fixture_w2_packed[],fixture_w2_packed_end[];')
            replace('0x5232434f4e533031','0x52325732434f3031')
            replace('fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales)==0,85);',
                    'fixture_tail_scales,fixture_tail_scales_end-fixture_tail_scales,\n                          fixture_w2_packed,fixture_w2_packed_end-fixture_w2_packed)==0,85);')
        restored=text
        for before,after,count in reversed(changes):
            need(restored.count(after)==count,'unambiguous reverse site')
            restored=restored.replace(after,before)
        need(restored==original,'complete source exactly reverses to parent')
        (output/name).write_text(text)
        records[name]=dict(parent_sha256=PARENTS[name],sha256=sha(text.encode()),exact_parent_reverse=True,substitutions=len(changes))
    return dict(contract=CONTRACT,sources=records,original_consumer_unchanged=True)
