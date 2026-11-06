#include <klib.h>
#include <stdint.h>

typedef void (*case_fn)(const int8_t *, const int8_t *, uint32_t *, uint64_t *);
extern void dot16_smoke_case0(const int8_t *, const int8_t *, uint32_t *, uint64_t *);
extern void dot16_smoke_case1(const int8_t *, const int8_t *, uint32_t *, uint64_t *);
extern void dot16_smoke_case2(const int8_t *, const int8_t *, uint32_t *, uint64_t *);
extern void dot16_smoke_case3(const int8_t *, const int8_t *, uint32_t *, uint64_t *);
extern void dot16_smoke_case4(const int8_t *, const int8_t *, uint32_t *, uint64_t *);
extern void dot16_smoke_case5(const int8_t *, const int8_t *, uint32_t *, uint64_t *);

#define Z8 0,0,0,0,0,0,0,0
#define N8 -128,-128,-128,-128,-128,-128,-128,-128
#define P8 127,127,127,127,127,127,127,127
#define S8 -128,127,-1,0,1,2,-2,3

static const int8_t inputs[6][2][16] __attribute__((aligned(16))) = {
  {{Z8,N8}, {Z8,N8}},
  {{Z8,N8}, {Z8,N8}},
  {{N8,N8}, {N8,N8}},
  {{N8,N8}, {P8,P8}},
  {{S8,S8}, {S8,S8}},
  {{N8,N8}, {P8,P8}}
};
static const case_fn run_case[6] = {
  dot16_smoke_case0, dot16_smoke_case1, dot16_smoke_case2,
  dot16_smoke_case3, dot16_smoke_case4, dot16_smoke_case5
};
static const unsigned lanes[6] = {8,16,16,16,16,8};

int main(void) {
  unsigned long vlenb;
  __asm__ volatile("li t0, 0x200; csrs mstatus, t0; csrwi vstart, 0; csrwi vcsr, 0; csrr %0, vlenb"
                   : "=r"(vlenb) : : "t0", "memory");
  printf("DOT16_CORE_SMOKE_BEGIN schema=1 cases=6 vlenb=%d\n", (int)vlenb);
  if (vlenb != 16) {
    printf("DOT16_CORE_SMOKE_FAIL reason=vlenb\n");
    return 1;
  }
  for (unsigned c = 0; c < 6; ++c) {
    uint32_t out[4] __attribute__((aligned(16))) = {0xdeadbeef,0x13579bdf,0x2468ace0,0x55aa55aa};
    uint64_t meta[4] = {~0ull,~0ull,~0ull,~0ull};
    int64_t golden = 0;
    for (unsigned i = 0; i < lanes[c]; ++i) {
      golden += (int64_t)inputs[c][0][i] * (int64_t)inputs[c][1][i];
    }
    run_case[c](inputs[c][0], inputs[c][1], out, meta);
    if (meta[0] != lanes[c] || meta[1] != 0xc0 || meta[2] != 0 || meta[3] != 4) {
      printf("DOT16_CORE_SMOKE_FAIL case=%d reason=vector_config vl=%d vtype=%x vstart=%d storevl=%d\n",
             (int)c, (int)meta[0], (unsigned)meta[1], (int)meta[2], (int)meta[3]);
      return 2;
    }
    if (out[0] != (uint32_t)golden || out[1] != 0 || out[2] != 0 || out[3] != 0) {
      printf("DOT16_CORE_SMOKE_FAIL case=%d reason=result expected=%08x actual=%08x,%08x,%08x,%08x\n",
             (int)c, (uint32_t)golden, out[0], out[1], out[2], out[3]);
      return 3;
    }
    printf("DOT16_CORE_SMOKE_CASE case=%d vl=%d low=%08x high96=zero PASS\n", (int)c, (int)meta[0], out[0]);
  }
  printf("DOT16_CORE_SMOKE_PASS cases=6 dot8=2 dot16=4 failures=0\n");
  return 0;
}
