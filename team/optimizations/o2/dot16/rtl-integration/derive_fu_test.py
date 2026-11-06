"""Derive a dot16-specific FU test from the unchanged, pinned O2 test.

The original test body, frozen vectors, scoreboard and observation faults are
retained. Only the legal op/VL predicate changes; new stimuli are appended after
the original coverage assertions. This does not modify any repository input.
"""
from pathlib import Path
import argparse
import hashlib
import json

BASE_SHA256 = 'd4dc81c7c206f1d395856023b01a32e76bf1dbef957b9023f8debc0a549bc01d'
OLD_ILLEGAL = '  bool illegal() const { return vill || !vm || vl!=8 || sew || lmul || start || op; }'
NEW_ILLEGAL = '  bool illegal() const { return vill || !vm || sew || lmul || start || !((op==0 && vl==8) || (op==1 && vl==16)); }'

HELPERS = r'''
// Independent scalar arithmetic over the architectural source bytes.
static Words dot16_scalar_gold(const Data& d, unsigned terms) {
  int32_t sum=0;
  for(unsigned i=0;i<terms;i++) {
    const uint32_t ua=(d.a[i/4]>>(8*(i%4)))&255U;
    const uint32_t ub=(d.b[i/4]>>(8*(i%4)))&255U;
    const int32_t a=ua>=128 ? int32_t(ua)-256 : int32_t(ua);
    const int32_t b=ub>=128 ? int32_t(ub)-256 : int32_t(ub);
    sum+=a*b;
  }
  return Words{uint32_t(sum),0,0,0};
}
static Data dot16_uniform(int al,int bl,int ah,int bh) {
  Data d;
  for(unsigned i=0;i<16;i++) {
    const uint32_t a=uint8_t(i<8?al:ah),b=uint8_t(i<8?bl:bh);
    d.a[i/4]|=a<<(8*(i%4));d.b[i/4]|=b<<(8*(i%4));
  }
  // Every Data keeps the original eight-lane gold convention.
  d.gold=dot16_scalar_gold(d,8);return d;
}
static std::vector<Data> dot16_directed_data() {
  std::vector<Data> out{
    dot16_uniform(-128,-128,-128,-128),
    dot16_uniform(-128,127,-128,127),
    dot16_uniform(127,127,127,127),
    dot16_uniform(0,0,-128,-128),
    dot16_uniform(1,1,-128,-128),
    dot16_uniform(-128,127,127,-128),
    dot16_uniform(0,0,0,0),
    dot16_uniform(-128,-128,-128,127)
  };
  for(unsigned lane=0;lane<16;lane++) for(bool negative:{false,true}) {
    Data d;d.a[lane/4]=uint32_t(0x80)<<(8*(lane%4));
    d.b[lane/4]=uint32_t(negative?0x7f:0x80)<<(8*(lane%4));
    d.gold=dot16_scalar_gold(d,8);out.push_back(d);
  }
  return out;
}
'''

