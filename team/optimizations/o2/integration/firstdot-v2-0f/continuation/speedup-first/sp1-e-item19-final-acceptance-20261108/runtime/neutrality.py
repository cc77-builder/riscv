"""Existing valid-data contract: compare every SP1/T13 field except invalid slot payloads."""
import re,json,hashlib

def effective_rows(text):
 result=[]
 for line in text.splitlines():
  if not line.startswith(('SP1_','T13_')):continue
  line=re.sub(r':[ \t]+',':',line);kind=line.split()[0];row=dict(re.findall(r'(\w+)=[ \t]*([^ \t]+)',line))
  if kind=='SP1_STATE':
   for valid,fields in [('pvalid',['prob','ppdest']),('rvalid',['rrob','rpdest'])]:
    if row[valid]=='0':
     for key in fields:row.pop(key)
  result.append((kind,row))
 return result

def compare(new,old):
 a,b=effective_rows(new),effective_rows(old)
 if a!=b:raise ValueError('effective SP1/T13 projection drift')
 return {'status':'PASS_EXACT_EFFECTIVE_SP1_T13','rows':len(a),'sha256':hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest(),'only_excluded':'prob/ppdest when pvalid=0; rrob/rpdest when rvalid=0; banner/timer raw file hash is provenance only'}
