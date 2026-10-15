/* Review candidate, NOT the team's accepted timing baseline.
 * RV64 + RVV 1.0, VLEN=128, entry e8,m1,actual vl=8,vstart=0,VS!=Off.
 * Input v8/v9, output v10; scratch v2/v3,t3/t4. All vta/vma accepted.
 * The six-instruction ROI excludes ret. No memory operations in the ROI.
 * Assemble: clang --target=riscv64 -march=rv64gcv -mabi=lp64d -c baseline6.S
 */
.text
.option push
.option norvc
.p2align 2
.globl baseline6_v10_v8_v9
.type baseline6_v10_v8_v9,@function
baseline6_v10_v8_v9:
.globl baseline6_begin
baseline6_begin:
    csrr t4, vtype
    vwmul.vv v2, v9, v8
    vsetivli t3, 8, e16, m1, tu, mu
    vmv.v.i v10, 0
    vwredsum.vs v10, v2, v10
    vsetvl zero, t3, t4
.globl baseline6_end
baseline6_end:
    ret
.size baseline6_v10_v8_v9, .-baseline6_v10_v8_v9
.option pop