EXTRA = r'''
static Req dot16_request(const Data& d,unsigned serial,bool wide) {
  Req q=request(d,serial);
  if(wide){q.op=1;q.vl=16;q.data.gold=dot16_scalar_gold(d,16);}
  return q;
}
static void dot16_extra(Bench& b,const std::vector<Data>& data) {
  b.check(b.pending.empty(),"dot16 extra starts drained");
  unsigned serial=100000;
  const auto directed=dot16_directed_data();
  b.check(dot16_scalar_gold(directed[0],16)==Words{262144,0,0,0},"dot16 positive 20-bit corner");
  b.check(dot16_scalar_gold(directed[1],16)==Words{uint32_t(-260096),0,0,0},"dot16 negative corner");
  b.check(dot16_scalar_gold(directed[3],16)==Words{131072,0,0,0} && directed[3].gold==Words{},"upper-half witness");
  Req noise=dot16_request(directed[0],serial++,true);
  uint64_t legalCompared=0,illegalCompared=0,extraPairs=0,extraResets=0;

  // Each frozen input is used unchanged once as dot8 and once as dot16.
  // This also replaces old P while old R responds on every unblocked cycle.
  b.label="dot16-mixed-frozen-II1";
  const auto accepted0=b.accepted,responses0=b.responses,start=b.tick;
  size_t next=0;uint64_t last=0,intervals=0,firstLatency=0;
  while(next<2*data.size() || !b.pending.empty()) {
    const bool valid=next<2*data.size();
    Req q=valid?dot16_request(data[next/2],serial+unsigned(next),bool(next&1)):noise;
    const auto before=b.responses;
    const bool fire=b.step(q,valid,true);
    if(fire){if(next){b.check(b.tick-1==last+1,"mixed dot8/dot16 II1");++intervals;}last=b.tick-1;++next;}
    if(before==responses0 && b.responses==responses0+1){firstLatency=b.tick-1-start;b.check(firstLatency==2,"mixed first latency2");}
    b.check(b.tick-start<2*data.size()+8,"mixed stream watchdog");
  }
  b.check(b.accepted-accepted0==2*data.size() && b.responses-responses0==2*data.size(),"mixed arithmetic completion count");
  b.check(intervals+1==2*data.size(),"mixed II inventory");
  legalCompared+=b.responses-responses0;serial+=unsigned(2*data.size());

  // Distinct upper and lower halves expose lane duplication and stale products.
  b.label="dot16-directed-halves-extremes";
  const auto directedBefore=b.responses;
  for(const auto& d:directed) for(bool wide:{true,false}) {
    Req q=dot16_request(d,serial++,wide);
    b.check(b.step(q,true,false),"directed accepts empty P");
    for(unsigned delay=0;delay<5;delay++)b.step(noise,false,false);
    // Invalid input noise must not alter the held response.
    b.drain(noise);b.step(noise);
  }
  legalCompared+=b.responses-directedBefore;

  b.label="dot16-illegal-and-v0";
  const auto illegalBefore=b.responses;
  for(unsigned flags=0;flags<4;flags++) for(unsigned kind=0;kind<10;kind++) {
    Req q=dot16_request(directed[kind%directed.size()],serial++,true);
    q.ta=flags&1;q.ma=flags>>1;q.v0=flags&1;
    switch(kind){
      case 0:q.vl=8;break;case 1:q.vl=0;break;case 2:q.sew=1;break;
      case 3:q.lmul=1;break;case 4:q.start=1;break;case 5:q.vill=true;break;
      case 6:q.vm=false;break;case 7:q.op=2;q.vl=8;break;
      case 8:q.op=2;q.vl=16;break;case 9:q.op=0;q.vl=16;break;
    }
    b.check(q.illegal(),"directed illegal inventory");
    b.check(b.step(q,true),"illegal accepts empty P");b.drain(noise);b.step(noise);
  }
  illegalCompared=b.responses-illegalBefore;b.check(illegalCompared==40,"illegal completion count");

  struct Relation{unsigned r,p,at;bool self;unsigned mask;};
  const Relation relations[]={
    {8,12,10,false,2},{12,8,10,false,1},{12,14,10,false,3},{8,6,10,false,0},
    {10,8,10,false,0},{10,8,10,true,1},{8,10,10,true,2},{10,10,10,true,3},
    {47,49,48,false,2},{49,47,48,false,1},{95,1,0,false,2},{1,95,0,false,1}
  };
  b.label="dot16-mixed-RobPtr-cancel-and-backpressure";
  for(unsigned modes=0;modes<4;modes++)for(const auto& rel:relations)for(bool ready:{false,true}){
    Req a=dot16_request(directed[4],serial++,modes&1),p=dot16_request(directed[7],serial++,modes&2);
    a.flag=rel.r/48;a.rob=rel.r%48;p.flag=rel.p/48;p.rob=rel.p%48;
    b.check(b.step(a,true,false),"mixed fill first");b.check(b.step(p,true,false),"mixed fill second");
    for(unsigned delay=0;delay<3;delay++)b.step(noise,true,false);
    const Flush flush{true,bool(rel.at/48),rel.at%48,rel.self};
    b.check(unsigned(killed(a,flush))+2*unsigned(killed(p,flush))==rel.mask,"mixed ROB relation oracle");
    const auto cancelsBefore=b.cancels;
    b.check(!b.step(noise,true,ready,flush),"redirect never accepts new op");
    const unsigned wanted=unsigned(bool(rel.mask&1))+unsigned(bool(rel.mask&2));
    b.check(b.cancels-cancelsBefore==wanted,"mixed exact cancel count");
    b.drain(noise);b.step(noise);++extraPairs;
  }

  b.label="dot16-reset-after-mixed-occupancy";
  for(unsigned modes=0;modes<4;modes++)for(unsigned shape=0;shape<4;shape++){
    Req a=dot16_request(directed[0],serial++,modes&1),p=dot16_request(directed[1],serial++,modes&2);
    if(shape){b.step(a,true,false);if(shape==2)b.step(noise,false,false);if(shape==3)b.step(p,true,false);}
    const auto occupied=b.pending.size(),dropped=b.resets,cancelled=b.cancels;
    b.step(noise,true,true,{true,a.flag,a.rob,true},true);
    b.check(b.pending.empty() && b.resets-dropped==occupied && b.cancels==cancelled,"mixed reset dominates cancel");
    ++b.resetCases;++extraResets;b.step(noise);
    b.check(b.step(a,true),"mixed reset recovery acceptance");b.drain(noise);b.step(noise);
  }
  b.check(b.pending.empty() && extraPairs==96 && extraResets==16,"dot16 additional control inventory");
  std::cout<<"DOT16_FU_EXTRA_PASS schema=1 paired_vectors="<<data.size()
    <<" directed_inputs="<<directed.size()<<" legal_compared="<<legalCompared
    <<" illegal_compared="<<illegalCompared<<" mixed_ii1_intervals="<<intervals
    <<" first_latency="<<firstLatency<<" mixed_cancel_pairs="<<extraPairs
    <<" additional_reset_cases="<<extraResets<<'\n';
}
'''


