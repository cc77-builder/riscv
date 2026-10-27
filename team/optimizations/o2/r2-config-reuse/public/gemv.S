.option norvc
.option norelax
.text
.balign 16
.global config_reuse_gemv_4x8_basic_vdot
.type config_reuse_gemv_4x8_basic_vdot, @function
config_reuse_gemv_4x8_basic_vdot:
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
.size config_reuse_gemv_4x8_basic_vdot, .-config_reuse_gemv_4x8_basic_vdot
.balign 16
.global config_reuse_gemv_4x8_basic_rvv
.type config_reuse_gemv_4x8_basic_rvv, @function
config_reuse_gemv_4x8_basic_rvv:
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
.size config_reuse_gemv_4x8_basic_rvv, .-config_reuse_gemv_4x8_basic_rvv
.balign 16
.global config_reuse_gemv_4x8_reuse_vdot
.type config_reuse_gemv_4x8_reuse_vdot, @function
config_reuse_gemv_4x8_reuse_vdot:
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
.size config_reuse_gemv_4x8_reuse_vdot, .-config_reuse_gemv_4x8_reuse_vdot
.balign 16
.global config_reuse_gemv_4x8_reuse_rvv
.type config_reuse_gemv_4x8_reuse_rvv, @function
config_reuse_gemv_4x8_reuse_rvv:
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
.size config_reuse_gemv_4x8_reuse_rvv, .-config_reuse_gemv_4x8_reuse_rvv

.option norvc
.option norelax
.text
.balign 16
.global config_reuse_gemv_8x32_basic_vdot
.type config_reuse_gemv_8x32_basic_vdot, @function
config_reuse_gemv_8x32_basic_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  .word 0x0388000b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 8
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 24
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 32
  vle8.v v16, (t6)
  .word 0x0388008b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 40
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 48
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 56
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 64
  vle8.v v16, (t6)
  .word 0x0388010b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 72
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 80
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 88
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 96
  vle8.v v16, (t6)
  .word 0x0388018b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 104
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 112
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 120
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 128
  vle8.v v16, (t6)
  .word 0x0388020b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 136
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 144
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 152
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 160
  vle8.v v16, (t6)
  .word 0x0388028b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 168
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 176
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 184
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 192
  vle8.v v16, (t6)
  .word 0x0388030b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 200
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 208
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 216
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 224
  vle8.v v16, (t6)
  .word 0x0388038b
  addi t6, a2, 264
  vle8.v v24, (t6)
  addi t6, a2, 232
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v24, (t6)
  addi t6, a2, 240
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 280
  vle8.v v24, (t6)
  addi t6, a2, 248
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
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
.size config_reuse_gemv_8x32_basic_vdot, .-config_reuse_gemv_8x32_basic_vdot
.balign 16
.global config_reuse_gemv_8x32_basic_rvv
.type config_reuse_gemv_8x32_basic_rvv, @function
config_reuse_gemv_8x32_basic_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v28, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v1, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 32
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v28, (t6)
  addi t6, a2, 48
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v2, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 64
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v28, (t6)
  addi t6, a2, 80
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 96
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v28, (t6)
  addi t6, a2, 112
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v4, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 128
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v28, (t6)
  addi t6, a2, 144
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v5, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 160
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v28, (t6)
  addi t6, a2, 176
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v6, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 192
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
  vle8.v v28, (t6)
  addi t6, a2, 208
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v7, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
  addi t6, a2, 224
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v7, v20, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 272
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
.size config_reuse_gemv_8x32_basic_rvv, .-config_reuse_gemv_8x32_basic_rvv
.balign 16
.global config_reuse_gemv_8x32_reuse_vdot
.type config_reuse_gemv_8x32_reuse_vdot, @function
config_reuse_gemv_8x32_reuse_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v24, (t6)
  addi t6, a2, 264
  vle8.v v25, (t6)
  addi t6, a2, 272
  vle8.v v26, (t6)
  addi t6, a2, 280
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
.size config_reuse_gemv_8x32_reuse_vdot, .-config_reuse_gemv_8x32_reuse_vdot
.balign 16
.global config_reuse_gemv_8x32_reuse_rvv
.type config_reuse_gemv_8x32_reuse_rvv, @function
config_reuse_gemv_8x32_reuse_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v28, (t6)
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
.size config_reuse_gemv_8x32_reuse_rvv, .-config_reuse_gemv_8x32_reuse_rvv

