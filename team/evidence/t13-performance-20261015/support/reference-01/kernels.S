.option norvc
.text
generic_10_8_9:
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v8, v9
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v10, 0
vwredsum.vs v10, v2, v10
vsetvl zero, t3, t4
vdot_10_8_9:
.word 0x0294050b
generic_8_8_9:
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v8, v9
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v8, 0
vwredsum.vs v8, v2, v8
vsetvl zero, t3, t4
vdot_8_8_9:
.word 0x0294040b
generic_9_8_9:
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v8, v9
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v9, 0
vwredsum.vs v9, v2, v9
vsetvl zero, t3, t4
vdot_9_8_9:
.word 0x0294048b
generic_10_8_8:
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v8, v8
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v10, 0
vwredsum.vs v10, v2, v10
vsetvl zero, t3, t4
vdot_10_8_8:
.word 0x0284050b
generic_8_8_8:
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v8, v8
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v8, 0
vwredsum.vs v8, v2, v8
vsetvl zero, t3, t4
vdot_8_8_8:
.word 0x0284040b
generic_0_0_9:
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v0, v9
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v0, 0
vwredsum.vs v0, v2, v0
vsetvl zero, t3, t4
vdot_0_0_9:
.word 0x0290000b
generic_31_8_31:
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v8, v31
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v31, 0
vwredsum.vs v31, v2, v31
vsetvl zero, t3, t4
vdot_31_8_31:
.word 0x03f40f8b
known:
vwmul.vv v2, v8, v9
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v10, 0
vwredsum.vs v10, v2, v10
vsetivli zero, 8, e8, m1, tu, mu
batch:
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
