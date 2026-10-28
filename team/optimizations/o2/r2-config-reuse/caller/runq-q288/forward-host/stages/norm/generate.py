"""Derive only RMSNorm's output loop from the fixed, unchanged upstream."""
from pathlib import Path
import hashlib

UPSTREAM_SHA='ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548'
OUTPUT='''    for (int j = 0; j < size; j++) {
        o[j] = weight[j] * (ss * x[j]);
    }'''
REPLACEMENT='    r2_norm_output_rvv(o, x, weight, ss, (unsigned)size);'
def sha(data): return hashlib.sha256(data).hexdigest()
def generate(upstream,output):
    raw=Path(upstream).read_bytes()
    if sha(raw)!=UPSTREAM_SHA: raise ValueError('fixed original runq.c identity')
    text=raw.decode();start=text.index('void rmsnorm(');end=text.index('\nvoid softmax(',start)
    original=text[start:end].rstrip()
    if original.count(OUTPUT)!=1: raise ValueError('one exact original output loop')
    candidate=original.replace('void rmsnorm(', '__attribute__((noinline)) void r2_rmsnorm_rvv(',1).replace(OUTPUT,REPLACEMENT)
    restored=candidate.replace('__attribute__((noinline)) void r2_rmsnorm_rvv(', 'void rmsnorm(',1).replace(REPLACEMENT,OUTPUT)
    if restored!=original: raise ValueError('complete derivation reversal')
    emitted='/* Derived from the fixed MIT-licensed runq.c; see adjacent upstream source. */\n#include <math.h>\n#include "norm.h"\n'+candidate+'\n'
    Path(output).write_text(emitted,encoding='utf-8')
    return dict(upstream_sha256=sha(raw),original_function_sha256=sha(original.encode()),
                candidate_sha256=sha(emitted.encode()),exact_reverse=True,
                unchanged_scalar_prefix=True,only_output_loop_replaced=True)
