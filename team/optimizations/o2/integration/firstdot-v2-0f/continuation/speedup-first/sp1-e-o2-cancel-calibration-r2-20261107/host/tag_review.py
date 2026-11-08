"""Source-level independent method review of the limited tag delta, not another Agent."""
from pathlib import Path
import ast
from common import read,sha,need
N=Path(__file__).resolve().parent.parent

def review():
    c=read(N/'R1_EVIDENCE.json');old=Path(c['old_root'])
    src=(N/'runtime/negative_group.py').read_text();previous=(old/'runtime/negative_group.py').read_text()
    def funcs(s):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)}
    a,b=funcs(previous),funcs(src)
    need(set(a)==set(b),'no extra parser entry point')
    for name in ('vector_destination','bind_current_custom','validate_negative_group'):need(a[name]==b[name],'strict group algorithm unchanged '+name)
    pattern=next(ast.literal_eval(x.value.args[0]) for x in ast.parse(src).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INSTR_ROW' for t in x.targets))
    need(pattern.startswith('^') and pattern.endswith('$') and '.*' not in pattern and '[SDW]' in pattern,'bounded anchored tag grammar')
    need("need(not row['tag'],'current group skip/delayed tag cannot prove executed DiffTest')" in src,'current tagged group rejected')
    need("'historical_tags':[{'slot':x['slot'],'tag':x['tag']}" in src,'history tags recorded explicitly')
    producer=Path(c['producer']['path']);need(sha(producer)==c['producer']['sha256'],'producer source pin')
    t=producer.read_text();need("t |= 'S';" in t and "t |= 'D';" in t and ord('S')|ord('D')==ord('W'),'producer-defined S/D/W')
    need(read(N/'review/R1_OFFLINE_RESULT.json')['status']=='PASS_R1_REAL_LOG_OFFLINE_ONLY','whole actual log gate precedes target')
    return {'status':'PASS_TAG_SOURCE_REVIEW','method':'same Agent separate AST/producer-source method; not teammate or second-agent signoff','strict_functions_unchanged':3,'tag_contract':'historical exact S/D/W; current tagged group rejected','real_log_offline_only':True,'target_runs':0}