DISABLED_EXTRA = r'''
static void dot16_disabled_extra(Bench& b,const std::vector<Data>& data) {
  b.check(b.pending.empty(),"disabled probe starts drained");
  const auto d=dot16_directed_data();Req noise=request(data[0],91000);
  const auto before=b.responses;unsigned serial=92000;
  b.label="dot16-disabled-new-op-rejected";
  for(unsigned flags=0;flags<8;flags++)for(unsigned op:{1U,2U}){
    Req q=request(d[0],serial++);q.op=op;q.vl=op==1?16:8;
    q.ta=flags&1;q.ma=(flags>>1)&1;q.v0=(flags>>2)&1;
    b.check(q.illegal(),"disabled unsupported op oracle");
    b.check(b.step(q,true,false),"disabled probe accepts empty P");
    for(unsigned n=0;n<3;n++)b.step(noise,false,false);
    b.drain(noise);b.step(noise);
  }
  b.check(b.responses-before==16 && b.pending.empty(),"disabled reject completion count");
  std::cout<<"DOT16_FU_DISABLED_EXTRA_PASS schema=1 new_op_rejected=8 unknown_op_rejected=8"<<'\n';
}
'''


def derive(source: Path, output: Path, feature: int = 1):
    if feature not in (0, 1):
        raise ValueError('feature must be exactly zero or one')
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_SHA256:
        raise ValueError('original O2 FU test identity mismatch')
    if output.exists() or output.resolve() == source.resolve():
        raise ValueError('derived file must be new and separate from the original')
    text = raw.decode('utf-8')
    edits = ([(OLD_ILLEGAL, NEW_ILLEGAL)] if feature else []) + [
        ('struct Req {', HELPERS + '\nstruct Req {'),
        ('static void test(Bench& b,const std::vector<Data>& data) {',
         (EXTRA if feature else DISABLED_EXTRA) + '\nstatic void test(Bench& b,const std::vector<Data>& data) {'),
        ('  b.finish();\n}\nint main',
         ('  dot16_extra(b,data);' if feature else '  dot16_disabled_extra(b,data);')
         + '\n  b.finish();\n}\nint main'),
    ]
    for before, after in edits:
        if text.count(before) != 1:
            raise ValueError('ambiguous or absent original replacement anchor')
        text = text.replace(before, after, 1)
    restored = text
    for before, after in reversed(edits):
        if restored.count(after) != 1:
            raise ValueError('ambiguous inverse replacement')
        restored = restored.replace(after, before, 1)
    if restored.encode('utf-8') != raw:
        raise ValueError('derivation did not preserve the complete original')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding='utf-8', newline='\n')
    result = dict(schema=1, input_path=str(source), input_sha256=BASE_SHA256,
                  output_path=str(output), output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  edits=len(edits), original_reconstructed_byte_exact=True,
                  source_modified=False, feature_required='VDOT_DOT16=' + str(feature),
                  architectural_aliases_tested=False, parent_tested=False,
                  old_observation_faults_retained=True)
    if source.read_bytes() != raw:
        raise ValueError('original source changed during derivation')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--record', type=Path, required=True)
    p.add_argument('--feature', type=int, choices=(0, 1), default=1)
    a = p.parse_args()
    if a.record.exists() or a.record.resolve() == a.output.resolve():
        raise SystemExit('record must be new')
    result = derive(a.source, a.output, a.feature)
    a.record.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