.option norvc
.option norelax
.text
.balign 16
.global config_reuse_gemv_16x64_basic_vdot
.type config_reuse_gemv_16x64_basic_vdot, @function
config_reuse_gemv_16x64_basic_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  .word 0x0388000b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 8
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 24
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 32
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 40
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 48
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 56
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 64
  vle8.v v16, (t6)
  .word 0x0388008b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 72
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 80
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 88
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 96
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 104
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 112
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 120
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v1, v1, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 128
  vle8.v v16, (t6)
  .word 0x0388010b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 136
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 144
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 152
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 160
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 168
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 176
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 184
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v2, v2, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 192
  vle8.v v16, (t6)
  .word 0x0388018b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 200
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 208
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 216
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 224
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 232
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 240
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 248
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v3, v3, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 256
  vle8.v v16, (t6)
  .word 0x0388020b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 264
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 272
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 280
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 288
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 296
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 304
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 312
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 320
  vle8.v v16, (t6)
  .word 0x0388028b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 328
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 336
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 344
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 352
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 360
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 368
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 376
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v5, v5, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 384
  vle8.v v16, (t6)
  .word 0x0388030b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 392
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 400
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 408
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 416
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 424
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 432
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 440
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v6, v6, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 448
  vle8.v v16, (t6)
  .word 0x0388038b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 456
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 464
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 472
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 480
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 488
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 496
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 504
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v7, v7, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 512
  vle8.v v16, (t6)
  .word 0x0388040b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 520
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 528
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 536
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 544
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 552
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 560
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 568
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 576
  vle8.v v16, (t6)
  .word 0x0388048b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 584
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v9, v9, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 592
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v9, v9, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 600
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v9, v9, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 608
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v9, v9, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 616
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v9, v9, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 624
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v9, v9, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 632
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v9, v9, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 640
  vle8.v v16, (t6)
  .word 0x0388050b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 648
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v10, v10, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 656
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v10, v10, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 664
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v10, v10, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 672
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v10, v10, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 680
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v10, v10, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 688
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v10, v10, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 696
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v10, v10, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 704
  vle8.v v16, (t6)
  .word 0x0388058b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 712
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v11, v11, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 720
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v11, v11, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 728
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v11, v11, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 736
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v11, v11, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 744
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v11, v11, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 752
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v11, v11, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 760
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v11, v11, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 768
  vle8.v v16, (t6)
  .word 0x0388060b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 776
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 784
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 792
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 800
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 808
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 816
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 824
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 832
  vle8.v v16, (t6)
  .word 0x0388068b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 840
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v13, v13, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 848
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v13, v13, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 856
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v13, v13, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 864
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v13, v13, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 872
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v13, v13, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 880
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v13, v13, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 888
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v13, v13, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 896
  vle8.v v16, (t6)
  .word 0x0388070b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 904
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v14, v14, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 912
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v14, v14, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 920
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v14, v14, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 928
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v14, v14, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 936
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v14, v14, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 944
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v14, v14, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 952
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v14, v14, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 960
  vle8.v v16, (t6)
  .word 0x0388078b
  addi t6, a2, 1032
  vle8.v v24, (t6)
  addi t6, a2, 968
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v15, v15, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v24, (t6)
  addi t6, a2, 976
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v15, v15, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1048
  vle8.v v24, (t6)
  addi t6, a2, 984
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v15, v15, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v24, (t6)
  addi t6, a2, 992
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v15, v15, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1064
  vle8.v v24, (t6)
  addi t6, a2, 1000
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v15, v15, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v24, (t6)
  addi t6, a2, 1008
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v15, v15, v20
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1080
  vle8.v v24, (t6)
  addi t6, a2, 1016
  vle8.v v16, (t6)
  .word 0x03880a0b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v15, v15, v20
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 1024
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
  vs1r.v v8, (t6)
  addi t6, t6, 16
  vs1r.v v9, (t6)
  addi t6, t6, 16
  vs1r.v v10, (t6)
  addi t6, t6, 16
  vs1r.v v11, (t6)
  addi t6, t6, 16
  vs1r.v v12, (t6)
  addi t6, t6, 16
  vs1r.v v13, (t6)
  addi t6, t6, 16
  vs1r.v v14, (t6)
  addi t6, t6, 16
  vs1r.v v15, (t6)
  addi t6, t6, 16
  ret
.size config_reuse_gemv_16x64_basic_vdot, .-config_reuse_gemv_16x64_basic_vdot
.balign 16
.global config_reuse_gemv_16x64_basic_rvv
.type config_reuse_gemv_16x64_basic_rvv, @function
config_reuse_gemv_16x64_basic_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 16
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 32
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 48
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v1, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 64
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 80
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 96
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 112
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v2, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 128
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 144
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 160
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 176
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 192
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 208
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 224
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 240
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v4, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 256
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 272
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 288
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 304
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v5, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 320
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 336
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 352
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 368
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v5, v20, v5
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v6, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 384
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 400
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 416
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 432
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v6, v20, v6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v7, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 448
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v7, v20, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 464
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v7, v20, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 480
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v7, v20, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 496
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v7, v20, v7
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v8, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 512
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 528
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 544
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 560
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v9, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 576
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v9, v20, v9
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 592
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v9, v20, v9
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 608
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v9, v20, v9
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 624
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v9, v20, v9
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v10, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 640
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v10, v20, v10
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 656
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v10, v20, v10
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 672
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v10, v20, v10
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 688
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v10, v20, v10
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v11, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 704
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v11, v20, v11
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 720
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v11, v20, v11
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 736
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v11, v20, v11
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 752
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v11, v20, v11
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v12, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 768
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 784
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 800
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 816
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v13, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 832
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v13, v20, v13
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 848
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v13, v20, v13
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 864
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v13, v20, v13
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 880
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v13, v20, v13
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v14, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 896
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v14, v20, v14
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 912
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v14, v20, v14
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 928
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v14, v20, v14
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 944
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v14, v20, v14
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v15, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 960
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v15, v20, v15
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1040
  vle8.v v28, (t6)
  addi t6, a2, 976
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v15, v20, v15
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 992
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v15, v20, v15
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1072
  vle8.v v28, (t6)
  addi t6, a2, 1008
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v15, v20, v15
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 1024
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
  vs1r.v v8, (t6)
  addi t6, t6, 16
  vs1r.v v9, (t6)
  addi t6, t6, 16
  vs1r.v v10, (t6)
  addi t6, t6, 16
  vs1r.v v11, (t6)
  addi t6, t6, 16
  vs1r.v v12, (t6)
  addi t6, t6, 16
  vs1r.v v13, (t6)
  addi t6, t6, 16
  vs1r.v v14, (t6)
  addi t6, t6, 16
  vs1r.v v15, (t6)
  addi t6, t6, 16
  ret
