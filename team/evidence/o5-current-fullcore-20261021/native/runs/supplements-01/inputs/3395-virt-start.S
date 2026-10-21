.option norvc
.section .text.init
.globl _start
_start:
  .option push
  .option norelax
  la gp, __global_pointer$
  .option pop
  la sp, virt_stack_top
  la t0, __bss_start
  la t1, __bss_end
1: bgeu t0, t1, 2f
  sd zero, 0(t0)
  addi t0, t0, 8
  j 1b
2: call main
  tail platform_halt
.section .bss
.balign 16
virt_stack:
  .space 16384
virt_stack_top:
