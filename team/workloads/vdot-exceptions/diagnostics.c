#include "diagnostics.h"
extern void _putc(char);
static void text(const char *s) { while (*s) _putc(*s++); }
static void number(unsigned v) {
  char b[11]; unsigned n=0;
  do { b[n++]='0'+v%10; v/=10; } while (v);
  while (n) _putc(b[--n]);
}
static void hex(uint64_t v) {
  text("0x");
  for (int i=60; i>=0; i-=4) _putc("0123456789abcdef"[(v>>i)&15]);
}
static void vector(const unsigned char *v) {
  text("0x");
  for (int i=15; i>=0; --i) { _putc("0123456789abcdef"[v[i]>>4]); _putc("0123456789abcdef"[v[i]&15]); }
}
void report_diagnostic(const struct diagnostic_context *c) {
  unsigned vd=(c->word>>7)&31, vs1=(c->word>>15)&31, vs2=(c->word>>20)&31;
  text("DIAGNOSTIC id="); text(c->id); text(" instruction="); hex(c->word);
  text(" vd="); number(vd); text(" vs1="); number(vs1); text(" vs2="); number(vs2);
  text(" begin_pc="); hex(c->begin_pc); text(" end_pc="); hex(c->end_pc);
  text(" pre_snapshot_valid="); number((unsigned)c->record->pre_valid);
  text(" post_snapshot_valid="); number(c->record->errors==0 && c->record->phase!=0);
  text(" pre_src1_128="); vector(c->record->pre_regs[vs1]);
  text(" pre_src2_128="); vector(c->record->pre_regs[vs2]);
  text(" post_src1_128="); vector(c->actual[vs1]);
  text(" post_src2_128="); vector(c->actual[vs2]);
  text(" actual_vd128="); vector(c->actual[vd]); text(" expected_vd128="); vector(c->expected[vd]);
  for (unsigned r=0; r<32; ++r) {
    if (c->scratch_mask & (1U<<r)) continue;
    for (unsigned b=0; b<16; ++b)
      if (c->actual[r][b]!=c->expected[r][b]) {
        text(" first_bad_reg="); number(r); text(" first_bad_byte="); number(b);
        text(" actual_byte="); number(c->actual[r][b]); text(" expected_byte="); number(c->expected[r][b]);
        _putc('\n'); return;
      }
  }
  text(" first_bad_reg=none\n");
}
