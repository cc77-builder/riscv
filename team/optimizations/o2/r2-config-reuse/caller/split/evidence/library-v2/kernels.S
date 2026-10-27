.option norvc
.option norelax
.text
.balign 16
.global split_gemv_8x32_vdot
.type split_gemv_8x32_vdot, @function
split_gemv_8x32_vdot:
  mv a3, a2
  mv a2, a0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v24, (t6)
  addi t6, a1, 8
  vle8.v v25, (t6)
  addi t6, a1, 16
  vle8.v v26, (t6)
  addi t6, a1, 24
  vle8.v v27, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 32
  vle8.v v17, (t6)
  addi t6, a2, 64
  vle8.v v18, (t6)
  addi t6, a2, 96
  vle8.v v19, (t6)
  .word 0x0388000b
  .word 0x0388808b
  .word 0x0389010b
  .word 0x0389818b
  addi t6, a2, 8
  vle8.v v16, (t6)
  addi t6, a2, 40
  vle8.v v17, (t6)
  addi t6, a2, 72
  vle8.v v18, (t6)
  addi t6, a2, 104
  vle8.v v19, (t6)
  .word 0x03980a0b
  .word 0x03988a8b
  .word 0x03990b0b
  .word 0x03998b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vadd.vv v1, v1, v21
  vadd.vv v2, v2, v22
  vadd.vv v3, v3, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 16
  vle8.v v16, (t6)
  addi t6, a2, 48
  vle8.v v17, (t6)
  addi t6, a2, 80
  vle8.v v18, (t6)
  addi t6, a2, 112
  vle8.v v19, (t6)
  .word 0x03a80a0b
  .word 0x03a88a8b
  .word 0x03a90b0b
  .word 0x03a98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vadd.vv v1, v1, v21
  vadd.vv v2, v2, v22
  vadd.vv v3, v3, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 24
  vle8.v v16, (t6)
  addi t6, a2, 56
  vle8.v v17, (t6)
  addi t6, a2, 88
  vle8.v v18, (t6)
  addi t6, a2, 120
  vle8.v v19, (t6)
  .word 0x03b80a0b
  .word 0x03b88a8b
  .word 0x03b90b0b
  .word 0x03b98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vadd.vv v1, v1, v21
  vadd.vv v2, v2, v22
  vadd.vv v3, v3, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 128
  vle8.v v16, (t6)
  addi t6, a2, 160
  vle8.v v17, (t6)
  addi t6, a2, 192
  vle8.v v18, (t6)
  addi t6, a2, 224
  vle8.v v19, (t6)
  .word 0x0388020b
  .word 0x0388828b
  .word 0x0389030b
  .word 0x0389838b
  addi t6, a2, 136
  vle8.v v16, (t6)
  addi t6, a2, 168
  vle8.v v17, (t6)
  addi t6, a2, 200
  vle8.v v18, (t6)
  addi t6, a2, 232
  vle8.v v19, (t6)
  .word 0x03980a0b
  .word 0x03988a8b
  .word 0x03990b0b
  .word 0x03998b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vadd.vv v5, v5, v21
  vadd.vv v6, v6, v22
  vadd.vv v7, v7, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 144
  vle8.v v16, (t6)
  addi t6, a2, 176
  vle8.v v17, (t6)
  addi t6, a2, 208
  vle8.v v18, (t6)
  addi t6, a2, 240
  vle8.v v19, (t6)
  .word 0x03a80a0b
  .word 0x03a88a8b
  .word 0x03a90b0b
  .word 0x03a98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vadd.vv v5, v5, v21
  vadd.vv v6, v6, v22
  vadd.vv v7, v7, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 152
  vle8.v v16, (t6)
  addi t6, a2, 184
  vle8.v v17, (t6)
  addi t6, a2, 216
  vle8.v v18, (t6)
  addi t6, a2, 248
  vle8.v v19, (t6)
  .word 0x03b80a0b
  .word 0x03b88a8b
  .word 0x03b90b0b
  .word 0x03b98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vadd.vv v5, v5, v21
  vadd.vv v6, v6, v22
  vadd.vv v7, v7, v23
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 256
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  vs1r.v v4, (t6)
  addi t6, t6, 16
  vs1r.v v5, (t6)
  addi t6, t6, 16
  vs1r.v v6, (t6)
  addi t6, t6, 16
  vs1r.v v7, (t6)
  addi t6, t6, 16
  ret
