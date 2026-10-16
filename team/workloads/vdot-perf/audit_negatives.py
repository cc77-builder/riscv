"""Apply labelled synthetic corruptions to actual accepted artifacts in temporary copies."""
from check import require
import argparse
import copy
import json
from pathlib import Path
import tempfile
import check as c


def main(a):
    manifest=json.loads((a.build/'data/manifest.json').read_text())
    evidence=c.verify(a.build,a.run)
    events=c.parse_events(c.read_text(a.run/'stderr.log'))
    kernels=c.elf_kernels(a.build/'vdot-perf.elf')
    outcomes=[]
    def reject(name,function):
        try:function()
        except (ValueError,KeyError) as error:outcomes.append(dict(name=name,status='EXPECTED_REJECTION',reason=str(error)))
        else:raise AssertionError('corruption accepted: '+name)
    for name,edit in [
        ('missing_last_retirement',lambda e:e['RETIRE'].pop()),
        ('missing_counter_sample',lambda e:e['CSR_SAMPLE'].pop()),
        ('wrong_rob_identity',lambda e:e['COUNTER_ENQUEUE'][0].update(rob=99)),
        ('sample_value_one_bit',lambda e:e['CSR_SAMPLE'][1].update(data=e['CSR_SAMPLE'][1]['data']^1)),
        ('wrong_retired_count',lambda e:e['RETIRE'][2].update(count=7)),
        ('counter_overtakes_previous_fence',lambda e:e['CSR_SAMPLE'][0].update(cycle=0)),
    ]:
        changed=copy.deepcopy(events);edit(changed)
        reject(name,lambda:c.trace_windows(changed,manifest,kernels))
    text=c.read_text(a.run/'stdout.log')
    for name,changed in [
        ('missing_summary',text.replace('T13_SUMMARY','MISSING_SUMMARY')),
        ('missing_scratch_control',text.replace('T13_SCRATCH_CONTROL allowed=1','T13_SCRATCH_CONTROL allowed=0')),
        ('missing_negative_control',text.replace('detected=6 expected=6','detected=5 expected=6')),
        ('duplicate_record',text+'\n'+next(x for x in text.splitlines() if x.startswith('T13_P '))+'\n'),
        ('bad_trap',text.replace('HIT GOOD TRAP','HIT BAD TRAP')),
    ]:reject(name,lambda:c.check_uart(changed,manifest,evidence['samples']))
    symbols,read=c.elf_data(a.build/'vdot-perf.elf');addr,length=symbols['cases'];blob=read(addr,length)
    original=(a.build/'vdot-perf.elf').read_bytes();offset=original.find(blob);require(offset>=0 and original.count(blob)==1, 'Validation failed: offset>=0 and original.count(blob)==1')
    with tempfile.TemporaryDirectory(prefix='t13-negative-') as tmp:
        for name,relative,mask in [('golden_high_bit',592+15,128),('scratch_mask',40,1),('stream_pointer',56,16)]:
            changed=bytearray(original);changed[offset+relative]^=mask
            path=Path(tmp)/(name+'.elf');path.write_bytes(changed)
            reject(name,lambda:c.check_compiled_cases(path,manifest))
    result=dict(status='PASS',synthetic_negative_tests=len(outcomes),controls=outcomes,scope='Synthetic mutations of temporary copies; no extra DUT executions and no edits to archived raw evidence.')
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','run','output'):p.add_argument('--'+n,type=Path,required=True)
    main(p.parse_args())
