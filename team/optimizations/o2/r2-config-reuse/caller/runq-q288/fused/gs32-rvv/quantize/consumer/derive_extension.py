"""Append one reversible GQ clone to the existing first-forward derivation."""
BASE_CORE=core
BASE_MAIN=main
CONTRACT='r2-s3-first-forward-gsq-v1'
MAGIC=0x5232475351563031
METHODS={**METHODS,'gs32_quantize':0x47535131}

def core(c_raw,inc_raw):
    generated,parent_proof=BASE_CORE(c_raw,inc_raw)
    c,inc=generated['consumer.c'].decode(),generated['consumer.inc'].decode()
    begin='__attribute__((noinline)) static float* consumer_gs32_cache('
    end='__attribute__((noinline)) static float* consumer_paired16_cache('
    need(inc.count(begin)==inc.count(end)==1,'one complete existing G template')
    template=inc[inc.index(begin):inc.index(end)]
    need(template.count('STAGE_QUANTIZE(')==5 and template.count('route_gs32(')==7 and template.count('route_fr(')==1,'five quantize calls and original eight GEMV routes')
    clone=template.replace('consumer_gs32_cache(','consumer_gs32_quantize_cache(').replace('STAGE_QUANTIZE(','r2_quantize_gs32_rvv(')
    need(clone.replace('consumer_gs32_quantize_cache(','consumer_gs32_cache(').replace('r2_quantize_gs32_rvv(','STAGE_QUANTIZE(')==template,'whole quantize clone exact reverse')
    public_start='__attribute__((noinline)) float *r2_w2_gs32_forward('
    public_end='__attribute__((noinline)) float *r2_w2_paired16_forward('
    need(c.count(public_start)==c.count(public_end)==1,'one existing G public entry')
    public=c[c.index(public_start):c.index(public_end)]
    entry=public.replace('r2_w2_gs32_forward(','r2_w2_gs32_quantize_forward(').replace('consumer_gs32_cache(','consumer_gs32_quantize_cache(')
    need(entry.replace('r2_w2_gs32_quantize_forward(','r2_w2_gs32_forward(').replace('consumer_gs32_quantize_cache(','consumer_gs32_cache(')==public,'thin entry exact reverse')
    declaration='extern void r2_quantize_gs32_rvv(QuantizedTensor *,float *,int);\n'
    marker='#define STAGE_QUANTIZE quantize\n'
    need(c.count(marker)==1 and declaration not in c,'unchanged original macro and unique declaration')
    changed_c=c.replace(marker,declaration+marker)+entry
    changed_inc=inc+'\n'+clone
    need(changed_c[:-len(entry)].replace(declaration,'')==c and changed_inc[:len(inc)]==inc,'all existing C/include bytes retained')
    return {'consumer.c':changed_c.encode(),'consumer.inc':changed_inc.encode()},dict(parent=parent_proof,old_combination_c_sha256=sha(c.encode()),old_combination_include_sha256=sha(inc.encode()),template_sha256=sha(template.encode()),clone_sha256=sha(clone.encode()),quantize_static_sites=5,k288_static_routes=7,retained_w2_fr_routes=1,whole_clone_exact_reverse=True,original_c_exact_reverse=True,original_include_prefix_preserved=True,original_quantize_definition_unchanged=True)

def main(raw):
    original,parent_proof=BASE_MAIN(raw)
    text,edits=original.decode(),[]
    pairs=[
        ('extern float *r2_w2_gs32_forward(struct r2_consumer_state *,int,int);\n','extern float *r2_w2_gs32_forward(struct r2_consumer_state *,int,int);\nextern float *r2_w2_gs32_quantize_forward(struct r2_consumer_state *,int,int);\n'),
        ('        case 0x47533332u: return r2_w2_gs32_forward(&target_state,1,0);\n','        case 0x47533332u: return r2_w2_gs32_forward(&target_state,1,0);\n        case 0x47535131u: return r2_w2_gs32_quantize_forward(&target_state,1,0);\n'),
        ('0x5232465752565631','0x5232475351563031')]
    for before,after in pairs:text=change(text,before,after,edits)
    restored=text
    for before,after in reversed(edits):
        need(restored.count(after)==1,'unique inverse GQ main span')
        restored=restored.replace(after,before)
    need(restored.encode()==original,'whole old first-forward main recovered')
    return text.encode(),dict(parent=parent_proof,exact_inverse=True,edits=edits,selector_load_and_dispatch_inside_window=True,no_new_in_window_probe=True)
