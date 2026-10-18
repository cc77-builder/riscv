// Real VFEX4 parent scoreboard. Gold is frozen vdot data or independent arithmetic.
#include "VVDotParentTestTop.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <optional>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#ifndef O1_PARENT_HANDOFF
#error O1_PARENT_HANDOFF must be explicitly set to 0 or 1
#endif
static_assert(O1_PARENT_HANDOFF == 0 || O1_PARENT_HANDOFF == 1);
constexpr bool handoff = O1_PARENT_HANDOFF;
using Words = std::array<uint32_t, 4>;
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
  bool illegal() const { return kind==0 && (vill || !vm || vl!=8 || sew || lmul || start || op); }
  uint32_t ctrl() const {
    return (uint32_t(vill)<<26)|(uint32_t(ma)<<25)|(uint32_t(ta)<<24)|(sew<<22)|
      (lmul<<19)|(uint32_t(vm)<<18)|(start<<10)|(ctrlVl<<2)|vxrm;
  }
};
struct Flush { bool valid=false, flag=false; unsigned value=0; bool self=false; };
struct Pending { Req req; uint64_t accepted; bool seen=false; };
struct Cycle { bool in=false, out=false, visible=false, killed=false; unsigned clocks=0; };
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
  std::unique_ptr<VVDotParentTestTop> dut=std::make_unique<VVDotParentTestTop>(ctx.get());
  bool injected=false, previousOverlap=false;
 public:
  std::string fault, label="initial";
  std::optional<Pending> pending;
  uint64_t tick=0,accepted=0,responses=0,cancels=0,resets=0,overlaps=0,stalls=0,groups=0;
  std::array<uint64_t,3> accepts{},responds{},kills{},drops{},rawKilled{},latMin{9999,9999,9999},latMax{},latSamples{},clockEdges{};
  std::array<uint64_t,9> directedPairs{};
  uint64_t redirects=0,resetCases=0,idleClockSamples=0,cancelIdleClockOn=0,legacySuppressed=0;
  explicit Bench(std::string f):fault(std::move(f)) {}
  void check(bool ok,const std::string& category,const std::string& why) const {
    need(ok,category,"case="+label+" tick="+std::to_string(tick)+" "+why);
  }
  void inject() { injected=true;std::cerr<<"O1_PARENT_INJECT "<<fault<<'\n'; }
  Cycle step(const Req& q,bool valid=false,bool ready=true,Flush f={},bool reset=false) {
    dut->clock=0;dut->reset=reset;dut->io_test_enable=reset;
    // The old parent relies on upstream suppression at reset/redirect boundaries.
    // O1 is additionally stressed with valid still asserted at those boundaries.
    const bool offered=valid && (handoff || (!reset && !f.valid));
    if(valid && !offered) ++legacySuppressed;
    dut->io_in_valid=offered;dut->io_out_ready=ready;dut->io_kind=q.kind;
    for (unsigned i=0;i<4;i++) {
      dut->io_vs1[i]=q.data.a[i];dut->io_vs2[i]=q.data.b[i];
      dut->io_old_vd[i]=uint32_t(tick*7919+i);dut->io_mask[i]=uint32_t(~(tick+i));
    }
    dut->io_vl=q.vl;dut->io_ctrl_vl=q.ctrlVl;dut->io_vsew=q.sew;dut->io_vlmul=q.lmul;
    dut->io_vstart=q.start;dut->io_vill=q.vill;dut->io_vm=q.vm;dut->io_vta=q.ta;
    dut->io_vma=q.ma;dut->io_vxrm=q.vxrm;dut->io_vuop_idx=0;dut->io_op=q.op;
    dut->io_frm=0;dut->io_fp_rm=0;dut->io_fp_wflags=q.kind==2;
    dut->io_rob_flag=q.flag;dut->io_rob_value=q.rob;dut->io_pdest=q.dest;
    dut->io_write_v0=q.v0;dut->io_perf_tag=q.tag;
    dut->io_flush_valid=f.valid;dut->io_flush_flag=f.flag;dut->io_flush_value=f.value;dut->io_flush_self=f.self;
    dut->eval();ctx->timeInc(1);
    bool busy=dut->io_busy;
    if (fault=="busy" && previousOverlap && !injected && !reset) {busy=!busy;inject();}
    if (!reset) check(busy==bool(pending),"busy","busy disagrees with architectural outstanding transaction");
    check(dut->io_fu_clock==0,"clock","gated clock high while parent clock low");
    const bool kill=pending && killed(pending->req,f);
    bool ov=dut->io_out_valid;
    if (fault=="cancel" && kill && pending->req.kind==0 && !injected && !reset) {ov=true;inject();}
    if (!reset) {
      if (!pending) check(!ov,"cancel","response without a live transaction (ghost)");
      else if (pending->req.kind==0) {
        check(ov==(tick>=pending->accepted+2 && !kill),kill?"cancel":"latency","vdot response deadline/kill");
      } else if (!kill) {
        if (pending->seen) check(ov,"stability","DIV valid withdrawn while response is backpressured");
        else {
          check(tick-pending->accepted<256,"latency","DIV exceeded bounded completion time");
          if (ov) check(tick>pending->accepted,"latency","DIV zero-cycle response");
        }
      }
    }
    const bool canOverlap=handoff && pending && pending->req.kind==0 && q.kind==0 && ov && ready;
    const bool expectedReady=(!pending || canOverlap) && !f.valid && !reset;
    check(bool(dut->io_in_ready)==expectedReady,"ready","parent ready disagrees with serialized/VDot-only handoff contract");
    const bool inf=offered && dut->io_in_ready && !reset;
    const bool rawFire=ov && ready && !reset;
    const bool of=rawFire && !kill;
    unsigned childFire=dut->io_fu_in_valid & dut->io_fu_in_ready;
    if (fault=="route" && inf && !injected) {childFire ^= (1U<<((q.kind+1)%3));inject();}
    check(childFire==(inf?(1U<<q.kind):0U),"route","selected child acceptance differs from parent acceptance");
    if (!reset) {
      const unsigned childOut=dut->io_fu_out_valid;
      check((childOut & (childOut-1))==0,"route","multiple child outputs on one-hot parent mux");
      check(bool(childOut)==bool(dut->io_out_valid),"route","parent and child output qualification disagree");
      if (ov) check(pending && childOut==(1U<<pending->req.kind),"route","wrong child owns current response");
      check(dut->io_fu_out_ready==(ready?7:0),"route","parent backpressure not propagated to all children");
    }
    if (ov && !reset) {
      check(bool(pending),"cancel","output without scoreboard request");
      const Req& old=pending->req;Words actual{},vec{},v0{};
      for (unsigned i=0;i<4;i++) {actual[i]=dut->io_result[i];vec[i]=dut->io_result_vec[i];v0[i]=dut->io_result_v0[i];}
      unsigned dest=dut->io_out_pdest;bool vw=dut->io_out_vec_wen,z=dut->io_out_v0_wen;
      if (inf && !injected) {
        if (fault=="identity") {dest^=1;inject();}
        if (fault=="wen") {vw=!vw;inject();}
        if (fault=="high") {actual[3]^=16;inject();}
      }
      Words gold=old.illegal()?Words{}:old.data.gold;
      check(actual==gold && vec==gold && v0==gold,"high","full 128-bit result or writeback replica");
      check(dest==old.dest && bool(dut->io_out_rob_flag)==old.flag && dut->io_out_rob_value==old.rob,"identity","old ROB/pdest identity");
      check(vw==(!old.illegal()&&!old.v0) && z==(!old.illegal()&&old.v0) && !dut->io_out_int_wen && !dut->io_out_fp_wen && !dut->io_out_vl_wen,"wen","old write enables");
      check(dut->io_out_exception==(old.illegal()?4U:0U),"exception","exception not bound to old request");
      check(dut->io_out_fflags==old.fflags && bool(dut->io_out_wflags)==(old.kind==2) && !dut->io_out_vxsat,"flags","floating flags/write qualification");
      check(dut->io_out_ctrl==old.ctrl(),"identity","observed old child vector config");
      check(dut->io_out_perf_tag==old.tag && dut->io_out_rename_tag==(old.tag^UINT64_C(0xf0e1d2c3b4a59687)),"identity","old debug identity");
      if (!pending->seen) {
        auto latency=tick-pending->accepted;latMin[old.kind]=std::min(latMin[old.kind],latency);
        latMax[old.kind]=std::max(latMax[old.kind],latency);++latSamples[old.kind];pending->seen=true;
      }
      if (!ready) ++stalls;
      if (rawFire && kill) ++rawKilled[old.kind];
    }
    unsigned requiredClocks=0;
    if (pending) requiredClocks|=1U<<pending->req.kind;
    if (inf) requiredClocks|=1U<<q.kind;
    if (reset) {if(pending){++resets;++drops[pending->req.kind];}pending.reset();}
    else if (kill) {++cancels;++kills[pending->req.kind];pending.reset();}
    else if (of) {++responses;++responds[pending->req.kind];pending.reset();}
    if (inf) {
      check(!pending,"busy","multiple architectural transactions in flight");
      pending=Pending{q,tick,false};++accepted;++accepts[q.kind];
    }
    if (of && inf) {check(handoff && q.kind==0,"busy","unexpected overlap with DIV");++overlaps;}
    previousOverlap=of&&inf;
    check(accepted==responses+cancels+resets+unsigned(pending.has_value()),"conservation","transaction conservation");
    dut->clock=1;dut->eval();ctx->timeInc(1);
    unsigned clocks=dut->io_fu_clock;
    if (fault=="clock" && of && inf && !injected) {clocks^=1;inject();}
    if (!reset) check((clocks&requiredClocks)==requiredClocks,"clock","missing real FU rising clock for active or accepted request");
    for (unsigned k=0;k<3;k++) if (clocks&(1U<<k)) ++clockEdges[k];
    ++tick;return {inf,of,ov&&!reset,kill&&!reset,clocks};
  }
  void group(const std::string& s) {++groups;if(fault.empty())std::cout<<"O1_PARENT_GROUP_PASS "<<s<<'\n';}
  void drain(const Req& noise) {
    unsigned n=0;while(pending){check(++n<300,"watchdog","drain");step(noise,false,true);}
  }
  void waitVisible(const Req& noise,bool valid=false) {
    unsigned n=0;while(true){check(++n<256,"watchdog","wait output");auto c=step(noise,valid,false);if(c.visible)break;}
  }
  void one(const Req& q,unsigned stall=0) {
    check(!pending,"test","one requires idle");check(step(q,true).in,"ready","initial request acceptance");
    if (stall) {waitVisible(q);for(unsigned i=1;i<stall;i++)step(q,false,false);}
    drain(q);
  }
  void finish() {check(!pending,"test","unfinished transaction");dut->final();}
};
static void test(Bench& b,const std::vector<Data>& data) {
  Req noise=sample(data,0,777);unsigned serial=30000;
  b.step(noise,false,true,{},true);b.step(noise,false,true,{},true);
  for(unsigned i=0;i<4;i++) {auto c=b.step(noise);b.check(c.clocks==0,"clock","initial idle clock not gated");++b.idleClockSamples;}
  b.group("real-ClockGate reset-TE-only idle-gating");
  b.label="frozen-vdot-stream";
  size_t next=0;unsigned held=0;const unsigned delays[]={0,1,2,7};uint64_t last=0;
  while (next<data.size() || b.pending) {
    Req q=next<data.size()?dot(data[next],unsigned(next)):noise;bool ready=true;
    if (b.pending && b.tick>=b.pending->accepted+2) {ready=held==0;if(held)--held;}
    uint64_t before=b.tick;
    if(b.step(q,next<data.size(),ready).in) {
      if(next)b.check(before-last==(handoff?2:3)+delays[(next-1)%4],"latency","parent VDot II");
      last=before;held=delays[next%4];++next;
    }
    b.check(b.tick<140000,"watchdog","vdot stream");
  }
  b.check(b.responds[0]==10022 && b.overlaps==(handoff?10021:0),"coverage","frozen arithmetic and same-cycle coverage");
  b.group("vdot=10022 full128-three-result-buses stalls=0,1,2,7 identity flags latency-II");
  b.label="integer-oracle-sanity";
  b.check(idiv(3,0).data.gold==Words{5,uint32_t(-5),uint32_t(INT32_MIN),UINT32_MAX},"oracle","signed quotient corners");
  b.check(idiv(1,0).data.gold==Words{2,uint32_t(-2),0,INT32_MAX},"oracle","signed remainder corners");
  b.check(idiv(2,0).data.gold==Words{0x7fffffff,0x2aaaaaaa,UINT32_MAX,UINT32_MAX},"oracle","unsigned quotient corners");
  b.check(idiv(0,0).data.gold==Words{1,2,19,0},"oracle","unsigned remainder corners");
  for(unsigned op=0;op<4;op++)for(unsigned stall:{0U,1U,7U})b.one(idiv(op,serial++),stall);
  for(unsigned i=0;i<64;i++)b.one(idiv(i%4,serial++,i+1),i%4);
  for(unsigned which=0;which<3;which++)for(unsigned stall:{0U,1U,7U})b.one(fdiv(which,serial++),stall);
  b.group("real-VIDiv div-divu-rem-remu=76 cases overflow-div0; real-VFDiv=9 exact-FP32-DZ-signed-zero");
  for(unsigned old=0;old<3;old++)for(unsigned incoming=0;incoming<3;incoming++)for(unsigned delay:{0U,1U,7U}) {
    b.label="switch-"+std::to_string(old)+"-"+std::to_string(incoming)+"-stall-"+std::to_string(delay);
    Req a=sample(data,old,serial++),n=sample(data,incoming,serial++);
    b.check(b.step(a,true).in,"ready","switch old accept");
    Cycle c;
    if(delay) {
      b.waitVisible(n,true);
      for(unsigned i=1;i<delay;i++)b.step(n,true,false);
      c=b.step(n,true,true);
    } else {
      unsigned waited=0;
      do {b.check(++waited<256,"watchdog","zero-stall switch");c=b.step(n,true,true);} while(!c.visible);
    }
    b.check(c.out && c.in==(handoff&&old==0&&incoming==0),"busy","only VDot-to-VDot may hand off");
    if(!c.in)b.check(b.step(n,true).in,"ready","DIV transition must accept next cycle");
    b.drain(noise);++b.directedPairs[old*3+incoming];
  }
  b.group("all-nine-FU-transitions x three-stalls; only-VDot-VDot-overlap");
  b.label="legal-illegal-handoff";unsigned sent=0;
  while(sent<96 || b.pending) {
    Req q=dot(data[(sent*17)%data.size()],serial+sent);
    if(sent%2) switch((sent/2)%8) {
      case 0:q.vl=7;break;case 1:q.sew=1;break;case 2:q.lmul=2;break;case 3:q.start=1;break;
      case 4:q.vill=true;break;case 5:q.vm=false;break;case 6:q.op=1;break;case 7:q.vl=0;break;
    }
    if(b.step(q,sent<96,true).in)++sent;
  }
  serial+=96;b.group("legal-illegal-vdot=96 full-parent-exception-and-write-suppression");
  struct Relation {bool rf;unsigned rv;bool ff;unsigned fv;bool self;bool kill;};
  const Relation relations[]={{0,12,0,10,0,1},{0,8,0,10,0,0},{0,10,0,10,0,0},{0,10,0,10,1,1},
    {1,1,0,47,0,1},{0,47,1,1,0,0},{0,1,1,47,0,1},{1,47,0,1,0,0}};
  for(unsigned kind=0;kind<3;kind++)for(unsigned incoming=0;incoming<3;incoming++)for(auto rel:relations)
  for(unsigned phase=0;phase<3;phase++)for(bool ready:{false,true}) {
    b.label="redirect-"+std::to_string(b.redirects);
    Req q=sample(data,kind,serial++),n=sample(data,incoming,serial++);q.flag=rel.rf;q.rob=rel.rv;
    Flush f{true,rel.ff,rel.fv,rel.self};b.check(killed(q,f)==rel.kill,"oracle","ROB relation");
    b.check(b.step(q,true).in,"ready","redirect initial accept");
    if(phase) {b.waitVisible(n,true);if(phase==2)for(unsigned i=0;i<7;i++)b.step(n,true,false);}
    auto c=b.step(n,true,ready,f);b.check(!c.in && c.killed==rel.kill,"cancel","redirect priority");
    if(rel.kill) {
      for(unsigned i=0;i<3;i++){auto idle=b.step(n);if(idle.clocks&(1U<<kind))++b.cancelIdleClockOn;}
    } else b.drain(n);
    b.one(n);++b.redirects;
  }
  b.check(b.redirects==432,"coverage","redirect matrix incomplete");
  b.check(b.rawKilled[0]==0 && b.rawKilled[1]>0 && b.rawKilled[2]>0,"coverage","DIV cancel-cycle raw response semantics not observed");
  b.group("redirect=432 older-self-younger-wrap x calculate-response-stalled x ready x all-FU-switches");
  for(unsigned kind=0;kind<3;kind++)for(unsigned incoming=0;incoming<3;incoming++)for(unsigned phase=0;phase<3;phase++) {
    b.label="reset-"+std::to_string(b.resetCases);
    Req q=sample(data,kind,serial++),n=sample(data,incoming,serial++);
    b.check(b.step(q,true).in,"ready","reset initial accept");
    if(phase){b.waitVisible(n,true);if(phase==2)for(unsigned i=0;i<7;i++)b.step(n,true,false);}
    b.check(!b.step(n,true,true,{},true).in,"reset","reset input accepted");
    b.step(n,false,true,{},true);for(unsigned i=0;i<3;i++)b.step(n);
    b.one(n);++b.resetCases;
  }
  b.group("reset=27 all-FUs x next-FU x calculate-response-stalled; TE-only-during-reset");
  b.label="random-control";std::mt19937 rng(0x20261018);
  for(unsigned i=0;i<20000;i++) {
    Req q=sample(data,rng()%3,serial++);if(q.kind==0&&rng()%9==0)q.vl=7;
    Flush f{};
    if(rng()%29==0) {
      unsigned pos=b.pending?unsigned(b.pending->req.flag)*48+b.pending->req.rob:0;
      unsigned at=(pos+96+(rng()%25)-12)%96;f={true,bool(at/48),at%48,bool(rng()%2)};
    }
    const bool valid=rng()%4!=0,ready=rng()%3!=0,reset=rng()%397==0;
    b.step(q,valid,ready,f,reset);
  }
  b.drain(noise);b.group("random-control=20000 seed=0x20261018 transaction-conservation-and-watchdog");
  b.label="clock-recovery";
  for(unsigned kind=0;kind<3;kind++)b.one(sample(data,kind,serial++));
  for(unsigned i=0;i<8;i++){auto c=b.step(noise);b.check(c.clocks==0,"clock","all FUs must gate after normal completion recovery");++b.idleClockSamples;}
  b.group("normal-completion-recovery all-real-FU-clocks-gated-idle");
  for(unsigned k=0;k<3;k++)b.check(b.accepts[k]>0&&b.responds[k]>0&&b.kills[k]>0&&b.drops[k]>0&&b.clockEdges[k]>0,"coverage","per-FU acceptance-response-cancel-reset-clock coverage");
  for(auto n:b.directedPairs)b.check(n==3,"coverage","missing directed FU transition");
  b.check(handoff?b.overlaps>10021:b.overlaps==0,"coverage","handoff mode coverage");b.finish();
}
int main(int argc,char** argv) {
  if(argc<2||argc>3){std::cerr<<"usage: parent_test vectors.tsv [identity|wen|high|cancel|busy|route|clock]\n";return 2;}
  const std::string fault=argc==3?argv[2]:"";
  try {
    need(fault.empty()||std::set<std::string>{"identity","wen","high","cancel","busy","route","clock"}.count(fault),"input","unknown fault");
    auto data=load(argv[1]);Bench b(fault);test(b,data);
    if(!fault.empty()){std::cerr<<"O1_PARENT_FAULT_ESCAPED "<<fault<<'\n';return 3;}
    for(unsigned k=0;k<3;k++) std::cout<<"O1_PARENT_FU kind="<<k<<" accepted="<<b.accepts[k]<<" responded="<<b.responds[k]
      <<" killed="<<b.kills[k]<<" reset_dropped="<<b.drops[k]<<" raw_killed_response="<<b.rawKilled[k]
      <<" latency_min="<<b.latMin[k]<<" latency_max="<<b.latMax[k]<<" latency_samples="<<b.latSamples[k]<<" clock_edges="<<b.clockEdges[k]<<'\n';
    std::cout<<"O1_PARENT_PASS mode="<<O1_PARENT_HANDOFF<<" cycles="<<b.tick<<" groups="<<b.groups<<" accepted="<<b.accepted
      <<" responses="<<b.responses<<" cancelled="<<b.cancels<<" reset_dropped="<<b.resets<<" handoffs="<<b.overlaps
      <<" stalls="<<b.stalls<<" redirects="<<b.redirects<<" reset_cases="<<b.resetCases<<" idle_clock_samples="<<b.idleClockSamples
      <<" cancel_idle_clock_on="<<b.cancelIdleClockOn<<" legacy_boundary_valid_suppressed="<<b.legacySuppressed
      <<" parent_tested=1 fullcore_tested=0\n";return 0;
  } catch(const Failure& e) {
    std::cerr<<"O1_PARENT_FAIL "<<e.category<<'\n';if(fault.empty())std::cerr<<e.what()<<'\n';return 1;
  } catch(const std::exception& e) {std::cerr<<"O1_PARENT_ERROR "<<e.what()<<'\n';return 2;}
}