.size config_reuse_gemv_16x64_basic_rvv, .-config_reuse_gemv_16x64_basic_rvv
.balign 16
.global config_reuse_gemv_16x64_reuse_vdot
.type config_reuse_gemv_16x64_reuse_vdot, @function
config_reuse_gemv_16x64_reuse_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v24, (t6)
  addi t6, a2, 1032
  vle8.v v25, (t6)
  addi t6, a2, 1040
  vle8.v v26, (t6)
  addi t6, a2, 1048
  vle8.v v27, (t6)
  addi t6, a2, 1056
  vle8.v v28, (t6)
  addi t6, a2, 1064
  vle8.v v29, (t6)
  addi t6, a2, 1072
  vle8.v v30, (t6)
  addi t6, a2, 1080
  vle8.v v31, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 64
  vle8.v v17, (t6)
  addi t6, a2, 128
  vle8.v v18, (t6)
  addi t6, a2, 192
  vle8.v v19, (t6)
  .word 0x0388000b
  .word 0x0388808b
  .word 0x0389010b
  .word 0x0389818b
  addi t6, a2, 8
  vle8.v v16, (t6)
  addi t6, a2, 72
  vle8.v v17, (t6)
  addi t6, a2, 136
  vle8.v v18, (t6)
  addi t6, a2, 200
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
  addi t6, a2, 80
  vle8.v v17, (t6)
  addi t6, a2, 144
  vle8.v v18, (t6)
  addi t6, a2, 208
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
  addi t6, a2, 88
  vle8.v v17, (t6)
  addi t6, a2, 152
  vle8.v v18, (t6)
  addi t6, a2, 216
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
  addi t6, a2, 32
  vle8.v v16, (t6)
  addi t6, a2, 96
  vle8.v v17, (t6)
  addi t6, a2, 160
  vle8.v v18, (t6)
  addi t6, a2, 224
  vle8.v v19, (t6)
  .word 0x03c80a0b
  .word 0x03c88a8b
  .word 0x03c90b0b
  .word 0x03c98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vadd.vv v1, v1, v21
  vadd.vv v2, v2, v22
  vadd.vv v3, v3, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 40
  vle8.v v16, (t6)
  addi t6, a2, 104
  vle8.v v17, (t6)
  addi t6, a2, 168
  vle8.v v18, (t6)
  addi t6, a2, 232
  vle8.v v19, (t6)
  .word 0x03d80a0b
  .word 0x03d88a8b
  .word 0x03d90b0b
  .word 0x03d98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vadd.vv v1, v1, v21
  vadd.vv v2, v2, v22
  vadd.vv v3, v3, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 48
  vle8.v v16, (t6)
  addi t6, a2, 112
  vle8.v v17, (t6)
  addi t6, a2, 176
  vle8.v v18, (t6)
  addi t6, a2, 240
  vle8.v v19, (t6)
  .word 0x03e80a0b
  .word 0x03e88a8b
  .word 0x03e90b0b
  .word 0x03e98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vadd.vv v1, v1, v21
  vadd.vv v2, v2, v22
  vadd.vv v3, v3, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 56
  vle8.v v16, (t6)
  addi t6, a2, 120
  vle8.v v17, (t6)
  addi t6, a2, 184
  vle8.v v18, (t6)
  addi t6, a2, 248
  vle8.v v19, (t6)
  .word 0x03f80a0b
  .word 0x03f88a8b
  .word 0x03f90b0b
  .word 0x03f98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v0, v0, v20
  vadd.vv v1, v1, v21
  vadd.vv v2, v2, v22
  vadd.vv v3, v3, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 256
  vle8.v v16, (t6)
  addi t6, a2, 320
  vle8.v v17, (t6)
  addi t6, a2, 384
  vle8.v v18, (t6)
  addi t6, a2, 448
  vle8.v v19, (t6)
  .word 0x0388020b
  .word 0x0388828b
  .word 0x0389030b
  .word 0x0389838b
  addi t6, a2, 264
  vle8.v v16, (t6)
  addi t6, a2, 328
  vle8.v v17, (t6)
  addi t6, a2, 392
  vle8.v v18, (t6)
  addi t6, a2, 456
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
  addi t6, a2, 272
  vle8.v v16, (t6)
  addi t6, a2, 336
  vle8.v v17, (t6)
  addi t6, a2, 400
  vle8.v v18, (t6)
  addi t6, a2, 464
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
  addi t6, a2, 280
  vle8.v v16, (t6)
  addi t6, a2, 344
  vle8.v v17, (t6)
  addi t6, a2, 408
  vle8.v v18, (t6)
  addi t6, a2, 472
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
  addi t6, a2, 288
  vle8.v v16, (t6)
  addi t6, a2, 352
  vle8.v v17, (t6)
  addi t6, a2, 416
  vle8.v v18, (t6)
  addi t6, a2, 480
  vle8.v v19, (t6)
  .word 0x03c80a0b
  .word 0x03c88a8b
  .word 0x03c90b0b
  .word 0x03c98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vadd.vv v5, v5, v21
  vadd.vv v6, v6, v22
  vadd.vv v7, v7, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 296
  vle8.v v16, (t6)
  addi t6, a2, 360
  vle8.v v17, (t6)
  addi t6, a2, 424
  vle8.v v18, (t6)
  addi t6, a2, 488
  vle8.v v19, (t6)
  .word 0x03d80a0b
  .word 0x03d88a8b
  .word 0x03d90b0b
  .word 0x03d98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vadd.vv v5, v5, v21
  vadd.vv v6, v6, v22
  vadd.vv v7, v7, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 304
  vle8.v v16, (t6)
  addi t6, a2, 368
  vle8.v v17, (t6)
  addi t6, a2, 432
  vle8.v v18, (t6)
  addi t6, a2, 496
  vle8.v v19, (t6)
  .word 0x03e80a0b
  .word 0x03e88a8b
  .word 0x03e90b0b
  .word 0x03e98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vadd.vv v5, v5, v21
  vadd.vv v6, v6, v22
  vadd.vv v7, v7, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 312
  vle8.v v16, (t6)
  addi t6, a2, 376
  vle8.v v17, (t6)
  addi t6, a2, 440
  vle8.v v18, (t6)
  addi t6, a2, 504
  vle8.v v19, (t6)
  .word 0x03f80a0b
  .word 0x03f88a8b
  .word 0x03f90b0b
  .word 0x03f98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v4, v4, v20
  vadd.vv v5, v5, v21
  vadd.vv v6, v6, v22
  vadd.vv v7, v7, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 512
  vle8.v v16, (t6)
  addi t6, a2, 576
  vle8.v v17, (t6)
  addi t6, a2, 640
  vle8.v v18, (t6)
  addi t6, a2, 704
  vle8.v v19, (t6)
  .word 0x0388040b
  .word 0x0388848b
  .word 0x0389050b
  .word 0x0389858b
  addi t6, a2, 520
  vle8.v v16, (t6)
  addi t6, a2, 584
  vle8.v v17, (t6)
  addi t6, a2, 648
  vle8.v v18, (t6)
  addi t6, a2, 712
  vle8.v v19, (t6)
  .word 0x03980a0b
  .word 0x03988a8b
  .word 0x03990b0b
  .word 0x03998b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vadd.vv v9, v9, v21
  vadd.vv v10, v10, v22
  vadd.vv v11, v11, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 528
  vle8.v v16, (t6)
  addi t6, a2, 592
  vle8.v v17, (t6)
  addi t6, a2, 656
  vle8.v v18, (t6)
  addi t6, a2, 720
  vle8.v v19, (t6)
  .word 0x03a80a0b
  .word 0x03a88a8b
  .word 0x03a90b0b
  .word 0x03a98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vadd.vv v9, v9, v21
  vadd.vv v10, v10, v22
  vadd.vv v11, v11, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 536
  vle8.v v16, (t6)
  addi t6, a2, 600
  vle8.v v17, (t6)
  addi t6, a2, 664
  vle8.v v18, (t6)
  addi t6, a2, 728
  vle8.v v19, (t6)
  .word 0x03b80a0b
  .word 0x03b88a8b
  .word 0x03b90b0b
  .word 0x03b98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vadd.vv v9, v9, v21
  vadd.vv v10, v10, v22
  vadd.vv v11, v11, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 544
  vle8.v v16, (t6)
  addi t6, a2, 608
  vle8.v v17, (t6)
  addi t6, a2, 672
  vle8.v v18, (t6)
  addi t6, a2, 736
  vle8.v v19, (t6)
  .word 0x03c80a0b
  .word 0x03c88a8b
  .word 0x03c90b0b
  .word 0x03c98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vadd.vv v9, v9, v21
  vadd.vv v10, v10, v22
  vadd.vv v11, v11, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 552
  vle8.v v16, (t6)
  addi t6, a2, 616
  vle8.v v17, (t6)
  addi t6, a2, 680
  vle8.v v18, (t6)
  addi t6, a2, 744
  vle8.v v19, (t6)
  .word 0x03d80a0b
  .word 0x03d88a8b
  .word 0x03d90b0b
  .word 0x03d98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vadd.vv v9, v9, v21
  vadd.vv v10, v10, v22
  vadd.vv v11, v11, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 560
  vle8.v v16, (t6)
  addi t6, a2, 624
  vle8.v v17, (t6)
  addi t6, a2, 688
  vle8.v v18, (t6)
  addi t6, a2, 752
  vle8.v v19, (t6)
  .word 0x03e80a0b
  .word 0x03e88a8b
  .word 0x03e90b0b
  .word 0x03e98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vadd.vv v9, v9, v21
  vadd.vv v10, v10, v22
  vadd.vv v11, v11, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 568
  vle8.v v16, (t6)
  addi t6, a2, 632
  vle8.v v17, (t6)
  addi t6, a2, 696
  vle8.v v18, (t6)
  addi t6, a2, 760
  vle8.v v19, (t6)
  .word 0x03f80a0b
  .word 0x03f88a8b
  .word 0x03f90b0b
  .word 0x03f98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v8, v8, v20
  vadd.vv v9, v9, v21
  vadd.vv v10, v10, v22
  vadd.vv v11, v11, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 768
  vle8.v v16, (t6)
  addi t6, a2, 832
  vle8.v v17, (t6)
  addi t6, a2, 896
  vle8.v v18, (t6)
  addi t6, a2, 960
  vle8.v v19, (t6)
  .word 0x0388060b
  .word 0x0388868b
  .word 0x0389070b
  .word 0x0389878b
  addi t6, a2, 776
  vle8.v v16, (t6)
  addi t6, a2, 840
  vle8.v v17, (t6)
  addi t6, a2, 904
  vle8.v v18, (t6)
  addi t6, a2, 968
  vle8.v v19, (t6)
  .word 0x03980a0b
  .word 0x03988a8b
  .word 0x03990b0b
  .word 0x03998b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vadd.vv v13, v13, v21
  vadd.vv v14, v14, v22
  vadd.vv v15, v15, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 784
  vle8.v v16, (t6)
  addi t6, a2, 848
  vle8.v v17, (t6)
  addi t6, a2, 912
  vle8.v v18, (t6)
  addi t6, a2, 976
  vle8.v v19, (t6)
  .word 0x03a80a0b
  .word 0x03a88a8b
  .word 0x03a90b0b
  .word 0x03a98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vadd.vv v13, v13, v21
  vadd.vv v14, v14, v22
  vadd.vv v15, v15, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 792
  vle8.v v16, (t6)
  addi t6, a2, 856
  vle8.v v17, (t6)
  addi t6, a2, 920
  vle8.v v18, (t6)
  addi t6, a2, 984
  vle8.v v19, (t6)
  .word 0x03b80a0b
  .word 0x03b88a8b
  .word 0x03b90b0b
  .word 0x03b98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vadd.vv v13, v13, v21
  vadd.vv v14, v14, v22
  vadd.vv v15, v15, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 800
  vle8.v v16, (t6)
  addi t6, a2, 864
  vle8.v v17, (t6)
  addi t6, a2, 928
  vle8.v v18, (t6)
  addi t6, a2, 992
  vle8.v v19, (t6)
  .word 0x03c80a0b
  .word 0x03c88a8b
  .word 0x03c90b0b
  .word 0x03c98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vadd.vv v13, v13, v21
  vadd.vv v14, v14, v22
  vadd.vv v15, v15, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 808
  vle8.v v16, (t6)
  addi t6, a2, 872
  vle8.v v17, (t6)
  addi t6, a2, 936
  vle8.v v18, (t6)
  addi t6, a2, 1000
  vle8.v v19, (t6)
  .word 0x03d80a0b
  .word 0x03d88a8b
  .word 0x03d90b0b
  .word 0x03d98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vadd.vv v13, v13, v21
  vadd.vv v14, v14, v22
  vadd.vv v15, v15, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 816
  vle8.v v16, (t6)
  addi t6, a2, 880
  vle8.v v17, (t6)
  addi t6, a2, 944
  vle8.v v18, (t6)
  addi t6, a2, 1008
  vle8.v v19, (t6)
  .word 0x03e80a0b
  .word 0x03e88a8b
  .word 0x03e90b0b
  .word 0x03e98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vadd.vv v13, v13, v21
  vadd.vv v14, v14, v22
  vadd.vv v15, v15, v23
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 824
  vle8.v v16, (t6)
  addi t6, a2, 888
  vle8.v v17, (t6)
  addi t6, a2, 952
  vle8.v v18, (t6)
  addi t6, a2, 1016
  vle8.v v19, (t6)
  .word 0x03f80a0b
  .word 0x03f88a8b
  .word 0x03f90b0b
  .word 0x03f98b8b
  vsetivli zero, 4, e32, m1, tu, mu
  vadd.vv v12, v12, v20
  vadd.vv v13, v13, v21
  vadd.vv v14, v14, v22
  vadd.vv v15, v15, v23
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 1024
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
  vs1r.v v8, (t6)
  addi t6, t6, 16
  vs1r.v v9, (t6)
  addi t6, t6, 16
  vs1r.v v10, (t6)
  addi t6, t6, 16
  vs1r.v v11, (t6)
  addi t6, t6, 16
  vs1r.v v12, (t6)
  addi t6, t6, 16
  vs1r.v v13, (t6)
  addi t6, t6, 16
  vs1r.v v14, (t6)
  addi t6, t6, 16
  vs1r.v v15, (t6)
  addi t6, t6, 16
  ret
