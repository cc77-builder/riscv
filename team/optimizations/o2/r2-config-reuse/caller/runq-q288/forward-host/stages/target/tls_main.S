.option norvc
.option norelax
.section .text.main,"ax",@progbits
.balign 4
.global main
.type main,@function
main:
    la tp, team_tls_area
    addi tp, tp, 16
    sd zero, 0(tp)
    sd zero, 8(tp)
    sd zero, 16(tp)
    sd zero, 24(tp)
    sd zero, 32(tp)
    sd zero, 40(tp)
    sd zero, 48(tp)
    sd zero, 56(tp)
    tail team_math_main
.size main,.-main
