"""Summarize only the fully verified current campaign."""
import json
from pathlib import Path
cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016');runs=cache/'runs'
completion=json.loads((runs/'completion.json').read_text());result=json.loads((runs/'analysis/result.json').read_text())
if completion['status']!='CURRENT_FULLCORE_REVALIDATION_PASS' or result['status']!='T13_FAIR_CYCLE_COMPARISON_PASS':raise ValueError('incomplete campaign')
groups=[]
for name in sorted({r['scenario'] for r in result['summary']}):
    rows=[r for r in result['summary'] if r['scenario']==name]
    groups.append(dict(scenario=name,configurations=len(rows),median_speedup_min=min(r['speedup_median'] for r in rows),median_speedup_max=max(r['speedup_median'] for r in rows)))
brief=dict(status=result['status'],runs=result['runs'],functional_calls=result['functional_calls'],windows=result['performance_windows'],paired_configurations=result['paired_configurations'],replay_identical=result['replay_identical'],scenario_ranges=groups,interpretation='RVV cycles / vdot cycles; range of configuration medians from four measured AB/BA rounds; no empty-window subtraction, not independent statistical samples, not PPA')
(runs/'analysis-brief.json').write_text(json.dumps(brief,indent=2)+'\n');print(json.dumps(brief,indent=2))
