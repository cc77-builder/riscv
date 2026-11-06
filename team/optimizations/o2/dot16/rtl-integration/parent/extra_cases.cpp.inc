// Additional parent coverage only. The complete frozen campaign runs first.
// All expected arithmetic and request metadata originate in this test producer.
static Req dot16_req(const Data& source, unsigned serial, unsigned op) {
  Req q; q.data=source; q.op=op; q.vl=op==1?16:8;
  int32_t sum=0;
  for(unsigned i=0;i<(op==1?16U:8U);++i){
    const unsigned a=(source.a[i/4]>>(8*(i%4)))&255U;
    const unsigned c=(source.b[i/4]>>(8*(i%4)))&255U;
    const int32_t sa=a<128?int32_t(a):int32_t(a)-256;
    const int32_t sc=c<128?int32_t(c):int32_t(c)-256;
    sum+=sa*sc;
  }
  q.data.gold={uint32_t(sum),0,0,0};
  return identify(q,serial);
}
static void dot16_label(Bench& b,const std::string& tag,const Req& q){
  b.label="dot16-"+tag+"-k"+std::to_string(q.kind)+"-o"+std::to_string(q.op)
    +"-l"+std::to_string(q.vl)+"-z"+std::to_string(q.v0)
    +"-t"+std::to_string(q.ta)+"-m"+std::to_string(q.ma)
    +"-e"+std::to_string(q.sew)+"-u"+std::to_string(q.lmul)
    +"-s"+std::to_string(q.start)+"-v"+std::to_string(q.vill)
    +"-w"+std::to_string(q.vm)+"-x"+std::to_string(q.illegal());
}
static Cycle dot16_step(Bench& b,const std::string& tag,const Req& q,
                       bool valid=false,bool ready=true,Flush f={},bool reset=false){
  dot16_label(b,tag,q);return b.step(q,valid,ready,f,reset,false);
}
static void dot16_accept(Bench& b,const std::string& tag,const Req& q){
  unsigned wait=0;
  while(!dot16_step(b,tag,q,true).in)b.check(++wait<300,"watchdog","dot16 accept");
}
static void dot16_drain(Bench& b,const std::string& tag,const Req& noise){
  unsigned wait=0;
  while(b.active()){
    b.check(++wait<300,"watchdog","dot16 drain");dot16_step(b,tag,noise);
  }
}
static void dot16_visible(Bench& b,const std::string& tag,const Req& noise){
  unsigned wait=0;
  while(!dot16_step(b,tag,noise,false,false).visible)
    b.check(++wait<256,"watchdog","dot16 visible");
}
static void dot16_one(Bench& b,const std::string& tag,const Req& q,unsigned stall=0){
  b.check(!b.active(),"test","dot16 one needs empty pipeline");
  dot16_accept(b,tag,q);
  if(stall){
    dot16_visible(b,tag,q);
    for(unsigned i=1;i<stall;++i)dot16_step(b,tag,q,false,false);
  }
  dot16_drain(b,tag,q);
}
static void dot16_pair(Bench& b,const std::string& tag,const Req& a,const Req& n){
  b.check(!b.active(),"test","dot16 pair needs empty pipeline");
  b.check(dot16_step(b,tag+"a",a,true,false).in,"ready","dot16 pair first");
  b.check(dot16_step(b,tag+"b",n,true,false).in,"ready","dot16 pair second");
  b.check(b.p&&b.r,"occupancy","dot16 pair did not fill P/R");
}
static void dot16_parent_extra(Bench& b,const std::vector<Data>& data,unsigned& serial){
  b.check(!b.active(),"test","dot16 extension needs drained original campaign");
  const auto accepted=b.accepted,responses=b.responses,cancels=b.cancels,resets=b.resets;
  const Req noise=dot(data[13],serial++);
  if(!@DOT16_FEATURE@){
    for(unsigned policy=0;policy<8;++policy)for(unsigned which=0;which<2;++which){
      Req q=dot16_req(data[(policy*19+which)%data.size()],serial++,which?2:1);
      q.v0=policy&1;q.ta=(policy>>1)&1;q.ma=(policy>>2)&1;
      b.check(q.illegal(),"oracle","disabled new/unknown operation must be illegal");
      dot16_one(b,"off"+std::to_string(2*policy+which),q,policy%3);
    }
    b.check(b.accepted-accepted==16 && b.responses-responses==16 &&
      b.cancels==cancels && b.resets==resets,"coverage","disabled parent inventory");
    return;
  }
  // Four copies of each (operation, v0, ta, ma) combination, no backpressure.
  const auto overlap=b.overlaps,first=b.tick;
  for(unsigned i=0;i<64;++i){
    Req q=dot16_req(data[(i*37)%data.size()],serial++,i&1);
    q.v0=(i>>1)&1;q.ta=(i>>2)&1;q.ma=(i>>3)&1;
    const auto now=b.tick;auto c=dot16_step(b,"stream"+std::to_string(i),q,true);
    b.check(c.in && now==first+i,"latency","mixed parent II must equal one");
    b.check(c.out==(i>=2),"latency","mixed parent response must start at E2");
  }
  dot16_drain(b,"stream64drain",noise);
  b.check(b.accepted-accepted==64 && b.responses-responses==64 &&
    b.overlaps-overlap==62,"coverage","mixed parent stream inventory");
  // Includes upper-half-only, full positive and full negative accumulations.
  std::array<Data,4> directed{};
  directed[0].a={0,0,0x80808080U,0x80808080U};directed[0].b=directed[0].a;
  directed[1].a.fill(0x80808080U);directed[1].b.fill(0x80808080U);
  directed[2].a.fill(0x80808080U);directed[2].b.fill(0x7f7f7f7fU);
  directed[3].a={0x807fff01U,0xff00807fU,0x01020304U,0xfefdfcfbU};
  directed[3].b={0x7f8080ffU,0x01ff7f80U,0x807fff01U,0x12345678U};
  for(unsigned i=0;i<4;++i)for(unsigned op=0;op<2;++op){
    Req q=dot16_req(directed[i],serial++,op);
    if(i==0)b.check(q.data.gold[0]==(op?131072U:0U),"oracle","upper-half directed arithmetic");
    dot16_one(b,"directed"+std::to_string(i*2+op),q,1+i%3);
  }
  unsigned index=0;
  for(unsigned order=0;order<2;++order)for(unsigned delay:{1U,7U}){
    const std::string tag="blocked"+std::to_string(index++);
    Req a=dot16_req(data[61],serial++,order),n=dot16_req(data[67],serial++,1-order);
    dot16_accept(b,tag+"a",a);dot16_visible(b,tag+"hold",noise);
    b.check(dot16_step(b,tag+"b",n,true,false).in,"ready","dot16 fill P while R blocked");
    for(unsigned i=0;i<delay;++i)
      b.check(!dot16_step(b,tag+"hold",noise,true,false).in,"ready","dot16 full pair accepted third");
    auto c=dot16_step(b,tag+"drain",noise);
    b.check(c.out&&b.active(),"clock","dot16 R response must leave P alive");
    dot16_drain(b,tag+"drain",noise);
  }
  index=0;
  for(unsigned kind=1;kind<3;++kind)for(unsigned order=0;order<2;++order)
  for(unsigned delay:{0U,7U}){
    const std::string tag="switch"+std::to_string(index++);
    Req q=dot16_req(data[73],serial++,1),other=sample(data,kind,serial++);
    Req a=order?other:q,n=order?q:other;
    dot16_accept(b,tag+"a",a);
    if(delay){dot16_visible(b,tag+"hold",n);
      for(unsigned i=1;i<delay;++i)dot16_step(b,tag+"hold",n,true,false);}
    unsigned wait=0;bool got=false;
    do{
      b.check(++wait<300,"watchdog","dot16 DIV transition");
      const bool before=b.active();auto c=dot16_step(b,tag+"b",n,true);got=c.in;
      if(before)b.check(!c.in,"route","dot16 DIV switch accepted before old work drained");
    }while(!got);
    dot16_drain(b,tag+"drain",noise);
  }
  struct Dot16Rel{unsigned a,n,at;bool self;unsigned mask;};
  const Dot16Rel rels[]={{8,12,10,false,2},{12,8,10,false,1},
                        {95,0,95,true,3},{47,46,48,false,0}};
  index=0;
  for(unsigned order=0;order<2;++order)for(const auto rel:rels)for(bool ready:{false,true}){
    const std::string tag="pair"+std::to_string(index++);
    Req a=dot16_req(data[79],serial++,order),n=dot16_req(data[83],serial++,1-order);
    a.flag=rel.a/48;a.rob=rel.a%48;n.flag=rel.n/48;n.rob=rel.n%48;
    Flush f{true,bool(rel.at/48),rel.at%48,rel.self};
    b.check(unsigned(killed(a,f))+2*unsigned(killed(n,f))==rel.mask,"oracle","dot16 ROB relation");
    dot16_pair(b,tag,a,n);
    for(unsigned i=0;i<3;++i)dot16_step(b,tag+"hold",noise,false,false);
    auto c=dot16_step(b,tag+"redirect",noise,true,ready,f);
    b.check(!c.in&&c.killed==unsigned(bool(rel.mask&1))+unsigned(bool(rel.mask&2)),
      "cancel","dot16 mixed-pair redirect count");
    dot16_drain(b,tag+"drain",noise);
  }
  index=0;
  for(unsigned phase=0;phase<2;++phase)for(bool ready:{false,true}){
    const std::string tag="single"+std::to_string(index++);
    Req q=dot16_req(data[89],serial++,1);q.flag=false;q.rob=10;
    dot16_accept(b,tag+"a",q);
    if(phase)dot16_visible(b,tag+"hold",noise);
    auto c=dot16_step(b,tag+"redirect",noise,true,ready,{true,false,10,true});
    b.check(!c.in&&c.killed==1,"cancel","dot16 single-slot cancel");
    dot16_drain(b,tag+"drain",noise);
  }
  index=0;
  for(unsigned phase=0;phase<4;++phase)for(bool withFlush:{false,true}){
    const std::string tag="reset"+std::to_string(index++);
    Req a=dot16_req(data[97],serial++,phase==3&&withFlush?0:1);
    Req n=dot16_req(data[101],serial++,phase==3&&withFlush?1:0);
    a.rob=12;a.flag=false;n.rob=14;n.flag=false;
    if(phase==1)dot16_accept(b,tag+"a",a);
    if(phase==2){dot16_accept(b,tag+"a",a);dot16_visible(b,tag+"hold",noise);}
    if(phase==3)dot16_pair(b,tag,a,n);
    const auto oldResets=b.resets,oldCancels=b.cancels;
    dot16_step(b,tag+"edge",n,true,true,{withFlush,false,10,false},true);
    b.check(b.resets-oldResets==(phase==3?2U:unsigned(phase!=0))&&b.cancels==oldCancels,
      "reset","dot16 TE0 reset must dominate matching redirect");
    dot16_step(b,tag+"settle",noise,false,true,{},true);
    for(unsigned i=0;i<3;++i)dot16_step(b,tag+"settle",noise);
    dot16_one(b,tag+"recovery",dot16_req(data[103],serial++,1));
  }
  for(unsigned which=0;which<9;++which)for(unsigned v0=0;v0<2;++v0){
    Req q=dot16_req(data[(which*43)%data.size()],serial++,1);q.v0=v0;
    switch(which){
      case 0:q.vl=8;break;case 1:q.op=0;q.vl=16;break;
      case 2:q.op=2;break;case 3:q.vl=0;break;case 4:q.sew=1;break;
      case 5:q.lmul=1;break;case 6:q.vill=true;break;case 7:q.vm=false;break;
      case 8:q.start=1;break;
    }
    b.check(q.illegal(),"oracle","dot16 malformed request expected illegal");
    dot16_one(b,"illegal"+std::to_string(2*which+v0),q,which%3);
  }
  b.check(b.accepted-accepted==166&&b.responses-responses==138&&
    b.cancels-cancels==20&&b.resets-resets==8&&!b.active(),
    "coverage","enabled dot16 parent exact terminal inventory");
}
