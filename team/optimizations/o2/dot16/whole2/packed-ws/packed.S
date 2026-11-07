.option norvc
.option norelax
.text
.balign 64
.global q288_dot16_whole8_narrow_packed_ws
.type q288_dot16_whole8_narrow_packed_ws, @function
q288_dot16_whole8_narrow_packed_ws:
  ld a2, 0(a0)
  ld a7, 8(a0)
  ld a4, 16(a0)
  ld t0, 24(a0)
  ld a6, 32(a0)
  ld a3, 40(a0)
  csrwi vstart, 0
  csrwi vcsr, 7
  li t2, 36
  li t3, 36
  vsetivli zero, 8, e32, m2, tu, mu
.Ltile_dot16_whole8_narrow:
  vmv.v.i v8, 0
  mv a1, a7
  mv a5, t0
  li t1, 9
.Lgroup_dot16_whole8_narrow:
  vsetivli zero, 16, e8, m1, ta, mu
  vl2re8.v v14, (a1)
  vl8re8.v v16, (a2)
  .word 0x0ee8000b
  .word 0x0ee9008b
  .word 0x0eea010b
  .word 0x0eeb018b
  .word 0x0ef88c0b
  .word 0x0ef98c8b
  .word 0x0efa8d0b
  .word 0x0efb8d8b
  addi t6, a2, 128
  vl8re8.v v16, (t6)
  .word 0x0ee8020b
  .word 0x0ee9028b
  .word 0x0eea030b
  .word 0x0eeb038b
  .word 0x0ef88e0b
  .word 0x0ef98e8b
  .word 0x0efa8f0b
  .word 0x0efb8f8b
  vsetvli t6, zero, e32, m8, tu, mu
  vadd.vv v0, v0, v24
  vsetivli zero, 16, e32, m4, tu, mu
  vnsrl.wi v16, v0, 0
  vsetivli zero, 8, e32, m2, tu, mu
  vnsrl.wi v10, v16, 0
  vfcvt.f.x.v v10, v10
  vle32.v v12, (a4)
  vfmul.vv v10, v10, v12
  flw ft0, 0(a5)
  vfmul.vf v10, v10, ft0
  vfadd.vv v8, v8, v10
  addi a2, a2, 256
  addi a1, a1, 32
  addi a4, a4, 32
  addi a5, a5, 4
  addi t1, t1, -1
  bnez t1, .Lgroup_dot16_whole8_narrow
  vse32.v v8, (a6)
  addi a6, a6, 32
  addi a4, a4, 0
  addi t2, t2, -1
  bnez t2, .Ltile_dot16_whole8_narrow
  vsetivli zero, 8, e8, m1, tu, mu
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
.size q288_dot16_whole8_narrow_packed_ws, .-q288_dot16_whole8_narrow_packed_ws

.option norvc
.option norelax
.text
.balign 64
.global q288_paired16_rvv_packed_ws
.type q288_paired16_rvv_packed_ws, @function
q288_paired16_rvv_packed_ws:
  csrwi vstart, 0
  csrwi vcsr, 7
  ld t0, 8(a0)
  li t1, 9
  li t4, 32
  li t5, -127
  vsetvli zero, t4, e8, m2, tu, mu
  li t4, 0
q288_paired16_rvv_packed_ws_guard_loop:
  vle8.v v14, (t0)
  vmslt.vx v12, v14, t5
  vcpop.m t6, v12
  addw t4, t4, t6
  addi t0, t0, 32
  addi t1, t1, -1
  bnez t1, q288_paired16_rvv_packed_ws_guard_loop
q288_paired16_rvv_packed_ws_guard_dispatch:
  bnez t4, q288_paired16_rvv_packed_ws_fallback_begin
q288_paired16_rvv_packed_ws_fast_begin:
  ld a2, 0(a0)
  ld a7, 8(a0)
  ld a4, 16(a0)
  ld t0, 24(a0)
  ld a6, 32(a0)
  ld a3, 40(a0)
  csrwi vstart, 0
  csrwi vcsr, 7
  li t2, 36
  li t3, 36
  vsetivli zero, 8, e32, m2, tu, mu
  vmv.v.i v0, 0
  vmv.v.i v2, 0
  vmv.v.i v4, 0
  vmv.v.i v6, 0
.Ltile_paired16:
  vmv.v.i v8, 0
  mv a1, a7
  mv a5, t0
  li t1, 9
