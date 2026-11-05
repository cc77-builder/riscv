/* Team candidate contract: vdot-s8x8-r32-v0.1. */
#ifdef CONFIG_CUSTOM_VDOT
_Static_assert(VLEN == 128, "vdot-s8x8-r32-v0.1 requires VLEN=128");
bool vp_enable();
void vp_set_dirty();

def_EHelper(vdot) {
  /* Validate before reading sources, writing the destination or dirtying VS. */
  if (!vp_enable() || vtype->vill || vtype->pad || vtype->vsew != 0 ||
      vtype->vlmul != 0 || vl->val != 8 || vstart->val != 0) {
    longjmp_exception(EX_II);
  }

  const uint32_t word = s->isa.instr.val;
  const unsigned vs1 = (word >> 15) & 31;
  const unsigned vs2 = (word >> 20) & 31;
  const unsigned vd = (word >> 7) & 31;
  /* Snapshot both sources: all source/destination aliases, including v0. */
  const uint64_t a = cpu.vr[vs1]._64[0];
  const uint64_t b = cpu.vr[vs2]._64[0];
  int32_t sum = 0;
  for (unsigned i = 0; i < 8; ++i) {
    const uint8_t byte_a = a >> (8 * i);
    const uint8_t byte_b = b >> (8 * i);
    const int32_t x = byte_a < 128 ? byte_a : (int32_t)byte_a - 256;
    const int32_t y = byte_b < 128 ? byte_b : (int32_t)byte_b - 256;
    sum += x * y;
  }
  /* Zero-extend the 32-bit two's-complement field; bypass tail/mask merge. */
  cpu.vr[vd]._64[0] = (uint32_t)sum;
  cpu.vr[vd]._64[1] = 0;
  vp_set_dirty();
  /* vl/vtype/vstart/vxrm/vxsat/vcsr are unchanged. */
}
#endif
