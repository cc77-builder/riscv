/* Test-only wrapper. The reference instret interval includes the call and
 * fixed store/call/sampling overhead. Register preparation, state checks
 * and all comparisons are outside it; this is not a target-cycle measure. */
.option push
.option norvc
.option norelax
.section .text.quant_probe,"ax",@progbits
.global quant_probe
.type quant_probe,@function

.macro save_pair i, sreg, freg
  sd \sreg, (16+8*\i)(sp)
  fsd \freg, (112+8*\i)(sp)
.endm
.macro seed_pair i, sreg, freg
  li \sreg, (0x123456789abc0100+\i)
  li t0, (0x3ff1234567800100+\i)
  fmv.d.x \freg, t0
.endm
.macro check_pair i, sreg, freg
  li t0, (0x123456789abc0100+\i)
  xor t0, t0, \sreg
  snez t0, t0
  slli t0, t0, \i
  or t1, t1, t0
  fmv.x.d t2, \freg
  li t0, (0x3ff1234567800100+\i)
  xor t0, t0, t2
  snez t0, t0
  slli t0, t0, (12+\i)
  or t1, t1, t0
.endm
.macro restore_pair i, sreg, freg
  ld \sreg, (16+8*\i)(sp)
  fld \freg, (112+8*\i)(sp)
.endm
.macro state base
  frcsr t0
  sd t0, (\base+0)(t6)
  csrr t0, vl
  sd t0, (\base+8)(t6)
  csrr t0, vtype
  sd t0, (\base+16)(t6)
  csrr t0, vstart
  sd t0, (\base+24)(t6)
  csrr t0, vcsr
  sd t0, (\base+32)(t6)
.endm

quant_probe:
  /* a0/a1/a2: original arguments; a3: function; a4: 13-word record. */
  addi sp, sp, -224
  sd ra, 0(sp)
  sd a4, 8(sp)
  save_pair 0, s0, fs0
  save_pair 1, s1, fs1
  save_pair 2, s2, fs2
  save_pair 3, s3, fs3
  save_pair 4, s4, fs4
  save_pair 5, s5, fs5
  save_pair 6, s6, fs6
  save_pair 7, s7, fs7
  save_pair 8, s8, fs8
  save_pair 9, s9, fs9
  save_pair 10, s10, fs10
  save_pair 11, s11, fs11
  mv t6, a4
  state 0
  seed_pair 0, s0, fs0
  seed_pair 1, s1, fs1
  seed_pair 2, s2, fs2
  seed_pair 3, s3, fs3
  seed_pair 4, s4, fs4
  seed_pair 5, s5, fs5
  seed_pair 6, s6, fs6
  seed_pair 7, s7, fs7
  seed_pair 8, s8, fs8
  seed_pair 9, s9, fs9
  seed_pair 10, s10, fs10
  seed_pair 11, s11, fs11
  rdinstret t0
  sd t0, 88(t6)
  jalr ra, a3, 0
  rdinstret t0
  ld t6, 8(sp)
  sd t0, 96(t6)
  state 40
  li t1, 0
  check_pair 0, s0, fs0
  check_pair 1, s1, fs1
  check_pair 2, s2, fs2
  check_pair 3, s3, fs3
  check_pair 4, s4, fs4
  check_pair 5, s5, fs5
  check_pair 6, s6, fs6
  check_pair 7, s7, fs7
  check_pair 8, s8, fs8
  check_pair 9, s9, fs9
  check_pair 10, s10, fs10
  check_pair 11, s11, fs11
  sd t1, 80(t6)
  restore_pair 0, s0, fs0
  restore_pair 1, s1, fs1
  restore_pair 2, s2, fs2
  restore_pair 3, s3, fs3
  restore_pair 4, s4, fs4
  restore_pair 5, s5, fs5
  restore_pair 6, s6, fs6
  restore_pair 7, s7, fs7
  restore_pair 8, s8, fs8
  restore_pair 9, s9, fs9
  restore_pair 10, s10, fs10
  restore_pair 11, s11, fs11
  ld ra, 0(sp)
  addi sp, sp, 224
  ret
.size quant_probe, .-quant_probe
.option pop
.section .note.GNU-stack,"",@progbits
