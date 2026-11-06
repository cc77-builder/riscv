#!/usr/bin/env python3
"""Derive a new, reversible parent campaign without editing frozen inputs."""
import hashlib
from pathlib import Path

PARENT_SHA256 = 'c691558f7c53433b212efe0c81d902abdfab7128257143cb329366c7032e952f'
OLD_PREDICATE = '  bool illegal() const { return kind==0 && (vill || !vm || vl!=8 || sew || lmul || start || op); }'
NEW_PREDICATE = '  bool illegal() const { return kind==0 && (vill || !vm || sew || lmul || start || !((op==0 && vl==8) || (op==1 && vl==16))); }'
HELPER_ANCHOR = 'static void test(Bench& b,const std::vector<Data>& data){'
HOOK_ANCHOR = '  b.label="clock-recovery";for(unsigned kind=0;kind<3;kind++)b.one(sample(data,kind,serial++));'


def derive(source, fragment, output, feature):
    if feature not in (0, 1):
        raise ValueError('feature must be 0 or 1')
    raw = Path(source).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_SHA256:
        raise ValueError('frozen parent source identity mismatch')
    extra = Path(fragment).read_text()
    if extra.count('@DOT16_FEATURE@') != 1:
        raise ValueError('feature placeholder must be unique')
    extra = extra.replace('@DOT16_FEATURE@', str(feature))
    edits = [(HELPER_ANCHOR, extra + '\n' + HELPER_ANCHOR),
             (HOOK_ANCHOR, '  dot16_parent_extra(b,data,serial);\n' + HOOK_ANCHOR)]
    if feature:
        edits.insert(0, (OLD_PREDICATE, NEW_PREDICATE))
    text = raw.decode()
    for before, after in edits:
        if text.count(before) != 1:
            raise ValueError('non-unique parent derivation anchor')
        text = text.replace(before, after, 1)
    restored = text
    for before, after in reversed(edits):
        if restored.count(after) != 1:
            raise ValueError('non-unique inverse parent anchor')
        restored = restored.replace(after, before, 1)
    if restored.encode() != raw:
        raise ValueError('full original campaign could not be reconstructed')
    if Path(output).exists():
        raise ValueError('derived output already exists')
    Path(output).write_text(text)
    return dict(schema=1, feature=feature, edits=len(edits),
                original_sha256=PARENT_SHA256,
                original_reconstructed_byte_exact=True,
                fragment_sha256=hashlib.sha256(Path(fragment).read_bytes()).hexdigest(),
                derived_sha256=hashlib.sha256(text.encode()).hexdigest())
