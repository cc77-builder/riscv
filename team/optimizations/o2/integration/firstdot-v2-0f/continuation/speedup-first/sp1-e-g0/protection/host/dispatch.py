"""Explicit mode dispatch. No prefix rewriting or silent fallback."""
from pathlib import Path
import analyze
import legacy_o2


def analyze_mode(mode,text,require_complete=True):
    analyze.require(Path(analyze.__file__).resolve().parent == Path(__file__).resolve().parent, 'foreign SP1 module import')
    analyze.require(Path(legacy_o2.__file__).resolve().parent == Path(__file__).resolve().parent, 'foreign O2 module import')
    if mode=='sp1-p4':
        return analyze.analyze(text,require_complete=require_complete)
    if mode=='stable-0f':
        analyze.require('SP1_' not in text,'SP1 events in stable-0f mode')
        return legacy_o2.analyze(text,require_complete=require_complete)
    raise ValueError('unknown observer mode')
