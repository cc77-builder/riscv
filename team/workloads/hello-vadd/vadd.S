.text
.align 2
.globl vadd8
.type vadd8, @function
vadd8:
  # a0/a1: source pointers; a2: destination pointer. Return actual VL.
  vsetivli t0, 8, e8, m1, ta, ma
  vle8.v v1, (a0)
  vle8.v v2, (a1)
  vadd.vv v3, v1, v2
  vse8.v v3, (a2)
  mv a0, t0
  ret
.size vadd8, .-vadd8