.Lgroup_paired16:
q288_paired16_rvv_packed_ws_core_begin:
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  vl2re8.v v14, (a1)
  addi t6, a2, 0
  vl2re8.v v12, (t6)
  vwmul.vv v16, v12, v14
  vwmacc.vv v16, v13, v15
  addi t6, a2, 32
  vl2re8.v v12, (t6)
  vwmul.vv v18, v12, v14
  vwmacc.vv v18, v13, v15
  addi t6, a2, 64
  vl2re8.v v12, (t6)
  vwmul.vv v20, v12, v14
  vwmacc.vv v20, v13, v15
  addi t6, a2, 96
  vl2re8.v v12, (t6)
  vwmul.vv v22, v12, v14
  vwmacc.vv v22, v13, v15
  addi t6, a2, 128
  vl2re8.v v12, (t6)
  vwmul.vv v24, v12, v14
  vwmacc.vv v24, v13, v15
  addi t6, a2, 160
  vl2re8.v v12, (t6)
  vwmul.vv v26, v12, v14
  vwmacc.vv v26, v13, v15
  addi t6, a2, 192
  vl2re8.v v12, (t6)
  vwmul.vv v28, v12, v14
  vwmacc.vv v28, v13, v15
  addi t6, a2, 224
  vl2re8.v v12, (t6)
  vwmul.vv v30, v12, v14
  vwmacc.vv v30, v13, v15
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v18, v0
  vwredsum.vs v2, v20, v0
  vwredsum.vs v3, v22, v0
  vwredsum.vs v4, v24, v0
  vwredsum.vs v5, v26, v0
  vwredsum.vs v6, v28, v0
  vwredsum.vs v7, v30, v0
  vwredsum.vs v0, v16, v0
q288_paired16_rvv_packed_ws_core_end:
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.v v10, v0
  vslideup.vi v10, v1, 1
  vslideup.vi v10, v2, 2
  vslideup.vi v10, v3, 3
  vmv.v.v v11, v4
  vslideup.vi v11, v5, 1
  vslideup.vi v11, v6, 2
  vslideup.vi v11, v7, 3
  vsetivli zero, 8, e32, m2, tu, mu
  vfcvt.f.x.v v10, v10
  vle32.v v12, (a4)
  vfmul.vv v10, v10, v12
  flw ft0, 0(a5)
  vfmul.vf v10, v10, ft0
  vfadd.vv v8, v8, v10
  addi a2, a2, 256
  addi a1, a1, 32
  addi a4, a4, 32
  addi a5, a5, 4
  addi t1, t1, -1
  bnez t1, .Lgroup_paired16
  vse32.v v8, (a6)
  addi a6, a6, 32
  addi a4, a4, 0
  addi t2, t2, -1
  bnez t2, .Ltile_paired16
  vsetivli zero, 8, e8, m1, tu, mu
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
q288_paired16_rvv_packed_ws_fast_end:
q288_paired16_rvv_packed_ws_fallback_begin:
  ld a2, 0(a0)
  ld a7, 8(a0)
  ld a4, 16(a0)
  ld t0, 24(a0)
  ld a6, 32(a0)
  ld a3, 40(a0)
  csrwi vstart, 0
  csrwi vcsr, 7
  li t2, 36
  li t3, 36
  vsetivli zero, 8, e32, m2, tu, mu
.Ltile_paired16_fallback:
  vmv.v.i v8, 0
  mv a1, a7
  mv a5, t0
  li t1, 9
.Lgroup_paired16_fallback:
q288_paired16_rvv_packed_ws_fallback_core_begin:
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
q288_paired16_rvv_packed_ws_fallback_core_end:
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.v v10, v0
  vslideup.vi v10, v1, 1
  vslideup.vi v10, v2, 2
  vslideup.vi v10, v3, 3
  vmv.v.v v11, v4
  vslideup.vi v11, v5, 1
  vslideup.vi v11, v6, 2
  vslideup.vi v11, v7, 3
  vsetivli zero, 8, e32, m2, tu, mu
  vfcvt.f.x.v v10, v10
  vle32.v v12, (a4)
  vfmul.vv v10, v10, v12
  flw ft0, 0(a5)
  vfmul.vf v10, v10, ft0
  vfadd.vv v8, v8, v10
  addi a2, a2, 256
  addi a1, a1, 32
  addi a4, a4, 32
  addi a5, a5, 4
  addi t1, t1, -1
  bnez t1, .Lgroup_paired16_fallback
  vse32.v v8, (a6)
  addi a6, a6, 32
  addi a4, a4, 0
  addi t2, t2, -1
  bnez t2, .Ltile_paired16_fallback
  vsetivli zero, 8, e8, m1, tu, mu
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
q288_paired16_rvv_packed_ws_fallback_end:
.size q288_paired16_rvv_packed_ws, .-q288_paired16_rvv_packed_ws

