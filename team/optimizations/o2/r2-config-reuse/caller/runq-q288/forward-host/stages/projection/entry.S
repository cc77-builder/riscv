/* Team-owned memory-only entry. No UART, syscalls or official startup patches. */
.section entry,"ax"
.option norelax
.global _start
.type _start,@function
_start:
  .irp r,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    li x\r,0
  .endr
  li t0,0x2200
  csrs mstatus,t0
  csrwi fcsr,0
  .irp r,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    fmv.w.x f\r,zero
  .endr
  la sp,_stack_pointer
  la tp,team_tls_area
  addi tp,tp,16
  mv t0,tp
  addi t1,tp,64
1:
  sd zero,0(t0)
  addi t0,t0,8
  bne t0,t1,1b
  call team_forward_main
.global full_success_trap
full_success_trap:
  .word 0x0000006b
2:
  j 2b
.size _start,.-_start
