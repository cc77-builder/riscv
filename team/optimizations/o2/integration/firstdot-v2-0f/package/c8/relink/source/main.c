#include <stdint.h>
#include <stddef.h>
#include "selected_gemv_c8.h"
#include "cases.h"
extern void _putc(char);
static const uint64_t canary = UINT64_C(0xd15ea5e5cafebabe);
static struct { uint64_t head[2]; int8_t value[1088]; uint64_t tail[2]; } input __attribute__((aligned(16)));
static struct { uint64_t head[2]; unsigned char value[16][16]; uint64_t tail[2]; } output __attribute__((aligned(16)));
static void text(const char *s) { while (*s) _putc(*s++); }
static void decimal(uint64_t x) {
  char buf[21]; unsigned n=0;
  do { buf[n++]=(char)('0'+x%10); x/=10; } while(x);
  while(n) _putc(buf[--n]);
}
static void fill(unsigned char *p, unsigned n, unsigned char v) { while(n--) *p++=v; }
static uint64_t hash(const unsigned char *p, unsigned n) {
  uint64_t h=UINT64_C(14695981039346656037);
  while(n--) { h^=*p++; h*=UINT64_C(1099511628211); }
  return h;
}
static unsigned judge(const struct r4_c_case *c) {
  if(input.head[0]!=canary || input.head[1]!=canary || input.tail[0]!=canary || input.tail[1]!=canary ||
     output.head[0]!=canary || output.head[1]!=canary || output.tail[0]!=canary || output.tail[1]!=canary) return 1;
  for(unsigned i=0;i<c->size;++i) if(input.value[i]!=c->packed[i]) return 2;
  for(unsigned i=c->size;i<1088;++i) if((unsigned char)input.value[i]!=0x5a) return 3;
  for(unsigned row=0;row<c->m;++row) {
    int32_t wanted=0;
    for(unsigned col=0;col<c->k;++col) wanted+=(int32_t)c->packed[row*c->k+col]*c->packed[c->m*c->k+col];
    for(unsigned byte=0;byte<16;++byte) {
      unsigned char value=byte<4?(unsigned char)((uint32_t)wanted>>(8*byte)):0;
      if(output.value[row][byte]!=value) return 10+row;
    }
  }
  for(unsigned row=c->m;row<16;++row) for(unsigned byte=0;byte<16;++byte)
    if(output.value[row][byte]!=0xa6) return 30;
  uint64_t vl,vtype,vstart,vcsr;
  __asm__ volatile("csrr %0,vl; csrr %1,vtype; csrr %2,vstart; csrr %3,vcsr"
                   :"=r"(vl),"=r"(vtype),"=r"(vstart),"=r"(vcsr));
  if(vl!=8 || vtype!=0 || vstart!=0 || vcsr!=7) return 31;
  if(hash(&output.value[0][0],c->m*16)!=c->expected_hash) return 32;
  return 0;
}
int main(void) {
  __asm__ volatile("csrs mstatus,%0"::"r"((uint64_t)0x600):"memory");
  text("R4C_BEGIN cases="); decimal(R4C_COUNT); text(" contract=" R4C_CONTRACT "\n");
  for(unsigned seq=0;seq<R4C_COUNT;++seq) {
    const struct r4_c_case *c=&r4_c_cases[seq];
    fill((unsigned char *)input.value,1088,0x5a);
    for(unsigned i=0;i<c->size;++i) input.value[i]=c->packed[i];
    fill(&output.value[0][0],256,0xa6);
    input.head[0]=input.head[1]=input.tail[0]=input.tail[1]=canary;
    output.head[0]=output.head[1]=output.tail[0]=output.tail[1]=canary;
    c->entry(input.value,output.value);
    unsigned verdict=judge(c);
    if(verdict) { text("R4C_FAIL seq="); decimal(seq); text(" verdict="); decimal(verdict); _putc('\n'); return 1; }
    if(seq==0) {
      unsigned detected=0;
      output.value[0][0]^=1; detected+=judge(c)!=0; output.value[0][0]^=1;
      output.value[0][15]^=0x80; detected+=judge(c)!=0; output.value[0][15]^=0x80;
      output.tail[0]^=1; detected+=judge(c)!=0; output.tail[0]^=1;
      input.value[0]^=1; detected+=judge(c)!=0; input.value[0]^=1;
      output.value[15][15]^=1; detected+=judge(c)!=0; output.value[15][15]^=1;
      text("R4C_CONTROLS detected="); decimal(detected); text(" expected=5\n");
      if(detected!=5 || judge(c)) return 2;
    }
    text("R4C_CASE seq="); decimal(seq); text(" hash="); decimal(hash(&output.value[0][0],c->m*16)); _putc('\n');
  }
  text("R4C_END executed="); decimal(R4C_COUNT); text(" failures=0\n");
  return 0;
}
