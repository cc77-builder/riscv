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