.size config_reuse_gemv_16x64_reuse_vdot, .-config_reuse_gemv_16x64_reuse_vdot
.balign 16
.global config_reuse_gemv_16x64_reuse_rvv
.type config_reuse_gemv_16x64_reuse_rvv, @function
config_reuse_gemv_16x64_reuse_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 1024
  vle8.v v28, (t6)
  addi t6, a2, 1040
  vle8.v v29, (t6)
  addi t6, a2, 1056
  vle8.v v30, (t6)
  addi t6, a2, 1072
  vle8.v v31, (t6)
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vmv.v.i v1, 0
  vmv.v.i v2, 0
  vmv.v.i v3, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 64
  vle8.v v17, (t6)
  addi t6, a2, 128
  vle8.v v18, (t6)
  addi t6, a2, 192
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
  addi t6, a2, 80
  vle8.v v17, (t6)
  addi t6, a2, 144
  vle8.v v18, (t6)
  addi t6, a2, 208
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
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 32
  vle8.v v16, (t6)
  addi t6, a2, 96
  vle8.v v17, (t6)
  addi t6, a2, 160
  vle8.v v18, (t6)
  addi t6, a2, 224
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v30
  vwmul.vv v22, v17, v30
  vwmul.vv v24, v18, v30
  vwmul.vv v26, v19, v30
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vwredsum.vs v1, v22, v1
  vwredsum.vs v2, v24, v2
  vwredsum.vs v3, v26, v3
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 48
  vle8.v v16, (t6)
  addi t6, a2, 112
  vle8.v v17, (t6)
  addi t6, a2, 176
  vle8.v v18, (t6)
  addi t6, a2, 240
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v31
  vwmul.vv v22, v17, v31
  vwmul.vv v24, v18, v31
  vwmul.vv v26, v19, v31
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
  addi t6, a2, 256
  vle8.v v16, (t6)
  addi t6, a2, 320
  vle8.v v17, (t6)
  addi t6, a2, 384
  vle8.v v18, (t6)
  addi t6, a2, 448
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
  addi t6, a2, 272
  vle8.v v16, (t6)
  addi t6, a2, 336
  vle8.v v17, (t6)
  addi t6, a2, 400
  vle8.v v18, (t6)
  addi t6, a2, 464
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
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 288
  vle8.v v16, (t6)
  addi t6, a2, 352
  vle8.v v17, (t6)
  addi t6, a2, 416
  vle8.v v18, (t6)
  addi t6, a2, 480
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v30
  vwmul.vv v22, v17, v30
  vwmul.vv v24, v18, v30
  vwmul.vv v26, v19, v30
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vwredsum.vs v5, v22, v5
  vwredsum.vs v6, v24, v6
  vwredsum.vs v7, v26, v7
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 304
  vle8.v v16, (t6)
  addi t6, a2, 368
  vle8.v v17, (t6)
  addi t6, a2, 432
  vle8.v v18, (t6)
  addi t6, a2, 496
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v31
  vwmul.vv v22, v17, v31
  vwmul.vv v24, v18, v31
  vwmul.vv v26, v19, v31
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v4, v20, v4
  vwredsum.vs v5, v22, v5
  vwredsum.vs v6, v24, v6
  vwredsum.vs v7, v26, v7
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v8, 0
  vmv.v.i v9, 0
  vmv.v.i v10, 0
  vmv.v.i v11, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 512
  vle8.v v16, (t6)
  addi t6, a2, 576
  vle8.v v17, (t6)
  addi t6, a2, 640
  vle8.v v18, (t6)
  addi t6, a2, 704
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vwredsum.vs v9, v22, v9
  vwredsum.vs v10, v24, v10
  vwredsum.vs v11, v26, v11
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 528
  vle8.v v16, (t6)
  addi t6, a2, 592
  vle8.v v17, (t6)
  addi t6, a2, 656
  vle8.v v18, (t6)
  addi t6, a2, 720
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vwredsum.vs v9, v22, v9
  vwredsum.vs v10, v24, v10
  vwredsum.vs v11, v26, v11
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 544
  vle8.v v16, (t6)
  addi t6, a2, 608
  vle8.v v17, (t6)
  addi t6, a2, 672
  vle8.v v18, (t6)
  addi t6, a2, 736
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v30
  vwmul.vv v22, v17, v30
  vwmul.vv v24, v18, v30
  vwmul.vv v26, v19, v30
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vwredsum.vs v9, v22, v9
  vwredsum.vs v10, v24, v10
  vwredsum.vs v11, v26, v11
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 560
  vle8.v v16, (t6)
  addi t6, a2, 624
  vle8.v v17, (t6)
  addi t6, a2, 688
  vle8.v v18, (t6)
  addi t6, a2, 752
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v31
  vwmul.vv v22, v17, v31
  vwmul.vv v24, v18, v31
  vwmul.vv v26, v19, v31
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v8, v20, v8
  vwredsum.vs v9, v22, v9
  vwredsum.vs v10, v24, v10
  vwredsum.vs v11, v26, v11
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v12, 0
  vmv.v.i v13, 0
  vmv.v.i v14, 0
  vmv.v.i v15, 0
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 768
  vle8.v v16, (t6)
  addi t6, a2, 832
  vle8.v v17, (t6)
  addi t6, a2, 896
  vle8.v v18, (t6)
  addi t6, a2, 960
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vwredsum.vs v13, v22, v13
  vwredsum.vs v14, v24, v14
  vwredsum.vs v15, v26, v15
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 784
  vle8.v v16, (t6)
  addi t6, a2, 848
  vle8.v v17, (t6)
  addi t6, a2, 912
  vle8.v v18, (t6)
  addi t6, a2, 976
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v29
  vwmul.vv v22, v17, v29
  vwmul.vv v24, v18, v29
  vwmul.vv v26, v19, v29
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vwredsum.vs v13, v22, v13
  vwredsum.vs v14, v24, v14
  vwredsum.vs v15, v26, v15
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 800
  vle8.v v16, (t6)
  addi t6, a2, 864
  vle8.v v17, (t6)
  addi t6, a2, 928
  vle8.v v18, (t6)
  addi t6, a2, 992
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v30
  vwmul.vv v22, v17, v30
  vwmul.vv v24, v18, v30
  vwmul.vv v26, v19, v30
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vwredsum.vs v13, v22, v13
  vwredsum.vs v14, v24, v14
  vwredsum.vs v15, v26, v15
  vsetivli zero, 16, e8, m1, tu, mu
  addi t6, a2, 816
  vle8.v v16, (t6)
  addi t6, a2, 880
  vle8.v v17, (t6)
  addi t6, a2, 944
  vle8.v v18, (t6)
  addi t6, a2, 1008
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v31
  vwmul.vv v22, v17, v31
  vwmul.vv v24, v18, v31
  vwmul.vv v26, v19, v31
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v12, v20, v12
  vwredsum.vs v13, v22, v13
  vwredsum.vs v14, v24, v14
  vwredsum.vs v15, v26, v15
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 1024
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
  vs1r.v v8, (t6)
  addi t6, t6, 16
  vs1r.v v9, (t6)
  addi t6, t6, 16
  vs1r.v v10, (t6)
  addi t6, t6, 16
  vs1r.v v11, (t6)
  addi t6, t6, 16
  vs1r.v v12, (t6)
  addi t6, t6, 16
  vs1r.v v13, (t6)
  addi t6, t6, 16
  vs1r.v v14, (t6)
  addi t6, t6, 16
  vs1r.v v15, (t6)
  addi t6, t6, 16
  ret
