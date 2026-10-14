#!/usr/bin/env python3
"""Record pinned native dependency inputs, including files hidden by Git ignores."""
import argparse
import json
from pathlib import Path

from artifact_guard import audit_repo, require


def audit(target, evidence):
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'check.json').unlink(missing_ok=True)
    output = evidence / 'dependency-sources.json'
    output.unlink(missing_ok=True)
    binding = json.loads((target / 'build/source-binding.json').read_bytes())
    sources = {}
    for name, revision in binding['modules'].items():
        sources[name] = audit_repo(target / name, revision,
                                 source_roots=('src', 'macros/src', 'include', 'lib-include', 'source', 'generator'))
    require(sources, 'No pinned dependencies')
    output.write_bytes((json.dumps(dict(sources=sources, failures={}), sort_keys=True, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(dict(status='CORE_DEPENDENCY_SOURCE_PASS', modules=len(sources), files=sum(map(len, sources.values()))), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    audit(args.target.resolve(), args.evidence.resolve())
