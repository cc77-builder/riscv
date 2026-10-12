/* Audit fixture: calls the actual judge, not an emulator pass result. */
#include "harness.h"
#include <stdio.h>
static unsigned char registers[32][16];
int main(void) {
  struct trap_record r={0};
  struct expectation e={{0,7,0,3,1,0,0},2,registers};
  r.pre=(struct vector_csrs){0,7,0,3,1,7};
  r.post=r.pre;
  r.expected_pc=r.epc=0x80000100;
  r.cause=2; r.trap_count=1; r.phase=1;
  r.pre_status=r.raw_status=0x600;
  enum verdict control=judge(&r,&e,registers,1);
  r.raw_status=0x200;
  enum verdict changed=judge(&r,&e,registers,1);
  printf("AUDIT_JUDGE_VS control=%s illegal_pre_vs=3 illegal_post_vs=1 changed_verdict=%s\n",
         verdict_name(control),verdict_name(changed));
  return control==PASS && changed==PASS ? 0 : 1;
}