.size config_reuse_gemv_16x64_reuse_rvv, .-config_reuse_gemv_16x64_reuse_rvv

.option norvc
.option norelax
.text
.balign 16
.global config_reuse_gemv_4x13_basic_vdot
.type config_reuse_gemv_4x13_basic_vdot, @function
config_reuse_gemv_4x13_basic_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v24, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  .word 0x0388000b
  li t0, 0
  lb t4, 60(a2)
  lb t6, 8(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 61(a2)
  lb t6, 9(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 62(a2)
  lb t6, 10(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 63(a2)
  lb t6, 11(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 64(a2)
  lb t6, 12(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v0
  addw t0, t0, t6
  vmv.s.x v0, t0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v24, (t6)
  addi t6, a2, 13
  vle8.v v16, (t6)
  .word 0x0388008b
  li t0, 0
  lb t4, 60(a2)
  lb t6, 21(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 61(a2)
  lb t6, 22(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 62(a2)
  lb t6, 23(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 63(a2)
  lb t6, 24(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 64(a2)
  lb t6, 25(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v1
  addw t0, t0, t6
  vmv.s.x v1, t0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v24, (t6)
  addi t6, a2, 26
  vle8.v v16, (t6)
  .word 0x0388010b
  li t0, 0
  lb t4, 60(a2)
  lb t6, 34(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 61(a2)
  lb t6, 35(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 62(a2)
  lb t6, 36(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 63(a2)
  lb t6, 37(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 64(a2)
  lb t6, 38(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v2
  addw t0, t0, t6
  vmv.s.x v2, t0
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v24, (t6)
  addi t6, a2, 39
  vle8.v v16, (t6)
  .word 0x0388018b
  li t0, 0
  lb t4, 60(a2)
  lb t6, 47(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 61(a2)
  lb t6, 48(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 62(a2)
  lb t6, 49(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 63(a2)
  lb t6, 50(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t4, 64(a2)
  lb t6, 51(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v3
  addw t0, t0, t6
  vmv.s.x v3, t0
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 52
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
.size config_reuse_gemv_4x13_basic_vdot, .-config_reuse_gemv_4x13_basic_vdot
.balign 16
.global config_reuse_gemv_4x13_basic_rvv
.type config_reuse_gemv_4x13_basic_rvv, @function
config_reuse_gemv_4x13_basic_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vsetivli zero, 13, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v28, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 13, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v1, 0
  vsetivli zero, 13, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v28, (t6)
  addi t6, a2, 13
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 13, e16, m2, tu, mu
  vwredsum.vs v1, v20, v1
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v2, 0
  vsetivli zero, 13, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v28, (t6)
  addi t6, a2, 26
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 13, e16, m2, tu, mu
  vwredsum.vs v2, v20, v2
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v3, 0
  vsetivli zero, 13, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v28, (t6)
  addi t6, a2, 39
  vle8.v v16, (t6)
  vwmul.vv v20, v16, v28
  vsetivli zero, 13, e16, m2, tu, mu
  vwredsum.vs v3, v20, v3
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 52
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
.size config_reuse_gemv_4x13_basic_rvv, .-config_reuse_gemv_4x13_basic_rvv
.balign 16
.global config_reuse_gemv_4x13_reuse_vdot
.type config_reuse_gemv_4x13_reuse_vdot, @function
config_reuse_gemv_4x13_reuse_vdot:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v24, (t6)
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 13
  vle8.v v17, (t6)
  addi t6, a2, 26
  vle8.v v18, (t6)
  addi t6, a2, 39
  vle8.v v19, (t6)
  .word 0x0388000b
  .word 0x0388808b
  .word 0x0389010b
  .word 0x0389818b
  li t0, 0
  li t1, 0
  li t2, 0
  li t3, 0
  lb t4, 60(a2)
  lb t6, 8(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t6, 21(a2)
  mulw t6, t6, t4
  addw t1, t1, t6
  lb t6, 34(a2)
  mulw t6, t6, t4
  addw t2, t2, t6
  lb t6, 47(a2)
  mulw t6, t6, t4
  addw t3, t3, t6
  lb t4, 61(a2)
  lb t6, 9(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t6, 22(a2)
  mulw t6, t6, t4
  addw t1, t1, t6
  lb t6, 35(a2)
  mulw t6, t6, t4
  addw t2, t2, t6
  lb t6, 48(a2)
  mulw t6, t6, t4
  addw t3, t3, t6
  lb t4, 62(a2)
  lb t6, 10(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t6, 23(a2)
  mulw t6, t6, t4
  addw t1, t1, t6
  lb t6, 36(a2)
  mulw t6, t6, t4
  addw t2, t2, t6
  lb t6, 49(a2)
  mulw t6, t6, t4
  addw t3, t3, t6
  lb t4, 63(a2)
  lb t6, 11(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t6, 24(a2)
  mulw t6, t6, t4
  addw t1, t1, t6
  lb t6, 37(a2)
  mulw t6, t6, t4
  addw t2, t2, t6
  lb t6, 50(a2)
  mulw t6, t6, t4
  addw t3, t3, t6
  lb t4, 64(a2)
  lb t6, 12(a2)
  mulw t6, t6, t4
  addw t0, t0, t6
  lb t6, 25(a2)
  mulw t6, t6, t4
  addw t1, t1, t6
  lb t6, 38(a2)
  mulw t6, t6, t4
  addw t2, t2, t6
  lb t6, 51(a2)
  mulw t6, t6, t4
  addw t3, t3, t6
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.x.s t6, v0
  addw t0, t0, t6
  vmv.s.x v0, t0
  vmv.x.s t6, v1
  addw t1, t1, t6
  vmv.s.x v1, t1
  vmv.x.s t6, v2
  addw t2, t2, t6
  vmv.s.x v2, t2
  vmv.x.s t6, v3
  addw t3, t3, t6
  vmv.s.x v3, t3
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 52
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
.size config_reuse_gemv_4x13_reuse_vdot, .-config_reuse_gemv_4x13_reuse_vdot
.balign 16
.global config_reuse_gemv_4x13_reuse_rvv
.type config_reuse_gemv_4x13_reuse_rvv, @function
config_reuse_gemv_4x13_reuse_rvv:
  mv a2, a0
  mv a3, a1
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 8, e8, m1, tu, mu
  vsetivli zero, 13, e8, m1, tu, mu
  addi t6, a2, 52
  vle8.v v28, (t6)
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vmv.v.i v1, 0
  vmv.v.i v2, 0
  vmv.v.i v3, 0
  vsetivli zero, 13, e8, m1, tu, mu
  addi t6, a2, 0
  vle8.v v16, (t6)
  addi t6, a2, 13
  vle8.v v17, (t6)
  addi t6, a2, 26
  vle8.v v18, (t6)
  addi t6, a2, 39
  vle8.v v19, (t6)
  vwmul.vv v20, v16, v28
  vwmul.vv v22, v17, v28
  vwmul.vv v24, v18, v28
  vwmul.vv v26, v19, v28
  vsetivli zero, 13, e16, m2, tu, mu
  vwredsum.vs v0, v20, v0
  vwredsum.vs v1, v22, v1
  vwredsum.vs v2, v24, v2
  vwredsum.vs v3, v26, v3
  vsetivli zero, 8, e8, m1, tu, mu
  li t5, 52
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
.size config_reuse_gemv_4x13_reuse_rvv, .-config_reuse_gemv_4x13_reuse_rvv
