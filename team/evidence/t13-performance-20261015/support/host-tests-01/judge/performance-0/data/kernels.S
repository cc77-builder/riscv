.option norvc
.text
.balign 64
.global t13_kernel_0
.type t13_kernel_0, @function
t13_kernel_0:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_0:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_0
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_0, .-t13_kernel_0
.balign 64
.global t13_kernel_1
.type t13_kernel_1, @function
t13_kernel_1:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_1:
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetivli zero, 8, e8, m1, tu, mu
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_1
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_1, .-t13_kernel_1
.balign 64
.global t13_kernel_2
.type t13_kernel_2, @function
t13_kernel_2:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 16
  .Lloop_2:
  .word 0x0295050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_2
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_2, .-t13_kernel_2
.balign 64
.global t13_kernel_3
.type t13_kernel_3, @function
t13_kernel_3:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 16
  .Lloop_3:
  vwmul.vv v2, v10, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetivli zero, 8, e8, m1, tu, mu
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_3
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_3, .-t13_kernel_3
.balign 64
.global t13_kernel_4
.type t13_kernel_4, @function
t13_kernel_4:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 64
  .Lloop_4:
  .word 0x0295050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_4
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_4, .-t13_kernel_4
.balign 64
.global t13_kernel_5
.type t13_kernel_5, @function
t13_kernel_5:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 64
  .Lloop_5:
  vwmul.vv v2, v10, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetivli zero, 8, e8, m1, tu, mu
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_5
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_5, .-t13_kernel_5
.balign 64
.global t13_kernel_6
.type t13_kernel_6, @function
t13_kernel_6:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 256
  .Lloop_6:
  .word 0x0295050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_6
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_6, .-t13_kernel_6
.balign 64
.global t13_kernel_7
.type t13_kernel_7, @function
t13_kernel_7:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 256
  .Lloop_7:
  vwmul.vv v2, v10, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetivli zero, 8, e8, m1, tu, mu
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_7
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_7, .-t13_kernel_7
.balign 64
.global t13_kernel_8
.type t13_kernel_8, @function
t13_kernel_8:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_8:
  .word 0x0294050b
  .word 0x0294058b
  .word 0x0294060b
  .word 0x0294068b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_8
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_8, .-t13_kernel_8
.balign 64
.global t13_kernel_9
.type t13_kernel_9, @function
t13_kernel_9:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_9:
  vwmul.vv v16, v8, v9
  vwmul.vv v18, v8, v9
  vwmul.vv v20, v8, v9
  vwmul.vv v22, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v16, v10
  vmv.v.i v11, 0
  vwredsum.vs v11, v18, v11
  vmv.v.i v12, 0
  vwredsum.vs v12, v20, v12
  vmv.v.i v13, 0
  vwredsum.vs v13, v22, v13
  vsetivli zero, 8, e8, m1, tu, mu
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_9
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_9, .-t13_kernel_9
.balign 64
.global t13_kernel_10
.type t13_kernel_10, @function
t13_kernel_10:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 8
  .Lloop_10:
  .word 0x0294050b
  .word 0x0294058b
  .word 0x0294060b
  .word 0x0294068b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_10
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_10, .-t13_kernel_10
.balign 64
.global t13_kernel_11
.type t13_kernel_11, @function
t13_kernel_11:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 8
  .Lloop_11:
  vwmul.vv v16, v8, v9
  vwmul.vv v18, v8, v9
  vwmul.vv v20, v8, v9
  vwmul.vv v22, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v16, v10
  vmv.v.i v11, 0
  vwredsum.vs v11, v18, v11
  vmv.v.i v12, 0
  vwredsum.vs v12, v20, v12
  vmv.v.i v13, 0
  vwredsum.vs v13, v22, v13
  vsetivli zero, 8, e8, m1, tu, mu
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_11
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_11, .-t13_kernel_11
.balign 64
.global t13_kernel_12
.type t13_kernel_12, @function
t13_kernel_12:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 32
  .Lloop_12:
  .word 0x0294050b
  .word 0x0294058b
  .word 0x0294060b
  .word 0x0294068b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_12
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_12, .-t13_kernel_12
.balign 64
.global t13_kernel_13
.type t13_kernel_13, @function
t13_kernel_13:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 32
  .Lloop_13:
  vwmul.vv v16, v8, v9
  vwmul.vv v18, v8, v9
  vwmul.vv v20, v8, v9
  vwmul.vv v22, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v16, v10
  vmv.v.i v11, 0
  vwredsum.vs v11, v18, v11
  vmv.v.i v12, 0
  vwredsum.vs v12, v20, v12
  vmv.v.i v13, 0
  vwredsum.vs v13, v22, v13
  vsetivli zero, 8, e8, m1, tu, mu
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_13
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_13, .-t13_kernel_13
.balign 64
.global t13_kernel_14
.type t13_kernel_14, @function
t13_kernel_14:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_14:
  vl1re8.v v8, (a2)
  addi a2, a2, 16
  vl1re8.v v9, (a2)
  addi a2, a2, 16
  .word 0x0294050b
  vs1r.v v10, (a3)
  addi a3, a3, 16
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_14
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_14, .-t13_kernel_14
.balign 64
.global t13_kernel_15
.type t13_kernel_15, @function
t13_kernel_15:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_15:
  vl1re8.v v8, (a2)
  addi a2, a2, 16
  vl1re8.v v9, (a2)
  addi a2, a2, 16
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetivli zero, 8, e8, m1, tu, mu
  vs1r.v v10, (a3)
  addi a3, a3, 16
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_15
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_15, .-t13_kernel_15
.balign 64
.global t13_kernel_16
.type t13_kernel_16, @function
t13_kernel_16:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 16
  .Lloop_16:
  vl1re8.v v8, (a2)
  addi a2, a2, 16
  vl1re8.v v9, (a2)
  addi a2, a2, 16
  .word 0x0294050b
  vs1r.v v10, (a3)
  addi a3, a3, 16
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_16
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_16, .-t13_kernel_16
.balign 64
.global t13_kernel_17
.type t13_kernel_17, @function
t13_kernel_17:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 16
  .Lloop_17:
  vl1re8.v v8, (a2)
  addi a2, a2, 16
  vl1re8.v v9, (a2)
  addi a2, a2, 16
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetivli zero, 8, e8, m1, tu, mu
  vs1r.v v10, (a3)
  addi a3, a3, 16
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_17
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_17, .-t13_kernel_17
.balign 64
.global t13_kernel_18
.type t13_kernel_18, @function
t13_kernel_18:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 64
  .Lloop_18:
  vl1re8.v v8, (a2)
  addi a2, a2, 16
  vl1re8.v v9, (a2)
  addi a2, a2, 16
  .word 0x0294050b
  vs1r.v v10, (a3)
  addi a3, a3, 16
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_18
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_18, .-t13_kernel_18
.balign 64
.global t13_kernel_19
.type t13_kernel_19, @function
t13_kernel_19:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 0
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 64
  .Lloop_19:
  vl1re8.v v8, (a2)
  addi a2, a2, 16
  vl1re8.v v9, (a2)
  addi a2, a2, 16
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetivli zero, 8, e8, m1, tu, mu
  vs1r.v v10, (a3)
  addi a3, a3, 16
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_19
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_19, .-t13_kernel_19
.balign 64
.global t13_kernel_20
.type t13_kernel_20, @function
t13_kernel_20:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 192
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_20:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_20
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_20, .-t13_kernel_20
.balign 64
.global t13_kernel_21
.type t13_kernel_21, @function
t13_kernel_21:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 192
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 1
  .Lloop_21:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_21
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_21, .-t13_kernel_21
.balign 64
.global t13_kernel_22
.type t13_kernel_22, @function
t13_kernel_22:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 192
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 16
  .Lloop_22:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_22
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_22, .-t13_kernel_22
.balign 64
.global t13_kernel_23
.type t13_kernel_23, @function
t13_kernel_23:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 192
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 16
  .Lloop_23:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_23
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_23, .-t13_kernel_23
.balign 64
.global t13_kernel_24
.type t13_kernel_24, @function
t13_kernel_24:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 192
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 64
  .Lloop_24:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_24
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_24, .-t13_kernel_24
.balign 64
.global t13_kernel_25
.type t13_kernel_25, @function
t13_kernel_25:
  li t0, 0x6600
  csrs mstatus, t0
  csrwi vstart, 0
  csrwi vcsr, 7
  vsetivli zero, 16, e8, m1, tu, mu
  mv t0, a0
  vl1re8.v v0, (t0)
  addi t0, t0, 16
  vl1re8.v v1, (t0)
  addi t0, t0, 16
  vl1re8.v v2, (t0)
  addi t0, t0, 16
  vl1re8.v v3, (t0)
  addi t0, t0, 16
  vl1re8.v v4, (t0)
  addi t0, t0, 16
  vl1re8.v v5, (t0)
  addi t0, t0, 16
  vl1re8.v v6, (t0)
  addi t0, t0, 16
  vl1re8.v v7, (t0)
  addi t0, t0, 16
  vl1re8.v v8, (t0)
  addi t0, t0, 16
  vl1re8.v v9, (t0)
  addi t0, t0, 16
  vl1re8.v v10, (t0)
  addi t0, t0, 16
  vl1re8.v v11, (t0)
  addi t0, t0, 16
  vl1re8.v v12, (t0)
  addi t0, t0, 16
  vl1re8.v v13, (t0)
  addi t0, t0, 16
  vl1re8.v v14, (t0)
  addi t0, t0, 16
  vl1re8.v v15, (t0)
  addi t0, t0, 16
  vl1re8.v v16, (t0)
  addi t0, t0, 16
  vl1re8.v v17, (t0)
  addi t0, t0, 16
  vl1re8.v v18, (t0)
  addi t0, t0, 16
  vl1re8.v v19, (t0)
  addi t0, t0, 16
  vl1re8.v v20, (t0)
  addi t0, t0, 16
  vl1re8.v v21, (t0)
  addi t0, t0, 16
  vl1re8.v v22, (t0)
  addi t0, t0, 16
  vl1re8.v v23, (t0)
  addi t0, t0, 16
  vl1re8.v v24, (t0)
  addi t0, t0, 16
  vl1re8.v v25, (t0)
  addi t0, t0, 16
  vl1re8.v v26, (t0)
  addi t0, t0, 16
  vl1re8.v v27, (t0)
  addi t0, t0, 16
  vl1re8.v v28, (t0)
  addi t0, t0, 16
  vl1re8.v v29, (t0)
  addi t0, t0, 16
  vl1re8.v v30, (t0)
  addi t0, t0, 16
  vl1re8.v v31, (t0)
  addi t0, t0, 16
  li t1, 8
  li t2, 192
  vsetvl zero, t1, t2
  li t5, 0
  fence rw, rw
  .word 0x51300013
  fence rw, rw
  csrr a4, instret
  fence rw, rw
  csrr a6, cycle
  fence rw, rw
  li t6, 64
  .Lloop_25:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_25
  fence rw, rw
  csrr a7, cycle
  fence rw, rw
  csrr a5, instret
  fence rw, rw
  .word 0x51400013
  fence rw, rw
  sd a6, 0(a1)
  sd a7, 8(a1)
  sd a4, 16(a1)
  sd a5, 24(a1)
  sd t5, 32(a1)
  csrr t0, vtype
  sd t0, 40(a1)
  csrr t0, vl
  sd t0, 48(a1)
  csrr t0, vstart
  sd t0, 56(a1)
  csrr t0, vxrm
  sd t0, 64(a1)
  csrr t0, vxsat
  sd t0, 72(a1)
  csrr t0, vcsr
  sd t0, 80(a1)
  csrr t0, mcountinhibit
  sd t0, 88(a1)
  addi t0, a1, 128
  vs1r.v v0, (t0)
  addi t0, t0, 16
  vs1r.v v1, (t0)
  addi t0, t0, 16
  vs1r.v v2, (t0)
  addi t0, t0, 16
  vs1r.v v3, (t0)
  addi t0, t0, 16
  vs1r.v v4, (t0)
  addi t0, t0, 16
  vs1r.v v5, (t0)
  addi t0, t0, 16
  vs1r.v v6, (t0)
  addi t0, t0, 16
  vs1r.v v7, (t0)
  addi t0, t0, 16
  vs1r.v v8, (t0)
  addi t0, t0, 16
  vs1r.v v9, (t0)
  addi t0, t0, 16
  vs1r.v v10, (t0)
  addi t0, t0, 16
  vs1r.v v11, (t0)
  addi t0, t0, 16
  vs1r.v v12, (t0)
  addi t0, t0, 16
  vs1r.v v13, (t0)
  addi t0, t0, 16
  vs1r.v v14, (t0)
  addi t0, t0, 16
  vs1r.v v15, (t0)
  addi t0, t0, 16
  vs1r.v v16, (t0)
  addi t0, t0, 16
  vs1r.v v17, (t0)
  addi t0, t0, 16
  vs1r.v v18, (t0)
  addi t0, t0, 16
  vs1r.v v19, (t0)
  addi t0, t0, 16
  vs1r.v v20, (t0)
  addi t0, t0, 16
  vs1r.v v21, (t0)
  addi t0, t0, 16
  vs1r.v v22, (t0)
  addi t0, t0, 16
  vs1r.v v23, (t0)
  addi t0, t0, 16
  vs1r.v v24, (t0)
  addi t0, t0, 16
  vs1r.v v25, (t0)
  addi t0, t0, 16
  vs1r.v v26, (t0)
  addi t0, t0, 16
  vs1r.v v27, (t0)
  addi t0, t0, 16
  vs1r.v v28, (t0)
  addi t0, t0, 16
  vs1r.v v29, (t0)
  addi t0, t0, 16
  vs1r.v v30, (t0)
  addi t0, t0, 16
  vs1r.v v31, (t0)
  addi t0, t0, 16
  ret
.size t13_kernel_25, .-t13_kernel_25
