// Real production O2 VFEX4 + ClockGate scoreboard.
// Fault modes modify C++ observations ONLY; they are not hardware mutations.

#include "VVDotElasticParentTestTop.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <limits>
#include <memory>
#include <optional>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using Words = std::array<uint32_t, 4>;
using Perf = std::array<uint32_t, 19>; // 577 valid bits; bit 576 is eliminatedMove.
template <typename T> static std::string perfHex(const T& p) {
  std::ostringstream out;out<<std::hex<<std::setfill('0');
  for(auto i=p.rbegin();i!=p.rend();++i)out<<std::setw(8)<<*i;
  return out.str();
}
static uint64_t perf64(const Perf& p,unsigned field) {
  return uint64_t(p[2*field])|(uint64_t(p[2*field+1])<<32);
}
struct Failure : std::runtime_error {
  std::string category;
  Failure(std::string c, std::string detail) : std::runtime_error(detail), category(c) {}
};
static void need(bool ok, const std::string& category, const std::string& detail) {
  if (!ok) throw Failure(category, detail);
}
struct Data { Words a{}, b{}, gold{}; };
struct Req {
  Data data;
  unsigned kind=0, vl=8, ctrlVl=255, sew=0, lmul=0, start=0, vxrm=0, op=0;
  unsigned rob=0, dest=0, fflags=0;
  bool vill=false, vm=true, ta=false, ma=false, flag=false, v0=false;
  uint64_t tag=0;
  Perf perf{};
  int walk=-1;
  bool walkZero=false;
  bool illegal() const { return kind==0 && (vill || !vm || vl!=8 || sew || lmul || start || op); }
  uint32_t ctrl() const {
    return (uint32_t(vill)<<26)|(uint32_t(ma)<<25)|(uint32_t(ta)<<24)|(sew<<22)|
      (lmul<<19)|(uint32_t(vm)<<18)|(start<<10)|(ctrlVl<<2)|vxrm;
  }
};
struct Flush { bool valid=false, flag=false; unsigned value=0; bool self=false; };
struct Pending {
  Req req; uint64_t accepted=0, seq=0; bool seen=false;
  std::vector<uint32_t> vpu, perf;
};
template <size_t N> static std::vector<uint32_t> snapshot(const VlWide<N>& x) {
  std::vector<uint32_t> a(N);for(size_t i=0;i<N;i++)a[i]=x[i];return a;
}
struct Cycle { bool in=false, out=false, visible=false; unsigned killed=0,clocks=0; };
static Words parse(const std::string& s) {
  need(s.size()==32 && s.find_first_not_of("0123456789abcdef")==std::string::npos,"input","bad hex");
  Words w{};
  for (unsigned i=0;i<4;i++) w[i]=uint32_t(std::stoul(s.substr(24-8*i,8),nullptr,16));
  return w;
}
static std::vector<Data> load(const char* file) {
  std::ifstream f(file); need(bool(f),"input","missing vectors");
  std::vector<Data> data; std::set<std::string> ids; unsigned d=0,r=0; std::string line;
  while (std::getline(f,line)) {
    std::istringstream row(line); std::string suite,id,a,b,g,extra;
    need(bool(row>>suite>>id>>a>>b>>g) && !(row>>extra),"input","malformed TSV");
    need(ids.insert(id).second,"input","duplicate vector");
    need(suite=="directed"||suite=="random","input","unknown suite");
    suite=="directed"?++d:++r; data.push_back({parse(a),parse(b),parse(g)});
  }
  need(f.eof() && d==22 && r==10000,"input","need frozen 22+10000 vectors"); return data;
}
static bool killed(const Req& q, Flush f) {
  if (!f.valid) return false;
  unsigned d=(unsigned(q.flag)*48+q.rob+96-unsigned(f.flag)*48-f.value)%96;
  need(d!=48,"input","ambiguous ROB window"); return d==0?f.self:d<48;
}
static Req identify(Req q, unsigned serial) {
  q.rob=serial%48; q.flag=(serial/48)%2; q.dest=serial%160; q.v0=serial%2;
  q.tag=UINT64_C(0xf123456789abcdef)^(UINT64_C(0x100000001)*serial);
  // SplitMix64 supplies different full-width values for all nine time/checkpoint
  // fields. This is stimulus, not an arithmetic/RTL oracle.
  uint64_t seed=UINT64_C(0x2026102500010000)^serial;
  for(unsigned field=0;field<9;field++){
    seed+=UINT64_C(0x9e3779b97f4a7c15);uint64_t z=seed;
    z=(z^(z>>30))*UINT64_C(0xbf58476d1ce4e5b9);
    z=(z^(z>>27))*UINT64_C(0x94d049bb133111eb);z^=z>>31;
    q.perf[2*field]=uint32_t(z);q.perf[2*field+1]=uint32_t(z>>32);
  }
  q.perf[18]=serial&1;
  q.ctrlVl=(serial*17)%256; q.vxrm=serial%4;
  if (q.kind==0) { q.ta=(serial>>1)&1; q.ma=(serial>>2)&1; }
  return q;
}
static Req dot(const Data& d, unsigned serial) { Req q; q.data=d; return identify(q,serial); }
// Explicit architectural corner cases avoid host signed-overflow/zero-divide UB.
static uint32_t int_gold(uint32_t a, uint32_t b, unsigned op) {
  const bool sign=op&1, quotient=op&2;
  if (!a) return quotient?UINT32_MAX:b;
  if (sign) {
    int64_t n=(b&0x80000000U)?int64_t(b)-INT64_C(0x100000000):b;
    int64_t d=(a&0x80000000U)?int64_t(a)-INT64_C(0x100000000):a;
    if (n==INT32_MIN && d==-1) return quotient?uint32_t(INT32_MIN):0;
    return uint32_t(quotient?n/d:n%d);
  }
  return quotient?b/a:b%a;
}
static Req idiv(unsigned op, unsigned serial, uint32_t seed=0) {
  Req q; q.kind=1; q.sew=2; q.vl=4; q.op=op;
  if (op&1) {
    q.data.a={3,3,UINT32_MAX,0}; q.data.b={17,uint32_t(-17),uint32_t(INT32_MIN),INT32_MAX};
  } else {
    q.data.a={2,3,0,0}; q.data.b={UINT32_MAX,0x80000000U,19,0};
  }
  if (seed) { // deterministic varied finite divisors, independent scalar oracle
    for (unsigned i=0;i<4;i++) {
      q.data.a[i]=((seed>>(i*5))&255)+1;
      q.data.b[i]=(seed*UINT32_C(2654435761))^(UINT32_C(0x10293847)*(i+1));
    }
  }
  for (unsigned i=0;i<4;i++) q.data.gold[i]=int_gold(q.data.a[i],q.data.b[i],op);
  return identify(q,serial);
}
static Req fdiv(unsigned which, unsigned serial) {
  Req q; q.kind=2; q.sew=2; q.vl=4; q.op=0;
  // Four distinct lanes and signs. Every result is exact binary32; no host FP oracle.
  q.data.b={0x41000000,0xc1000000,0x40c00000,0x00000000};
  q.data.a={0x40000000,0x40000000,0x40400000,0x40000000};
  q.data.gold={0x40800000,0xc0800000,0x40000000,0x00000000};
  if (which%3==1) {
    q.data.a[0]=q.data.a[1]=0;
    q.data.gold[0]=0x7f800000; q.data.gold[1]=0xff800000; q.fflags=8;
  } else if (which%3==2) {
    q.data.b={0x3f800000,0x00000000,0x80000000,0x41800000};
    q.data.a={0x40000000,0x40800000,0x40800000,0xc0000000};
    q.data.gold={0x3f000000,0x00000000,0x80000000,0xc1000000};
  }
  return identify(q,serial);
}
static Req sample(const std::vector<Data>& data, unsigned kind, unsigned serial) {
  if (kind==1) return idiv(serial%4,serial,serial%5==0?serial:0);
  if (kind==2) return fdiv(serial%3,serial);
  return dot(data[serial%data.size()],serial);
}

