.option norvc
.option norelax
.text
.balign 64
.global qkv_quantize
.type qkv_quantize,@function
/* a0: 288 finite floats; a1: 288 int8; a2: 9 float scales.
 * Domain checked before entry. RNE divisions, ties-away integer conversion.
 * All loop/addresses depend only on public fixed dimensions. */
qkv_quantize:
  li t0,9
  lui t4,0x42fe0
  fmv.w.x ft3,t4
.Lquant_group:
  fmv.w.x ft0,zero
  mv t1,a0
  addi t2,a0,128
.Lmaximum:
  flw ft1,0(t1)
  fsgnjx.s ft1,ft1,ft1
  fmax.s ft0,ft0,ft1
  addi t1,t1,4
  bne t1,t2,.Lmaximum
  fdiv.s ft2,ft0,ft3,rne
  fsw ft2,0(a2)
.Lquant_element:
  flw ft1,0(a0)
  fdiv.s ft1,ft1,ft2,rne
  fcvt.w.s t3,ft1,rmm
  sb t3,0(a1)
  addi a0,a0,4
  addi a1,a1,1
  bne a0,t2,.Lquant_element
  addi a2,a2,4
  addi t0,t0,-1
  bne t0,zero,.Lquant_group
  ret
.size qkv_quantize,.-qkv_quantize

.balign 64
.global qkv_boundary
.type qkv_boundary,@function
/* One quantization, three Q/K/V calls sharing its exact output buffers.
 * Context: fp,x,xs,qctx,kctx,vctx,kernel (7 RV64 pointers). */
qkv_boundary:
  addi sp,sp,-16
  sd ra,0(sp)
  sd s0,8(sp)
  mv s0,a0
  ld a0,0(s0)
  ld a1,8(s0)
  ld a2,16(s0)
  call qkv_quantize
  ld a0,24(s0)
  ld t0,48(s0)
  jalr ra,0(t0)
  ld a0,32(s0)
  ld t0,48(s0)
  jalr ra,0(t0)
  ld a0,40(s0)
  ld t0,48(s0)
  jalr ra,0(t0)
  ld ra,0(sp)
  ld s0,8(sp)
  addi sp,sp,16
  ret
.size qkv_boundary,.-qkv_boundary
