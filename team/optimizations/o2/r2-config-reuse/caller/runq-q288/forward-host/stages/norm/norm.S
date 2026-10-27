/* Output only: preserve two independent FP32 roundings per active element.
 * fa0 is a correctly NaN-boxed binary32 C ABI argument. No reassociation.
 */
.text
.option push
.option norvc
.option norelax
.balign 16
.global r2_norm_output_rvv
.type r2_norm_output_rvv,@function
r2_norm_output_rvv:
    csrr t3,vl
    csrr t4,vtype
.Lnorm_loop:
    vsetvli t0,a3,e32,m8,ta,ma
    vle32.v v8,(a1)
    vle32.v v16,(a2)
    vfmul.vf v8,v8,fa0
    vfmul.vv v8,v16,v8
    vse32.v v8,(a0)
    slli t1,t0,2
    add a0,a0,t1
    add a1,a1,t1
    add a2,a2,t1
    sub a3,a3,t0
    bnez a3,.Lnorm_loop
    vsetvl zero,t3,t4
    ret
.size r2_norm_output_rvv,.-r2_norm_output_rvv
.option pop
.section .note.GNU-stack,"",@progbits
