// Candidate FU test only. Uses the existing real VDotFuTestTop adapter.
// The scoreboard is deadline/transaction based, not a copy of the RTL state machine.
#include "VVDotFuTestTop.h"
#include "verilated.h"
#include <array>
#include <cstdint>
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
  std::unique_ptr<VVDotFuTestTop> dut=std::make_unique<VVDotFuTestTop>(ctx.get());
  std::string fault; bool injected=false;
 public:
  std::optional<Pending> pending;
  uint64_t tick=0,accepted=0,responses=0,cancels=0,resets=0,overlaps=0,stalls=0;
  explicit Bench(std::string f):fault(std::move(f)) {}
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
    dut->eval();
    const bool kill=pending && killed(pending->req,f);
    const bool ov=pending && tick>=pending->due && !kill && !reset;
    const bool ir=(!pending || (ov && ready)) && !f.valid && !reset;
    bool actualV=dut->io_out_valid;
    if(fault=="cancel" && kill && !reset && !injected) { actualV=true; inject(); }
    require(actualV==ov,"output valid/kill/latency");require(bool(dut->io_in_ready)==ir,"input ready");
    const bool of=ov&&ready, inf=ir&&valid;
    if(ov) {
      // Inspect the OLD complete output before replacing the pending transaction.
      const Req& old=pending->req; Words actual{};for(unsigned i=0;i<4;i++)actual[i]=dut->io_result[i];
      unsigned dest=dut->io_out_pdest; bool vw=dut->io_out_vec_wen,z=dut->io_out_v0_wen;
      if(inf && !injected) {
        if(fault=="identity") { dest^=1;inject(); }
        if(fault=="wen") { vw=!vw;inject(); }
        if(fault=="high") { actual[3]^=16;inject(); }
      }
      require(actual==(old.illegal()?Words{}:old.data.gold),"full128 result");
      require(dest==old.dest && bool(dut->io_out_rob_flag)==old.flag && dut->io_out_rob_value==old.rob,"old identity");
      require(vw==(!old.illegal()&&!old.v0) && z==(!old.illegal()&&old.v0),"old write enables");
      require(dut->io_out_exception==(old.illegal()?4U:0U),"exception");
      require(dut->io_out_ctrl==old.ctrl(),"old vector config");
      require(dut->io_out_perf_tag==old.tag && dut->io_out_rename_tag==(old.tag^UINT64_C(0xf0e1d2c3b4a59687)),"old debug identity");
      if(!ready)++stalls;
    }
    if(reset) { if(pending)++resets;pending.reset(); }
    else if(kill) { ++cancels;pending.reset(); }
    else if(of) { ++responses;pending.reset(); }
    if(inf) { require(!pending,"multiple in flight");pending=Pending{q,tick+2};++accepted; }
    if(of&&inf)++overlaps;
    require(accepted==responses+cancels+resets+unsigned(pending.has_value()),"conservation");
    dut->clock=1;dut->eval();ctx->timeInc(1);++tick;return inf;
  }
  void inject() {injected=true;std::cerr<<"O1_INJECT "<<fault<<'\n';}
  void drain(const Req& noise) {
    unsigned n=0;while(pending){require(++n<12,"drain timeout");step(noise,false,true);}
  }
  void finish() {require(!pending,"pending at finish");dut->final();}
};
static void test(Bench& b,const std::vector<Data>& data) {
  Req noise=request(data[7],777);b.step(noise,false,true,{},true);b.step(noise,false,true,{},true);
  size_t next=0;unsigned held=0;const unsigned delays[]={0,1,2,7};uint64_t last=0;
  while(next<data.size() || b.pending) {
    Req q=next<data.size()?request(data[next],unsigned(next)):noise;
    bool ready=true;if(b.pending && b.tick>=b.pending->due){ready=held==0;if(held)--held;}
    auto before=b.tick;
    if(b.step(q,next<data.size(),ready)) {
      if(next) require(before-last==2+delays[(next-1)%4],"candidate II");
      last=before;held=delays[next%4];++next;
    }
    require(b.tick<140000,"stream watchdog");
  }
  require(b.responses==10022 && b.overlaps==10021,"missing arithmetic/overlap coverage");
  // Alternate legal/illegal and vec/v0 requests across same-cycle handoffs.
  unsigned serial=20000; uint64_t initial=b.overlaps;unsigned sent=0;
  while(sent<96 || b.pending) {
    Req q=request(data[(sent*17)%data.size()],serial+sent);
    if(sent%2) {
      switch((sent/2)%8) {case 0:q.vl=7;break;case 1:q.sew=1;break;case 2:q.lmul=2;break;
        case 3:q.start=1;break;case 4:q.vill=true;break;case 5:q.vm=false;break;
        case 6:q.op=1;break;case 7:q.vl=0;break;}
    }
    if(b.step(q,sent<96,true))++sent;
  }
  require(b.overlaps-initial==95,"missing legal/illegal handoff coverage");serial+=96;
  struct Relation {bool rf;unsigned rv;bool ff;unsigned fv;bool self;bool kill;};
  const Relation rel[]={{0,12,0,10,0,1},{0,8,0,10,0,0},{0,10,0,10,0,0},{0,10,0,10,1,1},
    {1,1,0,47,0,1},{0,47,1,1,0,0},{0,1,1,47,0,1},{1,47,0,1,0,0}};
  for(auto x:rel)for(unsigned age:{1U,2U,9U})for(bool ready:{false,true}) {
    Req q=request(data[3],serial++);q.flag=x.rf;q.rob=x.rv;Flush f{true,x.ff,x.fv,x.self};
    require(killed(q,f)==x.kill,"directed kill oracle");require(b.step(q,true),"initial accept");
    for(unsigned i=1;i<age;i++)b.step(noise,true,false);
    require(!b.step(noise,true,ready,f),"accepted during redirect");b.drain(noise);
    require(b.step(request(data[7],serial++),true),"recovery accept");b.drain(noise);
  }
  for(unsigned age:{1U,2U,9U}) {
    require(b.step(request(data[3],serial++),true),"accept before reset");
    for(unsigned i=1;i<age;i++)b.step(noise,true,false);
    require(!b.step(noise,true,true,{},true),"accept during reset");b.drain(noise);
  }
  std::mt19937 rng(0x20261018);
  for(unsigned i=0;i<10000;i++) {
    Req q=request(data[rng()%data.size()],serial++);if(rng()%9==0)q.vl=7;Flush f{};
    if(rng()%13==0) {
      unsigned pos=b.pending?unsigned(b.pending->req.flag)*48+b.pending->req.rob:0;
      unsigned at=(pos+96+(rng()%25)-12)%96;f={true,bool(at/48),at%48,bool(rng()%2)};
    }
    b.step(q,rng()%4!=0,rng()%3!=0,f,rng()%211==0);
  }
  b.drain(noise);for(unsigned i=0;i<8;i++)b.step(noise);
  require(b.cancels>0 && b.resets>0 && b.stalls>0,"missing control coverage");b.finish();
}
int main(int argc,char** argv) {
  if(argc<2||argc>3){std::cerr<<"usage: handoff_test vectors.tsv [identity|wen|high|cancel]\n";return 2;}
  try {
    std::string fault=argc==3?argv[2]:"";
    require(fault.empty()||fault=="identity"||fault=="wen"||fault=="high"||fault=="cancel","unknown fault");
    auto data=load(argv[1]);Bench b(fault);test(b,data);
    // An injected fault that survives the scoreboard is a gate failure, never an
    // expected DUT rejection. Keep its status distinct from caught violations.
    if(!fault.empty()) {
      std::cerr<<"O1_FU_FAULT_ESCAPED "<<fault<<'\n';return 3;
    }
    std::cout<<"O1_FU_ONLY_PASS latency=2 ii=2 accepted="<<b.accepted<<" responses="<<b.responses
      <<" cancelled="<<b.cancels<<" reset_dropped="<<b.resets<<" handoffs="<<b.overlaps
      <<" stalls="<<b.stalls<<" parent_tested=0 fullcore_tested=0\n";return 0;
  }catch(const std::exception& e){std::cerr<<"O1_FU_FAIL "<<e.what()<<'\n';return 1;}
}
