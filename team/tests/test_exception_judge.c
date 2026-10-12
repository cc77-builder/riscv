#include "harness.h"
#include <stdio.h>
#include <stdlib.h>

static unsigned char expected[32][16], actual[32][16];
static void require(enum verdict actual_value, enum verdict wanted, const char *name) {
  if (actual_value!=wanted) {
    fprintf(stderr,"%s: wanted %s, got %s\n",name,verdict_name(wanted),verdict_name(actual_value));
    exit(1);
  }
}
int main(void) {
  struct trap_record good={0};
  struct expectation e={{0,8,0,3,1,0,0},2,expected};
  good.pre=(struct vector_csrs){0,8,0,3,1,7}; good.post=good.pre;
  good.expected_pc=good.epc=0x80000100; good.cause=2; good.trap_count=1;
  good.pre_status=good.raw_status=0x600; good.phase=1;
  for (unsigned r=0; r<32; ++r) for (unsigned b=0; b<16; ++b) expected[r][b]=actual[r][b]=0xAA;
  require(judge(&good,&e,actual,1),PASS,"precise exception");
  struct trap_record bad=good;
  bad.epc+=4; require(judge(&bad,&e,actual,1),FAULT_PC,"wrong fault PC");
  bad=good; bad.cause=UINT64_C(1)<<63|2; require(judge(&bad,&e,actual,1),CAUSE,"interrupt is not synchronous illegal");
  bad=good; bad.trap_count=0; require(judge(&bad,&e,actual,1),TRAP_COUNT,"missing trap");
  bad=good; bad.trap_count=2; require(judge(&bad,&e,actual,1),TRAP_COUNT,"duplicate trap");
  bad=good; bad.errors=ERR_UNARMED; require(judge(&bad,&e,actual,1),TRAP_PROTOCOL,"preparation trap");
  bad=good; bad.post.vxsat=0; require(judge(&bad,&e,actual,1),CSR_CHANGED,"vxsat unexpectedly cleared");
  bad=good; bad.post.vstart=1; require(judge(&bad,&e,actual,1),CSR_CHANGED,"vstart changed");
  bad=good; bad.pre.vl=7; require(judge(&bad,&e,actual,1),UNREACHABLE,"initial state not reached");
  actual[10][15]^=1; require(judge(&good,&e,actual,1),VECTOR_CHANGED,"high 96 bits compared"); actual[10][15]^=1;
  actual[31][0]^=1; require(judge(&good,&e,actual,1),VECTOR_CHANGED,"nonpurpose register compared"); actual[31][0]^=1;
  require(judge(&good,&e,actual,0),GUARD_CHANGED,"memory guard");
  bad=good; bad.phase=2; require(judge(&bad,&e,actual,1),CAPTURE_PHASE,"wrong capture phase");
  e.config.vs_off=1; bad=good; bad.pre_status=bad.raw_status=0; bad.phase=2;
  require(judge(&bad,&e,actual,1),PASS,"VS Off captured then re-enabled");
  bad.phase=1; require(judge(&bad,&e,actual,1),CAPTURE_PHASE,"VS Off must not fabricate raw CSR access");
  e.config.vs_off=0; e.config.vtype=0x100; e.config.vl=8;
  bad=good; bad.pre.vtype=UINT64_C(1)<<63; bad.pre.vl=0; bad.post=bad.pre;
  require(judge(&bad,&e,actual,1),PASS,"vill/vl coupling");
  e.config.vtype=0; e.cause=0; bad=good; bad.trap_count=0;
  require(judge(&bad,&e,actual,1),PASS,"successful instruction");
  bad.trap_count=1; require(judge(&bad,&e,actual,1),TRAP_COUNT,"legal vdot rejected by unextended platform");
  puts("EXCEPTION_JUDGE_PASS checks=18");
  return 0;
}