.size split_gemv_8x32_vdot, .-split_gemv_8x32_vdot
.balign 16
.global split_gemv_8x32_rvv0
.type split_gemv_8x32_rvv0, @function
split_gemv_8x32_rvv0:
  mv a3, a2
  mv a2, a0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vmv.s.x v0, t0
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 32
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 48
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v1, 0
  vmv.s.x v1, t0
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 64
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 80
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v2, 0
  vmv.s.x v2, t0
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 96
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 112
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v3, 0
  vmv.s.x v3, t0
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 128
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 144
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v4, 0
  vmv.s.x v4, t0
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 160
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 176
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v5, 0
  vmv.s.x v5, t0
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 192
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 208
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v6, 0
  vmv.s.x v6, t0
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 224
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 240
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v7, 0
  vmv.s.x v7, t0
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 256
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  vs1r.v v4, (t6)
  addi t6, t6, 16
  vs1r.v v5, (t6)
  addi t6, t6, 16
  vs1r.v v6, (t6)
  addi t6, t6, 16
  vs1r.v v7, (t6)
  addi t6, t6, 16
  ret
.size split_gemv_8x32_rvv0, .-split_gemv_8x32_rvv0
.balign 16
.global split_gemv_8x32_rvv1
.type split_gemv_8x32_rvv1, @function
split_gemv_8x32_rvv1:
  mv a3, a2
  mv a2, a0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v29, (t6)
  li t0, 0
  li t1, 0
  li t2, 0
  li t3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 32
  vle8.v v17, (t6)
  addi t6, a2, 64
  vle8.v v18, (t6)
  addi t6, a2, 96
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vmv.v.i v17, 0
  vmv.v.i v18, 0
  vmv.v.i v19, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vwredsum.vs v17, v22, v17
  vwredsum.vs v18, v24, v18
  vwredsum.vs v19, v26, v19
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vmv.x.s t6, v17
  addw t1, t1, t6
  vmv.x.s t6, v18
  addw t2, t2, t6
  vmv.x.s t6, v19
  addw t3, t3, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 16
  vle8.v v16, (t6)
  addi t6, a2, 48
  vle8.v v17, (t6)
  addi t6, a2, 80
  vle8.v v18, (t6)
  addi t6, a2, 112
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vmv.v.i v17, 0
  vmv.v.i v18, 0
  vmv.v.i v19, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vwredsum.vs v17, v22, v17
  vwredsum.vs v18, v24, v18
  vwredsum.vs v19, v26, v19
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vmv.x.s t6, v17
  addw t1, t1, t6
  vmv.x.s t6, v18
  addw t2, t2, t6
  vmv.x.s t6, v19
  addw t3, t3, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vmv.s.x v0, t0
  vmv.v.i v1, 0
  vmv.s.x v1, t1
  vmv.v.i v2, 0
  vmv.s.x v2, t2
  vmv.v.i v3, 0
  vmv.s.x v3, t3
  li t0, 0
  li t1, 0
  li t2, 0
  li t3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 128
  vle8.v v16, (t6)
  addi t6, a2, 160
  vle8.v v17, (t6)
  addi t6, a2, 192
  vle8.v v18, (t6)
  addi t6, a2, 224
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vmv.v.i v17, 0
  vmv.v.i v18, 0
  vmv.v.i v19, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vwredsum.vs v17, v22, v17
  vwredsum.vs v18, v24, v18
  vwredsum.vs v19, v26, v19
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vmv.x.s t6, v17
  addw t1, t1, t6
  vmv.x.s t6, v18
  addw t2, t2, t6
  vmv.x.s t6, v19
  addw t3, t3, t6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 144
  vle8.v v16, (t6)
  addi t6, a2, 176
  vle8.v v17, (t6)
  addi t6, a2, 208
  vle8.v v18, (t6)
  addi t6, a2, 240
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v16, 0
  vmv.v.i v17, 0
  vmv.v.i v18, 0
  vmv.v.i v19, 0
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v16, v20, v16
  vwredsum.vs v17, v22, v17
  vwredsum.vs v18, v24, v18
  vwredsum.vs v19, v26, v19
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v16
  addw t0, t0, t6
  vmv.x.s t6, v17
  addw t1, t1, t6
  vmv.x.s t6, v18
  addw t2, t2, t6
  vmv.x.s t6, v19
  addw t3, t3, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v4, 0
  vmv.s.x v4, t0
  vmv.v.i v5, 0
  vmv.s.x v5, t1
  vmv.v.i v6, 0
  vmv.s.x v6, t2
  vmv.v.i v7, 0
  vmv.s.x v7, t3
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 256
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  vs1r.v v4, (t6)
  addi t6, t6, 16
  vs1r.v v5, (t6)
  addi t6, t6, 16
  vs1r.v v6, (t6)
  addi t6, t6, 16
  vs1r.v v7, (t6)
  addi t6, t6, 16
  ret
.size split_gemv_8x32_rvv1, .-split_gemv_8x32_rvv1
.balign 16
.global split_gemv_8x32_rvv2
.type split_gemv_8x32_rvv2, @function
split_gemv_8x32_rvv2:
  mv a3, a2
  mv a2, a0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v1, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 32
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 48
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v2, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 64
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 80
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 96
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 112
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v4, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 128
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 144
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v5, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 160
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 176
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v6, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 192
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 208
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v7, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a2, 224
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v7, v20, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v28, (t6)
  addi t6, a2, 240
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v7, v20, v7
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 256
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  vs1r.v v4, (t6)
  addi t6, t6, 16
  vs1r.v v5, (t6)
  addi t6, t6, 16
  vs1r.v v6, (t6)
  addi t6, t6, 16
  vs1r.v v7, (t6)
  addi t6, t6, 16
  ret
