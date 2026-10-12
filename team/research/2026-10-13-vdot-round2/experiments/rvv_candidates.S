/* Research candidates only; assembly-checked, NOT run on NEMU/RTL.
 * VLEN=128, RV64GCV, VS enabled, vstart=0. No interrupt inside the measured
 * region. scratch registers are caller-clobbered. See 02-implementation.md.
 */
    .text
    .option norvc

/* B5 is equivalent only for the stated KNOWN entry policy. It is not a
 * five-instruction replacement for generic unknown-vtype B6.
 * Inputs v8,v9; result v10; scratch v2/v3. Each measured core is 20 bytes.
 */
    .macro B5 name, tail, mask
    .globl \name
    .type \name,@function
\name:
    .globl \name\()_begin
\name\()_begin:
    vwmul.vv    v2, v9, v8
    vsetivli    zero, 8, e16, m1, tu, mu
    vmv.v.i     v10, 0
    vwredsum.vs v10, v2, v10
    vsetivli    zero, 8, e8, m1, \tail, \mask
    .globl \name\()_end
\name\()_end:
    ret
    .size \name, .-\name
    .endm
    B5 b5_tumu, tu, mu
    B5 b5_tuma, tu, ma
    B5 b5_tamu, ta, mu
    B5 b5_tama, ta, ma

/* K-RVV: fixed-width delayed-reduction inner kernel.
 * Inputs a0/a1 -> readable signed-byte arrays; a2 = K.
 * PRECONDITION: K is a multiple of 8, 0 <= K <= 131064; VLEN=128.
 * Returns signed int32 in a0, sign-extended to RV64. Vector configuration,
 * v4,v8-v11,v16-v17,a1,a2,t0 are clobbered. No general tail/length wrapper.
 * Never call this research entry with arbitrary K. The caller must validate
 * length and supply scalar/tail/overflow fallback before target execution.
 * This is a KERNEL comparison, not full-state equivalence to one vdot.
 */
    .globl rvv_delayed_reduce_k8
    .type rvv_delayed_reduce_k8,@function
rvv_delayed_reduce_k8:
    beqz        a2, .Lzero
    vsetivli    zero, 8, e32, m2, tu, mu
    vmv.v.i     v16, 0
    vsetivli    zero, 8, e16, m1, tu, mu
.Lloop:
    /* EEW=8 with SEW=16, LMUL=1 -> EMUL=1/2. Eight bytes each. */
    vle8.v      v8, (a0)
    vle8.v      v9, (a1)
    vsext.vf2   v10, v8
    vsext.vf2   v11, v9
    vwmacc.vv   v16, v10, v11
    addi        a0, a0, 8
    addi        a1, a1, 8
    addi        a2, a2, -8
    bnez        a2, .Lloop
    vsetivli    zero, 8, e32, m2, tu, mu
    vmv.s.x     v4, zero
    vredsum.vs  v4, v16, v4
    vmv.x.s     a0, v4
    ret
.Lzero:
    li          a0, 0
    ret
    .size rvv_delayed_reduce_k8, .-rvv_delayed_reduce_k8