.option norvc
.option norelax
.text
.balign 64
.global q768_dot16_whole8_narrow_packed_ws
.type q768_dot16_whole8_narrow_packed_ws, @function
q768_dot16_whole8_narrow_packed_ws:
  ld a2, 0(a0)
  ld a7, 8(a0)
  ld a4, 16(a0)
  ld t0, 24(a0)
  ld a6, 32(a0)
  ld a3, 40(a0)
  csrwi vstart, 0
  csrwi vcsr, 7
  li t2, 36
  li t3, 96
  vsetivli zero, 8, e32, m2, tu, mu
.Ltile_dot16_whole8_narrow_k768:
  vmv.v.i v8, 0
  mv a1, a7
  mv a5, t0
  li t1, 24
.Lgroup_dot16_whole8_narrow_k768:
  vsetivli zero, 16, e8, m1, ta, mu
  vl2re8.v v14, (a1)
  vl8re8.v v16, (a2)
  .word 0x0ee8000b
  .word 0x0ee9008b
  .word 0x0eea010b
  .word 0x0eeb018b
  .word 0x0ef88c0b
  .word 0x0ef98c8b
  .word 0x0efa8d0b
  .word 0x0efb8d8b
  addi t6, a2, 128
  vl8re8.v v16, (t6)
  .word 0x0ee8020b
  .word 0x0ee9028b
  .word 0x0eea030b
  .word 0x0eeb038b
  .word 0x0ef88e0b
  .word 0x0ef98e8b
  .word 0x0efa8f0b
  .word 0x0efb8f8b
  vsetvli t6, zero, e32, m8, tu, mu
  vadd.vv v0, v0, v24
  vsetivli zero, 16, e32, m4, tu, mu
  vnsrl.wi v16, v0, 0
  vsetivli zero, 8, e32, m2, tu, mu
  vnsrl.wi v10, v16, 0
  vfcvt.f.x.v v10, v10
  vle32.v v12, (a4)
  vfmul.vv v10, v10, v12
  flw ft0, 0(a5)
  vfmul.vf v10, v10, ft0
  vfadd.vv v8, v8, v10
  addi a2, a2, 256
  addi a1, a1, 32
  addi a4, a4, 32
  addi a5, a5, 4
  addi t1, t1, -1
  bnez t1, .Lgroup_dot16_whole8_narrow_k768
  vse32.v v8, (a6)
  addi a6, a6, 32
  addi a4, a4, 0
  addi t2, t2, -1
  bnez t2, .Ltile_dot16_whole8_narrow_k768
  vsetivli zero, 8, e8, m1, tu, mu
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
.size q768_dot16_whole8_narrow_packed_ws, .-q768_dot16_whole8_narrow_packed_ws
.option norvc
.option norelax
.text
.balign 64
.global q768_paired16_rvv_packed_ws
.type q768_paired16_rvv_packed_ws, @function
q768_paired16_rvv_packed_ws:
  csrwi vstart, 0
  csrwi vcsr, 7
  ld t0, 8(a0)
  li t1, 24
  li t4, 32
  li t5, -127
  vsetvli zero, t4, e8, m2, tu, mu
  li t4, 0
q768_paired16_rvv_packed_ws_guard_loop:
  vle8.v v14, (t0)
  vmslt.vx v12, v14, t5
  vcpop.m t6, v12
  addw t4, t4, t6
  addi t0, t0, 32
  addi t1, t1, -1
  bnez t1, q768_paired16_rvv_packed_ws_guard_loop
q768_paired16_rvv_packed_ws_guard_dispatch:
  bnez t4, q768_paired16_rvv_packed_ws_fallback_begin
q768_paired16_rvv_packed_ws_fast_begin:
  ld a2, 0(a0)
  ld a7, 8(a0)
  ld a4, 16(a0)
  ld t0, 24(a0)
  ld a6, 32(a0)
  ld a3, 40(a0)
  csrwi vstart, 0
  csrwi vcsr, 7
  li t2, 36
  li t3, 96
  vsetivli zero, 8, e32, m2, tu, mu
  vmv.v.i v0, 0
  vmv.v.i v2, 0
  vmv.v.i v4, 0
  vmv.v.i v6, 0
.Ltile_paired16_k768:
  vmv.v.i v8, 0
  mv a1, a7
  mv a5, t0
  li t1, 24