.size split_gemv_8x32_rvv2, .-split_gemv_8x32_rvv2
.balign 16
.global split_gemv_8x32_rvv3
.type split_gemv_8x32_rvv3, @function
split_gemv_8x32_rvv3:
  mv a3, a2
  mv a2, a0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 16
  vle8.v v29, (t6)
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vmv.v.i v1, 0
  vmv.v.i v2, 0
  vmv.v.i v3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 32
  vle8.v v17, (t6)
  addi t6, a2, 64
  vle8.v v18, (t6)
  addi t6, a2, 96
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vwredsum.vs v1, v22, v1
  vwredsum.vs v2, v24, v2
  vwredsum.vs v3, v26, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 16
  vle8.v v16, (t6)
  addi t6, a2, 48
  vle8.v v17, (t6)
  addi t6, a2, 80
  vle8.v v18, (t6)
  addi t6, a2, 112
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vwredsum.vs v1, v22, v1
  vwredsum.vs v2, v24, v2
  vwredsum.vs v3, v26, v3
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v4, 0
  vmv.v.i v5, 0
  vmv.v.i v6, 0
  vmv.v.i v7, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 128
  vle8.v v16, (t6)
  addi t6, a2, 160
  vle8.v v17, (t6)
  addi t6, a2, 192
  vle8.v v18, (t6)
  addi t6, a2, 224
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vwredsum.vs v5, v22, v5
  vwredsum.vs v6, v24, v6
  vwredsum.vs v7, v26, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 144
  vle8.v v16, (t6)
  addi t6, a2, 176
  vle8.v v17, (t6)
  addi t6, a2, 208
  vle8.v v18, (t6)
  addi t6, a2, 240
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vwredsum.vs v5, v22, v5
  vwredsum.vs v6, v24, v6
  vwredsum.vs v7, v26, v7
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 256
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  vs1r.v v4, (t6)
  addi t6, t6, 16
  vs1r.v v5, (t6)
  addi t6, t6, 16
  vs1r.v v6, (t6)
  addi t6, t6, 16
  vs1r.v v7, (t6)
  addi t6, t6, 16
  ret
.size split_gemv_8x32_rvv3, .-split_gemv_8x32_rvv3
.balign 16
.global split_gemv_8x32_rvv4
.type split_gemv_8x32_rvv4, @function
split_gemv_8x32_rvv4:
  mv a3, a2
  mv a2, a0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a1, 0
  vle8.v v28, (t6)
  addi t6, a1, 16
  vle8.v v29, (t6)
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vmv.v.i v1, 0
  vmv.v.i v2, 0
  vmv.v.i v3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 32
  vle8.v v17, (t6)
  addi t6, a2, 64
  vle8.v v18, (t6)
  addi t6, a2, 96
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vwredsum.vs v1, v22, v1
  vwredsum.vs v2, v24, v2
  vwredsum.vs v3, v26, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 16
  vle8.v v16, (t6)
  addi t6, a2, 48
  vle8.v v17, (t6)
  addi t6, a2, 80
  vle8.v v18, (t6)
  addi t6, a2, 112
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vwredsum.vs v1, v22, v1
  vwredsum.vs v2, v24, v2
  vwredsum.vs v3, v26, v3
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v4, 0
  vmv.v.i v5, 0
  vmv.v.i v6, 0
  vmv.v.i v7, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 128
  vle8.v v16, (t6)
  addi t6, a2, 160
  vle8.v v17, (t6)
  addi t6, a2, 192
  vle8.v v18, (t6)
  addi t6, a2, 224
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vwredsum.vs v5, v22, v5
  vwredsum.vs v6, v24, v6
  vwredsum.vs v7, v26, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 144
  vle8.v v16, (t6)
  addi t6, a2, 176
  vle8.v v17, (t6)
  addi t6, a2, 208
  vle8.v v18, (t6)
  addi t6, a2, 240
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vwredsum.vs v5, v22, v5
  vwredsum.vs v6, v24, v6
  vwredsum.vs v7, v26, v7
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 256
  mv t6, a3
  vs1r.v v0, (t6)
  addi t6, t6, 16
  vs1r.v v1, (t6)
  addi t6, t6, 16
  vs1r.v v2, (t6)
  addi t6, t6, 16
  vs1r.v v3, (t6)
  addi t6, t6, 16
  vs1r.v v4, (t6)
  addi t6, t6, 16
  vs1r.v v5, (t6)
  addi t6, t6, 16
  vs1r.v v6, (t6)
  addi t6, t6, 16
  vs1r.v v7, (t6)
  addi t6, t6, 16
  ret
.size split_gemv_8x32_rvv4, .-split_gemv_8x32_rvv4
