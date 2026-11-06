.section .text
.balign 4

/* a0=A[16], a1=B[16], a2=out[4], a3=meta[4].
 * Each source is loaded with VL16 before selecting the instruction's VL.
 * Each function executes exactly one custom instruction, then stores all 128 bits.
 */
.macro DOTCASE id, base, vd, vs1, vs2, vl
.global dot16_smoke_case\id
.type dot16_smoke_case\id, @function
dot16_smoke_case\id:
    vsetivli t0, 16, e8, m1, ta, ma
    vle8.v v\vs1, (a0)
    vle8.v v\vs2, (a1)
.if (\vd != \vs1) && (\vd != \vs2)
    vmv.v.i v\vd, -1
.endif
    vsetivli t0, \vl, e8, m1, ta, ma
    sd t0, 0(a3)
    csrr t1, vtype
    sd t1, 8(a3)
    csrr t1, vstart
    sd t1, 16(a3)
    .word (\base | (\vd << 7) | (\vs1 << 15) | (\vs2 << 20))
    vsetivli t0, 4, e32, m1, ta, ma
    sd t0, 24(a3)
    vse32.v v\vd, (a2)
    ret
.global dot16_smoke_case\id\()_end
dot16_smoke_case\id\()_end:
.size dot16_smoke_case\id, .-dot16_smoke_case\id
.endm

DOTCASE 0, 0x0200000b, 10, 8, 9, 8
DOTCASE 1, 0x0e00000b,  8, 8, 9, 16
DOTCASE 2, 0x0e00000b,  0, 8, 9, 16
DOTCASE 3, 0x0e00000b,  9, 8, 9, 16
DOTCASE 4, 0x0e00000b,  0, 0, 0, 16
DOTCASE 5, 0x0200000b, 10, 8, 9, 8

.section .note.GNU-stack,"",@progbits
