"""Exact tuple/list representation adapter for the frozen phased certificate."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util

HERE=Path(__file__).resolve().parent
ORIGINAL_SHA='9107271e4d16dc0a3b0ae23478037612b403b71837be9c835f2d2d35f4635557'
CONTRACT_SHA='c7bdb9ad066b597a702f15e3cc4791313b9f9a21d681451a66538487ddfcff80'
spec=importlib.util.spec_from_file_location('phased_archive_json_original',HERE/'archive.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
e,g=legacy.e,legacy.g
g.require(g.sha(HERE/'archive.py')==ORIGINAL_SHA,'unchanged original phased archive adapter')
BASE_TOOLS=legacy.tools()
EXPECTED=((8,8),(4,32),(8,8),(4,32))

def json_certificate(result):
    certificate=result['phased_certificate'];phases=certificate['mode_phases']
    g.require(type(phases) is list and len(phases)==4 and
        all(type(pair) is tuple and len(pair)==2 and all(type(v) is int for v in pair) for pair in phases)
        and tuple(phases)==EXPECTED,'exact four frozen tuple-valued mode phases')
    # Copy only the two containers needed to replace this one field. Other
    # result values are passed unchanged to the original strict cache check.
    return dict(result,phased_certificate=dict(certificate,mode_phases=[list(pair) for pair in phases]))

def verification(repo,build):return json_certificate(e.verification(repo,build))

CONTEXT=SimpleNamespace(**vars(legacy.CONTEXT));CONTEXT.verification=verification

def tools():
    for rel,pin in BASE_TOOLS.items():g.require(g.sha(e.ROOT/rel)==pin,'frozen original auditor '+rel)
    contract=HERE/'ARCHIVE-JSON-CONTRACT.md'
    g.require(g.sha(contract)==CONTRACT_SHA,'exact JSON representation contract')
    return dict(BASE_TOOLS,**{Path(__file__).resolve().relative_to(e.ROOT).as_posix():g.sha(__file__),
        contract.relative_to(e.ROOT).as_posix():CONTRACT_SHA})

def bound():return e.adapt(legacy,CONTEXT=CONTEXT,tools=tools,__file__=__file__)

def pack(build,run,out):
    with bound():return legacy.pack(build,run,out)

def audit_snapshot(archive,out):
    with bound():return legacy.audit_snapshot(archive,out)

def main():
    with bound():return legacy.main()

if __name__=='__main__':main()