class Bench {
  std::unique_ptr<VerilatedContext> ctx=std::make_unique<VerilatedContext>();
  std::unique_ptr<VVDotElasticParentTestTop> dut=std::make_unique<VVDotElasticParentTestTop>(ctx.get());
  bool injected=false;
  std::ofstream metadata;
  std::set<uint64_t> live, ended;
  std::optional<std::pair<uint64_t,std::vector<uint32_t>>> held;
 public:
  std::string fault,label="initial";
  std::optional<Pending> p,r,div;
  uint64_t tick=0,accepted=0,responses=0,cancels=0,resets=0,overlaps=0,stalls=0,groups=0,moves=0;
  uint64_t fullCycles=0,retireWithPSurviving=0,zeroTeResets=0,emptyZeroTeResets=0;
  uint64_t killPOnly=0,killROnly=0,killBoth=0,resetBoth=0,redirects=0,resetCases=0,idleClockSamples=0;
  uint64_t pAcceptWhileRBlocked=0,fullBlocked=0,cancelIdleClockOn=0;
  std::array<uint64_t,3> accepts{},responds{},kills{},drops{},rawKilled{},latMin{9999,9999,9999},latMax{},latSamples{},clockEdges{},waits{};
  std::array<uint64_t,9> directedPairs{};
  uint64_t perfInputs=0,perfObservations=0,walkOnes=0,walkZeroes=0;
  explicit Bench(std::string f,const std::string& path):fault(std::move(f)) {
    if(!path.empty()){
      need(!std::ifstream(path).good(),"input","metadata output already exists");
      metadata.open(path);need(bool(metadata),"input","cannot create metadata output");
      metadata<<"R3_PERF schema=1 bits=577\n";
    }
  }
  void check(bool ok,const std::string& category,const std::string& why) const {
    need(ok,category,"case="+label+" tick="+std::to_string(tick)+" "+why);
  }
  bool active() const {return bool(p)||bool(r)||bool(div);}
  unsigned occupancy() const {return unsigned(bool(p))+unsigned(bool(r));}
  void inject() {injected=true;std::cerr<<"O2_PARENT_INJECT "<<fault<<'\n';}
  bool selectFault(const char* name,bool condition=true) {
    if(fault==name && condition && !injected){inject();return true;}return false;
  }
  void terminal(const Pending& x,unsigned reason) {
    check(live.erase(x.seq)==1 && ended.insert(x.seq).second,"conservation","duplicate or unknown terminal seq");
    if(metadata.is_open())metadata<<"E cycle="<<tick<<" seq="<<x.seq<<" reason="<<reason<<'\n';
    if(reason==0){++responses;++responds[x.req.kind];
      if(x.req.walk>=0){if(x.req.walkZero)++walkZeroes;else ++walkOnes;}
    }
    if(reason==1){++cancels;++kills[x.req.kind];}
    if(reason==2){++resets;++drops[x.req.kind];}
  }
  Cycle step(const Req& q,bool valid=false,bool ready=true,Flush f={},bool reset=false,bool te=false) {
    dut->clock=0;dut->reset=reset;dut->io_test_enable=te;
    dut->io_in_valid=valid;dut->io_out_ready=ready;dut->io_kind=q.kind;
    for(unsigned i=0;i<4;i++){
      dut->io_vs1[i]=q.data.a[i];dut->io_vs2[i]=q.data.b[i];
      dut->io_old_vd[i]=uint32_t(tick*7919+i);dut->io_mask[i]=uint32_t(~(tick+i));
    }
    dut->io_vl=q.vl;dut->io_ctrl_vl=q.ctrlVl;dut->io_vsew=q.sew;dut->io_vlmul=q.lmul;
    dut->io_vstart=q.start;dut->io_vill=q.vill;dut->io_vm=q.vm;dut->io_vta=q.ta;
    dut->io_vma=q.ma;dut->io_vxrm=q.vxrm;dut->io_vuop_idx=0;dut->io_op=q.op;
    dut->io_frm=0;dut->io_fp_rm=0;dut->io_fp_wflags=q.kind==2;
    dut->io_rob_flag=q.flag;dut->io_rob_value=q.rob;dut->io_pdest=q.dest;
    dut->io_write_v0=q.v0;dut->io_perf_tag=q.tag;
    for(unsigned i=0;i<q.perf.size();i++)dut->io_perf_payload[i]=q.perf[i];
    dut->io_flush_valid=f.valid;dut->io_flush_flag=f.flag;dut->io_flush_value=f.value;dut->io_flush_self=f.self;
    dut->eval();ctx->timeInc(1);
    check(dut->io_fu_clock==0,"clock","gated clock high while parent clock low");
    if(!reset){
      unsigned actualOcc=dut->io_occupancy;
      if(selectFault("occupancy",p&&r))actualOcc=1;
      check(bool(dut->io_p_valid)==bool(p) && bool(dut->io_r_valid)==bool(r) &&
        actualOcc==occupancy(),"occupancy","functional P/R valid disagree with independent state");
    }
    const bool kp=!reset && p && killed(p->req,f);
    const bool kr=!reset && r && killed(r->req,f);
    const bool kd=!reset && div && killed(div->req,f);
    const bool liveP=p && !kp && !reset, liveR=r && !kr && !reset;
    const bool rReady=!liveR || ready,move=liveP && rReady,pReady=!liveP || rReady;
    bool ov=dut->io_out_valid;
    if(selectFault("duplicate",!active() && responses>10000 && !reset))ov=true;
    if(selectFault("missing",liveR))ov=false;
    if(!reset){
      if(!active())check(!ov,"ghost","output with no transaction; cancel grace must not hide ghosts");
      else if(p||r)check(ov==liveR,"response","vdot visible output differs from surviving result slot");
      else if(div && !kd){
        check(tick-div->accepted<256,"latency","DIV completion watchdog");
        if(div->seen)check(ov,"stability","DIV stalled valid withdrawn");
        if(ov)check(tick>div->accepted,"latency","DIV zero-cycle response");
      }
    }else if(p||r)check(!ov,"reset","vdot output visible during reset");
    const unsigned childRawOut=dut->io_fu_out_valid;
    const unsigned childReady=dut->io_fu_in_ready;
    const bool parentBusy=dut->io_busy;
    const bool divReady=(dut->io_fu_in_ready&6U)==6U;
    const bool divUnavailable=bool(div) || (childRawOut&6U) || !divReady;
    const bool expectedReady=!reset && !f.valid && !divUnavailable &&
      (q.kind==0?pReady:(!p&&!r && (dut->io_fu_in_ready&(1U<<q.kind))));
    check(bool(dut->io_in_ready)==expectedReady,"ready","parent ready violates elastic/exclusive DIV contract");
    if(!reset){
      const bool expectedBusy=bool(p)||bool(r)||divUnavailable;
      check(bool(dut->io_busy)==expectedBusy,"busy","parent busy disagrees with slots/DIV recovery");
    }
    const bool inf=valid && dut->io_in_ready && !reset;
    const bool rawFire=ov && ready && !reset;
    const bool of=rawFire && !(kr||kd);
    unsigned childFire=dut->io_fu_in_valid & dut->io_fu_in_ready;
    if(selectFault("route",inf))childFire^=1U<<((q.kind+1)%3);
    check(childFire==(inf?(1U<<q.kind):0U),"route","parent/child acceptance is not atomic");
    if(!reset){
      unsigned childOut=childRawOut;
      if(selectFault("double",ov))childOut|=1U<<((r?0:div->req.kind)+1)%3;
      check((childOut&(childOut-1))==0,"route","multiple real FU outputs on one-hot mux");
      check(bool(childOut)==bool(dut->io_out_valid),"route","parent/child output qualification differs");
      if(ov)check((r||div) && childOut==(1U<<(r?0:div->req.kind)),"route","wrong child response owner");
      check(dut->io_fu_out_ready==(ready?7:0),"route","backpressure not propagated");
    }
    if(ov && !reset){
      check(bool(r)||bool(div),"ghost","output without expected R/DIV");
      Pending& old=r?*r:*div;
      Words actual{},vec{},v0{};
      for(unsigned i=0;i<4;i++){actual[i]=dut->io_result[i];vec[i]=dut->io_result_vec[i];v0[i]=dut->io_result_v0[i];}
      unsigned dest=dut->io_out_pdest,rob=dut->io_out_rob_value;
      bool flag=dut->io_out_rob_flag,vw=dut->io_out_vec_wen,z=dut->io_out_v0_wen;
      auto vpu=snapshot(dut->io_out_vpu_full),perf=snapshot(dut->io_out_perf_full);
      auto parentPerf=snapshot(dut->io_parent_perf_full);
      if(selectFault("identity",r&&p))dest=p->req.dest; // observe P identity on the old R response
      if(selectFault("rob",r&&p)){rob=p->req.rob;flag=p->req.flag;}
      if(selectFault("high"))actual[3]^=16;
      if(selectFault("metadata",r&&p))perf.back()^=1;
      if(selectFault("perf_swap",r&&p)){
        std::swap(perf[0],perf[2]);std::swap(perf[1],perf[3]);
      }
      if(selectFault("perf_parent",r&&p))parentPerf[6]^=1; // writebackTime bit 0
      if(selectFault("perf_cross",r&&p))parentPerf.assign(p->req.perf.begin(),p->req.perf.end());
      if(selectFault("wen"))vw=!vw;
      if(selectFault("stall",held && held->first==old.seq))dest^=1;
      std::vector<uint32_t> packet(actual.begin(),actual.end());
      packet.insert(packet.end(),vec.begin(),vec.end());packet.insert(packet.end(),v0.begin(),v0.end());
      packet.insert(packet.end(),{dest,rob,unsigned(flag),unsigned(vw),unsigned(z),
        unsigned(dut->io_out_int_wen),unsigned(dut->io_out_fp_wen),unsigned(dut->io_out_vl_wen),
        unsigned(dut->io_out_exception),unsigned(dut->io_out_fflags),unsigned(dut->io_out_wflags),
        unsigned(dut->io_out_vxsat),unsigned(dut->io_out_ctrl)});
      packet.insert(packet.end(),vpu.begin(),vpu.end());packet.insert(packet.end(),perf.begin(),perf.end());
      packet.insert(packet.end(),parentPerf.begin(),parentPerf.end());
      if(held && held->first==old.seq && !kr && !kd)check(held->second==packet,"stability","stalled complete response changed");
      const Words gold=old.req.illegal()?Words{}:old.req.data.gold;
      check(actual==gold&&vec==gold&&v0==gold,"high","full 128-bit result or writeback replica mismatch");
      check(dest==old.req.dest&&rob==old.req.rob&&flag==old.req.flag,"identity","response ROB/pdest switched identity");
      check(vpu==old.vpu && perf==old.perf,"identity","full VPU/perf identity changed across slots");
      check(parentPerf==old.perf,"perf_parent","actual parent debugInfo differs from accepted request");
      ++perfObservations;
      if(metadata.is_open())metadata<<"O cycle="<<tick<<" seq="<<old.seq
        <<" child="<<perfHex(perf)<<" parent="<<perfHex(parentPerf)<<'\n';
      check(vw==(!old.req.illegal()&&!old.req.v0)&&z==(!old.req.illegal()&&old.req.v0)&&
        !dut->io_out_int_wen&&!dut->io_out_fp_wen&&!dut->io_out_vl_wen,"wen","wrong write-enable class");
      check(dut->io_out_exception==(old.req.illegal()?4U:0U),"exception","wrong exception");
      check(dut->io_out_fflags==old.req.fflags && bool(dut->io_out_wflags)==(old.req.kind==2)&&
        !dut->io_out_vxsat,"flags","wrong FP flags/write qualification");
      check(dut->io_out_ctrl==old.req.ctrl(),"identity","independent vector control oracle mismatch");
      // Current declaration packs tlbResp first (LSB), issue at word 4, rename at 8.
      check(dut->io_out_perf_tag==perf64(old.req.perf,4) &&
        dut->io_out_rename_tag==perf64(old.req.perf,8),"identity","independent named debug field oracle");
      if(!old.seen){auto latency=tick-old.accepted;latMin[old.req.kind]=std::min(latMin[old.req.kind],latency);
        latMax[old.req.kind]=std::max(latMax[old.req.kind],latency);++latSamples[old.req.kind];old.seen=true;}
      if(!ready&&!kr&&!kd){++stalls;held=std::make_pair(old.seq,packet);}else held.reset();
      if(rawFire&&kd)++rawKilled[old.req.kind];
    }else if(reset||kr||kd)held.reset();
    const unsigned oldOcc=occupancy();
    const uint64_t pseq=p?p->seq:0,rseq=r?r->seq:0,dseq=div?div->seq:0;
    auto offeredPerf=snapshot(dut->io_in_perf_full);
    const std::vector<uint32_t> expectedPerf(q.perf.begin(),q.perf.end());
    if(selectFault("perf_input",inf))offeredPerf[14]^=1; // dispatchTime at child input
    if(inf){
      check(offeredPerf==expectedPerf,"perf_input","parent input route changed external metadata");
      ++perfInputs;
      if(metadata.is_open())metadata<<"A cycle="<<tick<<" seq="<<(accepted+1)<<" kind="<<q.kind
        <<" walk="<<q.walk<<" zero="<<q.walkZero<<" expected="<<perfHex(q.perf)
        <<" child="<<perfHex(offeredPerf)<<'\n';
    }
    // The expected perf comes from the request producer, never from a DUT tap.
    Pending fresh{q,tick,accepted+1,false,snapshot(dut->io_in_vpu_full),expectedPerf};
    unsigned requiredClocks=0;
    if(p||r)requiredClocks|=1;
    if(div)requiredClocks|=1U<<div->req.kind;
    if(inf)requiredClocks|=1U<<q.kind;
    if(reset)requiredClocks|=1; // O2 gate must propagate reset even when empty/clocked off.
    if(p&&r)++fullCycles;
    if(p&&r&&!ready&&!f.valid&&!reset)++fullBlocked;
    if(inf&&q.kind==0&&r&&!p&&!ready)++pAcceptWhileRBlocked;
    if(valid&&!inf&&!reset&&!f.valid)++waits[q.kind];
    if(of&&p&&r&&!inf&&!kp&&!reset)++retireWithPSurviving;
    if(kp&&!kr)++killPOnly;if(kr&&!kp)++killROnly;if(kp&&kr)++killBoth;
    if(reset){
      if(!te){++zeroTeResets;if(!active())++emptyZeroTeResets;}
      if(p&&r)++resetBoth;
      if(p)terminal(*p,2);if(r)terminal(*r,2);if(div)terminal(*div,2);
      p.reset();r.reset();div.reset();held.reset();
    }else{
      if(kp){terminal(*p,1);p.reset();}
      if(kr){terminal(*r,1);r.reset();}
      if(kd){terminal(*div,1);div.reset();}
      if(of){
        Pending old=r?*r:*div;
        check(!live.empty() && old.seq==*live.begin(),"order","survivor output reordered");
        terminal(old,0);if(r)r.reset();else div.reset();
      }
      if(move){check(p&&!r,"occupancy","invalid P to R transition");r=p;p.reset();++moves;}
      if(inf){
        check(live.insert(fresh.seq).second,"conservation","duplicate accept sequence");
        if(q.kind==0){check(!p&&!div,"occupancy","vdot accepted into occupied P or DIV");p=fresh;}
        else{check(!p&&!r&&!div,"route","DIV accepted before vdot drained");div=fresh;}
        ++accepted;++accepts[q.kind];
      }
    }
    if(of&&inf){check(q.kind==0,"route","cross-FU same-cycle handoff");++overlaps;}
    check(occupancy()<=2 && (!div||!occupancy()),"occupancy","more than two requests or simultaneous DIV");
    check(accepted==responses+cancels+resets+live.size() && live.size()==occupancy()+unsigned(bool(div)),
      "conservation","prefix transaction conservation");
    dut->clock=1;dut->eval();ctx->timeInc(1);
    unsigned clocks=dut->io_fu_clock;
    if(selectFault("clock",of&&move&&!inf))clocks&=~1U;
    if(reset || !te)check((clocks&requiredClocks)==requiredClocks,"clock","missing real FU rising clock");
    for(unsigned k=0;k<3;k++)if(clocks&(1U<<k))++clockEdges[k];
    bool nextPv=dut->io_p_valid,nextRv=dut->io_r_valid;
    if(selectFault("kill_p",kp&&!kr))nextPv=true;
    if(selectFault("kill_r",kr&&!kp&&!move))nextRv=true;
    if(selectFault("survivor",kp&&!kr&&bool(r)))nextRv=false;
    if(selectFault("reset",reset&&!te&&oldOcc>0))nextPv=true;
    check(nextPv==bool(p)&&nextRv==bool(r)&&dut->io_occupancy==occupancy(),
      reset?"reset":((kp||kr)?"cancel":"occupancy"),"next actual slots do not match exact transition");
    if(fault.empty()){
      std::cout<<"O2_PARENT_CYCLE schema=1 cycle="<<tick<<" p="<<unsigned(pseq!=0)<<" r="<<unsigned(rseq!=0)
        <<" case="<<label<<" rob_flag="<<q.flag<<" rob="<<q.rob<<" pdest="<<q.dest
        <<" block_reason="<<(reset?"reset":(f.valid?"redirect":(divUnavailable?"DIV":((q.kind!=0&&oldOcc)?"vdot-drain":((q.kind==0&&!pReady)?"vdot-full":"none")))))
        <<" pseq="<<pseq<<" rseq="<<rseq<<" divseq="<<dseq<<" occupancy="<<oldOcc
        <<" offered="<<valid<<" kind="<<q.kind<<" ready="<<expectedReady<<" out_ready="<<ready
        <<" accept="<<inf<<" accept_seq="<<(inf?fresh.seq:0)<<" p_to_r="<<move
        <<" response="<<of<<" response_seq="<<(of?(rseq?rseq:dseq):0)
        <<" stall="<<(ov&&!ready&&!reset&&!kr&&!kd)<<" kill_p="<<kp<<" kill_r="<<kr<<" kill_div="<<kd
        <<" reset="<<reset<<" reset_drop="<<(reset?oldOcc+unsigned(dseq!=0):0)
        <<" redirect="<<f.valid<<" redirect_flag="<<f.flag<<" redirect_rob="<<f.value<<" self="<<f.self
        <<" child_fire="<<childFire<<" child_out="<<childRawOut<<" child_ready="<<childReady<<" busy="<<parentBusy<<" clocks="<<clocks<<" te="<<te
        <<" next_occupancy="<<occupancy()<<" accepted_total="<<accepted<<" responses_total="<<responses
        <<" cancels_total="<<cancels<<" resets_total="<<resets<<" inflight="<<live.size()<<'\n';
    }
    ++tick;return {inf,of,ov&&!reset,unsigned(kp)+unsigned(kr)+unsigned(kd),clocks};
  }
  void group(const std::string& s){++groups;if(fault.empty())std::cout<<"O2_PARENT_GROUP_PASS "<<s<<'\n';}
  void drain(const Req& noise){unsigned n=0;while(active()){check(++n<300,"watchdog","drain");step(noise);}}
  void accept(const Req& q){
    unsigned n=0;while(!step(q,true).in)check(++n<300,"watchdog","waiting initial acceptance");
  }
  void waitVisible(const Req& noise,bool valid=false){
    unsigned n=0;while(true){check(++n<256,"watchdog","wait output");if(step(noise,valid,false).visible)break;}
  }
  void one(const Req& q,unsigned stall=0){
    check(!active(),"test","one requires empty pipeline");accept(q);
    if(stall){waitVisible(q);for(unsigned i=1;i<stall;i++)step(q,false,false);}
    drain(q);
  }
  void pair(const Req& a,const Req& b){
    check(!active(),"test","pair requires empty pipeline");
    check(step(a,true,false).in,"ready","pair first acceptance");
    check(step(b,true,false).in,"ready","pair second acceptance");
    check(p&&r,"occupancy","pair must fill both slots");
  }
  void finish(){
    check(!active()&&live.empty(),"test","unfinished transactions");
    check(perfInputs==accepted && perfObservations>=responses,"coverage","metadata observation coverage");
    check(walkOnes==577 && walkZeroes==577,"coverage","incomplete full-bit metadata sweep");
    if(metadata.is_open()){
      metadata<<"END cycles="<<tick<<" accepts="<<perfInputs<<" observations="<<perfObservations
        <<" one="<<walkOnes<<" zero="<<walkZeroes<<'\n';
      metadata.flush();need(bool(metadata),"output","metadata write failed");
    }
    dut->final();
  }
};
static void test(Bench& b,const std::vector<Data>& data){
  Req noise=sample(data,0,777);unsigned serial=30000;
  // Bootstrap only: unchanged legacy DIV clock gates require TE for reset.
  b.step(noise,false,true,{},true,true);b.step(noise,false,true,{},true,true);
  for(unsigned i=0;i<4;i++){auto c=b.step(noise);b.check(c.clocks==0,"clock","initial idle clocks not gated");++b.idleClockSamples;}
  b.step(noise,true,true,{},true,false); // actual empty O2 gated reset without TE
  for(unsigned i=0;i<3;i++)b.step(noise);
  b.group("real-ClockGate bootstrap-TE=1; empty-O2-reset-TE=0; idle-gating");
  b.label="frozen-vdot-II1";
  size_t next=0;uint64_t last=0;
  while(next<data.size()||b.active()){
    const auto now=b.tick;auto c=b.step(next<data.size()?dot(data[next],unsigned(next)):noise,next<data.size());
    if(c.in){if(next)b.check(now-last==1,"latency","continuous parent acceptance II must equal one");last=now;++next;}
    b.check(b.tick<20000,"watchdog","frozen II1 stream");
  }
  b.check(b.responds[0]==10022 && b.overlaps==10020,"coverage","frozen 22+10000/II1 overlap count");
  b.check(b.latMin[0]==2&&b.latMax[0]==2,"latency","unblocked frozen stream latency must be exactly two");
  b.step(noise); // catches negative duplicate output with an empty scoreboard
  b.group("frozen=10022 full128-three-buses; continuous-II=1 latency=2 full-vpu-perf-copy");
  b.label="two-slot-backpressure";
  for(unsigned delay:{1U,2U,7U,23U}){
    Req a=dot(data[serial%data.size()],serial++),n=dot(data[serial%data.size()],serial++);
    b.accept(a);b.waitVisible(noise);
    b.check(b.step(n,true,false).in,"ready","empty P should accept while R blocked");
    for(unsigned i=0;i<delay;i++)b.check(!b.step(noise,true,false).in,"ready","full blocked pipeline accepted third");
    auto c=b.step(noise,false,true);b.check(c.out&&b.active(),"clock","R response must leave old P alive without new request");
    b.drain(noise);
  }
  b.group("R-blocked-empty-P-fill; full-reject; stall=1,2,7,23; R-drain-P-survives-no-new-input");
  b.label="div-sanity";
  b.check(idiv(3,0).data.gold==Words{5,uint32_t(-5),uint32_t(INT32_MIN),UINT32_MAX},"oracle","signed quotient");
  b.check(idiv(1,0).data.gold==Words{2,uint32_t(-2),0,INT32_MAX},"oracle","signed remainder");
  b.check(idiv(2,0).data.gold==Words{0x7fffffff,0x2aaaaaaa,UINT32_MAX,UINT32_MAX},"oracle","unsigned quotient");
  b.check(idiv(0,0).data.gold==Words{1,2,19,0},"oracle","unsigned remainder");
  for(unsigned op=0;op<4;op++)for(unsigned stall:{0U,1U,7U})b.one(idiv(op,serial++),stall);
  for(unsigned i=0;i<64;i++)b.one(idiv(i%4,serial++,i+1),i%4);
  for(unsigned which=0;which<3;which++)for(unsigned stall:{0U,1U,7U})b.one(fdiv(which,serial++),stall);
  b.group("real-VIDiv=76 div-divu-rem-remu overflow-div0; real-VFDiv=9 FP32-DZ-signed-zero");
  for(unsigned old=0;old<3;old++)for(unsigned incoming=0;incoming<3;incoming++)for(unsigned delay:{0U,1U,7U}){
    b.label="switch-"+std::to_string(old)+"-"+std::to_string(incoming)+"-"+std::to_string(delay);
    Req a=sample(data,old,serial++),n=sample(data,incoming,serial++);
    if(old==0)b.pair(a,dot(data[(serial*7)%data.size()],serial++));else b.accept(a);
    if(delay){b.waitVisible(n);for(unsigned i=1;i<delay;i++)b.step(n,true,false);}
    unsigned wait=0;bool got=false;
    do{
      b.check(++wait<300,"watchdog","FU switch");
      const bool before=b.active();auto c=b.step(n,true,true);got=c.in;
      if(old!=0||incoming!=0)if(before)b.check(!c.in,"route","cross-FU accepted before prior transaction drained");
    }while(!got);
    b.drain(noise);++b.directedPairs[old*3+incoming];
  }
  b.group("all-nine-FU-transitions x stalls=0,1,7; full-vdot-pair-drain-before-DIV");
  b.label="legal-illegal-v0";
  unsigned sent=0;
  while(sent<128||b.active()){
    Req q=dot(data[(sent*17)%data.size()],serial+sent);
    if(sent%2)switch((sent/2)%8){
      case 0:q.vl=7;break;case 1:q.sew=1;break;case 2:q.lmul=2;break;case 3:q.start=1;break;
      case 4:q.vill=true;break;case 5:q.vm=false;break;case 6:q.op=1;break;case 7:q.vl=0;break;
    }
    if(b.step(q,sent<128,sent%9!=2||b.tick%3==0).in)++sent;
  }
  serial+=128;b.group("legal-illegal=128 mixed-v0-exception-full-metadata");
  struct PairRel{unsigned a,b,at;bool self;unsigned mask;};
  // Locations 0..95 include real RobPtr flags. mask bit0=R(A), bit1=P(B).
  const PairRel rels[]={
    {8,12,10,false,2},{12,8,10,false,1},{12,14,10,false,3},{8,6,10,false,0},
    {10,8,10,false,0},{10,8,10,true,1},{8,10,10,true,2},{10,10,10,true,3},
    {47,49,48,false,2},{49,47,48,false,1},{95,1,0,false,2},{1,95,0,false,1},
    {47,48,47,true,3},{95,0,95,true,3}
  };
  for(const auto rel:rels)for(bool ready:{false,true})for(unsigned incoming=0;incoming<3;incoming++){
    b.label="partial-ROB-"+std::to_string(b.redirects);
    Req a=dot(data[serial%data.size()],serial++),n=dot(data[serial%data.size()],serial++);
    a.rob=rel.a%48;a.flag=rel.a/48;n.rob=rel.b%48;n.flag=rel.b/48;
    Flush f{true,bool(rel.at/48),rel.at%48,rel.self};
    b.check(unsigned(killed(a,f))+2*unsigned(killed(n,f))==rel.mask,"oracle","ROB pair relation");
    b.pair(a,n);for(unsigned i=0;i<3;i++)b.step(noise,false,false);
    auto c=b.step(sample(data,incoming,serial++),true,ready,f);
    b.check(!c.in && c.killed==unsigned(bool(rel.mask&1))+unsigned(bool(rel.mask&2)),"cancel","partial kill count");
    b.drain(noise);b.one(sample(data,incoming,serial++));++b.redirects;
  }
  // P-only and R-only cancellations: includes R kill with no surviving P for miss-kill negative.
  for(unsigned phase=0;phase<2;phase++)for(bool self:{false,true})for(bool ready:{false,true}){
    b.label="single-slot-cancel";Req q=dot(data[serial%data.size()],serial++);q.rob=10;q.flag=false;
    b.accept(q);if(phase)b.waitVisible(noise);
    b.step(noise,true,ready,{true,false,self?10U:9U,self});b.drain(noise);++b.redirects;
  }
  b.group("ROB-pair-partial-both-neither age-order-reversal flag-wrap flush-self; single-slot-kills");
  for(unsigned kind=1;kind<3;kind++)for(unsigned incoming=0;incoming<3;incoming++)
  for(unsigned phase=0;phase<3;phase++)for(bool ready:{false,true}){
    b.label="DIV-cancel-"+std::to_string(b.redirects);
    Req q=sample(data,kind,serial++),n=sample(data,incoming,serial++);q.flag=false;q.rob=10;
    b.accept(q);if(phase){b.waitVisible(n);if(phase==2)for(unsigned i=0;i<7;i++)b.step(n,true,false);}
    auto c=b.step(n,true,ready,{true,false,10,true});
    b.check(!c.in&&c.killed==1,"cancel","DIV kill priority");
    for(unsigned i=0;i<3;i++){auto idle=b.step(n);if(idle.clocks&(1U<<kind))++b.cancelIdleClockOn;}
    b.one(n);++b.redirects;
  }
  b.check(b.rawKilled[0]==0&&b.rawKilled[1]>0&&b.rawKilled[2]>0,"coverage","legacy DIV cancel-cycle raw response not observed");
  b.group("DIV-cancel=36 calculate-visible-stalled x ready x next-FU; raw-cancel-output-retained-but-no-ghost-grace");
  for(unsigned phase=0;phase<4;phase++)for(bool withFlush:{false,true}){
    b.label="TE0-reset-"+std::to_string(b.resetCases);
    Req a=dot(data[serial%data.size()],serial++),n=dot(data[serial%data.size()],serial++);
    a.rob=12;a.flag=false;n.rob=14;n.flag=false;
    if(phase==1)b.accept(a);
    if(phase==2){b.accept(a);b.waitVisible(noise);}
    if(phase==3)b.pair(a,n);
    auto before=b.resets;b.step(n,true,true,{withFlush,false,10,false},true,false);
    b.check(b.resets-before==(phase==3?2U:unsigned(phase!=0)),"reset","reset must dominate cancel exactly once");
    b.step(noise,false,true,{},true,false);for(unsigned i=0;i<3;i++)b.step(noise);
    b.one(n);++b.resetCases;
  }
  b.group("O2-TE=0 reset empty-P-R-full x cancel; exact-reset-priority; post-reset-wakeup");
  for(unsigned kind=1;kind<3;kind++)for(unsigned phase=0;phase<3;phase++){
    b.label="DIV-legacy-reset";Req q=sample(data,kind,serial++);b.accept(q);
    if(phase){b.waitVisible(noise);if(phase==2)for(unsigned i=0;i<7;i++)b.step(noise,false,false);}
    b.step(noise,true,true,{},true,true);b.step(noise,false,true,{},true,true);
    for(unsigned i=0;i<3;i++)b.step(noise);b.one(sample(data,0,serial++));++b.resetCases;
  }
  b.group("legacy-DIV-reset=6 bootstrap-compatible-TE=1 (not-O2-TE0-reset-evidence)");
  b.label="random-control";std::mt19937 rng(0x20261019);
  for(unsigned i=0;i<20000;i++){
    Req q=sample(data,rng()%3,serial++);if(q.kind==0&&rng()%9==0)q.vl=7;
    // All current requests live in one bounded architectural ROB window.
    if(b.active()){
      auto old=b.r?b.r:(b.p?b.p:b.div);unsigned pos=unsigned(old->req.flag)*48+old->req.rob;
      unsigned at=(pos+(rng()%7))%96;q.flag=at/48;q.rob=at%48;
    }
    Flush f{};
    if(rng()%29==0){
      auto old=b.r?b.r:(b.p?b.p:b.div);unsigned pos=old?unsigned(old->req.flag)*48+old->req.rob:0;
      unsigned at=(pos+96+(rng()%25)-12)%96;f={true,bool(at/48),at%48,bool(rng()%2)};
    }
    const bool valid=rng()%4!=0,ready=rng()%3!=0,reset=rng()%397==0;
    b.step(q,valid,ready,f,reset,reset&&bool(b.div));
  }
  b.drain(noise);b.group("random=20000 seed=0x20261019; bounded-ROB-window; prefix-conservation");
  b.label="perf-walking";
  for(unsigned bit=0;bit<577;bit++){
    Req a=dot(data[bit%data.size()],serial++);
    Req n=dot(data[(bit+1)%data.size()],serial++);
    a.perf.fill(0);a.perf[bit/32]=uint32_t(1)<<(bit%32);a.walk=int(bit);
    n.perf.fill(UINT32_MAX);n.perf[18]=1;
    n.perf[bit/32]^=uint32_t(1)<<(bit%32);n.walk=int(bit);n.walkZero=true;
    b.pair(a,n);
    for(unsigned hold=0;hold<1+bit%3;hold++)
      b.check(!b.step(noise,true,false).in,"ready","metadata full pair accepted noise");
    b.drain(noise);
  }
  b.group("perf-v2 577-walking-one 577-walking-zero external-input-child-parent; blocked-two-slot-pairs");
  b.label="clock-recovery";for(unsigned kind=0;kind<3;kind++)b.one(sample(data,kind,serial++));
  for(unsigned i=0;i<8;i++){auto c=b.step(noise);b.check(c.clocks==0,"clock","normal-completion idle must gate all FUs");++b.idleClockSamples;}
  b.group("all-real-FU-clocks-gated-after-recovery");
  for(unsigned k=0;k<3;k++)b.check(b.accepts[k]&&b.responds[k]&&b.kills[k]&&b.drops[k]&&b.clockEdges[k],"coverage","missing per-FU terminal/clock coverage");
  for(auto n:b.directedPairs)b.check(n==3,"coverage","missing 9x3 transition");
  b.check(b.killPOnly&&b.killROnly&&b.killBoth&&b.resetBoth&&b.pAcceptWhileRBlocked&&b.fullBlocked&&b.retireWithPSurviving,
    "coverage","missing elastic control corner");
  b.check(b.zeroTeResets&&b.emptyZeroTeResets&&b.overlaps>=10020,"coverage","missing true-gate or II1 evidence");
  b.finish();
}
int main(int argc,char** argv){
  if(argc<2||argc>4){std::cerr<<"usage: parent_test vectors.tsv [fault|-] [new-metadata.log]\n";return 2;}
  const std::string fault=argc>=3&&std::string(argv[2])!="-"?argv[2]:"";
  const std::string metadata=argc==4?argv[3]:"";
  try{
    need(fault.empty()||std::set<std::string>{"identity","rob","high","metadata","wen","stall","route","double",
      "clock","occupancy","kill_p","kill_r","survivor","duplicate","missing","reset",
      "perf_input","perf_swap","perf_parent","perf_cross"}.count(fault),"input","unknown fault");
    auto data=load(argv[1]);Bench b(fault,metadata);test(b,data);
    if(!fault.empty()){std::cerr<<"O2_PARENT_FAULT_ESCAPED "<<fault<<'\n';return 3;}
    for(unsigned k=0;k<3;k++)std::cout<<"O2_PARENT_FU kind="<<k<<" accepted="<<b.accepts[k]<<" responded="<<b.responds[k]
      <<" killed="<<b.kills[k]<<" reset_dropped="<<b.drops[k]<<" raw_killed_response="<<b.rawKilled[k]
      <<" latency_min="<<b.latMin[k]<<" latency_max="<<b.latMax[k]<<" latency_samples="<<b.latSamples[k]
      <<" clock_edges="<<b.clockEdges[k]<<" waits="<<b.waits[k]<<'\n';
    std::cout<<"O2_PARENT_PASS schema=1 cycles="<<b.tick<<" groups="<<b.groups<<" accepted="<<b.accepted
      <<" responses="<<b.responses<<" cancelled="<<b.cancels<<" reset_dropped="<<b.resets<<" overlaps="<<b.overlaps
      <<" stalls="<<b.stalls<<" p_to_r="<<b.moves<<" full_cycles="<<b.fullCycles<<" full_blocked="<<b.fullBlocked
      <<" p_accept_r_blocked="<<b.pAcceptWhileRBlocked<<" r_response_p_survivor="<<b.retireWithPSurviving
      <<" kill_p_only="<<b.killPOnly<<" kill_r_only="<<b.killROnly<<" kill_both="<<b.killBoth<<" reset_both="<<b.resetBoth
      <<" redirects="<<b.redirects<<" reset_cases="<<b.resetCases<<" te0_resets="<<b.zeroTeResets
      <<" empty_te0_resets="<<b.emptyZeroTeResets<<" idle_clock_samples="<<b.idleClockSamples
      <<" cancel_idle_clock_on="<<b.cancelIdleClockOn<<" perf_contract=2 perf_bits=577"
      <<" perf_inputs="<<b.perfInputs<<" perf_observations="<<b.perfObservations
      <<" perf_walk_one="<<b.walkOnes<<" perf_walk_zero="<<b.walkZeroes
      <<" parent_tested=1 fullcore_tested=0 performance_measured=0\n";return 0;
  }catch(const Failure& e){std::cerr<<"O2_PARENT_FAIL "<<e.category<<'\n';if(fault.empty())std::cerr<<e.what()<<'\n';return 1;}
  catch(const std::exception& e){std::cerr<<"O2_PARENT_ERROR "<<e.what()<<'\n';return 2;}
}
