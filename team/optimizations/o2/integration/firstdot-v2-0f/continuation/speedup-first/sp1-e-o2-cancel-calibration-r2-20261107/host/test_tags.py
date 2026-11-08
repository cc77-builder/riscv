"""R2 complete real negative log and bounded tag/guard mutation controls; no targets."""
from pathlib import Path
import json,re,unittest
import adapter,negative_group
from common import read,save,sha,need
from test_delta import Delta
N=Path(__file__).resolve().parent.parent

def raw_real():
    c=read(N/'R1_EVIDENCE.json')
    for x in c['files']:
        p=Path(x['path']);need(p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],'R1 evidence drift')
    rec=read(c['record']['path'])
    need(rec['exit_code']==1 and rec['resource_ok'] and rec['cleanup_ok'],'old real resource/exit receipt')
    for s in ('stdout','stderr'):need(c[s]['sha256']==rec['raw_sha256'][s],'raw matches R1 measurement')
    return Path(c['stdout']['path']).read_text()+Path(c['stderr']['path']).read_text()

def row_at(text,slot):
    rows=[s for s in text.splitlines() if s.startswith(f'[{slot:02d}] commit ')]
    need(len(rows)==1,'exact real historical row')
    return rows[0]

class Tags(unittest.TestCase):
    def test_01_complete_R1_real_log(self):
        text=raw_real();r=adapter.collect(text,'bit100',1)
        self.assertEqual(r['status'],'NEW_GUARD_BIT100_LOG_PASS')
        self.assertFalse(r['target_run_qualified'])
        g=r['fault']['current_group']
        self.assertEqual((g['cmtcnt'],g['instruction_ring_tail']),(1,7))
        self.assertEqual(g['historical_tags'],[{'slot':10,'tag':'S'},{'slot':13,'tag':'S'}])
        self.assertEqual([(x['slot'],x['tag']) for x in g['instructions']],[(7,'')])
        self.assertEqual(r['fault']['final_vd_writer']['result'],0xfffffdec)
        save(N/'review/R1_OFFLINE_RESULT.json',{'status':'PASS_R1_REAL_LOG_OFFLINE_ONLY','collector':r,'raw_evidence':read(N/'R1_EVIDENCE.json'),'original_run_status':'FAIL_RETAINED','new_target_processes':0,'new_target_qualification':False,'scope':'Entire immutable stdout+stderr processed by new parser; original FAIL/locks unchanged, no current-boot claim for old receipts'})
        print('REAL_LOG_OFFLINE_PASS original_FAIL_retained',flush=True)

    def test_02_producer_legal_history_tags(self):
        t=raw_real()
        for slot in (0,10):
            original=row_at(t,slot);base=original.removesuffix(' (S)')
            for tag in ('','S','D','W'):
                label=f'history_slot{slot}_tag{tag or "none"}'
                with self.subTest(control=label):
                    revised=base+(' ('+tag+')' if tag else '')
                    changed=t if revised==original else Delta.mutate_once(t,original,revised)
                    r=adapter.collect(changed,'bit100',1)
                    tags={x['slot']:x['tag'] for x in r['fault']['current_group']['historical_tags']}
                    self.assertEqual(tags.get(slot,''),tag)
                    self.assertEqual(r['fault']['current_group']['instructions'][0]['tag'],'')
                    print('TAG_POSITIVE_PASS '+label,flush=True)

    def test_03_tag_negative_controls(self):
        t=raw_real();row=row_at(t,0)
        suffixes=[('unknown',' (Q)'),('lowercase',' (s)'),('combined_text',' (SD)'),('duplicate',' (S) (S)'),('two_tags',' (S) (D)'),('tag_before_queue',' (S) (05)'),('queue_after_tag',' (05) (S) (06)'),('tail_garbage',' (S) junk'),('bad_queue_width',' (005) (S)'),('missing_close',' (S')]
        for label,suffix in suffixes:
            with self.subTest(control=label):
                bad=Delta.mutate_once(t,row,row+suffix)
                with self.assertRaisesRegex(ValueError,'malformed or ambiguous instruction ring row'):adapter.collect(bad,'bit100',1)
                print('TAG_NEGATIVE_PASS '+label,flush=True)
        current=row_at(t,7);self.assertTrue(current.endswith(' <--'))
        for tag in ('S','D','W'):
            with self.subTest(control='current_group_'+tag):
                bad=Delta.mutate_once(t,current,current[:-4]+' ('+tag+') <--')
                with self.assertRaisesRegex(ValueError,'current group skip/delayed tag'):adapter.collect(bad,'bit100',1)
                print('TAG_NEGATIVE_PASS current_group_'+tag,flush=True)

    def test_04_real_guard_binding_negative_controls(self):
        t=raw_real();history=row_at(t,0);current=row_at(t,7)
        refs=re.findall(r'\bv0[ \t]*: 0x0000000000000000_00000000fffffdec',t)
        self.assertEqual(len(refs),1)
        changes=[
            ('history_uint8',history,history.replace(' dst 00 ',' dst 256 ',1)),
            ('guard_ELF_word',current,current.replace('inst 0294000b','inst 0294080b',1)),
            ('zero_group_count','commit group [09]: pc 0080000278 cmtcnt 1 <--','commit group [09]: pc 0080000278 cmtcnt 0 <--'),
            ('missing_history_row',history+'\n',''),
            ('duplicate_history_row',history,history+'\n'+history),
            ('wrong_bit','right= 0x0000001000000000','right= 0x0000000800000000'),
            ('full128_corruption',refs[0],refs[0].replace('0x0000000000000000_','0x0000000000000001_',1))]
        for label,old,new in changes:
            with self.subTest(control=label):
                bad=Delta.mutate_once(t,old,new)
                with self.assertRaises(ValueError):adapter.collect(bad,'bit100',1)
                print('REAL_GUARD_NEGATIVE_PASS '+label,flush=True)

if __name__=='__main__':unittest.main(verbosity=2)
