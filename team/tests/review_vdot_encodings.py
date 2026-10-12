"""Conservative static neighbor-word check against supplied pinned decoder sources."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from generate_vdot_cases import exception_cases


def matches(word, bits):
    bits=bits.replace(' ','')
    if len(bits)!=32:
        raise ValueError('only 32-bit decoder patterns supported')
    mask=int(''.join('0' if b=='?' else '1' for b in bits),2)
    value=int(bits.replace('?','0'),2)
    return word & mask == value


def review(rocket, custom, nemu):
    local=Path(__file__).resolve().parents[2]/'src/main/scala/xiangshan/backend/decode'
    tables=[local/'DecodeUnit.scala',local/'VecDecoder.scala']
    text='\n'.join(p.read_text(encoding='utf-8') for p in tables)
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    used=set(re.findall(r'^\s*([A-Z][A-Z0-9_]*)\s*->',text,re.M))
    definitions={}
    sources=[rocket,custom,*local.rglob('*.scala')]
    for path in sources:
        for name,bits in re.findall(r'def\s+(\w+)\s*=\s*BitPat\("b([01?]{32})"\)',path.read_text(encoding='utf-8')):
            definitions.setdefault(name,set()).add(bits)
    missing=sorted(used-definitions.keys())
    neighbors=[c for c in exception_cases() if c['model_class']=='not-vdot']
    collisions=[]
    for c in neighbors:
        for name in used & definitions.keys():
            if any(matches(c['word'],bits) for bits in definitions[name]):
                collisions.append(dict(id=c['id'],table_name=name))
    raw=nemu.read_text(encoding='utf-8')
    main=raw.split('def_THelper(main) {',1)[1].split('return table_inv(s);',1)[0]
    patterns=re.findall(r'def_INSTR_(?:ID)?TAB\s*\(\s*"([01? ]+)"',main)
    nemu_matches=[c['id'] for c in neighbors if any(matches(c['word'],p) for p in patterns)]
    return dict(xs_table_names=len(used),resolved_names=len(used & definitions.keys()),
                unresolved_names=missing,neighbor_cases=len(neighbors),xs_collisions=collisions,
                nemu_main_pattern_matches=nemu_matches,
                scope='named literal BitPat table entries and NEMU 32-bit main dispatch; recheck after integration',
                source_sha256={str(p.relative_to(local)) if p.is_relative_to(local) else p.name:
                               hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[nemu]})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rocket',type=Path,required=True)
    parser.add_argument('--custom',type=Path,required=True)
    parser.add_argument('--nemu',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=review(args.rocket,args.custom,args.nemu)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},sort_keys=True))
    raise SystemExit(bool(report['unresolved_names'] or report['xs_collisions'] or report['nemu_main_pattern_matches']))
