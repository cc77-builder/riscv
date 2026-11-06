static void dot16_decode_extra(){
  require(cases==131109,"original transaction inventory changed");
  require(simple_checks[0]==131109 && complex_checks[0]==131373,
          "original observed operation inventory changed");
  const auto before=cases;
  uint64_t rejected=0,neighbours=0;
  d.io_valid=0;d.io_redirect=0;d.io_out_ready=1;
  d.io_vsew=0;d.io_vlmul=0;d.io_vill=0;d.io_vstart=0;d.io_vs_off=0;
  requested_op=1;probe_fault_enabled=true;
  if(!@DOT16_FEATURE@){
    for(unsigned policy=0;policy<4;++policy){
      d.io_vta=policy&1;d.io_vma=policy>>1;
      for(unsigned vd=0;vd<32;++vd)for(unsigned vs1=0;vs1<32;++vs1)for(unsigned vs2=0;vs2<32;++vs2){
        d.io_word=word(vd,vs1,vs2);eval();
        require(!d.io_classified && !d.io_simple_vdot,"disabled dot16 classified/routed as vdot");
        ++rejected;
      }
    }
    require(rejected==131072 && cases==before,"disabled classification inventory changed");
  }else{
    for(unsigned policy=0;policy<4;++policy){
      d.io_vta=policy&1;d.io_vma=policy>>1;
      for(unsigned vd=0;vd<32;++vd)for(unsigned vs1=0;vs1<32;++vs1)for(unsigned vs2=0;vs2<32;++vs2)
        transaction(vd,vs1,vs2,false);
    }
    for(unsigned sew=0;sew<4;++sew)for(unsigned lmul=0;lmul<8;++lmul){
      d.io_vsew=sew;d.io_vlmul=lmul;
      transaction(10,9,8,sew!=0||lmul!=0,true);
    }
    d.io_vsew=0;d.io_vlmul=0;
    d.io_vill=1;transaction(0,0,0,true);d.io_vill=0;
    d.io_vs_off=1;transaction(10,9,8,true);d.io_vs_off=0;
    d.io_vstart=7;transaction(10,9,8,true,true);d.io_vstart=0;
    transaction(0,0,0,false);
    d.io_word=word(10,9,8);d.io_valid=1;d.io_out_ready=0;tick();
    d.io_valid=0;d.io_redirect=1;tick();
    require(!d.io_out_valid&&!d.io_extra_valid,"dot16 redirect left a pending uop");
    d.io_redirect=0;d.io_out_ready=1;
    transaction(10,9,8,false);
    for(unsigned bit=0;bit<32;++bit)if(0xfe00707fU&(1U<<bit)){
      d.io_word=word(10,9,8)^(1U<<bit);eval();
      require(!d.io_classified&&!d.io_simple_vdot,"dot16 mask neighbour decoded as vdot");
      ++neighbours;
    }
    require(cases-before==131109 && simple_checks[1]==131109 && complex_checks[1]==131373
            && neighbours==17,"enabled observed operation inventory changed");
  }
  requested_op=0;
  d.io_word=0x02940557;eval();
  require(!d.io_classified&&!d.io_simple_vdot&&d.io_complex,"post-dot16 vadd regression");
  require(probe_fault==0,"requested operation observation fault escaped");
  std::cout<<"DOT16_DECODE_EXTRA_PASS schema=1 feature="<<@DOT16_FEATURE@
    <<" old_transactions="<<before<<" new_transactions="<<(cases-before)
    <<" classification_rejects="<<rejected<<" neighbours="<<neighbours
    <<" simple_op0="<<simple_checks[0]<<" complex_op0="<<complex_checks[0]
    <<" simple_op1="<<simple_checks[1]<<" complex_op1="<<complex_checks[1]<<'\n';
}
