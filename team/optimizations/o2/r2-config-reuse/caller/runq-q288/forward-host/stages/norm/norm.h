#ifndef R2_RMSNORM_OUTPUT_RVV_H
#define R2_RMSNORM_OUTPUT_RVV_H
/* Fixed-model optional RMSNorm. RV64/lp64d, RVV 1.0, VLEN=128, RNE.
 * size==288; valid 4-byte aligned binary32 arrays. x and weight are finite,
 * but arithmetic overflow/underflow is permitted and fflags remain sticky.
 * weight is read-only and disjoint from both x and o. o==x or o and x are
 * disjoint size-element spans; no partial overlap is supported.
 * FS/VS enabled, vstart=0. vl/vtype/vcsr restored/preserved; vector registers
 * are caller-clobbered under the ordinary C ABI. No errno/frm reset.
 * Keep contraction and fast-math disabled. This is not a new R5 default.
 */
void r2_rmsnorm_rvv(float *o, float *x, float *weight, int size);
void r2_norm_output_rvv(float *o, const float *x, const float *weight,
                        float inverse_rms, unsigned size);
#endif
