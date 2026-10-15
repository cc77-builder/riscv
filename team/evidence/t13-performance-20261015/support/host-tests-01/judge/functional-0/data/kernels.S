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
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
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
  li t2, 64
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
  .Lloop_2:
  .word 0x0294040b
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
  li t2, 64
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
  .Lloop_3:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
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
  li t2, 128
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
  .Lloop_4:
  .word 0x0294048b
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
  li t2, 128
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
  .Lloop_5:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
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
  .Lloop_6:
  .word 0x0284050b
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
  .Lloop_7:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
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
  .word 0x0284040b
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
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
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
  li t2, 64
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
  .Lloop_10:
  .word 0x0294000b
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
  li t2, 64
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
  .Lloop_11:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v0, 0
  vwredsum.vs v0, v2, v0
  vsetvl zero, t3, t4
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
  li t2, 128
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
  .Lloop_12:
  .word 0x02940f8b
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
  li t2, 128
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
  .Lloop_13:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v31, 0
  vwredsum.vs v31, v2, v31
  vsetvl zero, t3, t4
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
  .Lloop_14:
  .word 0x0294050b
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
  .Lloop_15:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
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
  li t6, 1
  .Lloop_16:
  .word 0x0294040b
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
  li t6, 1
  .Lloop_17:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
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
  li t2, 64
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
  .Lloop_18:
  .word 0x0294048b
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
  li t2, 64
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
  .Lloop_19:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
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
  li t2, 128
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
  .word 0x0284050b
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
  li t2, 128
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
  vwmul.vv v2, v8, v8
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
  li t6, 1
  .Lloop_22:
  .word 0x0284040b
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
  li t6, 1
  .Lloop_23:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
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
  .Lloop_24:
  .word 0x0294000b
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
  .Lloop_25:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v0, 0
  vwredsum.vs v0, v2, v0
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
.balign 64
.global t13_kernel_26
.type t13_kernel_26, @function
t13_kernel_26:
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
  li t2, 64
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
  .Lloop_26:
  .word 0x02940f8b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_26
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
.size t13_kernel_26, .-t13_kernel_26
.balign 64
.global t13_kernel_27
.type t13_kernel_27, @function
t13_kernel_27:
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
  li t2, 64
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
  .Lloop_27:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v31, 0
  vwredsum.vs v31, v2, v31
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_27
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
.size t13_kernel_27, .-t13_kernel_27
.balign 64
.global t13_kernel_28
.type t13_kernel_28, @function
t13_kernel_28:
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
  li t2, 128
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
  .Lloop_28:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_28
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
.size t13_kernel_28, .-t13_kernel_28
.balign 64
.global t13_kernel_29
.type t13_kernel_29, @function
t13_kernel_29:
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
  li t2, 128
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
  .Lloop_29:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_29
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
.size t13_kernel_29, .-t13_kernel_29
.balign 64
.global t13_kernel_30
.type t13_kernel_30, @function
t13_kernel_30:
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
  .Lloop_30:
  .word 0x0294040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_30
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
.size t13_kernel_30, .-t13_kernel_30
.balign 64
.global t13_kernel_31
.type t13_kernel_31, @function
t13_kernel_31:
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
  .Lloop_31:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_31
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
.size t13_kernel_31, .-t13_kernel_31
.balign 64
.global t13_kernel_32
.type t13_kernel_32, @function
t13_kernel_32:
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
  .Lloop_32:
  .word 0x0294048b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_32
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
.size t13_kernel_32, .-t13_kernel_32
.balign 64
.global t13_kernel_33
.type t13_kernel_33, @function
t13_kernel_33:
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
  .Lloop_33:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_33
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
.size t13_kernel_33, .-t13_kernel_33
.balign 64
.global t13_kernel_34
.type t13_kernel_34, @function
t13_kernel_34:
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
  li t2, 64
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
  .Lloop_34:
  .word 0x0284050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_34
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
.size t13_kernel_34, .-t13_kernel_34
.balign 64
.global t13_kernel_35
.type t13_kernel_35, @function
t13_kernel_35:
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
  li t2, 64
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
  .Lloop_35:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_35
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
.size t13_kernel_35, .-t13_kernel_35
.balign 64
.global t13_kernel_36
.type t13_kernel_36, @function
t13_kernel_36:
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
  li t2, 128
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
  .Lloop_36:
  .word 0x0284040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_36
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
.size t13_kernel_36, .-t13_kernel_36
.balign 64
.global t13_kernel_37
.type t13_kernel_37, @function
t13_kernel_37:
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
  li t2, 128
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
  .Lloop_37:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_37
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
.size t13_kernel_37, .-t13_kernel_37
.balign 64
.global t13_kernel_38
.type t13_kernel_38, @function
t13_kernel_38:
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
  .Lloop_38:
  .word 0x0294000b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_38
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
.size t13_kernel_38, .-t13_kernel_38
.balign 64
.global t13_kernel_39
.type t13_kernel_39, @function
t13_kernel_39:
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
  .Lloop_39:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v0, 0
  vwredsum.vs v0, v2, v0
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_39
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
.size t13_kernel_39, .-t13_kernel_39
.balign 64
.global t13_kernel_40
.type t13_kernel_40, @function
t13_kernel_40:
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
  .Lloop_40:
  .word 0x02940f8b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_40
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
.size t13_kernel_40, .-t13_kernel_40
.balign 64
.global t13_kernel_41
.type t13_kernel_41, @function
t13_kernel_41:
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
  .Lloop_41:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v31, 0
  vwredsum.vs v31, v2, v31
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_41
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
.size t13_kernel_41, .-t13_kernel_41
.balign 64
.global t13_kernel_42
.type t13_kernel_42, @function
t13_kernel_42:
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
  li t2, 64
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
  .Lloop_42:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_42
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
.size t13_kernel_42, .-t13_kernel_42
.balign 64
.global t13_kernel_43
.type t13_kernel_43, @function
t13_kernel_43:
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
  li t2, 64
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
  .Lloop_43:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_43
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
.size t13_kernel_43, .-t13_kernel_43
.balign 64
.global t13_kernel_44
.type t13_kernel_44, @function
t13_kernel_44:
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
  li t2, 128
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
  .Lloop_44:
  .word 0x0294040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_44
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
.size t13_kernel_44, .-t13_kernel_44
.balign 64
.global t13_kernel_45
.type t13_kernel_45, @function
t13_kernel_45:
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
  li t2, 128
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
  .Lloop_45:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_45
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
.size t13_kernel_45, .-t13_kernel_45
.balign 64
.global t13_kernel_46
.type t13_kernel_46, @function
t13_kernel_46:
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
  .Lloop_46:
  .word 0x0294048b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_46
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
.size t13_kernel_46, .-t13_kernel_46
.balign 64
.global t13_kernel_47
.type t13_kernel_47, @function
t13_kernel_47:
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
  .Lloop_47:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_47
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
.size t13_kernel_47, .-t13_kernel_47
.balign 64
.global t13_kernel_48
.type t13_kernel_48, @function
t13_kernel_48:
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
  .Lloop_48:
  .word 0x0284050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_48
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
.size t13_kernel_48, .-t13_kernel_48
.balign 64
.global t13_kernel_49
.type t13_kernel_49, @function
t13_kernel_49:
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
  .Lloop_49:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_49
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
.size t13_kernel_49, .-t13_kernel_49
.balign 64
.global t13_kernel_50
.type t13_kernel_50, @function
t13_kernel_50:
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
  li t2, 64
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
  .Lloop_50:
  .word 0x0284040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_50
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
.size t13_kernel_50, .-t13_kernel_50
.balign 64
.global t13_kernel_51
.type t13_kernel_51, @function
t13_kernel_51:
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
  li t2, 64
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
  .Lloop_51:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_51
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
.size t13_kernel_51, .-t13_kernel_51
.balign 64
.global t13_kernel_52
.type t13_kernel_52, @function
t13_kernel_52:
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
  li t2, 128
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
  .Lloop_52:
  .word 0x0294000b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_52
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
.size t13_kernel_52, .-t13_kernel_52
.balign 64
.global t13_kernel_53
.type t13_kernel_53, @function
t13_kernel_53:
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
  li t2, 128
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
  .Lloop_53:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v0, 0
  vwredsum.vs v0, v2, v0
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_53
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
.size t13_kernel_53, .-t13_kernel_53
.balign 64
.global t13_kernel_54
.type t13_kernel_54, @function
t13_kernel_54:
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
  .Lloop_54:
  .word 0x02940f8b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_54
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
.size t13_kernel_54, .-t13_kernel_54
.balign 64
.global t13_kernel_55
.type t13_kernel_55, @function
t13_kernel_55:
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
  .Lloop_55:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v31, 0
  vwredsum.vs v31, v2, v31
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_55
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
.size t13_kernel_55, .-t13_kernel_55
.balign 64
.global t13_kernel_56
.type t13_kernel_56, @function
t13_kernel_56:
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
  .Lloop_56:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_56
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
.size t13_kernel_56, .-t13_kernel_56
.balign 64
.global t13_kernel_57
.type t13_kernel_57, @function
t13_kernel_57:
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
  .Lloop_57:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_57
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
.size t13_kernel_57, .-t13_kernel_57
.balign 64
.global t13_kernel_58
.type t13_kernel_58, @function
t13_kernel_58:
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
  li t2, 64
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
  .Lloop_58:
  .word 0x0294040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_58
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
.size t13_kernel_58, .-t13_kernel_58
.balign 64
.global t13_kernel_59
.type t13_kernel_59, @function
t13_kernel_59:
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
  li t2, 64
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
  .Lloop_59:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_59
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
.size t13_kernel_59, .-t13_kernel_59
.balign 64
.global t13_kernel_60
.type t13_kernel_60, @function
t13_kernel_60:
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
  li t2, 128
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
  .Lloop_60:
  .word 0x0294048b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_60
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
.size t13_kernel_60, .-t13_kernel_60
.balign 64
.global t13_kernel_61
.type t13_kernel_61, @function
t13_kernel_61:
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
  li t2, 128
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
  .Lloop_61:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_61
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
.size t13_kernel_61, .-t13_kernel_61
.balign 64
.global t13_kernel_62
.type t13_kernel_62, @function
t13_kernel_62:
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
  .Lloop_62:
  .word 0x0284050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_62
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
.size t13_kernel_62, .-t13_kernel_62
.balign 64
.global t13_kernel_63
.type t13_kernel_63, @function
t13_kernel_63:
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
  .Lloop_63:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_63
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
.size t13_kernel_63, .-t13_kernel_63
.balign 64
.global t13_kernel_64
.type t13_kernel_64, @function
t13_kernel_64:
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
  .Lloop_64:
  .word 0x0284040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_64
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
.size t13_kernel_64, .-t13_kernel_64
.balign 64
.global t13_kernel_65
.type t13_kernel_65, @function
t13_kernel_65:
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
  .Lloop_65:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_65
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
.size t13_kernel_65, .-t13_kernel_65
.balign 64
.global t13_kernel_66
.type t13_kernel_66, @function
t13_kernel_66:
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
  li t2, 64
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
  .Lloop_66:
  .word 0x0294000b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_66
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
.size t13_kernel_66, .-t13_kernel_66
.balign 64
.global t13_kernel_67
.type t13_kernel_67, @function
t13_kernel_67:
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
  li t2, 64
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
  .Lloop_67:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v0, 0
  vwredsum.vs v0, v2, v0
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_67
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
.size t13_kernel_67, .-t13_kernel_67
.balign 64
.global t13_kernel_68
.type t13_kernel_68, @function
t13_kernel_68:
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
  li t2, 128
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
  .Lloop_68:
  .word 0x02940f8b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_68
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
.size t13_kernel_68, .-t13_kernel_68
.balign 64
.global t13_kernel_69
.type t13_kernel_69, @function
t13_kernel_69:
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
  li t2, 128
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
  .Lloop_69:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v31, 0
  vwredsum.vs v31, v2, v31
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_69
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
.size t13_kernel_69, .-t13_kernel_69
.balign 64
.global t13_kernel_70
.type t13_kernel_70, @function
t13_kernel_70:
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
  .Lloop_70:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_70
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
.size t13_kernel_70, .-t13_kernel_70
.balign 64
.global t13_kernel_71
.type t13_kernel_71, @function
t13_kernel_71:
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
  .Lloop_71:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_71
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
.size t13_kernel_71, .-t13_kernel_71
.balign 64
.global t13_kernel_72
.type t13_kernel_72, @function
t13_kernel_72:
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
  .Lloop_72:
  .word 0x0294040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_72
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
.size t13_kernel_72, .-t13_kernel_72
.balign 64
.global t13_kernel_73
.type t13_kernel_73, @function
t13_kernel_73:
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
  .Lloop_73:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_73
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
.size t13_kernel_73, .-t13_kernel_73
.balign 64
.global t13_kernel_74
.type t13_kernel_74, @function
t13_kernel_74:
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
  li t2, 64
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
  .Lloop_74:
  .word 0x0294048b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_74
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
.size t13_kernel_74, .-t13_kernel_74
.balign 64
.global t13_kernel_75
.type t13_kernel_75, @function
t13_kernel_75:
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
  li t2, 64
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
  .Lloop_75:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_75
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
.size t13_kernel_75, .-t13_kernel_75
.balign 64
.global t13_kernel_76
.type t13_kernel_76, @function
t13_kernel_76:
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
  li t2, 128
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
  .Lloop_76:
  .word 0x0284050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_76
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
.size t13_kernel_76, .-t13_kernel_76
.balign 64
.global t13_kernel_77
.type t13_kernel_77, @function
t13_kernel_77:
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
  li t2, 128
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
  .Lloop_77:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_77
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
.size t13_kernel_77, .-t13_kernel_77
.balign 64
.global t13_kernel_78
.type t13_kernel_78, @function
t13_kernel_78:
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
  .Lloop_78:
  .word 0x0284040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_78
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
.size t13_kernel_78, .-t13_kernel_78
.balign 64
.global t13_kernel_79
.type t13_kernel_79, @function
t13_kernel_79:
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
  .Lloop_79:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_79
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
.size t13_kernel_79, .-t13_kernel_79
.balign 64
.global t13_kernel_80
.type t13_kernel_80, @function
t13_kernel_80:
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
  .Lloop_80:
  .word 0x0294000b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_80
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
.size t13_kernel_80, .-t13_kernel_80
.balign 64
.global t13_kernel_81
.type t13_kernel_81, @function
t13_kernel_81:
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
  .Lloop_81:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v0, 0
  vwredsum.vs v0, v2, v0
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_81
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
.size t13_kernel_81, .-t13_kernel_81
.balign 64
.global t13_kernel_82
.type t13_kernel_82, @function
t13_kernel_82:
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
  li t2, 64
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
  .Lloop_82:
  .word 0x02940f8b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_82
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
.size t13_kernel_82, .-t13_kernel_82
.balign 64
.global t13_kernel_83
.type t13_kernel_83, @function
t13_kernel_83:
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
  li t2, 64
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
  .Lloop_83:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v31, 0
  vwredsum.vs v31, v2, v31
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_83
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
.size t13_kernel_83, .-t13_kernel_83
.balign 64
.global t13_kernel_84
.type t13_kernel_84, @function
t13_kernel_84:
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
  li t2, 128
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
  .Lloop_84:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_84
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
.size t13_kernel_84, .-t13_kernel_84
.balign 64
.global t13_kernel_85
.type t13_kernel_85, @function
t13_kernel_85:
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
  li t2, 128
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
  .Lloop_85:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_85
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
.size t13_kernel_85, .-t13_kernel_85
.balign 64
.global t13_kernel_86
.type t13_kernel_86, @function
t13_kernel_86:
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
  .Lloop_86:
  .word 0x0294040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_86
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
.size t13_kernel_86, .-t13_kernel_86
.balign 64
.global t13_kernel_87
.type t13_kernel_87, @function
t13_kernel_87:
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
  .Lloop_87:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_87
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
.size t13_kernel_87, .-t13_kernel_87
.balign 64
.global t13_kernel_88
.type t13_kernel_88, @function
t13_kernel_88:
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
  .Lloop_88:
  .word 0x0294048b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_88
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
.size t13_kernel_88, .-t13_kernel_88
.balign 64
.global t13_kernel_89
.type t13_kernel_89, @function
t13_kernel_89:
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
  .Lloop_89:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_89
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
.size t13_kernel_89, .-t13_kernel_89
.balign 64
.global t13_kernel_90
.type t13_kernel_90, @function
t13_kernel_90:
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
  li t2, 64
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
  .Lloop_90:
  .word 0x0284050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_90
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
.size t13_kernel_90, .-t13_kernel_90
.balign 64
.global t13_kernel_91
.type t13_kernel_91, @function
t13_kernel_91:
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
  li t2, 64
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
  .Lloop_91:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_91
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
.size t13_kernel_91, .-t13_kernel_91
.balign 64
.global t13_kernel_92
.type t13_kernel_92, @function
t13_kernel_92:
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
  li t2, 128
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
  .Lloop_92:
  .word 0x0284040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_92
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
.size t13_kernel_92, .-t13_kernel_92
.balign 64
.global t13_kernel_93
.type t13_kernel_93, @function
t13_kernel_93:
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
  li t2, 128
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
  .Lloop_93:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_93
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
.size t13_kernel_93, .-t13_kernel_93
.balign 64
.global t13_kernel_94
.type t13_kernel_94, @function
t13_kernel_94:
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
  .Lloop_94:
  .word 0x0294000b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_94
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
.size t13_kernel_94, .-t13_kernel_94
.balign 64
.global t13_kernel_95
.type t13_kernel_95, @function
t13_kernel_95:
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
  .Lloop_95:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v0, 0
  vwredsum.vs v0, v2, v0
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_95
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
.size t13_kernel_95, .-t13_kernel_95
.balign 64
.global t13_kernel_96
.type t13_kernel_96, @function
t13_kernel_96:
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
  .Lloop_96:
  .word 0x02940f8b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_96
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
.size t13_kernel_96, .-t13_kernel_96
.balign 64
.global t13_kernel_97
.type t13_kernel_97, @function
t13_kernel_97:
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
  .Lloop_97:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v31, 0
  vwredsum.vs v31, v2, v31
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_97
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
.size t13_kernel_97, .-t13_kernel_97
.balign 64
.global t13_kernel_98
.type t13_kernel_98, @function
t13_kernel_98:
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
  li t2, 64
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
  .Lloop_98:
  .word 0x0294050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_98
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
.size t13_kernel_98, .-t13_kernel_98
.balign 64
.global t13_kernel_99
.type t13_kernel_99, @function
t13_kernel_99:
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
  li t2, 64
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
  .Lloop_99:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_99
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
.size t13_kernel_99, .-t13_kernel_99
.balign 64
.global t13_kernel_100
.type t13_kernel_100, @function
t13_kernel_100:
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
  li t2, 128
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
  .Lloop_100:
  .word 0x0294040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_100
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
.size t13_kernel_100, .-t13_kernel_100
.balign 64
.global t13_kernel_101
.type t13_kernel_101, @function
t13_kernel_101:
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
  li t2, 128
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
  .Lloop_101:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_101
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
.size t13_kernel_101, .-t13_kernel_101
.balign 64
.global t13_kernel_102
.type t13_kernel_102, @function
t13_kernel_102:
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
  .Lloop_102:
  .word 0x0294048b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_102
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
.size t13_kernel_102, .-t13_kernel_102
.balign 64
.global t13_kernel_103
.type t13_kernel_103, @function
t13_kernel_103:
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
  .Lloop_103:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v9
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v9, 0
  vwredsum.vs v9, v2, v9
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_103
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
.size t13_kernel_103, .-t13_kernel_103
.balign 64
.global t13_kernel_104
.type t13_kernel_104, @function
t13_kernel_104:
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
  .Lloop_104:
  .word 0x0284050b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_104
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
.size t13_kernel_104, .-t13_kernel_104
.balign 64
.global t13_kernel_105
.type t13_kernel_105, @function
t13_kernel_105:
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
  .Lloop_105:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v10, 0
  vwredsum.vs v10, v2, v10
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_105
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
.size t13_kernel_105, .-t13_kernel_105
.balign 64
.global t13_kernel_106
.type t13_kernel_106, @function
t13_kernel_106:
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
  li t2, 64
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
  .Lloop_106:
  .word 0x0284040b
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_106
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
.size t13_kernel_106, .-t13_kernel_106
.balign 64
.global t13_kernel_107
.type t13_kernel_107, @function
t13_kernel_107:
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
  li t2, 64
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
  .Lloop_107:
  csrr t3, vl
  csrr t4, vtype
  vwmul.vv v2, v8, v8
  vsetivli zero, 8, e16, m1, tu, mu
  vmv.v.i v8, 0
  vwredsum.vs v8, v2, v8
  vsetvl zero, t3, t4
  addi t5, t5, 1
  addi t6, t6, -1
  bnez t6, .Lloop_107
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
.size t13_kernel_107, .-t13_kernel_107
