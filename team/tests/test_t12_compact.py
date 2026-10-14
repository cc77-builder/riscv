"""Synthetic negative checks for lossless plan coverage; never DUT evidence."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from generate_t12 import generate
spec=importlib.util.spec_from_file_location('compact',Path(__file__).resolve().parents[1]/'scripts/check_t12_compact.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class Compact(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.data=Path(self.tmp.name)/'data';generate(self.data);self.m,self.rows=c.load(self.data)
 def tearDown(self):self.tmp.cleanup()
 def fixture(self,start,count):
  bits=bytearray((len(self.m['schedule'])+7)//8)
  lines=['Difftest enabled',f'T12R_BEGIN start={start} limit={count}','T12_CONTROLS high96=1 preserved=1 csr=1']
  for seq in range(start,start+count):
   bits[seq//8]|=1<<(seq%8)
   if self.rows[self.m['schedule'][seq]['id']]['kind']=='perf':lines.append(f'T12R_PERF seq={seq} cy=100,200 ir=100,150')
  return '\n'.join(lines+[f'T12R_END executed={count} bits={bits.hex()}','HIT GOOD TRAP'])
 def reject(self,text,start=0,count=190,rc=0):
  with self.assertRaises(ValueError):c.check(text,self.data,start,count,rc)
 def test_whole_and_slices(self):
  whole=c.check(self.fixture(0,190),self.data,0,190,0)
  r=c.aggregate([whole],self.data);self.assertEqual(r['unique_identities'],190);self.assertEqual(len(r['metrics']),27);self.assertEqual(len(r['pairs']),12)
  slices=[c.check(self.fixture(i,min(13,190-i)),self.data,i,min(13,190-i),0) for i in range(0,190,13)]
  self.assertEqual(c.aggregate(slices,self.data),r)
  for broken in (slices[:-1],slices+[slices[0]],list(reversed(slices))):
   with self.assertRaises(ValueError):c.aggregate(broken,self.data)
 def test_every_bit_of_bitmap(self):
  log=self.fixture(0,190);bits=bytearray.fromhex(log.split('bits=')[1].splitlines()[0])
  for bit in range(192):
   wrong=bytearray(bits);wrong[bit//8]^=1<<(bit%8)
   self.reject(log.replace(bits.hex(),wrong.hex()))
 def test_no_hash_can_substitute_for_checks(self):
  log=self.fixture(0,190)
  self.reject(log.replace('bits=','hash='));self.reject(log.replace('executed=190','executed=189'))
 def test_missing_duplicate_reordered_completion(self):
  log=self.fixture(0,190)
  for marker in ('Difftest enabled','T12_CONTROLS high96=1 preserved=1 csr=1','HIT GOOD TRAP'):
   self.reject(log.replace(marker,''));self.reject(log+'\n'+marker)
  self.reject('HIT GOOD TRAP\n'+log.replace('HIT GOOD TRAP',''))
 def test_limits_exit_and_failures(self):
  log=self.fixture(0,190)
  for marker in ('EXCEEDING CYCLE/INSTR LIMIT','SOME SIGNAL STOPS THE PROGRAM','FAIL','ABORT'):
   self.reject(log+'\n'+marker)
  for rc in (1,124,-15):self.reject(log,rc=rc)
 def test_perf_order_and_missing(self):
  log=self.fixture(0,190);line=next(x for x in log.splitlines() if x.startswith('T12R_PERF'))
  self.reject(log.replace(line,''));self.reject(log.replace(line,line+'\n'+line));self.reject(log.replace('cy=100,200','cy=100,100',1))
 def test_pair_mismatch(self):
  r=c.check(self.fixture(0,190),self.data,0,190,0);r['metrics'][1]['dots']+=1
  with self.assertRaises(ValueError):c.aggregate([r],self.data)
 def test_slice_bounds(self):
  for start,count in ((-1,1),(190,1),(0,0),(0,191)):
   self.reject(self.fixture(0,190),start,count)
if __name__=='__main__':unittest.main()
