/* Actual diagnostic emitter with a controlled high-byte mismatch. */
#include "diagnostics.h"
#include <stdio.h>
static struct trap_record record;
static unsigned char actual[32][16], expected[32][16];
void _putc(char ch) { putchar(ch); }
int main(void) {
  record.pre_valid=1; record.phase=1;
  for (unsigned i=0; i<16; ++i) { record.pre_regs[8][i]=0xA5; record.pre_regs[9][i]=0x5A; }
  actual[10][15]=128;
  struct diagnostic_context context={"diagnostic-negative",0x0294050b,0,0x80000000,0x80000004,
    &record,actual,expected};
  report_diagnostic(&context);
  return 0;
}
