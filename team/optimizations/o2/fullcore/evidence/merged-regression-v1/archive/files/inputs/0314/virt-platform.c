/* QEMU virt supports harness testing only; it has no vdot extension. */
#include "harness.h"
void _putc(char ch) {
  volatile unsigned char *uart=(volatile unsigned char *)0x10000000;
  while (!(uart[5]&0x20)) {}
  uart[0]=(unsigned char)ch;
}
void platform_halt(int code) {
  *(volatile unsigned *)0x100000=(unsigned)((code ? (code<<16)|0x3333 : 0x5555));
  for (;;) {}
}
