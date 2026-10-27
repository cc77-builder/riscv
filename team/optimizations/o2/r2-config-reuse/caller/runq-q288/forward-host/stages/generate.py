"""Derive explicit stage boundaries from the pinned, unchanged runq forward.

The generated fragment needs the original Config/RunState/Transformer types,
original neural-net functions, STAGE_QUANTIZE and STAGE_MARK from its caller.
It is not a target runtime or a replacement for the upstream reference.
"""
from pathlib import Path
import hashlib
import json

UPSTREAM_SHA = 'ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548'
OBSERVE_SHA = '92bd2986e8bca35dc2ed30d0338eac2a0c96ef6a54d766835c793ad6fb9e8236'
STAGES = ['embedding', 'rope_prepare', 'attn_norm', 'qkv_quantize', 'q', 'k', 'v',
          'rope', 'kv_write', 'attention', 'out_quantize', 'out_projection',
          'attn_residual', 'ffn_norm', 'ffn_quantize', 'ffn_up', 'ffn_gate',
          'swiglu', 'ffn_down_quantize', 'ffn_down', 'ffn_residual',
          'final_norm', 'classifier_quantize', 'classifier', 'end']
LAYER_STAGES = STAGES[2:21]
ANGLE = '''            float freq = 1.0f / powf(10000.0f, head_dim / (float)head_size);
            float val = pos * freq;
            float fcr = cosf(val);
            float fci = sinf(val);'''
CACHED = '''            float fcr = rope_cos[head_dim / 2];
            float fci = rope_sin[head_dim / 2];'''
DECLARATION = '    float rope_cos[24], rope_sin[24];\n'
PREPARE = '''    for (int head_dim = 0; head_dim < head_size; head_dim += 2) {
        float freq = 1.0f / powf(10000.0f, head_dim / (float)head_size);
        float val = pos * freq;
        rope_cos[head_dim / 2] = cosf(val);
        rope_sin[head_dim / 2] = sinf(val);
    }
    STAGE_TEST_CACHE(rope_cos, pos);
'''


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original(path):
    raw = Path(path).read_bytes()
    need(sha(raw) == UPSTREAM_SHA, 'unchanged complete upstream SHA-256')
    text = raw.decode('utf-8')
    start = text.index('float* forward(')
    end = text.index('\n// ----------------------------------------------------------------------------', start)
    return text[start:end].strip()


def insert_once(text, anchor, addition):
    need(text.count(anchor) == 1, 'unique stage anchor: '+anchor.strip())
    return text.replace(anchor, addition+anchor)


def expected_events():
    return [('embedding', -1), ('rope_prepare', -1)] + [
        (stage, layer) for layer in range(6) for stage in LAYER_STAGES
    ] + [(stage, -1) for stage in STAGES[21:]]


def render(source, name, cached=False, trace=True):
    code = source.replace('float* forward(', 'static float* '+name+'(', 1)
    code = code.replace('quantize(', 'STAGE_QUANTIZE(')
    additions = []

    def mark(anchor, stage, layer='l', indent='        '):
        nonlocal code
        if trace:
            addition = indent+f'STAGE_MARK({STAGES.index(stage)}, {layer});\n'
            code = insert_once(code, anchor, addition)
            additions.append(addition)

    mark('    // copy the token embedding into x', 'embedding', '-1', '    ')
    mark('    // forward all the layers', 'rope_prepare', '-1', '    ')
    anchors = [
        ('        // attention rmsnorm', 'attn_norm'),
        ('        // qkv matmuls for this position', 'qkv_quantize'),
        ('        matmul(s->q,', 'q'), ('        matmul(s->k,', 'k'),
        ('        matmul(s->v,', 'v'),
        ('        // RoPE relative positional encoding:', 'rope'),
        ('        // save key,value at this time step', 'kv_write'),
        ('        // multihead attention.', 'attention'),
        ('        // final matmul to get the output of the attention', 'out_quantize'),
        ('        matmul(s->xb2,', 'out_projection'),
        ('        // residual connection back into x', 'attn_residual'),
        ('        // ffn rmsnorm', 'ffn_norm'),
        ('        // Now for FFN in PyTorch', 'ffn_quantize'),
        ('        matmul(s->hb,', 'ffn_up'), ('        matmul(s->hb2,', 'ffn_gate'),
        ('        // SwiGLU non-linearity', 'swiglu'),
        ('        // final matmul to get the output of the ffn', 'ffn_down_quantize'),
        ('        matmul(s->xb,', 'ffn_down'),
        ('        // residual connection\n', 'ffn_residual'),
    ]
    for anchor, stage in anchors:
        mark(anchor, stage)
    for anchor, stage in [
        ('    // final rmsnorm', 'final_norm'),
        ('    STAGE_QUANTIZE(&s->xq, x, dim);', 'classifier_quantize'),
        ('    matmul(s->logits,', 'classifier'),
        ('    return s->logits;', 'end'),
    ]:
        mark(anchor, stage, '-1', '    ')
    if cached:
        code = insert_once(code, '    // copy the token embedding into x', DECLARATION)
        code = insert_once(code, '    // forward all the layers', PREPARE)
        need(code.count(ANGLE) == 1, 'one complete original RoPE angle expression')
        code = code.replace(ANGLE, CACHED)
    restored = code
    if cached:
        for addition in (DECLARATION, PREPARE):
            need(restored.count(addition) == 1, 'one explicit cache addition')
            restored = restored.replace(addition, '')
        need(restored.count(CACHED) == 1, 'one explicit cached angle use')
        restored = restored.replace(CACHED, ANGLE)
    for addition in additions:
        need(restored.count(addition) == 1, 'one exact emitted marker')
        restored = restored.replace(addition, '')
    restored = restored.replace('static float* '+name+'(', 'float* forward(', 1)
    restored = restored.replace('STAGE_QUANTIZE(', 'quantize(')
    need(restored == source, 'entire restored forward source equals original')
    return code


def generate(upstream, output):
    source = original(upstream)
    output = Path(output)
    functions = [render(source, 'stage_reference'),
                 render(source, 'stage_cached', cached=True),
                 render(source, 'cached_forward', cached=True, trace=False)]
    text = ('/* Generated team adapter; upstream MIT license remains in ../upstream/LICENSE. */\n'
            + '\n\n'.join(functions)+'\n')
    output.write_text(text, encoding='utf-8')
    events = expected_events()
    need(len(events) == 120, '120 fixed boundaries')
    return dict(upstream_sha256=UPSTREAM_SHA, original_forward_sha256=sha(source.encode()),
                generated_sha256=sha(text.encode()), restored_entire_source_equal=True,
                variants=['stage_reference', 'stage_cached', 'cached_forward'],
                stages=STAGES, expected_events=events, intervals=len(events)-1,
                rope_pairs_per_call=24, rope_table_bytes=192,
                target_runtime_provided=False, performance_qualified=False)
