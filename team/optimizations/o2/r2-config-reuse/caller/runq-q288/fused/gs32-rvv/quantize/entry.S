.option push
.option norvc
.option norelax
.section .text.quant_entry,"ax",@progbits
.global _start
.type _start,@function
_start:
  la sp, __quant_stack_top
  la gp, __global_pointer$
  li tp, 0
  li t0, 0x6600
  csrs mstatus, t0
  csrwi fcsr, 0
  csrwi vstart, 0
  tail team_quantize_main
.size _start, .-_start
.option pop
.section .note.GNU-stack,"",@progbits
