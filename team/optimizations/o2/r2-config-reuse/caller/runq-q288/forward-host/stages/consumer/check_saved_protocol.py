"""Reject malformed saved-result JSON and exercise actual 64 KiB read boundaries."""
from pathlib import Path
import argparse
import importlib.util
import json

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('consumer_saved_json',HERE/'recheck_stream.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def check(output):
    r.need(not output.exists() and not output.is_relative_to(r.s.REPO),'fresh parser control output');output.mkdir(parents=True)
    valid=[]
    for length in (0,1,65520,65524,65528,65532,65535,65536,65537,131073):
        value={'padding':'香'+('x'*length),'before':1234567890123456789,
               'transactions':[{'seq':0,'field':-1234567890123456789},{'seq':1,'data':'边界'}],
               'after':True,'empty':None}
        valid.append(json.dumps(value,ensure_ascii=False,separators=(',',':')))
    valid.append(' \t\r\n{"transactions":[]}\n')
    invalid=[
        '{"transactions":[{},]}',
        '{"transactions":[],}',
        '{"before":1,}',
        '{"transactions":[] "after":1}',
        '{"transactions":[{} {}]}',
        '{"transactions":[],"transactions":[]}',
        '{"transactions":[],"after":1,"after":2}',
        '{"transactions":[]\u00a0}',
        '{"transactions":[{"seq":1}',
        '{"transactions":[]',
        '{"transactions":[]}garbage',
        '{"no_array":1}',
    ]
    count=dict(accepted=0,rejected=0)
    for index,text in enumerate(valid+invalid):
        path=output/f'case-{index:02d}.json';path.write_text(text,encoding='utf-8')
        reader=None
        try:
            reader=r.SavedProtocol(path);transactions=[]
            while True:
                try:transactions.append(reader.next())
                except StopIteration:break
            reader.finish();actual=dict(reader.summary,transactions=transactions)
        except ValueError:
            r.need(index>=len(valid),'valid fixed-shape JSON survives chunk boundary');count['rejected']+=1
        else:
            r.need(index<len(valid) and actual==json.loads(text),'only complete valid saved protocol accepted');count['accepted']+=1
        finally:
            if reader is not None:reader.close()
    result=dict(status='SAVED_PROTOCOL_JSON_BOUNDARY_AND_REJECTION_PASS',**count,source_sha256=r.sha(HERE/'recheck_stream.py'))
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(check(args.output.resolve()),indent=2))
