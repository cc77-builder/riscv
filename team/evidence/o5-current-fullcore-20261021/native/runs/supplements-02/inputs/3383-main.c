#include <klib.h>
#include <stdint.h>
#include "identity.h"

extern unsigned long vadd8(const uint8_t *a, const uint8_t *b, uint8_t *out);

static const uint8_t inputs[3][2][8] = {
  {{1, 2, 3, 4, 5, 6, 7, 8}, {8, 7, 6, 5, 4, 3, 2, 1}},
  {{255, 254, 253, 252, 251, 250, 249, 248}, {255, 254, 253, 252, 251, 250, 249, 248}},
  {{127, 128, 255, 0, 1, 128, 127, 255}, {1, 255, 1, 0, 255, 128, 127, 255}}
};

int main(void) {
  printf("hello xiangshan, 我是%s, IPaddress=%s\n", TEAM_ID, HOST_IP);
  printf("identity_status=placeholder; IPaddress is WSL host IPv4\n");
  unsigned long vlbytes;
  __asm__ volatile("li t0, 0x200; csrs mstatus, t0; csrwi vstart, 0; csrwi vcsr, 0; csrr %0, vlenb"
                   : "=r"(vlbytes) : : "t0", "memory");
  printf("RVV VLEN=%d bits; SEW=8 LMUL=1 AVL=8\n", (int)(vlbytes * 8));
  if (vlbytes != 16) {
    printf("FAIL: expected VLEN=128\n");
    return 1;
  }
  uint8_t result[8] __attribute__((aligned(16)));
  for (int c = 0; c < 3; ++c) {
    unsigned long vl = vadd8(inputs[c][0], inputs[c][1], result);
    if (vl != 8) {
      printf("FAIL: case=%d VL=%d\n", c, (int)vl);
      return 2;
    }
    printf("vadd case=%d output:", c);
    for (int i = 0; i < 8; ++i) {
      uint8_t expected = (uint8_t)((unsigned int)inputs[c][0][i] + inputs[c][1][i]);
      printf(" %d", (int)result[i]);
      if (result[i] != expected) {
        printf("\nFAIL: lane=%d expected=%d actual=%d\n", i, (int)expected, (int)result[i]);
        return 3;
      }
    }
    printf(" PASS\n");
  }
  printf("HELLO_VADD_PASS cases=3 lanes=24\n");
  return 0;
}
