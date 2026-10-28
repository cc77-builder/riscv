// O2 isolated real FU: ordered transaction queue, independent frozen arithmetic.
// Visibility deadlines account for an older stalled response; no DUT state drives the oracle.
#include "VVDotElasticFuTestTop.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
#include <deque>
#include <algorithm>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>

using Words = std::array<uint32_t, 4>;
struct Data { Words a{}, b{}, gold{}; };
struct Req {
  Data data;
  unsigned vl=8, ctrlVl=255, sew=0, lmul=0, start=0, vxrm=0, op=0;
  bool vill=false, vm=true, ta=false, ma=false, flag=false, v0=false;
  unsigned rob=0, dest=0;
  uint64_t tag=0;
  bool illegal() const { return vill || !vm || vl!=8 || sew || lmul || start || op; }
  uint32_t ctrl() const {
    return (uint32_t(vill)<<26)|(uint32_t(ma)<<25)|(uint32_t(ta)<<24)|(sew<<22)|
      (lmul<<19)|(uint32_t(vm)<<18)|(start<<10)|(ctrlVl<<2)|vxrm;
  }
};
struct Flush { bool valid=false, flag=false; unsigned value=0; bool self=false; };
struct Pending { Req req; uint64_t due; };
static void require(bool ok,const std::string& why) { if(!ok) throw std::runtime_error(why); }
static Words parse(const std::string& s) {
  require(s.size()==32 && s.find_first_not_of("0123456789abcdef")==std::string::npos,"bad hex");
  Words w{};
  for(unsigned i=0;i<4;i++) w[i]=uint32_t(std::stoul(s.substr(24-8*i,8),nullptr,16));
  return w;
}
static std::vector<Data> load(const char* file) {
  std::ifstream f(file); require(bool(f),"missing vectors");
  std::vector<Data> data; std::set<std::string> ids; unsigned d=0,r=0; std::string line;
  while(std::getline(f,line)) {
    std::istringstream row(line); std::string suite,id,a,b,g,extra;
    require(bool(row>>suite>>id>>a>>b>>g) && !(row>>extra),"malformed TSV");
    require(ids.insert(id).second,"duplicate vector");
    require(suite=="directed"||suite=="random","unknown suite");
    suite=="directed"?++d:++r;
    data.push_back({parse(a),parse(b),parse(g)});
  }
  require(f.eof() && d==22 && r==10000,"need frozen 22+10000 vectors"); return data;
}
static bool killed(const Req& q,Flush f) {
  if(!f.valid) return false;
  unsigned d=(unsigned(q.flag)*48+q.rob+96-unsigned(f.flag)*48-f.value)%96;
  require(d!=48,"ambiguous ROB window"); return d==0?f.self:d<48;
}
static Req request(const Data& d,unsigned i) {
  Req q; q.data=d; q.rob=i%48;q.flag=(i/48)%2;q.dest=i%160;q.v0=i%2;
  q.tag=UINT64_C(0xf123456789abcdef)^(UINT64_C(0x100000001)*i);
  q.ctrlVl=(i*17)%256;q.ta=(i>>1)&1;q.ma=(i>>2)&1;q.vxrm=i%4;return q;
}