.Lgroup_paired16_k768:
q768_paired16_rvv_packed_ws_core_begin:
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.i v0, 0
  vsetivli zero, 16, e8, m1, tu, mu
  vl2re8.v v14, (a1)
  addi t6, a2, 0
  vl2re8.v v12, (t6)
  vwmul.vv v16, v12, v14
  vwmacc.vv v16, v13, v15
  addi t6, a2, 32
  vl2re8.v v12, (t6)
  vwmul.vv v18, v12, v14
  vwmacc.vv v18, v13, v15
  addi t6, a2, 64
  vl2re8.v v12, (t6)
  vwmul.vv v20, v12, v14
  vwmacc.vv v20, v13, v15
  addi t6, a2, 96
  vl2re8.v v12, (t6)
  vwmul.vv v22, v12, v14
  vwmacc.vv v22, v13, v15
  addi t6, a2, 128
  vl2re8.v v12, (t6)
  vwmul.vv v24, v12, v14
  vwmacc.vv v24, v13, v15
  addi t6, a2, 160
  vl2re8.v v12, (t6)
  vwmul.vv v26, v12, v14
  vwmacc.vv v26, v13, v15
  addi t6, a2, 192
  vl2re8.v v12, (t6)
  vwmul.vv v28, v12, v14
  vwmacc.vv v28, v13, v15
  addi t6, a2, 224
  vl2re8.v v12, (t6)
  vwmul.vv v30, v12, v14
  vwmacc.vv v30, v13, v15
  vsetivli zero, 16, e16, m2, tu, mu
  vwredsum.vs v1, v18, v0
  vwredsum.vs v2, v20, v0
  vwredsum.vs v3, v22, v0
  vwredsum.vs v4, v24, v0
  vwredsum.vs v5, v26, v0
  vwredsum.vs v6, v28, v0
  vwredsum.vs v7, v30, v0
  vwredsum.vs v0, v16, v0
q768_paired16_rvv_packed_ws_core_end:
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.v v10, v0
  vslideup.vi v10, v1, 1
  vslideup.vi v10, v2, 2
  vslideup.vi v10, v3, 3
  vmv.v.v v11, v4
  vslideup.vi v11, v5, 1
  vslideup.vi v11, v6, 2
  vslideup.vi v11, v7, 3
  vsetivli zero, 8, e32, m2, tu, mu
  vfcvt.f.x.v v10, v10
  vle32.v v12, (a4)
  vfmul.vv v10, v10, v12
  flw ft0, 0(a5)
  vfmul.vf v10, v10, ft0
  vfadd.vv v8, v8, v10
  addi a2, a2, 256
  addi a1, a1, 32
  addi a4, a4, 32
  addi a5, a5, 4
  addi t1, t1, -1
  bnez t1, .Lgroup_paired16_k768
  vse32.v v8, (a6)
  addi a6, a6, 32
  addi a4, a4, 0
  addi t2, t2, -1
  bnez t2, .Ltile_paired16_k768
  vsetivli zero, 8, e8, m1, tu, mu
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
q768_paired16_rvv_packed_ws_fast_end:
q768_paired16_rvv_packed_ws_fallback_begin:
  ld a2, 0(a0)
  ld a7, 8(a0)
  ld a4, 16(a0)
  ld t0, 24(a0)
  ld a6, 32(a0)
  ld a3, 40(a0)
  csrwi vstart, 0
  csrwi vcsr, 7
  li t2, 36
  li t3, 96
  vsetivli zero, 8, e32, m2, tu, mu
.Ltile_paired16_fallback_k768:
  vmv.v.i v8, 0
  mv a1, a7
  mv a5, t0
  li t1, 24
.Lgroup_paired16_fallback_k768:
q768_paired16_rvv_packed_ws_fallback_core_begin:
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
q768_paired16_rvv_packed_ws_fallback_core_end:
  vsetivli zero, 4, e32, m1, tu, mu
  vmv.v.v v10, v0
  vslideup.vi v10, v1, 1
  vslideup.vi v10, v2, 2
  vslideup.vi v10, v3, 3
  vmv.v.v v11, v4
  vslideup.vi v11, v5, 1
  vslideup.vi v11, v6, 2
  vslideup.vi v11, v7, 3
  vsetivli zero, 8, e32, m2, tu, mu
  vfcvt.f.x.v v10, v10
  vle32.v v12, (a4)
  vfmul.vv v10, v10, v12
  flw ft0, 0(a5)
  vfmul.vf v10, v10, ft0
  vfadd.vv v8, v8, v10
  addi a2, a2, 256
  addi a1, a1, 32
  addi a4, a4, 32
  addi a5, a5, 4
  addi t1, t1, -1
  bnez t1, .Lgroup_paired16_fallback_k768
  vse32.v v8, (a6)
  addi a6, a6, 32
  addi a4, a4, 0
  addi t2, t2, -1
  bnez t2, .Ltile_paired16_fallback_k768
  vsetivli zero, 8, e8, m1, tu, mu
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
q768_paired16_rvv_packed_ws_fallback_end:
.size q768_paired16_rvv_packed_ws, .-q768_paired16_rvv_packed_ws
