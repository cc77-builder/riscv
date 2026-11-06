/* Independent team candidate. The original quantize and math library are
 * linked unchanged. See CONTRACT.md for the non-aliasing caller domain. */
.option push
.option norvc
.option norelax
.option nopic
.section .text.r2_quantize_gs32_rvv,"ax",@progbits
.balign 64
.global r2_quantize_gs32_rvv
.type r2_quantize_gs32_rvv, @function
r2_quantize_gs32_rvv:
  /* a0 = {int8_t *q, float *s}, a1 = float input, a2 = int length.
   * Keep all three arguments intact for an exact whole-call fallback. */
  frcsr t3
  andi t0, t3, 224
  bnez t0, .Lquantize_scalar
  blez a2, .Lquantize_scalar
  andi t0, a2, 31
  bnez t0, .Lquantize_scalar
  la t0, GS
  lw t0, 0(t0)
  li t2, 32
  bne t0, t2, .Lquantize_scalar
  csrr t0, vstart
  bnez t0, .Lquantize_scalar
  csrr t4, vtype
  bltz t4, .Lquantize_scalar
  csrr t5, vl
  vsetvli t0, t2, e32, m8, ta, ma
  bne t0, t2, .Lquantize_restore_scalar
  ld a3, 0(a0)
  ld a4, 8(a0)
  mv a5, a1
  srli a6, a2, 5
  li a7, 0x7f800000
  li t6, 0x7fffffff
  li t0, 0x42fe0000
  fmv.w.x ft2, t0

.Lquantize_group:
  vsetvli zero, t2, e32, m8, ta, ma
  vle32.v v8, (a5)
  vand.vx v16, v8, t6
  vmv.s.x v1, zero
  vredmaxu.vs v1, v16, v1
  vmv.x.s t0, v1
  beqz t0, .Lquantize_restore_scalar
  bgeu t0, a7, .Lquantize_restore_scalar
  fmv.w.x ft0, t0
  fdiv.s ft1, ft0, ft2, rne
  fmv.x.w t0, ft1
  li t1, 0x00800000
  bltu t0, t1, .Lquantize_restore_scalar
  fsw ft1, 0(a4)
  vfdiv.vf v8, v8, ft1
  /* Original round hides its conversion's NX, but keeps division flags.
   * Restore this post-div snapshot, never the entry snapshot on success. */
  frcsr t0
  fsrmi 4
  vfcvt.x.f.v v16, v8
  fscsr t0
  vsetvli zero, t2, e16, m4, ta, ma
  vncvt.x.x.w v8, v16
  vsetvli zero, t2, e8, m2, ta, ma
  vncvt.x.x.w v16, v8
  vse8.v v16, (a3)
  addi a5, a5, 128
  addi a3, a3, 32
  addi a4, a4, 4
  addi a6, a6, -1
  bnez a6, .Lquantize_group
  vsetvl zero, t5, t4
  ret

.Lquantize_restore_scalar:
  /* Some earlier groups may have been stored. Their input is disjoint from
   * all outputs, so the unchanged scalar function safely overwrites them.
   * Restart its FP environment too, including all entry exception flags. */
  fscsr t3
  vsetvl zero, t5, t4
.Lquantize_scalar:
  tail quantize
.size r2_quantize_gs32_rvv, .-r2_quantize_gs32_rvv
.option pop
.section .note.GNU-stack,"",@progbits
