"""Sideband identity audit only; never grants item19 or replaces SP1 checks."""
import re
import io
from collections import Counter

def rows(lines):
    for line in lines:
        if not line.startswith(('SCHED_', 'SP1_REDIRECT ')): continue
        if len(line)>4096: raise ValueError('oversize sideband record')
        line=re.sub(r':[ \t]+',':',line.rstrip('\r\n'))
        fields=dict(re.findall(r'(\w+)=[ \t]*([^ \t]+)',line))
        yield line.split()[0],fields

def ordered(lines):
    priorities={'SCHED_SCHEMA':0,'SCHED_UOP':1,'SP1_REDIRECT':2,'SCHED_EXU_IN':3,'SCHED_EXU_OUT':4,'SCHED_WB3':5}
    current=-1; batch=[]
    for kind,row in rows(lines):
        if kind not in priorities: raise ValueError('unknown record')
        cycle=int(row['cycle'])
        if cycle<current: raise ValueError('clock reversal')
        if cycle!=current:
            yield from sorted(batch,key=lambda x:(priorities[x[0]],int(x[1].get('slot','0'))))
            batch=[];current=cycle
        batch.append((kind,row))
        if len(batch)>64:raise ValueError('too many records per cycle')
    yield from sorted(batch,key=lambda x:(priorities[x[0]],int(x[1].get('slot','0'))))

def audit(text,robsize=48):
    return audit_stream(io.StringIO(text),robsize)

def audit_stream(lines,robsize=48,require_complete=True,response_sink=None):
    parents={}; mapped={}; pending={}; schemas=set(); responses=[]; generation=0; last=-1
    def need(ok,msg):
        if not ok:raise ValueError(msg)
    def num(row,k):
        need(k in row,'missing '+k);return int(row[k],0)
    def rob(s):
        f,v=map(int,s.split(':'));need(f in (0,1)and 0<=v<robsize,'bad ROB');return f*robsize+v
    counts=Counter(); response_count=0; peak_mapped=0
    for kind,row in ordered(lines):
        counts[kind]+=1;peak_mapped=max(peak_mapped,len(mapped))
        cycle=num(row,'cycle');need(cycle>=last,'clock reversal');last=cycle
        if kind=='SCHED_SCHEMA':
            need(num(row,'version')==1,'schema version');need(row['module']in ('ROB','EXU','WB3'),'unknown module')
            if row['module']=='ROB':need(num(row,'robsize')==robsize,'ROB size mismatch')
            if row['module']=='EXU':num(row,'exu')
            key=(row['module'],row.get('exu',''));need(key not in schemas,'reset/duplicate schema');schemas.add(key);continue
        need(schemas,'missing schema')
        if kind=='SP1_REDIRECT':
            pivot=rob(row['rob']);own=num(row,'self')
            for key in list(pending):
                age=(rob(key[0])-pivot)%(2*robsize)
                if 0<age<robsize or(age==0 and own):del pending[key]
            for rr in list(parents):
                age=(rob(rr)-pivot)%(2*robsize)
                if 0<age<robsize or(age==0 and own):
                    del parents[rr]
                    mapped={k:v for k,v in mapped.items()if k[0]!=rr}
            continue
        if kind=='SCHED_UOP':
            need(('ROB','')in schemas,'missing ROB schema')
            rr=row['rob'];rob(rr)
            if num(row,'first'):
                need(row['alloc']==rr,'allocation mismatch');need(not any(k[0]==rr for k in pending),'reuse live ROB');generation+=1;parents[rr]=generation
                mapped={k:v for k,v in mapped.items()if k[0]!=rr}
            need(rr in parents,'orphan split uop')
            key=(rr,parents[rr],num(row,'fu'),num(row,'pdest'))
            # Multiple unobserved microops may alias; reject ambiguity only if used.
            duplicate=key in mapped
            for f in ['pc','word','uop','op','psrc','srcType','last','vec','v0']:need(f in row,'missing '+f)
            mapped[key]=None if duplicate else dict(row);continue
        if kind in ('SCHED_EXU_IN','SCHED_EXU_OUT'):
            need(('EXU',row.get('exu',''))in schemas,'missing EXU schema')
            rr=row['rob'];need(rr in parents,'unknown ROB generation');key=(rr,parents[rr],num(row,'fu'),num(row,'pdest'))
            need(key in mapped,'unmapped FU identity');need(mapped[key]is not None,'ambiguous microop identity')
            for f in ['exu','vec','v0']:need(f in row,'missing '+f)
            need(all(num(row,f)==num(mapped[key],f)for f in ['vec','v0']),'write enable mismatch')
            if kind.endswith('_IN'):
                need(key not in pending,'duplicate accept');need(num(row,'op')==num(mapped[key],'op'),'wrong op');pending[key]=(cycle,num(row,'exu'))
            else:
                need(key in pending,'output without live accept');need(num(row,'exu')==pending[key][1],'wrong EXU')
                valid,ready,fire=(num(row,f)for f in ['valid','ready','fire']);need(valid==1 and ready in (0,1) and fire==valid*ready,'handshake mismatch')
                if fire:
                    response={'pc':mapped[key]['pc'],'accept':pending[key][0],'output':cycle,'key':key}
                    if response_sink is None:responses.append(response)
                    else:response_sink(response)
                    response_count+=1
                    del pending[key]
        elif kind=='SCHED_WB3':
            need(('WB3','')in schemas,'missing WB schema')
            hv,lv,hr,lr=(num(row,f)for f in ['hv','lv','hr','lr']);need(all(x in (0,1)for x in [hv,lv,hr,lr]),'invalid handshake bits')
            need(hr==1 and lr==int(not hv or not lv),'vector arbiter mismatch')
            for prefix,valid in [('h',hv),('l',lv)]:
                if not valid:continue
                rr=row[prefix+'rob'];need(rr in parents,'WB stale ROB')
                matches=[v for k,v in mapped.items()if k[0]==rr and k[1]==parents[rr]and k[3]==num(row,prefix+'d')and v is not None and num(v,'vec')==1]
                need(len(matches)==1,'WB ambiguous or unmapped identity')
            if hv:need(num(row,'hs')==1 and num(row,'hvec')==1,'nonvector high request')
            if lv:need(num(row,'ls')==1 and num(row,'lvec')==1,'nonvector low request')
            need(num(row,'ov')==int(bool(hv or lv)),'wrong output valid')
            if hv or lv:need(num(row,'od')==num(row,'hd'if hv else 'ld'),'wrong winner')
    need(counts['SCHED_EXU_IN']>0,'empty or incomplete stream')
    if require_complete:need(not pending,'incomplete lifecycle')
    return {'status':'SIDEBAND_IDENTITY_PASS_ONLY','responses':responses,'response_count':response_count,'counts':dict(counts),'pending_at_end':len(pending),'peak_mapped':peak_mapped,'schemas':[list(x)for x in sorted(schemas)],'item19_qualified':False}