class Bench {
  std::unique_ptr<VerilatedContext> ctx=std::make_unique<VerilatedContext>();
  std::unique_ptr<VVDotElasticFuTestTop> dut=std::make_unique<VVDotElasticFuTestTop>(ctx.get());
  bool injected=false;
 public:
  std::deque<Pending> pending;
  std::string fault,label="initial";
  uint64_t tick=0,accepted=0,responses=0,cancels=0,resets=0,overlaps=0,stalls=0;
  uint64_t full=0,partialKill=0,bothKill=0,resetCases=0,ii1=0,latency2=0;
  explicit Bench(std::string f):fault(std::move(f)) {}
  void check(bool ok,const std::string& why) const {
    require(ok,"case="+label+" tick="+std::to_string(tick)+" "+why);
  }
  void inject() { injected=true;std::cerr<<"O2_FU_INJECT "<<fault<<'\n'; }
  bool step(const Req& q,bool valid=false,bool ready=true,Flush f={},bool reset=false) {
    dut->clock=0;dut->reset=reset;dut->io_in_valid=valid;dut->io_out_ready=ready;
    for(unsigned i=0;i<4;i++) {
      dut->io_vs1[i]=q.data.a[i];dut->io_vs2[i]=q.data.b[i];
      dut->io_old_vd[i]=uint32_t(tick*7919+i);dut->io_mask[i]=uint32_t(~(tick+i));
    }
    dut->io_vl=q.vl;dut->io_ctrl_vl=q.ctrlVl;dut->io_vsew=q.sew;dut->io_vlmul=q.lmul;
    dut->io_vstart=q.start;dut->io_vill=q.vill;dut->io_vm=q.vm;dut->io_vta=q.ta;
    dut->io_vma=q.ma;dut->io_vxrm=q.vxrm;dut->io_op=q.op;dut->io_rob_flag=q.flag;
    dut->io_rob_value=q.rob;dut->io_pdest=q.dest;dut->io_write_v0=q.v0;dut->io_perf_tag=q.tag;
    dut->io_flush_valid=f.valid;dut->io_flush_flag=f.flag;dut->io_flush_value=f.value;dut->io_flush_self=f.self;
    dut->eval();ctx->timeInc(1);
    if(!reset) {
      check(dut->io_occupancy==pending.size(),"occupancy");
      check(bool(dut->io_r_valid)==(!pending.empty() && pending.front().due<=tick),"R presence");
      check(bool(dut->io_p_valid)==(pending.size()==2 || (!pending.empty() && pending.front().due>tick)),"P presence");
    }
    std::vector<bool> kills;
    for(auto& p:pending) kills.push_back(!reset && killed(p.req,f));
    bool ov=!reset && !pending.empty() && pending.front().due<=tick && !kills.front();
    bool actualValid=dut->io_out_valid;
    if(fault=="cancel" && !kills.empty() && kills.front() && !injected) {actualValid=true;inject();}
    if(actualValid!=ov) {
      if(!fault.empty() && injected) throw std::runtime_error("cancel");
      check(false,"output valid/kill/deadline");
    }
    bool ir=!reset && !f.valid && (pending.size()<2 || (ov&&ready));
    check(bool(dut->io_in_ready)==ir,"capacity ready");
    bool inf=ir&&valid,of=ov&&ready;
    if(ov) {
      const Req& old=pending.front().req;
      Words actual{};for(unsigned i=0;i<4;i++) actual[i]=dut->io_result[i];
      unsigned dest=dut->io_out_pdest;bool vw=dut->io_out_vec_wen,z=dut->io_out_v0_wen;
      if(inf && !injected) {
        if(fault=="identity"){dest^=1;inject();}
        if(fault=="wen"){vw=!vw;inject();}
        if(fault=="high"){actual[3]^=16;inject();}
      }
      if(actual!=(old.illegal()?Words{}:old.data.gold)) throw std::runtime_error("high");
      if(dest!=old.dest || bool(dut->io_out_rob_flag)!=old.flag || dut->io_out_rob_value!=old.rob ||
         dut->io_out_ctrl!=old.ctrl() || dut->io_out_perf_tag!=old.tag ||
         dut->io_out_rename_tag!=(old.tag^UINT64_C(0xf0e1d2c3b4a59687))) throw std::runtime_error("identity");
      if(vw!=(!old.illegal()&&!old.v0) || z!=(!old.illegal()&&old.v0)) throw std::runtime_error("wen");
      check(dut->io_out_exception==(old.illegal()?4U:0U),"exception identity");
      if(!ready)++stalls;
    }
    size_t before=pending.size();
    unsigned count=unsigned(std::count(kills.begin(),kills.end(),true));
    if(before==2)++full;
    if(before==2 && count==1)++partialKill;
    if(count==2)++bothKill;
    if(reset){resets+=pending.size();pending.clear();}
    else {
      const bool releaseFront=before && (kills[0]||of);
      std::deque<Pending> survivors;
      for(size_t i=0;i<before;i++) {
        if(kills[i]){++cancels;continue;}
        if(i==0 && of){++responses;continue;}
        Pending p=pending[i];
        if(i==1 && releaseFront)p.due=std::max(p.due,tick+1);
        survivors.push_back(p);
      }
      pending=survivors;
    }
    if(inf){check(pending.size()<2,"queue overflow");pending.push_back({q,tick+2});++accepted;}
    if(inf&&of)++overlaps;
    check(accepted==responses+cancels+resets+pending.size(),"conservation");
    dut->clock=1;dut->eval();ctx->timeInc(1);++tick;return inf;
  }
  void drain(const Req& noise){unsigned n=0;while(!pending.empty()){check(++n<16,"drain watchdog");step(noise);}}
  void finish(){check(pending.empty(),"pending at finish");dut->final();}
};
static void test(Bench& b,const std::vector<Data>& data) {
  Req noise=request(data[0],1000);
  b.step(noise,true,true,{},true);b.step(noise,true,true,{},true);
  b.label="frozen-10022-stream";
  unsigned next=0;uint64_t last=0,start=b.tick;
  while(next<data.size() || !b.pending.empty()) {
    Req q=next<data.size()?request(data[next],next):noise;
    auto before=b.responses;
    bool fire=b.step(q,next<data.size(),true);
    if(fire){if(next){b.check(b.tick-1==last+1,"II=1");++b.ii1;}last=b.tick-1;++next;}
    if(before==0 && b.responses==1){b.check(b.tick-1==start+2,"first latency2");++b.latency2;}
  }
  b.check(next==10022 && b.ii1==10021,"vector inventory/II coverage");
  // Mix legal/illegal/v0 requests, filled slots, input noise and result backpressure.
  b.label="mixed-invalid-backpressure";
  next=0;
  for(unsigned i=0;i<1200 || !b.pending.empty();++i) {
    Req q=request(data[next%data.size()],next+20000);
    switch(next%10){case 0:q.vl=7;break;case 1:q.sew=1;break;case 2:q.lmul=2;break;
      case 3:q.start=1;break;case 4:q.vill=true;break;case 5:q.vm=false;break;case 6:q.op=1;break;default:break;}
    if(b.step(q,i<1200,(i%13)>=8))++next;
  }
  // Fill two requests; acceptance order can be older/younger or younger/older.
  for(unsigned reverse=0;reverse<2;reverse++) for(unsigned wrap=0;wrap<2;wrap++)
  for(unsigned kind=0;kind<4;kind++) for(unsigned ready=0;ready<2;ready++) {
    b.label="partial-and-all-cancel";
    Req a=request(data[3],30000),c=request(data[9],30001);
    a.flag=false;a.rob=wrap?47:10;c.flag=wrap;c.rob=wrap?0:11;
    if(reverse)std::swap(a,c);
    b.check(b.step(a,true,false),"fill P");b.check(b.step(c,true,false),"fill P/R");
    for(unsigned n=0;n<3;n++)b.step(noise,true,false);
    Req older=reverse?c:a,younger=reverse?a:c;
    Flush f{};
    if(kind==0)f={true,younger.flag,younger.rob,true};
    if(kind==1)f={true,older.flag,older.rob,true};
    if(kind==2)f={true,younger.flag,younger.rob,false};
    if(kind==3)f={true,older.flag,older.rob,false};
    b.step(noise,true,ready,f);b.drain(noise);
  }
  // Occupancy 0/1(P)/1(R)/2, reset coincident with redirect and attempted traffic.
  for(unsigned shape=0;shape<4;shape++) for(unsigned flush=0;flush<2;flush++) {
    b.label="reset-occupancy";
    Req a=request(data[2],100),c=request(data[5],101);
    if(shape){b.step(a,true,false);if(shape==2)b.step(noise,false,false);if(shape==3)b.step(c,true,false);}
    Flush f{bool(flush),a.flag,a.rob,true};
    b.step(noise,true,false,f,true);++b.resetCases;b.step(noise);b.step(a,true);b.drain(noise);
  }
  b.label="random-control-20000";
  std::mt19937 rng(0x02e1a57);unsigned serial=0;
  for(unsigned i=0;i<20000;i++) {
    Req q=request(data[rng()%data.size()],serial);
    if(rng()%11==0)q.vl=7;
    Flush f{};
    if(!b.pending.empty() && rng()%23==0) {
      const Req& target=b.pending[rng()%b.pending.size()].req;
      f={true,target.flag,target.rob,bool(rng()%2)};
    }
    if(b.step(q,rng()%5!=0,rng()%4!=0,f,rng()%431==0))++serial;
  }
  b.drain(noise);
  b.check(b.full>0 && b.partialKill>0 && b.bothKill>0 && b.resetCases==8 && b.stalls>0,"coverage");
  b.finish();
}
int main(int argc,char** argv) {
  try {
    require(argc==2 || argc==3,"usage: binary vectors.tsv [identity|wen|high|cancel]");
    std::string fault=argc==3?argv[2]:"";
    require(fault.empty()||fault=="identity"||fault=="wen"||fault=="high"||fault=="cancel","unknown fault");
    Bench b(fault);auto data=load(argv[1]);test(b,data);
    if(!fault.empty()){std::cerr<<"O2_FU_FAULT_ESCAPED "<<fault<<'\n';return 3;}
    std::cout<<"O2_FU_PASS vectors="<<data.size()<<" cycles="<<b.tick<<" accepted="<<b.accepted
      <<" responses="<<b.responses<<" cancelled="<<b.cancels<<" reset_dropped="<<b.resets
      <<" overlaps="<<b.overlaps<<" stalls="<<b.stalls<<" full="<<b.full
      <<" partial_kill="<<b.partialKill<<" both_kill="<<b.bothKill<<" reset_cases="<<b.resetCases
      <<" ii1_intervals="<<b.ii1<<" latency2_probes="<<b.latency2<<"\n";
    return 0;
  } catch(const std::exception& e){std::cerr<<"O2_FU_FAIL "<<e.what()<<'\n';return 1;}
}
