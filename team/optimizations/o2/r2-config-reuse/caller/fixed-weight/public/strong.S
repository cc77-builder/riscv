.option norvc
.option norelax
.text
.balign 16
.global r4_gemv_8x32_basic_rvv
.type r4_gemv_8x32_basic_rvv, @function
r4_gemv_8x32_basic_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  li t0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
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
  addi t6, a2, 272
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
  addi t6, a2, 256
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
  addi t6, a2, 272
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
  addi t6, a2, 256
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
  addi t6, a2, 272
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
  addi t6, a2, 256
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
  addi t6, a2, 272
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
  addi t6, a2, 256
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
  addi t6, a2, 272
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
  addi t6, a2, 256
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
  addi t6, a2, 272
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
  addi t6, a2, 256
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
  addi t6, a2, 272
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
  addi t6, a2, 256
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
  addi t6, a2, 272
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
.size r4_gemv_8x32_basic_rvv, .-r4_gemv_8x32_basic_rvv
.balign 16
.global r4_gemv_8x32_reuse_rvv
.type r4_gemv_8x32_reuse_rvv, @function
r4_gemv_8x32_reuse_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
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
.size r4_gemv_8x32_reuse_rvv, .-r4_gemv_8x32_reuse_rvv
.balign 16
.global firstdot_gemv_8x32_reuse_rvv
.type firstdot_gemv_8x32_reuse_rvv, @function
firstdot_gemv_8x32_reuse_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
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
.size firstdot_gemv_8x32_reuse_rvv, .-firstdot_gemv_8x32_reuse_rvv
