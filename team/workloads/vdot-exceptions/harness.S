#include "layout.h"
.option norvc
.text

/* All vector preparation/observation stays inside this assembly boundary.
 * The C caller is compiled without vectorization and uses only scalar code. */
.macro capture_csrs base
  csrr t0, vtype
  sd t0, \base+0(s0)
  csrr t0, vl
  sd t0, \base+8(s0)
  csrr t0, vstart
  sd t0, \base+16(s0)
  csrr t0, vxrm
  sd t0, \base+24(s0)
  csrr t0, vxsat
  sd t0, \base+32(s0)
  csrr t0, vcsr
  sd t0, \base+40(s0)
.endm

.macro load_reg n
  vle8.v v\n, (t0)
  addi t0, t0, 16
.endm
.macro store_reg n
  vse8.v v\n, (t0)
  addi t0, t0, 16
.endm

.globl vdot_run
.type vdot_run, @function
vdot_run:
  addi sp, sp, -96
  sd ra, 0(sp)
  sd s0, 8(sp)
  sd s1, 16(sp)
  sd s2, 24(sp)
  sd s3, 32(sp)
  sd s4, 40(sp)
  csrr t0, mtvec
  sd t0, 48(sp)
  csrr t0, mscratch
  sd t0, 56(sp)
  csrr t0, mie
  sd t0, 64(sp)
  csrr t0, mstatus
  sd t0, 72(sp)
  csrci mstatus, 8
  csrw mie, zero
  mv s0, a0
  mv s1, a1
  mv s2, a2
  mv s3, a3
  mv s4, a4
  la t0, vdot_abort
  sd t0, REC_ABORT_PC(s0)
  la t0, vdot_active_record
  sd s0, 0(t0)
  la t0, vdot_trap_stack_top
  csrw mscratch, t0
  la t0, vdot_trap_entry
  csrw mtvec, t0
  li t0, 0x600
  csrc mstatus, t0
  li t0, 0x200
  csrs mstatus, t0
  csrwi vstart, 0
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, s2
  .altmacro
  .set reg, 0
  .rept 32
    load_reg %reg
    .set reg, reg+1
  .endr
  .noaltmacro
  ld t0, CFG_VXRM(s1)
  csrw vxrm, t0
  ld t0, CFG_VXSAT(s1)
  csrw vxsat, t0
  ld t0, CFG_VL(s1)
  ld t1, CFG_VTYPE(s1)
  vsetvl zero, t0, t1
  ld t0, CFG_VSTART(s1)
  csrw vstart, t0
  capture_csrs REC_PRE_CSR
  ld t0, CFG_VS_OFF(s1)
  beqz t0, 1f
  li t0, 0x600
  csrc mstatus, t0
1: jr s4

.globl vdot_observe
vdot_observe:
  ld t0, REC_TRAP_COUNT(s0)
  bnez t0, 2f
  csrr t0, mstatus
  sd t0, REC_RAW_STATUS(s0)
  andi t0, t0, 0x600
  li t1, 1
  bnez t0, 1f
  li t0, 0x200
  csrs mstatus, t0
  li t1, 2
1: sd t1, REC_PHASE(s0)
  capture_csrs REC_POST_CSR
2: sd zero, REC_ARMED(s0)
  csrwi vstart, 0
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, s3
  .altmacro
  .set reg, 0
  .rept 32
    store_reg %reg
    .set reg, reg+1
  .endr
  .noaltmacro

vdot_abort:
  sd zero, REC_ARMED(s0)
  ld t0, 48(sp)
  csrw mtvec, t0
  ld t0, 56(sp)
  csrw mscratch, t0
  ld t0, 64(sp)
  csrw mie, t0
  ld t0, 72(sp)
  csrw mstatus, t0
  ld ra, 0(sp)
  ld s0, 8(sp)
  ld s1, 16(sp)
  ld s2, 24(sp)
  ld s3, 32(sp)
  ld s4, 40(sp)
  addi sp, sp, 96
  ret
.size vdot_run, .-vdot_run

.balign 4
.globl vdot_trap_entry
vdot_trap_entry:
  csrrw sp, mscratch, sp
  addi sp, sp, -256
  /* Save all GPRs before using temporaries; interrupted sp is in mscratch. */
  .irp n,1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    sd x\n, (\n*8)(sp)
  .endr
  csrr t0, mscratch
  sd t0, 16(sp)
  la t0, vdot_active_record
  ld s0, 0(t0)
  ld t0, REC_IN_HANDLER(s0)
  bnez t0, .Lnested
  li t0, 1
  sd t0, REC_IN_HANDLER(s0)
  ld t0, REC_TRAP_COUNT(s0)
  addi t0, t0, 1
  sd t0, REC_TRAP_COUNT(s0)
  csrr t0, mcause
  sd t0, REC_CAUSE(s0)
  csrr t0, mepc
  sd t0, REC_EPC(s0)
  csrr t0, mtval
  sd t0, REC_TVAL(s0)
  csrr t0, mstatus
  sd t0, REC_RAW_STATUS(s0)
  ld t0, REC_ARMED(s0)
  beqz t0, .Lunarmed
  ld t0, REC_EPC(s0)
  ld t1, REC_EXPECTED_PC(s0)
  bne t0, t1, .Lbadpc
  ld t0, REC_CAUSE(s0)
  ld t1, REC_EXPECTED_CAUSE(s0)
  bne t0, t1, .Lbadcause
  ld t0, REC_RAW_STATUS(s0)
  andi t0, t0, 0x600
  li t1, 1
  bnez t0, 1f
  /* VS Off: record raw status first, enable access, then capture CSRs. */
  li t0, 0x200
  csrs mstatus, t0
  li t1, 2
1: sd t1, REC_PHASE(s0)
  capture_csrs REC_POST_CSR
  ld t0, REC_RESUME_PC(s0)
  j .Lrestore
.Lunarmed:
  li t0, ERR_UNARMED
  j .Lprotocol
.Lbadpc:
  li t0, ERR_PC
  j .Lprotocol
.Lbadcause:
  li t0, ERR_CAUSE
.Lprotocol:
  sd t0, REC_ERRORS(s0)
  ld t0, REC_ABORT_PC(s0)
.Lrestore:
  csrw mepc, t0
  sd zero, REC_IN_HANDLER(s0)
  .irp n,1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    ld x\n, (\n*8)(sp)
  .endr
  addi sp, sp, 256
  csrrw sp, mscratch, sp
  mret
.Lnested:
  li t0, ERR_NESTED
  sd t0, REC_ERRORS(s0)
  li a0, 99
  tail platform_halt

.section .bss
.balign 16
vdot_trap_stack:
  .space 512
vdot_trap_stack_top:
