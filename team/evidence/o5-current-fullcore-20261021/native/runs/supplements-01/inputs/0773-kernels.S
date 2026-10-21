.option norvc
.text
.balign 64
.global o2_diag_0
.type o2_diag_0, @function
o2_diag_0:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_0_begin
o2_diag_0_begin:
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.global o2_diag_0_end
o2_diag_0_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_0, .-o2_diag_0
.balign 64
.global o2_diag_1
.type o2_diag_1, @function
o2_diag_1:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_1_begin
o2_diag_1_begin:
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.word 0x0294080b
.word 0x0294088b
.global o2_diag_1_end
o2_diag_1_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_1, .-o2_diag_1
.balign 64
.global o2_diag_2
.type o2_diag_2, @function
o2_diag_2:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_2_begin
o2_diag_2_begin:
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.word 0x0294080b
.word 0x0294088b
.word 0x0294090b
.word 0x0294098b
.global o2_diag_2_end
o2_diag_2_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_2, .-o2_diag_2
.balign 64
.global o2_diag_3
.type o2_diag_3, @function
o2_diag_3:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_3_begin
o2_diag_3_begin:
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.word 0x0294080b
.global o2_diag_3_end
o2_diag_3_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_3, .-o2_diag_3
.balign 64
.global o2_diag_4
.type o2_diag_4, @function
o2_diag_4:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_4_begin
o2_diag_4_begin:
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.word 0x0294080b
.word 0x02b5088b
.global o2_diag_4_end
o2_diag_4_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_4, .-o2_diag_4
.balign 64
.global o2_diag_5
.type o2_diag_5, @function
o2_diag_5:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_5_begin
o2_diag_5_begin:
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.word 0x0294080b
.word 0x02b5088b
.word 0x02d6090b
.word 0x02f7098b
.global o2_diag_5_end
o2_diag_5_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_5, .-o2_diag_5
.balign 64
.global o2_diag_6
.type o2_diag_6, @function
o2_diag_6:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_6_begin
o2_diag_6_begin:
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.word 0x0298080b
.global o2_diag_6_end
o2_diag_6_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_6, .-o2_diag_6
.balign 64
.global o2_diag_7
.type o2_diag_7, @function
o2_diag_7:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_7_begin
o2_diag_7_begin:
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.word 0x0298080b
.word 0x02b8888b
.global o2_diag_7_end
o2_diag_7_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_7, .-o2_diag_7
.balign 64
.global o2_diag_8
.type o2_diag_8, @function
o2_diag_8:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_8_begin
o2_diag_8_begin:
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.word 0x0298080b
.word 0x02b8888b
.word 0x02d9090b
.word 0x02f9898b
.global o2_diag_8_end
o2_diag_8_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_8, .-o2_diag_8
.balign 64
.global o2_diag_9
.type o2_diag_9, @function
o2_diag_9:
li t0, 0x6600
csrs mstatus, t0
csrwi vstart, 0
csrwi vcsr, 7
csrwi fcsr, 0
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
vsetivli zero, 8, e8, m1, tu, mu
.global o2_diag_9_begin
o2_diag_9_begin:
vsetivli zero, 8, e8, m1, tu, mu
.word 0x0294080b
vmv.x.s t2, v16
li t3, 0x0000000000000029
xor t2, t2, t3
vsetvli zero, t2, e8, m1, tu, mu
.word 0x0294088b
vmv.x.s t2, v17
li t3, 0x0000000000000029
xor t2, t2, t3
vsetvli zero, t2, e8, m1, tu, mu
.word 0x0294090b
vmv.x.s t2, v18
li t3, 0x0000000000000025
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vdivu.vv v19, v10, v11
vmv.x.s t2, v19
li t3, 0x0000000000000006
xor t2, t2, t3
vsetvli zero, t2, e8, m1, tu, mu
.word 0x0294080b
vmv.x.s t2, v16
li t3, 0x0000000000000025
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vfdiv.vv v17, v12, v13
vmv.x.s t2, v17
li t3, 0x0000000040600004
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vdivu.vv v18, v10, v11
vmv.x.s t2, v18
li t3, 0x0000000000000006
xor t2, t2, t3
vsetvli zero, t2, e8, m1, tu, mu
.word 0x0294098b
vmv.x.s t2, v19
li t3, 0x0000000000000025
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vdivu.vv v16, v10, v11
vmv.x.s t2, v16
li t3, 0x000000000000000a
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vdivu.vv v17, v10, v11
vmv.x.s t2, v17
li t3, 0x000000000000000a
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vdivu.vv v18, v10, v11
vmv.x.s t2, v18
li t3, 0x000000000000000a
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vfdiv.vv v19, v12, v13
vmv.x.s t2, v19
li t3, 0x0000000040600004
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vfdiv.vv v16, v12, v13
vmv.x.s t2, v16
li t3, 0x0000000040600008
xor t2, t2, t3
vsetvli zero, t2, e8, m1, tu, mu
.word 0x0294088b
vmv.x.s t2, v17
li t3, 0x0000000000000025
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vfdiv.vv v18, v12, v13
vmv.x.s t2, v18
li t3, 0x0000000040600004
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vdivu.vv v19, v10, v11
vmv.x.s t2, v19
li t3, 0x000000000000000a
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vfdiv.vv v16, v12, v13
vmv.x.s t2, v16
li t3, 0x0000000040600004
xor t2, t2, t3
vsetvli zero, t2, e32, m1, tu, mu
vfdiv.vv v17, v12, v13
vmv.x.s t2, v17
li t3, 0x0000000040600008
xor t2, t2, t3
vsetvli zero, t2, e8, m1, tu, mu
.global o2_diag_9_end
o2_diag_9_end:
mv t0, a1
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
csrr t0, vtype
sd t0, 0(a2)
csrr t0, vl
sd t0, 8(a2)
csrr t0, vstart
sd t0, 16(a2)
csrr t0, vxrm
sd t0, 24(a2)
csrr t0, vxsat
sd t0, 32(a2)
csrr t0, vcsr
sd t0, 40(a2)
csrr t0, fflags
sd t0, 48(a2)
fence rw, rw
ret
.size o2_diag_9, .-o2_diag_9
