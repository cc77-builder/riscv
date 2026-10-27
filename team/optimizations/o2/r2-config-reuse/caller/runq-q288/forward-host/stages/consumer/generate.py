"""Generate four pure routes from the unchanged forward, with exact reversals."""
from pathlib import Path
import importlib.util
import hashlib

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('consumer_stage_generator',HERE.parent/'generate.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def generate(upstream,output):
    original=g.original(upstream);functions=[];records=[]
    for suffix,route,cached in [('fr','route_fr',False),('ta','route_ta',False),
                                ('fr_cache','route_fr',True),('ta_cache','route_ta',True)]:
        name='consumer_'+suffix
        rendered=g.render(original,name,cached=cached,trace=False)
        g.need(rendered.count('matmul(')==8,'all eight static matmul sites')
        emitted=rendered.replace('matmul(',route+'(')
        emitted=emitted.replace('static float* '+name+'(', '__attribute__((noinline)) static float* '+name+'(',1)
        restored=emitted.replace('__attribute__((noinline)) ','',1).replace(route+'(','matmul(')
        g.need(restored==rendered,'exact route and attribute reversal')
        # render itself reverses cache and quantize substitutions back to original.
        g.need('STAGE_MARK(' not in emitted and 'checked_' not in emitted,'no observer or oracle')
        functions.append(emitted)
        records.append(dict(name=name,route=route,cache=cached,sha256=g.sha(emitted.encode()),
                            exact_route_reverse=True,exact_cache_reverse=True))
    text='/* Generated from fixed upstream; original license retained. */\n'+'\n\n'.join(functions)+'\n'
    Path(output).write_text(text,encoding='utf-8')
    return dict(upstream_sha256=g.UPSTREAM_SHA,original_forward_sha256=g.sha(original.encode()),
                generated_sha256=g.sha(text.encode()),functions=records,trace=False,oracle_in_forward=False)
