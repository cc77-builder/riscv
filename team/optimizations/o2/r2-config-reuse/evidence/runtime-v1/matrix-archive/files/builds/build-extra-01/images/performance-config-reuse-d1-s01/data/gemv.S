.option norvc
.option norelax
.text
.balign 16
.global r4_gemv_4x8_basic_vdot
.type r4_gemv_4x8_basic_vdot, @function
r4_gemv_4x8_basic_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v24, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  .word 0x0388000b
  addi t6, a2, 32
  vle8.v v24, (t6)
  addi t6, a2, 8
  vle8.v v16, (t6)
  .word 0x0388008b
  addi t6, a2, 32
  vle8.v v24, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  .word 0x0388010b
  addi t6, a2, 32
  vle8.v v24, (t6)
  addi t6, a2, 24
  vle8.v v16, (t6)
  .word 0x0388018b
  li t5, 32
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  ret
.size r4_gemv_4x8_basic_vdot, .-r4_gemv_4x8_basic_vdot
.balign 16
.global r4_gemv_4x8_basic_rvv
.type r4_gemv_4x8_basic_rvv, @function
r4_gemv_4x8_basic_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v28, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 8, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v1, 0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v28, (t6)
  addi t6, a2, 8
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 8, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v2, 0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v28, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 8, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v3, 0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v28, (t6)
  addi t6, a2, 24
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 8, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 32
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  ret
.size r4_gemv_4x8_basic_rvv, .-r4_gemv_4x8_basic_rvv
.balign 16
.global r4_gemv_4x8_reuse_vdot
.type r4_gemv_4x8_reuse_vdot, @function
r4_gemv_4x8_reuse_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v24, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 8
  vle8.v v17, (t6)
  addi t6, a2, 16
  vle8.v v18, (t6)
  addi t6, a2, 24
  vle8.v v19, (t6)
  .word 0x0388000b
  .word 0x0388808b
  .word 0x0389010b
  .word 0x0389818b
  li t5, 32
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  ret
.size r4_gemv_4x8_reuse_vdot, .-r4_gemv_4x8_reuse_vdot
.balign 16
.global r4_gemv_4x8_reuse_rvv
.type r4_gemv_4x8_reuse_rvv, @function
r4_gemv_4x8_reuse_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v28, (t6)
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vmv.v.i v1, 0
  vmv.v.i v2, 0
  vmv.v.i v3, 0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 8
  vle8.v v17, (t6)
  addi t6, a2, 16
  vle8.v v18, (t6)
  addi t6, a2, 24
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 8, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vwredsum.vs v1, v22, v1
  vwredsum.vs v2, v24, v2
  vwredsum.vs v3, v26, v3
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 32
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  ret
.size r4_gemv_4x8_reuse_rvv, .-r4_gemv_4x8_reuse_rvv
