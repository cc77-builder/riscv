// Real ExeUnit scoreboard: a transaction ledger, not an emulated divider or busy FSM.
#include "VVDotExuTestTop.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Words = std::array<uint32_t,4>;
static void check(bool ok,const std::string& why) { if(!ok) throw std::runtime_error(why); }
struct Data { Words a{},b{},gold{}; };
struct Req {
  Data data;
  unsigned kind=0,op=0,vl=8,sew=0,lmul=0,start=0,rob=0,dest=0;
  bool vill=false,vm=true,flag=false,v0=false;
  uint64_t tag=0;
  bool illegal() const { return kind==0 && (op || vl!=8 || sew || lmul || start || vill || !vm); }
};
struct Flush { bool valid=false,flag=false; unsigned rob=0; bool self=false; };
struct Pending { Req q; uint64_t at; bool seen=false; };
static bool killed(const Req& q,Flush f) {
  if(!f.valid) return false;
  unsigned age=(unsigned(q.flag)*48+q.rob+96-unsigned(f.flag)*48-f.rob)%96;
  check(age!=48,"ambiguous ROB window");return age==0?f.self:age<48;
}
static Words parse(const std::string& s) {
  check(s.size()==32 && s.find_first_not_of("0123456789abcdef")==std::string::npos,"bad hex");
  Words w{};for(unsigned i=0;i<4;i++)w[i]=uint32_t(std::stoul(s.substr(24-i*8,8),nullptr,16));return w;
}
static std::vector<Data> load(const char* path) {
  std::ifstream f(path);check(bool(f),"missing vectors");std::vector<Data> v;std::set<std::string> ids;
  std::string line;unsigned directed=0,random=0;
  while(std::getline(f,line)) {
    std::istringstream r(line);std::string suite,id,a,b,g,extra;
    check(bool(r>>suite>>id>>a>>b>>g) && !(r>>extra),"malformed TSV");
    check(ids.insert(id).second,"duplicate vector");check(suite=="directed"||suite=="random","suite");
    suite=="directed"?++directed:++random;v.push_back({parse(a),parse(b),parse(g)});
  }
  check(f.eof()&&directed==22&&random==10000,"need frozen 22+10000 vectors");return v;
}
static Req req(const Data& d,unsigned n,unsigned kind=0) {
  Req q;q.data=d;q.kind=kind;q.rob=n%48;q.flag=(n/48)%2;q.dest=n%160;q.v0=n%2;
  q.tag=UINT64_C(0xf123456789abcdef)^(UINT64_C(0x100000001)*n);
  if(kind) {
    q.sew=2;q.vl=4;q.op=kind==1?n%4:64;
    for(unsigned i=0;i<4;i++) {
      if(kind==1) {
        uint32_t a=(n*37+i*23)%100003+1,b=(n*701+i*199)%10000007;
        if(n%7==0)a=0;if(n%7==1){a=UINT32_MAX;b=0x80000000U;}
        if(n%3==0)b=uint32_t(0)-b;
        q.data.a[i]=a;q.data.b[i]=b;
        if(q.op&1) {
          int64_t sa=int32_t(a),sb=int32_t(b);
          q.data.gold[i]=a?uint32_t((q.op&2)?sb/sa:sb%sa):((q.op&2)?UINT32_MAX:b);
        } else q.data.gold[i]=a?((q.op&2)?b/a:b%a):((q.op&2)?UINT32_MAX:b);
      } else {
        // Exactly representable f32 division, independent host arithmetic oracle.
        float a=float(1U<<((n+i)%4)),b=float(int((n*17+i*7)%257)-128),g=b/a;
        std::memcpy(&q.data.a[i],&a,4);std::memcpy(&q.data.b[i],&b,4);std::memcpy(&q.data.gold[i],&g,4);
      }
    }
  }
  return q;
}
class Bench {
  std::unique_ptr<VerilatedContext> ctx=std::make_unique<VerilatedContext>();
  std::unique_ptr<VVDotExuTestTop> dut=std::make_unique<VVDotExuTestTop>(ctx.get());
  bool injected=false;
 public:
  unsigned mode;std::string fault;bool strictIdle;
  std::optional<Pending> pending;
  uint64_t tick=0,accepted=0,responses=0,cancels=0,resets=0,overlaps=0,stalls=0;
  std::array<uint64_t,3> counts{},clocks{},idleClocks{},minLatency{9999,9999,9999},maxLatency{};
  Bench(unsigned m,std::string f,bool idle):mode(m),fault(f),strictIdle(idle) {
    // Establish reset low before asserting it; gated asynchronous domains need
    // a real reset edge, not only Verilator's initial signal assignment.
    dut->clock=0;dut->reset=0;dut->eval();
  }
  void inject() {injected=true;std::cerr<<"PARENT_INJECT "<<fault<<'\n';}
  bool step(const Req& q,bool valid=false,bool ready=true,Flush f={},bool reset=false,bool idleSample=false) {
    check(tick<200000,"global cycle budget exceeded");
    dut->clock=0;dut->reset=reset;dut->io_in_valid=valid;dut->io_out_ready=ready;
    dut->io_kind=q.kind;dut->io_op=q.op;
    for(unsigned i=0;i<4;i++) {
      dut->io_vs1[i]=q.data.a[i];dut->io_vs2[i]=q.data.b[i];
      dut->io_old_vd[i]=uint32_t(tick*7919+i);dut->io_mask[i]=UINT32_MAX;
    }
    dut->io_vl=q.vl;dut->io_ctrl_vl=q.vl;dut->io_vsew=q.sew;dut->io_vlmul=q.lmul;
    dut->io_vstart=q.start;dut->io_vill=q.vill;dut->io_vm=q.vm;dut->io_vta=0;dut->io_vma=0;dut->io_vxrm=0;
    dut->io_rob_flag=q.flag;dut->io_rob_value=q.rob;dut->io_pdest=q.dest;dut->io_write_v0=q.v0;dut->io_perf_tag=q.tag;
    dut->io_flush_valid=f.valid;dut->io_flush_flag=f.flag;dut->io_flush_value=f.rob;dut->io_flush_self=f.self;
    dut->eval();
    const bool kill=pending && killed(pending->q,f);
    bool ov=dut->io_out_valid;
    if(fault=="cancel"&&kill&&!reset&&!injected){ov=true;inject();}
    if(!reset) {
      check(bool(dut->io_busy)==bool(pending),"parent busy disagrees with ledger");
      // Production dividers cancel at the edge; their raw response may remain
      // visible on that redirect cycle. VDot suppresses it combinationally.
      check(!(ov&&(!pending||(kill&&pending->q.kind==0))),"unsolicited or canceled vdot output");
      if(pending&&!kill) {
        if(pending->q.kind==0)check(ov==(tick>=pending->at+(mode?2:3)),"vdot latency/backpressure");
        if(pending->seen)check(ov,"response disappeared under backpressure");
        check(tick-pending->at<256,"bounded divider progress");
      }
      unsigned fv=dut->io_fu_valid;
      check(!fv || !(fv&(fv-1)),"shared output is not one hot");
      check(bool(fv)==ov,"parent/child output validity");
    }
    const bool of=ov&&ready&&!reset&&!kill;
    const bool inf=bool(dut->io_in_ready)&&valid&&!reset;
    if(!reset) {
      const bool overlapAllowed=mode==2&&pending&&pending->q.kind==0&&q.kind==0&&of&&!f.valid;
      if(pending)check(!inf||overlapAllowed,"illegal shared-unit overlap");
      if(mode==2) {
        if(f.valid)check(!dut->io_in_ready,"O1 redirect input suppression");
        else if(pending)check(bool(dut->io_in_ready)==overlapAllowed,"O1 response handoff ready");
      }
      check(dut->io_fu_accept==(inf?(1U<<q.kind):0U),"parent/selected child acceptance mismatch parent="+
        std::to_string(inf)+" children="+std::to_string(dut->io_fu_accept));
    }
    if(ov&&!reset) {
      check(bool(pending),"output without pending");const Req& old=pending->q;
      Words actual{},vec{},v0{};for(unsigned i=0;i<4;i++){actual[i]=dut->io_result[i];vec[i]=dut->io_vec_result[i];v0[i]=dut->io_v0_result[i];}
      unsigned dest=dut->io_out_pdest;bool vw=dut->io_out_vec_wen,zw=dut->io_out_v0_wen;
      if(of&&inf&&!injected) {
        if(fault=="identity"){dest^=1;inject();}if(fault=="wen"){vw=!vw;inject();}
        if(fault=="high"){vec[3]^=1;inject();}
      }
      Words gold=old.illegal()?Words{}:old.data.gold;
      check(actual==gold&&vec==gold&&v0==gold,"full128 shared/vec/v0 result");
      check(dest==old.dest&&bool(dut->io_out_rob_flag)==old.flag&&dut->io_out_rob_value==old.rob,"old identity");
      check(vw==(!old.illegal()&&!old.v0)&&zw==(!old.illegal()&&old.v0),"write class");
      check(dut->io_out_exception==(old.illegal()?4U:0U),"exception");
      check(dut->io_out_fflags==0,"unexpected FP flags");
      check(dut->io_out_perf_tag==old.tag&&dut->io_out_rename_tag==(old.tag^UINT64_C(0xf0e1d2c3b4a59687)),"old debug identity");
      if(!pending->seen) {
        auto age=tick-pending->at;auto k=old.kind;minLatency[k]=std::min(minLatency[k],age);maxLatency[k]=std::max(maxLatency[k],age);
        pending->seen=true;
      }
      if(!ready)++stalls;
    }
    if(reset){if(pending)++resets;pending.reset();}
    else if(kill){++cancels;pending.reset();}
    else if(of){++responses;pending.reset();}
    if(inf){check(!pending,"multiple outstanding");pending=Pending{q,tick,false};++accepted;++counts[q.kind];}
    if(of&&inf)++overlaps;
    check(accepted==responses+cancels+resets+unsigned(bool(pending)),"transaction conservation");
    dut->clock=1;dut->eval();
    for(unsigned k=0;k<3;k++)if(dut->io_fu_clocks&(1U<<k)){++clocks[k];if(idleSample)++idleClocks[k];}
    if(idleSample&&strictIdle)check(!dut->io_fu_clocks,"canceled FU clock stayed enabled during idle");
    ctx->timeInc(1);++tick;return inf;
  }
  void drain(const Req& noise){unsigned n=0;while(pending){check(++n<256,"drain timeout");step(noise);}}
  void send(const Req& q){unsigned n=0;while(!step(q,true)){check(++n<256,"accept timeout");}}
  void finish(){check(!pending,"pending at finish");if(!fault.empty())check(injected,"fault not exercised");dut->final();}
};
static void test(Bench& b,const std::vector<Data>& data) {
  Req noise=req(data[7],777);b.step(noise,false,true,{},true);b.step(noise,false,true,{},true);
  // Continuous numeric vectors: exact parent II, then backpressure with changing candidate identity.
  unsigned next=0;uint64_t last=0;
  while(next<data.size()||b.pending) {
    Req q=next<data.size()?req(data[next],next):noise;
    uint64_t at=b.tick;
    if(b.step(q,next<data.size())){if(next)check(at-last==(b.mode==2?2:b.mode==1?3:4),"saturated parent II");last=at;++next;}
  }
  for(unsigned n=0;n<300;n++) {
    Req q=req(data[n],20000+n,n%3);b.send(q);
    for(unsigned i=0;i<40;i++)b.step(req(data[i],50000+i,(n+1)%3),true,false);
    b.drain(noise);
  }
  // Illegal vdot mixed with legal requests, including same-edge illegal/legal handoff.
  next=0;
  while(next<128||b.pending) {
    Req q=req(data[next%data.size()],30000+next);if(next%2)q.vl=7;
    if(b.step(q,next<128))++next;
  }
  // All three real FUs: cancel in flight and while response is backpressured; observe clock closure.
  for(unsigned kind=0;kind<3;kind++)for(unsigned age: {1U,2U,60U})for(unsigned variant=0;variant<4;variant++) {
    Req q=req(data[6],40000+variant,kind);q.rob=variant%2?0:47;q.flag=variant%2;
    b.send(q);for(unsigned i=1;i<age;i++)b.step(noise,false,false);
    Flush f{true,q.flag,q.rob,true};
    if(variant>=2){unsigned older=(unsigned(q.flag)*48+q.rob+95)%96;f.flag=older/48;f.rob=older%48;f.self=false;}
    b.step(noise,false,false,f);for(unsigned i=0;i<16;i++)b.step(noise,false,true,{},false,true);
    b.send(q);b.drain(noise); // wake from the same gate after cancellation
  }
  // Non-killing redirects at response, both output ready values, wrap-around ages.
  for(unsigned k=0;k<3;k++)for(unsigned r=0;r<2;r++) {
    Req q=req(data[k],60001+k,k);q.rob=47;q.flag=false;b.send(q);
    for(unsigned i=0;i<60;i++)b.step(noise,false,false);
    b.step(noise,b.mode==2,r,Flush{true,true,0,false});b.drain(noise);
  }
  // Reset recovery with actual gate activity; no forced-open clock/reset surrogate.
  for(unsigned k=0;k<3;k++)for(unsigned age: {1U,60U}) {
    Req q=req(data[k],70000+k,k);b.send(q);for(unsigned i=1;i<age;i++)b.step(noise,false,false);
    b.step(noise,false,false,{},true);b.step(noise,false,true,{},true);b.send(q);b.drain(noise);
  }
  std::mt19937 rng(0x4f315041);
  for(unsigned n=0;n<12000;n++) {
    Req q=req(data[rng()%data.size()],80000+n,rng()%3);Flush f{};
    if(b.pending&&rng()%37==0)f={true,b.pending->q.flag,b.pending->q.rob,true};
    b.step(q,!f.valid&&rng()%5!=0,rng()%4!=0,f);
  }
  b.drain(noise);b.finish();
  check(b.counts[1]>100&&b.counts[2]>100&&b.cancels>=36&&b.resets==6,"coverage counts");
  check(b.mode==2?b.overlaps>10000:b.overlaps==0,"overlap coverage");
  std::cout<<"VFEX4_PARENT_PASS mode="<<b.mode<<" accepted="<<b.accepted<<" responses="<<b.responses
    <<" canceled="<<b.cancels<<" reset="<<b.resets<<" overlap="<<b.overlaps<<" stalls="<<b.stalls<<'\n';
  for(unsigned k=0;k<3;k++)std::cout<<"FU kind="<<k<<" accepted="<<b.counts[k]<<" latency="<<b.minLatency[k]<<":"<<b.maxLatency[k]
    <<" clocks="<<b.clocks[k]<<" canceled_idle_clocks="<<b.idleClocks[k]<<'\n';
}
int main(int argc,char** argv) {
  try {
    check(argc>=3&&argc<=5,"usage: parent_test vectors.tsv mode [fault|-] [strict-idle]");
    unsigned mode=std::stoul(argv[2]);check(mode<=2,"mode");std::string fault=argc>=4?argv[3]:"";if(fault=="-")fault.clear();
    Bench b(mode,fault,argc==5&&std::string(argv[4])=="strict-idle");
    try {test(b,load(argv[1]));}catch(const std::exception& e){throw std::runtime_error("tick="+std::to_string(b.tick)+" "+e.what());}
    return 0;
  }catch(const std::exception& e){std::cerr<<"VFEX4_PARENT_FAIL "<<e.what()<<'\n';return 1;}
}
