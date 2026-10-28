#!/usr/bin/env python3
"""Check every used Liberty cell area against pinned physical LEF dimensions."""
import argparse
import json
from pathlib import Path
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--run', type=Path, required=True)
p.add_argument('--lef-areas', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
lef = json.loads(a.lef_areas.read_text())
report = json.loads((a.run/'result.json').read_text())
checks = {}
for n in lef:
    text = (a.run/n/'combined.lib').read_text()
    areas = {k:float(v) for k,v in re.findall(r'cell\s*\(\s*(\w+)\s*\)\s*\{.*?\barea\s*:\s*([0-9.eE+-]+)',text,re.S)}
    types = report['platforms'][n]['mapped_types']
    bad = [t for t in types if t not in lef[n]['area_um2'] or abs(areas[t]-lef[n]['area_um2'][t]) > 1e-5]
    checks[n] = {'checked_types':len(types), 'mismatches':bad, 'lef_sha256':lef[n]['lef_sha256']}
a.output.write_text(json.dumps(checks,indent=2)+'\n')
if any(row['mismatches'] for row in checks.values()): raise SystemExit('LEF area mismatch')
print(json.dumps(checks))
